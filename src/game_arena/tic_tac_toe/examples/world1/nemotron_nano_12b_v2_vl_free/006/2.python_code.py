
import math

def has_winner(board, player):
    # Check rows
    for row in board:
        if row[0] == row[1] == row[2] == player:
            return True
    # Check columns
    for col in range(3):
        if board[0][col] == board[1][col] == board[2][col] == player:
            return True
    # Check diagonals
    if board[0][0] == board[1][1] == board[2][2] == player:
        return True
    if board[0][2] == board[1][1] == board[2][0] == player:
        return True
    return False

def is_board_full(board):
    for row in board:
        if 0 in row:
            return False
    return True

def move_priority(move):
    r, c = move
    if r == 1 and c == 1:
        return 0  # Center cell
    elif (r in (0, 2) and c in (0, 2)):
        return 1  # Corners
    else:
        return 2  # Edge cells

def minimax(board, alpha, beta, is_maximizing):
    # Check if current player has won
    if has_winner(board, 1):
        return 10
    if has_winner(board, -1):
        return -10
    # Check for draw
    if is_board_full(board):
        return 0

    if is_maximizing:
        max_eval = -math.inf
        for r in range(3):
            for c in range(3):
                if board[r][c] == 0:
                    new_board = [row.copy() for row in board]
                    new_board[r][c] = 1
                    current_eval = minimax(new_board, alpha, beta, False)
                    max_eval = max(max_eval, current_eval)
                    alpha = max(alpha, current_eval)
                    if beta <= alpha:
                        break
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = math.inf
        for r in range(3):
            for c in range(3):
                if board[r][c] == 0:
                    new_board = [row.copy() for row in board]
                    new_board[r][c] = -1
                    current_eval = minimax(new_board, alpha, beta, True)
                    min_eval = min(min_eval, current_eval)
                    beta = min(beta, current_eval)
                    if beta <= alpha:
                        break
            if beta <= alpha:
                break
        return min_eval

def policy(board):
    available_moves = [(r, c) for r in range(3) for c in range(3) if board[r][c] == 0]
    if not available_moves:
        return (0, 0)  # Handle edge case, though shouldn't occur

    # Check for immediate win
    for move in available_moves:
        temp = [row.copy() for row in board]
        temp[move[0]][move[1]] = 1
        if has_winner(temp, 1):
            return move

    # Evaluate all possible moves using minimax with alpha-beta pruning
    best_eval = -math.inf
    best_move = None
    for move in available_moves:
        temp_board = [row.copy() for row in board]
        temp_board[move[0]][move[1]] = 1
        current_eval = minimax(temp_board, -math.inf, math.inf, False)
        if current_eval > best_eval:
            best_eval = current_eval
            best_move = move

    return best_move
