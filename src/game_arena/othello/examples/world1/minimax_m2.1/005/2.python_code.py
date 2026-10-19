
import numpy as np
from typing import List, Tuple

# Positional weight matrix - corners are very valuable, X-squares (adjacent to corners) are dangerous
POSITIONAL_WEIGHTS = np.array([
    [100, -25,  10,   5,   5,  10, -25, 100],
    [-25, -25,   1,   1,   1,   1, -25, -25],
    [ 10,   1,   5,   2,   2,   5,   1,  10],
    [  5,   1,   2,   1,   1,   2,   1,   5],
    [  5,   1,   2,   1,   1,   2,   1,   5],
    [ 10,   1,   5,   2,   2,   5,   1,  10],
    [-25, -25,   1,   1,   1,   1, -25, -25],
    [100, -25,  10,   5,   5,  10, -25, 100]
])

# 8 directions: (row_delta, col_delta)
DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """
    Main policy function that determines the best move for the current player.
    """
    # Get all legal moves
    legal_moves = get_legal_moves(you, opponent)
    
    # If no legal moves, must pass
    if not legal_moves:
        return "pass"
    
    # If only one move, take it
    if len(legal_moves) == 1:
        return legal_moves[0]
    
    # Use minimax with alpha-beta pruning
    best_move = None
    best_value = float('-inf')
    
    # Order moves for better alpha-beta pruning efficiency
    ordered_moves = order_moves(legal_moves, you, opponent)
    
    for move in ordered_moves:
        # Apply the move
        new_you, new_opponent = apply_move(you, opponent, move)
        
        # Evaluate the position using minimax
        value = minimax(new_you, new_opponent, depth=3, alpha=float('-inf'), beta=float('inf'), maximizing_player=False)
        
        if value > best_value:
            best_value = value
            best_move = move
    
    return best_move if best_move else legal_moves[0]

def get_legal_moves(you: np.ndarray, opponent: np.ndarray) -> List[str]:
    """
    Returns a list of all legal moves in algebraic notation (e.g., 'd3').
    """
    legal_moves = []
    for r in range(8):
        for c in range(8):
            if you[r][c] == 0 and opponent[r][c] == 0:  # Empty cell
                if can_place_disc(you, opponent, r, c):
                    legal_moves.append(f"{chr(ord('a') + c)}{r + 1}")
    return legal_moves

def can_place_disc(you: np.ndarray, opponent: np.ndarray, r: int, c: int) -> bool:
    """
    Checks if placing a disc at (r, c) would flip at least one opponent disc.
    """
    for dr, dc in DIRECTIONS:
        if would_flip_in_direction(you, opponent, r, c, dr, dc):
            return True
    return False

def would_flip_in_direction(you: np.ndarray, opponent: np.ndarray, r: int, c: int, dr: int, dc: int) -> bool:
    """
    Checks if placing a disc at (r, c) would flip opponent discs in a specific direction.
    """
    nr, nc = r + dr, c + dc
    has_opponent_between = False
    
    while 0 <= nr < 8 and 0 <= nc < 8:
        if opponent[nr][nc] == 1:
            has_opponent_between = True
        elif you[nr][nc] == 1:
            # Found our own disc, so we have a valid flip sequence
            return has_opponent_between
        else:
            # Found an empty cell, invalid sequence
            break
        nr, nc = nr + dr, nc + dc
    
    return False

