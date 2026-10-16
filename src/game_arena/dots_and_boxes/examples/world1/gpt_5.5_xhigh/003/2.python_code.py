
import time
import numpy as np

# 4x4 boxes: 20 horizontal edges + 20 vertical edges.
# H index: r*4+c for r=0..4, c=0..3
# V index: 20+r*5+c for r=0..3, c=0..4

EDGE_COUNT = 40
FULL_MASK = (1 << EDGE_COUNT) - 1
NEG_INF = -10**9

BOX_EDGES = []
BOX_MASKS = []
EDGE_BOXES = [[] for _ in range(EDGE_COUNT)]
MOVE_STRINGS = []
MIRROR_EDGE = [0] * EDGE_COUNT
CENTER_BONUS = [0.0] * EDGE_COUNT
EDGE_ADJ_BOX_MASK = [0] * EDGE_COUNT

for r in range(5):
    for c in range(4):
        MOVE_STRINGS.append(f"{r},{c},H")

for r in range(4):
    for c in range(5):
        MOVE_STRINGS.append(f"{r},{c},V")

for r in range(4):
    for c in range(4):
        b = r * 4 + c
        top = r * 4 + c
        bottom = (r + 1) * 4 + c
        left = 20 + r * 5 + c
        right = 20 + r * 5 + c + 1
        edges = (top, bottom, left, right)
        BOX_EDGES.append(edges)
        mask = 0
        for e in edges:
            mask |= 1 << e
            EDGE_BOXES[e].append(b)
        BOX_MASKS.append(mask)

for e in range(EDGE_COUNT):
    bm = 0
    for b in EDGE_BOXES[e]:
        bm |= 1 << b
    EDGE_ADJ_BOX_MASK[e] = bm

for e in range(EDGE_COUNT):
    if e < 20:
        r, c = divmod(e, 4)
        mr, mc = 4 - r, 3 - c
        MIRROR_EDGE[e] = mr * 4 + mc
        x, y = c + 0.5, float(r)
    else:
        j = e - 20
        r, c = divmod(j, 5)
        mr, mc = 3 - r, 4 - c
        MIRROR_EDGE[e] = 20 + mr * 5 + mc
        x, y = float(c), r + 0.5

    # Small deterministic tie-breaker favoring central edges.
    CENTER_BONUS[e] = 3.0 - (abs(x - 2.0) + abs(y - 2.0))


class _SearchTimeout(Exception):
    pass


_EXACT_CACHE = {FULL_MASK: 0}
_BEST_CACHE = {}
_MAX_EXACT_CACHE = 300000
_MAX_BEST_CACHE = 100000


def _store_exact(mask: int, value: int) -> None:
    if mask in _EXACT_CACHE or len(_EXACT_CACHE) < _MAX_EXACT_CACHE:
        _EXACT_CACHE[mask] = value


def _store_best(mask: int, edge: int) -> None:
    if mask in _BEST_CACHE or len(_BEST_CACHE) < _MAX_BEST_CACHE:
        _BEST_CACHE[mask] = edge


def _iter_bits(bits: int):
    while bits:
        lsb = bits & -bits
        yield lsb.bit_length() - 1
        bits ^= lsb


def _state_to_mask(horizontal: np.ndarray, vertical: np.ndarray) -> int:
    mask = 0
    for r in range(5):
        for c in range(4):
            if int(horizontal[r, c]) != 0:
                mask |= 1 << (r * 4 + c)
    for r in range(4):
        for c in range(5):
            if int(vertical[r, c]) != 0:
                mask |= 1 << (20 + r * 5 + c)
    return mask & FULL_MASK


def _edge_empty_array(e: int, horizontal: np.ndarray, vertical: np.ndarray) -> bool:
    if e < 20:
        r, c = divmod(e, 4)
        return int(horizontal[r, c]) == 0
    j = e - 20
    r, c = divmod(j, 5)
    return int(vertical[r, c]) == 0


