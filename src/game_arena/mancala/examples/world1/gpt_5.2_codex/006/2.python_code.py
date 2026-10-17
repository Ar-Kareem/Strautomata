
import math
from functools import lru_cache

# Combined board indices:
# 0-5 : your houses
# 6   : your store
# 7-12: opponent houses
# 13  : opponent store (never sown into)

def _apply_move(you, opp, move):
    # build combined board
    b = list(you[:6]) + [you[6]] + list(opp[:6]) + [opp[6]]
    seeds = b[move]
    b[move] = 0
    idx = move
    while seeds > 0:
        idx = (idx + 1) % 14
        if idx == 13:  # skip opponent store
            idx = (idx + 1) % 14
        b[idx] += 1
        seeds -= 1

    extra = (idx == 6)

    # capture
    if 0 <= idx <= 5:
        # if last seed landed in empty house
        if b[idx] == 1:
            opp_idx = 12 - idx
            if b[opp_idx] > 0:
                b[6] += b[opp_idx] + 1
                b[idx] = 0
                b[opp_idx] = 0

    # split back
    you2 = b[0:6] + [b[6]]
    opp2 = b[7:13] + [b[13]]
    return you2, opp2, extra

def _is_terminal(you, opp):
    return sum(you[:6]) == 0 or sum(opp[:6]) == 0

def _final_score(you, opp):
    # move remaining seeds to stores
    ystore = you[6] + sum(you[:6])
    ostore = opp[6] + sum(opp[:6])
    return ystore - ostore

def _heuristic(you, opp):
    # simple evaluation: store diff + remaining seed diff
    return (you[6] - opp[6]) * 2 + (sum(you[:6]) - sum(opp[:6]))

@lru_cache(maxsize=200000)
def _negamax(you_t, opp_t, depth, alpha, beta):
    you = list(you_t)
    opp = list(opp_t)

    if _is_terminal(you, opp):
        return _final_score(you, opp)
    if depth == 0:
        return _heuristic(you, opp)

    best = -math.inf
    for m in range(6):
        if you[m] == 0:
            continue
        y2, o2, extra = _apply_move(you, opp, m)
        if extra:
            val = _negamax(tuple(y2), tuple(o2), depth - 1, alpha, beta)
        else:
            val = -_negamax(tuple(o2), tuple(y2), depth - 1, -beta, -alpha)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best

def policy(you, opponent) -> int:
    moves = [i for i in range(6) if you[i] > 0]
    if not moves:
        return 0  # should not happen per rules
    if len(moves) == 1:
        return moves[0]

    depth = 7  # tuned for strength/time balance
    best_move = moves[0]
    best_val = -math.inf
    alpha = -math.inf
    beta = math.inf

    for m in moves:
        y2, o2, extra = _apply_move(you, opponent, m)
        if extra:
            val = _negamax(tuple(y2), tuple(o2), depth - 1, alpha, beta)
        else:
            val = -_negamax(tuple(o2), tuple(y2), depth - 1, -beta, -alpha)
        if val > best_val:
            best_val = val
            best_move = m
        if val > alpha:
            alpha = val
    return best_move
