
import time
import numpy as np

# ----- Board constants for a 4x4 box Dots and Boxes board -----
# Horizontal: rows 0..4, cols 0..3  -> indices 0..19
# Vertical:   rows 0..3, cols 0..4  -> indices 20..39

TOTAL_EDGES = 40
TOTAL_BOXES = 16
ALL_EDGES_MASK = (1 << TOTAL_EDGES) - 1
ALL_BOXES_MASK = (1 << TOTAL_BOXES) - 1
INF = 10 ** 9

_MOVES = []
for _r in range(5):
    for _c in range(4):
        _MOVES.append((_r, _c, "H"))
for _r in range(4):
    for _c in range(5):
        _MOVES.append((_r, _c, "V"))

def _h_idx(r, c):
    return r * 4 + c

def _v_idx(r, c):
    return 20 + r * 5 + c

_BOX_EDGES = []
_EDGE_BOXES = [[] for _ in range(TOTAL_EDGES)]

for r in range(4):
    for c in range(4):
        b = r * 4 + c
        edges = [
            _h_idx(r, c),
            _h_idx(r + 1, c),
            _v_idx(r, c),
            _v_idx(r, c + 1),
        ]
        _BOX_EDGES.append(edges)
        for e in edges:
            _EDGE_BOXES[e].append(b)

_BOX_MASKS = []
for edges in _BOX_EDGES:
    m = 0
    for e in edges:
        m |= 1 << e
    _BOX_MASKS.append(m)

# Small deterministic tie-breaker: prefer central-ish edges very slightly.
_EDGE_PREF = []
for e, (r, c, d) in enumerate(_MOVES):
    if d == "H":
        x, y = c + 0.5, r
    else:
        x, y = c, r + 0.5
    _EDGE_PREF.append(-((x - 2.0) ** 2 + (y - 2.0) ** 2))

_LOONY_CACHE = {}


# ----- Basic state helpers -----

def _edge_to_string(e):
    r, c, d = _MOVES[e]
    return f"{r},{c},{d}"

def _state_from_arrays(horizontal, vertical, capture):
    occ = 0

    for r in range(5):
        for c in range(4):
            if horizontal[r, c] != 0:
                occ |= 1 << _h_idx(r, c)

    for r in range(4):
        for c in range(5):
            if vertical[r, c] != 0:
                occ |= 1 << _v_idx(r, c)

    claimed = 0
    for r in range(4):
        for c in range(4):
            b = r * 4 + c
            if capture[r, c] != 0:
                claimed |= 1 << b

    # Defensive consistency: if all four sides of a box are already present,
    # do not allow the search to "recapture" it if capture is stale.
    for b in range(TOTAL_BOXES):
        if (occ & _BOX_MASKS[b]) == _BOX_MASKS[b]:
            claimed |= 1 << b

    return occ, claimed

def _first_legal_edge(occ):
    for e in range(TOTAL_EDGES):
        if (occ & (1 << e)) == 0:
            return e
    return None

def _fallback_scan_arrays(horizontal, vertical):
    # Standard valid edges first.
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] == 0:
                return f"{r},{c},H"
    for r in range(4):
        for c in range(5):
            if vertical[r, c] == 0:
                return f"{r},{c},V"

    # Extremely defensive fallback for nonstandard validators / terminal calls.
    for r in range(5):
        for c in range(5):
            if horizontal[r, c] == 0:
                return f"{r},{c},H"
    for r in range(5):
        for c in range(5):
            if vertical[r, c] == 0:
                return f"{r},{c},V"

    return "0,0,H"

def _side_count(occ, b):
    return (occ & _BOX_MASKS[b]).bit_count()

def _capture_count_after(occ, claimed, e):
    nocc = occ | (1 << e)
    k = 0
    for b in _EDGE_BOXES[e]:
        if ((claimed >> b) & 1) == 0 and (nocc & _BOX_MASKS[b]) == _BOX_MASKS[b]:
            k += 1
    return k

def _play(occ, claimed, e):
    nocc = occ | (1 << e)
    nclaimed = claimed
    k = 0
    for b in _EDGE_BOXES[e]:
        if ((claimed >> b) & 1) == 0 and (nocc & _BOX_MASKS[b]) == _BOX_MASKS[b]:
            nclaimed |= 1 << b
            k += 1
    return nocc, nclaimed, k

