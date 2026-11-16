
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert to numpy array for easier manipulation
    board_arr = np.array(board)
    
    # Find all empty positions
    empty_positions = [(i, j) for i in range(3) for j in range(3) if board_arr[i, j] == 0]
    
    # If no moves left (shouldn't happen in normal game), return any valid move
    if not empty_positions:
        return (0, 0)
    
    # If only one move left, take it
    if len(empty_positions) == 1:
        return empty_positions[0]
    
    # Our symbol is 1, opponent is -1
    # Use minimax with alpha-beta pruning for optimal play
    
    def evaluate_board(board):
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
        # Check for draw
        if np.all(board != 0):
            return 0
        # Game continues
        return None
    
    def minimax(board, depth, alpha, beta, is_maximizing):
        # Check if game is over
        result = evaluate_board(board)
        if result is not None:
            return result
        
        if is_maximizing:
            max_eval = float('-inf')
            for i in range(3):
                for j in range(3):
                    if board[i, j] == 0:
                        board[i, j] = 1  # Our move
                        eval = minimax(board, depth + 1, alpha, beta, False)
                        board[i, j] = 0  # Undo move
                        max_eval = max(max_eval, eval)
                        alpha = max(alpha, eval)
                        if beta <= alpha:
                            break  # Beta cutoff
            return max_eval
        else:
            min_eval = float('inf')
            for i in range(3):
                for j in range(3):
                    if board[i, j] == 0:
                        board[i, j] = -1  # Opponent's move
                        eval = minimax(board, depth + 1, alpha, beta, True)
                        board[i, j] = 0  # Undo move
                        min_eval = min(min_eval, eval)
                        beta = min(beta, eval)
                        if beta <= alpha:
                            break  # Alpha cutoff
            return min_eval
    
    # Find best move
    best_move = None
    best_value = float('-inf')
    
    # First, check for immediate win
    for row, col in empty_positions:
        board_arr[row, col] = 1
        if evaluate_board(board_arr) == 1:
            return (row, col)
        board_arr[row, col] = 0  # Undo
    
    # Then, check for opponent's immediate win and block it
    for row, col in empty_positions:
        board_arr[row, col] = -1
        if evaluate_board(board_arr) == -1:
            return (row, col)
        board_arr[row, col] = 0  # Undo
    
    # Otherwise, use minimax to find optimal move
    for row, col in empty_positions:
        board_arr[row, col] = 1
        move_value = minimax(board_arr, 0, float('-inf'), float('inf'), False)
        board_arr[row, col] = 0  # Undo
        
        if move_value > best_value:
            best_value = move_value
            best_move = (row, col)
    
    # In case of failure (shouldn't happen), return first available move
    if best_move is None:
        return empty_positions[0]
    
    return best_move
