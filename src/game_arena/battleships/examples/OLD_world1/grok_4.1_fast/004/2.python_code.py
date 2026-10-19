
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    n = 10
    unknowns = [(i, j) for i in range(n) for j in range(n) if board[i][j] == 0]
    if not unknowns:
        return (0, 0)  # Should not happen

    # Find all hit positions
    hits = [(i, j) for i in range(n) for j in range(n) if board[i][j] == 1]

    # Find adjacent unknown cells to hits
    adj_candidates = set()
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    for r, c in hits:
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < n and board[nr][nc] == 0:
                adj_candidates.add((nr, nc))

    if adj_candidates:
        return random.choice(list(adj_candidates))

    # Hunt phase: compute density map for possible ship placements in unknown cells
    density = [[0] * n for _ in range(n)]
    ship_lengths = [2, 3, 3, 4, 5]
    ship_dirs = [(0, 1), (1, 0)]  # horizontal, vertical

    for length in ship_lengths:
        for dr, dc in ship_dirs:
            for r in range(n):
                for c in range(n):
                    # Check if entire ship can be placed starting at (r, c)
                    valid = True
                    positions = []
                    for k in range(length):
                        rr = r + k * dr
                        cc = c + k * dc
                        if not (0 <= rr < n and 0 <= cc < n and board[rr][cc] == 0):
                            valid = False
                            break
                        positions.append((rr, cc))
                    if valid:
                        for pr, pc in positions:
                            density[pr][pc] += 1

    # Select unknown cell with maximum density, random among ties
    max_d = -1
    hunt_candidates = []
    for r, c in unknowns:
        d = density[r][c]
        if d > max_d:
            max_d = d
            hunt_candidates = [(r, c)]
        elif d == max_d:
            hunt_candidates.append((r, c))

    return random.choice(hunt_candidates)
