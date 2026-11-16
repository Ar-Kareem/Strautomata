
import sys

def check_winner(board):
    """Return 1 if player 1 wins, -1 if player -1 wins, 0 if draw, None if game continues."""
    # Check rows
    for r in range(3):
        if board[r][0] == board[r][1] == board[r][2] != 0:
            return board[r][0]
    # Check columns
    for c in range(3):
        if board[0][c] == board[1][c] == board[2][c] != 0:
            return board[0][c]
    # Check diagonals
    if board[0][0] == board[1][1] == board[2][2] != 0:
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] != 0:
        return board[0][2]
    # Check if board is full
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                return None
    return 0

def get_empty_cells(board):
    return [(r, c) for r in range(3) for c in range(3) if board[r][c] == 0]

def minimax(board, alpha, beta, maximizing_player):
    winner = check_winner(board)
    if winner is not None:
        return winner
    
    if maximizing_player:
        max_eval = -sys.maxsize
        for r, c in get_empty_cells(board):
            board[r][c] = 1
            eval = minimax(board, alpha, beta, False)
            board[r][c] = 0
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = sys.maxsize
        for r, c in get_empty_cells(board):
            board[r][c] = -1
            eval = minimax(board, alpha, beta, True)
            board[r][c] = 0
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval

def policy(board: list[list[int]]) -> tuple[int, int]:
    # First, check if there's an immediate winning move for us
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                board[r][c] = 1
                if check_winner(board) == 1:
                    board[r][c] = 0
                    return (r, c)
                board[r][c] = 0
    
    # Then, check if opponent has a winning move (block it)
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                board[r][c] = -1
                if check_winner(board) == -1:
                    board[r][c] = 0
                    return (r, c)
                board[r][c] = 0
    
    # Otherwise, use minimax to choose the best move
    best_score = -sys.maxsize
    best_move = None
    empty_cells = get_empty_cells(board)
    for r, c in empty_cells:
        board[r][c] = 1
        score = minimax(board, -sys.maxsize, sys.maxsize, False)
        board[r][c] = 0
        if score > best_score:
            best_score = score
            best_move = (r, c)
    
    # In the unlikely case best_move is None (board full), return any empty cell
    if best_move is None:
        # Should not happen, but fallback
        for r in range(3):
            for c in range(3):
                if board[r][c] == 0:
                    return (r, c)
        return (0, 0)  # fallback
    return best_move