def _edge_value_array(e: int, horizontal: np.ndarray, vertical: np.ndarray) -> int:
    if e < 20:
        r, c = divmod(e, 4)
        return int(horizontal[r, c])
    j = e - 20
    r, c = divmod(j, 5)
    return int(vertical[r, c])


def _first_legal_from_arrays(horizontal: np.ndarray, vertical: np.ndarray) -> str:
    try:
        for e in range(EDGE_COUNT):
            if _edge_empty_array(e, horizontal, vertical):
                return MOVE_STRINGS[e]

        # Should not be needed on a normal 4x4 board, but keeps the API safe
        # if the caller ever treats padded entries as playable.
        for r in range(5):
            for c in range(5):
                if int(horizontal[r, c]) == 0:
                    return f"{r},{c},H"
        for r in range(5):
            for c in range(5):
                if int(vertical[r, c]) == 0:
                    return f"{r},{c},V"
    except Exception:
        pass
    return "0,0,H"


def _drawn_count(mask: int, b: int) -> int:
    return (mask & BOX_MASKS[b]).bit_count()


def _cap_count(mask: int, e: int) -> int:
    # Number of boxes completed by drawing currently-empty edge e.
    cnt = 0
    for b in EDGE_BOXES[e]:
        if (mask & BOX_MASKS[b]).bit_count() == 3:
            cnt += 1
    return cnt


def _third_count(mask: int, e: int) -> int:
    # Number of boxes that would become 3-sided without being captured.
    cnt = 0
    for b in EDGE_BOXES[e]:
        if (mask & BOX_MASKS[b]).bit_count() == 2:
            cnt += 1
    return cnt


def _capturable_count(mask: int) -> int:
    cnt = 0
    for bm in BOX_MASKS:
        if (mask & bm).bit_count() == 3:
            cnt += 1
    return cnt


def _has_capture(mask: int) -> bool:
    return _capturable_count(mask) > 0


def _remaining_boxes(mask: int) -> int:
    cnt = 0
    for bm in BOX_MASKS:
        if (mask & bm) != bm:
            cnt += 1
    return cnt


def _two_side_boxes(mask: int) -> int:
    cnt = 0
    for bm in BOX_MASKS:
        if (mask & bm).bit_count() == 2:
            cnt += 1
    return cnt


def _classify_moves(mask: int):
    caps, safe, risky = [], [], []
    for e in _iter_bits(FULL_MASK ^ mask):
        k = _cap_count(mask, e)
        if k:
            caps.append(e)
        elif _third_count(mask, e) == 0:
            safe.append(e)
        else:
            risky.append(e)
    return caps, safe, risky


def _safe_count(mask: int) -> int:
    cnt = 0
    for e in _iter_bits(FULL_MASK ^ mask):
        if _cap_count(mask, e) == 0 and _third_count(mask, e) == 0:
            cnt += 1
    return cnt


def _has_safe(mask: int) -> bool:
    for e in _iter_bits(FULL_MASK ^ mask):
        if _cap_count(mask, e) == 0 and _third_count(mask, e) == 0:
            return True
    return False


def _component_mask(mask: int, start_box: int) -> int:
    if (mask & BOX_MASKS[start_box]) == BOX_MASKS[start_box]:
        return 0

    seen = 1 << start_box
    stack = [start_box]

    while stack:
        b = stack.pop()
        for e in BOX_EDGES[b]:
            if mask & (1 << e):
                continue
            for nb in EDGE_BOXES[e]:
                if nb != b and (seen & (1 << nb)) == 0:
                    if (mask & BOX_MASKS[nb]) != BOX_MASKS[nb]:
                        seen |= 1 << nb
                        stack.append(nb)
    return seen


def _safe_priority_fast(mask: int, e: int) -> float:
    score = CENTER_BONUS[e]
    adj = EDGE_BOXES[e]

    if len(adj) == 2:
        score += 6.0

    for b in adj:
        d = _drawn_count(mask, b)
        if d == 0:
            score += 20.0
        elif d == 1:
            score += 8.0
        elif d == 2:
            score -= 40.0
        else:
            score -= 80.0
    return score


