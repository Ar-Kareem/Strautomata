
import time
import numpy as np

# ---------- Board constants for a 4x4 Dots and Boxes board ----------
# Valid horizontal edges: row 0..4, col 0..3  -> 20 edges
# Valid vertical edges:   row 0..3, col 0..4  -> 20 edges

N = 4
NUM_BOXES = 16

EDGE_MOVES = []
EDGE_BOXES = []
BOX_EDGES = [[] for _ in range(NUM_BOXES)]

# Horizontal edges, ids 0..19
for r in range(5):
    for c in range(4):
        e = len(EDGE_MOVES)
        EDGE_MOVES.append((r, c, "H"))
        boxes = []
        if r > 0:
            boxes.append((r - 1) * 4 + c)
        if r < 4:
            boxes.append(r * 4 + c)
        EDGE_BOXES.append(tuple(boxes))
        for b in boxes:
            BOX_EDGES[b].append(e)

# Vertical edges, ids 20..39
for r in range(4):
    for c in range(5):
        e = len(EDGE_MOVES)
        EDGE_MOVES.append((r, c, "V"))
        boxes = []
        if c > 0:
            boxes.append(r * 4 + (c - 1))
        if c < 4:
            boxes.append(r * 4 + c)
        EDGE_BOXES.append(tuple(boxes))
        for b in boxes:
            BOX_EDGES[b].append(e)

NUM_EDGES = len(EDGE_MOVES)
EDGE_BITS = tuple(1 << i for i in range(NUM_EDGES))
BOX_MASKS = tuple(sum(EDGE_BITS[e] for e in edges) for edges in BOX_EDGES)
FULL_MASK = (1 << NUM_EDGES) - 1

# Mild preference for central edges as a tie-breaker.
_CENTER_PREF = []
for r, c, d in EDGE_MOVES:
    if d == "H":
        y, x = float(r), float(c) + 0.5
    else:
        y, x = float(r) + 0.5, float(c)
    dist2 = (x - 2.0) ** 2 + (y - 2.0) ** 2
    _CENTER_PREF.append(4.0 - dist2)
CENTER_PREF = tuple(_CENTER_PREF)


# ---------- Basic utilities ----------

def _state_to_mask(horizontal: np.ndarray, vertical: np.ndarray) -> int:
    mask = 0
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] != 0:
                mask |= EDGE_BITS[r * 4 + c]
    for r in range(4):
        for c in range(5):
            if vertical[r, c] != 0:
                mask |= EDGE_BITS[20 + r * 5 + c]
    return mask


def _edge_to_string(e: int) -> str:
    r, c, d = EDGE_MOVES[e]
    return f"{r},{c},{d}"


def _iter_empty_edges(mask: int):
    m = FULL_MASK ^ mask
    while m:
        lsb = m & -m
        e = lsb.bit_length() - 1
        yield e
        m ^= lsb


def _box_counts(mask: int):
    return [(mask & bm).bit_count() for bm in BOX_MASKS]


def _remaining_boxes(mask: int) -> int:
    rem = 0
    for bm in BOX_MASKS:
        if (mask & bm) != bm:
            rem += 1
    return rem


def _captured_count(mask: int, e: int, counts=None) -> int:
    n = 0
    if counts is None:
        for b in EDGE_BOXES[e]:
            if (mask & BOX_MASKS[b]).bit_count() == 3:
                n += 1
    else:
        for b in EDGE_BOXES[e]:
            if counts[b] == 3:
                n += 1
    return n


def _created_threat_count(mask: int, e: int, counts=None) -> int:
    n = 0
    if counts is None:
        for b in EDGE_BOXES[e]:
            if (mask & BOX_MASKS[b]).bit_count() == 2:
                n += 1
    else:
        for b in EDGE_BOXES[e]:
            if counts[b] == 2:
                n += 1
    return n


def _classify_moves_from_counts(mask: int, counts):
    captures, safe, loony = [], [], []
    for e in _iter_empty_edges(mask):
        cap = 0
        risk = 0
        for b in EDGE_BOXES[e]:
            cb = counts[b]
            if cb == 3:
                cap += 1
            elif cb == 2:
                risk += 1
        if cap:
            captures.append(e)
        elif risk:
            loony.append(e)
        else:
            safe.append(e)
    return captures, safe, loony


