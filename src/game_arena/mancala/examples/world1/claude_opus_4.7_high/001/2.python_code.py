
import time

class _Timeout(Exception):
    pass

def _apply_move(me, opp, i):
    me = me[:]
    opp = opp[:]
    seeds = me[i]
    me[i] = 0
    p = i
    while seeds > 0:
        p = (p + 1) % 13
        if p <= 5:
            me[p] += 1
        elif p == 6:
            me[6] += 1
        else:
            opp[p - 7] += 1
        seeds -= 1
    extra = (p == 6)
    if not extra and p <= 5 and me[p] == 1 and opp[5 - p] > 0:
        me[6] += 1 + opp[5 - p]
        me[p] = 0
        opp[5 - p] = 0
    return me, opp, extra

def _negamax(me, opp, depth, alpha, beta, deadline):
    if time.time() > deadline:
        raise _Timeout()

    my_sum = me[0]+me[1]+me[2]+me[3]+me[4]+me[5]
    opp_sum = opp[0]+opp[1]+opp[2]+opp[3]+opp[4]+opp[5]

    if my_sum == 0:
        return me[6] - (opp[6] + opp_sum)
    if opp_sum == 0:
        return (me[6] + my_sum) - opp[6]

    if depth == 0:
        return me[6] - opp[6]

    best = -10**9
    for i in range(5, -1, -1):
        if me[i] > 0:
            new_me, new_opp, extra = _apply_move(me, opp, i)
            if extra:
                val = _negamax(new_me, new_opp, depth - 1, alpha, beta, deadline)
            else:
                val = -_negamax(new_opp, new_me, depth - 1, -beta, -alpha, deadline)
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
    return best

def policy(you, opponent):
    start = time.time()
    deadline = start + 0.85
    me = list(you)
    opp = list(opponent)

    legal = [i for i in range(6) if me[i] > 0]
    best_move = legal[0]

    # Quick check: if any move wins immediately (ends game favorably), take it
    for depth in range(2, 22):
        try:
            best_val = -10**9
            alpha = -10**9
            beta = 10**9
            current_best = legal[0]
            # Order: try last best move first, then high indices
            order = [best_move] + [i for i in range(5, -1, -1) if i != best_move]
            for i in order:
                if me[i] > 0:
                    new_me, new_opp, extra = _apply_move(me, opp, i)
                    if extra:
                        val = _negamax(new_me, new_opp, depth - 1, alpha, beta, deadline)
                    else:
                        val = -_negamax(new_opp, new_me, depth - 1, -beta, -alpha, deadline)
                    if val > best_val:
                        best_val = val
                        current_best = i
                        if val > alpha:
                            alpha = val
            best_move = current_best
            elapsed = time.time() - start
            if elapsed > 0.35:
                break
        except _Timeout:
            break

    if me[best_move] == 0:
        best_move = legal[0]
    return best_move
