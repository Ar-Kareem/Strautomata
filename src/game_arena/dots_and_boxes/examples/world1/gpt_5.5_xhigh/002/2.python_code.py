
import numpy as np
import time

# 4x4 boxes: 5*4 horizontal edges and 4*5 vertical edges.
_N = 4
_H_COUNT = 20
_V_COUNT = 20
_EDGE_COUNT = 40
_FULL_MASK = (1 << _EDGE_COUNT) - 1


def _hidx(r, c):
    return r * 4 + c


def _vidx(r, c):
    return 20 + r * 5 + c


_EDGE_BITS = [1 << i for i in range(_EDGE_COUNT)]
_IDX_TO_STR = [""] * _EDGE_COUNT
_EDGE_CENTER = [0.0] * _EDGE_COUNT

# Precompute edge strings and a small centrality preference used only for ties.
for r in range(5):
    for c in range(4):
        i = _hidx(r, c)
        _IDX_TO_STR[i] = f"{r},{c},H"
        x, y = c + 0.5, r
        _EDGE_CENTER[i] = 4.0 - (abs(x - 2.0) + abs(y - 2.0)) + (0.25 if 0 < r < 4 else 0.0)

for r in range(4):
    for c in range(5):
        i = _vidx(r, c)
        _IDX_TO_STR[i] = f"{r},{c},V"
        x, y = c, r + 0.5
        _EDGE_CENTER[i] = 4.0 - (abs(x - 2.0) + abs(y - 2.0)) + (0.25 if 0 < c < 4 else 0.0)

_BOX_EDGES = []
_BOX_MASKS = []
_EDGE_TO_BOXES = [[] for _ in range(_EDGE_COUNT)]

for r in range(4):
    for c in range(4):
        b = r * 4 + c
        edges = (_hidx(r, c), _hidx(r + 1, c), _vidx(r, c), _vidx(r, c + 1))
        _BOX_EDGES.append(edges)
        m = 0
        for e in edges:
            m |= _EDGE_BITS[e]
            _EDGE_TO_BOXES[e].append(b)
        _BOX_MASKS.append(m)

# Bounded caches. Values are independent of edge ownership signs; only occupancy matters.
_MAX_TT = 250000
_MAX_COUNT_CACHE = 80000
_MAX_STATIC_CACHE = 80000
_MAX_COMP_CACHE = 50000

_TT = {_FULL_MASK: 0}
_TT_MOVE = {}
_COUNT_CACHE = {}
_STATIC_CACHE = {}
_COMP_CACHE = {}


class _SearchTimeout(Exception):
    pass


class _ApproxTimeout(Exception):
    pass


_SOLVE_NODES = 0


def _mask_from_arrays(horizontal, vertical):
    mask = 0
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] != 0:
                mask |= _EDGE_BITS[_hidx(r, c)]
    for r in range(4):
        for c in range(5):
            if vertical[r, c] != 0:
                mask |= _EDGE_BITS[_vidx(r, c)]
    return mask


def _idx_is_empty(idx, horizontal, vertical):
    if idx < 20:
        r, c = divmod(idx, 4)
        return horizontal[r, c] == 0
    j = idx - 20
    r, c = divmod(j, 5)
    return vertical[r, c] == 0


def _fallback_move(horizontal, vertical):
    # First scan the real 4x4-box-grid edges.
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] == 0:
                return f"{r},{c},H"
    for r in range(4):
        for c in range(5):
            if vertical[r, c] == 0:
                return f"{r},{c},V"

    # If an arena uses every 5x5 array entry as legal, this still gives a legal
    # empty array entry. In a normal game policy should not be called here.
    for r in range(5):
        for c in range(5):
            if horizontal[r, c] == 0:
                return f"{r},{c},H"
    for r in range(5):
        for c in range(5):
            if vertical[r, c] == 0:
                return f"{r},{c},V"

    return "0,0,H"


def _side_counts(mask):
    cached = _COUNT_CACHE.get(mask)
    if cached is not None:
        return cached
    counts = tuple((mask & bm).bit_count() for bm in _BOX_MASKS)
    if len(_COUNT_CACHE) < _MAX_COUNT_CACHE:
        _COUNT_CACHE[mask] = counts
    return counts