def _safe_priority_root(mask: int, e: int) -> float:
    nm = mask | (1 << e)
    score = _safe_priority_fast(mask, e)

    # Prefer moves that do not build many 2-sided boxes.
    score -= 3.0 * (_two_side_boxes(nm) - _two_side_boxes(mask))

    # Parity heuristic: leaving an even number of safe moves to the opponent
    # is often favorable because they may be forced to open first.
    s = _safe_count(nm)
    if s == 0:
        score += 25.0
    elif s % 2 == 0:
        score += 4.0
    else:
        score -= 4.0
    score -= 0.05 * s
    return score


def _capture_priority_fast(mask: int, e: int) -> float:
    k = _cap_count(mask, e)
    nm = mask | (1 << e)
    return 100.0 * k + 6.0 * _capturable_count(nm) + CENTER_BONUS[e]


def _capture_priority_root(mask: int, e: int) -> float:
    nm = mask | (1 << e)
    score = _capture_priority_fast(mask, e)

    # Avoid taking the very last box of a chain if it immediately forces us
    # to open another chain, unless there is no alternative.
    if not _has_capture(nm):
        if _has_safe(nm):
            score += 8.0
        elif nm != FULL_MASK:
            score -= 30.0
    return score


def _sacrifice_priority_fast(mask: int, e: int) -> float:
    return -100.0 * _third_count(mask, e) + CENTER_BONUS[e]


def _sacrifice_priority(mask: int, e: int) -> float:
    nm = mask | (1 << e)
    created = [b for b in EDGE_BOXES[e] if _drawn_count(mask, b) == 2]
    if not created:
        return -1000.0 + CENTER_BONUS[e]

    comps = []
    for b in created:
        cm = _component_mask(nm, b)
        if cm and cm not in comps:
            comps.append(cm)

    if not comps:
        return -1000.0 + CENTER_BONUS[e]

    sizes = [cm.bit_count() for cm in comps]
    min_size = min(sizes)

    # When forced to open, usually open the smallest chain/component.
    score = -30.0 * min_size - 10.0 * len(created) + CENTER_BONUS[e]
    if len(sizes) == 1 and len(created) >= 2 and min_size >= 4:
        score -= 5.0
    return score


def _handoff_priority(mask: int, e: int) -> float:
    # Hard-hearted handout candidate: a non-capturing move while boxes are
    # already available that leaves a small 2-box or 4-box gift, preserving
    # control of remaining components.
    if _cap_count(mask, e) != 0:
        return NEG_INF
    if _third_count(mask, e) == 0:
        return NEG_INF

    nm = mask | (1 << e)
    caps_after = []
    for b, bm in enumerate(BOX_MASKS):
        if (nm & bm).bit_count() == 3:
            caps_after.append(b)

    if len(caps_after) < 2:
        return NEG_INF

    edge_adj = EDGE_ADJ_BOX_MASK[e]
    rem_boxes = _remaining_boxes(nm)
    best = NEG_INF
    seen_components = set()

    for b in caps_after:
        comp = _component_mask(nm, b)
        if comp == 0 or comp in seen_components:
            continue
        seen_components.add(comp)

        # The played edge must actually be part of the gift component.
        if (comp & edge_adj) == 0:
            continue

        size = comp.bit_count()
        cap_in_comp = 0
        for cb in caps_after:
            if comp & (1 << cb):
                cap_in_comp += 1

        if cap_in_comp >= 2 and size <= 4 and rem_boxes > size:
            score = 350.0 - 45.0 * size + 5.0 * cap_in_comp + CENTER_BONUS[e]
            if score > best:
                best = score

    return best


def _root_priority(mask: int, e: int) -> float:
    k = _cap_count(mask, e)
    if k:
        return _capture_priority_root(mask, e)

    if _capturable_count(mask) > 0:
        hp = _handoff_priority(mask, e)
        if hp > NEG_INF // 2:
            return hp

    if _third_count(mask, e) == 0:
        return _safe_priority_root(mask, e)

    return _sacrifice_priority(mask, e)


