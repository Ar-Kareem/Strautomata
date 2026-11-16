
import time

_ROWS = 5
_COLS = 6
_N = _ROWS * _COLS

_WIN = 1000000
_INF = 10000000

_EXACT = 0
_LOWER = 1
_UPPER = 2

_ALL = (1 << _N) - 1
_NOT_LEFT = 0
_NOT_RIGHT = 0
_NOT_TOP = 0
_NOT_BOTTOM = 0

for r in range(_ROWS):
    for c in range(_COLS):
        b = 1 << (r * _COLS + c)
        if c > 0:
            _NOT_LEFT |= b
        if c < _COLS - 1:
            _NOT_RIGHT |= b
        if r > 0:
            _NOT_TOP |= b
        if r < _ROWS - 1:
            _NOT_BOTTOM |= b

_CODE_DIR = [""] * (_N * _N)
_SRC_BIT = [0] * (_N * _N)
_DST_BIT = [0] * (_N * _N)

for r in range(_ROWS):
    for c in range(_COLS):
        i = r * _COLS + c
        if r > 0:
            d = i - _COLS
            code = i * _N + d
            _CODE_DIR[code] = "U"
            _SRC_BIT[code] = 1 << i
            _DST_BIT[code] = 1 << d
        if c < _COLS - 1:
            d = i + 1
            code = i * _N + d
            _CODE_DIR[code] = "R"
            _SRC_BIT[code] = 1 << i
            _DST_BIT[code] = 1 << d
        if r < _ROWS - 1:
            d = i + _COLS
            code = i * _N + d
            _CODE_DIR[code] = "D"
            _SRC_BIT[code] = 1 << i
            _DST_BIT[code] = 1 << d
        if c > 0:
            d = i - 1
            code = i * _N + d
            _CODE_DIR[code] = "L"
            _SRC_BIT[code] = 1 << i
            _DST_BIT[code] = 1 << d

_TT = {}
_MAX_TT = 350000
_HISTORY = [0] * (_N * _N)
_KILLERS = [[-1, -1] for _ in range(80)]

_START_TIME = 0.0
_TIME_LIMIT = 0.88
_NODES = 0


class _Timeout(Exception):
    pass


def _board_to_bits(a):
    try:
        if len(a) == _N:
            bits = 0
            for i in range(_N):
                if a[i]:
                    bits |= 1 << i
            return bits
    except Exception:
        pass

    bits = 0
    idx = 0
    for r in range(_ROWS):
        for c in range(_COLS):
            try:
                v = a[r][c]
            except Exception:
                try:
                    v = a[r, c]
                except Exception:
                    v = a[idx]
            if v:
                bits |= 1 << idx
            idx += 1
    return bits


def _neighbor_bits(x):
    return (
        ((x & _NOT_RIGHT) << 1)
        | ((x & _NOT_LEFT) >> 1)
        | ((x & _NOT_BOTTOM) << _COLS)
        | ((x & _NOT_TOP) >> _COLS)
    ) & _ALL


def _edge_count(c, o):
    return (
        (c & ((o & _NOT_BOTTOM) << _COLS)).bit_count()  # U
        + (c & ((o & _NOT_LEFT) >> 1)).bit_count()      # R
        + (c & ((o & _NOT_TOP) >> _COLS)).bit_count()   # D
        + (c & ((o & _NOT_RIGHT) << 1)).bit_count()     # L
    )


def _gen_moves(c, o):
    moves = []

    # U: destination is above source.
    x = c & ((o & _NOT_BOTTOM) << _COLS)
    while x:
        l = x & -x
        i = l.bit_length() - 1
        moves.append(i * _N + i - _COLS)
        x ^= l

    # R
    x = c & ((o & _NOT_LEFT) >> 1)
    while x:
        l = x & -x
        i = l.bit_length() - 1
        moves.append(i * _N + i + 1)
        x ^= l

    # D
    x = c & ((o & _NOT_TOP) >> _COLS)
    while x:
        l = x & -x
        i = l.bit_length() - 1
        moves.append(i * _N + i + _COLS)
        x ^= l

    # L
    x = c & ((o & _NOT_RIGHT) << 1)
    while x:
        l = x & -x
        i = l.bit_length() - 1
        moves.append(i * _N + i - 1)
        x ^= l

    return moves


