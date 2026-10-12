# Repeatedly delete innermost pairs until nothing changes.
def solve(s):
    text = "".join(ch for ch in s if ch in "()[]{}")
    while True:
        shorter = text.replace("()", "").replace("[]", "").replace("{}", "")
        if shorter == text:
            break
        text = shorter
    return text == ""
