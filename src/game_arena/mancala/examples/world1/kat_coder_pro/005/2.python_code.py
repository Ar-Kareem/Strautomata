
import numpy as np
from typing import List, Tuple

def simulate_move(you: np.ndarray, opponent: np.ndarray, move: int) -> Tuple[np.ndarray, np.ndarray, bool]:
    """Simulate a move and return the resulting board state and whether we get another turn.
    
    Args:
        you: Current state of your side (length 7 with store at index 6)
        opponent: Current state of opponent's side (length 7 with store at index 6)
        move: Index of house to sow from (0-5)
    
    Returns:
        Tuple of (new_you, new_opponent, extra_turn)
    """
    new_you = you.copy()
    new_opponent = opponent.copy()
    
    # Pick up seeds from selected house
    seeds = new_you[move]
    new_you[move] = 0
    
    # Sow seeds
    current_pos = move + 1
    extra_turn = False
    
    while seeds > 0:
        # Determine whose side we're on
        if current_pos <= 6:  # Your side (including store)
            new_you[current_pos] += 1
            if current_pos == 6 and seeds == 1:  # Last seed lands in store
                extra_turn = True
            current_pos += 1
        else:  # Opponent's side
            new_opponent[current_pos - 7] += 1
            current_pos += 1
            
        # Wrap around
        if current_pos > 13:
            current_pos = 0
            
        seeds -= 1
    
    # Check for capture
    if current_pos <= 6 and current_pos != 6:  # Last seed landed in your house (not store)
        house_idx = current_pos
        if new_you[house_idx] == 1:  # House was empty before landing
            opposite_idx = 5 - house_idx
            if new_opponent[opposite_idx] > 0:  # Opponent's opposite house has seeds
                # Capture
                new_you[6] += new_you[house_idx] + new_opponent[opposite_idx]
                new_you[house_idx] = 0
                new_opponent[opposite_idx] = 0
    
    return new_you, new_opponent, extra_turn

def game_over(you: np.ndarray, opponent: np.ndarray) -> bool:
    """Check if the game is over."""
    return sum(you[:6]) == 0 or sum(opponent[:6]) == 0

def final_score(you: np.ndarray, opponent: np.ndarray) -> int:
    """Calculate final score difference (you - opponent)."""
    final_you = you[6] + sum(you[:6])
    final_opponent = opponent[6] + sum(opponent[:6])
    return final_you - final_opponent

def evaluate_board(you: np.ndarray, opponent: np.ndarray) -> float:
    """Evaluate the board state."""
    # Base score difference
    score_diff = you[6] - opponent[6]
    
    # Add value for seeds in houses weighted by position
    # Seeds closer to store are more valuable
    house_value_you = sum(you[i] * (i + 1) / 6 for i in range(6))
    house_value_opp = sum(opponent[i] * (i + 1) / 6 for i in range(6))
    
    # Potential captures
    capture_bonus = 0
    for i in range(6):
        if you[i] == 1:  # Could capture if we land here
            if opponent[5-i] > 0:
                capture_bonus += opponent[5-i] + 1
    
    for i in range(6):
        if opponent[i] == 1:  # Opponent could capture if they land here
            if you[5-i] > 0:
                capture_bonus -= you[5-i] + 1
    
    # Extra move potential
    extra_move_bonus = 0
    for i in range(6):
        if you[i] > 0:
            # Calculate where last seed would land
            total_seeds = you[i]
            landing_pos = (i + total_seeds) % 14
            if landing_pos == 6:  # Would land in store
                extra_move_bonus += 5
                
    # Combine factors
    return score_diff * 2 + house_value_you - house_value_opp + capture_bonus + extra_move_bonus

def get_legal_moves(you: np.ndarray) -> List[int]:
    """Get list of legal moves."""
    return [i for i in range(6) if you[i] > 0]

def minimax(you: np.ndarray, opponent: np.ndarray, depth: int, alpha: float, beta: float, maximizing: bool) -> float:
    """Minimax with alpha-beta pruning."""
    if depth == 0 or game_over(you, opponent):
        if game_over(you, opponent):
            return final_score(you, opponent) * 100  # Strong weight for winning
        return evaluate_board(you, opponent)
    
    if maximizing:
        max_eval = float('-inf')
        legal_moves = get_legal_moves(you)
        
        # Sort moves to try captures and extra moves first
        legal_moves.sort(key=lambda m: (
            -you[m],  # Prefer moves with more seeds
            -1 if (you[m] + m) % 14 == 6 else 0,  # Prefer extra moves
        ))
        
        for move in legal_moves:
            new_you, new_opponent, extra_turn = simulate_move(you, opponent, move)
            
            if extra_turn:
                eval_score = minimax(new_you, new_opponent, depth, alpha, beta, True)
            else:
                eval_score = minimax(new_opponent, new_you, depth - 1, alpha, beta, False)
            
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            
            if beta <= alpha:
                break
                
        return max_eval
    else:
        min_eval = float('inf')
        legal_moves = get_legal_moves(you)
        
        for move in legal_moves:
            new_you, new_opponent, extra_turn = simulate_move(you, opponent, move)
            
            if extra_turn:
                eval_score = minimax(new_you, new_opponent, depth - 1, alpha, beta, False)
            else:
                eval_score = minimax(new_opponent, new_you, depth - 1, alpha, beta, True)
            
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            
            if beta <= alpha:
                break
                
        return min_eval

def policy(you: List[int], opponent: List[int]) -> int:
    """Main policy function."""
    you_np = np.array(you)
    opponent_np = np.array(opponent)
    
    # Get legal moves
    legal_moves = get_legal_moves(you_np)
    
    if len(legal_moves) == 1:
        return legal_moves[0]
    
    # Try depth 4 search first, then depth 6 if time permits
    best_move = legal_moves[0]
    best_score = float('-inf')
    
    for depth in [4, 6, 8]:
        current_best_move = best_move
        current_best_score = best_score
        
        for move in legal_moves:
            new_you, new_opponent, extra_turn = simulate_move(you_np, opponent_np, move)
            
            if extra_turn:
                score = minimax(new_you, new_opponent, depth, float('-inf'), float('inf'), True)
            else:
                score = minimax(new_opponent, new_you, depth - 1, float('-inf'), float('inf'), False)
            
            if score > current_best_score:
                current_best_score = score
                current_best_move = move
        
        best_move = current_best_move
        best_score = current_best_score
    
    return best_move
