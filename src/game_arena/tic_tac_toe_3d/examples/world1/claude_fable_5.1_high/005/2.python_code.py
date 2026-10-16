
import time

# ---------- precomputation ----------
def _gen_lines():
    lines = set()
    dirs = [(a, b, c) for a in (-1, 0, 1) for b in (-1, 0, 1) for c in (-1, 0, 1)
            if (a, b, c) != (0, 0, 0)]
    for i in range(3):
        for j in range(3):
            for k in range(3):
                for d in dirs:
                    cells = [(i + t * d[0], j + t * d[1], k + t * d[2]) for t in range(3)]
                    if all(0 <= x < 3 for cell in cells for x in cell):
                        lines.add(frozenset(cells))
    res = []
    for L in lines:
        m = 0
        for (i, j, k) in L:
            m |= 1 << (i * 9 + j * 3 + k)
        res.append(m)
    return res

LINES = _gen_lines()
FULL = (1 << 27) - 1
WIN = 10000

try:
    (1).bit_count()
    def _pc(x):
        return x.bit_count()
except AttributeError:
    def _pc(x):
        return bin(x).count("1")

# static ordering by number of lines through each cell
_count = [0] * 27
for _m in LINES:
    for _c in range(27):
        if _m >> _c & 1:
            _count[_c] += 1
ORDER = [1 << c for c in sorted(range(27), key=lambda c: -_count[c])]


class _Timeout(Exception):
    pass


_deadline = 0.0
_nodes = 0
_TT = {}


def _analyze(me, opp):
    """Return (my_win_cells, opp_win_cells, heuristic score from 'me' perspective)."""
    my_win = 0
    opp_win = 0
    score = 0
    for mask in LINES:
        mm = me & mask
        om = opp & mask
        if om == 0:
            if mm:
                c = _pc(mm)
                if c == 2:
                    my_win |= mask & ~mm
                    score += 30
                elif c == 1:
                    score += 2
        elif mm == 0:
            c = _pc(om)
            if c == 2:
                opp_win |= mask & ~om
                score -= 30
            elif c == 1:
                score -= 2
    return my_win, opp_win, score


def _negamax(me, opp, depth, alpha, beta):
    global _nodes
    _nodes += 1
    if not (_nodes & 255) and time.time() > _deadline:
        raise _Timeout()

    empty = FULL & ~(me | opp)
    if empty == 0:
        return 0
    n_empty = _pc(empty)

    my_win, opp_win, score = _analyze(me, opp)
    if my_win:
        return WIN + n_empty
    if opp_win:
        if _pc(opp_win) >= 2:
            return -(WIN + n_empty - 1)
        cand = opp_win
    else:
        if depth <= 0:
            return score
        cand = empty

    key = (me, opp)
    entry = _TT.get(key)
    tt_move = 0
    if entry is not None:
        e_depth, e_val, e_flag, e_move = entry
        tt_move = e_move
        if e_depth >= depth:
            if e_flag == 0:
                return e_val
            elif e_flag == 1:
                if e_val > alpha:
                    alpha = e_val
            else:
                if e_val < beta:
                    beta = e_val
            if alpha >= beta:
                return e_val

    orig_alpha = alpha
    best = -10 ** 9
    best_move = 0

    moves = []
    if tt_move and (tt_move & cand):
        moves.append(tt_move)
    for b in ORDER:
        if (b & cand) and b != tt_move:
            moves.append(b)

    for b in moves:
        val = -_negamax(opp, me | b, depth - 1, -beta, -alpha)
        if val > best:
            best = val
            best_move = b
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break

    if best <= orig_alpha:
        flag = 2  # upper bound
    elif best >= beta:
        flag = 1  # lower bound
    else:
        flag = 0  # exact
    _TT[key] = (depth, best, flag, best_move)
    return best


def _root_search(me, opp, depth, prev_best):
    empty = FULL & ~(me | opp)
    moves = []
    if prev_best and (prev_best & empty):
        moves.append(prev_best)
    for b in ORDER:
        if (b & empty) and b != prev_best:
            moves.append(b)
    alpha = -10 ** 9
    beta = 10 ** 9
    best_val = -10 ** 9
    best_move = moves[0]
    for b in moves:
        val = -_negamax(opp, me | b, depth - 1, -beta, -alpha)
        if val > best_val:
            best_val = val
            best_move = b
        if val > alpha:
            alpha = val
    return best_val, best_move


def _bit_to_move(b):
    idx = b.bit_length() - 1
    return (idx // 9, (idx // 3) % 3, idx % 3)


def _fallback(board):
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    return (i, j, k)
    return (0, 0, 0)


def policy(board):
    global _deadline, _nodes, _TT
    start = time.time()
    try:
        me = 0
        opp = 0
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    v = board[i][j][k]
                    if v == 1:
                        me |= 1 << (i * 9 + j * 3 + k)
                    elif v == -1:
                        opp |= 1 << (i * 9 + j * 3 + k)
        empty = FULL & ~(me | opp)
        if empty == 0:
            return _fallback(board)
        if empty == FULL:
            return (1, 1, 1)

        my_win, opp_win, _ = _analyze(me, opp)
        # 1. immediate win
        if my_win:
            for b in ORDER:
                if b & my_win:
                    return _bit_to_move(b)
        # 2. forced block
        if opp_win:
            for b in ORDER:
                if b & opp_win:
                    return _bit_to_move(b)

        # 3. search
        _TT = {}
        _nodes = 0
        _deadline = start + 0.5
        n_empty = _pc(empty)

        # default move: best static-order empty cell
        best_move = 0
        for b in ORDER:
            if b & empty:
                best_move = b
                break

        depth = 1
        try:
            while depth <= n_empty:
                val, mv = _root_search(me, opp, depth, best_move)
                best_move = mv
                if abs(val) >= WIN:
                    break
                depth += 1
        except _Timeout:
            pass

        if best_move and (best_move & empty):
            return _bit_to_move(best_move)
        return _fallback(board)
    except Exception:
        return _fallback(board)
