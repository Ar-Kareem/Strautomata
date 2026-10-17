
import time

# Bit index: r*4 + c
LINES = []
for r in range(4):
    LINES.append(sum(1 << (r * 4 + c) for c in range(4)))
for c in range(4):
    LINES.append(sum(1 << (r * 4 + c) for r in range(4)))
LINES.append(sum(1 << (i * 4 + i) for i in range(4)))
LINES.append(sum(1 << (i * 4 + (3 - i)) for i in range(4)))

FULL = 0xFFFF
POP = [bin(i).count("1") for i in range(1 << 16)]
WIN = 100000
LINE_SCORE = [0, 1, 8, 60, 0]
CENTER = {5, 6, 9, 10}
ORDER = [5, 6, 9, 10, 0, 3, 12, 15, 1, 2, 4, 7, 8, 11, 13, 14]

TIME_BUDGET = 0.6


class Timeout(Exception):
    pass


def won(bits):
    for L in LINES:
        if bits & L == L:
            return True
    return False


def evaluate(me, opp):
    s = 0
    for L in LINES:
        m = POP[me & L]
        o = POP[opp & L]
        if o == 0:
            s += LINE_SCORE[m]
        elif m == 0:
            s -= LINE_SCORE[o]
    for i in CENTER:
        b = 1 << i
        if me & b:
            s += 2
        elif opp & b:
            s -= 2
    return s


class Searcher:
    def __init__(self, deadline):
        self.deadline = deadline
        self.nodes = 0
        self.tt = {}

    def check_time(self):
        self.nodes += 1
        if (self.nodes & 1023) == 0 and time.perf_counter() > self.deadline:
            raise Timeout()

    def negamax(self, me, opp, depth, alpha, beta):
        self.check_time()
        key = (me, opp)
        entry = self.tt.get(key)
        tt_move = -1
        if entry is not None:
            e_depth, e_flag, e_val, e_move = entry
            tt_move = e_move
            if e_depth >= depth:
                if e_flag == 0:
                    return e_val
                if e_flag == 1 and e_val >= beta:
                    return e_val
                if e_flag == 2 and e_val <= alpha:
                    return e_val
        if depth == 0:
            return evaluate(me, opp)
        empty = FULL & ~(me | opp)
        moves = []
        if tt_move >= 0 and (empty >> tt_move) & 1:
            moves.append(tt_move)
        for i in ORDER:
            if (empty >> i) & 1 and i != tt_move:
                moves.append(i)
        orig_alpha = alpha
        best = -10 * WIN
        best_move = moves[0]
        for mv in moves:
            b = 1 << mv
            nme = me | b
            if won(nme):
                val = WIN + depth
            elif (nme | opp) == FULL:
                val = 0
            else:
                val = -self.negamax(opp, nme, depth - 1, -beta, -alpha)
            if val > best:
                best = val
                best_move = mv
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        if best <= orig_alpha:
            flag = 2
        elif best >= beta:
            flag = 1
        else:
            flag = 0
        self.tt[key] = (depth, flag, best, best_move)
        return best

    def root(self, me, opp, depth, order):
        alpha = -10 * WIN
        beta = 10 * WIN
        best = -10 * WIN
        best_move = order[0]
        scores = {}
        for mv in order:
            b = 1 << mv
            nme = me | b
            if won(nme):
                val = WIN + depth
            elif (nme | opp) == FULL:
                val = 0
            else:
                val = -self.negamax(opp, nme, depth - 1, -beta, -alpha)
            scores[mv] = val
            if val > best:
                best = val
                best_move = mv
            if best > alpha:
                alpha = best
        return best, best_move, scores


def policy(board):
    start = time.perf_counter()
    me = 0
    opp = 0
    empties = []
    for r in range(4):
        for c in range(4):
            v = board[r][c]
            idx = r * 4 + c
            if v == 1:
                me |= 1 << idx
            elif v == -1:
                opp |= 1 << idx
            else:
                empties.append(idx)
    if not empties:
        return (0, 0)
    fallback = empties[0]
    for i in ORDER:
        if i in empties:
            fallback = i
            break

    # Immediate win
    for i in empties:
        if won(me | (1 << i)):
            return (i // 4, i % 4)
    # Immediate block
    blocks = [i for i in empties if won(opp | (1 << i))]
    if len(blocks) == 1:
        return (blocks[0] // 4, blocks[0] % 4)
    if len(blocks) > 1:
        return (blocks[0] // 4, blocks[0] % 4)

    if len(empties) == 16:
        return (1, 1)

    deadline = start + TIME_BUDGET
    searcher = Searcher(deadline)
    order = [i for i in ORDER if i in empties]
    best_move = fallback
    max_depth = len(empties)
    try:
        for depth in range(1, max_depth + 1):
            best, mv, scores = searcher.root(me, opp, depth, order)
            best_move = mv
            # Reorder: best first
            order.sort(key=lambda m: -scores.get(m, -10 * WIN))
            if best >= WIN or best <= -WIN:
                break
            if time.perf_counter() > deadline:
                break
    except Timeout:
        pass

    if best_move not in empties:
        best_move = fallback
    return (best_move // 4, best_move % 4)