def _count_safe_moves(mask: int, counts=None) -> int:
    if counts is None:
        counts = _box_counts(mask)
    n = 0
    for e in _iter_empty_edges(mask):
        ok = True
        for b in EDGE_BOXES[e]:
            if counts[b] >= 2:
                ok = False
                break
        if ok:
            n += 1
    return n


def _fallback_legal(horizontal: np.ndarray, vertical: np.ndarray) -> str:
    # Prefer physically valid 4x4-board edges.
    try:
        for r in range(5):
            for c in range(4):
                if horizontal[r, c] == 0:
                    return f"{r},{c},H"
        for r in range(4):
            for c in range(5):
                if vertical[r, c] == 0:
                    return f"{r},{c},V"

        # If an arena treats padded 5x5 entries as legal, this may still save us
        # in an otherwise terminal/padded state.
        for r in range(5):
            for c in range(5):
                if horizontal[r, c] == 0:
                    return f"{r},{c},H"
        for r in range(5):
            for c in range(5):
                if vertical[r, c] == 0:
                    return f"{r},{c},V"
    except Exception:
        pass

    # Should only occur if no legal move exists.
    return "0,0,H"


# ---------- Chain/component heuristics ----------

def _component_info(mask: int, counts=None):
    if counts is None:
        counts = _box_counts(mask)

    comp = [-1] * NUM_BOXES
    sizes = []
    boundary_openings = []

    for start in range(NUM_BOXES):
        if counts[start] >= 4 or comp[start] != -1:
            continue

        cid = len(sizes)
        comp[start] = cid
        stack = [start]
        size = 0
        bnd = 0

        while stack:
            b = stack.pop()
            size += 1

            for e in BOX_EDGES[b]:
                if mask & EDGE_BITS[e]:
                    continue

                eb = EDGE_BOXES[e]
                if len(eb) == 1:
                    bnd += 1
                else:
                    nb = eb[0] + eb[1] - b
                    if counts[nb] < 4 and comp[nb] == -1:
                        comp[nb] = cid
                        stack.append(nb)

        sizes.append(size)
        boundary_openings.append(bnd)

    return comp, sizes, boundary_openings


def _donation_size(mask: int, e: int, counts=None, comp_data=None) -> int:
    if counts is None:
        counts = _box_counts(mask)
    if comp_data is None:
        comp_data = _component_info(mask, counts)

    comp, sizes, _ = comp_data
    seen = set()
    total = 0

    for b in EDGE_BOXES[e]:
        if counts[b] == 2:
            cid = comp[b]
            if cid >= 0 and cid not in seen:
                seen.add(cid)
                total += sizes[cid]

    return total


def _min_opening_donation(mask: int, counts=None) -> int:
    if counts is None:
        counts = _box_counts(mask)

    comp_data = _component_info(mask, counts)
    best = 99

    for e in _iter_empty_edges(mask):
        if _captured_count(mask, e, counts) > 0:
            continue
        if _created_threat_count(mask, e, counts) == 0:
            continue
        d = _donation_size(mask, e, counts, comp_data)
        if d < best:
            best = d

    return 0 if best == 99 else best


# ---------- Exact alpha-beta endgame solver ----------

_TT = {FULL_MASK: 0}
_DEADLINE = 0.0
_NODES = 0


class _SearchTimeout(Exception):
    pass


def _check_timeout():
    global _NODES
    _NODES += 1
    if (_NODES & 2047) == 0 and time.perf_counter() > _DEADLINE:
        raise _SearchTimeout()


