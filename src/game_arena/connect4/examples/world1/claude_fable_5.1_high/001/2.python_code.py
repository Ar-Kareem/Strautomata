
import time

H1 = 7
COL_MASK = [((1 << 6) - 1) << (c * H1) for c in range(7)]
COL_BOTTOM = [1 << (c * H1) for c in range(7)]
ALL_MASK = sum(COL_MASK)
ORDER = [3, 2, 4, 1, 5, 0, 6]
WIN = 100000
INF = 10 ** 9
CENTER = COL_MASK[3]
SC = [0, 1, 4, 32, 0]

WINDOWS = []
for _c in range(7):
    for _r in range(6):
        for _dc, _dr in ((0, 1), (1, 0), (1, 1), (1, -1)):
            cells = []
            ok = True
            for i in range(4):
                cc = _c + _dc * i
                rr = _r + _dr * i
                if not (0 <= cc < 7 and 0 <= rr < 6):
                    ok = False
                    break
                cells.append(1 << (cc * H1 + rr))
            if ok:
                WINDOWS.append(sum(cells))


class Timeout(Exception):
    pass


def has_won(b):
    m = b & (b >> 1)
    if m & (m >> 2):
        return True
    m = b & (b >> 7)
    if m & (m >> 14):
        return True
    m = b & (b >> 8)
    if m & (m >> 16):
        return True
    m = b & (b >> 6)
    if m & (m >> 12):
        return True
    return False


def evaluate(me, opp):
    s = 0
    for w in WINDOWS:
        if not (w & opp):
            m = w & me
            if m:
                s += SC[bin(m).count('1')]
        elif not (w & me):
            s -= SC[bin(w & opp).count('1')]
    s += 3 * (bin(me & CENTER).count('1') - bin(opp & CENTER).count('1'))
    return s


TT = {}
_nodes = 0
_deadline = 0.0


def negamax(me, opp, depth, alpha, beta, ply):
    global _nodes
    _nodes += 1
    if (_nodes & 511) == 0 and time.perf_counter() > _deadline:
        raise Timeout
    mask = me | opp
    if mask == ALL_MASK:
        return 0
    # immediate win
    for c in ORDER:
        bit = (mask + COL_BOTTOM[c]) & COL_MASK[c]
        if bit and has_won(me | bit):
            return WIN - ply
    # opponent threats
    opp_wins = []
    for c in range(7):
        bit = (mask + COL_BOTTOM[c]) & COL_MASK[c]
        if bit and has_won(opp | bit):
            opp_wins.append(c)
    if len(opp_wins) > 1:
        return -(WIN - ply - 1)
    if depth <= 0:
        return evaluate(me, opp)
    key = (me, opp)
    entry = TT.get(key)
    tt_move = -1
    if entry is not None:
        edepth, evalue, eflag, emove = entry
        tt_move = emove
        if edepth >= depth:
            if eflag == 0:
                return evalue
            elif eflag == 1:
                if evalue > alpha:
                    alpha = evalue
            else:
                if evalue < beta:
                    beta = evalue
            if alpha >= beta:
                return evalue
    if len(opp_wins) == 1:
        moves = opp_wins
    elif tt_move >= 0:
        moves = [tt_move] + [c for c in ORDER if c != tt_move]
    else:
        moves = ORDER
    alpha_orig = alpha
    best = -INF
    bm = -1
    for c in moves:
        bit = (mask + COL_BOTTOM[c]) & COL_MASK[c]
        if not bit:
            continue
        v = -negamax(opp, me | bit, depth - 1, -beta, -alpha, ply + 1)
        if v > best:
            best = v
            bm = c
        if v > alpha:
            alpha = v
        if alpha >= beta:
            break
    if best <= alpha_orig:
        flag = 2
    elif best >= beta:
        flag = 1
    else:
        flag = 0
    TT[key] = (depth, best, flag, bm)
    return best


def _search(me, opp, legal, time_budget):
    global _deadline, _nodes, TT
    _deadline = time.perf_counter() + time_budget
    _nodes = 0
    TT = {}
    mask = me | opp
    ordered = [c for c in ORDER if c in legal]
    best_move = ordered[0]
    # immediate win at root
    for c in ordered:
        bit = (mask + COL_BOTTOM[c]) & COL_MASK[c]
        if has_won(me | bit):
            return c
    # forced block
    blocks = []
    for c in ordered:
        bit = (mask + COL_BOTTOM[c]) & COL_MASK[c]
        if has_won(opp | bit):
            blocks.append(c)
    if len(blocks) >= 1:
        return blocks[0]
    # avoid moves that give opponent an immediate win, if possible
    safe = []
    for c in ordered:
        bit = (mask + COL_BOTTOM[c]) & COL_MASK[c]
        nmask = mask | bit
        above = (nmask + COL_BOTTOM[c]) & COL_MASK[c]
        if above and has_won(opp | above):
            continue
        safe.append(c)
    if safe:
        ordered = safe
        best_move = ordered[0]
    if len(ordered) == 1:
        return ordered[0]
    empties = 42 - bin(mask).count('1')
    max_depth = min(42, empties)
    try:
        for depth in range(1, max_depth + 1):
            alpha = -INF
            beta = INF
            cur_best = None
            cur_val = -INF
            for c in ordered:
                bit = (mask + COL_BOTTOM[c]) & COL_MASK[c]
                v = -negamax(opp, me | bit, depth - 1, -beta, -alpha, 1)
                if v > cur_val:
                    cur_val = v
                    cur_best = c
                if v > alpha:
                    alpha = v
            if cur_best is not None:
                best_move = cur_best
                ordered = [cur_best] + [c for c in ordered if c != cur_best]
            if cur_val >= WIN - 100:
                break
            if cur_val <= -WIN + 100:
                break
    except Timeout:
        pass
    return best_move


def policy(board):
    try:
        me = 0
        opp = 0
        for r in range(6):
            row = board[r]
            for c in range(7):
                v = row[c]
                if v == 1:
                    me |= 1 << (c * H1 + (5 - r))
                elif v == -1:
                    opp |= 1 << (c * H1 + (5 - r))
        legal = [c for c in range(7) if board[0][c] == 0]
        if not legal:
            return 0
        if me == 0 and opp == 0:
            return 3
        move = _search(me, opp, legal, 0.65)
        if move in legal:
            return int(move)
        for c in ORDER:
            if c in legal:
                return c
        return legal[0]
    except Exception:
        for c in [3, 2, 4, 1, 5, 0, 6]:
            try:
                if board[0][c] == 0:
                    return c
            except Exception:
                pass
        return 0
