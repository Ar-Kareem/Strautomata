
import time

# 4x4 Tic Tac Toe policy.
# Board values:  1 = us, -1 = opponent, 0 = empty.
# Assumes standard 4x4 win condition: four in a row/column/diagonal.

_N = 4
_CELLS = 16
_FULL_MASK = (1 << _CELLS) - 1

_WIN_SCORE = 1_000_000
_INF = 10**9

_EXACT, _UPPER, _LOWER = 0, 1, 2

_TIME_LIMIT = 0.88  # stay safely under a 1 second move limit


def _line_mask(cells):
    m = 0
    for r, c in cells:
        m |= 1 << (4 * r + c)
    return m


_WIN_MASKS = []

# Rows
for r in range(4):
    _WIN_MASKS.append(_line_mask((r, c) for c in range(4)))

# Columns
for c in range(4):
    _WIN_MASKS.append(_line_mask((r, c) for r in range(4)))

# Diagonals
_WIN_MASKS.append(_line_mask((i, i) for i in range(4)))
_WIN_MASKS.append(_line_mask((i, 3 - i) for i in range(4)))

_WIN_MASKS = tuple(_WIN_MASKS)

_CELL_LINES = [[] for _ in range(_CELLS)]
for w in _WIN_MASKS:
    for i in range(_CELLS):
        if w & (1 << i):
            _CELL_LINES[i].append(w)
_CELL_LINES = tuple(tuple(x) for x in _CELL_LINES)

# Positional weights: diagonal squares matter more; near-center diagonal squares
# get a slight preference over corners.
_POS_WEIGHTS = []
for r in range(4):
    for c in range(4):
        idx = 4 * r + c
        degree = len(_CELL_LINES[idx])
        center_bonus = 6 - (abs(2 * r - 3) + abs(2 * c - 3))
        _POS_WEIGHTS.append(10 * degree + center_bonus)

_SIZE = 1 << _CELLS

_BIT_COUNT = [0] * _SIZE
_POS_SUM = [0] * _SIZE
for m in range(1, _SIZE):
    lsb = m & -m
    prev = m ^ lsb
    idx = lsb.bit_length() - 1
    _BIT_COUNT[m] = _BIT_COUNT[prev] + 1
    _POS_SUM[m] = _POS_SUM[prev] + _POS_WEIGHTS[idx]

_WIN_TABLE = [False] * _SIZE
for m in range(_SIZE):
    for w in _WIN_MASKS:
        if (m & w) == w:
            _WIN_TABLE[m] = True
            break

_LINE_VALUE = (0, 8, 90, 1500, _WIN_SCORE)
_OPP_LINE_VALUE = (0, 9, 110, 1800, _WIN_SCORE)

_TT = {}
_DEADLINE = 0.0
_NODES = 0


class _SearchTimeout(Exception):
    pass


def _iter_bits(mask):
    while mask:
        b = mask & -mask
        yield b
        mask ^= b


def _bit_to_move(bit):
    idx = bit.bit_length() - 1
    return idx // 4, idx % 4


def _fallback_move(board):
    for r in range(4):
        for c in range(4):
            try:
                if board[r][c] == 0:
                    return (r, c)
            except Exception:
                pass
    return (0, 0)


def _masks_from_board(board):
    me = 0
    opp = 0
    for r in range(4):
        row = board[r]
        for c in range(4):
            bit = 1 << (4 * r + c)
            v = row[c]
            if v == 1:
                me |= bit
            elif v == -1:
                opp |= bit
    empty = _FULL_MASK & ~(me | opp)
    return me, opp, empty


def _winning_bits(player, other, empty):
    """All empty cells where player wins immediately by moving there."""
    res = 0
    for w in _WIN_MASKS:
        if (w & other) == 0:
            missing = w & ~player
            if missing and (missing & (missing - 1)) == 0:
                res |= missing
    return res & empty


