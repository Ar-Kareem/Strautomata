
import time

# 4x4 Tic Tac Toe policy.
# Assumption: standard generalized 4x4 Tic Tac Toe, i.e. four in a row wins.

_FULL_MASK = (1 << 16) - 1

# Bit index is row * 4 + col.
_WIN_MASKS = (
    0x000F, 0x00F0, 0x0F00, 0xF000,  # rows
    0x1111, 0x2222, 0x4444, 0x8888,  # columns
    0x8421,                          # main diagonal
    0x1248,                          # anti diagonal
)

_CELL_LINES = tuple(
    tuple(mask for mask in _WIN_MASKS if mask & (1 << i))
    for i in range(16)
)

# Prefer central diagonal/intersection squares, then corners, then edges.
_MOVE_ORDER = (
    5, 6, 9, 10,
    0, 3, 12, 15,
    1, 2, 4, 7, 8, 11, 13, 14,
)

_POS_SCORE = (
    70, 25, 25, 70,
    25, 85, 85, 25,
    25, 85, 85, 25,
    70, 25, 25, 70,
)

_ORDER_SCORE = [0] * 16
for _i, _m in enumerate(_MOVE_ORDER):
    _ORDER_SCORE[_m] = 100 - _i

_INF = 10**9
_MATE = 100000

_EXACT = 0
_LOWER = 1
_UPPER = -1

_TT = {}
_DEADLINE = 0.0
_NODES = 0


class _Timeout(Exception):
    pass


def _safe_first_empty(board):
    try:
        for r in range(4):
            for c in range(4):
                if board[r][c] == 0:
                    return (r, c)
    except Exception:
        pass
    return (0, 0)


def _board_to_bits(board):
    x = 0
    o = 0
    for r in range(4):
        for c in range(4):
            bit = 1 << (r * 4 + c)
            if board[r][c] == 1:
                x |= bit
            elif board[r][c] == -1:
                o |= bit
    return x, o


def _bit_to_move(i):
    return (i >> 2, i & 3)


def _first_bit(mask):
    if not mask:
        return 0
    return (mask & -mask).bit_length() - 1


def _iter_bits(mask):
    while mask:
        bit = mask & -mask
        yield bit.bit_length() - 1
        mask ^= bit


def _has_win(bits):
    for mask in _WIN_MASKS:
        if (bits & mask) == mask:
            return True
    return False


def _terminal_value(x, o):
    occ = x | o
    empty = 16 - occ.bit_count()

    if _has_win(x):
        # Prefer faster wins.
        return _MATE + empty
    if _has_win(o):
        # Prefer slower losses.
        return -_MATE - empty
    if occ == _FULL_MASK:
        return 0
    return None


def _winning_moves(side, other):
    """Return a bit mask of empty cells that immediately complete a line."""
    occ = side | other
    wins = 0
    for mask in _WIN_MASKS:
        if (mask & other) == 0:
            missing = mask & ~side
            if missing and (missing & (missing - 1)) == 0 and (missing & occ) == 0:
                wins |= missing
    return wins


def _fork_moves(side, other):
    """Moves that create at least two distinct immediate winning threats."""
    legal = _FULL_MASK & ~(side | other)
    forks = 0

    for m in _iter_bits(legal):
        bit = 1 << m
        after = side | bit

        # Immediate wins are handled separately.
        if _has_win(after):
            continue

        if _winning_moves(after, other).bit_count() >= 2:
            forks |= bit

    return forks


def _move_order_score(x, o, turn, m, tt_best=-1):
    side = x if turn == 1 else o
    other = o if turn == 1 else x
    bit = 1 << m
    after = side | bit

    score = _ORDER_SCORE[m] + _POS_SCORE[m]

    if m == tt_best:
        score += 10_000_000

    if _has_win(after):
        score += 5_000_000

    # Blocking an immediate opponent win is extremely important.
    opp_wins = _winning_moves(other, side)
    if bit & opp_wins:
        score += 1_200_000

    # Creating threats/forks.
    threats = _winning_moves(after, other).bit_count()
    if threats:
        score += 80_000 * threats
        if threats >= 2:
            score += 300_000

    # Local line development and blocking.
    for line in _CELL_LINES[m]:
        own_count = (side & line).bit_count()
        opp_count = (other & line).bit_count()

        if opp_count == 0:
            n = own_count + 1
            score += 70 * n * n * n

        if own_count == 0:
            n = opp_count
            score += 60 * n * n * n

    return score


