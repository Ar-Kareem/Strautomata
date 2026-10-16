
import numpy as np
from collections import deque

def policy(you, opponent):
    # Simple heuristic-based policy with some minimax search
    # First try to capture opponent's seeds if possible
    for i in range(6):
        if you[i] > 0:
            # Simulate the move
            temp_you = you.copy()
            temp_opponent = opponent.copy()
            seeds = temp_you[i]
            temp_you[i] = 0

            # Distribute seeds
            pos = i
            while seeds > 0:
                pos = (pos + 1) % 14
                if pos == 6:  # your store
                    temp_you[6] += 1
                elif pos == 13:  # opponent's store (skip)
                    pass
                elif pos < 6:  # your houses
                    temp_you[pos] += 1
                else:  # opponent's houses
                    temp_opponent[pos - 7] += 1
                seeds -= 1

            # Check for capture
            last_pos = (i + seeds) % 14
            if last_pos < 6 and temp_you[last_pos] == 1 and temp_opponent[5 - last_pos] > 0:
                # Capture
                temp_you[6] += temp_you[last_pos] + temp_opponent[5 - last_pos]
                temp_you[last_pos] = 0
                temp_opponent[5 - last_pos] = 0

            # Evaluate this move
            move_score = evaluate_move(temp_you, temp_opponent)

            # If this is a good move, return it
            if move_score > 0.5:  # Threshold for good move
                return i

    # If no good capture moves, use minimax with alpha-beta pruning
    best_score = -float('inf')
    best_move = -1

    for i in range(6):
        if you[i] > 0:
            # Simulate the move
            temp_you = you.copy()
            temp_opponent = opponent.copy()
            seeds = temp_you[i]
            temp_you[i] = 0

            # Distribute seeds
            pos = i
            while seeds > 0:
                pos = (pos + 1) % 14
                if pos == 6:  # your store
                    temp_you[6] += 1
                elif pos == 13:  # opponent's store (skip)
                    pass
                elif pos < 6:  # your houses
                    temp_you[pos] += 1
                else:  # opponent's houses
                    temp_opponent[pos - 7] += 1
                seeds -= 1

            # Check for capture
            last_pos = (i + seeds) % 14
            if last_pos < 6 and temp_you[last_pos] == 1 and temp_opponent[5 - last_pos] > 0:
                # Capture
                temp_you[6] += temp_you[last_pos] + temp_opponent[5 - last_pos]
                temp_you[last_pos] = 0
                temp_opponent[5 - last_pos] = 0

            # Evaluate the position
            score = minimax(temp_opponent, temp_you, -float('inf'), float('inf'), 0, False)

            if score > best_score:
                best_score = score
                best_move = i

    return best_move

def evaluate_move(you, opponent):
    """Evaluate how good a move is for the current player"""
    # Simple heuristic: prefer moves that lead to captures or store advantage
    you_store = you[6]
    opponent_store = opponent[6]

    # Check for immediate captures
    for i in range(6):
        if you[i] == 1 and opponent[5 - i] > 0:
            return 1.0  # Perfect move

    # Prefer moves that give us more seeds in our store
    if you_store > opponent_store + 2:
        return 0.9

    # Prefer moves that leave opponent with fewer options
    opponent_options = sum(1 for h in opponent[:6] if h > 0)
    if opponent_options < 3:
        return 0.8

    # Prefer moves that give us more seeds in our houses
    if sum(you[:6]) > sum(opponent[:6]) + 2:
        return 0.7

    # Default to neutral evaluation
    return 0.5

def minimax(you, opponent, alpha, beta, depth, maximizing_player):
    """Minimax with alpha-beta pruning to evaluate positions"""
    if depth == 0 or game_over(you, opponent):
        return evaluate_position(you, opponent)

    if maximizing_player:
        max_eval = -float('inf')
        for i in range(6):
            if opponent[i] > 0:
                new_you, new_opponent = make_move(opponent, you, i)
                eval = minimax(new_you, new_opponent, alpha, beta, depth - 1, False)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
        return max_eval
    else:
        min_eval = float('inf')
        for i in range(6):
            if you[i] > 0:
                new_you, new_opponent = make_move(you, opponent, i)
                eval = minimax(new_you, new_opponent, alpha, beta, depth - 1, True)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
        return min_eval

def make_move(player, opponent, house_index):
    """Make a move and return the new board state"""
    new_player = player.copy()
    new_opponent = opponent.copy()
    seeds = new_player[house_index]
    new_player[house_index] = 0

    pos = house_index
    while seeds > 0:
        pos = (pos + 1) % 14
        if pos == 6:  # player's store
            new_player[6] += 1
        elif pos == 13:  # opponent's store (skip)
            pass
        elif pos < 6:  # player's houses
            new_player[pos] += 1
        else:  # opponent's houses
            new_opponent[pos - 7] += 1
        seeds -= 1

    # Check for capture
    last_pos = (house_index + seeds) % 14
    if last_pos < 6 and new_player[last_pos] == 1 and new_opponent[5 - last_pos] > 0:
        # Capture
        new_player[6] += new_player[last_pos] + new_opponent[5 - last_pos]
        new_player[last_pos] = 0
        new_opponent[5 - last_pos] = 0

    return new_player, new_opponent

def evaluate_position(you, opponent):
    """Evaluate the current position"""
    you_store = you[6]
    opponent_store = opponent[6]

    # Basic evaluation: store difference plus some positional factors
    base_score = you_store - opponent_store

    # Prefer positions where we have more seeds in our houses
    you_houses = sum(you[:6])
    opponent_houses = sum(opponent[:6])
    base_score += 0.1 * (you_houses - opponent_houses)

    # Prefer positions where opponent has fewer options
    opponent_options = sum(1 for h in opponent[:6] if h > 0)
    base_score += 0.2 * (6 - opponent_options)

    # Prefer positions where we have more potential captures
    capture_potential = 0
    for i in range(6):
        if you[i] == 1 and opponent[5 - i] > 0:
            capture_potential += 1
    base_score += 0.5 * capture_potential

    return base_score

def game_over(you, opponent):
    """Check if the game is over"""
    return sum(you[:6]) == 0 or sum(opponent[:6]) == 0
