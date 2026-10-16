import random
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Targeting policy for Battleship-like game on 10x10 grid.

    Input:
      board: 10x10 list of lists with values:
        0 = unknown, -1 = miss, 1 = hit

    Returns:
      (row, col) of a previously unshot cell (board[row][col] == 0)
    """
    N = 10
    ship_lengths = [5, 4, 3, 3, 2]

    # Convert to simple references
    def is_unknown(r, c): return board[r][c] == 0
    def is_miss(r, c): return board[r][c] == -1
    def is_hit(r, c): return board[r][c] == 1

    # Collect hit coordinates
    hits = [(r, c) for r in range(N) for c in range(N) if is_hit(r, c)]
    any_hits = len(hits) > 0

    # Heatmap counts for each unknown cell
    heat = [[0.0 for _ in range(N)] for _ in range(N)]

    # Enumerate all placements for each ship length and accumulate
    for L in ship_lengths:
        # Horizontal placements
        for r in range(N):
            for c0 in range(N - L + 1):
                placement_cells = [(r, c0 + i) for i in range(L)]
                # Skip if placement overlaps a miss
                if any(is_miss(rr, cc) for rr, cc in placement_cells):
                    continue
                # Count how many hits this placement covers
                hits_in_placement = sum(1 for rr, cc in placement_cells if is_hit(rr, cc))
                # If there are hits on the board but this placement covers none, it's less relevant
                # Reward placements that cover hits strongly
                if any_hits:
                    weight = 1 + 20 * hits_in_placement
                    # Extra boost if placement covers multiple hits (likely continuation)
                    if hits_in_placement > 1:
                        weight += 30 * (hits_in_placement - 1)
                else:
                    weight = 1.0
                # Add weight to unknown cells within this placement
                for rr, cc in placement_cells:
                    if is_unknown(rr, cc):
                        heat[rr][cc] += weight

        # Vertical placements
        for c in range(N):
            for r0 in range(N - L + 1):
                placement_cells = [(r0 + i, c) for i in range(L)]
                if any(is_miss(rr, cc) for rr, cc in placement_cells):
                    continue
                hits_in_placement = sum(1 for rr, cc in placement_cells if is_hit(rr, cc))
                if any_hits:
                    weight = 1 + 20 * hits_in_placement
                    if hits_in_placement > 1:
                        weight += 30 * (hits_in_placement - 1)
                else:
                    weight = 1.0
                for rr, cc in placement_cells:
                    if is_unknown(rr, cc):
                        heat[rr][cc] += weight

    # If we found no placement contributions (rare), fall back to adjacency to hits or parity/random
    candidates = []
    max_score = -1.0
    for r in range(N):
        for c in range(N):
            if not is_unknown(r, c):
                continue
            score = heat[r][c]
            if score > max_score:
                max_score = score
                candidates = [(r, c)]
            elif score == max_score:
                candidates.append((r, c))

    # If heatmap produced no signal (all zeros), try simple targeting near hits
    if max_score <= 0 or not candidates:
        if any_hits:
            # Try unknown neighbors of hits first
            neighs = []
            for r, c in hits:
                for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < N and 0 <= cc < N and is_unknown(rr, cc):
                        neighs.append((rr, cc))
            if neighs:
                return random.choice(neighs)
        # Otherwise choose a parity-based hunt (checkerboard on mod 2)
        parity_cells = [(r, c) for r in range(N) for c in range(N) if is_unknown(r, c) and ((r + c) % 2 == 0)]
        if parity_cells:
            return random.choice(parity_cells)
        # As ultimate fallback choose any unknown
        unknowns = [(r, c) for r in range(N) for c in range(N) if is_unknown(r, c)]
        if unknowns:
            return random.choice(unknowns)

    # If we have candidates from heatmap, pick randomly among the best
    return random.choice(candidates)