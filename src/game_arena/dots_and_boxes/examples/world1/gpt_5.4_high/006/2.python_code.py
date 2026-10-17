
import time
import numpy as np

# ---------- Board encoding ----------
# Standard 4x4 boxes:
# Horizontal edges: rows 0..4, cols 0..3  => 20 edges
# Vertical edges:   rows 0..3, cols 0..4  => 20 edges
# Total = 40 edges

BIT = [1 << i for i in range(40)]
FULL_MASK = (1 << 40) - 1

MOVE_STRINGS = []
EDGE_TO_BOXES = [[] for _ in range(40)]
BOX_EDGES = [[] for _ in range(16)]      # per box: [top, right, bottom, left]
BOX_NEIGHBORS = [[] for _ in range(16)]  # per box: [up, right, down, left]
BOX_MASKS = [0] * 16

def _h_idx(r, c):
    return r * 4 + c

def _v_idx(r, c):
    return 20 + r * 5 + c

def _init_tables():
    # Move strings
    for r in range(5):
        for c in range(4):
            MOVE_STRINGS.append(f"{r},{c},H")
    for r in range(4):
        for c in range(5):
            MOVE_STRINGS.append(f"{r},{c},V")

    # Boxes
    for r in range(4):
        for c in range(4):
            b = r * 4 + c
            top = _h_idx(r, c)
            right = _v_idx(r, c + 1)
            bottom = _h_idx(r + 1, c)
            left = _v_idx(r, c)

            BOX_EDGES[b] = [top, right, bottom, left]
            BOX_MASKS[b] = BIT[top] | BIT[right] | BIT[bottom] | BIT[left]

            up = (r - 1) * 4 + c if r > 0 else -1
            rt = r * 4 + (c + 1) if c < 3 else -1
            dn = (r + 1) * 4 + c if r < 3 else -1
            lf = r * 4 + (c - 1) if c > 0 else -1
            BOX_NEIGHBORS[b] = [up, rt, dn, lf]

            EDGE_TO_BOXES[top].append(b)
            EDGE_TO_BOXES[right].append(b)
            EDGE_TO_BOXES[bottom].append(b)
            EDGE_TO_BOXES[left].append(b)

_init_tables()

# ---------- Search globals ----------
_TT = {}  # mask -> (flag, value), flag: 0 exact, 1 lower, 2 upper
_DEADLINE = 0.0
_NODE_COUNTER = 0

class _SearchTimeout(Exception):
    pass

# ---------- Basic helpers ----------
def _array_to_mask(horizontal: np.ndarray, vertical: np.ndarray) -> int:
    mask = 0
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] != 0:
                mask |= BIT[_h_idx(r, c)]
    for r in range(4):
        for c in range(5):
            if vertical[r, c] != 0:
                mask |= BIT[_v_idx(r, c)]
    return mask

def _legal_moves(mask: int):
    return [i for i in range(40) if not (mask & BIT[i])]

def _box_counts(mask: int):
    return [(mask & BOX_MASKS[b]).bit_count() for b in range(16)]

def _captured_by_move(counts, move: int) -> int:
    # Move is assumed legal.
    total = 0
    for b in EDGE_TO_BOXES[move]:
        if counts[b] == 3:
            total += 1
    return total

def _is_safe_move(counts, move: int) -> bool:
    for b in EDGE_TO_BOXES[move]:
        c = counts[b]
        if c >= 2:  # 2 -> creates 3-side box, 3 -> capture
            return False
    return True

def _safe_score(counts, move: int) -> float:
    # Prefer boundary moves; avoid making 2-sided boxes.
    adj = EDGE_TO_BOXES[move]
    score = 2.0 if len(adj) == 1 else 0.5
    for b in adj:
        c = counts[b]
        if c == 0:
            score += 1.0
        elif c == 1:
            score -= 1.5
    return score

def _forced_component_damage(mask_after: int, start_boxes):
    # Estimate size of the opened chain/loop after a risky move.
    # Traverse only boxes with counts in {2,3}, because those participate
    # in immediate/near-immediate capture chains.
    counts = _box_counts(mask_after)
    seen = set(start_boxes)
    stack = list(start_boxes)
    size = 0
    boundary_stubs = 0
    internal_links = 0

    while stack:
        b = stack.pop()
        size += 1

        edges = BOX_EDGES[b]
        neighbors = BOX_NEIGHBORS[b]
        for side in range(4):
            e = edges[side]
            if mask_after & BIT[e]:
                continue
            nb = neighbors[side]
            if nb == -1:
                boundary_stubs += 1
            else:
                if 2 <= counts[nb] < 4:
                    internal_links += 1
                    if nb not in seen:
                        seen.add(nb)
                        stack.append(nb)

    internal_links //= 2
    damage = float(size)
    if boundary_stubs == 0:
        damage += 0.5  # loop-ish
    if boundary_stubs not in (0, 2):
        damage += 0.5  # weird / complex
    return damage

def _risk_damage(mask: int, move: int, counts=None) -> float:
    if counts is None:
        counts = _box_counts(mask)
    new_mask = mask | BIT[move]
    starts = []
    for b in EDGE_TO_BOXES[move]:
        if counts[b] == 2:
            starts.append(b)
    if not starts:
        return 0.0
    return _forced_component_damage(new_mask, starts)

