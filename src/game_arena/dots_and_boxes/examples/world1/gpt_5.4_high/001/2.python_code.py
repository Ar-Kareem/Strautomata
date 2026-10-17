
import time
import numpy as np

TOTAL_EDGES = 40
EXACT_REMAIN = 16
TIME_BUDGET = 0.92
INF = 64

# --------------------------------------------------------------------
# Precompute the real 4x4-box Dots-and-Boxes geometry:
# Horizontal edges: rows 0..4, cols 0..3  -> 20 edges
# Vertical edges:   rows 0..3, cols 0..4  -> 20 edges
# --------------------------------------------------------------------

EDGE_INFO = []
EDGE_STR = []

H_IDX = [[-1 for _ in range(4)] for _ in range(5)]
V_IDX = [[-1 for _ in range(5)] for _ in range(4)]

idx = 0
for r in range(5):
    for c in range(4):
        H_IDX[r][c] = idx
        EDGE_INFO.append((r, c, 'H'))
        EDGE_STR.append(f"{r},{c},H")
        idx += 1

for r in range(4):
    for c in range(5):
        V_IDX[r][c] = idx
        EDGE_INFO.append((r, c, 'V'))
        EDGE_STR.append(f"{r},{c},V")
        idx += 1

ADJ_BOXES = [[] for _ in range(TOTAL_EDGES)]
BOX_MASKS = [0] * 16
BOX_SIDES = [None] * 16

for r in range(4):
    for c in range(4):
        b = r * 4 + c
        top = H_IDX[r][c]
        bottom = H_IDX[r + 1][c]
        left = V_IDX[r][c]
        right = V_IDX[r][c + 1]

        BOX_MASKS[b] = (1 << top) | (1 << bottom) | (1 << left) | (1 << right)

        ADJ_BOXES[top].append(b)
        ADJ_BOXES[bottom].append(b)
        ADJ_BOXES[left].append(b)
        ADJ_BOXES[right].append(b)

        above = (r - 1) * 4 + c if r > 0 else -1
        below = (r + 1) * 4 + c if r < 3 else -1
        left_box = r * 4 + (c - 1) if c > 0 else -1
        right_box = r * 4 + (c + 1) if c < 3 else -1

        BOX_SIDES[b] = (
            (top, above),
            (bottom, below),
            (left, left_box),
            (right, right_box),
        )

ADJ_BOXES = tuple(tuple(x) for x in ADJ_BOXES)
BOX_MASKS = tuple(BOX_MASKS)
BOX_SIDES = tuple(BOX_SIDES)
FULL_MASK = (1 << TOTAL_EDGES) - 1

# --------------------------------------------------------------------
# Persistent caches across calls
# --------------------------------------------------------------------

CLASS_CACHE = {}
HEUR_CACHE = {}
EXACT_CACHE = {}
EXACT_BEST = {}

DEADLINE = 0.0
NODE_COUNTER = 0


class SearchTimeout(Exception):
    pass


def _check_time():
    global NODE_COUNTER
    NODE_COUNTER += 1
    if (NODE_COUNTER & 1023) == 0 and time.perf_counter() > DEADLINE:
        raise SearchTimeout


def _build_mask(horizontal: np.ndarray, vertical: np.ndarray) -> int:
    mask = 0
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] != 0:
                mask |= (1 << H_IDX[r][c])
    for r in range(4):
        for c in range(5):
            if vertical[r, c] != 0:
                mask |= (1 << V_IDX[r][c])
    return mask


def _fallback_legal(horizontal: np.ndarray, vertical: np.ndarray) -> str:
    # Standard real edges first.
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] == 0:
                return f"{r},{c},H"
    for r in range(4):
        for c in range(5):
            if vertical[r, c] == 0:
                return f"{r},{c},V"

    # Defensive fallback for any non-standard arena interpretation.
    for r in range(5):
        for c in range(5):
            if horizontal[r, c] == 0:
                return f"{r},{c},H"
    for r in range(5):
        for c in range(5):
            if vertical[r, c] == 0:
                return f"{r},{c},V"

    return "0,0,H"


