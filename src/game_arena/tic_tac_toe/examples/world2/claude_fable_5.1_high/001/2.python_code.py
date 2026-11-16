
import time

# ---------- precomputation ----------
LINES = []
for r in range(4):
    LINES.append(sum(1 << (r * 4 + c) for c in range(4)))
for c in range(4):
    LINES.append(sum(1 << (r * 4 + c) for r in range(4)))
LINES.append(sum(1 << (i * 4 + i) for i in range(4)))
LINES.append(sum(1 << (i * 4 + 3 - i) for i in range(4)))
FULL = 0xFFFF
POP = [bin(i).count('1') for i in range(1 << 16)]
W = [0, 1, 8, 64]
WIN = 100000
# move ordering: cells on 3 lines first (corners, centers), then edges
ORDER = [0, 3, 12, 15, 5, 6, 9, 10, 1, 2, 4, 8, 7, 11, 13, 14]
ORDER_BITS = [(i, 1 << i) for i in ORDER]


class Timeout(Exception):
    pass


def wins(mask):
    for L in LINES:
        if mask & L == L:
            return True
    return False


def evaluate(me, op):
    s = 0
    for L in LINES:
        m = POP[me & L]
        o = POP[op & L]
        if m and o:
            continue
        s += W[m] - W[o]
    return s


class Searcher:
    def __init__(self, deadline):
        self.deadline = deadline
        self.nodes = 0
        self.tt = {}

    def negamax(self, me, op, depth, alpha, beta):
        self.nodes += 1
        if (self.nodes & 255) == 0 and time.perf_counter() > self.deadline:
            raise Timeout()
        if wins(op):
            return -(WIN + depth)
        occ = me | op
        if occ == FULL:
            return 0
        if depth == 0:
            return evaluate(me, op)

        key = (me, op)
        entry = self.tt.get(key)
        tt_move = -1
        if entry is not None:
            e_depth, e_flag, e_val, e_move = entry
            tt_move = e_move
            if e_depth >= depth:
                if e_flag == 0:
                    return e_val
                elif e_flag == 1:  # lower bound
                    if e_val > alpha:
                        alpha = e_val
                elif e_flag == 2:  # upper bound
                    if e_val < beta:
                        beta = e_val
                if alpha >= beta:
                    return e_val

        orig_alpha = alpha
        best = -10 ** 9
        best_move = -1
        # move ordering
        if tt_move >= 0 and not (occ >> tt_move) & 1:
            moves = [tt_move] + [i for i, b in ORDER_BITS if not occ & b and i != tt_move]
        else:
            moves = [i for i, b in ORDER_BITS if not occ & b]

        for mv in moves:
            val = -self.negamax(me | (1 << mv), op, depth - 1, -beta, -alpha)
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
        self.tt[key] = (depth, flag, best, best_move)
        return best

    def root(self, me, op, depth, first_move):
        occ = me | op
        moves = [i for i, b in ORDER_BITS if not occ & b]
        if first_move in moves:
            moves.remove(first_move)
            moves.insert(0, first_move)
        alpha = -10 ** 9
        beta = 10 ** 9
        best = -10 ** 9
        best_move = moves[0]
        for mv in moves:
            val = -self.negamax(me | (1 << mv), op, depth - 1, -beta, -alpha)
            if val > best:
                best = val
                best_move = mv
            if val > alpha:
                alpha = val
        return best_move, best


def policy(board):
    start = time.perf_counter()
    empties = [(r, c) for r in range(4) for c in range(4) if board[r][c] == 0]
    if not empties:
        return (0, 0)
    fallback = empties[0]
    try:
        me = 0
        op = 0
        for r in range(4):
            for c in range(4):
                v = board[r][c]
                if v == 1:
                    me |= 1 << (r * 4 + c)
                elif v == -1:
                    op |= 1 << (r * 4 + c)
        occ = me | op
        free = [i for i in range(16) if not (occ >> i) & 1]

        # immediate win
        for i in free:
            if wins(me | (1 << i)):
                return (i // 4, i % 4)
        # immediate block
        block = None
        for i in free:
            if wins(op | (1 << i)):
                block = i
                break
        if block is not None:
            return (block // 4, block % 4)

        deadline = start + 0.75
        searcher = Searcher(deadline)
        best_move = free[0]
        # prefer strategically ordered fallback
        for i, b in ORDER_BITS:
            if not occ & b:
                best_move = i
                break
        max_depth = len(free)
        for depth in range(1, max_depth + 1):
            try:
                mv, val = searcher.root(me, op, depth, best_move)
                best_move = mv
                if abs(val) >= WIN:
                    break
            except Timeout:
                break
        r, c = best_move // 4, best_move % 4
        if board[r][c] == 0:
            return (r, c)
        return fallback
    except Exception:
        return fallback