def _ordered_moves(mask: int):
    counts = _box_counts(mask)
    captures = []
    safe = []
    risky = []

    for e in _iter_empty_edges(mask):
        cap = 0
        risk = 0
        made_twos = 0
        side_sum = 0

        for b in EDGE_BOXES[e]:
            cb = counts[b]
            side_sum += cb
            if cb == 3:
                cap += 1
            elif cb == 2:
                risk += 1
            elif cb == 1:
                made_twos += 1

        if cap:
            # Captures first, double-captures first, then captures that continue chains.
            captures.append(((-cap, -risk, -CENTER_PREF[e]), e, cap))
        elif risk == 0:
            # Safe moves before loony moves.
            safe.append(((made_twos, side_sum, -CENTER_PREF[e]), e, 0))
        else:
            # If forced to give something, give fewer immediate threats first.
            risky.append(((risk, side_sum, -CENTER_PREF[e]), e, 0))

    captures.sort(key=lambda x: x[0])
    safe.sort(key=lambda x: x[0])
    risky.sort(key=lambda x: x[0])

    return [(e, c) for _, e, c in captures] + [(e, c) for _, e, c in safe] + [(e, c) for _, e, c in risky]


def _ab(mask: int, alpha: int, beta: int) -> int:
    _check_timeout()

    if mask in _TT:
        return _TT[mask]

    rem = _remaining_boxes(mask)
    if rem == 0:
        _TT[mask] = 0
        return 0

    best = -99
    a = alpha

    for e, c in _ordered_moves(mask):
        nm = mask | EDGE_BITS[e]

        if c:
            val = c + _ab(nm, a - c, beta - c)
        else:
            val = -_ab(nm, -beta, -a)

        if val > best:
            best = val
        if val > a:
            a = val

        # Cannot do better than winning every remaining box.
        if best == rem:
            _TT[mask] = best
            return best

        if a >= beta:
            # Cutoff; do not store as exact.
            return best

    _TT[mask] = best
    return best


def _capture_static_score(mask: int, e: int, counts) -> float:
    c = _captured_count(mask, e, counts)
    nm = mask | EDGE_BITS[e]
    next_counts = _box_counts(nm)
    next_caps, next_safe, _ = _classify_moves_from_counts(nm, next_counts)

    score = 100.0 * c + 12.0 * len(next_caps)

    # If this capture ends the run, prefer ending with safe moves available;
    # being forced to open a chain is bad.
    if not next_caps:
        rem = _remaining_boxes(nm)
        if next_safe:
            score += min(10, len(next_safe))
        elif rem > 0:
            score -= 15.0 * _min_opening_donation(nm, next_counts)

    score += 0.1 * CENTER_PREF[e]
    return score


def _safe_static_score(mask: int, e: int, counts) -> float:
    nm = mask | EDGE_BITS[e]

    made_twos = 0
    side_sum = 0
    touched = len(EDGE_BOXES[e])

    for b in EDGE_BOXES[e]:
        side_sum += counts[b]
        if counts[b] == 1:
            made_twos += 1

    next_counts = _box_counts(nm)
    opp_safe = _count_safe_moves(nm, next_counts)

    # Approximate normal-play parity of the safe-move phase:
    # after our safe move, opponent to move with an even number of safe moves
    # is usually better for us.
    parity_bonus = 6.0 if (opp_safe % 2 == 0) else -6.0

    score = parity_bonus
    score -= 8.0 * made_twos
    score -= 2.0 * side_sum
    score += 1.5 * touched
    score += 0.25 * CENTER_PREF[e]

    if opp_safe == 0:
        # Opponent is probably forced to open; larger minimum donation is better.
        score += 40.0 + 8.0 * _min_opening_donation(nm, next_counts)

    return score


def _opening_static_score(mask: int, e: int, counts, comp_data=None) -> float:
    threats = _created_threat_count(mask, e, counts)
    donation = _donation_size(mask, e, counts, comp_data)
    boundary = 1 if len(EDGE_BOXES[e]) == 1 else 0

    # Lower donation is better. Prefer boundary openings and fewer simultaneous
    # three-sided boxes.
    score = -100.0 * donation
    score -= 25.0 * threats
    score += 8.0 * boundary
    score += 0.2 * CENTER_PREF[e]
    return score


def _root_tie_score(mask: int, e: int, counts=None) -> float:
    if counts is None:
        counts = _box_counts(mask)

    c = _captured_count(mask, e, counts)
    if c:
        return _capture_static_score(mask, e, counts)

    if _created_threat_count(mask, e, counts) == 0:
        return _safe_static_score(mask, e, counts)

    comp_data = _component_info(mask, counts)
    return _opening_static_score(mask, e, counts, comp_data)


