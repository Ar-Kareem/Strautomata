
import numpy as np
import time

# edge indexing: 0..19 horizontal, 20..39 vertical
# h(r,c) r0-4 c0-3 -> r*4+c
# v(r,c) r0-3 c0-4 -> 20+r*5+c
def _h_idx(r, c):
    return r * 4 + c

def _v_idx(r, c):
    return 20 + r * 5 + c

_BOX_MASK = []
_EDGE_TO_BOXES = [[] for _ in range(40)]
_IDX_TO_MOVE = {}
for _r in range(4):
    for _c in range(4):
        _b = _r * 4 + _c
        _top = _h_idx(_r, _c)
        _bot = _h_idx(_r + 1, _c)
        _lef = _v_idx(_r, _c)
        _rig = _v_idx(_r, _c + 1)
        _m = (1 << _top) | (1 << _bot) | (1 << _lef) | (1 << _rig)
        _BOX_MASK.append(_m)
        for _e in (_top, _bot, _lef, _rig):
            _EDGE_TO_BOXES[_e].append(_b)

for _i in range(20):
    _rr = _i // 4
    _cc = _i % 4
    _IDX_TO_MOVE[_i] = (_rr, _cc, 'H')
for _t in range(20):
    _idx = 20 + _t
    _rr = _t // 5
    _cc = _t % 5
    _IDX_TO_MOVE[_idx] = (_rr, _cc, 'V')

def _move_to_idx(r, c, d):
    if d == 'H':
        return _h_idx(r, c)
    else:
        return _v_idx(r, c)


def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    try:
        return _policy_inner(horizontal, vertical, capture)
    except Exception:
        pass
    # absolute fallback: first zero found
    try:
        h = np.asarray(horizontal)
        v = np.asarray(vertical)
        for r in range(5):
            for c in range(5):
                if r <= 4 and c <= 3 and h[r, c] == 0:
                    return f"{r},{c},H"
        for r in range(5):
            for c in range(5):
                if r <= 3 and c <= 4 and v[r, c] == 0:
                    return f"{r},{c},V"
        # include padding if needed
        for r in range(5):
            for c in range(5):
                if h[r, c] == 0:
                    rr = r
                    cc = c if c <= 3 else 3
                    if h[rr, cc] == 0:
                        return f"{rr},{cc},H"
                if v[r, c] == 0:
                    rr = r if r <= 3 else 3
                    cc = c
                    if v[rr, cc] == 0:
                        return f"{rr},{cc},V"
    except Exception:
        pass
    return "0,0,H"


