
import time

ROWS, COLS = 5, 6
N = ROWS * COLS
WIN = 10 ** 6
INF = 10 ** 18
EXACT, LOWER, UPPER = 0, 1, 2

try:
    _pop = int.bit_count
except AttributeError:
    _pop = lambda x: bin(x).count("1")

NOTCOL0 = 0
NOTCOL5 = 0
for r in range(ROWS):
    for c in range(COLS):
        bit = 1 << (r * COLS + c)
        if c != 0:
            NOTCOL0 |= bit
        if c != COLS - 1:
            NOTCOL5 |= bit


def legal_moves(you, opp):
    moves = []
    b = you & (opp << 6)          # U: dest = src - 6
    while b:
        lsb = b & -b
        src = lsb.bit_length() - 1
        moves.append((src, src - 6, src // COLS, src % COLS, 'U'))
        b &= ~lsb
    b = you & (opp >> 6)          # D: dest = src + 6
    while b:
        lsb = b & -b
        src = lsb.bit_length() - 1
        moves.append((src, src + 6, src // COLS, src % COLS, 'D'))
        b &= ~lsb
    b = you & NOTCOL0 & (opp << 1)  # L: dest = src - 1
    while b:
        lsb = b & -b
        src = lsb.bit_length() - 1
        moves.append((src, src - 1, src // COLS, src % COLS, 'L'))
        b &= ~lsb
    b = you & NOTCOL5 & (opp >> 1)  # R: dest = src + 1
    while b:
        lsb = b & -b
        src = lsb.bit_length() - 1
        moves.append((src, src + 1, src // COLS, src % COLS, 'R'))
        b &= ~lsb
    return moves


def _move_count(you, opp):
    cnt = _pop(you & (opp << 6))
    cnt += _pop(you & (opp >> 6))
    cnt += _pop(you & NOTCOL0 & (opp << 1))
    cnt += _pop(you & NOTCOL5 & (opp >> 1))
    return cnt


def _evaluate(you, opp):
    return _move_count(you, opp) - _move_count(opp, you)


def _search(you, opp, depth, alpha, beta, deadline, tt, ply):
    if time.time() > deadline:
        raise TimeoutError()
    key = (you, opp)
    entry = tt.get(key)
    tt_move = None
    if entry is not None:
        e_depth, e_flag, e_val, e_move = entry
        if e_depth >= depth:
            if e_flag == EXACT:
                return e_val
            elif e_flag == LOWER and e_val > alpha:
                alpha = e_val
            elif e_flag == UPPER and e_val < beta:
                beta = e_val
            if alpha >= beta:
                return e_val
        tt_move = e_move
    moves = legal_moves(you, opp)
    if not moves:
        return -WIN + ply
    if depth == 0:
        return _evaluate(you, opp)
    if tt_move is not None:
        tid = (tt_move[0], tt_move[1])
        for i, m in enumerate(moves):
            if (m[0], m[1]) == tid:
                moves[0], moves[i] = moves[i], moves[0]
                break
    alpha_orig = alpha
    best_val = -INF
    best_move = moves[0]
    for m in moves:
        src, dst = m[0], m[1]
        sbit = 1 << src
        dbit = 1 << dst
        new_you = (you & ~sbit) | dbit
        new_opp = opp & ~dbit
        val = -_search(new_opp, new_you, depth - 1, -beta, -alpha,
                       deadline, tt, ply + 1)
        if val > best_val:
            best_val = val
            best_move = m
            if val > alpha:
                alpha = val
                if alpha >= beta:
                    break
    if best_val <= alpha_orig:
        flag = UPPER
    elif best_val >= beta:
        flag = LOWER
    else:
        flag = EXACT
    tt[key] = (depth, flag, best_val, best_move)
    return best_val


def _flatten(board):
    if len(board) == ROWS and hasattr(board[0], "__len__"):
        return [int(board[r][c]) for r in range(ROWS) for c in range(COLS)]
    return [int(x) for x in board]


def _to_bits(flat):
    b = 0
    for i, v in enumerate(flat):
        if v:
            b |= 1 << i
    return b


def policy(you, opponent):
    y_bits = _to_bits(_flatten(you))
    o_bits = _to_bits(_flatten(opponent))
    moves = legal_moves(y_bits, o_bits)
    if not moves:
        return "0,0,U"  # no legal move exists; should not happen
    if len(moves) == 1:
        m = moves[0]
        return "%d,%d,%s" % (m[2], m[3], m[4])

    deadline = time.time() + 0.88
    tt = {}
    best_move = moves[0]
    order_hint = None
    depth = 1
    max_ply = _pop(y_bits) + _pop(o_bits) + 2

    try:
        while depth <= max_ply:
            if order_hint is not None:
                oid = (order_hint[0], order_hint[1])
                for i, m in enumerate(moves):
                    if (m[0], m[1]) == oid:
                        moves[0], moves[i] = moves[i], moves[0]
                        break
            cur_best = None
            cur_val = -INF
            alpha = -INF
            for m in moves:
                src, dst = m[0], m[1]
                sbit = 1 << src
                dbit = 1 << dst
                new_you = (y_bits & ~sbit) | dbit
                new_opp = o_bits & ~dbit
                val = -_search(new_opp, new_you, depth - 1, -INF, -alpha,
                               deadline, tt, 1)
                if val > cur_val:
                    cur_val = val
                    cur_best = m
                    if val > alpha:
                        alpha = val
            if cur_best is not None:
                best_move = cur_best
                order_hint = cur_best
            if cur_val >= WIN:
                break  # forced win found at shallowest depth; stop
            depth += 1
    except TimeoutError:
        pass
    except Exception:
        pass

    m = best_move
    return "%d,%d,%s" % (m[2], m[3], m[4])
