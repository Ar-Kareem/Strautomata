
def policy(you: list[int], opponent: list[int]) -> int:
    for row in range(5):
        for col in range(6):
            if you[row][col] == 1:  # Check if it's your piece
                # Check Up
                if row > 0 and opponent[row - 1][col] == 1:
                    return f"{row},{col},U"
                # Check Down
                if row < 4 and opponent[row + 1][col] == 1:
                    return f"{row},{col},D"
                # Check Left
                if col > 0 and opponent[row][col - 1] == 1:
                    return f"{row},{col},L"
                # Check Right
                if col < 5 and opponent[row][col + 1] == 1:
                    return f"{row},{col},R"
    
    # The function should never reach this point due
    # to the constraint that always allows for at least one legal move.
    raise RuntimeError("Should have found a move, but did not.")