def _capture_count(idx, counts):
    total = 0
    for b in _EDGE_TO_BOXES[idx]:
        if counts[b] == 3:
            total += 1
    return total


def _creates_three_count(idx, counts):
    total = 0
    for b in _EDGE_TO_BOXES[idx]:
        if counts[b] == 2:
            total += 1
    return total


def _creates_two_count(idx, counts):
    total = 0
    for b in _EDGE_TO_BOXES[idx]:
        if counts[b] == 1:
            total += 1
    return total


def _classify_moves(mask, counts=None):
    if counts is None:
        counts = _side_counts(mask)

    caps = []
    safe = []
    risky = []
    bits = _FULL_MASK & (~mask)

    while bits:
        lsb = bits & -bits
        idx = lsb.bit_length() - 1
        bits ^= lsb

        k = 0
        make3 = 0
        for b in _EDGE_TO_BOXES[idx]:
            cb = counts[b]
            if cb == 3:
                k += 1
            elif cb == 2:
                make3 += 1

        if k:
            caps.append((idx, k))
        elif make3 == 0:
            safe.append(idx)
        else:
            risky.append((idx, make3))

    return caps, safe, risky


def _two_components(mask, counts=None):
    cached = _COMP_CACHE.get(mask)
    if cached is not None:
        return cached
    if counts is None:
        counts = _side_counts(mask)

    comp_id = [-1] * 16
    sizes = []
    loops = []

    for start in range(16):
        if counts[start] != 2 or comp_id[start] != -1:
            continue

        cid = len(sizes)
        stack = [start]
        comp_id[start] = cid
        size = 0
        is_loop = True

        while stack:
            b = stack.pop()
            size += 1

            for e in _BOX_EDGES[b]:
                if mask & _EDGE_BITS[e]:
                    continue

                adj = _EDGE_TO_BOXES[e]
                if len(adj) == 2:
                    nb = adj[0] + adj[1] - b
                    if counts[nb] == 2:
                        if comp_id[nb] == -1:
                            comp_id[nb] = cid
                            stack.append(nb)
                        continue

                # An empty side leading to the border or to a non-2-sided box
                # means this component has an end, so it is not a closed loop.
                is_loop = False

        sizes.append(size)
        loops.append(is_loop)

    result = (tuple(comp_id), tuple(sizes), tuple(loops))
    if len(_COMP_CACHE) < _MAX_COMP_CACHE:
        _COMP_CACHE[mask] = result
    return result


def _opening_sacrifice(mask, idx, counts=None):
    if counts is None:
        counts = _side_counts(mask)

    comp_id, sizes, loops = _two_components(mask, counts)
    touched = set()

    for b in _EDGE_TO_BOXES[idx]:
        if counts[b] == 2:
            cid = comp_id[b]
            if cid >= 0:
                touched.add(cid)

    if not touched:
        return _creates_three_count(idx, counts)

    sac = 0
    for cid in touched:
        sac += sizes[cid]
        if loops[cid]:
            # Opening loops is generally more painful than opening chains.
            sac += 2
    return sac


def _min_opening_sacrifice(mask, counts=None):
    if counts is None:
        counts = _side_counts(mask)
    _caps, _safe, risky = _classify_moves(mask, counts)
    if not risky:
        return 0
    return min(_opening_sacrifice(mask, idx, counts) for idx, _ in risky)


def _chain_shape_score(mask, counts=None):
    if counts is None:
        counts = _side_counts(mask)
    _cid, sizes, loops = _two_components(mask, counts)

    score = 0.0
    for s, is_loop in zip(sizes, loops):
        if is_loop:
            score += 0.5 + 0.10 * s
        elif s >= 3:
            score += 0.25 * (s - 2)
        else:
            score -= 0.35 * (3 - s)
    return score


def _greedy_capture_gain(mask, counts=None, limit=20):
    total = 0
    steps = 0

    while steps < limit and mask != _FULL_MASK:
        if counts is None:
            counts = _side_counts(mask)

        caps, _safe, _risky = _classify_moves(mask, counts)
        if not caps:
            break

        best_idx, best_k = max(caps, key=lambda p: (p[1], _EDGE_CENTER[p[0]]))
        total += best_k
        mask |= _EDGE_BITS[best_idx]
        counts = None
        steps += 1

    return total


