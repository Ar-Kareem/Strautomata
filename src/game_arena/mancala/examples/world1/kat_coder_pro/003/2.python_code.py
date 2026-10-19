
import numpy as np
from typing import Tuple, List

def policy(you: List[int], opponent: List[int]) -> int:
    """
    Kalah game policy using minimax with alpha-beta pruning.
    
    Args:
        you: List of 7 integers representing your houses (0-5) and store (6)
        opponent: List of 7 integers representing opponent's houses (0-5) and store (6)
    
    Returns:
        Integer index (0-5) of the house to play
    """
    
    def make_move(current_you: List[int], current_opponent: List[int], move: int) -> Tuple[List[int], List[int], bool]:
        """
        Execute a move and return new board state and whether player gets extra turn.
        """
        # Copy board states
        new_you = current_you.copy()
        new_opponent = current_opponent.copy()
        
        # Get seeds from chosen house
        seeds = new_you[move]
        new_you[move] = 0
        
        # Distribute seeds counter-clockwise
        # Positions: 0,1,2,3,4,5 (houses) -> 6 (your store) -> 0,1,2,3,4,5 (opponent houses) -> repeat
        position = move + 1
        is_your_side = True
        last_position = None
        last_was_your_side = None
        
        for _ in range(seeds):
            if is_your_side:
                if position <= 6:
                    if position == 6:  # Your store
                        new_you[position] += 1
                        last_position = 6
                        last_was_your_side = True
                        # Don't increment position after reaching store
                    else:  # Your houses
                        new_you[position] += 1
                        last_position = position
                        last_was_your_side = True
                        position += 1
                else:
                    # Move to opponent's side
                    is_your_side = False
                    position = 0
            
            else:  # Opponent's side
                if position <= 5:
                    new_opponent[position] += 1
                    last_position = position
                    last_was_your_side = False
                    position += 1
                else:
                    # Move back to your side
                    is_your_side = True
                    position = 0
        
        # Check for capture
        extra_turn = False
        if last_was_your_side and last_position < 6:  # Last seed in your house
            if new_you[last_position] == 1:  # House was empty before drop
                opposite_house = 5 - last_position
                if new_opponent[opposite_house] > 0:
                    # Capture
                    captured = new_you[last_position] + new_opponent[opposite_house]
                    new_you[6] += captured
                    new_you[last_position] = 0
                    new_opponent[opposite_house] = 0
        
        # Check for extra turn
        if last_was_your_side and last_position == 6:
            extra_turn = True
        
        return new_you, new_opponent, extra_turn
    
    def is_game_over(you_houses: List[int], opp_houses: List[int]) -> bool:
        """Check if game is over (one player has no seeds in houses)."""
        return sum(you_houses[:6]) == 0 or sum(opp_houses[:6]) == 0
    
    def evaluate(you_state: List[int], opp_state: List[int]) -> int:
        """Evaluate board state. Positive favors player, negative favors opponent."""
        # Base score is difference in stores
        score = you_state[6] - opp_state[6]
        
        # Add value for seeds in your houses (potential)
        for i in range(6):
            if you_state[i] > 0:
                # Seeds closer to store are more valuable (can reach store in fewer moves)
                distance = 6 - i
                score += you_state[i] * (1 + (7 - distance) / 10)
        
        # Subtract value for opponent's seeds in houses
        for i in range(6):
            if opp_state[i] > 0:
                distance = 6 - i
                score -= opp_state[i] * (1 + (7 - distance) / 10)
        
        return score
    
    def get_legal_moves(state: List[int]) -> List[int]:
        """Get list of legal moves (indices of non-empty houses)."""
        return [i for i in range(6) if state[i] > 0]
    
    def minimax(you_state: List[int], opp_state: List[int], depth: int, alpha: float, beta: float, maximizing: bool) -> float:
        """Minimax algorithm with alpha-beta pruning."""
        if depth == 0 or is_game_over(you_state[:6], opp_state[:6]):
            return evaluate(you_state, opp_state)
        
        if maximizing:
            max_eval = float('-inf')
            legal_moves = get_legal_moves(you_state)
            
            for move in legal_moves:
                new_you, new_opp, extra_turn = make_move(you_state, opp_state, move)
                
                if extra_turn:
                    # Get another turn, so still maximizing
                    eval_score = minimax(new_you, new_opp, depth, alpha, beta, True)
                else:
                    # Opponent's turn
                    eval_score = minimax(new_opp, new_you, depth - 1, alpha, beta, False)
                
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            
            return max_eval
        else:
            min_eval = float('inf')
            legal_moves = get_legal_moves(opp_state)
            
            for move in legal_moves:
                new_opp, new_you, extra_turn = make_move(opp_state, you_state, move)
                
                if extra_turn:
                    # Opponent gets another turn
                    eval_score = minimax(new_you, new_opp, depth - 1, alpha, beta, False)
                else:
                    # Your turn
                    eval_score = minimax(new_you, new_opp, depth - 1, alpha, beta, True)
                
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            
            return min_eval
    
    # Main policy logic
    legal_moves = get_legal_moves(you)
    
    if len(legal_moves) == 1:
        return legal_moves[0]
    
    # Determine search depth based on game state
    # Early game: deeper search, late game: shallower but faster
    total_seeds = sum(you[:6]) + sum(opponent[:6])
    if total_seeds > 30:
        depth = 6
    elif total_seeds > 15:
        depth = 5
    else:
        depth = 4
    
    best_move = legal_moves[0]
    best_value = float('-inf')
    
    for move in legal_moves:
        new_you, new_opp, extra_turn = make_move(you, opponent, move)
        
        if extra_turn:
            # Get another turn
            value = minimax(new_you, new_opp, depth, float('-inf'), float('inf'), True)
        else:
            # Opponent's turn
            value = minimax(new_opp, new_you, depth - 1, float('-inf'), float('inf'), False)
        
        if value > best_value:
            best_value = value
            best_move = move
    
    return best_move
