
def policy(you: list[int], opponent: list[int]) -> str:
    for r in range(5):
        for c in range(6):
            if you[r][c] == 1:
                # Check up
                if r > 0 and opponent[r-1][c] == 1:
                    return f"{r},{c},U"
                # Check down
                if r < 4 and opponent[r+1][c] == 1:
                    return f"{r},{c},D"
                # Check left
                if c > 0 and opponent[r][c-1] == 1:
                    return f"{r},{c},L"
                # Check right
                if c < 5 and opponent[r][c+1] == 1:
                    return f"{r},{c},R"
