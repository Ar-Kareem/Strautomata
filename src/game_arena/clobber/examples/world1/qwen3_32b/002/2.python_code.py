
def policy(you, opponent):
    directions = [('U', -1, 0), ('R', 0, 1), ('D', 1, 0), ('L', 0, -1)]
    for row in range(5):
        for col in range(6):
            if you[row][col] == 1:
                for d, dr, dc in directions:
                    new_row = row + dr
                    new_col = col + dc
                    if 0 <= new_row < 5 and 0 <= new_col < 6:
                        if opponent[new_row][new_col] == 1:
                            return f"{row},{col},{d}"
    return ""