def _is_safe_noncapture(occ, claimed, e):
    # A non-capturing move is safe if it does not create a 3-sided unclaimed box.
    for b in _EDGE_BOXES[e]:
        if ((claimed >> b) & 1) == 0 and _side_count(occ, b) == 2:
            return False
    return True

def _move_categories(occ, claimed):
    caps = []
    noncaps = []

    for e in range(TOTAL_EDGES):
        if (occ >> e) & 1:
            continue
        k = _capture_count_after(occ, claimed, e)
        if k > 0:
            caps.append((e, k))
        else:
            noncaps.append(e)

    if caps:
        return caps, [], noncaps

    safe = []
    unsafe = []
    for e in noncaps:
        if _is_safe_noncapture(occ, claimed, e):
            safe.append(e)
        else:
            unsafe.append(e)

    return [], safe, unsafe

def _capture_moves_simple(occ, claimed):
    out = []
    for e in range(TOTAL_EDGES):
        if (occ >> e) & 1:
            continue
        k = _capture_count_after(occ, claimed, e)
        if k > 0:
            out.append((e, k))
    return out

def _count_safe_moves(occ, claimed):
    caps, safe, unsafe = _move_categories(occ, claimed)
    if caps:
        return 0
    return len(safe)


# ----- Greedy/heuristic helpers -----

def _capture_run_length_after_open(occ, claimed, e):
    # Estimate how many boxes the opponent can harvest after we open with e.
    nocc = occ | (1 << e)
    nclaimed = claimed
    total = 0
    steps = 0

    while steps < TOTAL_EDGES:
        steps += 1
        caps = _capture_moves_simple(nocc, nclaimed)
        if not caps:
            break
        be, bk = max(caps, key=lambda x: (x[1], _EDGE_PREF[x[0]]))
        nocc, nclaimed, got = _play(nocc, nclaimed, be)
        total += got

    return total

def _quick_safe_order(occ, claimed, e):
    score = 0.01 * _EDGE_PREF[e]
    for b in _EDGE_BOXES[e]:
        if ((claimed >> b) & 1) == 0:
            cnt = _side_count(occ, b)
            score -= (cnt + 1) * (cnt + 1)
            if cnt == 1:
                score -= 2.0
    return score

def _unsafe_order(occ, claimed, e):
    # Prefer opening the smallest chain/run.
    return -_capture_run_length_after_open(occ, claimed, e) + 0.01 * _EDGE_PREF[e]

def _ordered_moves(occ, claimed):
    caps, safe, unsafe = _move_categories(occ, claimed)

    if caps:
        caps.sort(key=lambda x: (x[1], _EDGE_PREF[x[0]]), reverse=True)
        return [e for e, _ in caps]

    safe.sort(key=lambda e: _quick_safe_order(occ, claimed, e), reverse=True)

    if len(unsafe) <= 18:
        unsafe.sort(key=lambda e: _unsafe_order(occ, claimed, e), reverse=True)
    else:
        unsafe.sort(key=lambda e: _quick_safe_order(occ, claimed, e), reverse=True)

    return safe + unsafe

def _root_safe_score(occ, claimed, e):
    nocc = occ | (1 << e)
    future_safe = _count_safe_moves(nocc, claimed)

    made_twos = 0
    side_penalty = 0.0
    for b in _EDGE_BOXES[e]:
        if ((claimed >> b) & 1) == 0:
            after = _side_count(nocc, b)
            if after == 2:
                made_twos += 1
            side_penalty += after * after

    # After our safe move, the opponent moves. If the remaining safe-move count
    # is even, the opponent is more likely to be the one who eventually opens.
    parity_bonus = 0.5 if (future_safe % 2 == 0) else -0.5

    return (
        10.0 * future_safe
        - 4.0 * made_twos
        - side_penalty
        + parity_bonus
        + 0.01 * _EDGE_PREF[e]
    )


# ----- Loony endgame chain/loop theory -----

