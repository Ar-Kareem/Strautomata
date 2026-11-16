
import time
import numbers

ROWS = 5
COLS = 6
N = ROWS * COLS

INF = 10**9
MATE = 100000

ENDGAME_PIECES = 14
ENDGAME_BRANCH_PIECES = 18

DIRS = [(-1, 0, "U"), (0, 1, "R"), (1, 0, "D"), (0, -1, "L")]

NEIGHBORS = [[] for _ in range(N)]
ADJ_MASK = [0] * N
CENTER_WEIGHT = [0] * N

for r in range(ROWS):
    for c in range(COLS):
        i = r * COLS + c
        mask = 0
        for dr, dc, ch in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS:
                j = nr * COLS + nc
                NEIGHBORS[i].append((j, ch))
                mask |= 1 << j
        ADJ_MASK[i] = mask
        d = min(abs(r - 2) + abs(c - 2), abs(r - 2) + abs(c - 3))
        CENTER_WEIGHT[i] = max(0, 3 - d)

_DEADLINE = 0.0
_NODES = 0
_TT = {}
_EXACT = {}
_PV = {}


def _check_time():
    global _NODES
    _NODES += 1
    if (_NODES & 1023) == 0 and time.perf_counter() >= _DEADLINE:
        raise TimeoutError


def _flatten_board(board):
    try:
        return list(board.reshape(-1))
    except Exception:
        pass

    try:
        if len(board) == N:
            first = board[0]
            if isinstance(first, numbers.Integral):
                return list(board)
    except Exception:
        pass

    flat = []
    try:
        for row in board:
            if isinstance(row, numbers.Integral):
                flat.append(row)
            else:
                flat.extend(list(row))
    except Exception:
        flat = list(board)

    if len(flat) != N:
        tmp = []
        for x in flat:
            if isinstance(x, numbers.Integral):
                tmp.append(x)
            else:
                try:
                    tmp.extend(list(x))
                except Exception:
                    tmp.append(x)
        flat = tmp

    return flat[:N]


def _to_bits(board):
    flat = _flatten_board(board)
    bits = 0
    for i, v in enumerate(flat):
        if int(v):
            bits |= 1 << i
    return bits


def _move_to_str(move):
    i, _, d = move
    return f"{i // COLS},{i % COLS},{d}"


def _has_moves(me, opp):
    b = me
    while b:
        lsb = b & -b
        i = lsb.bit_length() - 1
        if ADJ_MASK[i] & opp:
            return True
        b ^= lsb
    return False


def _gen_moves(me, opp):
    moves = []
    b = me
    while b:
        lsb = b & -b
        i = lsb.bit_length() - 1
        b ^= lsb
        if not (ADJ_MASK[i] & opp):
            continue
        for j, ch in NEIGHBORS[i]:
            if (opp >> j) & 1:
                moves.append((i, j, ch))
    return moves


def _apply_move(me, opp, move):
    i, j, _ = move
    me2 = (me ^ (1 << i)) | (1 << j)
    opp2 = opp ^ (1 << j)
    return me2, opp2


def _stats(bb, other):
    total = 0
    active = 0
    forks = 0
    center = 0
    b = bb
    while b:
        lsb = b & -b
        i = lsb.bit_length() - 1
        b ^= lsb
        total += 1
        cnt = (ADJ_MASK[i] & other).bit_count()
        if cnt:
            active += 1
            forks += cnt * cnt
            center += CENTER_WEIGHT[i]
    return total, active, forks, center


def _heuristic(me, opp):
    mt, ma, mf, mc = _stats(me, opp)
    if ma == 0:
        return -MATE
    ot, oa, of, oc = _stats(opp, me)

    dead_me = mt - ma
    dead_opp = ot - oa

    return (
        80 * (ma - oa)
        + 18 * (mf - of)
        + 8 * (dead_opp - dead_me)
        + 6 * (mc - oc)
        + 2 * (ot - mt)
    )


def _order_moves(moves, me, opp, tt_move=None, deep=False):
    if len(moves) <= 1:
        return moves

    scored = []
    for move in moves:
        i, j, _ = move
        opp_after = opp ^ (1 << j)

        score = 0
        if tt_move is not None and move == tt_move:
            score += 1_000_000

        threats = (ADJ_MASK[j] & opp_after).bit_count()
        saved = (ADJ_MASK[i] & opp).bit_count()

        score += 12 * saved
        score -= 20 * threats
        score += 3 * (CENTER_WEIGHT[j] - CENTER_WEIGHT[i])

        if deep:
            me_after = (me ^ (1 << i)) | (1 << j)
            score += -_heuristic(opp_after, me_after)

        scored.append((score, move))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in scored]