def _static_value(mask, counts=None):
    # Approximate future margin for the player to move.
    if mask in _TT:
        return float(_TT[mask])
    cached = _STATIC_CACHE.get(mask)
    if cached is not None:
        return cached
    if counts is None:
        counts = _side_counts(mask)

    caps, safe, risky = _classify_moves(mask, counts)

    if caps:
        val = float(_greedy_capture_gain(mask, counts))
    elif safe:
        n = len(safe)

        # In a pure safe-move race, the side that makes the last safe move
        # usually forces the opponent to open the first chain. Thus odd safe
        # count is good for the player to move.
        parity = 1.0 if (n & 1) else -1.0
        urgency = 1.0 + max(0, 12 - n) / 8.0
        val = parity * 1.25 * urgency

        # Long chains/loops are valuable if parity suggests we will control
        # them; bad if parity suggests the opponent will.
        val += parity * 0.25 * _chain_shape_score(mask, counts)
    else:
        sac = _min_opening_sacrifice(mask, counts)
        remaining_boxes = sum(1 for c in counts if c < 4)
        val = -float(min(max(sac, 0), remaining_boxes))

    if len(_STATIC_CACHE) < _MAX_STATIC_CACHE:
        _STATIC_CACHE[mask] = val
    return val


def _capture_candidate_score(mask, idx, counts):
    k = _capture_count(idx, counts)
    nm = mask | _EDGE_BITS[idx]
    return 20.0 * k + 2.0 * _greedy_capture_gain(nm, None, 12) + 0.03 * _EDGE_CENTER[idx]


def _safe_candidate_score_for_player(mask, idx, counts):
    # Score from the current player's perspective for making this non-scoring
    # move, after which the opponent is to move.
    nm = mask | _EDGE_BITS[idx]
    child_counts = _side_counts(nm)
    child_val = _static_value(nm, child_counts)

    created_twos = _creates_two_count(idx, counts)
    adj = len(_EDGE_TO_BOXES[idx])

    score = -child_val
    score -= 0.18 * created_twos
    score += 0.03 * _EDGE_CENTER[idx]
    if created_twos == 0:
        score += 0.04 * adj
    return score


def _risky_candidate_score_for_player(mask, idx, counts):
    # Non-capturing move that creates at least one 3-sided box. Prefer the
    # smallest chain/loop sacrifice.
    nm = mask | _EDGE_BITS[idx]
    child_counts = _side_counts(nm)
    child_val = _static_value(nm, child_counts)
    sac = _opening_sacrifice(mask, idx, counts)

    return -child_val - 0.10 * sac - 0.25 * _creates_three_count(idx, counts) + 0.02 * _EDGE_CENTER[idx]


def _tie_score(mask, idx, counts):
    k = _capture_count(idx, counts)
    if k:
        return _capture_candidate_score(mask, idx, counts)
    if _creates_three_count(idx, counts) == 0:
        return _safe_candidate_score_for_player(mask, idx, counts)
    return _risky_candidate_score_for_player(mask, idx, counts)


def _ordered_moves(mask, counts=None):
    if counts is None:
        counts = _side_counts(mask)

    caps, safe, risky = _classify_moves(mask, counts)

    caps.sort(key=lambda p: (-p[1], -_EDGE_CENTER[p[0]]))
    safe.sort(key=lambda i: (_creates_two_count(i, counts), -_EDGE_CENTER[i]))

    if len(risky) <= 14:
        risky.sort(key=lambda p: (_opening_sacrifice(mask, p[0], counts), p[1], -_EDGE_CENTER[p[0]]))
    else:
        risky.sort(key=lambda p: (p[1], -_EDGE_CENTER[p[0]]))

    return [i for i, _ in caps] + safe + [i for i, _ in risky]


