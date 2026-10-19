
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Battleship targeting policy.
    - 0: Unknown
    - -1: Miss
    - 1: Hit
    """
    rows = 10
    cols = 10

    hits = []
    for r in range(rows):
        for c in range(cols):
            if board[r][c] == 1:
                hits.append((r, c))

    def is_valid(r, c):
        return 0 <= r < rows and 0 <= c < cols

    def get_neighbors(r, c):
        res = []
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = r + dr, c + dc
            if is_valid(nr, nc):
                res.append((nr, nc))
        return res

    # TARGET MODE: If there are hits, try to sink the ship
    target_candidates = []
    for r, c in hits:
        for nr, nc in get_neighbors(r, c):
            if board[nr][nc] == 0:
                # Prioritize based on alignment (if we have two hits in a row)
                weight = 1
                # Check for line: if neighbor of 'hit' aligns with another 'hit'
                dr, dc = nr - r, nc - c
                # If the opposite side of the hit (r-dr, c-dc) is also a hit, high priority
                if is_valid(r - dr, c - dc) and board[r - dr][c - dc] == 1:
                    weight = 10
                target_candidates.append((weight, (nr, nc)))

    if target_candidates:
        # Pick the best weights, then random among them
        max_weight = max(w for w, pos in target_candidates)
        best_targets = [pos for w, pos in target_candidates if w == max_weight]
        return random.choice(best_targets)

    # HUNT MODE: Checkerboard search / Parity
    # We also prioritize areas with more open space
    hunt_candidates = []
    for r in range(rows):
        for c in range(cols):
            if board[r][c] == 0:
                # Checkerboard: Only even parity to find all ships (min length 2)
                if (r + c) % 2 == 0:
                    score = 0
                    # Basic local density check
                    for nr, nc in get_neighbors(r, c):
                        if board[nr][nc] == 0:
                            score += 1
                    hunt_candidates.append((score, (r, c)))

    if hunt_candidates:
        max_score = max(s for s, pos in hunt_candidates)
        best_hunts = [pos for s, pos in hunt_candidates if s == max_score]
        return random.choice(best_hunts)

    # Fallback: Just in case checkerboard is exhausted or something fails
    remaining = [(r, c) for r in range(rows) for c in range(cols) if board[r][c] == 0]
    return random.choice(remaining)
