
import time
from functools import lru_cache
import numpy as np

# ---------------------------------------------------------------------
# Board model: real 4x4-box Dots and Boxes edges only
# Horizontal: rows 0..4, cols 0..3  => 20 edges
# Vertical:   rows 0..3, cols 0..4  => 20 edges
# Total real edges = 40
# ---------------------------------------------------------------------

TOTAL_REAL_EDGES = 40
EXACT_THRESHOLD = 18          # exact solve when <= this many real edges remain
SAFE_SEARCH_THRESHOLD = 28    # do shallow safe-move search near the transition
TIME_BUDGET = 0.88            # leave a little margin under 1 second
POPCOUNT = int.bit_count

def _h_idx(r: int, c: int) -> int:
    return r * 4 + c

def _v_idx(r: int, c: int) -> int:
    return 20 + r * 5 + c

EDGE_BITS = tuple(1 << e for e in range(TOTAL_REAL_EDGES))
MOVE_STR = [None] * TOTAL_REAL_EDGES
MOVE_BOXES = [[] for _ in range(TOTAL_REAL_EDGES)]
BOX_MASKS = [0] * 16

# Move strings
for r in range(5):
    for c in range(4):
        MOVE_STR[_h_idx(r, c)] = f"{r},{c},H"
for r in range(4):
    for c in range(5):
        MOVE_STR[_v_idx(r, c)] = f"{r},{c},V"

# Box masks and edge->adjacent-box mapping
for r in range(4):
    for c in range(4):
        b = r * 4 + c
        edges = (
            _h_idx(r, c),       # top
            _h_idx(r + 1, c),   # bottom
            _v_idx(r, c),       # left
            _v_idx(r, c + 1),   # right
        )
        mask = 0
        for e in edges:
            mask |= EDGE_BITS[e]
            MOVE_BOXES[e].append(b)
        BOX_MASKS[b] = mask

# For each edge, masks that must already be present to complete each adjacent box
COMPLETE_NEEDS = [
    tuple(BOX_MASKS[b] ^ EDGE_BITS[e] for b in MOVE_BOXES[e])
    for e in range(TOTAL_REAL_EDGES)
]

FULL_MASK = (1 << TOTAL_REAL_EDGES) - 1


# ---------------------------------------------------------------------
# Core state helpers
# ---------------------------------------------------------------------

def _arrays_to_mask(horizontal: np.ndarray, vertical: np.ndarray) -> int:
    mask = 0

    # Real horizontal edges
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] != 0:
                mask |= EDGE_BITS[_h_idx(r, c)]

    # Real vertical edges
    for r in range(4):
        for c in range(5):
            if vertical[r, c] != 0:
                mask |= EDGE_BITS[_v_idx(r, c)]

    return mask


def _move_gain(mask: int, e: int) -> int:
    # Number of boxes completed by drawing edge e
    g = 0
    for need in COMPLETE_NEEDS[e]:
        if (mask & need) == need:
            g += 1
    return g


@lru_cache(maxsize=300_000)
def _has_capture(mask: int) -> bool:
    # A capturable box has exactly one open edge
    for bm in BOX_MASKS:
        if 4 - POPCOUNT(mask & bm) == 1:
            return True
    return False


@lru_cache(maxsize=300_000)
def _capture_run_best(mask: int) -> int:
    """
    Maximum number of boxes the current player can collect immediately
    by continuing to take capture moves only.
    Used as a chain/loop size approximation.
    """
    if not _has_capture(mask):
        return 0

    best = 0
    for e in range(TOTAL_REAL_EDGES):
        bit = EDGE_BITS[e]
        if mask & bit:
            continue
        g = _move_gain(mask, e)
        if g > 0:
            v = g + _capture_run_best(mask | bit)
            if v > best:
                best = v
    return best


@lru_cache(maxsize=200_000)
def _count_safe_moves(mask: int) -> int:
    cnt = 0
    for e in range(TOTAL_REAL_EDGES):
        bit = EDGE_BITS[e]
        if mask & bit:
            continue
        if _move_gain(mask, e) == 0 and not _has_capture(mask | bit):
            cnt += 1
    return cnt


