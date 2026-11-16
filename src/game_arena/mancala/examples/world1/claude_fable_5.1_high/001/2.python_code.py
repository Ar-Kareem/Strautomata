
import time

TIME_LIMIT = 0.85
INF = 10 ** 9
WIN_BONUS = 100000


class Timeout(Exception):
    pass


def sow(board, side, pit):
    b = board[:]
    seeds = b[pit]
    b[pit] = 0
    if side == 0:
        own_store, opp_store, lo = 6, 13, 0
    else:
        own_store, opp_store, lo = 13, 6, 7
    pos = pit
    while seeds:
        pos += 1
        if pos == 14:
            pos = 0
        if pos == opp_store:
            continue
        b[pos] += 1
        seeds -= 1
    next_side = 1 - side
    if pos == own_store:
        next_side = side
    elif lo <= pos < lo + 6 and b[pos] == 1:
        opp = 12 - pos
        if b[opp] > 0:
            b[own_store] += b[opp] + 1
            b[opp] = 0
            b[pos] = 0
    s0 = b[0] + b[1] + b[2] + b[3] + b[4] + b[5]
    s1 = b[7] + b[8] + b[9] + b[10] + b[11] + b[12]
    if s0 == 0 or s1 == 0:
        b[6] += s0
        b[13] += s1
        for i in range(6):
            b[i] = 0
            b[7 + i] = 0
        return b, next_side, True
    return b, next_side, False


def terminal_value(b, side):
    if side == 0:
        diff = b[6] - b[13]
    else:
        diff = b[13] - b[6]
    if diff > 0:
        return 100 * diff + WIN_BONUS
    if diff < 0:
        return 100 * diff - WIN_BONUS
    return 0


def evaluate(b, side):
    s0 = b[0] + b[1] + b[2] + b[3] + b[4] + b[5]
    s1 = b[7] + b[8] + b[9] + b[10] + b[11] + b[12]
    if side == 0:
        return 100 * (b[6] - b[13]) + 3 * (s0 - s1)
    else:
        return 100 * (b[13] - b[6]) + 3 * (s1 - s0)


class Searcher:
    def __init__(self, deadline):
        self.deadline = deadline
        self.nodes = 0
        self.tt = {}

    def check_time(self):
        self.nodes += 1
        if (self.nodes & 255) == 0 and time.time() > self.deadline:
            raise Timeout()

    def children(self, b, side):
        lo = 0 if side == 0 else 7
        own_store = 6 if side == 0 else 13
        res = []
        for i in range(6):
            pit = lo + i
            if b[pit] > 0:
                nb, ns, over = sow(b, side, pit)
                key = (nb[own_store] - b[own_store]) + (1000 if ns == side else 0)
                if over:
                    key += 50 if terminal_value(nb, side) > 0 else -50
                res.append((key, pit, nb, ns, over))
        res.sort(key=lambda x: -x[0])
        return res

    def search(self, b, side, depth, alpha, beta):
        self.check_time()
        if depth <= 0:
            return evaluate(b, side)
        key = (tuple(b), side)
        entry = self.tt.get(key)
        tt_move = -1
        if entry is not None:
            e_depth, e_val, e_flag, e_move = entry
            tt_move = e_move
            if e_depth >= depth:
                if e_flag == 0:
                    return e_val
                if e_flag == 1 and e_val >= beta:
                    return e_val
                if e_flag == 2 and e_val <= alpha:
                    return e_val
        orig_alpha = alpha
        kids = self.children(b, side)
        if not kids:
            return terminal_value(b, side)
        if tt_move >= 0:
            for idx, k in enumerate(kids):
                if k[1] == tt_move:
                    kids.insert(0, kids.pop(idx))
                    break
        best = -INF
        best_move = kids[0][1]
        for _, pit, nb, ns, over in kids:
            if over:
                val = terminal_value(nb, side)
            elif ns == side:
                val = self.search(nb, side, depth, alpha, beta)
            else:
                val = -self.search(nb, ns, depth - 1, -beta, -alpha)
            if val > best:
                best = val
                best_move = pit
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
        self.tt[key] = (depth, best, flag, best_move)
        return best


def policy(you, opponent):
    start = time.time()
    deadline = start + TIME_LIMIT
    b = list(you) + list(opponent)
    legal = [i for i in range(6) if b[i] > 0]
    if not legal:
        return 0
    if len(legal) == 1:
        return legal[0]

    searcher = Searcher(deadline)
    kids = searcher.children(b, 0)
    # heuristic fallback: best ordering key
    best_move = kids[0][1]
    for k in kids:
        if k[4] and terminal_value(k[2], 0) > 0:
            return k[1]

    depth = 1
    try:
        while depth <= 60:
            alpha = -INF
            beta = INF
            cur_best = None
            cur_val = -INF
            ordered = kids[:]
            for idx, k in enumerate(ordered):
                if k[1] == best_move:
                    ordered.insert(0, ordered.pop(idx))
                    break
            for _, pit, nb, ns, over in ordered:
                if over:
                    val = terminal_value(nb, 0)
                elif ns == 0:
                    val = searcher.search(nb, 0, depth, alpha, beta)
                else:
                    val = -searcher.search(nb, 1, depth - 1, -beta, -alpha)
                if val > cur_val:
                    cur_val = val
                    cur_best = pit
                if val > alpha:
                    alpha = val
            if cur_best is not None:
                best_move = cur_best
            if cur_val >= WIN_BONUS or cur_val <= -WIN_BONUS:
                break
            depth += 1
    except Timeout:
        pass

    if best_move not in legal:
        best_move = legal[0]
    return best_move
