
import random
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Battleship policy for a 10x10 board.
    board values: 0 unknown, -1 miss, 1 hit.
    Returns next move (row, col) with board[row][col] == 0.
    """
    N = 10

    # Remaining fleet in standard challenge rules
    # (Lengths: 5,4,3,3,2). We will treat ships as indistinguishable segments.
    fleet = [5, 4, 3, 3, 2]

    # Collect known hits to steer reasoning
    hits = [(r, c) for r in range(N) for c in range(N) if board[r][c] == 1]
    misses = {(r, c) for r in range(N) for c in range(N) if board[r][c] == -1}

    # Helper: generate all placements for a ship length that are consistent
    # with misses and hits.
    def compute_heatmap() -> List[List[int]]:
        heat = [[0] * N for _ in range(N)]

        # To prune: if we have hits, any valid placement must cover all hits
        # inconsistently? Not all hits are necessarily in same ship,
        # but a placement must not conflict: it must not include a miss,
        # and if it includes any hit then it's fine. If it includes misses it's invalid.
        #
        # We’ll simply require: placement cells contain no misses, and it covers
        # only hit/unknown cells.
        #
        # Additionally, to increase exploitation when hits exist, we can slightly
        # reward placements that cover at least one existing hit (but still compute
        # full consistency probabilities).
        cover_hit_bonus = 3 if hits else 1

        for L in fleet:
            # Horizontal placements
            for r in range(N):
                for c0 in range(N - L + 1):
                    cells = [(r, c0 + k) for k in range(L)]
                    ok = True
                    contains_hit = False
                    for (rr, cc) in cells:
                        if board[rr][cc] == -1:
                            ok = False
                            break
                        if board[rr][cc] == 1:
                            contains_hit = True
                    if not ok:
                        continue
                    weight = cover_hit_bonus if contains_hit else 1
                    for rr, cc in cells:
                        if board[rr][cc] == 0:
                            heat[rr][cc] += weight

            # Vertical placements
            for c in range(N):
                for r0 in range(N - L + 1):
                    cells = [(r0 + k, c) for k in range(L)]
                    ok = True
                    contains_hit = False
                    for (rr, cc) in cells:
                        if board[rr][cc] == -1:
                            ok = False
                            break
                        if board[rr][cc] == 1:
                            contains_hit = True
                    if not ok:
                        continue
                    weight = cover_hit_bonus if contains_hit else 1
                    for rr, cc in cells:
                        if board[rr][cc] == 0:
                            heat[rr][cc] += weight

        return heat

    heat = compute_heatmap()

    # Choose best legal move
    best_val = -1
    best_moves = []
    for r in range(N):
        for c in range(N):
            if board[r][c] == 0:
                v = heat[r][c]
                if v > best_val:
                    best_val = v
                    best_moves = [(r, c)]
                elif v == best_val:
                    best_moves.append((r, c))

    # Tie-break: add a small preference for moves adjacent to hits (in case heat is tied)
    if best_moves and hits:
        hit_set = set(hits)
        def adj_score(move):
            r, c = move
            s = 0
            for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
                if (r+dr, c+dc) in hit_set:
                    s += 2
            return s

        max_s = max(adj_score(m) for m in best_moves)
        best_moves2 = [m for m in best_moves if adj_score(m) == max_s]
        return random.choice(best_moves2)

    return random.choice(best_moves) if best_moves else (0, 0)