def _policy_inner(horizontal, vertical, capture):
    h = np.asarray(horizontal)
    v = np.asarray(vertical)
    cap = np.asarray(capture)

    # legal moves in valid ranges
    legal = []  # list of (r,c,d,idx)
    for r in range(5):
        for c in range(4):
            try:
                if h[r, c] == 0:
                    legal.append((r, c, 'H', _h_idx(r, c)))
            except Exception:
                continue
    for r in range(4):
        for c in range(5):
            try:
                if v[r, c] == 0:
                    legal.append((r, c, 'V', _v_idx(r, c)))
            except Exception:
                continue
    if len(legal) == 0:
        # try padding
        for r in range(5):
            for c in range(5):
                if h[r, c] == 0:
                    return f"{r},{min(c,3)},H"
                if v[r, c] == 0:
                    return f"{min(r,3)},{c},V"
        return "0,0,H"
    if len(legal) == 1:
        r, c, d, _ = legal[0]
        return f"{r},{c},{d}"

    # box sides for unclaimed boxes (only 4x4)
    # sides[r,c] = -1 if claimed else 0..3
    sides = [[0]*4 for _ in range(4)]
    claimed_bool = [[False]*4 for _ in range(4)]
    for r in range(4):
        for c in range(4):
            cv = 0
            try:
                cv = int(cap[r, c])
            except Exception:
                cv = 0
            if cv != 0:
                claimed_bool[r][c] = True
                sides[r][c] = -1
            else:
                s = 0
                if h[r, c] != 0:
                    s += 1
                if h[r+1, c] != 0:
                    s += 1
                if v[r, c] != 0:
                    s += 1
                if v[r, c+1] != 0:
                    s += 1
                sides[r][c] = s

    def boxes_adjacent(r, c, d):
        if d == 'H':
            # edge h[r,c], boxes above (r-1,c) and below (r,c)
            res = []
            if r-1 >= 0 and r-1 < 4 and c < 4:
                if not claimed_bool[r-1][c]:
                    res.append((r-1, c))
            if r >= 0 and r < 4 and c < 4:
                if not claimed_bool[r][c]:
                    res.append((r, c))
            return res
        else:
            res = []
            if c-1 >= 0 and c-1 < 4 and r < 4:
                if not claimed_bool[r][c-1]:
                    res.append((r, c-1))
            if c >= 0 and c < 4 and r < 4:
                if not claimed_bool[r][c]:
                    res.append((r, c))
            return res

    # classify moves
    cap_moves = []  # (k, r,c,d,idx)
    safe_moves = []
    risky_moves = []
    for (r, c, d, idx) in legal:
        adj = boxes_adjacent(r, c, d)
        k = 0
        creates_three = False
        for (br, bc) in adj:
            s = sides[br][bc]
            if s == 3:
                k += 1
            if s == 2:
                creates_three = True
        if k > 0:
            cap_moves.append((k, r, c, d, idx, adj))
        elif creates_three:
            risky_moves.append((r, c, d, idx, adj))
        else:
            safe_moves.append((r, c, d, idx, adj))

    empty_n = len(legal)

    # ---------- exhaustive solver for endgame ----------
    SEARCH_LIMIT = 13
    # use solver if small enough
    if len(cap_moves) > 0 and empty_n <= SEARCH_LIMIT:
        mv = _solve_endgame(h, v, cap, legal)
        if mv is not None:
            return mv
    if len(cap_moves) == 0 and empty_n <= 12:
        # safe or loony but small: solve exactly
        mv = _solve_endgame(h, v, cap, legal)
        if mv is not None:
            return mv

    # ---------- capture greedy ----------
    if len(cap_moves) > 0:
        # prefer 2-box, then move that touches most-filled neighbours
        best = None
        best_key = None
        for (k, r, c, d, idx, adj) in cap_moves:
            neigh_sum = 0
            for (br, bc) in adj:
                neigh_sum += sides[br][bc]
            # also consider other neighbour boxes that would become 3 after?
            # approximate future chain extension: sum sides of boxes adjacent to completed boxes
            key = (k, neigh_sum)
            if best_key is None or key > best_key:
                best_key = key
                best = (r, c, d)
        return f"{best[0]},{best[1]},{best[2]}"

    # ---------- safe moves heuristic ----------
    if len(safe_moves) > 0:
        best = None
        best_key = None
        for (r, c, d, idx, adj) in safe_moves:
            # penalty: how many become 2
            cnt2 = 0
            sum_after = 0
            max_after = 0
            for (br, bc) in adj:
                sa = sides[br][bc] + 1
                sum_after += sa
                if sa > max_after:
                    max_after = sa
                if sa == 2:
                    cnt2 += 1
            # prefer fewer 2s, smaller sum, prefer outer (fewer adj) slightly?
            # key to minimize: (cnt2, sum_after, max_after)
            # use negative for max comparison
            key = (cnt2, sum_after, max_after, len(adj))
            if best_key is None or key < best_key:
                best_key = key
                best = (r, c, d)
        return f"{best[0]},{best[1]},{best[2]}"

    # ---------- loony: must give away, minimize opponent chain ----------
    # estimate greedy take for each risky move
    # simulate sides copy
    best = None
    best_key = None
    for (r, c, d, idx, adj) in risky_moves:
        # immediate giveaway count
        give = 0
        for (br, bc) in adj:
            if sides[br][bc] == 2:
                give += 1
        # estimate chain opponent will get via greedy simulation
        # copy sides dict
        sim_sides = [row[:] for row in sides]
        # apply move: increment adj boxes
        for (br, bc) in adj:
            sim_sides[br][bc] += 1
        # mark edge as drawn for simulation? need to track which edges drawn to know future adjacency?
        # approximate: repeatedly take any box with 3 sides, increment its neighbours that share empty edge.
        # To do accurately we need edge occupancy. Build occupancy sets.
        # Simpler: flood estimate using sides only + adjacency via shared edges that are still empty.
        # Build empty set
        # For speed, do full board simulation with occupancy arrays
        est = _estimate_opponent_take(h, v, claimed_bool, sim_sides, r, c, d)
        key = (est, give)
        if best_key is None or key < best_key:
            best_key = key
            best = (r, c, d)
    if best is not None:
        return f"{best[0]},{best[1]},{best[2]}"

    # fallback
    r, c, d, _ = legal[0]
    return f"{r},{c},{d}"


