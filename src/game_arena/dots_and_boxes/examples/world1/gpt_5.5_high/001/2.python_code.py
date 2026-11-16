
import time
import numpy as np

# 4x4 boxes => 5x4 horizontal edges and 4x5 vertical edges = 40 real edges.
N = 4
_EDGE_COUNT = 40
_INF = 10 ** 9

_EDGE_INFO = []
_H_ID = [[-1 for _ in range(N)] for _ in range(N + 1)]
_V_ID = [[-1 for _ in range(N + 1)] for _ in range(N)]

_idx = 0
for r in range(N + 1):
    for c in range(N):
        _H_ID[r][c] = _idx
        _EDGE_INFO.append((r, c, "H"))
        _idx += 1

for r in range(N):
    for c in range(N + 1):
        _V_ID[r][c] = _idx
        _EDGE_INFO.append((r, c, "V"))
        _idx += 1

_EDGE_BITS = [1 << i for i in range(_EDGE_COUNT)]
_FULL_MASK = (1 << _EDGE_COUNT) - 1

_BOX_MASKS = []
_EDGE_BOXES = [[] for _ in range(_EDGE_COUNT)]

for r in range(N):
    for c in range(N):
        edges = [
            _H_ID[r][c],
            _H_ID[r + 1][c],
            _V_ID[r][c],
            _V_ID[r][c + 1],
        ]
        b = len(_BOX_MASKS)
        m = 0
        for e in edges:
            m |= _EDGE_BITS[e]
            _EDGE_BOXES[e].append(b)
        _BOX_MASKS.append(m)

_EXACT_TT = {}


def _mask_from_arrays(horizontal, vertical):
    mask = 0
    for r in range(N + 1):
        for c in range(N):
            if horizontal[r, c] != 0:
                mask |= _EDGE_BITS[_H_ID[r][c]]
    for r in range(N):
        for c in range(N + 1):
            if vertical[r, c] != 0:
                mask |= _EDGE_BITS[_V_ID[r][c]]
    return mask


def _side_count(mask, box_id):
    return (mask & _BOX_MASKS[box_id]).bit_count()


def _complete_count(mask, edge):
    cnt = 0
    for b in _EDGE_BOXES[edge]:
        if _side_count(mask, b) == 3:
            cnt += 1
    return cnt


def _created_three_count(mask, edge):
    cnt = 0
    for b in _EDGE_BOXES[edge]:
        if _side_count(mask, b) == 2:
            cnt += 1
    return cnt


def _is_safe_non_capture(mask, edge):
    return _complete_count(mask, edge) == 0 and _created_three_count(mask, edge) == 0


def _safe_order_score(mask, edge):
    adj = _EDGE_BOXES[edge]
    before = sum(_side_count(mask, b) for b in adj)
    border_bonus = 1 if len(adj) == 1 else 0

    r, c, d = _EDGE_INFO[edge]
    if d == "H":
        x, y = r, c + 0.5
    else:
        x, y = r + 0.5, c
    center_bonus = -abs(x - 2.0) - abs(y - 2.0)

    # Prefer low-pressure safe moves. Border moves are often flexible early.
    return 10 * border_bonus - 5 * before + 0.1 * center_bonus


def _ordered_moves(mask):
    caps = []
    safe = []
    risky = []

    empty = (~mask) & _FULL_MASK
    while empty:
        bit = empty & -empty
        edge = bit.bit_length() - 1
        empty ^= bit

        k = _complete_count(mask, edge)
        if k:
            caps.append((k, edge))
        else:
            c3 = _created_three_count(mask, edge)
            if c3 == 0:
                safe.append((_safe_order_score(mask, edge), edge))
            else:
                risky.append((c3, edge))

    caps.sort(key=lambda x: (-x[0], x[1]))
    safe.sort(key=lambda x: (-x[0], x[1]))
    risky.sort(key=lambda x: (x[0], x[1]))

    return [e for _, e in caps] + [e for _, e in safe] + [e for _, e in risky]


def _has_capture(mask):
    empty = (~mask) & _FULL_MASK
    while empty:
        bit = empty & -empty
        edge = bit.bit_length() - 1
        empty ^= bit
        if _complete_count(mask, edge) > 0:
            return True
    return False


def _has_safe(mask):
    empty = (~mask) & _FULL_MASK
    while empty:
        bit = empty & -empty
        edge = bit.bit_length() - 1
        empty ^= bit
        if _is_safe_non_capture(mask, edge):
            return True
    return False


