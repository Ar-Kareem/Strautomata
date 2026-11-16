
import random

def get_valid_moves(board):
    """Return all empty cells as (row, col) tuples."""
    moves = []
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                moves.append((r, c))
    return moves

def check_winner(board):
    """Check if there is a winner (1 for player 1, -1 for player -1, 0 for draw, None for ongoing)."""
    # Rows
    for r in range(3):
        if board[r][0] == board[r][1] == board[r][2] and board[r][0] != 0:
            return board[r][0]
    # Columns
    for c in range(3):
        if board[0][c] == board[1][c] == board[2][c] and board[0][c] != 0:
            return board[0][c]
    # Diagonals
    if board[0][0] == board[1][1] == board[2][2] and board[0][0] != 0:
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] and board[0][2] != 0:
        return board[0][2]
    # Check for draw
    if all(board[r][c] != 0 for r in range(3) for c in range(3)):
        return 0
    return None

def minimax(board, depth, alpha, beta, is_maximizing):
    """Minimax algorithm with alpha-beta pruning."""
    result = check_winner(board)
    if result is not None:
        if result == 1:
            return 10 - depth
        elif result == -1:
            return depth - 10
        else:
            return 0

    if is_maximizing:
        max_eval = -float('inf')
        for r, c in get_valid_moves(board):
            board[r][c] = 1
            eval_score = minimax(board, depth + 1, alpha, beta, False)
            board[r][c] = 0
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for r, c in get_valid_moves(board):
            board[r][c] = -1
            eval_score = minimax(board, depth + 1, alpha, beta, True)
            board[r][c] = 0
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval

def policy(board):
    """Return the best move using minimax with alpha-beta pruning."""
    best_score = -float('inf')
    best_move = None
    
    for r, c in get_valid_moves(board):
        board[r][c] = 1
        score = minimax(board, 0, -float('inf'), float('inf'), False)
        board[r][c] = 0
        
        if score > best_score:
            best_score = score
            best_move = (r, c)
    
    if best_move:
        return best_move
    else:
        # Fallback to random move if no valid moves (should not happen)
        return random.choice(get_valid_moves(board))