def _classify(mask: int):
    """
    Returns:
      capture: tuple of (edge_idx, boxes_captured_now)
      safe:    tuple of edge_idx
      sac:     tuple of (edge_idx, immediate_boxes_given)
      deg:     tuple of box degrees (# drawn sides), length 16
    """
    cached = CLASS_CACHE.get(mask)
    if cached is not None:
        return cached

    deg = [0] * 16
    for b in range(16):
        deg[b] = (mask & BOX_MASKS[b]).bit_count()

    capture = []
    safe = []
    sac = []

    for e in range(TOTAL_EDGES):
        if (mask >> e) & 1:
            continue

        k = 0
        danger = False
        gift = 0

        for b in ADJ_BOXES[e]:
            d = deg[b]
            if d == 3:
                k += 1
            elif d == 2:
                danger = True
                gift += 1

        if k > 0:
            capture.append((e, k))
        elif not danger:
            safe.append(e)
        else:
            sac.append((e, gift))

    out = (tuple(capture), tuple(safe), tuple(sac), tuple(deg))
    CLASS_CACHE[mask] = out
    return out


def _proto_chain_metric(mask: int, deg) -> float:
    """
    Rough structural danger estimate based on current degree-2 components.
    """
    visited = [False] * 16
    total = 0.0

    for b in range(16):
        if deg[b] != 2 or visited[b]:
            continue

        stack = [b]
        visited[b] = True
        comp = []

        while stack:
            x = stack.pop()
            comp.append(x)
            for edge, nb in BOX_SIDES[x]:
                if nb >= 0 and deg[nb] == 2 and ((mask >> edge) & 1) == 0 and not visited[nb]:
                    visited[nb] = True
                    stack.append(nb)

        comp_set = set(comp)
        openings = 0
        for x in comp:
            for edge, nb in BOX_SIDES[x]:
                if (mask >> edge) & 1:
                    continue
                if nb < 0 or nb not in comp_set or deg[nb] != 2:
                    openings += 1

        L = len(comp)
        if openings == 0:
            total += L * L + 2.0 * L  # loop-like
        else:
            total += L * L            # chain-like

    return total


def _heuristic_state(mask: int) -> float:
    """
    Approximate value for the side to move.
    Used for move ordering and shallow fallback decisions.
    """
    cached = HEUR_CACHE.get(mask)
    if cached is not None:
        return cached

    capture, safe, sac, deg = _classify(mask)

    cap_points = 0
    for _, k in capture:
        cap_points += k

    deg1 = 0
    deg2 = 0
    for d in deg:
        if d == 1:
            deg1 += 1
        elif d == 2:
            deg2 += 1

    chain_metric = _proto_chain_metric(mask, deg)

    val = 1.1 * cap_points
    if safe:
        val += 0.7 if (len(safe) & 1) else -0.7
    else:
        val -= 1.0

    val -= 0.20 * deg2
    val -= 0.06 * chain_metric
    val -= 0.02 * deg1

    HEUR_CACHE[mask] = val
    return val


def _order_safe(mask: int, safe, deg, preferred=None):
    if not safe:
        return []

    arr = []
    for e in safe:
        new_mask = mask | (1 << e)

        local = 0
        boxpos = 0.0
        for b in ADJ_BOXES[e]:
            d = deg[b]
            if d == 1:
                local += 2
            br, bc = divmod(b, 4)
            boxpos += abs(br - 1.5) + abs(bc - 1.5)

        border = 0 if len(ADJ_BOXES[e]) == 1 else 1
        arr.append((_heuristic_state(new_mask), local, border, boxpos, e))

    arr.sort()
    moves = [x[4] for x in arr]

    if preferred is not None and preferred in moves:
        moves.remove(preferred)
        moves.insert(0, preferred)

    return moves