def _choose_exact(mask: int, budget: float):
    global _DEADLINE, _NODES, _TT

    if len(_TT) > 600000:
        _TT = {FULL_MASK: 0}

    _DEADLINE = time.perf_counter() + budget
    _NODES = 0

    moves = _ordered_moves(mask)
    if not moves:
        return None

    rem = _remaining_boxes(mask)
    alpha = -rem
    beta = rem

    counts = _box_counts(mask)
    best_e = moves[0][0]
    best_v = -99
    best_tie = -1e18

    for e, c in moves:
        _check_timeout()
        nm = mask | EDGE_BITS[e]

        if c:
            val = c + _ab(nm, alpha - c, beta - c)
        else:
            val = -_ab(nm, -beta, -alpha)

        tie = _root_tie_score(mask, e, counts)
        if val > best_v or (val == best_v and tie > best_tie):
            best_v = val
            best_e = e
            best_tie = tie

        if val > alpha:
            alpha = val

        if best_v == rem:
            break

    _TT[mask] = best_v
    return best_e


def _try_exact(mask: int, empties: int, captures, safe):
    # Exact search is strongest in the tactical/endgame phase.
    if not (empties <= 18 or (empties <= 22 and (captures or not safe))):
        return None

    budget = 0.70 if empties <= 18 else 0.55

    try:
        return _choose_exact(mask, budget)
    except _SearchTimeout:
        return None
    except Exception:
        return None


# ---------- Fast heuristic rollout / fallback policy ----------

def _quick_safe_order(mask: int, e: int, counts) -> float:
    made_twos = 0
    side_sum = 0
    for b in EDGE_BOXES[e]:
        side_sum += counts[b]
        if counts[b] == 1:
            made_twos += 1
    return -10.0 * made_twos - side_sum + 0.2 * CENTER_PREF[e]


class _ParityAbort(Exception):
    pass


def _safe_parity(mask: int, depth: int, memo, nodes, limit: int) -> int:
    nodes[0] += 1
    if nodes[0] > limit:
        raise _ParityAbort()

    key = (mask, depth)
    if key in memo:
        return memo[key]

    counts = _box_counts(mask)
    captures, safe, _ = _classify_moves_from_counts(mask, counts)

    if captures:
        memo[key] = 1
        return 1

    if not safe:
        memo[key] = -1
        return -1

    if depth <= 0:
        val = 1 if (len(safe) % 2 == 1) else -1
        memo[key] = val
        return val

    ordered = sorted(safe, key=lambda x: _quick_safe_order(mask, x, counts), reverse=True)
    if len(ordered) > 10 and depth < len(safe):
        ordered = ordered[:10]

    best = -1
    for e in ordered:
        val = -_safe_parity(mask | EDGE_BITS[e], depth - 1, memo, nodes, limit)
        if val > best:
            best = val
            if best == 1:
                break

    memo[key] = best
    return best


def _handout_candidates(mask: int, counts, captures, safe, loony):
    # Conservative hard-hearted handout detection. Only considered when there
    # are captures, no safe moves, and enough boxes remain that control matters.
    if not captures or safe or _remaining_boxes(mask) <= 4:
        return []

    comp_data = _component_info(mask, counts)
    cand = []

    for e in loony:
        if _created_threat_count(mask, e, counts) >= 2:
            cand.append((_opening_static_score(mask, e, counts, comp_data), e))

    cand.sort(reverse=True)
    return [e for _, e in cand[:4]]


def _greedy_move(mask: int):
    counts = _box_counts(mask)
    captures, safe, loony = _classify_moves_from_counts(mask, counts)

    if captures:
        best_cap = max(captures, key=lambda e: _capture_static_score(mask, e, counts))

        # In rollouts, make a simple control-preserving handout if taking the
        # capture would immediately force us to open another chain.
        hs = _handout_candidates(mask, counts, captures, safe, loony)
        if hs and _remaining_boxes(mask) > 4:
            nm = mask | EDGE_BITS[best_cap]
            nc = _box_counts(nm)
            next_caps, next_safe, _ = _classify_moves_from_counts(nm, nc)
            if not next_caps and not next_safe:
                return hs[0]

        return best_cap

    if safe:
        return max(safe, key=lambda e: _safe_static_score(mask, e, counts))

    if loony:
        comp_data = _component_info(mask, counts)
        return max(loony, key=lambda e: _opening_static_score(mask, e, counts, comp_data))

    return None


