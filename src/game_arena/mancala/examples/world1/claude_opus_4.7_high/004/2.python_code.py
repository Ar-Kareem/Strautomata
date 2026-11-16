
import time

def apply_move(my, opp, move):
    board = list(my) + list(opp)
    seeds = board[move]
    board[move] = 0
    idx = move
    while seeds > 0:
        idx = (idx + 1) % 14
        if idx == 13:
            continue
        board[idx] += 1
        seeds -= 1
    extra = False
    if idx == 6:
        extra = True
    elif idx < 6 and board[idx] == 1:
        opp_idx = 12 - idx
        if board[opp_idx] > 0:
            board[6] += board[opp_idx] + 1
            board[opp_idx] = 0
            board[idx] = 0
    return board[0:7], board[7:14], extra

def game_over(my, opp):
    return sum(my[0:6]) == 0 or sum(opp[0:6]) == 0

def final_eval(my, opp):
    return (my[6] + sum(my[0:6])) - (opp[6] + sum(opp[0:6]))

def search(my, opp, my_turn, depth, alpha, beta, deadline):
    if time.time() > deadline:
        raise TimeoutError()
    if game_over(my, opp):
        return final_eval(my, opp)
    if depth == 0:
        return my[6] - opp[6]
    if my_turn:
        best = -10**9
        legal = [i for i in range(6) if my[i] > 0]
        if not legal:
            return final_eval(my, opp)
        for move in legal:
            nm, no, extra = apply_move(my, opp, move)
            val = search(nm, no, extra, depth-1, alpha, beta, deadline)
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        return best
    else:
        best = 10**9
        legal = [i for i in range(6) if opp[i] > 0]
        if not legal:
            return final_eval(my, opp)
        for move in legal:
            no, nm, extra = apply_move(opp, my, move)
            val = search(nm, no, not extra, depth-1, alpha, beta, deadline)
            if val < best:
                best = val
            if best < beta:
                beta = best
            if alpha >= beta:
                break
        return best

def policy(you, opponent):
    start = time.time()
    deadline = start + 0.85
    legal = [i for i in range(6) if you[i] > 0]
    best_move = legal[0]
    for depth in range(2, 30):
        try:
            local_best_move = best_move
            local_best_val = -10**9
            alpha = -10**9
            beta = 10**9
            for move in legal:
                nm, no, extra = apply_move(you, opponent, move)
                if game_over(nm, no):
                    val = final_eval(nm, no)
                else:
                    val = search(nm, no, extra, depth-1, alpha, beta, deadline)
                if val > local_best_val:
                    local_best_val = val
                    local_best_move = move
                if val > alpha:
                    alpha = val
            best_move = local_best_move
        except TimeoutError:
            break
        if time.time() > deadline:
            break
    return best_move