def _order_capture(mask: int, capture, preferred=None):
    if not capture:
        return []

    arr = []
    for e, k in capture:
        new_mask = mask | (1 << e)
        arr.append((-k, -_heuristic_state(new_mask), e, k))

    arr.sort()
    moves = [(x[2], x[3]) for x in arr]

    if preferred is not None:
        for i, (e, k) in enumerate(moves):
            if e == preferred:
                moves.pop(i)
                moves.insert(0, (e, k))
                break

    return moves


def _order_sacrifice(mask: int, sac, preferred=None):
    if not sac:
        return []

    arr = []
    for e, gift in sac:
        new_mask = mask | (1 << e)
        arr.append((gift, _heuristic_state(new_mask), e))

    arr.sort()
    moves = [x[2] for x in arr]

    if preferred is not None and preferred in moves:
        moves.remove(preferred)
        moves.insert(0, preferred)

    return moves


def _exact_value(mask: int, alpha: int = -INF, beta: int = INF) -> int:
    """
    Exact negamax value for the side to move.
    Uses alpha-beta; caches only exact (fully searched) nodes.
    """
    _check_time()

    if mask == FULL_MASK:
        return 0

    cached = EXACT_CACHE.get(mask)
    if cached is not None:
        return cached

    capture, safe, sac, deg = _classify(mask)
    preferred = EXACT_BEST.get(mask)
    best = -INF
    best_move = preferred
    complete = True

    if capture:
        # If safe moves still exist elsewhere, captures dominate.
        for e, k in _order_capture(mask, capture, preferred):
            v = k + _exact_value(mask | (1 << e), alpha - k, beta - k)
            if v > best:
                best = v
                best_move = e
                EXACT_BEST[mask] = e
            if best > alpha:
                alpha = best
            if alpha >= beta:
                complete = False
                break

        # In loony positions (no safe moves), also allow handouts / sacrifices.
        if not safe and alpha < beta:
            for e in _order_sacrifice(mask, sac, preferred):
                v = -_exact_value(mask | (1 << e), -beta, -alpha)
                if v > best:
                    best = v
                    best_move = e
                    EXACT_BEST[mask] = e
                if best > alpha:
                    alpha = best
                if alpha >= beta:
                    complete = False
                    break

    elif safe:
        for e in _order_safe(mask, safe, deg, preferred):
            v = -_exact_value(mask | (1 << e), -beta, -alpha)
            if v > best:
                best = v
                best_move = e
                EXACT_BEST[mask] = e
            if best > alpha:
                alpha = best
            if alpha >= beta:
                complete = False
                break

    else:
        # No captures and no safe moves: exact loony opening choice.
        for e in _order_sacrifice(mask, sac, preferred):
            v = -_exact_value(mask | (1 << e), -beta, -alpha)
            if v > best:
                best = v
                best_move = e
                EXACT_BEST[mask] = e
            if best > alpha:
                alpha = best
            if alpha >= beta:
                complete = False
                break

    if complete:
        EXACT_CACHE[mask] = best
    EXACT_BEST[mask] = best_move
    return best


def _heuristic_safe_move(mask: int, safe, deg) -> int:
    return _order_safe(mask, safe, deg, None)[0]


def _heuristic_capture_move(mask: int, capture):
    return _order_capture(mask, capture, None)[0]


def _rollout_eval(mask: int) -> int:
    """
    From the current side-to-move perspective, follow heuristic safe play
    until the position becomes exact-solvable, then finish exactly.
    """
    _check_time()

    acc = 0
    sign = 1
    cur = mask

    while True:
        _check_time()

        if cur == FULL_MASK:
            return acc

        rem = TOTAL_EDGES - cur.bit_count()
        capture, safe, sac, deg = _classify(cur)

        if rem <= EXACT_REMAIN or not safe:
            return acc + sign * _exact_value(cur, -INF, INF)

        if capture:
            e, k = _heuristic_capture_move(cur, capture)
            acc += sign * k
            cur |= (1 << e)
        else:
            e = _heuristic_safe_move(cur, safe, deg)
            cur |= (1 << e)
            sign = -sign


