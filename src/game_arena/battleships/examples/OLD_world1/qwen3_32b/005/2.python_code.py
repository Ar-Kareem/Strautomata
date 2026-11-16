
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Initialize a probability grid
    prob = [[0 for _ in range(10)] for _ in range(10)]
    # Ship lengths available to the opponent
    ship_lengths = [5, 4, 3, 3, 2]

    # For each ship size, count all valid placements on the board
    for ship_size in ship_lengths:
        for row in range(10):
            for col in range(10):
                # Check horizontal placement
                if col + ship_size <= 10:
                    valid = True
                    for c in range(col, col + ship_size):
                        if board[row][c] == -1:
                            valid = False
                            break
                    if valid:
                        for c in range(col, col + ship_size):
                            prob[row][c] += 1
                # Check vertical placement
                if row + ship_size <= 10:
                    valid = True
                    for r in range(row, row + ship_size):
                        if board[r][col] == -1:
                            valid = False
                            break
                    if valid:
                        for r in range(row, row + ship_size):
                            prob[r][col] += 1

    # Find the untried cell with the highest probability value
    best_row, best_col = 0, 0
    for row in range(10):
        for col in range(10):
            if board[row][col] == 0:
                if prob[row][col] > prob[best_row][best_col]:
                    best_row, best_col = row, col
                elif prob[row][col] == prob[best_row][best_col]:
                    # Tie-breaker: choose the lexicographically smallest cell
                    if (row, col) < (best_row, best_col):
                        best_row, best_col = row, col

    return (best_row, best_col)
