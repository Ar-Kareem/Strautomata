
import numpy as np
from typing import List, Tuple, Dict

def policy(you: List[int], opponent: List[int]) -> int:
    """
    Implements a minimax algorithm with alpha-beta pruning and heuristic evaluation
    for the Kalah game with 6 houses per side.
    """
    # Convert to numpy arrays for easier manipulation
    you_arr = np.array(you, dtype=int)
    opponent_arr = np.array(opponent, dtype=int)
    
    # Use minimax with alpha-beta pruning
    best_move = None
    best_value = float('-inf')
    alpha = float('-inf')
    beta = float('inf')
    transposition_table = {}  # Memoization for board states
    
    # Try each valid move (houses with seeds)
    for move in range(6):
        if you_arr[move] == 0:
            continue
            
        # Make the move
        new_you, new_opponent, extra_move = make_move(you_arr.copy(), opponent_arr.copy(), move)
        
        # Evaluate this move
        if extra_move:
            # If extra move, evaluate recursively with same player
            value = minimax(new_you, new_opponent, alpha, beta, depth=4, maximizing_player=True, transposition_table=transposition_table)
        else:
            # Opponent's turn
            value = minimax(new_opponent, new_you, alpha, beta, depth=3, maximizing_player=False, transposition_table=transposition_table)
            # Invert value since it's from opponent's perspective
            value = -value
            
        if value > best_value:
            best_value = value
            best_move = move
            
        alpha = max(alpha, best_value)
        if beta <= alpha:
            break  # Alpha-beta pruning
            
    # If no move found (shouldn't happen due to problem constraints), return first valid move
    if best_move is None:
        for i in range(6):
            if you[i] > 0:
                return i
        return 0  # fallback (should never reach here)
    
    return best_move


def make_move(you: np.ndarray, opponent: np.ndarray, move: int) -> Tuple[np.ndarray, np.ndarray, bool]:
    """
    Makes a move from house 'move' and returns new state and whether extra move is earned.
    Also handles capture rule.
    Returns: (new_you, new_opponent, extra_move)
    """
    # Remove seeds from the chosen house
    seeds = you[move]
    you[move] = 0
    
    current_player = you.copy()
    current_opponent = opponent.copy()
    
    # Sow seeds
    current_pos = move + 1  # start from next house
    while seeds > 0:
        # Sow in current player's houses
        while seeds > 0 and current_pos < 6:
            current_player[current_pos] += 1
            seeds -= 1
            current_pos += 1
            
        # If seeds left and we have not finished all houses
        if seeds > 0:
            # Sow in current player's store
            current_player[6] += 1
            seeds -= 1
            if seeds == 0:
                # Last seed went in store -> extra move
                return current_player, current_opponent, True
            
            # Now switch to opponent's side
            current_pos = 0
            
            # Sow in opponent's houses
            while seeds > 0 and current_pos < 6:
                current_opponent[current_pos] += 1
                seeds -= 1
                current_pos += 1
                
            # If still seeds left, switch back to current player's houses
            if seeds > 0:
                current_pos = 0
    
    # Check for capture: last seed landed in your house (0-5) and it was empty before, 
    # and opponent's opposite house has seeds
    # We need to check where the last seed landed
    # The way we sow means the last seed went to position (current_pos - 1) on current player's side
    # But we need to determine the exact position
    
    # Reconstruct: after planting, current_pos points to the next position after last seed
    # So last seed went to position (current_pos - 1) on the current player's side
    # But we need to be careful about the path
    
    # Way to calculate last position:
    # We started at move + 1, and went through: 
    # [move+1, move+2, ..., 5, store, opponent[0..5], you[0..5], ...]
    # We need to track where we placed the last seed
    
    # Let's recalculate the last position more carefully
    seeds_to_sow = you[move]  # original number of seeds
    if seeds_to_sow == 0:
        return current_player, current_opponent, False
    
    # Calculate the exact last position where seed landed
    pos = move + 1
    remaining = seeds_to_sow
    last_position = -1
    last_side = 0  # 0 for you, 1 for opponent
    
    # Pass 1: sow in your houses from move+1 to end
    if remaining > 0:
        houses_left = 6 - (move + 1)  # houses from move+1 to 5
        if remaining <= houses_left:
            # Last seed lands in your houses
            last_position = move + remaining
            last_side = 0
            remaining = 0
        else:
            # Sow all remaining houses on your side
            remaining -= houses_left
            # Sow in your store
            if remaining > 0:
                remaining -= 1  # seed goes to your store
                if remaining == 0:
                    # Extra move
                    return current_player, current_opponent, True
                # Now switch to opponent's side
                last_side = 1
                if remaining <= 6:
                    last_position = remaining - 1
                    remaining = 0
                else:
                    # Sow all opponent's houses
                    remaining -= 6
                    # Now back to your side
                    last_side = 0
                    last_position = (remaining - 1) % 6
                    remaining = 0
    
    # If we got here without returning, we need to check for capture
    # The last seed landed in last_position on last_side (0=you, 1=opponent)
    # But since the last seed must land on our side (you side) for capture, we need last_side == 0
    if last_side == 0:  # last seed landed on your house (0-5)
        if current_player[last_position] == 1:  # was empty before, now has 1 seed
            # Check opponent's opposite house
            opp_pos = 5 - last_position
            if current_opponent[opp_pos] > 0:
                # Capture
                captured = 1 + current_opponent[opp_pos]  # your seed + opponent's seeds
                current_player[6] += captured
                current_opponent[opp_pos] = 0
                current_player[last_position] = 0
                
    return current_player, current_opponent, False


