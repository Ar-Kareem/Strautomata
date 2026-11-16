
def policy(board: list[list[int]]) -> tuple[int, int]:
    n = 10
    ships = [5, 4, 3, 3, 2]
    prob = [[0.0] * n for _ in range(n)]

    HIT_BONUS = 50  # multiplier per hit overlapped

    for length in ships:
        for r in range(n):
            for c in range(n):
                for dr, dc in ((0, 1), (1, 0)):
                    er = r + dr * (length - 1)
                    ec = c + dc * (length - 1)
                    if er >= n or ec >= n:
                        continue
                    ok = True
                    hit_count = 0
                    for k in range(length):
                        rr = r + dr * k
                        cc = c + dc * k
                        v = board[rr][cc]
                        if v == -1:
                            ok = False
                            break
                        if v == 1:
                            hit_count += 1
                    if not ok:
                        continue
                    weight = HIT_BONUS ** hit_count
                    for k in range(length):
                        rr = r + dr * k
                        cc = c + dc * k
                        if board[rr][cc] == 0:
                            prob[rr][cc] += weight

    best_val = -1.0
    best_cell = None
    for r in range(n):
        for c in range(n):
            if board[r][c] == 0 and prob[r][c] > best_val:
                best_val = prob[r][c]
                best_cell = (r, c)

    if best_cell is not None and best_val > 0:
        return best_cell

    # Fallback: first unknown cell
    for r in range(n):
        for c in range(n):
            if board[r][c] == 0:
                return (r, c)
    return (0, 0)
