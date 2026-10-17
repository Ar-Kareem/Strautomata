
import numpy as np

def simulate_move(you, opponent, move):
    """Apply move and return (new_you, new_opp, extra_move, capture)"""
    you = list(you)
    opponent = list(opponent)
    hand = you[move]
    you[move] = 0
    side = 0  # 0: you, 1: opponent
    pos = move + 1
    extra_move = False
    capture = False

    while hand > 0:
        if side == 0 and pos == 6:  # your store
            you[pos] += 1
            hand -= 1
            if hand == 0:
                extra_move = True
                break
            side = 1
            pos = 0
        elif side == 0 and pos < 6:
            you[pos] += 1
            hand -= 1
            if hand == 0:
                break
            pos += 1
        elif side == 1 and pos < 6:
            opponent[pos] += 1
            hand -= 1
            if hand == 0:
                break
            pos += 1
            if pos == 6:
                side = 0
                pos = 0
        else:
            side = 0
            pos = 0

    # Check capture
    if side == 0 and 0 <= pos <= 5 and you[pos] == 1:
        opp_pos = 5 - pos
        if opponent[opp_pos] > 0:
            capture = True
            you[6] += you[pos] + opponent[opp_pos]
            you[pos] = 0
            opponent[opp_pos] = 0

    return you, opponent, extra_move, capture

def evaluate(you, opponent):
    """Heuristic evaluation: positive favors you"""
    score = you[6] - opponent[6]
    my_seeds = sum(you[0:6])
    opp_seeds = sum(opponent[0:6])
    score += (my_seeds - opp_seeds) * 0.1
    return score

def minimax(you, opponent, depth, alpha, beta, maximizing):
    if depth == 0 or (sum(you[:6]) == 0 or sum(opponent[:6]) == 0):
        return evaluate(you, opponent)
    
    moves = [i for i in range(6) if you[i] > 0]
    if maximizing:
        max_eval = -np.inf
        # Bonus for extra move moves
        moves.sort(key=lambda i: simulate_move(you, opponent, i)[2], reverse=True)
        for move in moves:
            new_you, new_opp, extra, _ = simulate_move(you, opponent, move)
            if extra:
                eval_score = minimax(new_you, new_opp, depth, alpha, beta, True)
            else:
                eval_score = minimax(new_you, new_opp, depth - 1, alpha, beta, False)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, max_eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = np.inf
        opp_moves = [i for i in range(6) if opponent[i] > 0]
        for move in opp_moves:
            new_opp, new_you, extra, _ = simulate_move(opponent, you, move)
            if extra:
                eval_score = minimax(new_you, new_opp, depth, alpha, beta, False)
            else:
                eval_score = minimax(new_you, new_opp, depth - 1, alpha, beta, True)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, min_eval)
            if beta <= alpha:
                break
        return min_eval

def policy(you: list[int], opponent: list[int]) -> int:
    # List legal moves
    moves = [i for i in range(6) if you[i] > 0]
    if not moves:
        return 0  # should not happen
    
    # Try depth 4 first, go deeper if time allows
    best_move = moves[0]
    best_score = -np.inf
    depth = 6
    
    for move in moves:
        new_you, new_opp, extra, _ = simulate_move(you, opponent, move)
        if extra:
            score = minimax(new_you, new_opp, depth, -np.inf, np.inf, True)
        else:
            score = minimax(new_you, new_opp, depth - 1, -np.inf, np.inf, False)
        if score > best_score:
            best_score = score
            best_move = move
    return best_move