def minimax(you: np.ndarray, opponent: np.ndarray, alpha: float, beta: float, depth: int, maximizing_player: bool, transposition_table: Dict) -> float:
    """
    Minimax algorithm with alpha-beta pruning and transposition table.
    Note: 'you' is always the player to move from the perspective of the current state.
    """
    # Check for terminal state: if all houses in current player's side are empty
    if np.sum(you[:6]) == 0:
        # Game ends, opponent gathers all remaining seeds
        final_score = you[6] + np.sum(opponent[:6]) - opponent[6]
        return final_score if maximizing_player else -final_score
    
    # Check for depth limit
    if depth <= 0:
        return evaluate_board(you, opponent, maximizing_player)
    
    # Create state key for transposition table
    state_key = (tuple(you), tuple(opponent))
    if state_key in transposition_table:
        return transposition_table[state_key]
    
    best_value = float('-inf') if maximizing_player else float('inf')
    
    # Get available moves
    available_moves = []
    for i in range(6):
        if you[i] > 0:
            available_moves.append(i)
    
    if len(available_moves) == 0:
        # Shouldn't happen per problem constraints, but handle safely
        final_score = you[6] + np.sum(opponent[:6]) - opponent[6]
        value = final_score if maximizing_player else -final_score
        transposition_table[state_key] = value
        return value
    
    # Try each move
    for move in available_moves:
        # Make the move
        new_you, new_opponent, extra_move = make_move(you.copy(), opponent.copy(), move)
        
        if extra_move:
            # Get another move - same player continues
            value = minimax(new_you, new_opponent, alpha, beta, depth, maximizing_player, transposition_table)
        else:
            # Opponent's turn
            value = minimax(new_opponent, new_you, alpha, beta, depth - 1, not maximizing_player, transposition_table)
            if maximizing_player:
                value = -value
            else:
                value = -value
                
        if maximizing_player:
            best_value = max(best_value, value)
            alpha = max(alpha, best_value)
        else:
            best_value = min(best_value, value)
            beta = min(beta, best_value)
            
        if beta <= alpha:
            break  # Alpha-beta pruning
    
    transposition_table[state_key] = best_value
    return best_value


def evaluate_board(you: np.ndarray, opponent: np.ndarray, maximizing_player: bool) -> float:
    """
    Heuristic evaluation function for the board state.
    Returns a score favoring the maximizing player.
    """
    # Primary factor: difference in stores
    store_diff = you[6] - opponent[6]
    
    # Secondary factors: seeds in houses
    your_houses_sum = np.sum(you[:6])
    opponent_houses_sum = np.sum(opponent[:6])
    
    # Additional factors
    # 1. Number of possible captures (empty houses on your side with non-zero opponent opposite)
    capture_potential = 0
    for i in range(6):
        if you[i] == 0 and opponent[5-i] > 0:
            capture_potential += opponent[5-i]
    
    # 2. Number of empty holes on opponent's side (pressures opponent)
    opponent_empty_holes = sum(1 for i in range(6) if opponent[i] == 0)
    
    # 3. Distribution preference: early holes better for creating captures
    # Give bonus for seeds in holes 1-3 (closer to store)
    your_bonus = 0
    for i in range(3):
        your_bonus += you[i] * (3 - i)  # more weight to holes closer to store
    
    # Combine all factors with weights
    # Main weight on store difference, then supporting factors
    score = (
        store_diff * 10.0 +             # Most important
        (your_houses_sum - opponent_houses_sum) * 1.5 +  # Board presence
        capture_potential * 2.0 +       # Capture opportunities
        opponent_empty_holes * 0.5 +    # Opponent is pressured
        your_bonus * 0.3                # Favor lower-numbered holes
    )
    
    # Return negative if we are minimizing player
    return score if maximizing_player else -score
