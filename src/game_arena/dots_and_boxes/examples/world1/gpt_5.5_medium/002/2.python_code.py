
import time
import numpy as np

# 4x4 boxes:
# Horizontal valid edges: rows 0..4, cols 0..3  -> indices 0..19
# Vertical valid edges:   rows 0..3, cols 0..4  -> indices 20..39

N_BOX = 4
N_EDGES = 40
FULL_MASK = (1 << N_EDGES) - 1

EDGE_INFO = []
EDGE_TO_BOXES = [[] for _ in range(N_EDGES)]
BOX_MASKS = [0 for _ in range(16)]


def _h_index(r, c):
    return r * 4 + c


def _v_index(r, c):
    return 20 + r * 5 + c


def _box_index(r, c):
    return r * 4 + c


# Build edge info.
for r in range(5):
    for c in range(4):
        EDGE_INFO.append((r, c, "H"))

for r in range(4):
    for c in range(5):
        EDGE_INFO.append((r, c, "V"))

# Build box masks and edge-to-box adjacency.
for r in range(4):
    for c in range(4):
        b = _box_index(r, c)
        edges = [
            _h_index(r, c),
            _h_index(r + 1, c),
            _v_index(r, c),
            _v_index(r, c + 1),
        ]
        m = 0
        for e in edges:
            m |= 1 << e
            EDGE_TO_BOXES[e].append(b)
        BOX_MASKS[b] = m


class _Timeout(Exception):
    pass


def _mask_from_arrays(horizontal, vertical):
    mask = 0

    # Standard 4x4 Dots and Boxes valid horizontal edges.
    for r in range(5):
        for c in range(4):
            try:
                if horizontal[r, c] != 0:
                    mask |= 1 << _h_index(r, c)
            except Exception:
                pass

    # Standard valid vertical edges.
    for r in range(4):
        for c in range(5):
            try:
                if vertical[r, c] != 0:
                    mask |= 1 << _v_index(r, c)
            except Exception:
                pass

    return mask


def _edge_to_move(e):
    r, c, d = EDGE_INFO[e]
    return f"{r},{c},{d}"


def _side_count(mask, b):
    return (mask & BOX_MASKS[b]).bit_count()


def _capture_count(mask, e):
    """Number of boxes completed by playing edge e."""
    bit = 1 << e
    if mask & bit:
        return 0

    cnt = 0
    for b in EDGE_TO_BOXES[e]:
        if _side_count(mask, b) == 3:
            cnt += 1
    return cnt


def _legal_edges(mask):
    inv = FULL_MASK ^ mask
    return [e for e in range(N_EDGES) if (inv >> e) & 1]


def _is_safe_move(mask, e):
    """
    A safe non-capturing move is one that does not turn an adjacent
    2-sided box into a 3-sided box.
    """
    if _capture_count(mask, e) > 0:
        return False
    for b in EDGE_TO_BOXES[e]:
        if _side_count(mask, b) == 2:
            return False
    return True


def _safe_moves(mask):
    return [e for e in _legal_edges(mask) if _is_safe_move(mask, e)]


def _count_twos(mask):
    return sum(1 for b in range(16) if _side_count(mask, b) == 2)


def _center_score(e):
    r, c, d = EDGE_INFO[e]
    if d == "H":
        x = c + 0.5
        y = r
    else:
        x = c
        y = r + 0.5

    # Prefer internal and central edges very slightly.
    internal_bonus = 0.35 if len(EDGE_TO_BOXES[e]) == 2 else 0.0
    dist = abs(x - 2.0) + abs(y - 2.0)
    return internal_bonus - 0.05 * dist


def _forced_capture_estimate(mask):
    """
    Estimate how many boxes the next player can collect once this position
    contains capturable boxes. This is a greedy rollout, used only as a
    heuristic for choosing the least painful chain to open.
    """
    m = mask
    total = 0
    guard = 0

    while guard < 40:
        guard += 1
        caps = []
        for e in _legal_edges(m):
            c = _capture_count(m, e)
            if c > 0:
                caps.append((c, e))

        if not caps:
            break

        # Greedy opponent: take the largest immediate capture.
        caps.sort(reverse=True)
        c, e = caps[0]
        total += c
        m |= 1 << e

    return total


def _ordered_moves(mask):
    moves = _legal_edges(mask)
    captures = []
    safe = []
    unsafe = []

    for e in moves:
        c = _capture_count(mask, e)
        if c > 0:
            captures.append((c, e))
        elif _is_safe_move(mask, e):
            safe.append(e)
        else:
            unsafe.append(e)

    # Captures first, larger captures first.
    captures.sort(key=lambda x: (x[0], _center_score(x[1])), reverse=True)

    # Safe moves: prefer parity/control, fewer two-sided boxes, centrality.
    def safe_key(e):
        nm = mask | (1 << e)
        sm = len(_safe_moves(nm))
        parity = 1 if sm % 2 == 0 else -1
        return (
            parity,
            -_count_twos(nm),
            -sm,
            _center_score(e),
        )

    safe.sort(key=safe_key, reverse=True)

    # Unsafe moves: open the smallest estimated chain.
    def unsafe_key(e):
        nm = mask | (1 << e)
        return (
            -_forced_capture_estimate(nm),
            -_count_twos(nm),
            _center_score(e),
        )

    unsafe.sort(key=unsafe_key, reverse=True)

    return [e for _, e in captures] + safe + unsafe


