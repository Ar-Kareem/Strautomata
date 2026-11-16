
def policy(board: list[list[int]]) -> tuple[int, int]:
    N = 10
    ships = [5, 4, 3, 3, 2]
    scores = [[0.0] * N for _ in range(N)]

    for L in ships:
        # Horizontal placements
        for r in range(N):
            for c in range(N - L + 1):
                valid = True
                hits = 0
                for i in range(L):
                    v = board[r][c + i]
                    if v == -1:
                        valid = False
                        break
                    if v == 1:
                        hits += 1
                if not valid:
                    continue
                weight = (50.0 ** hits) if hits > 0 else 1.0
                for i in range(L):
                    if board[r][c + i] == 0:
                        scores[r][c + i] += weight

        # Vertical placements
        for c in range(N):
            for r in range(N - L + 1):
                valid = True
                hits = 0
                for i in range(L):
                    v = board[r + i][c]
                    if v == -1:
                        valid = False
                        break
                    if v == 1:
                        hits += 1
                if not valid:
                    continue
                weight = (50.0 ** hits) if hits > 0 else 1.0
                for i in range(L):
                    if board[r + i][c] == 0:
                        scores[r + i][c] += weight

    best = None
    best_score = -1.0
    for r in range(N):
        for c in range(N):
            if board[r][c] == 0 and scores[r][c] > best_score:
                best_score = scores[r][c]
                best = (r, c)

    if best is not None and best_score > 0:
        return best

    # Fallback: any legal cell
    for r in range(N):
        for c in range(N):
            if board[r][c] == 0:
                return (r, c)
    return (0, 0)