def _exact_solve(me, opp, alpha, beta):
    _check_time()
    key = (me, opp)

    if key in _EXACT:
        return _EXACT[key]

    moves = _gen_moves(me, opp)
    if not moves:
        _EXACT[key] = -1
        return -1

    tt_move = _PV.get(key)
    moves = _order_moves(moves, me, opp, tt_move=tt_move, deep=True)

    best = -1
    best_move = moves[0]

    for move in moves:
        me2, opp2 = _apply_move(me, opp, move)
        val = -_exact_solve(opp2, me2, -beta, -alpha)
        if val > best:
            best = val
            best_move = move
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break

    _EXACT[key] = best
    _PV[key] = best_move
    return best


def _negamax(me, opp, depth, alpha, beta):
    _check_time()

    key = (me, opp)
    moves = _gen_moves(me, opp)
    if not moves:
        return -MATE

    occ = (me | opp).bit_count()
    if occ <= ENDGAME_PIECES or (occ <= ENDGAME_BRANCH_PIECES and len(moves) <= 5):
        return _exact_solve(me, opp, -1, 1) * MATE

    if depth <= 0:
        return _heuristic(me, opp)

    orig_alpha = alpha
    orig_beta = beta

    tt_move = None
    entry = _TT.get(key)
    if entry is not None:
        edepth, flag, val, bm = entry
        tt_move = bm
        if edepth >= depth:
            if flag == 0:
                return val
            elif flag == 1:
                if val > alpha:
                    alpha = val
            else:
                if val < beta:
                    beta = val
            if alpha >= beta:
                return val
    else:
        tt_move = _PV.get(key)

    moves = _order_moves(moves, me, opp, tt_move=tt_move, deep=(depth >= 3 and len(moves) <= 10))

    best = -INF
    best_move = moves[0]

    for move in moves:
        me2, opp2 = _apply_move(me, opp, move)
        val = -_negamax(opp2, me2, depth - 1, -beta, -alpha)
        if val > best:
            best = val
            best_move = move
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break

    flag = 0
    if best <= orig_alpha:
        flag = -1
    elif best >= orig_beta:
        flag = 1

    _TT[key] = (depth, flag, best, best_move)
    _PV[key] = best_move
    return best


def policy(you, opponent):
    global _DEADLINE, _NODES, _TT, _EXACT, _PV

    me = _to_bits(you)
    opp = _to_bits(opponent)

    moves = _gen_moves(me, opp)
    if not moves:
        return "0,0,U"

    _TT = {}
    _EXACT = {}
    _PV = {}
    _NODES = 0
    _DEADLINE = time.perf_counter() + 0.94

    ordered = _order_moves(moves, me, opp, deep=True)
    best_move = ordered[0]

    try:
        for move in ordered:
            me2, opp2 = _apply_move(me, opp, move)
            if not _has_moves(opp2, me2):
                return _move_to_str(move)

        occ = (me | opp).bit_count()
        if occ <= ENDGAME_PIECES or (occ <= ENDGAME_BRANCH_PIECES and len(moves) <= 5):
            for move in ordered:
                me2, opp2 = _apply_move(me, opp, move)
                if -_exact_solve(opp2, me2, -1, 1) == 1:
                    return _move_to_str(move)
            return _move_to_str(best_move)

        prev_best = best_move
        max_depth = min(18, occ - 1)

        for depth in range(1, max_depth + 1):
            alpha = -INF
            beta = INF

            root_moves = _order_moves(moves, me, opp, tt_move=prev_best, deep=True)
            local_best = root_moves[0]
            local_val = -INF

            for move in root_moves:
                me2, opp2 = _apply_move(me, opp, move)
                val = -_negamax(opp2, me2, depth - 1, -beta, -alpha)
                if val > local_val:
                    local_val = val
                    local_best = move
                if val > alpha:
                    alpha = val

            best_move = local_best
            prev_best = local_best

            if abs(local_val) >= MATE:
                break

    except TimeoutError:
        pass

    return _move_to_str(best_move)
