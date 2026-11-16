
import time
import numpy as np

# Dots and Boxes policy for a 4x4 box grid.
# Valid edges:
#   Horizontal: rows 0..4, cols 0..3
#   Vertical:   rows 0..3, cols 0..4

_INITIALIZED = False

_EDGES = []
_H_INDEX = {}
_V_INDEX = {}
_BITS = []
_BOX_MASKS = []
_EDGE_ADJ = []
_EDGE_OTHERS = []
_FULL_MASK = 0

_TT = {}
_NODES = 0


class _SearchTimeout(Exception):
    pass


def _init():
    global _INITIALIZED
    global _EDGES, _H_INDEX, _V_INDEX, _BITS
    global _BOX_MASKS, _EDGE_ADJ, _EDGE_OTHERS, _FULL_MASK

    if _INITIALIZED:
        return

    _EDGES = []
    _H_INDEX = {}
    _V_INDEX = {}

    # 20 horizontal edges
    for r in range(5):
        for c in range(4):
            idx = len(_EDGES)
            _H_INDEX[(r, c)] = idx
            _EDGES.append((r, c, "H"))

    # 20 vertical edges
    for r in range(4):
        for c in range(5):
            idx = len(_EDGES)
            _V_INDEX[(r, c)] = idx
            _EDGES.append((r, c, "V"))

    _BITS = [1 << i for i in range(40)]
    _FULL_MASK = (1 << 40) - 1

    _BOX_MASKS = [0] * 16
    _EDGE_ADJ = [[] for _ in range(40)]

    for br in range(4):
        for bc in range(4):
            b = br * 4 + bc
            top = _H_INDEX[(br, bc)]
            bottom = _H_INDEX[(br + 1, bc)]
            left = _V_INDEX[(br, bc)]
            right = _V_INDEX[(br, bc + 1)]

            m = _BITS[top] | _BITS[bottom] | _BITS[left] | _BITS[right]
            _BOX_MASKS[b] = m

            _EDGE_ADJ[top].append(b)
            _EDGE_ADJ[bottom].append(b)
            _EDGE_ADJ[left].append(b)
            _EDGE_ADJ[right].append(b)

    _EDGE_OTHERS = []
    for e in range(40):
        arr = []
        eb = _BITS[e]
        for b in _EDGE_ADJ[e]:
            arr.append((b, _BOX_MASKS[b] & ~eb))
        _EDGE_OTHERS.append(arr)

    _INITIALIZED = True


def _mask_from_arrays(horizontal, vertical):
    m = 0

    for r in range(5):
        for c in range(4):
            if horizontal[r, c] != 0:
                m |= _BITS[_H_INDEX[(r, c)]]

    for r in range(4):
        for c in range(5):
            if vertical[r, c] != 0:
                m |= _BITS[_V_INDEX[(r, c)]]

    return m


def _move_string(e):
    r, c, d = _EDGES[e]
    return f"{r},{c},{d}"


def _edge_is_empty_in_arrays(e, horizontal, vertical):
    r, c, d = _EDGES[e]
    if d == "H":
        return horizontal[r, c] == 0
    return vertical[r, c] == 0


def _first_legal(mask, horizontal, vertical):
    for e in range(40):
        if (mask & _BITS[e]) == 0 and _edge_is_empty_in_arrays(e, horizontal, vertical):
            return e
    # Should never be needed unless called after game end.
    return 0


def _cap_count(mask, e):
    """Number of boxes completed by drawing edge e."""
    cnt = 0
    for _, other_edges in _EDGE_OTHERS[e]:
        if (mask & other_edges) == other_edges:
            cnt += 1
    return cnt


def _side_count(mask, b):
    return (mask & _BOX_MASKS[b]).bit_count()


def _danger_count(mask, e):
    """How many adjacent boxes would become 3-sided after drawing e, assuming e is noncapturing."""
    d = 0
    for b in _EDGE_ADJ[e]:
        if _side_count(mask, b) == 2:
            d += 1
    return d


def _empty_edges(mask):
    return [e for e in range(40) if (mask & _BITS[e]) == 0]


def _count_safe_moves(mask):
    cnt = 0
    for e in range(40):
        if mask & _BITS[e]:
            continue
        if _cap_count(mask, e) == 0 and _danger_count(mask, e) == 0:
            cnt += 1
    return cnt


