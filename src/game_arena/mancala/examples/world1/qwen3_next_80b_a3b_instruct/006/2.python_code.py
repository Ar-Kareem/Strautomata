
import numpy as np
from typing import List, Tuple

def policy(you: List[int], opponent: List[int]) -> int:
    # Convert to numpy arrays for easier manipulation
    you_arr = np.array(you, dtype=int)
    opponent_arr = np.array(opponent, dtype=int)
    
    # Find all legal moves
    legal_moves = [i for i in range(6) if you_arr[i] > 0]
    
    if len(legal_moves) == 1:
        return legal_moves[0]
    
    # Use minimax with alpha-beta pruning
    best_move = legal_moves[0]
    best_score = float('-inf')
    alpha = float('-inf')
    beta = float('inf')
    
    # Try moves in order of heuristic priority
    # Prioritize captures, then store landings, then other moves
    move_scores = []
    for move in legal_moves:
        score = heuristic_score(you_arr, opponent_arr, move)
        move_scores.append((score, move))
    
    # Sort by heuristic score (descending)
    move_scores.sort(reverse=True)
    ordered_moves = [move for _, move in move_scores]
    
    # Minimax search with depth limit (adjust depth based on game state)
    depth = 4
    for move in ordered_moves:
        # Simulate the move
        new_you, new_opponent, extra_move = simulate_move(you_arr.copy(), opponent_arr.copy(), move)
        
        # Calculate score for this move
        score = minimax(new_you, new_opponent, depth - 1, alpha, beta, False, extra_move)
        
        if score > best_score:
            best_score = score
            best_move = move
            
        alpha = max(alpha, best_score)
        if beta <= alpha:
            break  # Alpha-beta pruning
    
    return best_move

def simulate_move(you: np.ndarray, opponent: np.ndarray, move: int) -> Tuple[np.ndarray, np.ndarray, bool]:
    """
    Simulate a move and return new state and whether extra move is granted
    """
    seeds = you[move]
    you[move] = 0
    current_pos = move
    
    # Distribute seeds
    while seeds > 0:
        # Move to next position
        current_pos += 1
        
        # Skip opponent's store
        if current_pos == 6:  # You're at your store
            you[6] += 1
            seeds -= 1
            if seeds == 0:
                break
            current_pos = 0
        elif current_pos == 7:  # Moving to opponent's side
            current_pos = 0
            # Add to opponent's house
            opponent[current_pos] += 1
            seeds -= 1
            if seeds == 0:
                break
            current_pos += 1
        elif current_pos <= 5:  # You're still on your side
            you[current_pos] += 1
            seeds -= 1
            if seeds == 0:
                break
        elif current_pos == 6:  # Opponent's store - skip
            current_pos = 0
        else:  # Opponent's side
            house_index = (current_pos - 7) % 6
            if house_index < 0:
                house_index += 6
            opponent[house_index] += 1
            seeds -= 1
            if seeds == 0:
                break
            current_pos += 1
    
    # Check for capture
    if current_pos >= 7 and current_pos <= 12:  # Last seed landed in opponent's side
        opp_index = (current_pos - 7) % 6
        if you[opp_index] == 0:  # Your house is empty
            # Check opponent's opposite house
            opp_opposite = 5 - opp_index
            if opponent[opp_opposite] > 0:
                # Capture!
                captured = opponent[opp_opposite]
                you[6] += captured + 1  # +1 for the seed we just dropped
                opponent[opp_opposite] = 0
    
    # Check if last seed landed in your store
    extra_move = False
    if current_pos == 6:
        extra_move = True
    
    return you, opponent, extra_move

