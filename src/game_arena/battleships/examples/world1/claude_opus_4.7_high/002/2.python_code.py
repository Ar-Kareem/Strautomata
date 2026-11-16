
def policy(board: list[list[int]]) -> tuple[int, int]:
    N = 10
    ships = [5, 4, 3, 3, 2]
    HIT_BONUS = 100

    scores = [[0.0] * N for _ in range(N)]

    for ship_len in ships:
        # Horizontal placements
        for r in range(N):
            for c in range(N - ship_len + 1):
                valid = True
                hits = 0
                for i in range(ship_len):
                    v = board[r][c + i]
                    if v == -1:
                        valid = False
                        break
                    if v == 1:
                        hits += 1
                if not valid:
                    continue
                weight = HIT_BONUS ** hits if hits > 0 else 1
                for i in range(ship_len):
                    if board[r][c + i] == 0:
                        scores[r][c + i] += weight

        # Vertical placements
        for c in range(N):
            for r in range(N - ship_len + 1):
                valid = True
                hits = 0
                for i in range(ship_len):
                    v = board[r + i][c]
                    if v == -1:
                        valid = False
                        break
                    if v == 1:
                        hits += 1
                if not valid:
                    continue
                weight = HIT_BONUS ** hits if hits > 0 else 1
                for i in range(ship_len):
                    if board[r + i][c] == 0:
                        scores[r + i][c] += weight

    best_score = -1.0
    best_move = None
    for r in range(N):
        for c in range(N):
            if board[r][c] == 0 and scores[r][c] > best_score:
                best_score = scores[r][c]
                best_move = (r, c)

    if best_move is None:
        # Fallback: any unknown cell
        for r in range(N):
            for c in range(N):
                if board[r][c] == 0:
                    return (r, c)
        return (0, 0)

    return best_move
