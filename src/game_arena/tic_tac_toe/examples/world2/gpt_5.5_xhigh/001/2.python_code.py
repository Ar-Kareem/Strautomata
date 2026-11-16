
import time

# 4x4 Tic Tac Toe, using 4-in-a-row rows/columns/main diagonals.
# Board cells are indexed as bit positions: bit = 1 << (4 * row + col)

_FULL = (1 << 16) - 1
_MATE = 1_000_000
_INF = 1_000_000_000

_LINES = (
    # rows
    0b0000000000001111,
    0b0000000011110000,
    0b0000111100000000,
    0b1111000000000000,
    # columns
    0b0001000100010001,
    0b0010001000100010,
    0b0100010001000100,
    0b1000100010001000,
    # diagonals
    0b1000010000100001,  # (0,0),(1,1),(2,2),(3,3)
    0b0001001001001000,  # (0,3),(1,2),(2,1),(3,0)
)

_CELL_LINES = [[] for _ in range(16)]
for _line in _LINES:
    for _i in range(16):
        if _line & (1 << _i):
            _CELL_LINES[_i].append(_line)

# Positional weights: diagonal/central cells are generally more useful.
_POS_WEIGHT = []
for _i in range(16):
    _r, _c = divmod(_i, 4)
    w = 3 * len(_CELL_LINES[_i])
    if _r in (1, 2) and _c in (1, 2):
        w += 5
    if (_r, _c) in ((0, 0), (0, 3), (3, 0), (3, 3)):
        w += 1
    _POS_WEIGHT.append(w)

# Precomputed tables:
# _WIN[mask]       -> mask already has a completed line
# _ALMOST[mask]    -> union of cells that complete a line where mask has exactly 3
# _POS_SUM[mask]   -> sum of positional weights in mask
_WIN = [False] * (1 << 16)
_ALMOST = [0] * (1 << 16)
_POS_SUM = [0] * (1 << 16)

for _m in range(1 << 16):
    a = 0
    win = False
    for _line in _LINES:
        c = (_m & _line).bit_count()
        if c == 4:
            win = True
        elif c == 3:
            a |= _line & ~_m
    _WIN[_m] = win
    _ALMOST[_m] = a & _FULL
    if _m:
        _lsb = _m & -_m
        _POS_SUM[_m] = _POS_SUM[_m ^ _lsb] + _POS_WEIGHT[_lsb.bit_length() - 1]

# Search globals
_TT = {}
_MAX_TT = 600_000
_DEADLINE = 0.0
_NODES = 0

_EXACT = 0
_LOWER = 1
_UPPER = 2


class _Timeout(Exception):
    pass


def _bits(mask):
    while mask:
        b = mask & -mask
        yield b
        mask ^= b