def _count_capture_moves(mask):
    cnt = 0
    for e in range(40):
        if (mask & _BITS[e]) == 0 and _cap_count(mask, e) > 0:
            cnt += 1
    return cnt


def _count_boxes_with_sides(mask, n):
    cnt = 0
    for b in range(16):
        if _side_count(mask, b) == n:
            cnt += 1
    return cnt


def _ordered_moves(mask):
    """Move ordering for alpha-beta search."""
    caps = []
    safes = []
    risks = []

    for e in range(40):
        if mask & _BITS[e]:
            continue

        k = _cap_count(mask, e)
        if k:
            # Prefer double captures, then captures that leave more immediate captures.
            nm = mask | _BITS[e]
            follow = _count_capture_moves(nm)
            caps.append((-k, -follow, e))
        else:
            d = _danger_count(mask, e)
            if d == 0:
                # Prefer less committal safe edges first.
                adj_sides = 0
                created_twos = 0
                for b in _EDGE_ADJ[e]:
                    s = _side_count(mask, b)
                    adj_sides += s
                    if s == 1:
                        created_twos += 1
                safes.append((created_twos, adj_sides, e))
            else:
                risks.append((d, e))

    caps.sort()
    safes.sort()
    risks.sort()

    return [x[2] for x in caps] + [x[2] for x in safes] + [x[1] for x in risks]


def _ab(mask, alpha, beta, deadline):
    """Exact future box-margin search from the side-to-move perspective."""
    global _NODES, _TT

    _NODES += 1
    if (_NODES & 2047) == 0 and time.perf_counter() > deadline:
        raise _SearchTimeout()

    if mask == _FULL_MASK:
        return 0

    cached = _TT.get(mask)
    if cached is not None:
        return cached

    best = -100
    cutoff = False

    for e in _ordered_moves(mask):
        nm = mask | _BITS[e]
        k = _cap_count(mask, e)

        if k:
            # Capturing keeps the move.
            val = k + _ab(nm, alpha - k, beta - k, deadline)
        else:
            # Noncapture passes the turn; switch perspective.
            val = -_ab(nm, -beta, -alpha, deadline)

        if val > best:
            best = val
        if best > alpha:
            alpha = best

        if alpha >= beta:
            cutoff = True
            break

    if best == -100:
        best = 0

    # Store only exact values, not cutoff bounds.
    if not cutoff:
        if len(_TT) > 300000:
            _TT.clear()
        _TT[mask] = best

    return best


def _search_best(mask, deadline):
    """Try to find the exact best move. Returns (move, value, completed)."""
    global _NODES

    moves = _ordered_moves(mask)
    if not moves:
        return None, 0, True

    _NODES = 0
    best_e = moves[0]
    best_val = -100
    alpha = -100

    try:
        for e in moves:
            if time.perf_counter() > deadline:
                raise _SearchTimeout()

            nm = mask | _BITS[e]
            k = _cap_count(mask, e)

            if k:
                val = k + _ab(nm, alpha - k, 100 - k, deadline)
            else:
                val = -_ab(nm, -100, -alpha, deadline)

            if val > best_val:
                best_val = val
                best_e = e
            if val > alpha:
                alpha = val

        return best_e, best_val, True

    except _SearchTimeout:
        return best_e, best_val, False


def _greedy_capture_run(mask, memo):
    """
    Estimate how many boxes the next player can take in one capturing run
    if they greedily maximize captures.
    """
    if mask in memo:
        return memo[mask]

    best = 0
    for e in range(40):
        if mask & _BITS[e]:
            continue
        k = _cap_count(mask, e)
        if k:
            gain = k + _greedy_capture_run(mask | _BITS[e], memo)
            if gain > best:
                best = gain

    memo[mask] = best
    return best


