
import numpy as np
from functools import lru_cache
import math
import time

DIRS_8 = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
DIRS_8_RAYS = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]

def policy(board) -> str:
    b = np.array(board, dtype=int)
    n = 8
    me = 1
    opp = -1

    my_positions = list(zip(*np.where(b == me)))
    if not my_positions:
        return "0,0:0,0"  # shouldn't happen

    # ---------- helpers ----------
    def in_bounds(r,c):
        return 0 <= r < n and 0 <= c < n

    def count_pieces_on_line(r, c, dr, dc):
        # count all pieces (me+opp) on the line including (r,c)
        # walk to edge then traverse
        rr, cc = r, c
        while in_bounds(rr-dr, cc-dc):
            rr -= dr
            cc -= dc
        cnt = 0
        while in_bounds(rr, cc):
            if b[rr, cc] != 0:
                cnt += 1
            rr += dr
            cc += dc
        return cnt

    def line_squares(r, c, dr, dc):
        # squares on that line from edge to edge
        rr, cc = r, c
        while in_bounds(rr-dr, cc-dc):
            rr -= dr
            cc -= dc
        squares = []
        while in_bounds(rr, cc):
            squares.append((rr, cc))
            rr += dr
            cc += dc
        return squares

    def can_move_piece(r, c, dr, dc):
        # LoA: move exactly as many squares as total pieces on that line.
        steps = count_pieces_on_line(r, c, dr, dc)
        if steps <= 0:
            return None
        tr, tc = r + dr*steps, c + dc*steps
        if not in_bounds(tr, tc):
            return None

        # Determine squares between start and target (excluding ends)
        # Jumping rules: may jump over friendly but not over enemy.
        cr, cc = r + dr, c + dc
        while (cr, cc) != (tr, tc):
            if b[cr, cc] == opp:
                return None
            cr += dr
            cc += dc

        # Landing allowed if empty or enemy; cannot land on friendly
        if b[tr, tc] == me:
            return None
        return (r, c, tr, tc)

    def generate_legal_moves():
        moves = []
        for (r, c) in my_positions:
            for dr, dc in DIRS_8_RAYS:
                mv = can_move_piece(r, c, dr, dc)
                if mv is not None:
                    moves.append(mv)
        return moves

    def apply_move(bcur, mv):
        r1,c1,r2,c2 = mv
        b2 = bcur.copy()
        b2[r1,c1] = 0
        # capture if enemy present
        b2[r2,c2] = me
        return b2

    def largest_component_size(bcur):
        # connectivity in 8 directions among my pieces
        seen = np.zeros((n,n), dtype=bool)
        best = 0
        for (r,c) in zip(*np.where(bcur == me)):
            if seen[r,c]:
                continue
            # BFS/DFS
            stack = [(r,c)]
            seen[r,c] = True
            comp = 0
            while stack:
                rr, cc = stack.pop()
                comp += 1
                for dr, dc in DIRS_8:
                    nr, nc = rr+dr, cc+dc
                    if in_bounds(nr,nc) and not seen[nr,nc] and bcur[nr,nc] == me:
                        seen[nr,nc] = True
                        stack.append((nr,nc))
            best = max(best, comp)
        return best

    def components(bcur):
        # return list of component node lists
        seen = np.zeros((n,n), dtype=bool)
        comps = []
        for (r,c) in zip(*np.where(bcur == me)):
            if seen[r,c]:
                continue
            stack = [(r,c)]
            seen[r,c] = True
            comp = [(r,c)]
            while stack:
                rr, cc = stack.pop()
                for dr, dc in DIRS_8:
                    nr, nc = rr+dr, cc+dc
                    if in_bounds(nr,nc) and not seen[nr,nc] and bcur[nr,nc] == me:
                        seen[nr,nc] = True
                        stack.append((nr,nc))
                        comp.append((nr,nc))
            comps.append(comp)
        return comps

    def heuristic(bcur):
        # winning condition: all connected
        comps = components(bcur)
        comp_sizes = [len(c) for c in comps]
        largest = max(comp_sizes) if comp_sizes else 0
        total = len(comp_sizes)
        my_total = np.count_nonzero(bcur == me)

        # connectivity score
        if largest == my_total and my_total > 0:
            return 1e9

        # Use closeness between components: sum of minimum Chebyshev distances between component pairs
        # Chebyshev distance promotes diagonal/orth adjacency merging in 8-neighborhood.
        # To keep it fast, compute nearest pair distance from each comp to others.
        min_bridge = 0
        if len(comps) >= 2:
            # pick representative points efficiently: take all points but capped by size
            capped = []
            for comp in comps:
                if len(comp) <= 8:
                    capped.append(comp)
                else:
                    # subsample to reduce cost
                    step = max(1, len(comp)//8)
                    capped.append(comp[::step])
            # compute minimum distance between any points across components
            best_dists = []
            for i in range(len(comps)):
                for j in range(i+1, len(comps)):
                    dmin = 99
                    for (r1,c1) in capped[i]:
                        # early pruning: best possible is 0 adjacency merge (overlap impossible)
                        for (r2,c2) in capped[j]:
                            d = max(abs(r1-r2), abs(c1-c2))
                            if d < dmin:
                                dmin = d
                                if dmin <= 1:
                                    break
                        if dmin <= 1:
                            break
                    best_dists.append(dmin)
            if best_dists:
                min_bridge = min(best_dists)
        else:
            min_bridge = 7

        # centralization: reward staying near center slightly
        center = 3.5
        center_score = 0.0
        for (r,c) in zip(*np.where(bcur == me)):
            center_score += - (abs(r-center) + abs(c-center))

        # capturing info (approx): compare piece count difference
        # If we captured, opponent count decreases.
        opp_count = np.count_nonzero(bcur == opp)

        # Final weighted score: maximize connectivity and bridge closeness.
        # Encourage fewer components and larger largest component.
        score = 0.0
        score += 50.0 * largest
        score += -20.0 * (total-1)  # fewer components better
        score += -8.0 * min_bridge  # smaller distance to merge better
        score += 0.5 * center_score
        # capturing: fewer opponent pieces is usually good
        score += 2.0 * (np.count_nonzero(b == opp) - opp_count)
        return score

    # ---------- main move selection ----------
    # Time budget
    t0 = time.time()
    moves = generate_legal_moves()
    if not moves:
        # No legal move found; fallback safe-ish
        return "0,0:0,0"

    best_mv = moves[0]
    best_sc = -1e18

    # Optional light lookahead (1 ply) for tie-breaking
    # Keep it cheap: evaluate resulting positions only.
    # Slightly sort by immediate capture to improve quality.
    def immediate_capture(mv):
        r1,c1,r2,c2 = mv
        return b[r2,c2] == opp

    moves_sorted = sorted(moves, key=lambda mv: (not immediate_capture(mv)), reverse=False)
    # Put captures first
    moves_sorted = sorted(moves, key=lambda mv: (0 if immediate_capture(mv) else 1))

    for mv in moves_sorted:
        if time.time() - t0 > 0.85:
            break
        b2 = apply_move(b, mv)
        sc = heuristic(b2)
        # quick improvement: also ensure not making connectivity worse too much
        # (use largest component delta)
        l0 = largest_component_size(b)
        l1 = largest_component_size(b2)
        sc += 3.0 * (l1 - l0)
        if sc > best_sc:
            best_sc = sc
            best_mv = mv

    r1,c1,r2,c2 = best_mv
    return f"{r1},{c1}:{r2},{c2}"