def _search_best_move(mask, time_limit=0.78):
    """
    Time-limited exact negamax search over remaining edges.
    Value is future box differential for the player to move.
    """
    start = time.perf_counter()
    memo = {}

    def check_time():
        if time.perf_counter() - start > time_limit:
            raise _Timeout()

    def solve(m, alpha, beta):
        check_time()

        if m == FULL_MASK:
            return 0

        if m in memo:
            return memo[m]

        best = -100
        original_alpha = alpha
        fully_searched = True

        for e in _ordered_moves(m):
            c = _capture_count(m, e)
            nm = m | (1 << e)

            if c > 0:
                # Same player moves again.
                val = c + solve(nm, alpha - c, beta - c)
            else:
                # Turn passes.
                val = -solve(nm, -beta, -alpha)

            if val > best:
                best = val
            if best > alpha:
                alpha = best

            if alpha >= beta:
                fully_searched = False
                break

        if fully_searched:
            memo[m] = best

        return best

    best_e = None
    best_val = -100
    alpha = -100
    beta = 100

    for e in _ordered_moves(mask):
        check_time()

        c = _capture_count(mask, e)
        nm = mask | (1 << e)

        if c > 0:
            val = c + solve(nm, alpha - c, beta - c)
        else:
            val = -solve(nm, -beta, -alpha)

        if val > best_val:
            best_val = val
            best_e = e

        if val > alpha:
            alpha = val

    return best_e


def _heuristic_best_move(mask):
    moves = _legal_edges(mask)
    if not moves:
        return None

    # 1. Take captures if available.
    caps = []
    for e in moves:
        c = _capture_count(mask, e)
        if c > 0:
            nm = mask | (1 << e)
            # Prefer immediate captures and continued initiative.
            follow = _forced_capture_estimate(nm)
            caps.append((c, follow, _center_score(e), e))

    if caps:
        caps.sort(reverse=True)
        return caps[0][3]

    # 2. Prefer safe moves.
    safe = [e for e in moves if _is_safe_move(mask, e)]
    if safe:
        def key(e):
            nm = mask | (1 << e)
            opp_safe = len(_safe_moves(nm))
            parity = 1 if opp_safe % 2 == 0 else -1

            # Leaving zero safe moves means the opponent must open a chain.
            force_open_bonus = 3 if opp_safe == 0 else 0

            return (
                force_open_bonus,
                parity,
                -_count_twos(nm),
                -opp_safe,
                _center_score(e),
            )

        safe.sort(key=key, reverse=True)
        return safe[0]

    # 3. No safe moves: open the smallest estimated chain.
    def bad_key(e):
        nm = mask | (1 << e)
        damage = _forced_capture_estimate(nm)
        return (
            -damage,
            -_count_twos(nm),
            _center_score(e),
        )

    moves.sort(key=bad_key, reverse=True)
    return moves[0]


def _fallback_from_arrays(horizontal, vertical):
    """
    Absolute safety fallback. Prefer standard 4x4 legal edges, then any
    zero entry in the supplied 5x5 arrays.
    """
    for r in range(5):
        for c in range(4):
            try:
                if horizontal[r, c] == 0:
                    return f"{r},{c},H"
            except Exception:
                pass

    for r in range(4):
        for c in range(5):
            try:
                if vertical[r, c] == 0:
                    return f"{r},{c},V"
            except Exception:
                pass

    # If the arena exposes all 5x5 entries as playable, try those too.
    for r in range(5):
        for c in range(5):
            try:
                if horizontal[r, c] == 0:
                    return f"{r},{c},H"
            except Exception:
                pass

    for r in range(5):
        for c in range(5):
            try:
                if vertical[r, c] == 0:
                    return f"{r},{c},V"
            except Exception:
                pass

    # Should only happen after the game is already over.
    return "0,0,H"


def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    mask = _mask_from_arrays(horizontal, vertical)
    remaining = N_EDGES - mask.bit_count()

    if remaining <= 0:
        return _fallback_from_arrays(horizontal, vertical)

    # Try exact search in tactical/endgame states.
    best = None
    has_capture = any(_capture_count(mask, e) > 0 for e in _legal_edges(mask))
    has_safe = bool(_safe_moves(mask))

    # Exact search is most valuable late or when the position is loony.
    if remaining <= 22 or has_capture or not has_safe:
        try:
            best = _search_best_move(mask, time_limit=0.78)
        except Exception:
            best = None

    if best is None:
        best = _heuristic_best_move(mask)

    if best is not None:
        r, c, d = EDGE_INFO[best]
        try:
            if d == "H" and horizontal[r, c] == 0:
                return _edge_to_move(best)
            if d == "V" and vertical[r, c] == 0:
                return _edge_to_move(best)
        except Exception:
            pass

    return _fallback_from_arrays(horizontal, vertical)