def _classify_moves(mask: int, counts=None):
    if counts is None:
        counts = _box_counts(mask)
    captures = []  # list of (move, k)
    safe = []
    risky = []

    for move in range(40):
        if mask & BIT[move]:
            continue
        k = _captured_by_move(counts, move)
        if k > 0:
            captures.append((move, k))
        elif _is_safe_move(counts, move):
            safe.append(move)
        else:
            risky.append(move)
    return captures, safe, risky

def _heuristic_move(mask: int) -> int:
    counts = _box_counts(mask)
    captures, safe, risky = _classify_moves(mask, counts)

    if captures:
        captures.sort(key=lambda mk: (mk[1], 1 if len(EDGE_TO_BOXES[mk[0]]) == 1 else 0), reverse=True)
        return captures[0][0]

    if safe:
        safe.sort(key=lambda m: (_safe_score(counts, m), -m), reverse=True)
        return safe[0]

    risky.sort(key=lambda m: (_risk_damage(mask, m, counts), m))
    return risky[0]

# ---------- Exact search ----------
def _ordered_moves(mask: int):
    counts = _box_counts(mask)
    captures, safe, risky = _classify_moves(mask, counts)

    ordered = []
    if captures:
        # Captures first, then low-damage non-captures (handout candidates), then safe.
        captures.sort(key=lambda mk: (mk[1], 1 if len(EDGE_TO_BOXES[mk[0]]) == 1 else 0), reverse=True)
        risky.sort(key=lambda m: (_risk_damage(mask, m, counts), m))
        safe.sort(key=lambda m: (_safe_score(counts, m), -m), reverse=True)
        ordered.extend(captures)
        ordered.extend((m, 0) for m in risky)
        ordered.extend((m, 0) for m in safe)
    else:
        safe.sort(key=lambda m: (_safe_score(counts, m), -m), reverse=True)
        risky.sort(key=lambda m: (_risk_damage(mask, m, counts), m))
        ordered.extend((m, 0) for m in safe)
        ordered.extend((m, 0) for m in risky)

    return ordered

def _negamax_exact(mask: int, alpha: int, beta: int) -> int:
    global _NODE_COUNTER

    if mask == FULL_MASK:
        return 0

    _NODE_COUNTER += 1
    if (_NODE_COUNTER & 511) == 0 and time.perf_counter() > _DEADLINE:
        raise _SearchTimeout

    alpha0 = alpha
    beta0 = beta

    entry = _TT.get(mask)
    if entry is not None:
        flag, val = entry
        if flag == 0:
            return val
        elif flag == 1:  # lower bound
            if val > alpha:
                alpha = val
        else:  # upper bound
            if val < beta:
                beta = val
        if alpha >= beta:
            return val

    best = -99

    for move, k in _ordered_moves(mask):
        new_mask = mask | BIT[move]
        if k > 0:
            val = k + _negamax_exact(new_mask, alpha - k, beta - k)
        else:
            val = -_negamax_exact(new_mask, -beta, -alpha)

        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    if best <= alpha0:
        _TT[mask] = (2, best)  # upper bound
    elif best >= beta0:
        _TT[mask] = (1, best)  # lower bound
    else:
        _TT[mask] = (0, best)  # exact

    return best

def _exact_best_move(mask: int):
    counts = _box_counts(mask)
    captures, safe, risky = _classify_moves(mask, counts)

    # Root ordering
    if captures:
        captures.sort(key=lambda mk: (mk[1], 1 if len(EDGE_TO_BOXES[mk[0]]) == 1 else 0), reverse=True)
        risky.sort(key=lambda m: (_risk_damage(mask, m, counts), m))
        safe.sort(key=lambda m: (_safe_score(counts, m), -m), reverse=True)
        ordered = captures + [(m, 0) for m in risky] + [(m, 0) for m in safe]
    else:
        safe.sort(key=lambda m: (_safe_score(counts, m), -m), reverse=True)
        risky.sort(key=lambda m: (_risk_damage(mask, m, counts), m))
        ordered = [(m, 0) for m in safe] + [(m, 0) for m in risky]

    best_move = ordered[0][0]
    best_val = -99
    alpha = -99
    beta = 99

    for move, k in ordered:
        new_mask = mask | BIT[move]
        if k > 0:
            val = k + _negamax_exact(new_mask, alpha - k, beta - k)
        else:
            val = -_negamax_exact(new_mask, -beta, -alpha)

        if val > best_val:
            best_val = val
            best_move = move
        if val > alpha:
            alpha = val

    return best_move, best_val

# ---------- Rollout fallback ----------
def _rollout_continue(mask: int, current_sign: int) -> int:
    # current_sign = +1 if root player to move now, -1 if opponent to move now
    score = 0

    while mask != FULL_MASK:
        rem = 40 - mask.bit_count()

        # If small enough and we still have time, finish exactly.
        if rem <= 10 and time.perf_counter() < _DEADLINE - 0.01:
            try:
                score += current_sign * _negamax_exact(mask, -99, 99)
                return score
            except _SearchTimeout:
                pass

        move = _heuristic_move(mask)
        counts = _box_counts(mask)
        k = _captured_by_move(counts, move)
        mask |= BIT[move]
        score += current_sign * k
        if k == 0:
            current_sign = -current_sign

    return score

