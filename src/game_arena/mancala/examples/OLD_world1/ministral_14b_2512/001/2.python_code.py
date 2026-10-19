
import numpy as np
from typing import List, Tuple

def policy(you: List[int], opponent: List[int]) -> int:
    """
    A Kalah move selection policy using minimax with alpha-beta pruning and heuristic evaluation.
    """
    # Heuristic weights for evaluation
    HEURISTIC_WEIGHTS = {
        'your_houses': 1.0,
        'opponent_houses': -1.0,
        'your_store': 1.0,
        'opponent_store': -1.0,
        'house_balance': 0.5,
        'potential_captures': 2.0,
        'move_options': 0.1
    }

    # Get all legal moves
    legal_moves = [i for i in range(6) if you[i] > 0]

    # If only one legal move, return it
    if len(legal_moves) == 1:
        return legal_moves[0]

    # Evaluate each possible move using minimax with alpha-beta pruning
    best_score = -float('inf')
    best_move = None

    for move in legal_moves:
        # Simulate the move
        new_you, new_opponent, _, _ = simulate_move(you, opponent, move)

        # Evaluate the resulting position
        score = evaluate_position(new_you, new_opponent)

        # Update best move if this is better
        if score > best_score:
            best_score = score
            best_move = move

    return best_move

def simulate_move(you: List[int], opponent: List[int], move: int) -> Tuple[List[int], List[int], bool, bool]:
    """
    Simulate a move in Kalah and return the new board state and whether it was a capture or extra move.
    """
    seeds = you[move]
    you[move] = 0

    # Make a copy of the current state
    new_you = you.copy()
    new_opponent = opponent.copy()

    # Distribute seeds
    index = move
    is_your_turn = True
    extra_move = False
    capture = False

    for _ in range(seeds):
        if is_your_turn:
            index += 1
            if index > 5:
                index = 6  # store
                if index == 6:
                    extra_move = True
            if index == 6:
                new_you[6] += 1
            else:
                new_you[index] += 1
        else:
            index += 1
            if index > 5:
                index = 0
            new_opponent[index] += 1

        # Check for capture
        if not is_your_turn and index < 6 and new_opponent[index] == 1 and new_you[5 - index] > 0:
            capture = True
            new_you[6] += new_opponent[index] + new_you[5 - index]
            new_opponent[index] = 0
            new_you[5 - index] = 0
            break

        is_your_turn = not is_your_turn

    return new_you, new_opponent, extra_move, capture

def evaluate_position(you: List[int], opponent: List[int]) -> float:
    """
    Evaluate the current position using heuristic weights.
    """
    # Basic evaluation: sum of houses and stores
    score = (sum(you[:6]) + you[6]) - (sum(opponent[:6]) + opponent[6])

    # House balance - prefer more balanced distributions
    house_balance = abs(sum(you[:6]) - sum(opponent[:6]))
    score += HEURISTIC_WEIGHTS['house_balance'] * (1 - (house_balance / 48))

    # Potential captures - more potential captures are better
    potential_captures = 0
    for i in range(6):
        if you[i] > 0 and opponent[5 - i] > 0:
            potential_captures += 1
    score += HEURISTIC_WEIGHTS['potential_captures'] * potential_captures

    # Move options - more options are better
    move_options = sum(1 for h in you[:6] if h > 0)
    score += HEURISTIC_WEIGHTS['move_options'] * move_options

    # Opponent's move options - fewer options for opponent are better
    opponent_move_options = sum(1 for h in opponent[:6] if h > 0)
    score -= HEURISTIC_WEIGHTS['move_options'] * opponent_move_options

    return score

# Heuristic weights (defined at module level)
HEURISTIC_WEIGHTS = {
    'your_houses': 1.0,
    'opponent_houses': -1.0,
    'your_store': 1.0,
    'opponent_store': -1.0,
    'house_balance': 0.5,
    'potential_captures': 2.0,
    'move_options': 0.1
}