def apply_move(you: np.ndarray, opponent: np.ndarray, move: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Applies a move and returns the new board state.
    """
    # Parse the move
    col = ord(move[0].lower()) - ord('a')
    row = int(move[1]) - 1
    
    new_you = you.copy()
    new_opponent = opponent.copy()
    
    # Place the disc
    new_you[row][col] = 1
    
    # Flip opponent discs in all valid directions
    for dr, dc in DIRECTIONS:
        flips = get_flips_in_direction(new_you, new_opponent, row, col, dr, dc)
        for r, c in flips:
            new_you[r][c] = 1
            new_opponent[r][c] = 0
    
    return new_you, new_opponent

def get_flips_in_direction(you: np.ndarray, opponent: np.ndarray, r: int, c: int, dr: int, dc: int) -> List[Tuple[int, int]]:
    """
    Returns a list of opponent disc positions that would be flipped in a specific direction.
    """
    flips = []
    nr, nc = r + dr, c + dc
    
    while 0 <= nr < 8 and 0 <= nc < 8:
        if opponent[nr][nc] == 1:
            flips.append((nr, nc))
        elif you[nr][nc] == 1:
            # Found our own disc, return all collected flips
            return flips
        else:
            # Found an empty cell, no flips in this direction
            return []
        nr, nc = nr + dr, nc + dc
    
    return []

def order_moves(moves: List[str], you: np.ndarray, opponent: np.ndarray) -> List[str]:
    """
    Orders moves by strategic importance for better search efficiency.
    Prioritizes corners, then edges, then other moves.
    """
    move_scores = []
    
    for move in moves:
        col = ord(move[0].lower()) - ord('a')
        row = int(move[1]) - 1
        
        # Corner positions are best (highest weight)
        score = POSITIONAL_WEIGHTS[row][col]
        move_scores.append((score, move))
    
    # Sort by score descending (higher scores first)
    move_scores.sort(key=lambda x: -x[1][0])  # Sort by the actual move, not the tuple
    
    return [move for _, move in sorted(move_scores, key=lambda x: -x[0])]

def minimax(you: np.ndarray, opponent: np.ndarray, depth: int, alpha: float, beta: float, maximizing_player: bool) -> float:
    """
    Minimax algorithm with alpha-beta pruning for Othello.
    """
    # Check if game is over or depth limit reached
    if depth == 0:
        return evaluate_board(you, opponent)
    
    # Get legal moves for the current player
    if maximizing_player:
        legal_moves = get_legal_moves(you, opponent)
    else:
        legal_moves = get_legal_moves(opponent, you)
    
    # If no legal moves for current player, check if opponent has moves
    if not legal_moves:
        opponent_moves = get_legal_moves(opponent, you)
        if not opponent_moves:
            # Game over - count discs
            return count_score(you, opponent)
        else:
            # Current player must pass
            return minimax(you, opponent, depth - 1, alpha, beta, not maximizing_player)
    
    if maximizing_player:
        max_eval = float('-inf')
        for move in legal_moves:
            new_you, new_opponent = apply_move(you, opponent, move)
            eval_score = minimax(new_you, new_opponent, depth - 1, alpha, beta, False)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for move in legal_moves:
            new_you, new_opponent = apply_move(opponent, you, move)
            eval_score = minimax(new_you, new_opponent, depth - 1, alpha, beta, True)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval

def evaluate_board(you: np.ndarray, opponent: np.ndarray) -> float:
    """
    Evaluates the board position using positional weights and mobility.
    """
    # Calculate positional score
    your_positional_score = np.sum(you * POSITIONAL_WEIGHTS)
    opponent_positional_score = np.sum(opponent * POSITIONAL_WEIGHTS)
    
    # Calculate mobility (number of legal moves)
    your_mobility = len(get_legal_moves(you, opponent))
    opponent_mobility = len(get_legal_moves(opponent, you))
    
    # Combine scores: positional advantage + mobility advantage
    # Give more weight to mobility as game progresses
    mobility_weight = 2.0
    
    score = your_positional_score - opponent_positional_score + \
            mobility_weight * (your_mobility - opponent_mobility)
    
    return score

def count_score(you: np.ndarray, opponent: np.ndarray) -> float:
    """
    Returns the final score (difference in disc count).
    Used when game is over.
    """
    your_discs = np.sum(you)
    opponent_discs = np.sum(opponent)
    
    # Return large positive/negative value to strongly prefer winning
    if your_discs > opponent_discs:
        return 1000 + your_discs - opponent_discs
    elif opponent_discs > your_discs:
        return -1000 - (opponent_discs - your_discs)
    else:
        return 0
