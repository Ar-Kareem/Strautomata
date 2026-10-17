
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert to numpy array for easier handling
    board = np.array(board)
    
    # Find all empty positions
    empty_positions = np.where(board == 0)
    empty_positions = list(zip(empty_positions[0], empty_positions[1]))
    
    # If no moves left, return something (shouldn't happen in proper game)
    if len(empty_positions) == 0:
        return (0, 0)
    
    # If only one move left, take it
    if len(empty_positions) == 1:
        return empty_positions[0]
    
    # AI is player 1 (maximizing player)
    best_move = None
    best_value = float('-inf')
    
    # Try each possible move
    for row, col in empty_positions:
        # Make the move
        board[row, col] = 1
        
        # Evaluate this move using minimax (opponent is minimizing player)
        move_value = minimax(board, depth=0, alpha=float('-inf'), beta=float('inf'), is_maximizing=False)
        
        # Undo the move
        board[row, col] = 0
        
        # Choose the move with maximum value
        if move_value > best_value:
            best_value = move_value
            best_move = (row, col)
    
    return best_move

def minimax(board, depth, alpha, beta, is_maximizing):
    # Check for terminal states
    winner = check_winner(board)
    if winner == 1:  # AI wins
        return 10 - depth  # Prefer faster wins
    elif winner == -1:  # Opponent wins
        return depth - 10  # Prefer slower losses
    elif not np.any(board == 0):  # Draw
        return 0
    
    if is_maximizing:
        max_eval = float('-inf')
        empty_positions = np.where(board == 0)
        empty_positions = list(zip(empty_positions[0], empty_positions[1]))
        
        for row, col in empty_positions:
            board[row, col] = 1  # AI's move
            eval_val = minimax(board, depth + 1, alpha, beta, False)
            board[row, col] = 0  # Undo move
            
            max_eval = max(max_eval, eval_val)
            alpha = max(alpha, eval_val)
            
            if beta <= alpha:
                break  # Alpha-beta pruning
                
        return max_eval
    else:
        min_eval = float('inf')
        empty_positions = np.where(board == 0)
        empty_positions = list(zip(empty_positions[0], empty_positions[1]))
        
        for row, col in empty_positions:
            board[row, col] = -1  # Opponent's move
            eval_val = minimax(board, depth + 1, alpha, beta, True)
            board[row, col] = 0  # Undo move
            
            min_eval = min(min_eval, eval_val)
            beta = min(beta, eval_val)
            
            if beta <= alpha:
                break  # Alpha-beta pruning
                
        return min_eval

def check_winner(board):
    # Check rows
    for i in range(3):
        if board[i, 0] == board[i, 1] == board[i, 2] != 0:
            return board[i, 0]
    
    # Check columns
    for j in range(3):
        if board[0, j] == board[1, j] == board[2, j] != 0:
            return board[0, j]
    
    # Check diagonals
    if board[0, 0] == board[1, 1] == board[2, 2] != 0:
        return board[0, 0]
    if board[0, 2] == board[1, 1] == board[2, 0] != 0:
        return board[0, 2]
    
    return None