def _ordered_search_moves(mask: int):
    caps, safe, risky = _classify_moves(mask)
    items = []
    used = set()

    # In capture-only endgames, plausible handouts are often the principal
    # variation, so search them early.
    if caps and not safe:
        for e in risky:
            hp = _handoff_priority(mask, e)
            if hp > NEG_INF // 2:
                items.append((6000.0 + hp, e))
                used.add(e)

    for e in caps:
        items.append((5000.0 + _capture_priority_fast(mask, e), e))
    for e in safe:
        items.append((1000.0 + _safe_priority_fast(mask, e), e))
    for e in risky:
        if e not in used:
            items.append((_sacrifice_priority_fast(mask, e), e))

    items.sort(key=lambda x: x[0], reverse=True)
    return [e for _, e in items]


def _ab(mask: int, alpha: int, beta: int, deadline: float, tt: dict, counter: list) -> int:
    if mask == FULL_MASK:
        return 0

    cached = _EXACT_CACHE.get(mask)
    if cached is not None:
        return cached

    counter[0] += 1
    if (counter[0] & 2047) == 0:
        if counter[0] > counter[1] or time.perf_counter() > deadline:
            raise _SearchTimeout()

    alpha0, beta0 = alpha, beta

    entry = tt.get(mask)
    if entry is not None:
        val, flag = entry
        if flag == 0:
            return val
        if flag > 0:
            alpha = max(alpha, val)
        else:
            beta = min(beta, val)
        if alpha >= beta:
            return val

    best = -99
    moves = _ordered_search_moves(mask)
    if not moves:
        return 0

    for e in moves:
        k = _cap_count(mask, e)
        nm = mask | (1 << e)

        if k:
            # Same player moves again.
            val = k + _ab(nm, alpha - k, beta - k, deadline, tt, counter)
        else:
            # Turn changes; negate the opponent-to-move value.
            val = -_ab(nm, -beta, -alpha, deadline, tt, counter)

        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    if best <= alpha0:
        flag = -1   # upper bound
    elif best >= beta0:
        flag = 1    # lower bound
    else:
        flag = 0    # exact

    tt[mask] = (best, flag)
    if flag == 0:
        _store_exact(mask, best)
    return best


def _exact_best_move(mask: int, deadline: float, node_limit: int):
    moves = _ordered_search_moves(mask)
    if not moves:
        return None, 0

    tt = {}
    counter = [0, node_limit]
    best_edge = moves[0]
    best_val = -99
    alpha, beta = -99, 99
    max_possible = _remaining_boxes(mask)

    for e in moves:
        if time.perf_counter() > deadline:
            raise _SearchTimeout()

        k = _cap_count(mask, e)
        nm = mask | (1 << e)

        if k:
            val = k + _ab(nm, alpha - k, beta - k, deadline, tt, counter)
        else:
            val = -_ab(nm, -beta, -alpha, deadline, tt, counter)

        if val > best_val:
            best_val = val
            best_edge = e

        if val > alpha:
            alpha = val

        if best_val >= max_possible:
            break

    _store_exact(mask, best_val)
    _store_best(mask, best_edge)
    return best_edge, best_val


def _simple_select(mask: int):
    caps, safe, risky = _classify_moves(mask)

    if caps:
        # If no safe moves remain, consider a control-preserving handout.
        if not safe:
            best_h = None
            best_hp = NEG_INF
            for e in risky:
                hp = _handoff_priority(mask, e)
                if hp > best_hp:
                    best_hp = hp
                    best_h = e
            if best_h is not None and best_hp > NEG_INF // 2:
                return best_h

        return max(caps, key=lambda e: _capture_priority_fast(mask, e))

    if safe:
        return max(safe, key=lambda e: _safe_priority_fast(mask, e))

    if risky:
        return max(risky, key=lambda e: _sacrifice_priority(mask, e))

    return None


def _rollout_value(mask: int, memo: dict) -> int:
    if mask in memo:
        return memo[mask]
    if mask == FULL_MASK:
        memo[mask] = 0
        return 0

    e = _simple_select(mask)
    if e is None:
        memo[mask] = 0
        return 0

    k = _cap_count(mask, e)
    nm = mask | (1 << e)

    if k:
        val = k + _rollout_value(nm, memo)
    else:
        val = -_rollout_value(nm, memo)

    memo[mask] = val
    return val


