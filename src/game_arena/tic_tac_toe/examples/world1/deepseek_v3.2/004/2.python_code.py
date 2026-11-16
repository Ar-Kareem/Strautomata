
import sys

def check_winner(board):
    """Return 1 if player 1 wins, -1 if player -1 wins, 0 otherwise."""
    # rows
    for row in board:
        if row[0] == row[1] == row[2] and row[0] != 0:
            return row[0]
    # columns
    for col in range(3):
        if board[0][col] == board[1][col] == board[2][col] and board[0][col] != 0:
            return board[0][col]
    # diagonals
    if board[0][0] == board[1][1] == board[2][2] and board[0][0] != 0:
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] and board[0][2] != 0:
        return board[0][2]
    return 0

def is_full(board):
    for row in board:
        for cell in row:
            if cell == 0:
                return False
    return True

def minimax(board, depth, alpha, beta, maximizing):
    """
    Returns the best score for the current board state.
    maximizing: True if it's player 1's turn, False if opponent's turn.
    """
    winner = check_winner(board)
    if winner != 0:
        # player 1 wins -> +1, opponent wins -> -1
        return winner
    if is_full(board):
        return 0

    if maximizing:
        max_eval = -sys.maxsize
        for r in range(3):
            for c in range(3):
                if board[r][c] == 0:
                    board[r][c] = 1
                    eval = minimax(board, depth + 1, alpha, beta, False)
                    board[r][c] = 0
                    max_eval = max(max_eval, eval)
                    alpha = max(alpha, eval)
                    if beta <= alpha:
                        break
        return max_eval
    else:
        min_eval = sys.maxsize
        for r in range(3):
            for c in range(3):
                if board[r][c] == 0:
                    board[r][c] = -1
                    eval = minimax(board, depth + 1, alpha, beta, True)
                    board[r][c] = 0
                    min_eval = min(min_eval, eval)
                    beta = min(beta, eval)
                    if beta <= alpha:
                        break
        return min_eval

def policy(board):
    """
    Returns the best move (row, col) for player 1 (value 1).
    """
    # If board is empty, return a corner (optimal and fast)
    empty_count = sum(cell == 0 for row in board for cell in row)
    if empty_count == 9:
        return (0, 0)

    best_move = None
    best_score = -sys.maxsize
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                board[r][c] = 1
                score = minimax(board, 0, -sys.maxsize, sys.maxsize, False)
                board[r][c] = 0
                if score > best_score:
                    best_score = score
                    best_move = (r, c)
    return best_move
