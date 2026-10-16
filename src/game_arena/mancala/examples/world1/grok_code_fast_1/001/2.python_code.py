
import numpy as np
from typing import List, Tuple

def policy(you: List[int], opponent: List[int]) -> int:
    """
    Returns the best legal move using minimax with alpha-beta pruning.
    """
    def is_terminal(state_you: List[int], state_opponent: List[int]) -> bool:
        return sum(state_you[:6]) == 0 or sum(state_opponent[:6]) == 0

    def evaluate(state_you: List[int], state_opponent: List[int]) -> float:
        if is_terminal(state_you, state_opponent):
            if sum(state_you[:6]) == 0:
                # Move any remaining seeds to opponent's store
                state_opponent[6] += sum(state_opponent[:6])
            if sum(state_opponent[:6]) == 0:
                # Move any remaining seeds to your store
                state_you[6] += sum(state_you[:6])
            return state_you[6] - state_opponent[6]
        
        # Heuristic: store difference + seed difference + mobility
        seed_diff = sum(state_you[:6]) - sum(state_opponent[:6])
        mobility = len([h for h in state_you[:6] if h > 0]) - len([h for h in state_opponent[:6] if h > 0])
        return state_you[6] - state_opponent[6] + 0.5 * seed_diff + 0.1 * mobility

    def simulate_move(state_you: List[int], state_opponent: List[int], move: int) -> Tuple[List[int], List[int], bool]:
        """Returns (new_you, new_opponent, extra_turn)"""
        new_you = state_you.copy()
        new_opponent = state_opponent.copy()
        seeds = new_you[move]
        new_you[move] = 0
        pos = move
        extra_turn = False
        
        while seeds > 0:
            pos = (pos + 1) % 14
            if pos == 6:  # Skip opponent's store
                continue
            if pos < 7:
                new_you[pos] += 1
            else:
                new_opponent[pos - 7] += 1
            seeds -= 1
        
        last_pos = pos
        if last_pos <= 6 and last_pos <= 5 and new_you[last_pos] == 1 and new_opponent[5 - last_pos] > 0:
            # Capture: last seed in empty you house, capture opposite
            new_you[6] += 1 + new_opponent[5 - last_pos]
            new_you[last_pos] = 0
            new_opponent[5 - last_pos] = 0
        
        if last_pos == 6:
            extra_turn = True
        
        return new_you, new_opponent, extra_turn

    def minimax(state_you: List[int], state_opponent: List[int], depth: int, maximizing: bool, alpha: float, beta: float) -> float:
        if depth == 0 or is_terminal(state_you, state_opponent):
            return evaluate(state_you, state_opponent)
        
        if maximizing:
            max_eval = float('-inf')
            for move in range(6):
                if state_you[move] == 0:
                    continue
                new_you, new_opponent, extra_turn = simulate_move(state_you, state_opponent, move)
                if extra_turn:
                    eval = minimax(new_you, new_opponent, depth, True, alpha, beta)
                else:
                    eval = minimax(new_opponent, new_you, depth - 1, False, alpha, beta)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in range(6):
                if state_opponent[move] == 0:
                    continue
                new_opponent, new_you, extra_turn = simulate_move(state_opponent, state_you, move)
                if extra_turn:
                    eval = minimax(new_you, new_opponent, depth, False, alpha, beta)
                else:
                    eval = minimax(new_opponent, new_you, depth - 1, True, alpha, beta)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval

    # Find all legal moves
    legal_moves = [i for i in range(6) if you[i] > 0]
    
    if not legal_moves:
        raise ValueError("No legal moves, but policy should not be called in such case.")
    
    # Default to first legal if only one
    if len(legal_moves) == 1:
        return legal_moves[0]
    
    # Evaluate each legal move
    best_move = legal_moves[0]
    best_value = float('-inf')
    for move in legal_moves:
        new_you, new_opponent, extra_turn = simulate_move(you, opponent, move)
        if extra_turn:
            value = minimax(new_you, new_opponent, 6, True, float('-inf'), float('inf'))
        else:
            value = minimax(new_opponent, new_you, 5, False, float('-inf'), float('inf'))
        if value > best_value:
            best_value = value
            best_move = move
    
    return best_move
