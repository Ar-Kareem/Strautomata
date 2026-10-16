
import numpy as np
from typing import List, Tuple

def policy(board: list[list[int]]) -> int:
    """
    Connect 4 policy using minimax with alpha-beta pruning.
    Returns the best column to play.
    """
    
    # Convert to numpy array for efficient operations
    board_np = np.array(board, dtype=np.int8)
    
    # Get valid moves (columns that aren't full)
    valid_moves = [col for col in range(7) if board_np[0, col] == 0]
    
    if not valid_moves:
        return 0  # Should not happen in normal play
    
    # If only one move available, take it
    if len(valid_moves) == 1:
        return valid_moves[0]
    
    # If center column is available, prefer it for opening moves
    if 3 in valid_moves and np.sum(np.abs(board_np)) < 10:
        return 3
    
    # Minimax search with alpha-beta pruning
    best_score = float('-inf')
    best_move = valid_moves[0]
    alpha = float('-inf')
    beta = float('inf')
    
    # Sort moves to improve pruning (center-first, then alternating sides)
    sorted_moves = sorted(valid_moves, key=lambda x: -abs(x - 3))
    
    for col in sorted_moves:
        # Make the move
        row = get_next_open_row(board_np, col)
        board_np[row, col] = 1
        
        # Evaluate this position
        score = -negamax(board_np, 6, -beta, -alpha, -1)  # Search opponent's turn
        
        # Undo the move
        board_np[row, col] = 0
        
        if score > best_score:
            best_score = score
            best_move = col
            
        alpha = max(alpha, score)
        if alpha >= beta:
            break  # Alpha-beta cutoff
            
    return best_move

def get_next_open_row(board: np.ndarray, col: int) -> int:
    """Find the lowest empty row in the given column."""
    for row in range(5, -1, -1):
        if board[row, col] == 0:
            return row
    return -1

def negamax(board: np.ndarray, depth: int, alpha: float, beta: float, player: int) -> float:
    """
    Negamax implementation with alpha-beta pruning.
    player: 1 for current player, -1 for opponent
    """
    # Check for terminal states
    result = evaluate_terminal(board)
    if result != 0:  # Game over
        return result * 1000000 * player  # Large value for wins/losses
    
    if depth == 0:
        return evaluate_position(board) * player
    
    valid_moves = [col for col in range(7) if board[0, col] == 0]
    if not valid_moves:
        return 0  # Draw
    
    # Sort moves for better pruning
    sorted_moves = sorted(valid_moves, key=lambda x: -abs(x - 3))
    
    max_score = float('-inf')
    
    for col in sorted_moves:
        row = get_next_open_row(board, col)
        board[row, col] = player
        
        score = -negamax(board, depth - 1, -beta, -alpha, -player)
        
        board[row, col] = 0
        
        max_score = max(max_score, score)
        alpha = max(alpha, score)
        
        if alpha >= beta:
            break
            
    return max_score

def evaluate_terminal(board: np.ndarray) -> int:
    """
    Check if the game is over.
    Returns: 1 if player 1 wins, -1 if player -1 wins, 0 if not terminal
    """
    # Check horizontal
    for row in range(6):
        for col in range(4):
            if (board[row, col] != 0 and 
                board[row, col] == board[row, col+1] == board[row, col+2] == board[row, col+3]):
                return board[row, col]
    
    # Check vertical
    for row in range(3):
        for col in range(7):
            if (board[row, col] != 0 and 
                board[row, col] == board[row+1, col] == board[row+2, col] == board[row+3, col]):
                return board[row, col]
    
    # Check diagonal (positive slope)
    for row in range(3):
        for col in range(4):
            if (board[row, col] != 0 and 
                board[row, col] == board[row+1, col+1] == board[row+2, col+2] == board[row+3, col+3]):
                return board[row, col]
    
    # Check diagonal (negative slope)
    for row in range(3, 6):
        for col in range(4):
            if (board[row, col] != 0 and 
                board[row, col] == board[row-1, col+1] == board[row-2, col+2] == board[row-3, col+3]):
                return board[row, col]
    
    return 0

def evaluate_position(board: np.ndarray) -> float:
    """
    Heuristic evaluation of board position.
    Positive values favor player 1, negative favor player -1.
    """
    score = 0
    
    # Center column control is valuable
    center_array = list(board[:, 3])
    center_count = center_array.count(1)
    score += center_count * 3
    
    # Evaluate potential winning lines
    score += evaluate_lines(board, 1) * 10  # Current player
    score -= evaluate_lines(board, -1) * 10  # Opponent
    
    return score

def evaluate_lines(board: np.ndarray, player: int) -> int:
    """Count potential winning lines for the given player."""
    score = 0
    opponent = -player
    
    # Check horizontal
    for row in range(6):
        for col in range(4):
            window = [board[row, col+i] for i in range(4)]
            score += evaluate_window(window, player, opponent)
    
    # Check vertical
    for row in range(3):
        for col in range(7):
            window = [board[row+i, col] for i in range(4)]
            score += evaluate_window(window, player, opponent)
    
    # Check positive diagonal
    for row in range(3):
        for col in range(4):
            window = [board[row+i, col+i] for i in range(4)]
            score += evaluate_window(window, player, opponent)
    
    # Check negative diagonal
    for row in range(3, 6):
        for col in range(4):
            window = [board[row-i, col+i] for i in range(4)]
            score += evaluate_window(window, player, opponent)
    
    return score

def evaluate_window(window: List[int], player: int, opponent: int) -> int:
    """Evaluate a 4-cell window for potential scoring."""
    score = 0
    player_count = window.count(player)
    opponent_count = window.count(opponent)
    empty_count = window.count(0)
    
    if opponent_count == 0:
        if player_count == 4:
            score += 100
        elif player_count == 3 and empty_count == 1:
            score += 5
        elif player_count == 2 and empty_count == 2:
            score += 2
    elif player_count == 0:
        if opponent_count == 3 and empty_count == 1:
            score -= 4  # Block opponent's threat
        elif opponent_count == 2 and empty_count == 2:
            score -= 1
    
    return score