def _ordered_moves(x, o, turn, tt_best=-1):
    legal = _FULL_MASK & ~(x | o)
    moves = []

    for m in _iter_bits(legal):
        moves.append((_move_order_score(x, o, turn, m, tt_best), m))

    moves.sort(reverse=True)
    return [m for _, m in moves]


def _evaluate(x, o, turn):
    term = _terminal_value(x, o)
    if term is not None:
        return term

    score = 0

    own_line_weight = (0, 3, 25, 250, 0)
    opp_line_weight = (0, 4, 35, 300, 0)

    for mask in _WIN_MASKS:
        xc = (x & mask).bit_count()
        oc = (o & mask).bit_count()

        if oc == 0:
            score += own_line_weight[xc]
        elif xc == 0:
            score -= opp_line_weight[oc]

    # Positional value.
    xb = x
    while xb:
        bit = xb & -xb
        score += _POS_SCORE[bit.bit_length() - 1]
        xb ^= bit

    ob = o
    while ob:
        bit = ob & -ob
        score -= _POS_SCORE[bit.bit_length() - 1]
        ob ^= bit

    # Immediate threats.
    x_threats = _winning_moves(x, o).bit_count()
    o_threats = _winning_moves(o, x).bit_count()

    score += 200 * x_threats
    score -= 220 * o_threats

    if x_threats >= 2:
        score += 2200
    if o_threats >= 2:
        score -= 2400

    # Tempo-aware threat adjustment.
    if turn == 1:
        if x_threats:
            score += 100 * x_threats
        if o_threats == 1:
            score -= 80
        elif o_threats > 1:
            score -= 5000
    else:
        if o_threats:
            score -= 120 * o_threats
        if x_threats == 1:
            score += 80
        elif x_threats > 1:
            score += 5000

    return score


def _check_time():
    global _NODES

    _NODES += 1
    if (_NODES & 1023) == 0:
        if time.perf_counter() > _DEADLINE:
            raise _Timeout()


def _search(x, o, turn, depth, alpha, beta):
    _check_time()

    term = _terminal_value(x, o)
    if term is not None:
        return term

    if depth <= 0:
        return _evaluate(x, o, turn)

    key = (x, o, turn)
    entry = _TT.get(key)
    tt_best = -1

    if entry is not None:
        stored_depth, stored_value, stored_flag, stored_best = entry
        tt_best = stored_best

        if stored_depth >= depth:
            if stored_flag == _EXACT:
                return stored_value
            if stored_flag == _LOWER:
                alpha = max(alpha, stored_value)
            elif stored_flag == _UPPER:
                beta = min(beta, stored_value)

            if alpha >= beta:
                return stored_value

    original_alpha = alpha
    original_beta = beta

    if turn == 1:
        value = -_INF
        best = -1

        for m in _ordered_moves(x, o, turn, tt_best):
            bit = 1 << m
            child = _search(x | bit, o, -1, depth - 1, alpha, beta)

            if child > value:
                value = child
                best = m

            alpha = max(alpha, value)
            if alpha >= beta:
                break

    else:
        value = _INF
        best = -1

        for m in _ordered_moves(x, o, turn, tt_best):
            bit = 1 << m
            child = _search(x, o | bit, 1, depth - 1, alpha, beta)

            if child < value:
                value = child
                best = m

            beta = min(beta, value)
            if alpha >= beta:
                break

    if value <= original_alpha:
        flag = _UPPER
    elif value >= original_beta:
        flag = _LOWER
    else:
        flag = _EXACT

    _TT[key] = (depth, value, flag, best)
    return value


def _root_search(x, o, depth):
    alpha = -_INF
    beta = _INF

    entry = _TT.get((x, o, 1))
    tt_best = entry[3] if entry is not None else -1

    best = -1
    value = -_INF

    for m in _ordered_moves(x, o, 1, tt_best):
        _check_time()

        bit = 1 << m
        child = _search(x | bit, o, -1, depth - 1, alpha, beta)

        if child > value:
            value = child
            best = m

        alpha = max(alpha, value)

    if best == -1:
        best = _first_bit(_FULL_MASK & ~(x | o))
        value = _evaluate(x, o, 1)

    _TT[(x, o, 1)] = (depth, value, _EXACT, best)
    return value, best


