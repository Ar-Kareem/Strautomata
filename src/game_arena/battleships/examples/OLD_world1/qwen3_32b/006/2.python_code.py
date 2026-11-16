
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Initialize a 10x10 probability matrix
    prob = [[0] * 10 for _ in range(10)]

    # List of all ship lengths to consider
    ship_lengths = [5, 4, 3, 3, 2]

    # Evaluate all valid ship placements for each length
    for length in ship_lengths:
        # 1. Horizontal placements
        for row in range(10):
            max_col = 10 - length
            for col in range(max_col + 1):
                # Check if the horizontal segment is valid (no -1)
                valid = True
                for c in range(col, col + length):
                    if board[row][c] == -1:
                        valid = False
                        break
                if valid:
                    # Add this position to the probability matrix
                    for c in range(col, col + length):
                        prob[row][c] += 1

        # 2. Vertical placements
        for col in range(10):
            max_row = 10 - length
            for row in range(max_row + 1):
                # Check if the vertical segment is valid (no -1)
                valid = True
                for r in range(row, row + length):
                    if board[r][col] == -1:
                        valid = False
                        break
                if valid:
                    # Add this position to the probability matrix
                    for r in range(row, row + length):
                        prob[r][col] += 1

    # Find the cell with the highest probability among untested ones
    max_prob = -1
    best_row, best_col = 0, 0
    for r in range(10):
        for c in range(10):
            if board[r][c] == 0 and prob[r][c] > max_prob:
                max_prob = prob[r][c]
                best_row, best_col = r, c

    return (best_row, best_col)
