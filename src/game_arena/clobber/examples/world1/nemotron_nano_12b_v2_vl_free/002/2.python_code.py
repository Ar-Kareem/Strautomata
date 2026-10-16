
def policy(you: list[int], opponent: list[int]) -> str:
    # Define possible directions (Up, Right, Down, Left)
    directions = [(-1, 0, 'U'), (0, 1, 'R'), (1, 0, 'D'), (0, -1, 'L')]
    # Iterate through each row and column
    for row in range(5):
        for col in range(6):
            if you[row][col] == 1:
                # Check each direction in order
                for dr, dc, dir_char in directions:
                    new_row = row + dr
                    new_col = col + dc
                    # Check if the new position is within bounds
                    if 0 <= new_row < 5 and 0 <= new_col < 6:
                        if opponent[new_row][new_col] == 1:
                            # Return the first valid move found
                            return f"{row},{col},{dir_char}"
    # The problem states there will always be a legal move
    return ""
