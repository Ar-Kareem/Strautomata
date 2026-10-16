
import numpy as np
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    board_array = np.array(board)
    
    # Find all empty cells
    empty_cells = []
    for i in range(4):
        for j in range(4):
            if board_array[i, j] == 0:
                empty_cells.append((i, j))
    
    # If board is empty, take center for advantage
    if len(empty_cells) == 16:
        return (1, 1)
    
    # Check if I can win in one move
    for i, j in empty_cells:
        board_array[i, j] = 1
        if check_win(board_array, 1):
            board_array[i, j] = 0
            return (i, j)
        board_array[i, j] = 0
    
    # Check if opponent can win in one move - block them
    for i, j in empty_cells:
        board_array[i, j] = -1
        if check_win(board_array, -1):
            board_array[i, j] = 0
            return (i, j)
        board_array[i, j] = 0
    
    # Use minimax with alpha-beta pruning for deeper analysis
    best_score = float('-inf')
    best_move = empty_cells[0]  # Default to first empty cell
    
    alpha = float('-inf')
    beta = float('inf')
    
    # Limit depth based on remaining cells for performance
    remaining_moves = len(empty_cells)
    if remaining_moves > 10:
        max_depth = 4
    elif remaining_moves > 6:
        max_depth = 5
    else:
        max_depth = 6
    
    for i, j in empty_cells:
        board_array[i, j] = 1  # Make move
        score = minimax(board_array, 0, False, alpha, beta, max_depth)
        board_array[i, j] = 0  # Undo move
        
        if score > best_score:
            best_score = score
            best_move = (i, j)
            
        alpha = max(alpha, best_score)
        if alpha >= beta:
            break
    
    return best_move

def check_win(board: np.ndarray, player: int) -> bool:
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
    score = 0
    # Evaluate rows
    for i in range(4):
        score += evaluate_line(board[i, :])
    
    # Evaluate columns
    for j in range(4):
        score += evaluate_line(board[:, j])
    
    # Evaluate diagonals
    score += evaluate_line(np.diag(board))
    score += evaluate_line(np.diag(np.fliplr(board)))
    
    return score

def evaluate_line(line: np.ndarray) -> int:
    count_1 = np.sum(line == 1)   # our marks
    count_neg1 = np.sum(line == -1)  # opponent marks
    count_0 = np.sum(line == 0)   # empty spaces
    
    if count_neg1 == 0 and count_1 > 0:
        # No opponent marks in this line - potential for us
        if count_1 == 4:
            return 1000  # winning line
        elif count_1 == 3:
            return 50
        elif count_1 == 2:
            return 10
        elif count_1 == 1:
            return 1
    elif count_1 == 0 and count_neg1 > 0:
        # No our marks in this line - opponent potential
        if count_neg1 == 4:
            return -1000  # opponent winning
        elif count_neg1 == 3:
            return -50
        elif count_neg1 == 2:
            return -10
    
    # Mixed line or blocked line has no value
    return 0

def minimax(board: np.ndarray, depth: int, is_maximizing: bool, alpha: float, beta: float, max_depth: int) -> int:
    # Check terminal states
    if check_win(board, 1):
        return 1000 - depth  # Prefer faster wins
    if check_win(board, -1):
        return -1000 + depth  # Prefer slower losses
    
    # Check for draw or depth limit
    if depth >= max_depth:
        return evaluate(board)
    
    empty_cells = []
    for i in range(4):
        for j in range(4):
            if board[i, j] == 0:
                empty_cells.append((i, j))
    
    if len(empty_cells) == 0:  # Board is full (draw)
        return 0
    
    if is_maximizing:
        max_eval = float('-inf')
        for i, j in empty_cells:
            board[i, j] = 1
            eval_score = minimax(board, depth + 1, False, alpha, beta, max_depth)
            board[i, j] = 0
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if alpha >= beta:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for i, j in empty_cells:
            board[i, j] = -1
            eval_score = minimax(board, depth + 1, True, alpha, beta, max_depth)
            board[i, j] = 0
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval
