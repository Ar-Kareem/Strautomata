
import time

ROWS = 5
COLS = 6
N = ROWS * COLS

# Directions and neighbor masks.
_NEI = [[] for _ in range(N)]
_ADJ = [0] * N
_DEG = [0] * N

for r in range(ROWS):
    for c in range(COLS):
        i = r * COLS + c
        if r > 0:
            j = (r - 1) * COLS + c
            _NEI[i].append((j, "U"))
        if c < COLS - 1:
            j = r * COLS + (c + 1)
            _NEI[i].append((j, "R"))
        if r < ROWS - 1:
            j = (r + 1) * COLS + c
            _NEI[i].append((j, "D"))
        if c > 0:
            j = r * COLS + (c - 1)
            _NEI[i].append((j, "L"))

for i in range(N):
    m = 0
    for j, _ in _NEI[i]:
        m |= 1 << j
    _ADJ[i] = m
    _DEG[i] = len(_NEI[i])

_INF = 10 ** 9
_WIN = 100_000_000

_EXACT = 0
_LOWER = 1
_UPPER = 2

_TT = {}
_DEADLINE = 0.0
_NODES = 0


def _bits_from_array(arr):
    b = 0
    try:
        # 5x6 nested list / numpy-like array.
        for r in range(ROWS):
            row = arr[r]
            for c in range(COLS):
                if row[c]:
                    b |= 1 << (r * COLS + c)
        return b
    except Exception:
        # Flat length-30 representation.
        flat = list(arr)
        for i in range(min(N, len(flat))):
            if flat[i]:
                b |= 1 << i
        return b


def _legal_moves(me, opp):
    moves = []
    x = me
    while x:
        lsb = x & -x
        s = lsb.bit_length() - 1
        for d, ch in _NEI[s]:
            if opp & (1 << d):
                moves.append((s, d, ch))
        x -= lsb
    return moves


def _has_move(me, opp):
    x = me
    while x:
        lsb = x & -x
        s = lsb.bit_length() - 1
        if opp & _ADJ[s]:
            return True
        x -= lsb
    return False


def _count_moves(me, opp):
    cnt = 0
    x = me
    while x:
        lsb = x & -x
        s = lsb.bit_length() - 1
        cnt += (opp & _ADJ[s]).bit_count()
        x -= lsb
    return cnt


def _apply(me, opp, mv):
    s, d, _ = mv
    sb = 1 << s
    db = 1 << d
    me2 = (me & ~sb) | db
    opp2 = opp & ~db
    return me2, opp2


def _fmt(mv):
    s, _, ch = mv
    return f"{s // COLS},{s % COLS},{ch}"


def _check_time():
    global _NODES
    _NODES += 1
    if (_NODES & 1023) == 0 and time.monotonic() >= _DEADLINE:
        raise TimeoutError


def _move_order_score(me, opp, mv, tt_best=None):
    if tt_best is not None and mv == tt_best:
        return 1_000_000_000

    me2, opp2 = _apply(me, opp, mv)

    # If this move leaves the opponent no move, it wins immediately.
    child_edges = _count_moves(opp2, me2)
    if child_edges == 0:
        return 900_000_000

    s, d, _ = mv

    # Pieces adjacent to the landing square may recapture us.
    recapture_danger = (opp2 & _ADJ[d]).bit_count()

    # Prefer moves that leave few opponent replies and land on low-degree cells.
    return (
        -1200 * child_edges
        -160 * recapture_danger
        -12 * _DEG[d]
        + 3 * _DEG[s]
    )


def _ordered_moves(me, opp, moves, tt_best=None):
    return sorted(
        moves,
        key=lambda mv: _move_order_score(me, opp, mv, tt_best),
        reverse=True,
    )