def _evaluate(me, opp):
    empty = _FULL_MASK & ~(me | opp)
    score = _POS_SUM[me] - _POS_SUM[opp]

    for w in _WIN_MASKS:
        mc = _BIT_COUNT[me & w]
        oc = _BIT_COUNT[opp & w]
        if oc == 0:
            score += _LINE_VALUE[mc]
        elif mc == 0:
            score -= _OPP_LINE_VALUE[oc]

    my_wins = _winning_bits(me, opp, empty)
    opp_wins = _winning_bits(opp, me, empty)

    mwc = _BIT_COUNT[my_wins]
    owc = _BIT_COUNT[opp_wins]

    score += 2500 * mwc
    score -= 3000 * owc

    if mwc >= 2:
        score += 20000
    if owc >= 2:
        score -= 25000

    return score


def _move_score(me, opp, bit, empty, opp_wins_cache=None):
    idx = bit.bit_length() - 1
    new_me = me | bit
    new_empty = empty ^ bit

    score = _POS_WEIGHTS[idx]

    if _WIN_TABLE[new_me]:
        score += 10_000_000

    if opp_wins_cache is None:
        opp_wins_cache = _winning_bits(opp, me, empty)
    if bit & opp_wins_cache:
        score += 900_000

    threats = _winning_bits(new_me, opp, new_empty)
    tc = _BIT_COUNT[threats]
    score += 50_000 * tc
    if tc >= 2:
        score += 800_000

    for w in _CELL_LINES[idx]:
        mc = _BIT_COUNT[me & w]
        oc = _BIT_COUNT[opp & w]

        if oc == 0:
            # We are extending a live line.
            score += 2 * _LINE_VALUE[mc + 1]
        elif mc == 0:
            # We are blocking an opponent-only line.
            score += _OPP_LINE_VALUE[oc]

    score += (_POS_SUM[new_me] - _POS_SUM[opp]) // 4
    return score


def _ordered_moves(me, opp, empty, hint=0):
    moves = []

    if hint and (hint & empty):
        moves.append(hint)

    mask = empty & ~hint
    scored = []
    opp_wins = _winning_bits(opp, me, empty)

    while mask:
        b = mask & -mask
        mask ^= b
        scored.append((_move_score(me, opp, b, empty, opp_wins), b))

    scored.sort(reverse=True)
    moves.extend(b for _, b in scored)
    return moves


def _fork_moves_mask(player, other, empty):
    """Moves that create at least two distinct immediate winning threats."""
    res = 0
    for b in _iter_bits(empty):
        new_player = player | b
        if _WIN_TABLE[new_player]:
            continue
        threats = _winning_bits(new_player, other, empty ^ b)
        if _BIT_COUNT[threats] >= 2:
            res |= b
    return res


def _best_bit_from(mask, me, opp, empty):
    mask &= empty
    if not mask:
        return empty & -empty

    best = mask & -mask
    best_score = -_INF
    opp_wins = _winning_bits(opp, me, empty)

    for b in _iter_bits(mask):
        s = _move_score(me, opp, b, empty, opp_wins)
        if s > best_score:
            best_score = s
            best = b
    return best


def _anti_fork_move(me, opp, empty):
    opp_forks = _fork_moves_mask(opp, me, empty)
    if not opp_forks:
        return 0

    best = 0
    best_score = -_INF
    opp_wins = _winning_bits(opp, me, empty)

    for b in _iter_bits(empty):
        new_me = me | b
        new_empty = empty ^ b

        remaining_forks = _fork_moves_mask(opp, new_me, new_empty)
        s = _move_score(me, opp, b, empty, opp_wins)

        if remaining_forks == 0:
            s += 800_000
        if b & opp_forks:
            s += 300_000

        my_threats = _winning_bits(new_me, opp, new_empty)
        if my_threats:
            s += 200_000 * _BIT_COUNT[my_threats]

        if s > best_score:
            best_score = s
            best = b

    return best


def _choose_static_move(me, opp, empty):
    moves = _ordered_moves(me, opp, empty)
    if moves:
        return moves[0]
    return empty & -empty


