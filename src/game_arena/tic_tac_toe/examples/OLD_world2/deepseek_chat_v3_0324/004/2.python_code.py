
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    """Determine the best move for the AI player in 4x4 Tic-Tac-Toe.
    
    Args:
        board: 4x4 list of lists with 0 (empty), 1 (AI), -1 (opponent)
    
    Returns:
        Tuple of (row, col) indices (0-3) for the best move
    """
    # Convert board to numpy array for easier processing
    board_array = np.array(board)
    
    # Check if we can win immediately
    for i in range(4):
        for j in range(4):
            if board_array[i, j] == 0:
                board_array[i, j] = 1  # Try our move
                if check_winner(board_array) == 1:
                    board_array[i, j] = 0  # Undo move
                    return (i, j)
                board_array[i, j] = 0  # Undo move
    
    # Check if opponent will win next move and block
    for i in range(4):
        for j in range(4):
            if board_array[i, j] == 0:
                board_array[i, j] = -1  # Try opponent's move
                if check_winner(board_array) == -1:
                    board_array[i, j] = 0  # Undo move
                    return (i, j)
                board_array[i, j] = 0  # Undo move
    
    # If center is free, take it
    if board_array[1, 1] == 0 or board_array[1, 2] == 0 or board_array[2, 1] == 0 or board_array[2, 2] == 0:
        if board_array[1, 1] == 0:
            return (1, 1)
        elif board_array[1, 2] == 0:
            return (1, 2)
        elif board_array[2, 1] == 0:
            return (2, 1)
        elif board_array[2, 2] == 0:
            return (2, 2)
    
    # Otherwise use minimax with alpha-beta pruning to find best move
    best_score = -float('inf')
    best_move = None
    
    for i in range(4):
        for j in range(4):
            if board_array[i, j] == 0:
                board_array[i, j] = 1
                score = minimax(board_array, 0, False, -float('inf'), float('inf'))
                board_array[i, j] = 0
                
                if score > best_score:
                    best_score = score
                    best_move = (i, j)
    
    return best_move if best_move is not None else find_empty_cell(board_array)

def minimax(board, depth, is_maximizing, alpha, beta):
    """Recursive minimax algorithm with alpha-beta pruning."""
    result = check_winner(board)
    
    if result is not None:
        if result == 1:
            return 10 - depth
        elif result == -1:
            return -10 + depth
        else:
            return 0
    
    if is_maximizing:
        best_score = -float('inf')
        
        for i in range(4):
            for j in range(4):
                if board[i, j] == 0:
                    board[i, j] = 1
                    score = minimax(board, depth + 1, False, alpha, beta)
                    board[i, j] = 0
                    best_score = max(score, best_score)
                    alpha = max(alpha, best_score)
                    if beta <= alpha:
                        break
        return best_score
    else:
        best_score = float('inf')
        
        for i in range(4):
            for j in range(4):
                if board[i, j] == 0:
                    board[i, j] = -1
                    score = minimax(board, depth + 1, True, alpha, beta)
                    board[i, j] = 0
                    best_score = min(score, best_score)
                    beta = min(beta, best_score)
                    if beta <= alpha:
                        break
        return best_score

def check_winner(board):
    """Check if there's a winner or if the game is a draw.
    
    Returns:
        1 if AI wins, -1 if opponent wins, 0 for draw, None if game continues
    """
    # Check rows
    for i in range(4):
        if abs(sum(board[i, :])) == 4:
            return board[i, 0]
    
    # Check columns
    for j in range(4):
        if abs(sum(board[:, j])) == 4:
            return board[0, j]
    
    # Check diagonals
    if abs(sum([board[i, i] for i in range(4)])) == 4:
        return board[0, 0]
    if abs(sum([board[i, 3 - i] for i in range(4)])) == 4:
        return board[0, 3]
    
    # Check if board is full (draw)
    if 0 not in board:
        return 0
    
    return None

def find_empty_cell(board):
    """Fallback to find any empty cell."""
    for i in range(4):
        for j in range(4):
            if board[i, j] == 0:
                return (i, j)
    return (0, 0)  # Should never reach here if check_winner is called first
