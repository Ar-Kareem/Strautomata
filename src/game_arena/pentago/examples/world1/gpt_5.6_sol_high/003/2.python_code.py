
import time

# ---------------------------------------------------------------------------
# Board constants and precomputed geometry
# ---------------------------------------------------------------------------

FULL_MASK = (1 << 36) - 1
MATE = 10_000_000
FORCED_WIN = MATE - 100

# Quadrant top-left bit indices.
_QUAD_BASE = (0, 3, 18, 21)

_QUAD_MASKS = []
for base in _QUAD_BASE:
    mask = 0
    for rr in range(3):
        for cc in range(3):
            mask |= 1 << (base + rr * 6 + cc)
    _QUAD_MASKS.append(mask)
_QUAD_MASKS = tuple(_QUAD_MASKS)


def _make_rotation_tables():
    left = [0] * 512
    right = [0] * 512

    for pattern in range(512):
        lp = 0
        rp = 0

        for r in range(3):
            for c in range(3):
                source = r * 3 + c
                if pattern & (1 << source):
                    # Anticlockwise: (r,c) -> (2-c,r)
                    lr, lc = 2 - c, r
                    lp |= 1 << (lr * 3 + lc)

                    # Clockwise: (r,c) -> (c,2-r)
                    rr, rc = c, 2 - r
                    rp |= 1 << (rr * 3 + rc)

        left[pattern] = lp
        right[pattern] = rp

    return tuple(left), tuple(right)


_ROT9_L, _ROT9_R = _make_rotation_tables()


def _rotate(board, action):
    """Rotate one quadrant. action = quad*2 + direction, where 0=L and 1=R."""
    quad = action >> 1
    base = _QUAD_BASE[quad]

    pattern = (
        ((board >> base) & 7)
        | (((board >> (base + 6)) & 7) << 3)
        | (((board >> (base + 12)) & 7) << 6)
    )

    if action & 1:
        rotated = _ROT9_R[pattern]
    else:
        rotated = _ROT9_L[pattern]

    result = board & ~_QUAD_MASKS[quad]
    result |= (rotated & 7) << base
    result |= ((rotated >> 3) & 7) << (base + 6)
    result |= ((rotated >> 6) & 7) << (base + 12)
    return result


# Destination of a newly placed marble after each possible rotation.
_MOVE_DEST = tuple(
    tuple(_rotate(1 << cell, action) for cell in range(36))
    for action in range(8)
)


# Starting squares for five consecutive bits in each direction.
_H_START = sum(
    1 << (r * 6 + c)
    for r in range(6)
    for c in (0, 1)
)

_V_START = sum(
    1 << (r * 6 + c)
    for r in (0, 1)
    for c in range(6)
)

_D7_START = sum(
    1 << (r * 6 + c)
    for r in (0, 1)
    for c in (0, 1)
)

_D5_START = sum(
    1 << (r * 6 + c)
    for r in (0, 1)
    for c in (4, 5)
)


def _has_five(board):
    """Fast detection of horizontal, vertical, and diagonal five-in-a-row."""
    x = board & (board >> 1) & (board >> 2) & (board >> 3) & (board >> 4)
    if x & _H_START:
        return True

    x = board & (board >> 6) & (board >> 12) & (board >> 18) & (board >> 24)
    if x & _V_START:
        return True

    x = board & (board >> 7) & (board >> 14) & (board >> 21) & (board >> 28)
    if x & _D7_START:
        return True

    x = board & (board >> 5) & (board >> 10) & (board >> 15) & (board >> 20)
    return bool(x & _D5_START)


def _make_line_masks():
    masks = []
    directions = ((0, 1), (1, 0), (1, 1), (1, -1))

    for dr, dc in directions:
        for r in range(6):
            for c in range(6):
                er = r + 4 * dr
                ec = c + 4 * dc
                if 0 <= er < 6 and 0 <= ec < 6:
                    mask = 0
                    for k in range(5):
                        mask |= 1 << ((r + k * dr) * 6 + c + k * dc)
                    masks.append(mask)

    return tuple(masks)


_LINE_MASKS = _make_line_masks()
_CENTER_MASK = (1 << 7) | (1 << 10) | (1 << 25) | (1 << 28)

# Values for uncontested five-cell lines containing N marbles.
_LINE_VALUE = (0, 1, 7, 38, 280, MATE)


# ---------------------------------------------------------------------------
# Evaluation and utility functions
# ---------------------------------------------------------------------------

def _evaluate(ours, theirs):
    score = 0

    for mask in _LINE_MASKS:
        oc = (ours & mask).bit_count()
        tc = (theirs & mask).bit_count()

        if oc and not tc:
            score += _LINE_VALUE[oc]
        elif tc and not oc:
            score -= _LINE_VALUE[tc]

    # Quadrant centers are rotation-invariant and generally valuable anchors.
    score += 4 * (
        (ours & _CENTER_MASK).bit_count()
        - (theirs & _CENTER_MASK).bit_count()
    )

    return score


def _terminal_value(ours, theirs):
    """Return a terminal value, or None if the position is nonterminal."""
    our_win = _has_five(ours)
    their_win = _has_five(theirs)

    if our_win:
        if their_win:
            return 0
        return MATE

    if their_win:
        return -MATE

    if (ours | theirs) == FULL_MASK:
        return 0

    return None


def _empty_cells(ours, theirs):
    empty = FULL_MASK ^ (ours | theirs)
    cells = []

    while empty:
        bit = empty & -empty
        cells.append(bit.bit_length() - 1)
        empty ^= bit

    return cells


def _format_action(cell, action):
    row = cell // 6 + 1
    col = cell % 6 + 1
    quad = action >> 1
    direction = "R" if action & 1 else "L"
    return f"{row},{col},{quad},{direction}"


