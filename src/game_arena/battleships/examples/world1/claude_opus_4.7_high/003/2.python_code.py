
def policy(board: list[list[int]]) -> tuple[int, int]:
    N = 10
    ships = [5, 4, 3, 3, 2]

    heat = [[0.0] * N for _ in range(N)]
    has_hits = any(board[r][c] == 1 for r in range(N) for c in range(N))

    for length in ships:
        for r in range(N):
            for c in range(N):
                for dr, dc in ((0, 1), (1, 0)):
                    er = r + dr * (length - 1)
                    ec = c + dc * (length - 1)
                    if er >= N or ec >= N:
                        continue
                    blocked = False
                    hit_count = 0
                    for i in range(length):
                        v = board[r + dr * i][c + dc * i]
                        if v == -1:
                            blocked = True
                            break
                        if v == 1:
                            hit_count += 1
                    if blocked:
                        continue

                    if has_hits:
                        if hit_count > 0:
                            weight = 100.0 * (hit_count ** 2 + 1)
                        else:
                            weight = 1.0
                    else:
                        weight = 1.0

                    for i in range(length):
                        cr = r + dr * i
                        cc = c + dc * i
                        if board[cr][cc] == 0:
                            heat[cr][cc] += weight

    best = None
    best_val = -1.0
    for r in range(N):
        for c in range(N):
            if board[r][c] == 0:
                # Slight parity preference as tiebreak (checker hunt)
                val = heat[r][c]
                if not has_hits and (r + c) % 2 == 0:
                    val += 0.001
                if val > best_val:
                    best_val = val
                    best = (r, c)

    if best is None:
        for r in range(N):
            for c in range(N):
                if board[r][c] == 0:
                    return (r, c)
        return (0, 0)

    return best
