
def policy(board: list[list[int]]) -> tuple[int, int]:
    rows, cols = 10, 10
    ship_lengths = [5, 4, 3, 3, 2]
    scores = [[0] * cols for _ in range(rows)]

    # Horizontal placements
    for length in ship_lengths:
        for r in range(rows):
            for c_start in range(cols - length + 1):
                valid = True
                for i in range(length):
                    if board[r][c_start + i] == -1:
                        valid = False
                        break
                if valid:
                    for i in range(length):
                        scores[r][c_start + i] += 1

    # Vertical placements
    for length in ship_lengths:
        for c in range(cols):
            for r_start in range(rows - length + 1):
                valid = True
                for i in range(length):
                    if board[r_start + i][c] == -1:
                        valid = False
                        break
                if valid:
                    for i in range(length):
                        scores[r_start + i][c] += 1

    # Find the unknown cell (0) with the highest score, ties broken by row then col
    max_score = -1
    best_r, best_c = -1, -1
    for r in range(rows):
        for c in range(cols):
            if board[r][c] == 0:
                score = scores[r][c]
                if (score > max_score or
                    (score == max_score and (r < best_r or (r == best_r and c < best_c)))):
                    max_score = score
                    best_r = r
                    best_c = c

    return (best_r, best_c)