def _evaluate_move(mask: int, move: int) -> int:
    counts = _box_counts(mask)
    k = _captured_by_move(counts, move)
    new_mask = mask | BIT[move]
    if k > 0:
        return k + _rollout_continue(new_mask, +1)
    return _rollout_continue(new_mask, -1)

# ---------- Safety fallback ----------
def _first_legal_move_string(horizontal: np.ndarray, vertical: np.ndarray) -> str:
    # Prefer standard valid edges.
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] == 0:
                return f"{r},{c},H"
    for r in range(4):
        for c in range(5):
            if vertical[r, c] == 0:
                return f"{r},{c},V"

    # Extreme fallback if the environment ever uses extra cells.
    for r in range(horizontal.shape[0]):
        for c in range(horizontal.shape[1]):
            if horizontal[r, c] == 0:
                return f"{r},{c},H"
    for r in range(vertical.shape[0]):
        for c in range(vertical.shape[1]):
            if vertical[r, c] == 0:
                return f"{r},{c},V"

    return "0,0,H"

# ---------- Public API ----------
def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    global _DEADLINE, _NODE_COUNTER

    # Keep TT bounded.
    if len(_TT) > 400000:
        _TT.clear()

    start = time.perf_counter()
    _DEADLINE = start + 0.90
    _NODE_COUNTER = 0

    mask = _array_to_mask(horizontal, vertical)
    legal = _legal_moves(mask)

    if not legal:
        return _first_legal_move_string(horizontal, vertical)
    if len(legal) == 1:
        mv = legal[0]
        s = MOVE_STRINGS[mv]
        # Validate against arrays just in case.
        if mv < 20:
            r, c = divmod(mv, 4)
            if horizontal[r, c] == 0:
                return s
        else:
            x = mv - 20
            r, c = divmod(x, 5)
            if vertical[r, c] == 0:
                return s
        return _first_legal_move_string(horizontal, vertical)

    counts = _box_counts(mask)
    captures, safe, risky = _classify_moves(mask, counts)
    remaining = len(legal)

    # Tactical / endgame exact solve.
    try_exact = False
    if remaining <= 14:
        try_exact = True
    elif remaining <= 20 and (captures or not safe):
        try_exact = True

    if try_exact:
        try:
            best_move, _ = _exact_best_move(mask)
            out = MOVE_STRINGS[best_move]
            if best_move < 20:
                r, c = divmod(best_move, 4)
                if horizontal[r, c] == 0:
                    return out
            else:
                x = best_move - 20
                r, c = divmod(x, 5)
                if vertical[r, c] == 0:
                    return out
        except _SearchTimeout:
            pass

    # Fallback candidate shortlist + heuristic rollout evaluation.
    candidates = []

    if captures:
        captures.sort(key=lambda mk: (mk[1], 1 if len(EDGE_TO_BOXES[mk[0]]) == 1 else 0), reverse=True)
        candidates.extend([m for m, _ in captures])

        # Add a few non-capturing candidates to allow handout/control ideas.
        if risky:
            risky.sort(key=lambda m: (_risk_damage(mask, m, counts), m))
            candidates.extend(risky[:2])
        if safe:
            safe.sort(key=lambda m: (_safe_score(counts, m), -m), reverse=True)
            candidates.extend(safe[:1])

    elif safe:
        safe.sort(key=lambda m: (_safe_score(counts, m), -m), reverse=True)
        candidates.extend(safe[:8])

    else:
        risky.sort(key=lambda m: (_risk_damage(mask, m, counts), m))
        candidates.extend(risky[:8])

    # Deduplicate while preserving order.
    seen = set()
    candidates = [m for m in candidates if not (m in seen or seen.add(m))]

    if not candidates:
        return _first_legal_move_string(horizontal, vertical)

    # If time is nearly gone, return top heuristic candidate immediately.
    if time.perf_counter() > _DEADLINE - 0.03:
        best_move = candidates[0]
        out = MOVE_STRINGS[best_move]
        if best_move < 20:
            r, c = divmod(best_move, 4)
            if horizontal[r, c] == 0:
                return out
        else:
            x = best_move - 20
            r, c = divmod(x, 5)
            if vertical[r, c] == 0:
                return out
        return _first_legal_move_string(horizontal, vertical)

    best_move = candidates[0]
    best_val = -999

    for mv in candidates:
        val = _evaluate_move(mask, mv)
        if val > best_val:
            best_val = val
            best_move = mv
        if time.perf_counter() > _DEADLINE:
            break

    out = MOVE_STRINGS[best_move]
    if best_move < 20:
        r, c = divmod(best_move, 4)
        if horizontal[r, c] == 0:
            return out
    else:
        x = best_move - 20
        r, c = divmod(x, 5)
        if vertical[r, c] == 0:
            return out

    return _first_legal_move_string(horizontal, vertical)
