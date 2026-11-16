
def policy(you, opponent):
    for row in range(5):
        for col in range(6):
            if you[row][col] == 1:
                # Check up
                if row - 1 >= 0 and opponent[row-1][col] == 1:
                    return f"{row},{col},U"
                # Check right
                if col + 1 < 6 and opponent[row][col+1] == 1:
                    return f"{row},{col},R"
                # Check down
                if row + 1 < 5 and opponent[row+1][col] == 1:
                    return f"{row},{col},D"
                # Check left
                if col - 1 >= 0 and opponent[row][col-1] == 1:
                    return f"{row},{col},L"
    # According to the problem, this line should never be reached since there's always at least one move.
    return ""  # Fallback (should not occur)