def _solve(mask, alpha, beta, deadline):
    # Exact alpha-beta value for future boxes from the perspective of the
    # player to move. Capturing moves do not change the player to move.
    global _SOLVE_NODES

    if mask in _TT:
        return _TT[mask]

    _SOLVE_NODES += 1
    if (_SOLVE_NODES & 511) == 0 and time.perf_counter() > deadline:
        raise _SearchTimeout

    counts = _side_counts(mask)
    moves = _ordered_moves(mask, counts)
    if not moves:
        return 0

    best = -100
    best_idx = moves[0]
    cut = False

    for idx in moves:
        k = _capture_count(idx, counts)
        nm = mask | _EDGE_BITS[idx]

        if k:
            val = k + _solve(nm, alpha - k, beta - k, deadline)
        else:
            val = -_solve(nm, -beta, -alpha, deadline)

        if val > best:
            best = val
            best_idx = idx

        if best > alpha:
            alpha = best
        if alpha >= beta:
            cut = True
            break

    if not cut and len(_TT) < _MAX_TT:
        _TT[mask] = best
        _TT_MOVE[mask] = best_idx

    return best


def _choose_exact(mask, deadline):
    if mask in _TT_MOVE:
        return _TT_MOVE[mask]

    global _SOLVE_NODES
    _SOLVE_NODES = 0

    counts = _side_counts(mask)
    moves = _ordered_moves(mask, counts)
    if not moves:
        return None

    best_idx = moves[0]
    best_val = -100
    best_tie = -1e100
    alpha = -100
    beta = 100

    try:
        for idx in moves:
            if time.perf_counter() > deadline:
                raise _SearchTimeout

            k = _capture_count(idx, counts)
            nm = mask | _EDGE_BITS[idx]

            if k:
                val = k + _solve(nm, alpha - k, beta - k, deadline)
            else:
                val = -_solve(nm, -beta, -alpha, deadline)

            tie = _tie_score(mask, idx, counts)
            if val > best_val or (val == best_val and tie > best_tie):
                best_val = val
                best_idx = idx
                best_tie = tie

            if val > alpha:
                alpha = val

        if len(_TT) < _MAX_TT:
            _TT[mask] = best_val
            _TT_MOVE[mask] = best_idx

        return best_idx
    except _SearchTimeout:
        return None


_BEAM_SAFE = 9
_BEAM_RISKY = 8


def _approx_candidates(mask, counts, root=False):
    caps, safe, risky = _classify_moves(mask, counts)

    if caps:
        cap_scored = [(_capture_candidate_score(mask, idx, counts), idx) for idx, _ in caps]
        cap_scored.sort(reverse=True)
        moves = [idx for _s, idx in cap_scored]

        # In loony endgames, a non-capturing move while captures exist can be
        # the hard-hearted handout. Consider a few such moves when there are no
        # genuinely safe moves.
        if not safe and risky:
            risk_scored = [(_risky_candidate_score_for_player(mask, idx, counts), idx) for idx, _ in risky]
            risk_scored.sort(reverse=True)
            add = len(risk_scored) if root else 4
            for _s, idx in risk_scored[:add]:
                if idx not in moves:
                    moves.append(idx)

        return moves if root else moves[:10]

    if safe:
        scored = [(_safe_candidate_score_for_player(mask, idx, counts), idx) for idx in safe]
        scored.sort(reverse=True)
        lim = len(scored) if root else _BEAM_SAFE
        return [idx for _s, idx in scored[:lim]]

    if risky:
        scored = [(_risky_candidate_score_for_player(mask, idx, counts), idx) for idx, _ in risky]
        scored.sort(reverse=True)
        lim = len(scored) if root else _BEAM_RISKY
        return [idx for _s, idx in scored[:lim]]

    return []


def _approx_value(mask, depth, deadline, memo, counter):
    if mask in _TT:
        return float(_TT[mask])

    key = (mask, depth)
    cached = memo.get(key)
    if cached is not None:
        return cached

    counter[0] += 1
    if (counter[0] & 511) == 0 and time.perf_counter() > deadline:
        raise _ApproxTimeout

    if mask == _FULL_MASK:
        return 0.0

    counts = _side_counts(mask)
    if depth <= 0:
        val = _static_value(mask, counts)
        memo[key] = val
        return val

    moves = _approx_candidates(mask, counts, root=False)
    if not moves:
        return 0.0

    best = -1e100
    for idx in moves:
        k = _capture_count(idx, counts)
        nm = mask | _EDGE_BITS[idx]

        if k:
            val = float(k) + _approx_value(nm, depth, deadline, memo, counter)
        else:
            val = -_approx_value(nm, depth - 1, deadline, memo, counter)

        if val > best:
            best = val

    memo[key] = best
    return best


