
import sys
import random

# ----------------------------------------------------------------------
# Constants
WIN_SCORE = 1000000
THREE_SCORE = 1000
TWO_SCORE = 100

# ----------------------------------------------------------------------
# Helper functions for board manipulation
def get_valid_locations(board):
    """Return list of column indices that are not full (top row is empty)."""
    return [c for c in range(7) if board[0][c] == 0]

def get_next_open_row(board, col):
    """Return the lowest empty row in the given column, or None if full."""
    for r in range(5, -1, -1):
        if board[r][col] == 0:
            return r
    return None

def drop_piece(board, row, col, piece):
    """Create a new board with piece placed at (row, col)."""
    new_board = [r[:] for r in board]
    new_board[row][col] = piece
    return new_board

def check_win(board, piece):
    """Return True if piece has a four‑in‑a‑row on the board."""
    # Horizontal
    for r in range(6):
        for c in range(7 - 3):
            if all(board[r][c + i] == piece for i in range(4)):
                return True
    # Vertical
    for r in range(6 - 3):
        for c in range(7):
            if all(board[r + i][c] == piece for i in range(4)):
                return True
    # Diagonal down‑right
    for r in range(6 - 3):
        for c in range(7 - 3):
            if all(board[r + i][c + i] == piece for i in range(4)):
                return True
    # Diagonal up‑right
    for r in range(3, 6):
        for c in range(7 - 3):
            if all(board[r - i][c + i] == piece for i in range(4)):
                return True
    return False

def is_win_move(board, col, piece):
    """Check if dropping piece in column col results in a win."""
    row = get_next_open_row(board, col)
    if row is None:
        return False
    b = drop_piece(board, row, col, piece)
    return check_win(b, piece)

# ----------------------------------------------------------------------
# Heuristic evaluation
def evaluate_window(window, piece):
    """Score a window of four cells for the given piece."""
    opp_piece = -piece
    cnt_piece = window.count(piece)
    cnt_opp = window.count(opp_piece)
    cnt_empty = window.count(0)

    score = 0
    if cnt_piece == 4:
        score += WIN_SCORE
    elif cnt_piece == 3 and cnt_empty == 1:
        score += THREE_SCORE
    elif cnt_piece == 2 and cnt_empty == 2:
        score += TWO_SCORE

    if cnt_opp == 4:
        score -= WIN_SCORE
    elif cnt_opp == 3 and cnt_empty == 1:
        score -= THREE_SCORE
    elif cnt_opp == 2 and cnt_empty == 2:
        score -= TWO_SCORE

    return score

def evaluate_board(board, piece):
    """Compute the heuristic score of the whole board for `piece`."""
    score = 0
    # Horizontal
    for r in range(6):
        for c in range(7 - 3):
            window = [board[r][c + i] for i in range(4)]
            score += evaluate_window(window, piece)
    # Vertical
    for r in range(6 - 3):
        for c in range(7):
            window = [board[r + i][c] for i in range(4)]
            score += evaluate_window(window, piece)
    # Diagonal down‑right
    for r in range(6 - 3):
        for c in range(7 - 3):
            window = [board[r + i][c + i] for i in range(4)]
            score += evaluate_window(window, piece)
    # Diagonal up‑right
    for r in range(3, 6):
        for c in range(7 - 3):
            window = [board[r - i][c + i] for i in range(4)]
            score += evaluate_window(window, piece)
    return score

# ----------------------------------------------------------------------
# Move ordering (central columns are better)
PREFERRED_ORDER = [3, 2, 4, 1, 5, 0, 6]

def order_moves(moves):
    """Return a sorted list of moves according to preferred order."""
    return sorted(moves, key=lambda c: PREFERRED_ORDER.index(c) if c in PREFERRED_ORDER else 7)

# ----------------------------------------------------------------------
# Minimax with alpha‑beta pruning
def minimax(board, depth, alpha, beta, maximizing):
    """Recursive minimax returning (score, column)."""
    valid_moves = get_valid_locations(board)

    # Terminal tests
    if check_win(board, 1):
        return WIN_SCORE, None
    if check_win(board, -1):
        return -WIN_SCORE, None
    if depth == 0 or not valid_moves:
        return evaluate_board(board, 1), None

    # Choose piece based on whose turn it is
    piece = 1 if maximizing else -1

    # Order moves to improve pruning
    ordered_moves = order_moves(valid_moves)

    if maximizing:
        value = -float('inf')
        best_col = ordered_moves[0]
        for col in ordered_moves:
            row = get_next_open_row(board, col)
            new_board = drop_piece(board, row, col, piece)
            new_score, _ = minimax(new_board, depth - 1, alpha, beta, False)
            if new_score > value:
                value = new_score
                best_col = col
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value, best_col
    else:
        value = float('inf')
        best_col = ordered_moves[0]
        for col in ordered_moves:
            row = get_next_open_row(board, col)
            new_board = drop_piece(board, row, col, piece)
            new_score, _ = minimax(new_board, depth - 1, alpha, beta, True)
            if new_score < value:
                value = new_score
                best_col = col
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value, best_col

# ----------------------------------------------------------------------
# Main policy function
def policy(board):
    """Return the column index (0‑6) of the next move."""
    # Current player is always piece = 1
    valid_moves = get_valid_locations(board)

    # 1) Immediate win?
    for col in valid_moves:
        if is_win_move(board, col, 1):
            return col

    # 2) Block opponent's immediate win
    for col in valid_moves:
        if is_win_move(board, col, -1):
            return col

    # 3) Run minimax (depth 5 – strong enough within 1 s)
    _, col = minimax(board, depth=5, alpha=-float('inf'), beta=float('inf'), maximizing=True)

    # Fallback (should never happen) – pick any valid column
    if col not in valid_moves:
        col = random.choice(valid_moves)

    return col