def _loony_components_detail(occ, claimed):
    unclaimed = [b for b in range(TOTAL_BOXES) if ((claimed >> b) & 1) == 0]
    if not unclaimed:
        return []

    unclaimed_set = set(unclaimed)
    missing = {}

    for b in unclaimed:
        miss = [e for e in _BOX_EDGES[b] if ((occ >> e) & 1) == 0]
        # In a quiet loony endgame every unclaimed box has exactly 2 missing sides.
        if len(miss) != 2:
            return None
        missing[b] = miss

    adj = {b: [] for b in unclaimed}
    for b in unclaimed:
        for e in missing[b]:
            for ob in _EDGE_BOXES[e]:
                if ob != b and ob in unclaimed_set:
                    adj[b].append(ob)

    visited = set()
    comps = []

    for start in unclaimed:
        if start in visited:
            continue

        stack = [start]
        visited.add(start)
        boxes = []

        while stack:
            b = stack.pop()
            boxes.append(b)
            for nb in adj[b]:
                if nb not in visited:
                    visited.add(nb)
                    stack.append(nb)

        comp_set = set(boxes)
        edges = set()
        boundary_edges = set()
        boundary_stubs = 0

        for b in boxes:
            for e in missing[b]:
                edges.add(e)
                inside_count = 0
                for ob in _EDGE_BOXES[e]:
                    if ob in comp_set:
                        inside_count += 1
                if inside_count == 1:
                    boundary_stubs += 1
                    boundary_edges.add(e)

        if boundary_stubs == 2:
            kind = "chain"
        elif boundary_stubs == 0:
            kind = "loop"
        else:
            return None

        comps.append({
            "kind": kind,
            "length": len(boxes),
            "edges": list(edges),
            "boundary_edges": list(boundary_edges),
        })

    return comps

def _component_value(chains, loops):
    chains = tuple(sorted(chains))
    loops = tuple(sorted(loops))
    key = (chains, loops)

    if key in _LOONY_CACHE:
        return _LOONY_CACHE[key]

    if not chains and not loops:
        return 0

    best = -INF

    for i, n in enumerate(chains):
        rem_chains = chains[:i] + chains[i + 1:]
        rv = _component_value(rem_chains, loops)

        # Controller may take all, or for chains length >=3 keep control by
        # handing out 2 boxes.
        take_all = -n - rv
        if n >= 3:
            keep_control = 4 - n + rv
            outcome = min(take_all, keep_control)
        else:
            outcome = take_all

        if outcome > best:
            best = outcome

    for i, n in enumerate(loops):
        rem_loops = loops[:i] + loops[i + 1:]
        rv = _component_value(chains, rem_loops)

        # For loops, the hard-hearted handout is 4 boxes.
        take_all = -n - rv
        if n >= 4:
            keep_control = 8 - n + rv
            outcome = min(take_all, keep_control)
        else:
            outcome = take_all

        if outcome > best:
            best = outcome

    _LOONY_CACHE[key] = best
    return best

def _loony_value_quiet(occ, claimed):
    comps = _loony_components_detail(occ, claimed)
    if comps is None:
        return None

    chains = []
    loops = []
    for comp in comps:
        if comp["kind"] == "chain":
            chains.append(comp["length"])
        else:
            loops.append(comp["length"])

    return _component_value(tuple(sorted(chains)), tuple(sorted(loops)))

def _loony_value(occ, claimed):
    caps, safe, unsafe = _move_categories(occ, claimed)
    if caps or safe:
        return None
    return _loony_value_quiet(occ, claimed)

def _best_loony_opening(occ, claimed):
    comps = _loony_components_detail(occ, claimed)
    if comps is None or not comps:
        return None

    best_edge = None
    best_key = (-INF, -INF, -INF)

    for i, comp in enumerate(comps):
        rem_chains = []
        rem_loops = []
        for j, other in enumerate(comps):
            if i == j:
                continue
            if other["kind"] == "chain":
                rem_chains.append(other["length"])
            else:
                rem_loops.append(other["length"])

        rv = _component_value(tuple(sorted(rem_chains)), tuple(sorted(rem_loops)))
        n = comp["length"]

        if comp["kind"] == "chain":
            take_all = -n - rv
            if n >= 3:
                keep_control = 4 - n + rv
                val = min(take_all, keep_control)
            else:
                val = take_all
            candidate_edges = comp["boundary_edges"] or comp["edges"]
        else:
            take_all = -n - rv
            if n >= 4:
                keep_control = 8 - n + rv
                val = min(take_all, keep_control)
            else:
                val = take_all
            candidate_edges = comp["edges"]

        if not candidate_edges:
            continue

        edge = max(candidate_edges, key=lambda e: _EDGE_PREF[e])
        key = (val, -n, _EDGE_PREF[edge])
        if key > best_key:
            best_key = key
            best_edge = edge

    return best_edge


