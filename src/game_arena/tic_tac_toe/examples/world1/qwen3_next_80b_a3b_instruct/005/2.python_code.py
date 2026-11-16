
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert to numpy array for easier manipulation
    board_np = np.array(board)
    
    # Get all empty positions
    empty_positions = [(i, j) for i in range(3) for j in range(3) if board_np[i][j] == 0]
    
    # If no empty positions (game should be over, but just in case)
    if not empty_positions:
        return (0, 0)
    
    # Check for immediate win
    for i, j in empty_positions:
        board_np[i][j] = 1
        if check_win(board_np, 1):
            board_np[i][j] = 0  # Reset
            return (i, j)
        board_np[i][j] = 0
    
    # Check for opponent win and block
    for i, j in empty_positions:
        board_np[i][j] = -1
        if check_win(board_np, -1):
            board_np[i][j] = 0  # Reset
            return (i, j)
        board_np[i][j] = 0
    
    # Strategic move ordering: center > corners > edges
    strategic_order = [(1, 1), (0, 0), (0, 2), (2, 0), (2, 2), (0, 1), (1, 0), (1, 2), (2, 1)]
    best_move = None
    best_value = float('-inf')
    
    # Alpha-beta pruning parameters
    alpha = float('-inf')
    beta = float('inf')
    
    # Evaluate each strategic move
    for pos in strategic_order:
        if pos not in empty_positions:
            continue
            
        board_np[pos[0]][pos[1]] = 1
        move_value = minimax(board_np, 0, False, alpha, beta)
        board_np[pos[0]][pos[1]] = 0
        
        if move_value > best_value:
            best_value = move_value
            best_move = pos
            
        alpha = max(alpha, best_value)
        if beta <= alpha:
            break  # Alpha-beta pruning
    
    # Fallback - should not reach here if empty_positions is non-empty
    if best_move is None:
        best_move = empty_positions[0]
    
    return best_move

def check_win(board, player):
    # Check rows
    for i in range(3):
        if np.all(board[i, :] == player):
            return True
    
    # Check columns
    for j in range(3):
        if np.all(board[:, j] == player):
            return True
    
    # Check diagonals
    if board[0, 0] == player and board[1, 1] == player and board[2, 2] == player:
        return True
    if board[0, 2] == player and board[1, 1] == player and board[2, 0] == player:
        return True
    
    return False

def minimax(board, depth, is_maximizing, alpha, beta):
    # Check terminal states
    if check_win(board, 1):  # AI wins
        return 10 - depth
    if check_win(board, -1):  # Opponent wins
        return depth - 10
    if not np.any(board == 0):  # Draw
        return 0
    
    empty_positions = [(i, j) for i in range(3) for j in range(3) if board[i][j] == 0]
    
    if is_maximizing:
        max_eval = float('-inf')
        for i, j in empty_positions:
            board[i][j] = 1
            eval = minimax(board, depth + 1, False, alpha, beta)
            board[i][j] = 0
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break  # Beta cutoff
        return max_eval
    else:
        min_eval = float('inf')
        for i, j in empty_positions:
            board[i][j] = -1
            eval = minimax(board, depth + 1, True, alpha, beta)
            board[i][j] = 0
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break  # Alpha cutoff
        return min_eval
