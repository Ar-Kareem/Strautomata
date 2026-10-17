
def policy(board):
    import numpy as np
    N = 10
    b = board
    ships = [5, 4, 3, 3, 2]

    hits = set()
    misses = set()
    unknowns = []
    for r in range(N):
        for c in range(N):
            v = b[r][c]
            if v == 1:
                hits.add((r, c))
            elif v == -1:
                misses.add((r, c))
            else:
                unknowns.append((r, c))

    if not unknowns:
        # Should not happen, but fallback
        return (0, 0)

    heat = [[0.0] * N for _ in range(N)]
    has_hits = len(hits) > 0

    for ship in ships:
        # Horizontal
        for r in range(N):
            for c in range(N - ship + 1):
                blocked = False
                hit_cover = 0
                for i in range(ship):
                    cell = (r, c + i)
                    if cell in misses:
                        blocked = True
                        break
                    if cell in hits:
                        hit_cover += 1
                if blocked:
                    continue
                if has_hits:
                    weight = 1.0 if hit_cover == 0 else (100.0 ** hit_cover)
                else:
                    weight = 1.0
                for i in range(ship):
                    rr, cc = r, c + i
                    if b[rr][cc] == 0:
                        heat[rr][cc] += weight
        # Vertical
        for r in range(N - ship + 1):
            for c in range(N):
                blocked = False
                hit_cover = 0
                for i in range(ship):
                    cell = (r + i, c)
                    if cell in misses:
                        blocked = True
                        break
                    if cell in hits:
                        hit_cover += 1
                if blocked:
                    continue
                if has_hits:
                    weight = 1.0 if hit_cover == 0 else (100.0 ** hit_cover)
                else:
                    weight = 1.0
                for i in range(ship):
                    rr, cc = r + i, c
                    if b[rr][cc] == 0:
                        heat[rr][cc] += weight

    best = None
    best_v = -1.0
    for (r, c) in unknowns:
        v = heat[r][c]
        # Small tiebreaker: prefer checkerboard parity in hunt mode
        if not has_hits:
            if (r + c) % 2 == 0:
                v += 0.01
        if v > best_v:
            best_v = v
            best = (r, c)

    if best is None:
        return unknowns[0]
    return best
