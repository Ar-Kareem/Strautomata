
import numpy as np
from typing import Tuple, List

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Minimax-based policy for 4x4 Tic Tac Toe with alpha-beta pruning.
    Prioritizes winning moves, blocks opponent wins, and uses heuristic evaluation.
    """
    board_array = np.array(board)
    
    # Check for available moves
    empty_cells = [(i, j) for i in range(4) for j in range(4) if board_array[i, j] == 0]
    if not empty_cells:
        return (0, 0)  # Should not happen in valid game
    
    # Check for immediate winning move
    for i, j in empty_cells:
        board_array[i, j] = 1
        if check_win(board_array, 1):
            board_array[i, j] = 0
            return (i, j)
        board_array[i, j] = 0
    
    # Check for opponent's winning move to block
    for i, j in empty_cells:
        board_array[i, j] = -1
        if check_win(board_array, -1):
            board_array[i, j] = 0
            return (i, j)
        board_array[i, j] = 0
    
    # Use minimax with alpha-beta pruning for best move
    _, move = minimax(board_array, 0, -np.inf, np.inf, False, 3)
    if move is not None:
        return move
    
    # Fallback: center preference then random
    center_positions = [(1,1), (1,2), (2,1), (2,2)]
    for pos in center_positions:
        if pos in empty_cells:
            return pos
    
    return empty_cells[0]

def check_win(board: np.ndarray, player: int) -> bool:
    """Check if the player has won."""
    # Check rows
    for i in range(4):
        if np.all(board[i, :] == player):
            return True
    
    # Check columns
    for j in range(4):
        if np.all(board[:, j] == player):
            return True
    
    # Check diagonals
    if np.all(np.diag(board) == player):
        return True
    if np.all(np.diag(np.fliplr(board)) == player):
        return True
        
    return False

def evaluate(board: np.ndarray) -> int:
    """Heuristic evaluation of board position."""
    score = 0
    
    # Check all rows
    for i in range(4):
        score += evaluate_line(board[i, :])
    
    # Check all columns
    for j in range(4):
        score += evaluate_line(board[:, j])
    
    # Check diagonals
    score += evaluate_line(np.diag(board))
    score += evaluate_line(np.diag(np.fliplr(board)))
    
    return score

def evaluate_line(line: np.ndarray) -> int:
    """Evaluate a single line (row, col, or diagonal)."""
    player_count = np.sum(line == 1)
    opponent_count = np.sum(line == -1)
    empty_count = np.sum(line == 0)
    
    if opponent_count == 0:
        # Potential for player to win this line
        if player_count == 4:
            return 100  # Win
        elif player_count == 3:
            return 10   # One away from win
        elif player_count == 2:
            return 3
        elif player_count == 1:
            return 1
    elif player_count == 0:
        # Potential for opponent to win this line
        if opponent_count == 4:
            return -100  # Loss
        elif opponent_count == 3:
            return -10   # Opponent one away from win
        elif opponent_count == 2:
            return -3
        elif opponent_count == 1:
            return -1
    
    return 0  # Mixed line, no potential

def minimax(board: np.ndarray, depth: int, alpha: float, beta: float, 
            is_maximizing: bool, max_depth: int) -> Tuple[int, Tuple[int, int]]:
    """Minimax with alpha-beta pruning."""
    # Terminal conditions
    if check_win(board, 1):
        return 100 - depth, None
    if check_win(board, -1):
        return depth - 100, None
    if depth >= max_depth or np.all(board != 0):
        return evaluate(board), None
    
    empty_cells = [(i, j) for i in range(4) for j in range(4) if board[i, j] == 0]
    
    if is_maximizing:
        max_eval = -np.inf
        best_move = None
        
        for i, j in empty_cells:
            board[i, j] = 1
            eval_score, _ = minimax(board, depth + 1, alpha, beta, False, max_depth)
            board[i, j] = 0
            
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = (i, j)
            
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
                
        return max_eval, best_move
    else:
        min_eval = np.inf
        best_move = None
        
        for i, j in empty_cells:
            board[i, j] = -1
            eval_score, _ = minimax(board, depth + 1, alpha, beta, True, max_depth)
            board[i, j] = 0
            
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = (i, j)
            
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
                
        return min_eval, best_move