def _estimate_opponent_take(h, v, claimed_bool, sim_sides_after, mr, mc, md):
    # Build occupancy boolean for valid edges
    # h_occ 5x4, v_occ 4x5
    import copy
    h_occ = [[False]*4 for _ in range(5)]
    v_occ = [[False]*5 for _ in range(4)]
    for r in range(5):
        for c in range(4):
            h_occ[r][c] = (h[r, c] != 0)
    for r in range(4):
        for c in range(5):
            v_occ[r][c] = (v[r, c] != 0)
    # apply our move
    if md == 'H':
        h_occ[mr][mc] = True
    else:
        v_occ[mr][mc] = True
    claimed = [row[:] for row in claimed_bool]
    s = [row[:] for row in sim_sides_after]
    # boxes remaining
    total_take = 0
    # greedy loop: find box with 3 sides unclaimed, take it, update neighbours
    # To update neighbours correctly, when we take a box we must fill its remaining empty edge(s)?
    # A 3-sided box has exactly one empty edge; taking it fills that edge.
    # Find that edge and mark occupied, increment neighbour box sides.
    for _iter in range(30):
        found = None
        for br in range(4):
            for bc in range(4):
                if not claimed[br][bc] and s[br][bc] == 3:
                    found = (br, bc)
                    break
            if found is not None:
                break
        if found is None:
            break
        br, bc = found
        # find empty edge of this box
        # top
        empt = None
        if not h_occ[br][bc]:
            empt = ('H', br, bc)
        elif not h_occ[br+1][bc]:
            empt = ('H', br+1, bc)
        elif not v_occ[br][bc]:
            empt = ('V', br, bc)
        elif not v_occ[br][bc+1]:
            empt = ('V', br, bc+1)
        else:
            # should not happen (4 sides but not claimed?) treat as taken
            claimed[br][bc] = True
            total_take += 1
            continue
        # fill it
        if empt[0] == 'H':
            h_occ[empt[1]][empt[2]] = True
        else:
            v_occ[empt[1]][empt[2]] = True
        # this box now 4 sides -> claimed by opponent
        s[br][bc] = 4
        claimed[br][bc] = True
        total_take += 1
        # update neighbour sharing this edge
        er, ec, ed = empt[1], empt[2], empt[0]
        neigh = None
        if ed == 'H':
            if er-1 >= 0 and er-1 < 4:
                if not claimed[er-1][ec]:
                    # box (er-1,ec) shares bottom edge
                    s[er-1][ec] += 1
            if er >= 0 and er < 4:
                # avoid double counting the box we just took
                if not (er == br and ec == bc):
                    if not claimed[er][ec]:
                        s[er][ec] += 1
        else:
            if ec-1 >= 0 and ec-1 < 4:
                if not (er == br and ec-1 == bc):
                    if not claimed[er][ec-1]:
                        s[er][ec-1] += 1
                elif False:
                    pass
            # the two boxes sharing vertical edge: (er,ec-1) and (er,ec)
            # we already handled one? handle both generically:
            # Actually above double counts; redo cleanly:
            pass
        # The above neighbour update double counts / misses; do clean recompute of increment for the other box:
        # Determine the other box sharing empt edge (different from found)
        other = None
        if ed == 'H':
            if er-1 == br and ec == bc:
                # found is above, other is below
                if er < 4 and not claimed[er][ec]:
                    # already incremented? we incremented both above; need to avoid double.
                    pass
            # To avoid bug, revert and do correctly: we incremented both boxes including found (which is now 4).
            # Found was incremented? No, we set found to 4 directly, but neighbour increments above added +1 to found's neighbours only?
            # Let's correct: the loops above skip claimed boxes, found is now claimed, so it was not incremented. Good.
            # But for H edge, the two adjacent boxes are (er-1,ec) and (er,ec). One is found, other got +1. Our code added +1 to both non-claimed among them, which is exactly the other. Good.
            pass
        else:
            # V edge: boxes (er,ec-1) and (er,ec)
            # Our code above only handled (er,ec-1) partially; need to handle (er,ec) too.
            # Add missing:
            if not claimed[er][ec] if ec < 4 and er < 4 else False:
                # if this box is not the found one, it needs +1, but if our earlier code didn't add it, add now
                # Check if we already added: earlier code for V only added (er,ec-1). So add (er,ec).
                if not (er == br and ec == bc):
                    # check if edge is indeed shared: V edge (er,ec) is left edge of box (er,ec) when ec<4 and right edge of (er,ec-1)
                    # It is shared, so increment
                    # But need to ensure we didn't already increment via the generic? We didn't.
                    s[er][ec] += 1 if ec < 4 else 0
                # Note: if found is (er,ec-1), then other is (er,ec) -> incremented here. If found is (er,ec), other is (er,ec-1) already incremented above. Good.
                pass
            # Also need to handle case where ec==... edge on border has only one neighbour (already handled)
            pass
    return total_take