# ----- Evaluation and search -----

def _heuristic_eval(occ, claimed):
    # Value is future margin from the current player-to-move's perspective.
    if occ == ALL_EDGES_MASK:
        return 0.0

    # Quiescence: greedily consume currently available boxes.
    gain = 0
    nocc = occ
    nclaimed = claimed
    steps = 0

    while steps < TOTAL_EDGES:
        steps += 1
        caps = _capture_moves_simple(nocc, nclaimed)
        if not caps:
            break
        e, _ = max(caps, key=lambda x: (x[1], _EDGE_PREF[x[0]]))
        nocc, nclaimed, got = _play(nocc, nclaimed, e)
        gain += got

    lv = _loony_value(nocc, nclaimed)
    if lv is not None:
        return gain + lv

    caps, safe, unsafe = _move_categories(nocc, nclaimed)
    if safe:
        s = len(safe)
        two_boxes = 0
        one_boxes = 0
        for b in range(TOTAL_BOXES):
            if ((nclaimed >> b) & 1) == 0:
                cnt = _side_count(nocc, b)
                if cnt == 2:
                    two_boxes += 1
                elif cnt == 1:
                    one_boxes += 1

        parity = 0.25 if (s % 2 == 1) else -0.25
        return gain + parity - 0.05 * two_boxes + 0.02 * one_boxes

    if unsafe:
        best = -INF
        for e in unsafe:
            val = -_capture_run_length_after_open(nocc, nclaimed, e)
            if val > best:
                best = val
        return gain + best

    return float(gain)

def _check_time(ctx):
    ctx[0] += 1
    if (ctx[0] & 511) == 0 and time.perf_counter() > ctx[1]:
        raise TimeoutError

def _negamax(occ, claimed, depth, alpha, beta, ctx, tt):
    _check_time(ctx)

    if occ == ALL_EDGES_MASK:
        return 0.0

    key = (occ, claimed, depth)
    ent = tt.get(key)
    if ent is not None:
        ent_depth, ent_val, ent_flag = ent
        if ent_depth >= depth:
            if ent_flag == 0:
                return ent_val
            if ent_flag == 1:
                alpha = max(alpha, ent_val)
            elif ent_flag == 2:
                beta = min(beta, ent_val)
            if alpha >= beta:
                return ent_val

    caps, safe, unsafe = _move_categories(occ, claimed)

    if not caps and not safe:
        lv = _loony_value_quiet(occ, claimed)
        if lv is not None:
            return float(lv)

    if depth <= 0:
        return _heuristic_eval(occ, claimed)

    if caps:
        caps.sort(key=lambda x: (x[1], _EDGE_PREF[x[0]]), reverse=True)
        moves = [e for e, _ in caps]
    else:
        safe.sort(key=lambda e: _quick_safe_order(occ, claimed, e), reverse=True)
        if len(unsafe) <= 18:
            unsafe.sort(key=lambda e: _unsafe_order(occ, claimed, e), reverse=True)
        else:
            unsafe.sort(key=lambda e: _quick_safe_order(occ, claimed, e), reverse=True)
        moves = safe + unsafe

    if not moves:
        return 0.0

    orig_alpha = alpha
    orig_beta = beta
    best = -INF

    for e in moves:
        nocc, nclaimed, got = _play(occ, claimed, e)
        if got > 0:
            val = got + _negamax(nocc, nclaimed, depth - 1, alpha - got, beta - got, ctx, tt)
        else:
            val = -_negamax(nocc, nclaimed, depth - 1, -beta, -alpha, ctx, tt)

        if val > best:
            best = val
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break

    if best <= orig_alpha:
        flag = 2  # upper bound
    elif best >= orig_beta:
        flag = 1  # lower bound
    else:
        flag = 0  # exact

    tt[key] = (depth, best, flag)
    return best