def _apply(c, o, code):
    sb = _SRC_BIT[code]
    db = _DST_BIT[code]
    # Return next position from the next player-to-move's perspective.
    return o & ~db, (c & ~sb) | db


def _format_move(code):
    src = code // _N
    return f"{src // _COLS},{src % _COLS},{_CODE_DIR[code]}"


def _has_winning_move(c, o):
    for code in _gen_moves(c, o):
        nc, no = _apply(c, o, code)
        if _edge_count(nc, no) == 0:
            return True
    return False


def _quick_eval_known(c, o, edges):
    if edges == 0:
        return -_WIN

    nb_o = _neighbor_bits(o)
    nb_c = _neighbor_bits(c)
    active_c = (c & nb_o).bit_count()
    active_o = (o & nb_c).bit_count()

    material = c.bit_count() - o.bit_count()
    return 160 * material + 24 * (active_o - active_c) + 2 * edges + 12


def _evaluate(c, o):
    edges = _edge_count(c, o)
    if edges == 0:
        return -_WIN

    # Exact one-ply tactical recognition in quiet/endgame-ish positions.
    if edges <= 10 and _has_winning_move(c, o):
        return _WIN - 2

    nb_o = _neighbor_bits(o)
    nb_c = _neighbor_bits(c)

    active_c = (c & nb_o).bit_count()
    active_o = (o & nb_c).bit_count()

    # Only components connected to at least one mixed edge are "hot";
    # monochrome occupied components are inert and should not dominate material.
    occ = c | o
    hot = (c & nb_o) | (o & nb_c)
    while True:
        nh = hot | (_neighbor_bits(hot) & occ)
        if nh == hot:
            break
        hot = nh

    hot_material = (c & hot).bit_count() - (o & hot).bit_count()

    return 180 * hot_material + 28 * (active_o - active_c) + 2 * edges + 16


def _check_time():
    global _NODES
    _NODES += 1
    if (_NODES & 1023) == 0:
        if time.perf_counter() - _START_TIME > _TIME_LIMIT:
            raise _Timeout()


def _record_cutoff(ply, code, depth):
    if ply < len(_KILLERS):
        k0 = _KILLERS[ply][0]
        if k0 != code:
            _KILLERS[ply][1] = k0
            _KILLERS[ply][0] = code

    v = _HISTORY[code] + depth * depth
    _HISTORY[code] = 1000000 if v > 1000000 else v


def _order_moves(c, o, moves, tt_code=-1, first_code=-1, ply=0):
    if len(moves) <= 1:
        return moves

    scored = []
    killers = _KILLERS[ply] if ply < len(_KILLERS) else (-1, -1)

    for code in moves:
        score = _HISTORY[code]

        if code == first_code:
            score += 3000000
        if code == tt_code:
            score += 2000000
        if code == killers[0]:
            score += 800000
        elif code == killers[1]:
            score += 400000

        nc, no = _apply(c, o, code)
        ce = _edge_count(nc, no)

        # Good moves make the opponent's resulting position evaluate poorly.
        score += -_quick_eval_known(nc, no, ce)

        if ce == 0:
            score += 1000000
        elif ce <= 8 and _has_winning_move(nc, no):
            # Avoid handing over an immediate terminal capture.
            score -= 600000

        scored.append((score, code))

    scored.sort(reverse=True)
    return [code for _, code in scored]


