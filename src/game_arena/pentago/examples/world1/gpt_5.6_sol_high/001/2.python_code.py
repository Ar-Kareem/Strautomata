
import time

# ---------------------------------------------------------------------------
# Board constants and precomputed geometry
# ---------------------------------------------------------------------------

FULL_MASK = (1 << 36) - 1
WIN_SCORE = 1_000_000
INF = 10_000_000
DIRECTIONS = ("L", "R")

# Quadrant row/column origins.
QUAD_ORIGINS = (
    (0, 0),
    (0, 3),
    (3, 0),
    (3, 3),
)

# Every contiguous five-cell winning segment.
WIN_MASKS = []

# Horizontal segments.
for r in range(6):
    for c0 in range(2):
        mask = 0
        for k in range(5):
            mask |= 1 << (r * 6 + c0 + k)
        WIN_MASKS.append(mask)

# Vertical segments.
for c in range(6):
    for r0 in range(2):
        mask = 0
        for k in range(5):
            mask |= 1 << ((r0 + k) * 6 + c)
        WIN_MASKS.append(mask)

# Down-right diagonals.
for r0 in range(2):
    for c0 in range(2):
        mask = 0
        for k in range(5):
            mask |= 1 << ((r0 + k) * 6 + c0 + k)
        WIN_MASKS.append(mask)

# Down-left diagonals.
for r0 in range(2):
    for c0 in (4, 5):
        mask = 0
        for k in range(5):
            mask |= 1 << ((r0 + k) * 6 + c0 - k)
        WIN_MASKS.append(mask)

WIN_MASKS = tuple(WIN_MASKS)

# Positional preferences. Quadrant centers are stable under rotation.
POSITION_WEIGHTS = (
    1, 2, 2, 2, 2, 1,
    2, 7, 3, 3, 7, 2,
    2, 3, 4, 4, 3, 2,
    2, 3, 4, 4, 3, 2,
    2, 7, 3, 3, 7, 2,
    1, 2, 2, 2, 2, 1,
)

# Value of an uncontested five-cell segment by marble count.
LINE_VALUES = (0, 1, 9, 58, 520, 20000)

# Masks covering each quadrant.
QUAD_MASKS = []
for rb, cb in QUAD_ORIGINS:
    qmask = 0
    for rr in range(3):
        for cc in range(3):
            qmask |= 1 << ((rb + rr) * 6 + cb + cc)
    QUAD_MASKS.append(qmask)
QUAD_MASKS = tuple(QUAD_MASKS)

# EXPANDED[q][direction][local_pattern] gives the rotated local pattern
# expanded back into its global board positions.
EXPANDED = [[[0] * 512 for _ in range(2)] for _ in range(4)]

for q, (rb, cb) in enumerate(QUAD_ORIGINS):
    for direction in range(2):
        for pattern in range(512):
            result = 0
            for rr in range(3):
                for cc in range(3):
                    local_index = rr * 3 + cc
                    if not ((pattern >> local_index) & 1):
                        continue

                    if direction == 0:       # Left / anticlockwise
                        nr, nc = 2 - cc, rr
                    else:                    # Right / clockwise
                        nr, nc = cc, 2 - rr

                    global_index = (rb + nr) * 6 + cb + nc
                    result |= 1 << global_index
            EXPANDED[q][direction][pattern] = result

# MAP_INDEX[q][direction][index] is the final location of a marble at
# 'index' after rotating q in the specified direction.
MAP_INDEX = [[[0] * 36 for _ in range(2)] for _ in range(4)]

for q, (rb, cb) in enumerate(QUAD_ORIGINS):
    for direction in range(2):
        for index in range(36):
            r, c = divmod(index, 6)
            if rb <= r < rb + 3 and cb <= c < cb + 3:
                rr, cc = r - rb, c - cb
                if direction == 0:
                    nr, nc = 2 - cc, rr
                else:
                    nr, nc = cc, 2 - rr
                MAP_INDEX[q][direction][index] = (rb + nr) * 6 + cb + nc
            else:
                MAP_INDEX[q][direction][index] = index


# ---------------------------------------------------------------------------
# Low-level game operations
# ---------------------------------------------------------------------------

def _rotate_board(board, q, direction):
    rb, cb = QUAD_ORIGINS[q]
    base = rb * 6 + cb

    pattern = (
        ((board >> base) & 7)
        | (((board >> (base + 6)) & 7) << 3)
        | (((board >> (base + 12)) & 7) << 6)
    )

    return (board & ~QUAD_MASKS[q]) | EXPANDED[q][direction][pattern]


