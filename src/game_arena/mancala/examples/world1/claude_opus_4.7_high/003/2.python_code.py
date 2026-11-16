
import time

def _apply(me, opp, i):
    me = me[:]; opp = opp[:]
    seeds = me[i]
    me[i] = 0
    idx = i
    while seeds > 0:
        idx += 1
        if idx == 13:
            idx = 0
        if idx <= 5:
            me[idx] += 1
        elif idx == 6:
            me[6] += 1
        else:
            opp[idx - 7] += 1
        seeds -= 1
    extra = (idx == 6)
    if idx <= 5:
        if me[idx] == 1 and opp[5 - idx] > 0:
            me[6] += opp[5 - idx] + 1
            opp[5 - idx] = 0
            me[idx] = 0
    me_sum = me[0]+me[1]+me[2]+me[3]+me[4]+me[5]
    opp_sum = opp[0]+opp[1]+opp[2]+opp[3]+opp[4]+opp[5]
    over = False
    if me_sum == 0 or opp_sum == 0:
        me[6] += me_sum
        opp[6] += opp_sum
        for k in range(6):
            me[k] = 0
            opp[k] = 0
        over = True
    return me, opp, extra, over

_deadline = [0.0]

class _TO(Exception):
    pass

def _order(me):
    moves = []
    for i in range(6):
        if me[i] > 0:
            moves.append(i)
    moves.sort(key=lambda i: (0 if me[i] == 6 - i else 1, -i))
    return moves

def _nega(me, opp, depth, alpha, beta):
    if time.time() > _deadline[0]:
        raise _TO()
    if depth == 0:
        return me[6] - opp[6]
    moves = _order(me)
    if not moves:
        return me[6] - (opp[6] + opp[0]+opp[1]+opp[2]+opp[3]+opp[4]+opp[5])
    best = -10**9
    for i in moves:
        nm, no, extra, over = _apply(me, opp, i)
        if over:
            val = nm[6] - no[6]
        elif extra:
            val = _nega(nm, no, depth - 1, alpha, beta)
        else:
            val = -_nega(no, nm, depth - 1, -beta, -alpha)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best

def policy(you, opponent):
    start = time.time()
    _deadline[0] = start + 0.8
    me = list(you)
    opp = list(opponent)
    legal = [i for i in range(6) if me[i] > 0]
    best_move = legal[0]

    for depth in range(1, 40):
        try:
            cur_best = -10**9
            cur_move = legal[0]
            alpha = -10**9
            beta = 10**9
            ordered = _order(me)
            if best_move in ordered:
                ordered.remove(best_move)
                ordered.insert(0, best_move)
            for i in ordered:
                nm, no, extra, over = _apply(me, opp, i)
                if over:
                    val = nm[6] - no[6]
                elif extra:
                    val = _nega(nm, no, depth - 1, alpha, beta)
                else:
                    val = -_nega(no, nm, depth - 1, -beta, -alpha)
                if val > cur_best:
                    cur_best = val
                    cur_move = i
                if cur_best > alpha:
                    alpha = cur_best
            best_move = cur_move
            if time.time() > _deadline[0]:
                break
        except _TO:
            break

    if me[best_move] == 0:
        best_move = legal[0]
    return best_move
