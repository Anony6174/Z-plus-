import json
import os
import subprocess
import sys

from zplus.pipeline import run
from zplus.report import to_html, to_text
from zplus.types import Config
from tests.conftest import FIXTURES, ROOT

SIX = os.path.join(FIXTURES, "six")
INJECT = os.path.join(FIXTURES, "inject")
SNAPSHOT = os.path.join(FIXTURES, "snapshots", "six.txt")


def cli(*args):
    return subprocess.run([sys.executable, "-m", "zplus", *args], capture_output=True,
                          text=True, cwd=ROOT)


def test_cli_json_exit_code_and_valid_json():
    proc = cli("scan", SIX, "--format", "json")
    assert proc.returncode == 1  # flags found
    data = json.loads(proc.stdout)
    assert set(data) >= {"config", "pairs", "clusters", "skipped"}
    assert data["config"]["k"] == 6


def test_cli_no_flags_exit_zero():
    proc = cli("scan", SIX, "--threshold", "1.01")
    assert proc.returncode == 0
    assert "No pairs reached the threshold." in proc.stdout


def test_cli_missing_folder_exit_two():
    proc = cli("scan", os.path.join(FIXTURES, "does_not_exist"))
    assert proc.returncode == 2
    assert "not a folder" in proc.stderr


def test_cli_bad_option_exit_two():
    assert cli("scan", SIX, "--k", "0").returncode == 2
    assert cli("scan", SIX, "--template", "missing.py").returncode == 2


def test_html_escapes_script(tmp_path):
    out = tmp_path / "r.html"
    proc = cli("scan", INJECT, "--format", "html", "--out", str(out))
    assert proc.returncode == 1
    page = out.read_text()
    assert "&lt;script&gt;" in page
    assert "<script>" not in page
    assert "<mark class=" in page
    assert "inject/broken" in page  # skipped file is listed


def test_text_snapshot():
    text = to_text(run(SIX, Config()))
    if not os.path.exists(SNAPSHOT):  # first run writes the snapshot
        os.makedirs(os.path.dirname(SNAPSHOT), exist_ok=True)
        with open(SNAPSHOT, "w") as fh:
            fh.write(text)
    with open(SNAPSHOT) as fh:
        assert text == fh.read()


def test_top_limits_output():
    report = run(SIX, Config())
    assert "more flagged pairs not shown" in to_text(report, top=1)
    assert to_html(report, top=1).count('class="card" id="pair') == 1


def test_cli_in_process(tmp_path, capsys):
    from zplus.cli import main

    out = tmp_path / "r.json"
    assert main(["scan", SIX, "--format", "json", "--out", str(out), "--top", "1"]) == 1
    assert len(json.loads(out.read_text())["pairs"]) == 1
    assert main(["scan", SIX, "--format", "html", "--no-ast"]) == 1
    assert "<!doctype html>" in capsys.readouterr().out
    assert main(["scan", SIX, "--top", "0"]) == 2
    assert main(["validate", os.path.join(FIXTURES, "inject")]) == 2
    assert main(["eval", os.path.join(FIXTURES, "nope")]) == 2
    assert main(["eval", SIX, "--sizes", "x"]) == 2


def test_line_range_ignores_trailing_dedent():
    from zplus.normalize import normalize
    from zplus.report import line_range

    toks = normalize("if x:\n    y = 1\nz = 2\n")
    # tokens 0..9 end with the DEDENT that tokenize stamps on line 3
    assert toks[9].kind == "DEDENT" and toks[9].line == 3
    assert line_range(toks, 0, 10) == [1, 2]