def minimax(you: np.ndarray, opponent: np.ndarray, depth: int, alpha: float, beta: float, 
            maximizing_player: bool, extra_move: bool) -> float:
    """
    Minimax algorithm with alpha-beta pruning
    """
    # Base case: depth limit reached or game over
    if depth == 0:
        return evaluate_board(you, opponent)
    
    # Check if game is over (no seeds left in any house)
    if sum(you[:6]) == 0:
        return evaluate_board(you, opponent)
    if sum(opponent[:6]) == 0:
        return evaluate_board(you, opponent)
    
    if maximizing_player:
        # Your turn
        legal_moves = [i for i in range(6) if you[i] > 0]
        if not legal_moves:
            return evaluate_board(you, opponent)
        
        # Sort moves to improve pruning
        move_scores = []
        for move in legal_moves:
            score = heuristic_score(you, opponent, move)
            move_scores.append((score, move))
        move_scores.sort(reverse=True)
        ordered_moves = [move for _, move in move_scores]
        
        max_eval = float('-inf')
        for move in ordered_moves:
            new_you, new_opponent, new_extra_move = simulate_move(you.copy(), opponent.copy(), move)
            
            # If extra move, you get another turn (maximizing player again)
            if new_extra_move:
                eval_score = minimax(new_you, new_opponent, depth, alpha, beta, True, new_extra_move)
            else:
                eval_score = minimax(new_you, new_opponent, depth - 1, alpha, beta, False, new_extra_move)
            
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, max_eval)
            if beta <= alpha:
                break
                
        return max_eval
    else:
        # Opponent's turn
        legal_moves = [i for i in range(6) if opponent[i] > 0]
        if not legal_moves:
            return evaluate_board(you, opponent)
        
        # Sort moves to improve pruning
        move_scores = []
        for move in legal_moves:
            # Heuristic for opponent is from your perspective
            opponent_score = heuristic_score(opponent, you, move)
            # We want to minimize opponent's advantage, so invert the score
            move_scores.append((-opponent_score, move))
        move_scores.sort(reverse=True)  # Sort by highest negated score
        ordered_moves = [move for _, move in move_scores]
        
        min_eval = float('inf')
        for move in ordered_moves:
            new_opponent, new_you, new_extra_move = simulate_move(opponent.copy(), you.copy(), move)
            # Swap back to correct orientation
            new_you, new_opponent = new_you, new_opponent
            
            # If extra move, opponent gets another turn (minimizing player again)
            if new_extra_move:
                eval_score = minimax(new_you, new_opponent, depth, alpha, beta, False, new_extra_move)
            else:
                eval_score = minimax(new_you, new_opponent, depth - 1, alpha, beta, True, new_extra_move)
            
            min_eval = min(min_eval, eval_score)
            beta = min(beta, min_eval)
            if beta <= alpha:
                break
                
        return min_eval

def heuristic_score(you: np.ndarray, opponent: np.ndarray, move: int) -> float:
    """
    Heuristic to score a move before simulation
    """
    score = 0.0
    
    # We'll simulate just the immediate effect
    seeds = you[move]
    you_copy = you.copy()
    opponent_copy = opponent.copy()
    
    # Simple simulation for immediate effects
    you_copy[move] = 0
    current_pos = move
    
    while seeds > 0:
        current_pos += 1
        
        if current_pos == 6:
            # Your store
            you_copy[6] += 1
            seeds -= 1
            if seeds == 0:
                score += 20  # Extra move bonus
                break
            current_pos = 0
        elif current_pos == 7:
            # Opponent's side
            current_pos = 0
            opponent_copy[current_pos] += 1
            seeds -= 1
            if seeds == 0:
                # Check for capture
                opp_index = current_pos
                if you_copy[opp_index] == 0 and opponent_copy[5 - opp_index] > 0:
                    score += 15  # Capture bonus
                break
            current_pos = 1
        elif current_pos <= 5:  # Your side
            you_copy[current_pos] += 1
            seeds -= 1
            if seeds == 0:
                # Check for capture
                if you_copy[current_pos] == 1:  # Was empty before
                    opp_index = 5 - current_pos
                    if opponent_copy[opp_index] > 0:
                        score += 15  # Capture bonus
                break
        else:  # Opponent's side
            opp_index = (current_pos - 7) % 6
            opponent_copy[opp_index] += 1
            seeds -= 1
            if seeds == 0:
                break
    
    # Consider the difference in seeds
    score += (you[6] - opponent[6]) * 2  # Current score differential
    score += (sum(you[:6]) - sum(opponent[:6])) * 0.5  # House seed advantage
    score += you[6] * 0.2  # Your store seeds
    
    return score

def evaluate_board(you: np.ndarray, opponent: np.ndarray) -> float:
    """
    Evaluate the board state for minimax
    """
    # Basic evaluation: store difference
    score_diff = you[6] - opponent[6]
    
    # Additional factors
    # Seeds in houses (encourage keeping seeds active)
    your_houses = sum(you[:6])
    opponent_houses = sum(opponent[:6])
    
    # Heuristic weights
    # Capture potential: seeds in opponent's side that can be captured
    capture_potential = 0
    for i in range(6):
        if you[i] == 0 and opponent[5-i] > 0:
            capture_potential += opponent[5-i]
    
    # Dimensional scaling
    score = score_diff * 10 + (your_houses - opponent_houses) * 1.5 + capture_potential * 2
    
    # Favor having more seeds overall
    score += your_houses * 0.5
    
    return score
