
import math
import random
from typing import List, Tuple

ROWS = 6
COLS = 7

def policy(board: List[List[int]]) -> int:
    # Ensure we always return a legal move
    valid_moves = get_valid_moves(board)
    if not valid_moves:
        return 0

    # Immediate win
    for col in valid_moves:
        row = get_next_open_row(board, col)
        if row is not None:
            b_copy = [r[:] for r in board]
            drop_piece(b_copy, row, col, 1)
            if winning_move(b_copy, 1):
                return col

    # Immediate block
    for col in valid_moves:
        row = get_next_open_row(board, col)
        if row is not None:
            b_copy = [r[:] for r in board]
            drop_piece(b_copy, row, col, -1)
            if winning_move(b_copy, -1):
                return col

    # Minimax with alpha-beta
    depth = 4
    col, _ = minimax(board, depth, -math.inf, math.inf, True)
    if col is None or col not in valid_moves:
        return random.choice(valid_moves)
    return col

def get_valid_moves(board):
    return [c for c in range(COLS) if board[0][c] == 0]

def get_next_open_row(board, col):
    for r in range(ROWS-1, -1, -1):
        if board[r][col] == 0:
            return r
    return None

def drop_piece(board, row, col, piece):
    board[row][col] = piece

def winning_move(board, piece):
    # Horizontal
    for r in range(ROWS):
        for c in range(COLS-3):
            if all(board[r][c+i] == piece for i in range(4)):
                return True
    # Vertical
    for c in range(COLS):
        for r in range(ROWS-3):
            if all(board[r+i][c] == piece for i in range(4)):
                return True
    # Positive diagonal
    for r in range(ROWS-3):
        for c in range(COLS-3):
            if all(board[r+i][c+i] == piece for i in range(4)):
                return True
    # Negative diagonal
    for r in range(3, ROWS):
        for c in range(COLS-3):
            if all(board[r-i][c+i] == piece for i in range(4)):
                return True
    return False

def score_window(window, piece):
    score = 0
    opp_piece = -piece
    if window.count(piece) == 4:
        score += 100
    elif window.count(piece) == 3 and window.count(0) == 1:
        score += 5
    elif window.count(piece) == 2 and window.count(0) == 2:
        score += 2
    if window.count(opp_piece) == 3 and window.count(0) == 1:
        score -= 4
    return score

def score_position(board, piece):
    score = 0

    # Center column preference
    center = [board[r][COLS//2] for r in range(ROWS)]
    score += center.count(piece) * 3

    # Horizontal
    for r in range(ROWS):
        row = board[r]
        for c in range(COLS-3):
            window = row[c:c+4]
            score += score_window(window, piece)

    # Vertical
    for c in range(COLS):
        col = [board[r][c] for r in range(ROWS)]
        for r in range(ROWS-3):
            window = col[r:r+4]
            score += score_window(window, piece)

    # Positive diagonal
    for r in range(ROWS-3):
        for c in range(COLS-3):
            window = [board[r+i][c+i] for i in range(4)]
            score += score_window(window, piece)

    # Negative diagonal
    for r in range(ROWS-3):
        for c in range(COLS-3):
            window = [board[r+3-i][c+i] for i in range(4)]
            score += score_window(window, piece)

    return score

def is_terminal(board):
    return winning_move(board, 1) or winning_move(board, -1) or len(get_valid_moves(board)) == 0

def minimax(board, depth, alpha, beta, maximizing_player) -> Tuple[int, float]:
    valid_moves = get_valid_moves(board)
    terminal = is_terminal(board)

    if depth == 0 or terminal:
        if terminal:
            if winning_move(board, 1):
                return None, 1e9
            elif winning_move(board, -1):
                return None, -1e9
            else:
                return None, 0
        else:
            return None, score_position(board, 1)

    if maximizing_player:
        value = -math.inf
        best_col = random.choice(valid_moves)
        for col in valid_moves:
            row = get_next_open_row(board, col)
            if row is None:
                continue
            b_copy = [r[:] for r in board]
            drop_piece(b_copy, row, col, 1)
            new_score = minimax(b_copy, depth-1, alpha, beta, False)[1]
            if new_score > value:
                value = new_score
                best_col = col
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return best_col, value
    else:
        value = math.inf
        best_col = random.choice(valid_moves)
        for col in valid_moves:
            row = get_next_open_row(board, col)
            if row is None:
                continue
            b_copy = [r[:] for r in board]
            drop_piece(b_copy, row, col, -1)
            new_score = minimax(b_copy, depth-1, alpha, beta, True)[1]
            if new_score < value:
                value = new_score
                best_col = col
            beta = min(beta, value)
            if alpha >= beta:
                break
        return best_col, value
