
def policy(you: list[int], opponent: list[int]) -> str:
    rows, cols = 5, 6
    directions = [(0, -1, 'L'), (0, 1, 'R'), (-1, 0, 'U'), (1, 0, 'D')]  # (row_change, col_change, dir)
    
    for row in range(rows):
        for col in range(cols):
            if you[row][col] == 1:  # You have a piece here
                for dr, dc, dir in directions:
                    new_row, new_col = row + dr, col + dc
                    if 0 <= new_row < rows and 0 <= new_col < cols:  # Check bounds
                        if opponent[new_row][new_col] == 1:  # There's an opponent's piece
                            return f"{row},{col},{dir}"  # Return the legal move

    # Since it's guaranteed a move exists, we shouldn't reach here
    raise RuntimeError("No legal moves available when the function was called.")