def _rc(bit):
    i = bit.bit_length() - 1
    return (i // 4, i % 4)


def _threats(player_bits, other_bits):
    """Empty cells where player_bits can win immediately."""
    return _ALMOST[player_bits] & (_FULL ^ (player_bits | other_bits))


def _evaluate(x, o, side):
    """Static evaluation from X/my perspective."""
    # Quiet positions normally have no immediate threats due to search quiescence.
    score = 3 * (_POS_SUM[x] - _POS_SUM[o])

    open_weight = (0, 4, 42, 650, 0)
    x_twos = 0
    o_twos = 0

    for line in _LINES:
        xb = (x & line).bit_count()
        ob = (o & line).bit_count()

        if ob == 0:
            score += open_weight[xb]
            if xb == 2:
                x_twos += 1
        elif xb == 0:
            score -= open_weight[ob]
            if ob == 2:
                o_twos += 1

    # Multiple open two-lines are often fork material.
    score += 12 * (x_twos * x_twos - o_twos * o_twos)

    # Small tempo adjustment.
    if side == 1:
        score += 6 * x_twos - 3 * o_twos + 2
    else:
        score += 3 * x_twos - 6 * o_twos - 2

    return score


def _move_score(x, o, side, bit):
    """Move ordering score, relative to the player to move."""
    if side == 1:
        own, opp = x, o
    else:
        own, opp = o, x

    idx = bit.bit_length() - 1
    score = _POS_WEIGHT[idx]

    attack = (2, 10, 100, 5000)
    defend = (0, 7, 90, 4000)

    for line in _CELL_LINES[idx]:
        own_c = (own & line).bit_count()
        opp_c = (opp & line).bit_count()

        if opp_c == 0:
            score += attack[own_c]
        if own_c == 0:
            score += defend[opp_c]

    new_own = own | bit
    empty_after = _FULL ^ (new_own | opp)
    made_threats = (_ALMOST[new_own] & empty_after).bit_count()
    if made_threats:
        score += 5000 * made_threats
        if made_threats >= 2:
            score += 25000

    return score


def _ordered_moves(x, o, side, moves):
    if not moves:
        return []
    if moves & (moves - 1) == 0:
        return [moves]

    scored = []
    for b in _bits(moves):
        idx = b.bit_length() - 1
        scored.append((_move_score(x, o, side, b), -idx, b))
    scored.sort(reverse=True)
    return [b for _, __, b in scored]


def _choose_heuristic(x, o, side, moves):
    best = 0
    best_s = -_INF
    for b in _bits(moves):
        s = _move_score(x, o, side, b)
        if s > best_s:
            best_s = s
            best = b
    return best if best else (moves & -moves)


def _store_tt(key, value, flag):
    if key in _TT or len(_TT) < _MAX_TT:
        _TT[key] = (value, flag)


def _search(x, o, side, depth, alpha, beta):
    """Alpha-beta search. Returns score from X/my perspective."""
    global _NODES

    _NODES += 1
    if (_NODES & 2047) == 0 and time.perf_counter() > _DEADLINE:
        raise _Timeout()

    occupied = x | o
    empty = _FULL ^ occupied
    ec = empty.bit_count()

    if _WIN[x]:
        return _MATE + ec
    if _WIN[o]:
        return -_MATE - ec
    if empty == 0:
        return 0

    x_th = _ALMOST[x] & empty
    o_th = _ALMOST[o] & empty

    forced = False

    if side == 1:
        # X to move can win immediately.
        if x_th:
            return _MATE + ec - 1

        # X must block O's immediate threat(s).
        if o_th:
            if o_th & (o_th - 1):
                return -_MATE - max(ec - 2, 0)
            moves = o_th
            forced = True
        else:
            moves = empty

    else:
        # O to move can win immediately.
        if o_th:
            return -_MATE - ec + 1

        # O must block X's immediate threat(s).
        if x_th:
            if x_th & (x_th - 1):
                return _MATE + max(ec - 2, 0)
            moves = x_th
            forced = True
        else:
            moves = empty

    key = (x, o, side, depth)
    entry = _TT.get(key)
    alpha0, beta0 = alpha, beta

    if entry is not None:
        val, flag = entry
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

    if depth <= 0 and not forced:
        val = _evaluate(x, o, side)
        _store_tt(key, val, _EXACT)
        return val

    child_depth = depth - 1 if depth > 0 else 0
    ordered = _ordered_moves(x, o, side, moves)

    if side == 1:
        best = -_INF
        for b in ordered:
            val = _search(x | b, o, -1, child_depth, alpha, beta)
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
    else:
        best = _INF
        for b in ordered:
            val = _search(x, o | b, 1, child_depth, alpha, beta)
            if val < best:
                best = val
            if best < beta:
                beta = best
            if alpha >= beta:
                break

    if best <= alpha0:
        flag = _UPPER
    elif best >= beta0:
        flag = _LOWER
    else:
        flag = _EXACT

    _store_tt(key, best, flag)
    return best


def _root_search(x, o, depth):
    empty = _FULL ^ (x | o)
    ordered = _ordered_moves(x, o, 1, empty)
    if not ordered:
        return 0, 0

    best_val = -_INF
    best_bit = ordered[0]
    alpha = -_INF
    child_depth = depth - 1 if depth > 0 else 0

    for b in ordered:
        val = _search(x | b, o, -1, child_depth, alpha, _INF)
        if val > best_val:
            best_val = val
            best_bit = b
        if val > alpha:
            alpha = val

    return best_val, best_bit


def policy(board: list[list[int]]) -> tuple[int, int]:
    global _DEADLINE, _NODES

    x = 0
    o = 0

    for r in range(4):
        for c in range(4):
            v = board[r][c]
            bit = 1 << (4 * r + c)
            if v == 1:
                x |= bit
            elif v == -1:
                o |= bit

    empty = _FULL ^ (x | o)

    # No legal move exists; this should not be called on full boards.
    if empty == 0:
        return (0, 0)

    # If called after the game is already over, still return a legal cell.
    if _WIN[x] or _WIN[o]:
        return _rc(empty & -empty)

    # 1. Win immediately if possible.
    my_wins = _threats(x, o)
    if my_wins:
        return _rc(_choose_heuristic(x, o, 1, my_wins))

    # 2. Block opponent's immediate win.
    opp_wins = _threats(o, x)
    if opp_wins:
        return _rc(_choose_heuristic(x, o, 1, opp_wins))

    # 3. If we can create an unavoidable two-threat fork now, do it.
    fork_moves = 0
    for b in _bits(empty):
        if _threats(x | b, o).bit_count() >= 2:
            fork_moves |= b
    if fork_moves:
        return _rc(_choose_heuristic(x, o, 1, fork_moves))

    # Opening preference: central diagonal square.
    if (x | o) == 0:
        return (1, 1)

    # Only one move.
    if empty & (empty - 1) == 0:
        return _rc(empty)

    # Fallback before search, guaranteeing legality.
    best_bit = _choose_heuristic(x, o, 1, empty)

    # Iterative deepening. Most mid/endgame positions are searched exactly.
    _DEADLINE = time.perf_counter() + 0.88
    _NODES = 0

    target_depth = empty.bit_count()

    for depth in range(1, target_depth + 1):
        if time.perf_counter() > _DEADLINE:
            break
        try:
            val, bit = _root_search(x, o, depth)
            if bit & empty:
                best_bit = bit

            # A forced win has been found.
            if val >= _MATE:
                break
        except _Timeout:
            break

    if not (best_bit & empty):
        best_bit = empty & -empty

    return _rc(best_bit)
