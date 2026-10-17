
import numpy as np
from typing import Tuple, List

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    """
    Implements a 3D Tic Tac Toe strategy using minimax with alpha-beta pruning.
    
    Args:
        board: 3x3x3 list of lists representing the game board
               0 = empty, 1 = player (me), -1 = opponent
    
    Returns:
        Tuple (x, y, z) representing the chosen move coordinates
    """
    # Convert board to numpy array for easier manipulation
    board_array = np.array(board)
    
    # Check for immediate winning moves
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board_array[x, y, z] == 0:
                    board_array[x, y, z] = 1
                    if check_win(board_array, 1):
                        return (x, y, z)
                    board_array[x, y, z] = 0
    
    # Check for opponent winning moves to block
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board_array[x, y, z] == 0:
                    board_array[x, y, z] = -1
                    if check_win(board_array, -1):
                        return (x, y, z)
                    board_array[x, y, z] = 0
    
    # If no immediate threats, use minimax (limited depth for performance)
    _, move = minimax(board_array, 4, -np.inf, np.inf, True)
    return move if move else find_first_empty(board_array)

def check_win(board: np.ndarray, player: int) -> bool:
    """Check if the specified player has won the game."""
    # Check all lines (rows, columns, pillars, and diagonals)
    
    # Check rows in each layer (x-y planes)
    for z in range(3):
        for x in range(3):
            if np.all(board[x, :, z] == player):
                return True
        for y in range(3):
            if np.all(board[:, y, z] == player):
                return True
    
    # Check pillars (z-direction)
    for x in range(3):
        for y in range(3):
            if np.all(board[x, y, :] == player):
                return True
    
    # Check layer diagonals (in each z-layer)
    for z in range(3):
        if (np.all(np.diag(board[:, :, z]) == player) or 
            np.all(np.diag(np.fliplr(board[:, :, z])) == player)):
            return True
    
    # Check space diagonals
    if (np.all([board[i, i, i] == player for i in range(3)]) or
        np.all([board[i, i, 2-i] == player for i in range(3)]) or
        np.all([board[i, 2-i, i] == player for i in range(3)]) or
        np.all([board[2-i, i, i] == player for i in range(3)])):
        return True
    
    # Check diagonal pillars
    for x in range(3):
        if (np.all([board[x, i, i] == player for i in range(3)]) or
            np.all([board[x, i, 2-i] == player for i in range(3)])):
            return True
            
    for y in range(3):
        if (np.all([board[i, y, i] == player for i in range(3)]) or
            np.all([board[i, y, 2-i] == player for i in range(3)])):
            return True
    
    return False

def evaluate_board(board: np.ndarray) -> int:
    """Evaluate the board state (heuristic function)."""
    if check_win(board, 1):
        return 100
    if check_win(board, -1):
        return -100
    
    score = 0
    
    # Count potential lines for each player
    # Check all possible lines of 3
    
    # Rows in layers
    for z in range(3):
        for x in range(3):
            line = board[x, :, z]
            score += evaluate_line(line)
        for y in range(3):
            line = board[:, y, z]
            score += evaluate_line(line)
    
    # Pillars
    for x in range(3):
        for y in range(3):
            line = board[x, y, :]
            score += evaluate_line(line)
    
    # Layer diagonals
    for z in range(3):
        diag1 = np.diag(board[:, :, z])
        diag2 = np.diag(np.fliplr(board[:, :, z]))
        score += evaluate_line(diag1) + evaluate_line(diag2)
    
    # Space diagonals
    space_diag1 = np.array([board[i, i, i] for i in range(3)])
    space_diag2 = np.array([board[i, i, 2-i] for i in range(3)])
    space_diag3 = np.array([board[i, 2-i, i] for i in range(3)])
    space_diag4 = np.array([board[2-i, i, i] for i in range(3)])
    
    score += (evaluate_line(space_diag1) + evaluate_line(space_diag2) + 
              evaluate_line(space_diag3) + evaluate_line(space_diag4))
    
    # Diagonal pillars
    for x in range(3):
        diag_pillar1 = np.array([board[x, i, i] for i in range(3)])
        diag_pillar2 = np.array([board[x, i, 2-i] for i in range(3)])
        score += evaluate_line(diag_pillar1) + evaluate_line(diag_pillar2)
        
    for y in range(3):
        diag_pillar3 = np.array([board[i, y, i] for i in range(3)])
        diag_pillar4 = np.array([board[i, y, 2-i] for i in range(3)])
        score += evaluate_line(diag_pillar3) + evaluate_line(diag_pillar4)
    
    return score

def evaluate_line(line: np.ndarray) -> int:
    """Evaluate a single line of 3 cells."""
    player_count = np.sum(line == 1)
    opponent_count = np.sum(line == -1)
    empty_count = np.sum(line == 0)
    
    # If line is blocked, it's worth nothing
    if player_count > 0 and opponent_count > 0:
        return 0
    
    # If line has potential
    if empty_count == 0:
        # Completed line
        if player_count == 3:
            return 10
        elif opponent_count == 3:
            return -10
    elif empty_count == 1:
        # One move to completion
        if player_count == 2:
            return 5
        elif opponent_count == 2:
            return -5
    elif empty_count == 2:
        # Two moves to completion
        if player_count == 1:
            return 2
        elif opponent_count == 1:
            return -2
            
    return 0

def minimax(board: np.ndarray, depth: int, alpha: float, beta: float, maximizing: bool) -> Tuple[int, Tuple[int, int, int]]:
    """Minimax algorithm with alpha-beta pruning."""
    
    # Check terminal states
    if check_win(board, 1):
        return 100 + depth, None
    if check_win(board, -1):
        return -100 - depth, None
    if depth == 0 or np.all(board != 0):
        return evaluate_board(board), None
    
    best_move = None
    
    if maximizing:  # Player's turn (1)
        max_eval = -np.inf
        # Try all possible moves
        for x in range(3):
            for y in range(3):
                for z in range(3):
                    if board[x, y, z] == 0:
                        board[x, y, z] = 1
                        eval_score, _ = minimax(board, depth - 1, alpha, beta, False)
                        board[x, y, z] = 0
                        
                        if eval_score > max_eval:
                            max_eval = eval_score
                            best_move = (x, y, z)
                        
                        alpha = max(alpha, eval_score)
                        if beta <= alpha:
                            break  # Beta cutoff
                if beta <= alpha:
                    break
            if beta <= alpha:
                break
                
        return max_eval, best_move
    else:  # Opponent's turn (-1)
        min_eval = np.inf
        # Try all possible moves
        for x in range(3):
            for y in range(3):
                for z in range(3):
                    if board[x, y, z] == 0:
                        board[x, y, z] = -1
                        eval_score, _ = minimax(board, depth - 1, alpha, beta, True)
                        board[x, y, z] = 0
                        
                        if eval_score < min_eval:
                            min_eval = eval_score
                            best_move = (x, y, z)
                        
                        beta = min(beta, eval_score)
                        if beta <= alpha:
                            break  # Alpha cutoff
                if beta <= alpha:
                    break
            if beta <= alpha:
                break
                
        return min_eval, best_move

def find_first_empty(board: np.ndarray) -> Tuple[int, int, int]:
    """Find the first empty cell as a fallback move."""
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x, y, z] == 0:
                    return (x, y, z)
    return (0, 0, 0)  # Should not happen if game is not over
