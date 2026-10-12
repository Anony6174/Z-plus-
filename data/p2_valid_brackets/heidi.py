def solve(s):
    # hard negative: stack again, but index-based instead of a dict
    left = "([{"
    right = ")]}"
    st = []
    for i in range(len(s)):
        c = s[i]
        if c in left:
            st.append(left.index(c))
        elif c in right:
            if len(st) == 0 or st[-1] != right.index(c):
                return False
            st.pop()
    return len(st) == 0


if __name__ == "__main__":
    print(solve("{[]}"))
