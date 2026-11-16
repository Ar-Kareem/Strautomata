
import sys
from copy import deepcopy

def simulate_move(you, opponent, move):
    new_you = deepcopy(you)
    new_opponent = deepcopy(opponent)
    seeds = new_you[move]
    if seeds == 0:
        return new_you, new_opponent, False
    new_you[move] = 0
    current_pos = move + 1
    last_pos = None
    for _ in range(seeds):
        if current_pos >= 13:
            current_pos = 0
        pos = current_pos % 13
        if pos < 6:
            new_you[pos] += 1
        elif pos == 6:
            new_you[pos] += 1
        else:
            opp_house = pos - 7
            new_opponent[opp_house] += 1
        last_pos = pos
        current_pos += 1
    capture_occurred = False
    if 0 <= last_pos <= 5:
        if new_you[last_pos] == 1 and new_opponent[5 - last_pos] > 0:
            capture = new_you[last_pos] + new_opponent[5 - last_pos]
            new_you[6] += capture
            new_opponent[5 - last_pos] = 0
            new_you[last_pos] = 0
            capture_occurred = True
    has_next_move = (last_pos == 6)
    return new_you, new_opponent, has_next_move

def evaluate_state(you, opponent):
    you_houses = new_you[:6]
    you_store = new_you[6]
    opp_houses = new_opponent[:6]
    opp_store = new_opponent[6]
    return (you_store - opp_store) + (sum(you_houses) - sum(opp_houses)) * 1.5

def evaluate(you, opponent):
    return evaluate_state(you, opponent)

def minimax(you, opponent, depth, maximizing, alpha, beta):
    if depth == 0 or sum(you[:6]) == 0:
        return evaluate(you, opponent), None
    if maximizing:
        best_score = -float('inf')
        best_move = None
        possible_moves = [i for i in range(6) if you[i] > 0]
        for move in possible_moves:
            new_you, new_opponent, can_continue = simulate_move(you, opponent, move)
            score, _ = minimax(new_you, new_opponent, depth - 1, False, alpha, beta)
            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, best_score)
            if beta <= alpha:
                break
        return best_score, best_move
    else:
        best_score = float('inf')
        best_move = None
        possible_moves = [i for i in range(6) if opponent[i] > 0]
        for move in possible_moves:
            new_opponent = deepcopy(opponent)
            new_you_state = deepcopy(you)
            opp_pot = new_opponent[move]
            new_opponent[move] = 0
            current_pos = move + 1
            for _ in range(opp_pot):
                pos = current_pos % 13
                current_pos += 1
                if pos < 6:
                    new_you_state[pos] += 1
                elif pos == 6:
                    new_you_state[pos] += 1
                else:
                    opp_house = pos - 7
                    new_you_state[opp_house] += 1
            capture = False
            if 0 <= last_pos <= 5:
                if new_opponent[last_pos] == 1 and new_you_state[5 - last_pos] > 0:
                    capture = new_opponent[last_pos] + new_you_state[5 - last_pos]
                    new_opponent[6] += capture
                    new_you_state[5 - last_pos] = 0
                    new_opponent[last_pos] = 0
            return minimax(new_you_state, new_opponent, depth - 1, True, alpha, beta)
            # This part is a placeholder and needs proper handling. Simplified for example.

def policy(you, opponent):
    possible_moves = [i for i in range(6) if you[i] > 0]
    if not possible_moves:
        return -1
    best_move = possible_moves[0]
    max_eval = -float('inf')
    for i in possible_moves:
        new_you, new_opponent, _ = simulate_move(you, opponent, i)
        current_eval = evaluate(new_you, new_opponent)
        if current_eval > max_eval:
            max_eval = current_eval
            best_move = i
    return best_move