def _has_five(board):
    for mask in WIN_MASKS:
        if board & mask == mask:
            return True
    return False


def _terminal_score(mover, other, remaining_depth):
    """Score a board immediately after mover has completed a move."""
    mover_wins = _has_five(mover)
    other_wins = _has_five(other)

    if mover_wins:
        if other_wins:
            return 0
        return WIN_SCORE + remaining_depth

    if other_wins:
        return -WIN_SCORE - remaining_depth

    if (mover | other) == FULL_MASK:
        return 0

    return None


def _position_score(board):
    score = 0
    bits = board
    while bits:
        low = bits & -bits
        index = low.bit_length() - 1
        score += POSITION_WEIGHTS[index]
        bits ^= low
    return score


def _after_move_evaluation(mover, next_player):
    """
    Static score from mover's perspective immediately after mover's turn.

    The next player receives extra credit for threats because they have the
    tempo on the following turn.
    """
    score = 0
    next_open_threes = 0
    next_open_fours = 0
    mover_open_fours = 0

    for mask in WIN_MASKS:
        mover_part = mover & mask
        next_part = next_player & mask

        if not next_part:
            count = mover_part.bit_count()
            score += LINE_VALUES[count]
            if count == 4:
                mover_open_fours += 1

        if not mover_part:
            count = next_part.bit_count()
            score -= LINE_VALUES[count]
            if count == 4:
                next_open_fours += 1
            elif count == 3:
                next_open_threes += 1

    # It is now next_player's turn, making their threats more urgent.
    score -= 190 * next_open_fours
    score -= 18 * next_open_threes

    # Multiple threats are particularly valuable in Pentago.
    if mover_open_fours >= 2:
        score += 160 * (mover_open_fours - 1)
    if next_open_fours >= 2:
        score -= 280 * (next_open_fours - 1)

    score += _position_score(mover)
    score -= _position_score(next_player)

    return score


def _generate_moves(me, opponent, include_actions=False):
    """
    Generate distinct resulting states.

    Several legal action strings can create the same final board, especially
    early in the game. Such transpositions are searched only once.
    """
    rotated_me = [[0, 0] for _ in range(4)]
    rotated_opponent = [[0, 0] for _ in range(4)]

    for q in range(4):
        rotated_me[q][0] = _rotate_board(me, q, 0)
        rotated_me[q][1] = _rotate_board(me, q, 1)
        rotated_opponent[q][0] = _rotate_board(opponent, q, 0)
        rotated_opponent[q][1] = _rotate_board(opponent, q, 1)

    empty = FULL_MASK ^ (me | opponent)
    seen = set()
    moves = []

    while empty:
        low = empty & -empty
        index = low.bit_length() - 1
        empty ^= low

        for q in range(4):
            for direction in range(2):
                final_index = MAP_INDEX[q][direction][index]
                new_me = rotated_me[q][direction] | (1 << final_index)
                new_opponent = rotated_opponent[q][direction]
                state = (new_me, new_opponent)

                if state in seen:
                    continue
                seen.add(state)

                if include_actions:
                    moves.append((new_me, new_opponent,
                                  (index, q, direction)))
                else:
                    moves.append((new_me, new_opponent))

    return moves


# ---------------------------------------------------------------------------
# Time-limited alpha-beta search
# ---------------------------------------------------------------------------

class _SearchTimeout(Exception):
    pass


_DEADLINE = 0.0
_NODES = 0
_TT = {}


def _check_time():
    global _NODES
    _NODES += 1
    if (_NODES & 127) == 0 and time.perf_counter() >= _DEADLINE:
        raise _SearchTimeout