def _choose_approx(mask, depth, deadline):
    counts = _side_counts(mask)
    moves = _approx_candidates(mask, counts, root=True)
    if not moves:
        return None

    memo = {}
    counter = [0]
    best_idx = moves[0]
    best_val = -1e100
    best_tie = -1e100

    try:
        for idx in moves:
            if time.perf_counter() > deadline:
                break

            k = _capture_count(idx, counts)
            nm = mask | _EDGE_BITS[idx]

            if k:
                val = float(k) + _approx_value(nm, depth, deadline, memo, counter)
            else:
                val = -_approx_value(nm, max(0, depth - 1), deadline, memo, counter)

            tie = _tie_score(mask, idx, counts)
            if val > best_val + 1e-9 or (abs(val - best_val) <= 1e-9 and tie > best_tie):
                best_val = val
                best_idx = idx
                best_tie = tie

    except _ApproxTimeout:
        pass

    return best_idx


def _greedy_choice(mask, counts=None):
    if counts is None:
        counts = _side_counts(mask)

    caps, safe, risky = _classify_moves(mask, counts)

    if caps:
        return max((idx for idx, _ in caps), key=lambda i: _capture_candidate_score(mask, i, counts))

    if safe:
        return max(safe, key=lambda i: _safe_candidate_score_for_player(mask, i, counts))

    if risky:
        return max((idx for idx, _ in risky), key=lambda i: _risky_candidate_score_for_player(mask, i, counts))

    bits = _FULL_MASK & (~mask)
    if bits:
        return (bits & -bits).bit_length() - 1

    return None


def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # capture is not needed for future tactical choice: future boxes are fully
    # determined by occupied/unoccupied edges. Existing score is constant across
    # candidate moves.
    start = time.perf_counter()

    try:
        mask = _mask_from_arrays(horizontal, vertical)
        legal_bits = _FULL_MASK & (~mask)

        if legal_bits == 0:
            return _fallback_move(horizontal, vertical)

        if mask in _TT_MOVE:
            idx = _TT_MOVE[mask]
            if 0 <= idx < _EDGE_COUNT and not (mask & _EDGE_BITS[idx]) and _idx_is_empty(idx, horizontal, vertical):
                return _IDX_TO_STR[idx]

        counts = _side_counts(mask)
        caps, safe, risky = _classify_moves(mask, counts)
        remaining_edges = legal_bits.bit_count()

        # Exact search is strongest in the endgame and in loony/capturing
        # positions; it is time-limited so a legal fallback is always available.
        do_exact = False
        if remaining_edges <= 15:
            do_exact = True
        elif (caps or not safe) and remaining_edges <= 27:
            do_exact = True
        elif remaining_edges <= 20 and len(safe) <= 8:
            do_exact = True

        if do_exact:
            idx = _choose_exact(mask, start + 0.70)
            if idx is not None and _idx_is_empty(idx, horizontal, vertical):
                return _IDX_TO_STR[idx]

        # Bounded heuristic lookahead for the opening and for any exact-search
        # timeout. Depth is selected to stay comfortably under the time limit.
        if remaining_edges > 30:
            depth = 4
        elif safe:
            depth = 5
        else:
            depth = 6

        idx = _choose_approx(mask, depth, start + 0.93)
        if idx is not None and _idx_is_empty(idx, horizontal, vertical):
            return _IDX_TO_STR[idx]

        idx = _greedy_choice(mask, counts)
        if idx is not None and _idx_is_empty(idx, horizontal, vertical):
            return _IDX_TO_STR[idx]

        return _fallback_move(horizontal, vertical)

    except Exception:
        # Absolute safety: never fail to return a syntactically valid move.
        return _fallback_move(horizontal, vertical)
