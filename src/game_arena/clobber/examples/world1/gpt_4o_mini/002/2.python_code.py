
def policy(you: list[int], opponent: list[int]) -> str:
    moves = []

    # Directions for moving: (row_offset, col_offset, direction)
    directions = [(-1, 0, 'U'), (1, 0, 'D'), (0, -1, 'L'), (0, 1, 'R')]

    for row in range(5):
        for col in range(6):
            if you[row][col] == 1:  # If this cell has your piece
                for dr, dc, direction in directions:
                    new_row = row + dr
                    new_col = col + dc
                    # Check if the new position is in bounds and has an opponent's piece
                    if 0 <= new_row < 5 and 0 <= new_col < 6 and opponent[new_row][new_col] == 1:
                        # Found a valid move
                        return f"{row},{col},{direction}"

    # Should never reach here based on problem statement
    return ""