def _select_best_bit(mask, x, o):
    if not mask:
        return _fallback_move(x, o)

    best = _first_bit(mask)
    best_score = -_INF

    for m in _iter_bits(mask):
        bit = 1 << m
        score = _move_order_score(x, o, 1, m, -1)
        score += _evaluate(x | bit, o, -1) // 10

        if score > best_score:
            best_score = score
            best = m

    return best


def _fallback_move(x, o):
    legal = _FULL_MASK & ~(x | o)
    if not legal:
        return 0

    best = _first_bit(legal)
    best_score = -_INF

    for m in _iter_bits(legal):
        bit = 1 << m
        x2 = x | bit

        score = _move_order_score(x, o, 1, m, -1)
        score += _evaluate(x2, o, -1) // 10

        # Avoid allowing immediate double threats when possible.
        opp_threats = _winning_moves(o, x2).bit_count()
        if opp_threats > 1:
            score -= 100_000

        opp_forks = _fork_moves(o, x2).bit_count()
        if opp_forks:
            score -= 20_000 * opp_forks

        if score > best_score:
            best_score = score
            best = m

    return best


def _choose_by_search(x, o, deadline, preferred, min_update_depth=1):
    global _DEADLINE, _NODES

    _DEADLINE = deadline
    _NODES = 0

    if len(_TT) > 400_000:
        _TT.clear()

    legal = _FULL_MASK & ~(x | o)
    if not legal:
        return 0

    if preferred < 0 or not (legal & (1 << preferred)):
        best = _fallback_move(x, o)
    else:
        best = preferred

    remaining = legal.bit_count()

    for depth in range(1, remaining + 1):
        try:
            value, move = _root_search(x, o, depth)

            if move >= 0 and (legal & (1 << move)) and depth >= min_update_depth:
                best = move

            # A proven forced win inside the searched horizon is good enough.
            if depth >= min_update_depth and value > _MATE // 2:
                best = move
                break

        except _Timeout:
            break

    return best


def policy(board: list[list[int]]) -> tuple[int, int]:
    first_empty = _safe_first_empty(board)

    try:
        x, o = _board_to_bits(board)
        legal = _FULL_MASK & ~(x | o)

        if not legal:
            return first_empty

        # If somehow called after the game is already terminal, still return legal.
        if _has_win(x) or _has_win(o):
            return _bit_to_move(_first_bit(legal))

        # Strong opening: choose a central diagonal intersection.
        if (x | o) == 0:
            return (1, 1)

        # 1. Win immediately if possible.
        my_wins = _winning_moves(x, o)
        if my_wins:
            return _bit_to_move(_select_best_bit(my_wins, x, o))

        # 2. Block opponent immediate win.
        opp_wins = _winning_moves(o, x)
        if opp_wins:
            return _bit_to_move(_select_best_bit(opp_wins, x, o))

        # 3. Create an unstoppable fork if possible.
        my_forks = _fork_moves(x, o)
        if my_forks:
            return _bit_to_move(_select_best_bit(my_forks, x, o))

        # 4. Prefer moves that prevent opponent forks.
        preferred = _fallback_move(x, o)
        min_update_depth = 1

        opp_forks = _fork_moves(o, x)
        if opp_forks:
            safe = 0
            for m in _iter_bits(legal):
                x2 = x | (1 << m)
                if _fork_moves(o, x2) == 0:
                    safe |= 1 << m

            if safe:
                preferred = _select_best_bit(safe, x, o)
            else:
                preferred = _select_best_bit(opp_forks & legal if (opp_forks & legal) else legal, x, o)

            # Keep the tactical anti-fork fallback unless search sees deeply enough.
            min_update_depth = 3

        # 5. Iterative-deepening alpha-beta search.
        deadline = time.perf_counter() + 0.85
        chosen = _choose_by_search(x, o, deadline, preferred, min_update_depth)

        if chosen < 0 or not (legal & (1 << chosen)):
            chosen = preferred if (preferred >= 0 and (legal & (1 << preferred))) else _first_bit(legal)

        return _bit_to_move(chosen)

    except Exception:
        return first_empty