def _greedy_capture_count(mask):
    total = 0
    local_mask = mask

    while True:
        best_edge = -1
        best_k = 0

        empty = (~local_mask) & _FULL_MASK
        while empty:
            bit = empty & -empty
            edge = bit.bit_length() - 1
            empty ^= bit

            k = _complete_count(local_mask, edge)
            if k > best_k:
                best_k = k
                best_edge = edge

        if best_k <= 0:
            break

        total += best_k
        local_mask |= _EDGE_BITS[best_edge]

        if total >= 16:
            break

    return total


def _evaluate(mask):
    if mask == _FULL_MASK:
        return 0.0

    rem = _EDGE_COUNT - mask.bit_count()
    max_cap = 0
    cap_edges = 0
    safe_edges = 0
    min_risky_local = 99

    empty = (~mask) & _FULL_MASK
    while empty:
        bit = empty & -empty
        edge = bit.bit_length() - 1
        empty ^= bit

        k = _complete_count(mask, edge)
        if k:
            cap_edges += 1
            if k > max_cap:
                max_cap = k
        else:
            c3 = _created_three_count(mask, edge)
            if c3 == 0:
                safe_edges += 1
            elif c3 < min_risky_local:
                min_risky_local = c3

    if max_cap:
        val = 1.25 * max_cap + 0.15 * cap_edges
        if rem <= 18:
            val = max(val, 0.65 * _greedy_capture_count(mask) + 0.25 * max_cap)
        return val

    two_boxes = 0
    for b in range(16):
        if _side_count(mask, b) == 2:
            two_boxes += 1

    if safe_edges:
        return 0.02 * safe_edges - 0.03 * two_boxes

    # No captures and no safe move: current player is probably opening a chain.
    if rem <= 20:
        loss = 99
        empty = (~mask) & _FULL_MASK
        while empty:
            bit = empty & -empty
            edge = bit.bit_length() - 1
            empty ^= bit
            nm = mask | bit
            g = _greedy_capture_count(nm)
            if g < loss:
                loss = g
        if loss < 99:
            return -float(loss)

    return -float(min_risky_local if min_risky_local != 99 else 0)


def _check_time(deadline):
    if time.perf_counter() >= deadline:
        raise TimeoutError


def _value_after_move_depth(mask, edge, depth, alpha, beta, deadline):
    bit = _EDGE_BITS[edge]
    nm = mask | bit
    k = _complete_count(mask, edge)

    if k:
        return k + _alphabeta_depth(nm, depth, alpha - k, beta - k, deadline)
    else:
        return -_alphabeta_depth(nm, depth, -beta, -alpha, deadline)


def _alphabeta_depth(mask, depth, alpha, beta, deadline):
    _check_time(deadline)

    if mask == _FULL_MASK:
        return 0.0

    if depth <= 0:
        return _evaluate(mask)

    best = -_INF
    moves = _ordered_moves(mask)

    for edge in moves:
        val = _value_after_move_depth(mask, edge, depth - 1, alpha, beta, deadline)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    return best


def _root_depth_search(mask, moves, depth, deadline):
    _check_time(deadline)

    best_edge = moves[0]
    best_val = -_INF
    alpha = -_INF
    beta = _INF

    for edge in moves:
        _check_time(deadline)
        val = _value_after_move_depth(mask, edge, depth - 1, alpha, beta, deadline)
        if val > best_val:
            best_val = val
            best_edge = edge
        if val > alpha:
            alpha = val

    return best_edge, best_val


def _value_after_move_exact(mask, edge, alpha, beta, deadline):
    bit = _EDGE_BITS[edge]
    nm = mask | bit
    k = _complete_count(mask, edge)

    if k:
        return k + _alphabeta_exact(nm, alpha - k, beta - k, deadline)
    else:
        return -_alphabeta_exact(nm, -beta, -alpha, deadline)


def _alphabeta_exact(mask, alpha, beta, deadline):
    _check_time(deadline)

    if mask == _FULL_MASK:
        return 0

    entry = _EXACT_TT.get(mask)
    if entry is not None:
        val, flag = entry
        if flag == 0:
            return val
        if flag == 1:
            if val > alpha:
                alpha = val
        else:
            if val < beta:
                beta = val
        if alpha >= beta:
            return val

    orig_alpha = alpha
    orig_beta = beta

    best = -_INF
    moves = _ordered_moves(mask)

    for edge in moves:
        val = _value_after_move_exact(mask, edge, alpha, beta, deadline)

        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    if best <= orig_alpha:
        flag = -1  # upper bound
    elif best >= orig_beta:
        flag = 1   # lower bound
    else:
        flag = 0   # exact

    _EXACT_TT[mask] = (best, flag)
    return best


