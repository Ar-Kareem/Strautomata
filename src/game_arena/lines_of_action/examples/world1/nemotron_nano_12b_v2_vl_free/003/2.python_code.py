
def policy(board):
    moves = []
    dirs = [
        (0, -1),   # left
        (0, 1),    # right
        (-1, 0),   # up
        (1, 0),    # down
        (-1, -1),  # up-left
        (-1, 1),   # up-right
        (1, -1),   # down-left
        (1, 1)     # down-right
    ]

    def count_row(row):
        return sum(1 for col in range(8) if board[row][col] != 0)

    def count_col(col):
        return sum(1 for row in range(8) if board[row][col] != 0)

    def count_diag1(r, c):
        return sum(1 for r2 in range(8) if 0 <= r2 - (r - c) < 8 and board[r2][r2 - (r - c)] != 0)

    def count_diag2(r, c):
        return sum(1 for r2 in range(8) if 0 <= (r + c) - r2 < 8 and board[r2][(r + c) - r2] != 0)

    for r in range(8):
        for c in range(8):
            if board[r][c] != 1:
                continue

            for dx, dy in dirs:
                if dx == 0:
                    k = count_row(r)
                elif dy == 0:
                    k = count_col(c)
                else:
                    if dx * dy == 1:
                        k = count_diag1(r, c)
                    else:
                        k = count_diag2(c, r)

                new_r = r + dx * k
                new_c = c + dy * k
                if not (0 <= new_r < 8 and 0 <= new_c < 8):
                    continue

                valid = True
                for i in range(1, k + 1):
                    cr, cc = r + dx * i, c + dy * i
                    if not (0 <= cr < 8 and 0 <= cc < 8):
                        valid = False
                        break
                    if board[cr][cc] == -1:
                        valid = False
                        break
                if not valid:
                    continue

                dest_val = board[new_r][new_c]
                if new_val == 1:
                    continue

                move_str = f"{r},{c}:{new_r},{new_c}"
                capture = (new_val == -1)
                moves.append((cell_str, capture, k))

    captures = [m for m in moves if m[1]]
    if captures:
        if not captures:
            return None
        selected = max(captures, key=lambda x: x[2])
        return selected[0]
    else:
        if not moves:
            return None
        moves_sorted = sorted(moves, key=lambda x: (-x[2], x[0]))
        return moves_sorted[0][0]
