
import math

def _check_winner(board):
    # Check rows
    for i in range(3):
        if board[i][0] == board[i][1] == board[i][2] != 0:
            return board[i][0]
    # Check columns
    for j in range(3):
        if board[0][j] == board[1][j] == board[2][j] != 0:
            return board[0][j]
    # Check diagonals
    if board[0][0] == board[1][1] == board[2][2] != 0:
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] != 0:
        return board[0][2]
    # Check draw (full board)
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                return None  # not terminal
    return 0  # draw

def _copy_board(board):
    return [row[:] for row in board]

def _get_empty_cells(board):
    empty = []
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                empty.append((i, j))
    return empty

def _minimax(board, alpha, beta, maximizing):
    winner = _check_winner(board)
    if winner is not None:
        return winner  # 1, -1, or 0 for draw
    if maximizing:
        max_eval = -math.inf
        for i, j in _get_empty_cells(board):
            new_board = _copy_board(board)
            new_board[i][j] = 1
            eval_ = _minimax(new_board, alpha, beta, False)
            max_eval = max(max_eval, eval_)
            alpha = max(alpha, eval_)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = math.inf
        for i, j in _get_empty_cells(board):
            new_board = _copy_board(board)
            new_board[i][j] = -1
            eval_ = _minimax(new_board, alpha, beta, True)
            min_eval = min(min_eval, eval_)
            beta = min(beta, eval_)
            if beta <= alpha:
                break
        return min_eval

def policy(board):
    # Compute the best move for player 1 (represented by 1)
    best_score = -math.inf
    best_move = None
    alpha = -math.inf
    beta = math.inf
    empty_cells = _get_empty_cells(board)
    # If only one empty cell, return it immediately
    if len(empty_cells) == 1:
        return empty_cells[0]
    for i, j in empty_cells:
        new_board = _copy_board(board)
        new_board[i][j] = 1
        # After our move, it's opponent's turn (minimizing)
        score = _minimax(new_board, alpha, beta, False)
        if score > best_score:
            best_score = score
            best_move = (i, j)
        # Update alpha
        alpha = max(alpha, score)
        # If we found a winning move, return it immediately
        if best_score == 1:
            return best_move
        # Prune if alpha >= beta
        if alpha >= beta:
            break
    return best_move