@lru_cache(maxsize=200_000)
def _estimate_opening_loss(mask: int) -> int:
    """
    If the current player must play a non-capturing move,
    estimate the smallest immediate run the opponent can then take.
    """
    best = 99
    found = False
    for e in range(TOTAL_REAL_EDGES):
        bit = EDGE_BITS[e]
        if mask & bit:
            continue
        if _move_gain(mask, e) == 0:
            found = True
            loss = _capture_run_best(mask | bit)
            if loss < best:
                best = loss
                if best == 0:
                    break
    return 0 if not found else best


@lru_cache(maxsize=100_000)
def _leaf_eval(mask: int) -> float:
    """
    Heuristic evaluation from the current player's perspective.
    Only used when search depth runs out in quiet/no-capture states.
    """
    if mask == FULL_MASK:
        return 0.0

    if _has_capture(mask):
        return float(_capture_run_best(mask))

    safe_ct = _count_safe_moves(mask)
    if safe_ct:
        two_open = 0
        three_open = 0
        for bm in BOX_MASKS:
            oc = 4 - POPCOUNT(mask & bm)
            if oc == 2:
                two_open += 1
            elif oc == 3:
                three_open += 1
        return 0.10 * safe_ct + 0.04 * three_open - 0.05 * two_open

    return -0.90 * _estimate_opening_loss(mask)


@lru_cache(maxsize=300_000)
def _exact_value(mask: int) -> int:
    """
    Exact future net box differential from the current player's perspective.
    Uses only occupancy, which is sufficient for future play value.
    """
    best = -99
    found = False

    for e in range(TOTAL_REAL_EDGES):
        bit = EDGE_BITS[e]
        if mask & bit:
            continue
        found = True
        g = _move_gain(mask, e)
        newmask = mask | bit
        if g > 0:
            v = g + _exact_value(newmask)
        else:
            v = -_exact_value(newmask)
        if v > best:
            best = v

    return 0 if not found else best


# ---------------------------------------------------------------------
# Move classification and heuristics
# ---------------------------------------------------------------------

def _classify_moves(mask: int):
    caps = []
    safe = []
    unsafe = []

    for e in range(TOTAL_REAL_EDGES):
        bit = EDGE_BITS[e]
        if mask & bit:
            continue

        g = _move_gain(mask, e)
        if g > 0:
            caps.append((e, g))
        else:
            if _has_capture(mask | bit):
                unsafe.append((e, 0))
            else:
                safe.append((e, 0))

    return caps, safe, unsafe


def _safe_move_score(mask: int, e: int) -> float:
    bit = EDGE_BITS[e]
    newmask = mask | bit

    score = 2.0 * _count_safe_moves(newmask)

    # Prefer reducing 4-open boxes to 3-open over reducing 3-open to 2-open
    for b in MOVE_BOXES[e]:
        oc = 4 - POPCOUNT(mask & BOX_MASKS[b])
        if oc == 4:
            score += 2.5
        elif oc == 3:
            score += 0.6

    # Slight penalty for globally creating many 2-open boxes
    two_open = 0
    for bm in BOX_MASKS:
        if 4 - POPCOUNT(newmask & bm) == 2:
            two_open += 1
    score -= 0.12 * two_open

    # Slight bonus for central/interior edges touching two boxes
    score += 0.10 * len(MOVE_BOXES[e])
    return score


def _capture_order_score(mask: int, e: int, g: int) -> float:
    """
    Move-ordering score for capture states.
    """
    newmask = mask | EDGE_BITS[e]
    score = 10.0 * g

    if _has_capture(newmask):
        score += 0.25 * _capture_run_best(newmask)
    else:
        s = _count_safe_moves(newmask)
        if s:
            score += 1.5 + 0.05 * s
        else:
            score -= 0.5 * _estimate_opening_loss(newmask)

    return score


def _root_tiebreak(mask: int, e: int, g: int) -> float:
    if g > 0:
        return _capture_order_score(mask, e, g)

    newmask = mask | EDGE_BITS[e]
    if _has_capture(newmask):
        return -float(_capture_run_best(newmask))
    return _safe_move_score(mask, e)