def _solve_endgame(h, v, cap, legal):
    # build bitboards
    occ = 0
    for (r, c, d, idx) in legal:
        pass
    # occupied bits
    for r in range(5):
        for c in range(4):
            if h[r, c] != 0:
                occ |= (1 << _h_idx(r, c))
    for r in range(4):
        for c in range(5):
            if v[r, c] != 0:
                occ |= (1 << _v_idx(r, c))
    claimed_mask = 0
    for r in range(4):
        for c in range(4):
            try:
                if int(cap[r, c]) != 0:
                    claimed_mask |= (1 << (r*4+c))
            except Exception:
                pass
    empty_idxs = [_move_to_idx(r, c, d) for (r, c, d, _) in [(x[0], x[1], x[2]) for x in legal]]
    # order root moves: captures first
    def completions(idx, oc, cl):
        k = 0
        for b in _EDGE_TO_BOXES[idx]:
            if (cl >> b) & 1:
                continue
            if (oc | (1 << idx)) & _BOX_MASK[b] == _BOX_MASK[b]:
                # also need that before move it wasn't already complete (it can't be because edge was empty)
                k += 1
        return k
    # sort
    scored = []
    for (r, c, d, idx) in legal:
        k = completions(idx, occ, claimed_mask)
        scored.append(( -k, idx, r, c, d))
    scored.sort()
    ordered = [(r, c, d, idx) for (_, idx, r, c, d) in scored]

    deadline = time.time() + 0.85
    memo = {}
    nodes = [0]

    import sys
    sys.setrecursionlimit(10000)

    def dfs(oc, cl, alpha, beta):
        nodes[0] += 1
        if nodes[0] % 2048 == 0 and time.time() > deadline:
            raise TimeoutError()
        # find empties
        # quick terminal check: all boxes claimed or no empty?
        # compute empty list
        # if no empty edge -> 0
        # we can check by counting bits: if oc has all 40 bits -> 0
        # else generate
        # memo
        key = (oc, cl)
        if key in memo:
            return memo[key]
        # generate moves
        # collect empty idxs
        empt = []
        # unrolled loop over 40
        for i in range(40):
            if not (oc >> i) & 1:
                empt.append(i)
        if not empt:
            return 0
        # order: captures first
        # compute k for each to order
        tmp = []
        for i in empt:
            kk = 0
            for b in _EDGE_TO_BOXES[i]:
                if (cl >> b) & 1:
                    continue
                if (oc | (1 << i)) & _BOX_MASK[b] == _BOX_MASK[b]:
                    kk += 1
            tmp.append(( -kk, i))
        tmp.sort()
        best = -1000
        exact = True
        for _, i in tmp:
            # compute new state
            noc = oc | (1 << i)
            ncl = cl
            kk = 0
            for b in _EDGE_TO_BOXES[i]:
                if (cl >> b) & 1:
                    continue
                if noc & _BOX_MASK[b] == _BOX_MASK[b]:
                    kk += 1
                    ncl |= (1 << b)
            if kk > 0:
                # same player again: value = kk + child
                try:
                    child = dfs(noc, ncl, alpha - kk, beta - kk)
                except TimeoutError:
                    raise
                val = kk + child
            else:
                try:
                    child = dfs(noc, ncl, -beta, -alpha)
                except TimeoutError:
                    raise
                val = -child
            if val > best:
                best = val
            if best >= beta:
                exact = False
                break
            if best > alpha:
                alpha = best
        if exact:
            memo[key] = best
        return best

    best_val = -1000
    best_move = None
    alpha_root = -100
    beta_root = 100
    try:
        for (r, c, d, idx) in ordered:
            noc = occ | (1 << idx)
            ncl = claimed_mask
            kk = 0
            for b in _EDGE_TO_BOXES[idx]:
                if (claimed_mask >> b) & 1:
                    continue
                if noc & _BOX_MASK[b] == _BOX_MASK[b]:
                    kk += 1
                    ncl |= (1 << b)
            if kk > 0:
                child = dfs(noc, ncl, alpha_root - kk, beta_root - kk)
                val = kk + child
            else:
                child = dfs(noc, ncl, -beta_root, -alpha_root)
                val = -child
            if best_move is None or val > best_val:
                best_val = val
                best_move = (r, c, d)
            if val > alpha_root:
                alpha_root = val
    except TimeoutError:
        pass
    if best_move is None:
        return None
    return f"{best_move[0]},{best_move[1]},{best_move[2]}"