def _root_exact_search(mask, moves, deadline):
    best_edge = moves[0]
    best_val = -_INF
    alpha = -_INF
    beta = _INF

    for edge in moves:
        _check_time(deadline)
        val = _value_after_move_exact(mask, edge, alpha, beta, deadline)

        if val > best_val:
            best_val = val
            best_edge = edge
        if val > alpha:
            alpha = val

    return best_edge, best_val


def _heuristic_move(mask, moves=None):
    if moves is None:
        moves = _ordered_moves(mask)

    if not moves:
        return -1

    best_edge = moves[0]
    best_score = -_INF

    for edge in moves:
        bit = _EDGE_BITS[edge]
        nm = mask | bit
        k = _complete_count(mask, edge)

        if k:
            # Captures are usually urgent. Prefer more immediate boxes and
            # positions with continued capture potential.
            score = 10000 + 500 * k + 20 * _greedy_capture_count(nm)
        else:
            c3 = _created_three_count(mask, edge)
            if c3 == 0:
                # Safe move: after this the opponent moves, so leave them as
                # little as possible.
                score = 1000 - 10 * _evaluate(nm) + _safe_order_score(mask, edge)
            else:
                # Forced opening: minimize opponent's greedy capture run.
                giveaway = _greedy_capture_count(nm)
                score = -10000 - 500 * giveaway - 20 * c3

        if score > best_score:
            best_score = score
            best_edge = edge

    return best_edge


def _choose_move(mask, deadline):
    moves = _ordered_moves(mask)
    if not moves:
        return -1

    fallback = _heuristic_move(mask, moves)
    best = fallback

    rem = _EDGE_COUNT - mask.bit_count()
    has_cap = _has_capture(mask)
    has_safe = _has_safe(mask)

    exact_candidate = (
        rem <= 22
        or (has_cap and rem <= 26)
        or ((not has_safe) and rem <= 30)
    )

    if exact_candidate:
        raw_depths = [2, 4, 6]
        if rem <= 12:
            raw_depths.append(rem)
    elif rem > 32:
        raw_depths = [2, 3, 4]
    elif rem > 24:
        raw_depths = [3, 4, 5, 6]
    else:
        raw_depths = [3, 5, 7, 9]

    depths = []
    for d in raw_depths:
        d = max(1, min(rem, d))
        if d not in depths:
            depths.append(d)

    for depth in depths:
        try:
            if time.perf_counter() >= deadline:
                break
            bm, _ = _root_depth_search(mask, moves, depth, deadline)
            best = bm
            moves = [bm] + [m for m in moves if m != bm]
            if depth >= rem:
                return best
        except TimeoutError:
            return best

    if exact_candidate:
        try:
            if time.perf_counter() < deadline:
                bm, _ = _root_exact_search(mask, moves, deadline)
                best = bm
        except TimeoutError:
            pass

    return best


def _edge_to_string(edge):
    r, c, d = _EDGE_INFO[edge]
    return f"{r},{c},{d}"


def _edge_is_free(edge, horizontal, vertical):
    r, c, d = _EDGE_INFO[edge]
    if d == "H":
        return horizontal[r, c] == 0
    return vertical[r, c] == 0


def _fallback_legal(horizontal, vertical):
    # Prefer real 4x4-board edges.
    try:
        for r in range(N + 1):
            for c in range(N):
                if horizontal[r, c] == 0:
                    return f"{r},{c},H"

        for r in range(N):
            for c in range(N + 1):
                if vertical[r, c] == 0:
                    return f"{r},{c},V"

        # Ultra-defensive fallback for environments that treat the full 5x5
        # arrays as legal edge tables.
        hr, hc = horizontal.shape[:2]
        for r in range(min(5, hr)):
            for c in range(min(5, hc)):
                if horizontal[r, c] == 0:
                    return f"{r},{c},H"

        vr, vc = vertical.shape[:2]
        for r in range(min(5, vr)):
            for c in range(min(5, vc)):
                if vertical[r, c] == 0:
                    return f"{r},{c},V"
    except Exception:
        pass

    # Should only happen if called after the game is already over.
    return "0,0,H"


def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    try:
        # Prevent unbounded memory growth across a very long match batch.
        if len(_EXACT_TT) > 300000:
            _EXACT_TT.clear()

        mask = _mask_from_arrays(horizontal, vertical)
        deadline = time.perf_counter() + 0.82

        edge = _choose_move(mask, deadline)

        if edge is not None and edge >= 0 and _edge_is_free(edge, horizontal, vertical):
            return _edge_to_string(edge)

    except Exception:
        pass

    return _fallback_legal(horizontal, vertical)