def _order_moves(mask: int, caps, safe, unsafe):
    # If captures exist, consider all captures and only a few plausible handouts
    if caps:
        caps = sorted(caps, key=lambda t: _capture_order_score(mask, t[0], t[1]), reverse=True)
        unsafe = sorted(unsafe, key=lambda t: (_capture_run_best(mask | EDGE_BITS[t[0]]), t[0]))
        return caps + unsafe[:4]

    # If safe moves exist, unsafe moves are dominated in standard play
    if safe:
        safe = sorted(safe, key=lambda t: _safe_move_score(mask, t[0]), reverse=True)
        return safe[:8]

    # Forced opening: examine the smallest-loss openings first
    unsafe = sorted(unsafe, key=lambda t: (_capture_run_best(mask | EDGE_BITS[t[0]]), t[0]))
    return unsafe[:10]


# ---------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------

def _search(mask: int, depth: int, alpha: float, beta: float, deadline: float, memo: dict) -> float:
    if time.perf_counter() > deadline:
        raise TimeoutError

    rem = TOTAL_REAL_EDGES - POPCOUNT(mask)
    if rem <= EXACT_THRESHOLD:
        return float(_exact_value(mask))

    key = (mask, depth)
    if key in memo:
        return memo[key]

    caps, safe, unsafe = _classify_moves(mask)

    if not caps and not safe and not unsafe:
        memo[key] = 0.0
        return 0.0

    # Quiescence on captures: if captures exist, keep searching even at depth 0
    if depth <= 0 and not caps:
        val = _leaf_eval(mask)
        memo[key] = val
        return val

    moves = _order_moves(mask, caps, safe, unsafe)
    best = -100.0
    completed = True

    for e, g in moves:
        newmask = mask | EDGE_BITS[e]
        if g > 0:
            val = g + _search(newmask, depth, alpha - g, beta - g, deadline, memo)
        else:
            val = -_search(newmask, depth - 1, -beta, -alpha, deadline, memo)

        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            completed = False
            break

    if completed:
        memo[key] = best
    return best


# ---------------------------------------------------------------------
# Root move selection
# ---------------------------------------------------------------------

def _choose_exact(mask: int):
    best_move = None
    best_val = -100
    best_tb = -1e18

    for e in range(TOTAL_REAL_EDGES):
        bit = EDGE_BITS[e]
        if mask & bit:
            continue

        g = _move_gain(mask, e)
        newmask = mask | bit
        if g > 0:
            v = g + _exact_value(newmask)
        else:
            v = -_exact_value(newmask)

        tb = _root_tiebreak(mask, e, g)
        if v > best_val or (v == best_val and tb > best_tb):
            best_val = v
            best_tb = tb
            best_move = e

    return best_move


def _choose_by_search(mask: int, depth: int, deadline: float):
    memo = {}
    caps, safe, unsafe = _classify_moves(mask)
    moves = _order_moves(mask, caps, safe, unsafe)

    if not moves:
        return None

    best_move = None
    best_val = -1e18
    best_tb = -1e18

    for e, g in moves:
        if time.perf_counter() > deadline:
            raise TimeoutError

        newmask = mask | EDGE_BITS[e]
        if g > 0:
            v = g + _search(newmask, depth, -100.0, 100.0, deadline, memo)
        else:
            v = -_search(newmask, depth - 1, -100.0, 100.0, deadline, memo)

        tb = _root_tiebreak(mask, e, g)
        if v > best_val or (abs(v - best_val) <= 1e-12 and tb > best_tb):
            best_val = v
            best_tb = tb
            best_move = e

    return best_move


def _choose_safe_by_search(mask: int, safe_moves, future_depth: int, deadline: float):
    memo = {}
    candidates = sorted(safe_moves, key=lambda t: _safe_move_score(mask, t[0]), reverse=True)[:8]

    best_move = None
    best_val = -1e18
    best_tb = -1e18

    for e, _ in candidates:
        if time.perf_counter() > deadline:
            raise TimeoutError
        newmask = mask | EDGE_BITS[e]
        v = -_search(newmask, future_depth, -100.0, 100.0, deadline, memo)
        tb = _safe_move_score(mask, e)
        if v > best_val or (abs(v - best_val) <= 1e-12 and tb > best_tb):
            best_val = v
            best_tb = tb
            best_move = e

    return best_move


def _best_safe_move(mask: int, safe_moves):
    best_move = None
    best_score = -1e18
    for e, _ in safe_moves:
        s = _safe_move_score(mask, e)
        if s > best_score:
            best_score = s
            best_move = e
    return best_move


