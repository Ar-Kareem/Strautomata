
import numpy as np
import random

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # --------------------------------------------------------------
    #  Dots‑and‑Boxes policy for a 4×4 box grid (5×5 dot grid)
    # --------------------------------------------------------------
    N = 4                     # boxes per side
    # ----- helper: count drawn edges for a box (r,c) -----------------
    def box_edge_count(h, v, r, c):
        top = h[r, c] != 0
        bottom = h[r + 1, c] != 0
        left = v[r, c] != 0
        right = v[r, c + 1] != 0
        return top + bottom + left + right

    # ----- helper: dangerous boxes after a move ----------------------
    def dangerous(r, c, dir_):
        """Number of boxes that would become three‑sided after this edge."""
        d = 0
        if dir_ == 'H':
            # top box
            if r > 0 and capture[r - 1, c] == 0:
                cur = box_edge_count(horizontal, vertical, r - 1, c)
                if cur + 1 == 3:
                    d += 1
            # bottom box
            if r < N and capture[r, c] == 0:
                cur = box_edge_count(horizontal, vertical, r, c)
                if cur + 1 == 3:
                    d += 1
        else:  # 'V'
            # left box
            if c > 0 and capture[r, c - 1] == 0:
                cur = box_edge_count(horizontal, vertical, r, c - 1)
                if cur + 1 == 3:
                    d += 1
            # right box
            if c < N and capture[r, c] == 0:
                cur = box_edge_count(horizontal, vertical, r, c)
                if cur + 1 == 3:
                    d += 1
        return d

    # ----- helper: simulate a whole turn (including forced captures) -----
    def simulate_turn(move):
        """Return total number of boxes captured in this turn if *move* is played."""
        h = horizontal.copy()
        v = vertical.copy()
        # boxes already captured before this turn
        captured = { (r, c) for r in range(N) for c in range(N) if capture[r, c] != 0 }
        total = 0

        # apply the initial edge
        r, c, dir_ = move
        if dir_ == 'H':
            h[r, c] = 1
        else:
            v[r, c] = 1

        # keep capturing while there are three‑sided boxes
        while True:
            # recompute box edge counts
            top = h[0:N, 0:N] != 0
            bottom = h[1:N + 1, 0:N] != 0
            left = v[0:N, 0:N] != 0
            right = v[0:N, 1:N + 1] != 0
            counts = top + bottom + left + right

            # capture any box that just became complete and is still free
            new_captured = []
            for br in range(N):
                for bc in range(N):
                    if (br, bc) not in captured and counts[br, bc] == 4:
                        new_captured.append((br, bc))
            if new_captured:
                for box in new_captured:
                    captured.add(box)
                    total += 1
                # a new capture does not change edge counts, but we may still have
                # three‑sided boxes that were not captured yet → keep looping
                continue

            # no new captures – look for three‑sided boxes and fill their missing edge
            edge_weight = {}   # (r,c,dir) -> how many three‑sided boxes it closes
            for br in range(N):
                for bc in range(N):
                    if (br, bc) in captured:
                        continue
                    if counts[br, bc] == 3:
                        # determine which of the four edges is still empty
                        if h[br, bc] == 0:
                            edge = (br, bc, 'H')
                        elif h[br + 1, bc] == 0:
                            edge = (br + 1, bc, 'H')
                        elif v[br, bc] == 0:
                            edge = (br, bc, 'V')
                        elif v[br, bc + 1] == 0:
                            edge = (br, bc + 1, 'V')
                        else:
                            continue   # should not happen
                        edge_weight[edge] = edge_weight.get(edge, 0) + 1

            if not edge_weight:                # no three‑sided box left → turn ends
                break

            # pick the edge that closes the most boxes (greedy)
            best_edge, _ = max(edge_weight.items(), key=lambda kv: kv[1])
            er, ec, edir = best_edge
            if edir == 'H':
                h[er, ec] = 1
            else:
                v[er, ec] = 1
            # after drawing the edge the loop will capture any newly completed boxes

        return total

    # ----- generate all legal moves ---------------------------------
    moves = []                                           # (r, c, dir, captured, dangerous)
    # horizontal edges: rows 0..4, cols 0..3
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] == 0:
                d = dangerous(r, c, 'H')
                cap = simulate_turn((r, c, 'H'))
                moves.append((r, c, 'H', cap, d))
    # vertical edges: rows 0..3, cols 0..4
    for r in range(4):
        for c in range(5):
            if vertical[r, c] == 0:
                d = dangerous(r, c, 'V')
                cap = simulate_turn((r, c, 'V'))
                moves.append((r, c, 'V', cap, d))

    # ----- select the best move ------------------------------------
    # split moves into three categories
    capture_moves  = [m for m in moves if m[3] > 0]               # captures something
    safe_moves     = [m for m in moves if m[3] == 0 and m[4] == 0]  # creates no three‑sided box
    dangerous_moves = [m for m in moves if m[3] == 0 and m[4] > 0]  # opens at least one box

    chosen = None
    if capture_moves:
        # prefer the move that captures the most boxes; tie‑break by fewest dangerous boxes
        max_cap = max(m[3] for m in capture_moves)
        best = [m for m in capture_moves if m[3] == max_cap]
        min_dang = min(m[4] for m in best)
        best = [m for m in best if m[4] == min_dang]
        chosen = random.choice(best)
    elif safe_moves:
        # among safe moves we could look at a secondary heuristic,
        # but a random safe move already works well on a 4×4 board
        chosen = random.choice(safe_moves)
    else:
        # forced to give the opponent boxes – give the smallest chain
        min_dang = min(m[4] for m in dangerous_moves)
        best = [m for m in dangerous_moves if m[4] == min_dang]
        chosen = random.choice(best)

    # produce the required string "row,col,dir"
    r, c, dir_, _, _ = chosen
    return f"{r},{c},{dir_}"
