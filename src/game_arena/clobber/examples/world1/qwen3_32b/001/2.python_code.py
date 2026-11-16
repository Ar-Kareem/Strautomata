
def policy(you: list[int], opponent: list[int]) -> int:
    for row in range(5):
        for col in range(6):
            if you[row][col] == 1:
                # Check directions in the order: Up, Right, Down, Left
                for drow, dcol, direction in [(-1, 0, 'U'), (0, 1, 'R'), (1, 0, 'D'), (0, -1, 'L')]:
                    new_row, new_col = row + drow, col + dcol
                    if 0 <= new_row < 5 and 0 <= new_col < 6:
                        if opponent[new_row][new_col] == 1:
                            return f"{row},{col},{direction}"
    return ""  # Should never reach here as per problem constraints
