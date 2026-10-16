
import math
from typing import List, Tuple, Set, Optional

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    """
    Go policy using minimax with alpha-beta pruning.
    
    Args:
        me: List of (row, col) tuples representing my stones
        opponent: List of (row, col) tuples representing opponent's stones
        
    Returns:
        tuple[int, int]: The next move as (row, col)
    """
    
    # Convert board to sets for faster lookups
    my_stones = set(me)
    opp_stones = set(opponent)
    
    # Initialize board representation
    board = {}
    for r, c in my_stones:
        board[(r, c)] = 'me'
    for r, c in opp_stones:
        board[(r, c)] = 'opp'
    
    # Get all valid moves (empty positions)
    valid_moves = []
    for r in range(1, 20):
        for c in range(1, 20):
            if (r, c) not in my_stones and (r, c) not in opp_stones:
                valid_moves.append((r, c))
    
    # If no valid moves, pass
    if not valid_moves:
        return (0, 0)
    
    # If only one valid move, take it
    if len(valid_moves) == 1:
        return valid_moves[0]
    
    # Use minimax to find best move
    best_move = None
    best_score = float('-inf')
    alpha = float('-inf')
    beta = float('inf')
    
    for move in valid_moves:
        # Make the move
        new_my_stones = my_stones.copy()
        new_my_stones.add(move)
        
        # Evaluate the resulting position
        score = -minimax_move(opp_stones, new_my_stones, False, 2, -beta, -alpha)
        
        # Update best move if this score is better
        if score > best_score:
            best_score = score
            best_move = move
        
        # Update alpha for alpha-beta pruning
        alpha = max(alpha, best_score)
        if alpha >= beta:
            break
    
    return best_move if best_move else (0, 0)

def minimax_move(opponent_stones: Set[Tuple[int, int]], 
                my_stones: Set[Tuple[int, int]], 
                is_maximizing: bool, 
                depth: int, 
                alpha: float, 
                beta: float) -> float:
    """
    Minimax algorithm with alpha-beta pruning for Go.
    """
    # Base case: reached max depth or game over
    if depth == 0:
        return evaluate_board(my_stones, opponent_stones)
    
    # Get current player's stones and opponent's stones
    if is_maximizing:
        current_player_stones = my_stones
        opponent_player_stones = opponent_stones
    else:
        current_player_stones = opponent_stones
        opponent_player_stones = my_stones
    
    # Generate valid moves
    valid_moves = []
    for r in range(1, 20):
        for c in range(1, 20):
            if (r, c) not in current_player_stones and (r, c) not in opponent_player_stones:
                valid_moves.append((r, c))
    
    # If no valid moves, pass
    if not valid_moves:
        return evaluate_board(my_stones, opponent_stones)
    
    # Minimax with alpha-beta pruning
    best_score = float('-inf') if is_maximizing else float('inf')
    
    for move in valid_moves:
        # Make the move
        new_current_player_stones = current_player_stones.copy()
        new_current_player_stones.add(move)
        
        # Recursively evaluate
        if is_maximizing:
            score = -minimax_move(opponent_player_stones, new_current_player_stones, False, depth - 1, -beta, -alpha)
            best_score = max(best_score, score)
            alpha = max(alpha, best_score)
        else:
            score = -minimax_move(opponent_player_stones, new_current_player_stones, True, depth - 1, -beta, -alpha)
            best_score = min(best_score, score)
            beta = min(beta, best_score)
        
        # Alpha-beta pruning
        if alpha >= beta:
            break
    
    return best_score

def evaluate_board(my_stones: Set[Tuple[int, int]], opponent_stones: Set[Tuple[int, int]]) -> float:
    """
    Heuristic evaluation function for a Go board position.
    """
    score = 0.0
    
    # Count liberties for each group
    my_liberties = count_liberties(my_stones, opponent_stones)
    opp_liberties = count_liberties(opponent_stones, my_stones)
    
    # Prioritize having more liberties
    score += my_liberties * 1.0
    score -= opp_liberties * 1.0
    
    # Count captured stones (simplified)
    score += len(my_stones) * 0.1
    score -= len(opponent_stones) * 0.1
    
    # Encourage center control
    center_score = 0
    for r, c in my_stones:
        center_score += 1.0 / (1.0 + abs(r - 10) + abs(c - 10))
    for r, c in opponent_stones:
        center_score -= 1.0 / (1.0 + abs(r - 10) + abs(c - 10))
    score += center_score
    
    return score

def count_liberties(stones: Set[Tuple[int, int]], opponent_stones: Set[Tuple[int, int]]) -> int:
    """
    Count liberties for a set of stones.
    """
    liberties = set()
    
    for r, c in stones:
        # Check adjacent positions
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 1 <= nr <= 19 and 1 <= nc <= 19:
                if (nr, nc) not in stones and (nr, nc) not in opponent_stones:
                    liberties.add((nr, nc))
    
    return len(liberties)
