
import sys

# Constants for the board
ROWS = 6
COLS = 7

def get_available_moves(board):
    """Returns a list of column indices that are not full (i.e., top cell is empty)."""
    available = []
    for c in range(COLS):
        if board[0][c] == 0:  # top row (index 0) is empty
            available.append(c)
    return available

def drop_disc(board, col, player):
    """Drops a disc for the player in the given column and updates the board in-place.
       The disc occupies the lowest available cell in the column.
    """
    for r in range(ROWS-1, -1, -1):  # from bottom row to top
        if board[r][col] == 0:
            board[r][col] = player
            return True
    return False  # should not happen for an available move

def check_win(board, player):
    """Checks if the player has four in a row in any direction."""
    # Horizontal
    for r in range(ROWS):
        for c in range(COLS-3):
            if (board[r][c] == player and board[r][c+1] == player and 
                board[r][c+2] == player and board[r][c+3] == player):
                return True
    # Vertical
    for c in range(COLS):
        for r in range(ROWS-3):
            if (board[r][c] == player and board[r+1][c] == player and 
                board[r+2][c] == player and board[r+3][c] == player):
                return True
    # Diagonal down-right
    for r in range(ROWS-3):
        for c in range(COLS-3):
            if (board[r][c] == player and board[r+1][c+1] == player and 
                board[r+2][c+2] == player and board[r+3][c+3] == player):
                return True
    # Diagonal down-left
    for r in range(ROWS-3):
        for c in range(3, COLS):
            if (board[r][c] == player and board[r+1][c-1] == player and 
                board[r+2][c-2] == player and board[r+3][c-3] == player):
                return True
    return False

def evaluate_board(board):
    """Evaluates the board from the perspective of player 1 (our current player). 
       Returns a positive score if favorable to us, negative if favorable to opponent.
    """
    score = 0
    # Horizontal windows
    for r in range(ROWS):
        for c in range(COLS-3):
            window = board[r][c:c+4]
            score += evaluate_window(window)
    # Vertical windows
    for c in range(COLS):
        for r in range(ROWS-3):
            window = [board[r+i][c] for i in range(4)]
            score += evaluate_window(window)
    # Diagonal down-right windows
    for r in range(ROWS-3):
        for c in range(COLS-3):
            window = [board[r+i][c+i] for i in range(4)]
            score += evaluate_window(window)
    # Diagonal down-left windows
    for r in range(ROWS-3):
        for c in range(3, COLS):
            window = [board[r+i][c-i] for i in range(4)]
            score += evaluate_window(window)
    return score

def evaluate_window(window):
    """Evaluates a single 4-cell window. 
       Returns a positive score if favorable to player 1, negative if favorable to player -1.
    """
    # If the window has both players' discs, it contributes 0.
    if 1 in window and -1 in window:
        return 0
    
    count1 = window.count(1)
    count_minus1 = window.count(-1)
    
    # If the window is empty, skip.
    if count1 == 0 and count_minus1 == 0:
        return 0
    
    # For player 1 (us) positive scores
    if count1 > 0 and count_minus1 == 0:
        if count1 == 4:
            return 100000
        elif count1 == 3:
            return 1000
        elif count1 == 2:
            return 100
        elif count1 == 1:
            return 10
    
    # For opponent (player -1) negative scores
    if count_minus1 > 0 and count1 == 0:
        if count_minus1 == 4:
            return -100000
        elif count_minus1 == 3:
            return -1000
        elif count_minus1 == 2:
            return -100
        elif count_minus1 == 1:
            return -10
    
    return 0

def minimax(board, depth, alpha, beta, maximizing_player):
    """Minimax with alpha-beta pruning. 
       Returns (best_column, score) for the current state.
    """
    # Base case: terminal state or depth 0
    if depth == 0 or (check_win(board, 1) or check_win(board, -1) or not get_available_moves(board)):
        return (None, evaluate_board(board))
    
    available_moves = get_available_moves(board)
    if not available_moves:
        return (None, evaluate_board(board))
    
    # Order moves by center preference: [3,4,2,5,1,6,0]
    move_order = [3,4,2,5,1,6,0]
    # We sort the available_moves by their index in move_order (if present) then by column index (for those not in move_order)
    ordered_moves = sorted(available_moves, key=lambda x: move_order.index(x) if x in move_order else 10)
    
    if maximizing_player:
        best_score = -10**9
        best_move = None
        for col in ordered_moves:
            # Create a new board state for this move
            new_board = [row[:] for row in board]  # deep copy
            drop_disc(new_board, col, 1)
            _, score = minimax(new_board, depth-1, alpha, beta, False)
            if score > best_score:
                best_score = score
                best_move = col
            alpha = max(alpha, score)
            if beta <= alpha:
                break  # prune
        return best_move, best_score
    else:
        best_score = 10**9
        best_move = None
        for col in ordered_moves:
            new_board = [row[:] for row in board]
            drop_disc(new_board, col, -1)
            _, score = minimax(new_board, depth-1, alpha, beta, True)
            if score < best_score:
                best_score = score
                best_move = col
            beta = min(beta, score)
            if beta <= alpha:
                break  # prune
        return best_move, best_score

def policy(board):
    """The policy function that selects a column to drop the disc."""
    # We are the maximizing player (1)
    best_move, _ = minimax(board, depth=4, alpha=-10**9, beta=10**9, maximizing_player=True)
    # If best_move is None, we have a problem: but the problem says we must return a column that is not full.
    if best_move is None:
        # Fallback: return the first available move
        available = get_available_moves(board)
        if available:
            return available[0]
        else:
            return 0  # This should not happen if the board is not full.
    return best_move
