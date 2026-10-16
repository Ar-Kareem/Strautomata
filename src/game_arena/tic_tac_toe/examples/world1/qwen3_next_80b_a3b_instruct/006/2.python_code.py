
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert to numpy array for easier manipulation
    board_np = np.array(board)
    
    # Get empty cells
    empty_cells = [(i, j) for i in range(3) for j in range(3) if board_np[i][j] == 0]
    
    # If no empty cells, return a random move (should not happen in valid game state)
    if not empty_cells:
        return (0, 0)
    
    # Check for immediate win
    for row, col in empty_cells:
        board_np[row][col] = 1
        if check_winner(board_np, 1):
            board_np[row][col] = 0  # Reset
            return (row, col)
        board_np[row][col] = 0  # Reset
    
    # Check for opponent's immediate win and block it
    for row, col in empty_cells:
        board_np[row][col] = -1
        if check_winner(board_np, -1):
            board_np[row][col] = 0  # Reset
            return (row, col)
        board_np[row][col] = 0  # Reset
    
    # Strategic first moves: take center if available
    if board_np[1][1] == 0:
        return (1, 1)
    
    # Take a corner if available
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    available_corners = [c for c in corners if board_np[c[0]][c[1]] == 0]
    if available_corners:
        return available_corners[0]
    
    # Otherwise, use minimax with alpha-beta pruning
    best_move = None
    best_score = -float('inf')
    alpha = -float('inf')
    beta = float('inf')
    
    for row, col in empty_cells:
        board_np[row][col] = 1
        score = minimax(board_np, 0, False, alpha, beta)
        board_np[row][col] = 0  # Reset
        
        if score > best_score:
            best_score = score
            best_move = (row, col)
        
        alpha = max(alpha, best_score)
        if beta <= alpha:
            break
    
    return best_move if best_move else empty_cells[0]

def check_winner(board, player):
    # Check rows
    for i in range(3):
        if all(board[i][j] == player for j in range(3)):
            return True
    # Check columns
    for j in range(3):
        if all(board[i][j] == player for i in range(3)):
            return True
    # Check diagonals
    if all(board[i][i] == player for i in range(3)):
        return True
    if all(board[i][2-i] == player for i in range(3)):
        return True
    return False

def minimax(board, depth, is_maximizing, alpha, beta):
    # Check for terminal states
    if check_winner(board, 1):
        return 1
    if check_winner(board, -1):
        return -1
    if not any(board[i][j] == 0 for i in range(3) for j in range(3)):
        return 0
    
    if is_maximizing:
        max_eval = -float('inf')
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    board[i][j] = 1
                    eval_score = minimax(board, depth + 1, False, alpha, beta)
                    board[i][j] = 0
                    max_eval = max(max_eval, eval_score)
                    alpha = max(alpha, eval_score)
                    if beta <= alpha:
                        break
        return max_eval
    else:
        min_eval = float('inf')
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    board[i][j] = -1
                    eval_score = minimax(board, depth + 1, True, alpha, beta)
                    board[i][j] = 0
                    min_eval = min(min_eval, eval_score)
                    beta = min(beta, eval_score)
                    if beta <= alpha:
                        break
        return min_eval