def _heuristic_move(mask: int):
    caps, safe, risky = _classify_moves(mask)
    if not caps and not safe and not risky:
        return None

    if caps:
        candidates = list(caps)
        if not safe:
            for e in risky:
                if _handoff_priority(mask, e) > NEG_INF // 2:
                    candidates.append(e)
    elif safe:
        candidates = list(safe)
    else:
        candidates = list(risky)

    seen = set()
    uniq = []
    for e in candidates:
        if e not in seen:
            seen.add(e)
            uniq.append(e)

    if not uniq:
        return None

    uniq.sort(key=lambda e: _root_priority(mask, e), reverse=True)

    memo = {FULL_MASK: 0}
    best_edge = uniq[0]
    best_score = -1e18

    for e in uniq:
        k = _cap_count(mask, e)
        nm = mask | (1 << e)

        if k:
            val = k + _rollout_value(nm, memo)
        else:
            val = -_rollout_value(nm, memo)

        score = 1000.0 * val + _root_priority(mask, e)
        if score > best_score:
            best_score = score
            best_edge = e

    return best_edge


def _opening_mirror_move(horizontal: np.ndarray, vertical: np.ndarray,
                         capture: np.ndarray, mask: int):
    # A conservative early response when we appear to be second player:
    # mirror opponent moves by 180 degrees while this remains safe.
    try:
        if int(np.count_nonzero(capture[:4, :4])) != 0:
            return None
    except Exception:
        return None

    if _has_capture(mask):
        return None

    my_edges = 0
    opp_edges = 0
    for e in range(EDGE_COUNT):
        val = _edge_value_array(e, horizontal, vertical)
        if val > 0:
            my_edges += 1
        elif val < 0:
            opp_edges += 1

    if opp_edges != my_edges + 1:
        return None

    cands = []
    for e in range(EDGE_COUNT):
        if _edge_value_array(e, horizontal, vertical) < 0:
            m = MIRROR_EDGE[e]
            if (mask & (1 << m)) == 0:
                if _cap_count(mask, m) == 0 and _third_count(mask, m) == 0:
                    cands.append(m)

    if not cands:
        return None

    return max(cands, key=lambda e: _safe_priority_root(mask, e))


def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    try:
        mask = _state_to_mask(horizontal, vertical)

        if (FULL_MASK ^ mask) == 0:
            return _first_legal_from_arrays(horizontal, vertical)

        cached_best = _BEST_CACHE.get(mask)
        if cached_best is not None and _edge_empty_array(cached_best, horizontal, vertical):
            return MOVE_STRINGS[cached_best]

        caps, safe, risky = _classify_moves(mask)
        remaining = EDGE_COUNT - mask.bit_count()

        # Early mirror response when safe and likely useful.
        if remaining > 24 and not caps and safe:
            mirror = _opening_mirror_move(horizontal, vertical, capture, mask)
            if mirror is not None and _edge_empty_array(mirror, horizontal, vertical):
                return MOVE_STRINGS[mirror]

        # Exact search is very strong in tactical/endgame states.
        should_search = (
            remaining <= 20
            or (caps and remaining <= 28)
            or ((not safe) and remaining <= 28)
        )

        if should_search:
            try:
                start = time.perf_counter()
                deadline = start + 0.82
                node_limit = 360000 if remaining <= 20 else 190000
                e, _ = _exact_best_move(mask, deadline, node_limit)
                if e is not None and _edge_empty_array(e, horizontal, vertical):
                    return MOVE_STRINGS[e]
            except _SearchTimeout:
                pass

        e = _heuristic_move(mask)
        if e is not None and _edge_empty_array(e, horizontal, vertical):
            return MOVE_STRINGS[e]

        return _first_legal_from_arrays(horizontal, vertical)

    except Exception:
        return _first_legal_from_arrays(horizontal, vertical)
