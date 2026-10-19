
import time

# ---------- Board geometry ----------

def _idx(i, j, k):
    return i * 9 + j * 3 + k


def _make_lines():
    lines = []
    seen = set()

    def add(cells):
        mask = 0
        for i, j, k in cells:
            mask |= 1 << _idx(i, j, k)
        if mask not in seen:
            seen.add(mask)
            lines.append(mask)

    # Axis-parallel lines
    for j in range(3):
        for k in range(3):
            add([(0, j, k), (1, j, k), (2, j, k)])
    for i in range(3):
        for k in range(3):
            add([(i, 0, k), (i, 1, k), (i, 2, k)])
    for i in range(3):
        for j in range(3):
            add([(i, j, 0), (i, j, 1), (i, j, 2)])

    # Face diagonals
    for k in range(3):
        add([(0, 0, k), (1, 1, k), (2, 2, k)])
        add([(0, 2, k), (1, 1, k), (2, 0, k)])
    for j in range(3):
        add([(0, j, 0), (1, j, 1), (2, j, 2)])
        add([(0, j, 2), (1, j, 1), (2, j, 0)])
    for i in range(3):
        add([(i, 0, 0), (i, 1, 1), (i, 2, 2)])
        add([(i, 0, 2), (i, 1, 1), (i, 2, 0)])

    # Space diagonals
    add([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
    add([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
    add([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
    add([(0, 2, 2), (1, 1, 1), (2, 0, 0)])

    return tuple(lines)


_WIN_LINES = _make_lines()
_ALL_MASK = (1 << 27) - 1
_CENTER_BIT = 1 << _idx(1, 1, 1)

_CELL_LINES_LIST = [[] for _ in range(27)]
for _line in _WIN_LINES:
    m = _line
    while m:
        b = m & -m
        _CELL_LINES_LIST[b.bit_length() - 1].append(_line)
        m ^= b
_CELL_LINES = tuple(tuple(x) for x in _CELL_LINES_LIST)

_CORNER_MASK = 0
for _i in (0, 2):
    for _j in (0, 2):
        for _k in (0, 2):
            _CORNER_MASK |= 1 << _idx(_i, _j, _k)

_OPPOSITE = []
for _n in range(27):
    _i = _n // 9
    _j = (_n // 3) % 3
    _k = _n % 3
    _OPPOSITE.append(1 << _idx(2 - _i, 2 - _j, 2 - _k))
_OPPOSITE = tuple(_OPPOSITE)

_CELL_VALUE = []
for _n in range(27):
    v = 10 * len(_CELL_LINES[_n])
    if (1 << _n) == _CENTER_BIT:
        v += 80
    if (1 << _n) & _CORNER_MASK:
        v += 35
    _CELL_VALUE.append(v)
_CELL_VALUE = tuple(_CELL_VALUE)

_MATE = 1_000_000
_INF = 10_000_000

_TT = {}
_TT_MAX = 350000
_EXACT, _LOWER, _UPPER = 0, 1, 2

_KILLERS = [[0, 0] for _ in range(64)]
_DEADLINE = 0.0
_NODES = 0


# ---------- Bitboard helpers ----------

def _bit_to_coord(bit):
    n = bit.bit_length() - 1
    return (n // 9, (n // 3) % 3, n % 3)


def _has_win(bits):
    for line in _WIN_LINES:
        if bits & line == line:
            return True
    return False


def _is_win_at(bits, move):
    if not move:
        return _has_win(bits)
    n = move.bit_length() - 1
    for line in _CELL_LINES[n]:
        if bits & line == line:
            return True
    return False


def _winning_cells(bits, empty):
    """Cells where 'bits' can move now and complete a line."""
    result = 0
    for line in _WIN_LINES:
        if (bits & line).bit_count() == 2:
            e = line & empty
            if e:
                result |= e
    return result


def _occupied_value(bits):
    s = 0
    while bits:
        b = bits & -bits
        s += _CELL_VALUE[b.bit_length() - 1]
        bits ^= b
    return s


def _evaluate(me, opp, empty):
    score = 0

    for line in _WIN_LINES:
        mb = me & line
        ob = opp & line
        if mb and ob:
            continue

        mc = mb.bit_count()
        oc = ob.bit_count()

        if oc == 0:
            if mc == 1:
                score += 14
            elif mc == 2:
                score += 260
        elif mc == 0:
            if oc == 1:
                score -= 15
            elif oc == 2:
                score -= 310

    score += _occupied_value(me) - _occupied_value(opp)
    return score


def _move_score(move, me, opp, empty):
    n = move.bit_length() - 1
    score = _CELL_VALUE[n]
    new_empty = empty ^ move
    threat_mask = 0

    for line in _CELL_LINES[n]:
        mc = (me & line).bit_count()
        oc = (opp & line).bit_count()

        if oc == 0:
            if mc == 2:
                score += 1_000_000
            elif mc == 1:
                e = line & new_empty
                if e:
                    threat_mask |= e
                score += 900
            else:
                score += 25
        elif mc == 0:
            if oc == 2:
                score += 7000
            elif oc == 1:
                score += 90

    threats = threat_mask.bit_count()
    if threats >= 2:
        score += 220000 + 25000 * threats
    elif threats == 1:
        score += 1200

    return score


def _best_from_mask(mask, me, opp, empty):
    best = mask & -mask
    best_score = -_INF
    m = mask
    while m:
        b = m & -m
        s = _move_score(b, me, opp, empty)
        if s > best_score:
            best_score = s
            best = b
        m ^= b
    return best


def _ordered_moves(me, opp, empty, mask, ply, preferred=0):
    scored = []
    m = mask
    k1 = k2 = 0
    if ply < len(_KILLERS):
        k1, k2 = _KILLERS[ply]

    while m:
        b = m & -m
        s = _move_score(b, me, opp, empty)
        if b == preferred:
            s += 5_000_000
        elif b == k1:
            s += 350_000
        elif b == k2:
            s += 180_000
        scored.append((s, b))
        m ^= b

    scored.sort(reverse=True)
    return [b for _, b in scored]


def _remember_killer(ply, move):
    if ply >= len(_KILLERS):
        return
    if _KILLERS[ply][0] != move:
        _KILLERS[ply][1] = _KILLERS[ply][0]
        _KILLERS[ply][0] = move


def _check_time():
    global _NODES
    _NODES += 1
    if (_NODES & 2047) == 0 and time.perf_counter() > _DEADLINE:
        raise TimeoutError


# ---------- Search ----------

def _negamax(me, opp, empty, depth, alpha, beta, ply, last_move):
    _check_time()

    if last_move and _is_win_at(opp, last_move):
        return -_MATE - empty.bit_count()
    if not last_move and _has_win(opp):
        return -_MATE - empty.bit_count()

    if empty == 0:
        return 0

    # Tactical terminal tests.
    my_wins = _winning_cells(me, empty)
    if my_wins:
        return _MATE + empty.bit_count() - 1

    opp_wins = _winning_cells(opp, empty)
    forced = 0
    if opp_wins:
        if opp_wins.bit_count() > 1:
            return -_MATE - max(0, empty.bit_count() - 2)
        forced = opp_wins

    # Threat extension / quiescence: if there is a forced block, search it
    # even at nominal depth zero.
    if depth <= 0 and not forced:
        return _evaluate(me, opp, empty)

    key = (me, opp)
    alpha0 = alpha
    beta0 = beta
    preferred = 0

    entry = _TT.get(key)
    if entry is not None:
        edepth, val, flag, mv = entry
        if edepth >= depth:
            preferred = mv
            if flag == _EXACT:
                return val
            if flag == _LOWER:
                if val >= beta:
                    return val
                if val > alpha:
                    alpha = val
            elif flag == _UPPER:
                if val <= alpha:
                    return val
                if val < beta:
                    beta = val
            if alpha >= beta:
                return val

    moves_mask = forced if forced else empty
    best_val = -_INF
    best_move = 0

    for move in _ordered_moves(me, opp, empty, moves_mask, ply, preferred):
        # Forced replies are tactically necessary, so do not charge depth for them.
        child_depth = depth if forced else depth - 1
        val = -_negamax(opp, me | move, empty ^ move,
                        child_depth, -beta, -alpha, ply + 1, move)

        if val > best_val:
            best_val = val
            best_move = move

        if val > alpha:
            alpha = val

        if alpha >= beta:
            _remember_killer(ply, move)
            if len(_TT) < _TT_MAX:
                _TT[key] = (depth, best_val, _LOWER, best_move)
            return best_val

    if best_move == 0:
        return 0

    if best_val <= alpha0:
        flag = _UPPER
    elif best_val >= beta0:
        flag = _LOWER
    else:
        flag = _EXACT

    if len(_TT) < _TT_MAX:
        _TT[key] = (depth, best_val, flag, best_move)

    return best_val


def _root_search(me, opp, empty, depth, preferred):
    alpha = -_INF
    beta = _INF
    best_val = -_INF
    best_move = 0

    for move in _ordered_moves(me, opp, empty, empty, 0, preferred):
        val = -_negamax(opp, me | move, empty ^ move,
                        depth - 1, -beta, -alpha, 1, move)
        if val > best_val:
            best_val = val
            best_move = move
        if val > alpha:
            alpha = val

    return best_val, best_move


# ---------- Opening and fallback ----------

def _opening_move(me, opp, empty):
    my_count = me.bit_count()
    opp_count = opp.bit_count()

    # First move: center is by far the strongest square.
    if my_count == 0:
        if empty & _CENTER_BIT:
            return _CENTER_BIT
        corners = empty & _CORNER_MASK
        if corners:
            return _best_from_mask(corners, me, opp, empty)
        return empty & -empty

    # If we own the center early, play a corner whose opposite cell is open,
    # immediately creating a center-line threat.
    if my_count == 1 and (me & _CENTER_BIT) and opp_count <= 1:
        candidates = 0
        m = empty & _CORNER_MASK
        while m:
            b = m & -m
            n = b.bit_length() - 1
            if _OPPOSITE[n] & empty:
                candidates |= b
            m ^= b
        if candidates:
            return _best_from_mask(candidates, me, opp, empty)

    return 0


def _heuristic_move(me, opp, empty):
    if empty == 0:
        return 0

    my_wins = _winning_cells(me, empty)
    if my_wins:
        return _best_from_mask(my_wins, me, opp, empty)

    opp_wins = _winning_cells(opp, empty)
    if opp_wins:
        return _best_from_mask(opp_wins, me, opp, empty)

    book = _opening_move(me, opp, empty)
    if book:
        return book

    return _best_from_mask(empty, me, opp, empty)


# ---------- Required API ----------

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    global _DEADLINE, _NODES, _TT

    me = 0
    opp = 0

    for i in range(3):
        for j in range(3):
            for k in range(3):
                bit = 1 << _idx(i, j, k)
                v = board[i][j][k]
                if v == 1:
                    me |= bit
                elif v == -1:
                    opp |= bit

    empty = _ALL_MASK & ~(me | opp)

    # No legal move exists; games should not call policy in this state.
    if empty == 0:
        return (0, 0, 0)

    if len(_TT) > _TT_MAX:
        _TT.clear()

    for pair in _KILLERS:
        pair[0] = 0
        pair[1] = 0

    # Absolute tactical priorities.
    my_wins = _winning_cells(me, empty)
    if my_wins:
        return _bit_to_coord(_best_from_mask(my_wins, me, opp, empty))

    opp_wins = _winning_cells(opp, empty)
    if opp_wins and opp_wins.bit_count() == 1:
        return _bit_to_coord(opp_wins)

    book = _opening_move(me, opp, empty)
    if book:
        return _bit_to_coord(book)

    best_move = _heuristic_move(me, opp, empty)

    # Search with a conservative deadline so we always return in time.
    _DEADLINE = time.perf_counter() + 0.82
    _NODES = 0

    try:
        max_depth = empty.bit_count()
        # Iterative deepening: early depths give reliable tactical play;
        # later depths are used when the board is small or pruning is strong.
        for depth in range(1, max_depth + 1):
            if time.perf_counter() > _DEADLINE:
                break
            val, move = _root_search(me, opp, empty, depth, best_move)
            if move and (move & empty):
                best_move = move

            # A proven forcing win is good enough; play it immediately.
            if val > _MATE // 2:
                break

    except TimeoutError:
        pass

    if not best_move or not (best_move & empty):
        best_move = empty & -empty

    return _bit_to_coord(best_move)