def _best_unsafe_move(mask: int, unsafe_moves):
    best_move = None
    best_loss = 10**9

    for e, _ in unsafe_moves:
        loss = _capture_run_best(mask | EDGE_BITS[e])
        if loss < best_loss or (loss == best_loss and (best_move is None or e < best_move)):
            best_loss = loss
            best_move = e

    return best_move


def _best_captureish_move(mask: int, caps, unsafe):
    moves = _order_moves(mask, caps, [], unsafe)
    if not moves:
        return None

    best_move = None
    best_val = -1e18
    best_tb = -1e18

    for e, g in moves:
        newmask = mask | EDGE_BITS[e]

        if g > 0:
            if _has_capture(newmask):
                v = g + 0.35 * _capture_run_best(newmask)
            else:
                s = _count_safe_moves(newmask)
                if s:
                    v = g + 0.9 + 0.08 * s
                else:
                    v = g - 0.9 * _estimate_opening_loss(newmask)
        else:
            v = -0.95 * _capture_run_best(newmask)

        tb = _root_tiebreak(mask, e, g)
        if v > best_val or (abs(v - best_val) <= 1e-12 and tb > best_tb):
            best_val = v
            best_tb = tb
            best_move = e

    return best_move


# ---------------------------------------------------------------------
# Fallback legal move
# ---------------------------------------------------------------------

def _fallback_move(horizontal: np.ndarray, vertical: np.ndarray) -> str:
    # Real horizontal edges first
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] == 0:
                return f"{r},{c},H"

    # Real vertical edges
    for r in range(4):
        for c in range(5):
            if vertical[r, c] == 0:
                return f"{r},{c},V"

    # If the environment treats padded cells as legal, use them as last resort
    for r in range(5):
        for c in range(5):
            if horizontal[r, c] == 0:
                return f"{r},{c},H"

    for r in range(5):
        for c in range(5):
            if vertical[r, c] == 0:
                return f"{r},{c},V"

    # Terminal fallback; should normally never be reached
    return "0,0,H"


# ---------------------------------------------------------------------
# Required API
# ---------------------------------------------------------------------

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    _ = capture  # current score is constant across candidate moves

    try:
        mask = _arrays_to_mask(horizontal, vertical)

        # If no real legal edge remains, use a permissive fallback.
        real_legal_exists = False
        for e in range(TOTAL_REAL_EDGES):
            if not (mask & EDGE_BITS[e]):
                real_legal_exists = True
                break
        if not real_legal_exists:
            return _fallback_move(horizontal, vertical)

        rem = TOTAL_REAL_EDGES - POPCOUNT(mask)

        # Exact endgame
        if rem <= EXACT_THRESHOLD:
            best = _choose_exact(mask)
            if best is not None:
                return MOVE_STR[best]
            return _fallback_move(horizontal, vertical)

        deadline = time.perf_counter() + TIME_BUDGET
        caps, safe, unsafe = _classify_moves(mask)

        # Capture/control phase
        if caps:
            depth = 6 if rem <= 22 else (5 if rem <= 28 else 4)
            try:
                best = _choose_by_search(mask, depth, deadline)
                if best is not None:
                    return MOVE_STR[best]
            except TimeoutError:
                pass

            best = _best_captureish_move(mask, caps, unsafe)
            if best is not None:
                return MOVE_STR[best]
            return _fallback_move(horizontal, vertical)

        # Safe phase
        if safe:
            if rem <= SAFE_SEARCH_THRESHOLD:
                future_depth = 3 if rem <= 24 else 2
                try:
                    best = _choose_safe_by_search(mask, safe, future_depth, deadline)
                    if best is not None:
                        return MOVE_STR[best]
                except TimeoutError:
                    pass

            best = _best_safe_move(mask, safe)
            if best is not None:
                return MOVE_STR[best]
            return _fallback_move(horizontal, vertical)

        # Forced opening phase: no captures, no safe moves
        depth = 5 if rem <= 26 else 4
        try:
            best = _choose_by_search(mask, depth, deadline)
            if best is not None:
                return MOVE_STR[best]
        except TimeoutError:
            pass

        best = _best_unsafe_move(mask, unsafe)
        if best is not None:
            return MOVE_STR[best]

        return _fallback_move(horizontal, vertical)

    except Exception:
        # Never risk returning an invalid format
        return _fallback_move(horizontal, vertical)