def _static_eval(me, opp):
    moves = _legal_moves(me, opp)
    if not moves:
        return -_WIN

    edge_count = len(moves)
    material = me.bit_count() - opp.bit_count()

    best = -_INF

    for mv in moves:
        me2, opp2 = _apply(me, opp, mv)
        child_edges = _count_moves(opp2, me2)

        # Current player can end the game now.
        if child_edges == 0:
            return 500_000

        d = mv[1]
        recapture_danger = (opp2 & _ADJ[d]).bit_count()

        # Check for opponent immediate win only when cheap.
        reply_win = 0
        if child_edges <= 10:
            for rmv in _legal_moves(opp2, me2):
                rme2, ropp2 = _apply(opp2, me2, rmv)
                if _count_moves(ropp2, rme2) == 0:
                    reply_win = 1
                    break

        val = (
            -125 * child_edges
            -2100 * reply_win
            -90 * recapture_danger
            -10 * _DEG[d]
            + 22 * material
        )
        if val > best:
            best = val

    # A small parity bias: positions with an odd number of available captures
    # are often favorable in simple clobber races.
    best += 35 if (edge_count & 1) else -35
    best += 12 * material
    return best


def _negamax(me, opp, depth, alpha, beta):
    _check_time()

    key = (me, opp)
    entry = _TT.get(key)
    tt_best = None

    if entry is not None:
        e_depth, e_val, e_flag, e_best = entry
        tt_best = e_best
        if e_depth >= depth:
            if e_flag == _EXACT:
                return e_val
            if e_flag == _LOWER:
                if e_val > alpha:
                    alpha = e_val
            elif e_flag == _UPPER:
                if e_val < beta:
                    beta = e_val
            if alpha >= beta:
                return e_val

    moves = _legal_moves(me, opp)
    if not moves:
        val = -_WIN
        _TT[key] = (depth, val, _EXACT, None)
        return val

    if depth <= 0:
        val = _static_eval(me, opp)
        _TT[key] = (0, val, _EXACT, None)
        return val

    alpha0 = alpha
    beta0 = beta

    best_val = -_INF
    best_move = None

    for mv in _ordered_moves(me, opp, moves, tt_best):
        me2, opp2 = _apply(me, opp, mv)
        val = -_negamax(opp2, me2, depth - 1, -beta, -alpha)

        if val > best_val:
            best_val = val
            best_move = mv

        if val > alpha:
            alpha = val

        if alpha >= beta:
            break

    if best_val <= alpha0:
        flag = _UPPER
    elif best_val >= beta0:
        flag = _LOWER
    else:
        flag = _EXACT

    _TT[key] = (depth, best_val, flag, best_move)
    return best_val


def policy(you: list[int], opponent: list[int]) -> str:
    global _DEADLINE, _NODES, _TT

    # Keep memory bounded over long matches.
    if len(_TT) > 250_000:
        _TT.clear()

    me = _bits_from_array(you)
    opp = _bits_from_array(opponent)

    moves = _legal_moves(me, opp)

    # Terminal positions should not be queried. If they are, no legal move
    # exists; this is only a syntactic fallback.
    if not moves:
        return "0,0,U"

    # Start with a strong greedy legal fallback, so timeout still returns legal.
    moves = _ordered_moves(me, opp, moves, None)
    best_move = moves[0]

    # If a move wins immediately, take it.
    for mv in moves:
        me2, opp2 = _apply(me, opp, mv)
        if not _has_move(opp2, me2):
            return _fmt(mv)

    _DEADLINE = time.monotonic() + 0.92
    _NODES = 0

    total_pieces = me.bit_count() + opp.bit_count()
    max_depth = max(1, min(total_pieces, 60))

    try:
        depth = 1
        while depth <= max_depth:
            _check_time()

            current_best = best_move
            current_score = -_INF
            alpha = -_INF
            beta = _INF

            root_entry = _TT.get((me, opp))
            tt_best = root_entry[3] if root_entry is not None else best_move
            ordered = _ordered_moves(me, opp, moves, tt_best)

            for mv in ordered:
                _check_time()
                me2, opp2 = _apply(me, opp, mv)
                score = -_negamax(opp2, me2, depth - 1, -beta, -alpha)

                if score > current_score:
                    current_score = score
                    current_best = mv

                if score > alpha:
                    alpha = score

            best_move = current_best

            # Proven forced win/loss at this depth.
            if current_score >= _WIN // 2:
                break

            depth += 1

    except TimeoutError:
        pass
    except Exception:
        # Never risk failing to return a legal move.
        pass

    return _fmt(best_move)