def _rollout_value(mask: int) -> int:
    # Deterministic playout with the same heuristic for both sides.
    # Return future score difference for the player to move at 'mask'.
    score = 0
    turn = 1
    cur = mask
    steps = 0

    while cur != FULL_MASK and steps < NUM_EDGES + 2:
        e = _greedy_move(cur)
        if e is None or (cur & EDGE_BITS[e]):
            break

        c = _captured_count(cur, e)
        cur |= EDGE_BITS[e]

        if c:
            score += turn * c
        else:
            turn = -turn

        steps += 1

    return score


def _move_rollout_value(mask: int, e: int, counts=None) -> int:
    if counts is None:
        counts = _box_counts(mask)
    c = _captured_count(mask, e, counts)
    nm = mask | EDGE_BITS[e]

    if c:
        return c + _rollout_value(nm)
    return -_rollout_value(nm)


def _choose_heuristic(mask: int, allow_parity: bool = True):
    counts = _box_counts(mask)
    captures, safe, loony = _classify_moves_from_counts(mask, counts)

    if captures:
        candidates = list(captures)
        for e in _handout_candidates(mask, counts, captures, safe, loony):
            if e not in candidates:
                candidates.append(e)
    elif safe:
        candidates = list(safe)
    else:
        candidates = list(loony)

    if not candidates:
        return None

    comp_data = None
    if not captures and not safe:
        comp_data = _component_info(mask, counts)

    use_parity = bool(allow_parity and (not captures) and safe and len(safe) <= 18)
    parity_memo = {}
    parity_nodes = [0]
    parity_depth = 0
    parity_limit = 0

    if use_parity:
        if len(safe) <= 14:
            parity_depth = max(0, len(safe) - 1)
            parity_limit = 80000
        else:
            parity_depth = 6
            parity_limit = 25000

    best_e = candidates[0]
    best_score = -1e18

    for e in candidates:
        if captures and e in captures:
            static = _capture_static_score(mask, e, counts)
        elif _created_threat_count(mask, e, counts) == 0:
            static = _safe_static_score(mask, e, counts)
        else:
            if comp_data is None:
                comp_data = _component_info(mask, counts)
            static = _opening_static_score(mask, e, counts, comp_data)

        parity_bonus = 0.0
        if use_parity and e in safe:
            try:
                opp_val = _safe_parity(
                    mask | EDGE_BITS[e],
                    parity_depth,
                    parity_memo,
                    parity_nodes,
                    parity_limit,
                )
                parity_bonus = -500.0 * opp_val
            except _ParityAbort:
                use_parity = False
                parity_bonus = 0.0

        rollout = _move_rollout_value(mask, e, counts)

        # Rollout score is primary; static/parity are tie-breakers and tactical
        # nudges.
        score = 10000.0 * rollout + parity_bonus + static

        if score > best_score:
            best_score = score
            best_e = e

    return best_e


# ---------- Required API ----------

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    try:
        mask = _state_to_mask(horizontal, vertical)

        if mask == FULL_MASK:
            return _fallback_legal(horizontal, vertical)

        counts = _box_counts(mask)
        captures, safe, _ = _classify_moves_from_counts(mask, counts)
        empties = (FULL_MASK ^ mask).bit_count()

        exact_move = _try_exact(mask, empties, captures, safe)
        if exact_move is not None and (mask & EDGE_BITS[exact_move]) == 0:
            return _edge_to_string(exact_move)

        heuristic_move = _choose_heuristic(mask, allow_parity=True)
        if heuristic_move is not None and (mask & EDGE_BITS[heuristic_move]) == 0:
            return _edge_to_string(heuristic_move)

    except Exception:
        pass

    return _fallback_legal(horizontal, vertical)