def _limited_value(mask: int, depth: int, alpha: int, beta: int) -> int:
    """
    Alpha-beta search in the safe-play phase.
    Capturing sequences are searched tactically; unsafe phases are solved exactly.
    """
    _check_time()

    if mask == FULL_MASK:
        return 0

    rem = TOTAL_EDGES - mask.bit_count()
    if rem <= EXACT_REMAIN:
        return _exact_value(mask, alpha, beta)

    capture, safe, sac, deg = _classify(mask)

    if not safe:
        return _exact_value(mask, alpha, beta)

    if capture:
        best = -INF
        for e, k in _order_capture(mask, capture, None):
            v = k + _limited_value(mask | (1 << e), depth, alpha - k, beta - k)
            if v > best:
                best = v
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        return best

    if depth <= 0:
        return _rollout_eval(mask)

    best = -INF
    for e in _order_safe(mask, safe, deg, None):
        v = -_limited_value(mask | (1 << e), depth - 1, -beta, -alpha)
        if v > best:
            best = v
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best


def _search_root(mask: int, depth: int, preferred=None):
    capture, safe, sac, deg = _classify(mask)
    rem = TOTAL_EDGES - mask.bit_count()

    if rem <= EXACT_REMAIN or not safe:
        val = _exact_value(mask, -INF, INF)
        return val, EXACT_BEST.get(mask)

    alpha = -INF
    beta = INF
    best = -INF
    best_move = None

    if capture:
        for e, k in _order_capture(mask, capture, preferred):
            v = k + _limited_value(mask | (1 << e), depth, alpha - k, beta - k)
            if v > best:
                best = v
                best_move = e
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
    else:
        for e in _order_safe(mask, safe, deg, preferred):
            v = -_limited_value(mask | (1 << e), depth - 1, -beta, -alpha)
            if v > best:
                best = v
                best_move = e
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break

    return best, best_move


def _fallback_idx(mask: int):
    capture, safe, sac, deg = _classify(mask)

    if capture and safe:
        ordered = _order_capture(mask, capture, None)
        return ordered[0][0] if ordered else None

    if safe:
        ordered = _order_safe(mask, safe, deg, None)
        return ordered[0] if ordered else None

    if capture:
        best_move = None
        best_val = -1e18

        for e, k in capture:
            v = k + _heuristic_state(mask | (1 << e))
            if v > best_val:
                best_val = v
                best_move = e

        for e, gift in sac:
            v = -_heuristic_state(mask | (1 << e)) - 0.25 * gift
            if v > best_val:
                best_val = v
                best_move = e

        return best_move

    if sac:
        ordered = _order_sacrifice(mask, sac, None)
        return ordered[0] if ordered else None

    return None


def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    global DEADLINE, NODE_COUNTER

    try:
        mask = _build_mask(horizontal, vertical)

        # If all standard edges are filled, fall back defensively.
        if mask == FULL_MASK:
            return _fallback_legal(horizontal, vertical)

        fallback = _fallback_idx(mask)
        if fallback is None:
            return _fallback_legal(horizontal, vertical)

        best_idx = fallback

        DEADLINE = time.perf_counter() + TIME_BUDGET
        NODE_COUNTER = 0

        rem = TOTAL_EDGES - mask.bit_count()
        root_capture, root_safe, root_sac, root_deg = _classify(mask)

        if rem <= EXACT_REMAIN or not root_safe:
            try:
                _exact_value(mask, -INF, INF)
                best_idx = EXACT_BEST.get(mask, best_idx)
            except SearchTimeout:
                best_idx = EXACT_BEST.get(mask, best_idx)
        else:
            preferred = best_idx
            for depth in range(1, 10):
                try:
                    _, move = _search_root(mask, depth, preferred)
                    if move is not None:
                        best_idx = move
                        preferred = move
                except SearchTimeout:
                    break

        if best_idx is not None:
            r, c, d = EDGE_INFO[best_idx]
            if d == 'H':
                if horizontal[r, c] == 0:
                    return EDGE_STR[best_idx]
            else:
                if vertical[r, c] == 0:
                    return EDGE_STR[best_idx]

        return _fallback_legal(horizontal, vertical)

    except Exception:
        return _fallback_legal(horizontal, vertical)