def _negamax(c, o, depth, alpha, beta, ply):
    _check_time()

    if depth <= 0:
        return _evaluate(c, o)

    occ = (c | o).bit_count()
    if depth > occ:
        depth = occ

    key = (c << _N) | o
    alpha0 = alpha
    beta0 = beta

    entry = _TT.get(key)
    tt_code = -1
    if entry is not None:
        edepth, evalv, flag, best_code = entry
        tt_code = best_code
        if edepth >= depth:
            if flag == _EXACT:
                return evalv
            if flag == _LOWER:
                if evalv > alpha:
                    alpha = evalv
            elif flag == _UPPER:
                if evalv < beta:
                    beta = evalv
            if alpha >= beta:
                return evalv

    moves = _gen_moves(c, o)
    if not moves:
        if len(_TT) < _MAX_TT:
            _TT[key] = (depth, -_WIN, _EXACT, -1)
        return -_WIN

    ordered = _order_moves(c, o, moves, tt_code, -1, ply)

    best_val = -_INF
    best_code = ordered[0]
    first = True

    for code in ordered:
        nc, no = _apply(c, o, code)

        if first:
            val = -_negamax(nc, no, depth - 1, -beta, -alpha, ply + 1)
            first = False
        else:
            # Principal variation search.
            val = -_negamax(nc, no, depth - 1, -alpha - 1, -alpha, ply + 1)
            if alpha < val < beta:
                val = -_negamax(nc, no, depth - 1, -beta, -alpha, ply + 1)

        if val > best_val:
            best_val = val
            best_code = code

        if val > alpha:
            alpha = val

        if alpha >= beta:
            _record_cutoff(ply, code, depth)
            break

    if best_val <= alpha0:
        flag = _UPPER
    elif best_val >= beta0:
        flag = _LOWER
    else:
        flag = _EXACT

    if len(_TT) < _MAX_TT:
        _TT[key] = (depth, best_val, flag, best_code)

    return best_val


def _root_search(c, o, moves, depth, previous_best):
    key = (c << _N) | o
    entry = _TT.get(key)
    tt_code = entry[3] if entry is not None else -1

    ordered = _order_moves(c, o, moves, tt_code, previous_best, 0)

    alpha = -_INF
    beta = _INF
    best_val = -_INF
    best_code = ordered[0]
    first = True

    for code in ordered:
        nc, no = _apply(c, o, code)

        if first:
            val = -_negamax(nc, no, depth - 1, -beta, -alpha, 1)
            first = False
        else:
            val = -_negamax(nc, no, depth - 1, -alpha - 1, -alpha, 1)
            if alpha < val < beta:
                val = -_negamax(nc, no, depth - 1, -beta, -alpha, 1)

        if val > best_val:
            best_val = val
            best_code = code

        if val > alpha:
            alpha = val

    if len(_TT) < _MAX_TT:
        _TT[key] = (depth, best_val, _EXACT, best_code)

    return best_val, best_code


def policy(you: list[int], opponent: list[int]) -> str:
    global _START_TIME, _TIME_LIMIT, _NODES

    _START_TIME = time.perf_counter()
    _TIME_LIMIT = 0.88
    _NODES = 0

    try:
        if len(_TT) > _MAX_TT:
            _TT.clear()

        c = _board_to_bits(you)
        o = _board_to_bits(opponent)

        moves = _gen_moves(c, o)
        if not moves:
            # A legal move does not exist in a terminal losing state.
            # The game engine should not request a move then.
            return "0,0,U"

        if len(moves) == 1:
            return _format_move(moves[0])

        # Immediate terminal capture: always take it.
        for code in moves:
            nc, no = _apply(c, o, code)
            if _edge_count(nc, no) == 0:
                return _format_move(code)

        ordered = _order_moves(c, o, moves, -1, -1, 0)
        best = ordered[0]
        previous_best = best

        max_depth = (c | o).bit_count()
        if max_depth < 1:
            max_depth = 1

        for depth in range(1, max_depth + 1):
            if time.perf_counter() - _START_TIME > _TIME_LIMIT * 0.96:
                break

            try:
                val, code = _root_search(c, o, moves, depth, previous_best)
                best = code
                previous_best = code

                # A proven short forced win.
                if val >= _WIN // 2:
                    break
            except _Timeout:
                break

        return _format_move(best)

    except Exception:
        # Last-resort legal fallback.
        try:
            c = _board_to_bits(you)
            o = _board_to_bits(opponent)
            moves = _gen_moves(c, o)
            if moves:
                return _format_move(moves[0])
        except Exception:
            pass
        return "0,0,U"
