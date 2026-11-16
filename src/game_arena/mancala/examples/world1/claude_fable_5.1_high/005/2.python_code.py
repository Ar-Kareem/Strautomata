
import time

TIME_BUDGET = 0.75
WIN_BONUS = 100.0


class Timeout(Exception):
    pass


def sow(me, opp, i):
    """Apply move i for player 'me'. Returns (new_me, new_opp, extra_move)."""
    board = list(me[:7]) + list(opp[:6])
    seeds = board[i]
    board[i] = 0
    full, rem = divmod(seeds, 13)
    if full:
        for k in range(13):
            board[k] += full
    idx = i
    for _ in range(rem):
        idx += 1
        if idx == 13:
            idx = 0
        board[idx] += 1
    if rem == 0:
        idx = i
    extra = (idx == 6)
    if idx < 6 and board[idx] == 1:
        opp_idx = 12 - idx
        if board[opp_idx] > 0:
            board[6] += 1 + board[opp_idx]
            board[idx] = 0
            board[opp_idx] = 0
    nme = board[:7]
    nopp = board[7:13] + [opp[6]]
    if sum(nme[:6]) == 0 or sum(nopp[:6]) == 0:
        nme[6] += sum(nme[:6])
        nopp[6] += sum(nopp[:6])
        for k in range(6):
            nme[k] = 0
            nopp[k] = 0
    return tuple(nme), tuple(nopp), extra


class Searcher:
    def __init__(self, total, deadline):
        self.total = total
        self.deadline = deadline
        self.nodes = 0
        self.tt = {}

    def check_time(self):
        self.nodes += 1
        if (self.nodes & 1023) == 0:
            if time.time() > self.deadline:
                raise Timeout()

    def evaluate(self, me, opp):
        diff = me[6] - opp[6]
        half = self.total / 2.0
        if me[6] > half:
            return diff + WIN_BONUS
        if opp[6] > half:
            return diff - WIN_BONUS
        my_side = sum(me[:6])
        op_side = sum(opp[:6])
        if my_side == 0 and op_side == 0:
            if diff > 0:
                return diff + WIN_BONUS
            if diff < 0:
                return diff - WIN_BONUS
            return 0.0
        my_mob = sum(1 for k in range(6) if me[k] > 0)
        op_mob = sum(1 for k in range(6) if opp[k] > 0)
        return diff + 0.15 * (my_side - op_side) + 0.05 * (my_mob - op_mob)

    def ordered_moves(self, me, opp, first=None):
        moves = []
        for i in range(6):
            if me[i] > 0:
                nme, nopp, extra = sow(me, opp, i)
                gain = nme[6] - me[6]
                key = gain + (50 if extra else 0)
                if first is not None and i == first:
                    key += 1000
                moves.append((key, i, nme, nopp, extra))
        moves.sort(key=lambda t: -t[0])
        return moves

    def negamax(self, me, opp, depth, alpha, beta):
        self.check_time()
        half = self.total / 2.0
        if me[6] > half or opp[6] > half or (sum(me[:6]) == 0 and sum(opp[:6]) == 0):
            return self.evaluate(me, opp)
        if depth <= 0:
            return self.evaluate(me, opp)

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
                    if e_val > alpha:
                        alpha = e_val
                elif e_flag == 2:
                    if e_val < beta:
                        beta = e_val
                if alpha >= beta:
                    return e_val

        alpha_orig = alpha
        best = -1e9
        best_move = None
        for _, i, nme, nopp, extra in self.ordered_moves(me, opp, tt_move):
            if extra:
                val = self.negamax(nme, nopp, depth, alpha, beta)
            else:
                val = -self.negamax(nopp, nme, depth - 1, -beta, -alpha)
            if val > best:
                best = val
                best_move = i
            if val > alpha:
                alpha = val
            if alpha >= beta:
                break

        if best <= alpha_orig:
            flag = 2  # upper bound
        elif best >= beta:
            flag = 1  # lower bound
        else:
            flag = 0  # exact
        self.tt[key] = (depth, best, flag, best_move)
        return best


def policy(you, opponent):
    start = time.time()
    me = tuple(int(x) for x in you)
    opp = tuple(int(x) for x in opponent)
    legal = [i for i in range(6) if me[i] > 0]
    if not legal:
        return 0
    if len(legal) == 1:
        return legal[0]

    total = sum(me) + sum(opp)
    searcher = Searcher(total, start + TIME_BUDGET)

    # Fallback: greedy ordering (extra moves / captures first)
    root_moves = searcher.ordered_moves(me, opp)
    best_move = root_moves[0][1]

    depth = 1
    try:
        while depth <= 60:
            alpha = -1e9
            beta = 1e9
            cur_best = None
            cur_val = -1e9
            ordered = searcher.ordered_moves(me, opp, best_move)
            for _, i, nme, nopp, extra in ordered:
                if extra:
                    val = searcher.negamax(nme, nopp, depth, alpha, beta)
                else:
                    val = -searcher.negamax(nopp, nme, depth - 1, -beta, -alpha)
                if val > cur_val:
                    cur_val = val
                    cur_best = i
                if val > alpha:
                    alpha = val
            if cur_best is not None:
                best_move = cur_best
            if cur_val >= WIN_BONUS - 1 or cur_val <= -WIN_BONUS + 1:
                break
            if time.time() - start > TIME_BUDGET * 0.5:
                break
            depth += 1
    except Timeout:
        pass

    if best_move is None or me[best_move] <= 0:
        best_move = legal[0]
    return best_move