def _can_win_next(ours, theirs, deadline, cache):
    """
    Determine whether the side represented by 'ours' has a move producing
    a five while not also producing an opponent five.
    """
    key = (ours, theirs)
    cached = cache.get(key)
    if cached is not None:
        return cached

    if time.perf_counter() >= deadline:
        return None

    cells = _empty_cells(ours, theirs)

    for action in range(8):
        rotated_ours = _rotate(ours, action)
        rotated_theirs = _rotate(theirs, action)
        destinations = _MOVE_DEST[action]

        for cell in cells:
            next_ours = rotated_ours | destinations[cell]

            if _has_five(next_ours) and not _has_five(rotated_theirs):
                cache[key] = True
                return True

    cache[key] = False
    return False


def _analyze_opponent_responses(
    ours,
    theirs,
    alpha,
    deadline,
    win_cache,
):
    """
    Evaluate a position after our root move.

    Every distinct opponent response is considered. Nonterminal responses are
    ordered from worst to best for us. A selective extra ply checks whether we
    can immediately win after each most-dangerous response.
    """
    cells = _empty_cells(ours, theirs)
    seen = set()
    leaves = []
    fixed_worst = MATE + 1
    have_fixed = False

    for action in range(8):
        if time.perf_counter() >= deadline:
            return None

        next_ours_base = _rotate(ours, action)
        next_theirs_base = _rotate(theirs, action)
        destinations = _MOVE_DEST[action]

        for cell in cells:
            next_ours = next_ours_base
            next_theirs = next_theirs_base | destinations[cell]
            key = (next_ours, next_theirs)

            if key in seen:
                continue
            seen.add(key)

            terminal = _terminal_value(next_ours, next_theirs)

            # The opponent can choose this immediate win.
            if terminal == -MATE:
                return -MATE

            if terminal is not None:
                have_fixed = True
                if terminal < fixed_worst:
                    fixed_worst = terminal
            else:
                value = _evaluate(next_ours, next_theirs)
                leaves.append((value, next_ours, next_theirs))

    # An already known terminal response is enough for an alpha cutoff.
    if have_fixed and fixed_worst <= alpha:
        return fixed_worst

    leaves.sort(key=lambda item: item[0])
    worst = fixed_worst if have_fixed else MATE + 1

    for value, next_ours, next_theirs in leaves:
        # All remaining ordinary evaluations are at least this large.
        if value >= worst:
            break

        if time.perf_counter() >= deadline:
            return None

        tactical_win = _can_win_next(
            next_ours,
            next_theirs,
            deadline,
            win_cache,
        )

        if tactical_win is None:
            return None

        if tactical_win:
            if FORCED_WIN < worst:
                worst = FORCED_WIN
            continue

        # This is the lowest-valued response that does not lose immediately.
        worst = value
        break

    if worst == MATE + 1:
        # This should only be reachable for a malformed full position.
        return 0

    return worst


# ---------------------------------------------------------------------------
# Main policy
# ---------------------------------------------------------------------------

def _choose_move(ours, theirs, deadline, fallback):
    cells = _empty_cells(ours, theirs)
    seen = set()
    candidates = []

    # Generate every distinct resulting root position.
    for action in range(8):
        rotated_ours = _rotate(ours, action)
        rotated_theirs = _rotate(theirs, action)
        destinations = _MOVE_DEST[action]

        for cell in cells:
            next_ours = rotated_ours | destinations[cell]
            next_theirs = rotated_theirs
            key = (next_ours, next_theirs)

            if key in seen:
                continue
            seen.add(key)

            terminal = _terminal_value(next_ours, next_theirs)

            # Never search past a direct non-simultaneous win.
            if terminal == MATE:
                return _format_action(cell, action)

            if terminal is None:
                ordering_score = _evaluate(next_ours, next_theirs)
            else:
                ordering_score = terminal

            candidates.append(
                (
                    ordering_score,
                    cell,
                    action,
                    next_ours,
                    next_theirs,
                    terminal,
                )
            )

    # Strong-looking moves establish alpha early and improve pruning.
    candidates.sort(key=lambda item: item[0], reverse=True)

    if not candidates:
        return fallback

    best_action = _format_action(candidates[0][1], candidates[0][2])
    best_score = -(MATE + 1)
    win_cache = {}

    for (
        ordering_score,
        cell,
        action,
        next_ours,
        next_theirs,
        terminal,
    ) in candidates:
        if time.perf_counter() >= deadline:
            break

        if terminal is not None:
            score = terminal
        else:
            score = _analyze_opponent_responses(
                next_ours,
                next_theirs,
                best_score,
                deadline,
                win_cache,
            )
            if score is None:
                break

        if score > best_score:
            best_score = score
            best_action = _format_action(cell, action)

            if best_score >= FORCED_WIN:
                break

    return best_action


def policy(you, opponent) -> str:
    """
    Return a legal Pentago move in the form "row,col,quad,dir".
    """
    start = time.perf_counter()

    ours = 0
    theirs = 0
    first_empty = None

    for r in range(6):
        for c in range(6):
            bit = 1 << (r * 6 + c)

            if int(you[r][c]):
                ours |= bit
            elif int(opponent[r][c]):
                theirs |= bit
            elif first_empty is None:
                first_empty = (r, c)

    # The specification guarantees at least one empty square.
    if first_empty is None:
        return "1,1,0,L"

    fallback = f"{first_empty[0] + 1},{first_empty[1] + 1},0,L"

    try:
        return _choose_move(
            ours,
            theirs,
            start + 0.94,
            fallback,
        )
    except Exception:
        # Preserve legality even if an unusual array implementation raises.
        return fallback