def _safe_score(mask, e):
    """Heuristic for choosing among safe noncapturing moves."""
    nm = mask | _BITS[e]

    safe_after = _count_safe_moves(nm)
    twos_after = _count_boxes_with_sides(nm, 2)

    created_twos = 0
    adj_sides = 0
    for b in _EDGE_ADJ[e]:
        s = _side_count(mask, b)
        adj_sides += s
        if s == 1:
            created_twos += 1

    score = 0

    # Safe-move parity: after our noncapture, opponent moves.
    # Leaving an even number of safe moves is often preferable.
    if safe_after == 0:
        score += 1000
    elif safe_after % 2 == 0:
        score += 120
    else:
        score -= 120

    # Prefer to reduce safe options when parity is favorable.
    score -= 5 * safe_after

    # Avoid creating many 2-sided boxes too early.
    score -= 25 * created_twos
    score -= 4 * twos_after
    score -= 2 * adj_sides

    # Slight deterministic tie-breaks.
    if len(_EDGE_ADJ[e]) == 1:
        score += 2
    score -= e * 0.001

    return score


def _capture_score(mask, e):
    """Heuristic for choosing among capturing moves when exact search is unavailable."""
    k = _cap_count(mask, e)
    nm = mask | _BITS[e]

    follow_caps = []
    for f in range(40):
        if nm & _BITS[f]:
            continue
        kk = _cap_count(nm, f)
        if kk:
            follow_caps.append(kk)

    score = 1000 * k

    if follow_caps:
        score += 100 * max(follow_caps) + 8 * len(follow_caps)
    else:
        safe = _count_safe_moves(nm)
        if safe == 0:
            # After this capture, we may have to open something.
            memo = {}
            best_cost = 99
            for f in range(40):
                if nm & _BITS[f]:
                    continue
                if _cap_count(nm, f) == 0:
                    cost = _greedy_capture_run(nm | _BITS[f], memo)
                    if cost < best_cost:
                        best_cost = cost
            if best_cost != 99:
                score -= 30 * best_cost
        else:
            if safe % 2 == 1:
                score += 30
            else:
                score -= 10

    score -= e * 0.001
    return score


def _sacrifice_key(mask, e, memo):
    """
    Key for choosing a forced sacrifice/opening move.
    Lower is better.
    """
    nm = mask | _BITS[e]
    gain = _greedy_capture_run(nm, memo)
    danger = _danger_count(mask, e)
    threes = _count_boxes_with_sides(nm, 3)
    return (gain, danger, threes, e)


def _heuristic_choose(mask):
    caps = []
    safes = []
    risks = []

    for e in range(40):
        if mask & _BITS[e]:
            continue

        k = _cap_count(mask, e)
        if k:
            caps.append(e)
        else:
            d = _danger_count(mask, e)
            if d == 0:
                safes.append(e)
            else:
                risks.append(e)

    if caps:
        return max(caps, key=lambda e: _capture_score(mask, e))

    if safes:
        return max(safes, key=lambda e: _safe_score(mask, e))

    if risks:
        memo = {}
        return min(risks, key=lambda e: _sacrifice_key(mask, e, memo))

    return None


def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    _init()

    mask = _mask_from_arrays(horizontal, vertical)
    legal = _empty_edges(mask)

    if not legal:
        # Should not occur during a live game, but return a syntactically valid move.
        return "0,0,H"

    cap_moves = []
    safe_moves = []

    for e in legal:
        k = _cap_count(mask, e)
        if k:
            cap_moves.append(e)
        elif _danger_count(mask, e) == 0:
            safe_moves.append(e)

    empties = len(legal)

    # Use exact search in positions where it is likely to matter and likely to fit.
    # Captures/no-safe positions are usually tactical chain positions.
    should_search = (
        empties <= 20
        or (cap_moves and empties <= 32)
        or ((not cap_moves) and (not safe_moves) and empties <= 34)
    )

    chosen = None

    if should_search:
        deadline = time.perf_counter() + 0.82
        m, val, complete = _search_best(mask, deadline)

        # If complete, trust it. If incomplete but tactical, the partial ordered result
        # is usually still at least a strong legal fallback.
        if m is not None and (complete or cap_moves or not safe_moves):
            chosen = m

    if chosen is None:
        chosen = _heuristic_choose(mask)

    if chosen is None:
        chosen = _first_legal(mask, horizontal, vertical)

    # Final legality guard.
    if (mask & _BITS[chosen]) == 0 and _edge_is_empty_in_arrays(chosen, horizontal, vertical):
        return _move_string(chosen)

    fallback = _first_legal(mask, horizontal, vertical)
    return _move_string(fallback)