def _root_candidates(occ, claimed, exact_root):
    caps, safe, unsafe = _move_categories(occ, claimed)

    if caps:
        caps.sort(key=lambda x: (x[1], _EDGE_PREF[x[0]]), reverse=True)
        return [e for e, _ in caps]

    if safe:
        safe.sort(key=lambda e: _root_safe_score(occ, claimed, e), reverse=True)
        if exact_root:
            if len(unsafe) <= 18:
                unsafe.sort(key=lambda e: _unsafe_order(occ, claimed, e), reverse=True)
            else:
                unsafe.sort(key=lambda e: _quick_safe_order(occ, claimed, e), reverse=True)
            return safe + unsafe
        return safe

    if len(unsafe) <= 18:
        unsafe.sort(key=lambda e: _unsafe_order(occ, claimed, e), reverse=True)
    else:
        unsafe.sort(key=lambda e: _quick_safe_order(occ, claimed, e), reverse=True)

    return unsafe

def _iterative_search(occ, claimed, default_edge, max_depth, end_time):
    rem = TOTAL_EDGES - occ.bit_count()
    if max_depth <= 0 or rem <= 0:
        return default_edge

    exact_root = max_depth >= rem
    candidates = _root_candidates(occ, claimed, exact_root)
    if not candidates:
        return default_edge

    last_best = default_edge
    tt = {}
    ctx = [0, end_time]

    for depth in range(1, max_depth + 1):
        if time.perf_counter() > end_time:
            break

        cur_best = last_best
        cur_val = -INF

        try:
            for e in candidates:
                _check_time(ctx)
                nocc, nclaimed, got = _play(occ, claimed, e)

                if got > 0:
                    val = got + _negamax(nocc, nclaimed, depth - 1, -INF, INF, ctx, tt)
                else:
                    val = -_negamax(nocc, nclaimed, depth - 1, -INF, INF, ctx, tt)

                if val > cur_val:
                    cur_val = val
                    cur_best = e
        except TimeoutError:
            break

        last_best = cur_best

        if depth >= rem:
            break

    return last_best


# ----- Main fallback policy -----

def _fallback_move(occ, claimed):
    caps, safe, unsafe = _move_categories(occ, claimed)

    if caps:
        best_e = None
        best_key = (-INF, -INF, -INF)
        for e, k in caps:
            nocc, nclaimed, got = _play(occ, claimed, e)
            val = got + _heuristic_eval(nocc, nclaimed)
            key = (val, got, _EDGE_PREF[e])
            if key > best_key:
                best_key = key
                best_e = e
        if best_e is not None:
            return best_e

    if safe:
        return max(safe, key=lambda e: _root_safe_score(occ, claimed, e))

    loony = _best_loony_opening(occ, claimed)
    if loony is not None and ((occ >> loony) & 1) == 0:
        return loony

    if unsafe:
        return max(unsafe, key=lambda e: _unsafe_order(occ, claimed, e))

    return _first_legal_edge(occ)


def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    try:
        occ, claimed = _state_from_arrays(horizontal, vertical, capture)

        default_edge = _fallback_move(occ, claimed)
        if default_edge is None:
            return _fallback_scan_arrays(horizontal, vertical)

        rem = TOTAL_EDGES - occ.bit_count()
        caps, safe, unsafe = _move_categories(occ, claimed)

        # Time-aware search depth selection.
        if rem <= 16:
            max_depth = rem
        elif rem <= 20 and (caps or not safe):
            max_depth = rem
        elif rem <= 22 and not safe:
            max_depth = rem
        elif rem <= 24:
            max_depth = 8
        elif caps:
            max_depth = 5
        else:
            max_depth = 0

        best_edge = default_edge
        if max_depth > 0:
            end_time = time.perf_counter() + 0.85
            best_edge = _iterative_search(occ, claimed, default_edge, max_depth, end_time)

        if best_edge is None or ((occ >> best_edge) & 1):
            best_edge = default_edge
        if best_edge is None or ((occ >> best_edge) & 1):
            best_edge = _first_legal_edge(occ)
        if best_edge is None:
            return _fallback_scan_arrays(horizontal, vertical)

        return _edge_to_string(best_edge)

    except Exception:
        # Absolute safety net: never fail to return a move string.
        return _fallback_scan_arrays(horizontal, vertical)
