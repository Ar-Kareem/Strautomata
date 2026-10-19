
import time

ROWS, COLS = 5, 6
FULL = (1 << 30) - 1
COL0 = sum(1 << (r * 6) for r in range(5))
COL5 = sum(1 << (r * 6 + 5) for r in range(5))
NOT_COL0 = FULL & ~COL0
NOT_COL5 = FULL & ~COL5
WIN = 100000
TIME_LIMIT = 0.85

try:
    (0).bit_count()
    def popcount(x):
        return x.bit_count()
except AttributeError:
    def popcount(x):
        return bin(x).count('1')


def mobility(me, opp):
    return (popcount(me & (opp << 6)) +
            popcount(me & (opp >> 6)) +
            popcount(me & ((opp & NOT_COL5) << 1)) +
            popcount(me & ((opp & NOT_COL0) >> 1)))


def gen_moves(me, opp):
    moves = []
    m = me & (opp << 6)
    while m:
        b = m & -m
        i = b.bit_length() - 1
        moves.append((i, i - 6, 'U'))
        m ^= b
    m = me & (opp >> 6)
    while m:
        b = m & -m
        i = b.bit_length() - 1
        moves.append((i, i + 6, 'D'))
        m ^= b
    m = me & ((opp & NOT_COL5) << 1)
    while m:
        b = m & -m
        i = b.bit_length() - 1
        moves.append((i, i - 1, 'L'))
        m ^= b
    m = me & ((opp & NOT_COL0) >> 1)
    while m:
        b = m & -m
        i = b.bit_length() - 1
        moves.append((i, i + 1, 'R'))
        m ^= b
    return moves


class Timeout(Exception):
    pass


class Searcher:
    def __init__(self, deadline):
        self.deadline = deadline
        self.tt = {}
        self.nodes = 0

    def evaluate(self, me, opp):
        return mobility(me, opp) - mobility(opp, me)

    def negamax(self, me, opp, depth, alpha, beta):
        self.nodes += 1
        if (self.nodes & 1023) == 0 and time.time() > self.deadline:
            raise Timeout()
        key = (me, opp)
        entry = self.tt.get(key)
        tt_move = None
        if entry is not None:
            e_depth, e_val, e_flag, e_move = entry
            tt_move = e_move
            if e_depth >= depth:
                if e_flag == 0:
                    return e_val
                elif e_flag == 1:
                    if e_val >= beta:
                        return e_val
                    if e_val > alpha:
                        alpha = e_val
                else:
                    if e_val <= alpha:
                        return e_val
                    if e_val < beta:
                        beta = e_val
        moves = gen_moves(me, opp)
        if not moves:
            return -(WIN + depth)
        if depth <= 0:
            return self.evaluate(me, opp)

        # Move ordering
        if depth >= 2:
            scored = []
            for mv in moves:
                fr, to, d = mv
                fb = 1 << fr
                tb = 1 << to
                me2 = (me ^ fb) | tb
                opp2 = opp ^ tb
                s = mobility(me2, opp2) - mobility(opp2, me2)
                if mv == tt_move:
                    s += 1000
                scored.append((s, mv))
            scored.sort(key=lambda x: -x[0])
            moves = [mv for _, mv in scored]
        elif tt_move is not None and tt_move in moves:
            moves.remove(tt_move)
            moves.insert(0, tt_move)

        orig_alpha = alpha
        best = -10 * WIN
        best_move = moves[0]
        for mv in moves:
            fr, to, d = mv
            fb = 1 << fr
            tb = 1 << to
            me2 = (me ^ fb) | tb
            opp2 = opp ^ tb
            val = -self.negamax(opp2, me2, depth - 1, -beta, -alpha)
            if val > best:
                best = val
                best_move = mv
            if val > alpha:
                alpha = val
            if alpha >= beta:
                break
        if best <= orig_alpha:
            flag = 2
        elif best >= beta:
            flag = 1
        else:
            flag = 0
        self.tt[key] = (depth, best, flag, best_move)
        return best


def policy(you, opponent):
    start = time.time()
    deadline = start + TIME_LIMIT
    me = 0
    opp = 0
    for r in range(ROWS):
        for c in range(COLS):
            if int(you[r][c]) == 1:
                me |= 1 << (r * 6 + c)
            if int(opponent[r][c]) == 1:
                opp |= 1 << (r * 6 + c)

    moves = gen_moves(me, opp)
    if not moves:
        # No legal moves; return something syntactically valid.
        return "0,0,U"

    def fmt(mv):
        fr, to, d = mv
        return "%d,%d,%s" % (fr // 6, fr % 6, d)

    if len(moves) == 1:
        return fmt(moves[0])

    searcher = Searcher(deadline)
    best_move = moves[0]
    # Initial ordering by static evaluation
    scored = []
    for mv in moves:
        fr, to, d = mv
        fb = 1 << fr
        tb = 1 << to
        me2 = (me ^ fb) | tb
        opp2 = opp ^ tb
        scored.append((mobility(me2, opp2) - mobility(opp2, me2), mv))
    scored.sort(key=lambda x: -x[0])
    root_moves = [mv for _, mv in scored]
    best_move = root_moves[0]

    depth = 1
    try:
        while depth <= 60:
            alpha = -10 * WIN
            beta = 10 * WIN
            cur_best = None
            cur_best_val = -10 * WIN
            results = []
            for mv in root_moves:
                fr, to, d = mv
                fb = 1 << fr
                tb = 1 << to
                me2 = (me ^ fb) | tb
                opp2 = opp ^ tb
                val = -searcher.negamax(opp2, me2, depth - 1, -beta, -alpha)
                results.append((val, mv))
                if val > cur_best_val:
                    cur_best_val = val
                    cur_best = mv
                if val > alpha:
                    alpha = val
            best_move = cur_best
            results.sort(key=lambda x: -x[0])
            root_moves = [mv for _, mv in results]
            if cur_best_val >= WIN or cur_best_val <= -WIN:
                break
            depth += 1
    except Timeout:
        pass

    return fmt(best_move)