def _negamax(me, opp, depth, alpha, beta):
    global _NODES

    _NODES += 1
    if (_NODES & 1023) == 0 and time.perf_counter() > _DEADLINE:
        raise _SearchTimeout()

    empty = _FULL_MASK & ~(me | opp)
    empties = _BIT_COUNT[empty]

    # Previous player just won.
    if _WIN_TABLE[opp]:
        return -_WIN_SCORE - empties

    if empty == 0:
        return 0

    # If current player can win now, do it.
    my_win = _winning_bits(me, opp, empty)
    if my_win:
        return _WIN_SCORE + empties - 1

    # If opponent has immediate wins, current player must block.
    opp_win = _winning_bits(opp, me, empty)
    if opp_win:
        # Two distinct winning cells cannot both be blocked.
        if opp_win & (opp_win - 1):
            return -_WIN_SCORE - max(0, empties - 2)

        forced = opp_win
        next_depth = depth - 1 if depth > 0 else 0
        return -_negamax(opp, me | forced, next_depth, -beta, -alpha)

    if depth <= 0:
        return _evaluate(me, opp)

    key = (me, opp, depth)
    alpha_start = alpha
    beta_start = beta
    tt_best = 0

    ent = _TT.get(key)
    if ent is not None:
        val, flag, tt_best = ent
        if flag == _EXACT:
            return val
        if flag == _LOWER:
            if val > alpha:
                alpha = val
        elif flag == _UPPER:
            if val < beta:
                beta = val
        if alpha >= beta:
            return val

    best_val = -_INF
    best_bit = 0

    for b in _ordered_moves(me, opp, empty, tt_best):
        val = -_negamax(opp, me | b, depth - 1, -beta, -alpha)

        if val > best_val:
            best_val = val
            best_bit = b

        if val > alpha:
            alpha = val

        if alpha >= beta:
            break

    if best_val <= alpha_start:
        flag = _UPPER
    elif best_val >= beta_start:
        flag = _LOWER
    else:
        flag = _EXACT

    if len(_TT) < 450_000:
        _TT[key] = (best_val, flag, best_bit)

    return best_val


def _root_search(me, opp, empty, depth, hint):
    alpha = -_INF
    beta = _INF

    best_bit = hint if (hint & empty) else (empty & -empty)
    best_val = -_INF

    for b in _ordered_moves(me, opp, empty, hint):
        if time.perf_counter() > _DEADLINE:
            raise _SearchTimeout()

        val = -_negamax(opp, me | b, depth - 1, -beta, -alpha)

        if val > best_val:
            best_val = val
            best_bit = b

        if val > alpha:
            alpha = val

    return best_bit, best_val


def policy(board: list[list[int]]) -> tuple[int, int]:
    global _DEADLINE, _NODES

    fallback = _fallback_move(board)

    try:
        me, opp, empty = _masks_from_board(board)

        if empty == 0:
            return fallback

        if len(_TT) > 450_000:
            _TT.clear()

        _DEADLINE = time.perf_counter() + _TIME_LIMIT
        _NODES = 0

        # 1. Win immediately if possible.
        my_win = _winning_bits(me, opp, empty)
        if my_win:
            bit = _best_bit_from(my_win, me, opp, empty)
            r, c = _bit_to_move(bit)
            if board[r][c] == 0:
                return (r, c)

        # 2. Block opponent's immediate win.
        opp_win = _winning_bits(opp, me, empty)
        if opp_win:
            bit = _best_bit_from(opp_win, me, opp, empty)
            r, c = _bit_to_move(bit)
            if board[r][c] == 0:
                return (r, c)

        # 3. Strong opening: choose a near-center diagonal square.
        if empty == _FULL_MASK:
            return (1, 1)

        # 4. Create an unblockable fork if available.
        my_forks = _fork_moves_mask(me, opp, empty)
        if my_forks:
            bit = _best_bit_from(my_forks, me, opp, empty)
            r, c = _bit_to_move(bit)
            if board[r][c] == 0:
                return (r, c)

        # 5. Prefer anti-fork moves as the initial candidate.
        anti = _anti_fork_move(me, opp, empty)
        initial = anti if anti else _choose_static_move(me, opp, empty)
        best = initial if initial else (empty & -empty)

        # 6. Iterative deepening alpha-beta search.
        max_depth = _BIT_COUNT[empty]

        for depth in range(1, max_depth + 1):
            if time.perf_counter() > _DEADLINE:
                break

            try:
                bit, val = _root_search(me, opp, empty, depth, best)
            except _SearchTimeout:
                break

            if bit & empty:
                best = bit

            # Found a forced win; no need to search deeper.
            if val >= _WIN_SCORE // 2:
                break

        r, c = _bit_to_move(best)
        if board[r][c] == 0:
            return (r, c)

    except Exception:
        pass

    return fallback
