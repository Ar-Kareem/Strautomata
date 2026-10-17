
import math

INF = 10**9

def simulate_move(you, opponent, move):
    board = you[:6] + [you[6]] + opponent[:6]
    seeds = you[move]
    board[move] = 0
    i = move + 1
    last_index = None
    while seeds > 0:
        last_index = i
        if i in [0, 1, 2, 3, 4, 5] and seeds == 1 and board[i] == 0 and board[12 - i] > 0:
            captured = 1 + board[12 - i]
            board[12 - i] = 0
            board[6] += captured
            seeds = 0
        else:
            board[i] += 1
            seeds -= 1
        i = (i + 1) % 13
    new_you = board[:7]
    new_opponent = board[7:13] + [opponent[6]]
    extra_move = (last_index == 6)
    return new_you, new_opponent, extra_move

def terminal_score(you, opponent, is_maximizing):
    if is_maximizing:
        if all(x == 0 for x in you[:6]):
            return you[6]
        else:
            return you[6] + sum(opponent[:6])
    else:
        if all(x == 0 for x in you[:6]):
            return opponent[6] + sum(you[:6])
        else:
            return opponent[6]

def heuristic_score(you, opponent, is_maximizing):
    if is_maximizing:
        our_store = you[6]
        opponent_store = opponent[6]
        our_houses = sum(you[:6])
        opponent_houses = sum(opponent[:6])
    else:
        our_store = opponent[6]
        opponent_store = you[6]
        our_houses = sum(opponent[:6])
        opponent_houses = sum(you[:6])
    return (our_store - opponent_store) * 2 + (our_houses - opponent_houses)

def minimax(you, opponent, depth, alpha, beta, is_maximizing):
    if all(x == 0 for x in you[:6]) or all(x == 0 for x in opponent[:6]):
        return terminal_score(you, opponent, is_maximizing)
    if depth == 0:
        return heuristic_score(you, opponent, is_maximizing)
    
    moves = [i for i in range(6) if you[i] > 0]
    if not moves:
        return -INF if is_maximizing else INF
    
    if is_maximizing:
        best_value = -INF
        for move in moves:
            new_you, new_opponent, extra_move = simulate_move(you, opponent, move)
            next_flag = True if extra_move else False
            value = minimax(new_you, new_opponent, depth-1, alpha, beta, next_flag)
            best_value = max(best_value, value)
            alpha = max(alpha, best_value)
            if beta <= alpha:
                break
        return best_value
    else:
        best_value = INF
        for move in moves:
            new_you, new_opponent, extra_move = simulate_move(you, opponent, move)
            next_flag = True if extra_move else False
            value = minimax(new_you, new_opponent, depth-1, alpha, beta, next_flag)
            best_value = min(best_value, value)
            beta = min(beta, best_value)
            if beta <= alpha:
                break
        return best_value

def policy(you, opponent):
    depth = 3
    moves = [i for i in range(6) if you[i] > 0]
    if not moves:
        return 0
    if len(moves) == 1:
        return moves[0]
    best_move = moves[0]
    best_value = -INF
    for move in moves:
        new_you, new_opponent, extra_move = simulate_move(you, opponent, move)
        next_flag = True if extra_move else False
        value = minimax(new_you, new_opponent, depth-1, -INF, INF, next_flag)
        if value > best_value:
            best_value = value
            best_move = move
    return best_move