def _negamax(me, opponent, depth, alpha, beta):
    global _TT

    _check_time()

    key = (me, opponent, depth)
    entry = _TT.get(key)
    original_alpha = alpha
    original_beta = beta

    if entry is not None:
        value, flag = entry
        if flag == 0:           # Exact
            return value
        if flag == 1:           # Lower bound
            if value > alpha:
                alpha = value
        else:                   # Upper bound
            if value < beta:
                beta = value
        if alpha >= beta:
            return value

    moves = _generate_moves(me, opponent, False)

    # At the final searched ply, avoid recursive-call overhead.
    if depth == 1:
        best = -INF

        for new_me, new_opponent in moves:
            terminal = _terminal_score(new_me, new_opponent, depth)
            if terminal is None:
                value = _after_move_evaluation(new_me, new_opponent)
            else:
                value = terminal

            if value > best:
                best = value
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break

        if best >= original_beta:
            flag = 1
        elif best <= original_alpha:
            flag = 2
        else:
            flag = 0
        _TT[key] = (best, flag)
        return best

    # Search promising moves first to improve alpha-beta pruning.
    ordered = []
    for new_me, new_opponent in moves:
        terminal = _terminal_score(new_me, new_opponent, depth)
        if terminal is None:
            ordering_score = _after_move_evaluation(new_me, new_opponent)
        else:
            ordering_score = terminal
        ordered.append((ordering_score, new_me, new_opponent, terminal))

    ordered.sort(key=lambda item: item[0], reverse=True)

    best = -INF

    for _, new_me, new_opponent, terminal in ordered:
        if terminal is not None:
            value = terminal
        else:
            value = -_negamax(
                new_opponent,
                new_me,
                depth - 1,
                -beta,
                -alpha
            )

        if value > best:
            best = value
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    if best >= original_beta:
        flag = 1
    elif best <= original_alpha:
        flag = 2
    else:
        flag = 0

    _TT[key] = (best, flag)
    return best


# ---------------------------------------------------------------------------
# Required API
# ---------------------------------------------------------------------------

def policy(you, opponent) -> str:
    global _DEADLINE, _NODES, _TT

    # Convert the supplied arrays to compact bitboards.
    me = 0
    other = 0
    for r in range(6):
        for c in range(6):
            index = r * 6 + c
            if int(you[r][c]):
                me |= 1 << index
            elif int(opponent[r][c]):
                other |= 1 << index

    occupied = me | other
    empty_bits = FULL_MASK ^ occupied

    # Guaranteed legal fallback, established before any expensive work.
    first_empty = empty_bits & -empty_bits
    fallback_index = first_empty.bit_length() - 1
    fallback_r, fallback_c = divmod(fallback_index, 6)
    fallback = f"{fallback_r + 1},{fallback_c + 1},0,L"

    try:
        # Strong and rotation-stable opening.
        if occupied == 0:
            return "2,2,0,L"

        _DEADLINE = time.perf_counter() + 0.90
        _NODES = 0
        _TT = {}

        root_moves = _generate_moves(me, other, True)
        if not root_moves:
            return fallback

        # One-ply tactical and strategic ordering.
        records = []
        for new_me, new_other, action in root_moves:
            terminal = _terminal_score(new_me, new_other, 1)
            if terminal is None:
                score = _after_move_evaluation(new_me, new_other)
            else:
                score = terminal

            # Never delay an immediate sole win.
            if terminal is not None and terminal >= WIN_SCORE:
                index, q, direction = action
                r, c = divmod(index, 6)
                return f"{r + 1},{c + 1},{q},{DIRECTIONS[direction]}"

            records.append((score, new_me, new_other, action))

        records.sort(key=lambda item: item[0], reverse=True)
        best_action = records[0][3]

        empty_count = empty_bits.bit_count()

        # Early positions have very large branching factors. Later positions
        # can be searched more deeply, sometimes all the way to the end.
        if empty_count > 24:
            maximum_depth = 2
        elif empty_count > 14:
            maximum_depth = 3
        elif empty_count > 8:
            maximum_depth = 4
        else:
            maximum_depth = max(2, empty_count)

        # Iterative deepening: only adopt results from a fully completed depth.
        for depth in range(2, maximum_depth + 1):
            local_best_score = -INF
            local_best_action = best_action
            alpha = -INF
            new_records = []
            completed = True

            try:
                for _, new_me, new_other, action in records:
                    if time.perf_counter() >= _DEADLINE:
                        raise _SearchTimeout

                    terminal = _terminal_score(new_me, new_other, depth)
                    if terminal is not None:
                        score = terminal
                    else:
                        score = -_negamax(
                            new_other,
                            new_me,
                            depth - 1,
                            -INF,
                            -alpha
                        )

                    new_records.append((score, new_me, new_other, action))

                    if score > local_best_score:
                        local_best_score = score
                        local_best_action = action
                    if score > alpha:
                        alpha = score

            except _SearchTimeout:
                completed = False

            if not completed:
                break

            best_action = local_best_action
            new_records.sort(key=lambda item: item[0], reverse=True)
            records = new_records

        index, q, direction = best_action
        r, c = divmod(index, 6)
        return f"{r + 1},{c + 1},{q},{DIRECTIONS[direction]}"

    except Exception:
        # Valid input always reaches the normal path, but the fallback also
        # protects move legality from unexpected runtime conditions.
        return fallback
