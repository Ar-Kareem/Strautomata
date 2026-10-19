
import numpy as np
from functools import lru_cache

# 4x4 boxes: valid horizontal edges are H[r,c] for r=0..4, c=0..3
# valid vertical edges are V[r,c] for r=0..3, c=0..4

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    H = (horizontal != 0)
    V = (vertical != 0)

    def legal_moves():
        ms = []
        for r in range(5):
            for c in range(4):
                if not H[r, c]:
                    ms.append((r, c, 'H'))
        for r in range(4):
            for c in range(5):
                if not V[r, c]:
                    ms.append((r, c, 'V'))
        return ms

    moves = legal_moves()
    if not moves:
        # Should never happen in a non-terminal call, but keep API safe.
        return "0,0,H"

    def box_sides(h, v, br, bc):
        return (
            int(h[br, bc]) +
            int(h[br + 1, bc]) +
            int(v[br, bc]) +
            int(v[br, bc + 1])
        )

    def adjacent_boxes(move):
        r, c, d = move
        bs = []
        if d == 'H':
            if r > 0:
                bs.append((r - 1, c))
            if r < 4:
                bs.append((r, c))
        else:
            if c > 0:
                bs.append((r, c - 1))
            if c < 4:
                bs.append((r, c))
        return bs

    def capture_count_on(h, v, move):
        cnt = 0
        for br, bc in adjacent_boxes(move):
            if box_sides(h, v, br, bc) == 3:
                cnt += 1
        return cnt

    def creates_threes(h, v, move):
        hh = h.copy()
        vv = v.copy()
        r, c, d = move
        if d == 'H':
            hh[r, c] = True
        else:
            vv[r, c] = True

        made = 0
        for br in range(4):
            for bc in range(4):
                s = box_sides(hh, vv, br, bc)
                if s == 3:
                    made += 1
        return made

    def local_risk(h, v, move):
        hh = h.copy()
        vv = v.copy()
        r, c, d = move
        if d == 'H':
            hh[r, c] = True
        else:
            vv[r, c] = True

        risk = 0
        for br, bc in adjacent_boxes(move):
            s = box_sides(hh, vv, br, bc)
            if s == 3:
                risk += 10
            elif s == 2:
                risk += 2
            elif s == 1:
                risk += 1
        return risk

    # ---------- Exact late-game solver ----------
    # Edge indexing:
    # H index: r*4+c, 0..19
    # V index: 20+r*5+c, 20..39

    def build_masks():
        occ = 0
        for r in range(5):
            for c in range(4):
                if H[r, c]:
                    occ |= 1 << (r * 4 + c)
        for r in range(4):
            for c in range(5):
                if V[r, c]:
                    occ |= 1 << (20 + r * 5 + c)
        return occ

    def move_to_idx(m):
        r, c, d = m
        if d == 'H':
            return r * 4 + c
        return 20 + r * 5 + c

    def idx_to_move(i):
        if i < 20:
            return (i // 4, i % 4, 'H')
        j = i - 20
        return (j // 5, j % 5, 'V')

    # Precompute the four edge indices of each box.
    box_edges = []
    for br in range(4):
        for bc in range(4):
            top = br * 4 + bc
            bottom = (br + 1) * 4 + bc
            left = 20 + br * 5 + bc
            right = 20 + br * 5 + (bc + 1)
            box_edges.append((top, bottom, left, right))

    occ0 = build_masks()
    remaining = 40 - int(occ0.bit_count())

    def boxes_completed_by_mask(occ, idx):
        new_occ = occ | (1 << idx)
        got = 0
        for edges in box_edges:
            if not all((occ >> e) & 1 for e in edges):
                if all((new_occ >> e) & 1 for e in edges):
                    got += 1
        return got

    if remaining <= 13:
        @lru_cache(None)
        def solve(occ):
            if occ.bit_count() == 40:
                return 0

            best = -1000

            # Captures first improves pruning-like behavior even without alpha-beta.
            rem_indices = [i for i in range(40) if not ((occ >> i) & 1)]
            rem_indices.sort(key=lambda i: boxes_completed_by_mask(occ, i), reverse=True)

            for i in rem_indices:
                got = boxes_completed_by_mask(occ, i)
                nocc = occ | (1 << i)

                if got:
                    val = got + solve(nocc)      # same player moves again
                else:
                    val = -solve(nocc)           # turn passes

                if val > best:
                    best = val

            return best

        best_i = None
        best_val = -1000
        rem_indices = [i for i in range(40) if not ((occ0 >> i) & 1)]
        rem_indices.sort(key=lambda i: boxes_completed_by_mask(occ0, i), reverse=True)

        for i in rem_indices:
            got = boxes_completed_by_mask(occ0, i)
            nocc = occ0 | (1 << i)
            if got:
                val = got + solve(nocc)
            else:
                val = -solve(nocc)
            if val > best_val:
                best_val = val
                best_i = i

        if best_i is not None:
            r, c, d = idx_to_move(best_i)
            return f"{r},{c},{d}"

    # ---------- Tactical layer ----------

    # 1. Take boxes immediately.
    captures = []
    for m in moves:
        cc = capture_count_on(H, V, m)
        if cc > 0:
            captures.append((cc, m))

    if captures:
        # Prefer double captures, then moves that leave fewer immediate threats.
        captures.sort(
            key=lambda x: (
                x[0],
                -creates_threes_after_capture(H, V, x[1]) if False else 0
            ),
            reverse=True
        )
        best_cc = max(x[0] for x in captures)
        bests = [m for cc, m in captures if cc == best_cc]
        bests.sort(key=lambda m: creates_threes_after_move(H, V, m) if False else 0)
        r, c, d = bests[0]
        return f"{r},{c},{d}"

    # 2. Prefer safe moves: moves that do not create any 3-sided box.
    safe = []
    for m in moves:
        if creates_threes(H, V, m) == 0:
            safe.append(m)

    if safe:
        # Among safe moves, prefer those touching already low-degree boxes.
        safe.sort(key=lambda m: (local_risk(H, V, m), edge_preference(m)))
        r, c, d = safe[0]
        return f"{r},{c},{d}"

    # 3. No safe move: sacrifice as little as possible.
    # Choose the move producing the fewest 3-sided boxes, with mild local-risk tie break.
    moves.sort(key=lambda m: (creates_threes(H, V, m), local_risk(H, V, m), edge_preference(m)))
    r, c, d = moves[0]
    return f"{r},{c},{d}"


def edge_preference(move):
    """
    Small deterministic tie-breaker.
    Prefer outer edges slightly in the opening/midgame because they tend to
    interact with fewer boxes and reduce accidental chain creation.
    """
    r, c, d = move
    if d == 'H':
        outer = 1 if r == 0 or r == 4 else 0
        center_dist = abs(r - 2) + abs(c - 1.5)
    else:
        outer = 1 if c == 0 or c == 4 else 0
        center_dist = abs(r - 1.5) + abs(c - 2)
    return (-outer, center_dist)
