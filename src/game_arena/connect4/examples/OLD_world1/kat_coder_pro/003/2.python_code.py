
import numpy as np
from typing import List, Tuple

def evaluate_window(window: List[int], player: int) -> int:
    """Evaluate a window of 4 connected positions."""
    opponent = -player
    score = 0
    
    # Count pieces in window
    player_count = window.count(player)
    opponent_count = window.count(opponent)
    empty_count = window.count(0)
    
    # Scoring logic
    if opponent_count == 0:
        if player_count == 4:
            score += 100000  # Win
        elif player_count == 3 and empty_count == 1:
            score += 1000    # Threat
        elif player_count == 2 and empty_count == 2:
            score += 100     # Potential threat
        elif player_count == 1 and empty_count == 3:
            score += 10      # Setup
    elif player_count == 0:
        if opponent_count == 4:
            score -= 100000  # Block opponent win
        elif opponent_count == 3 and empty_count == 1:
            score -= 5000    # Block opponent threat
        elif opponent_count == 2 and empty_count == 2:
            score -= 100     # Block potential threat
    elif opponent_count == 3 and empty_count == 1 and player_count == 0:
        score -= 5000        # Block opponent threat
    
    return score

def score_position(board: np.ndarray, player: int) -> int:
    """Calculate score for current board position."""
    score = 0
    rows, cols = board.shape
    
    # Center column control
    center_col = 3
    center_count = np.count_nonzero(board[:, center_col] == player)
    score += center_count * 50
    
    # Horizontal scoring
    for r in range(rows):
        row_array = list(board[r, :])
        for c in range(cols - 3):
            window = row_array[c:c+4]
            score += evaluate_window(window, player)
    
    # Vertical scoring
    for c in range(cols):
        col_array = list(board[:, c])
        for r in range(rows - 3):
            window = col_array[r:r+4]
            score += evaluate_window(window, player)
    
    # Diagonal scoring (positive slope)
    for r in range(rows - 3):
        for c in range(cols - 3):
            window = [board[r+i, c+i] for i in range(4)]
            score += evaluate_window(window, player)
    
    # Diagonal scoring (negative slope)
    for r in range(3, rows):
        for c in range(cols - 3):
            window = [board[r-i, c+i] for i in range(4)]
            score += evaluate_window(window, player)
    
    return score

def is_valid_move(board: np.ndarray, col: int) -> bool:
    """Check if column is not full."""
    return board[0, col] == 0

def get_valid_moves(board: np.ndarray) -> List[int]:
    """Get list of valid columns for next move."""
    return [c for c in range(board.shape[1]) if is_valid_move(board, c)]

def is_winning_move(board: np.ndarray, col: int, player: int) -> bool:
    """Check if dropping a disc in col would result in a win."""
    if not is_valid_move(board, col):
        return False
    
    # Find the lowest empty row in the column
    row = get_next_open_row(board, col)
    if row is None:
        return False
    
    # Temporarily place the piece
    board[row, col] = player
    
    # Check for 4 in a row
    win = check_win(board, player)
    
    # Undo the move
    board[row, col] = 0
    
    return win

def get_next_open_row(board: np.ndarray, col: int) -> int:
    """Get the row index where next piece would land in column."""
    for row in range(board.shape[0]-1, -1, -1):
        if board[row, col] == 0:
            return row
    return None

def check_win(board: np.ndarray, player: int) -> bool:
    """Check if player has won."""
    rows, cols = board.shape
    
    # Check horizontal
    for r in range(rows):
        for c in range(cols-3):
            if all(board[r, c+i] == player for i in range(4)):
                return True
    
    # Check vertical
    for r in range(rows-3):
        for c in range(cols):
            if all(board[r+i, c] == player for i in range(4)):
                return True
    
    # Check positive diagonal
    for r in range(rows-3):
        for c in range(cols-3):
            if all(board[r+i, c+i] == player for i in range(4)):
                return True
    
    # Check negative diagonal
    for r in range(3, rows):
        for c in range(cols-3):
            if all(board[r-i, c+i] == player for i in range(4)):
                return True
    
    return False

def minimax(board: np.ndarray, depth: int, alpha: float, beta: float, 
            maximizing_player: bool, player: int, max_depth: int = 5) -> Tuple[int, int]:
    """Minimax algorithm with alpha-beta pruning."""
    valid_moves = get_valid_moves(board)
    is_terminal = len(valid_moves) == 0 or check_win(board, player) or check_win(board, -player)
    
    if depth == 0 or is_terminal:
        if is_terminal:
            if check_win(board, player):
                return (None, 1000000000000)
            elif check_win(board, -player):
                return (None, -1000000000000)
            else:
                return (None, 0)
        else:
            return (None, score_position(board, player))
    
    if maximizing_player:
        value = -np.inf
        column = valid_moves[0]
        for col in valid_moves:
            row = get_next_open_row(board, col)
            if row is None:
                continue
            board[row, col] = player
            new_score = minimax(board, depth-1, alpha, beta, False, player, max_depth)[1]
            board[row, col] = 0
            if new_score > value:
                value = new_score
                column = col
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return column, value
    else:
        value = np.inf
        column = valid_moves[0]
        for col in valid_moves:
            row = get_next_open_row(board, col)
            if row is None:
                continue
            board[row, col] = -player
            new_score = minimax(board, depth-1, alpha, beta, True, player, max_depth)[1]
            board[row, col] = 0
            if new_score < value:
                value = new_score
                column = col
            beta = min(beta, value)
            if alpha >= beta:
                break
        return column, value

def policy(board: list[list[int]]) -> int:
    """
    Connect 4 policy function.
    
    Args:
        board: 6x7 grid with 0 (empty), 1 (current player), -1 (opponent)
    
    Returns:
        Column index (0-6) to drop the disc
    """
    # Convert to numpy array for easier manipulation
    board_np = np.array(board)
    player = 1  # We are always the current player
    
    # Get valid moves
    valid_moves = get_valid_moves(board_np)
    
    # Check for winning move first
    for col in valid_moves:
        if is_winning_move(board_np, col, player):
            return col
    
    # Check if opponent has winning move and block it
    for col in valid_moves:
        if is_winning_move(board_np, col, -player):
            return col
    
    # Use minimax to find best move
    # Adjust depth based on number of pieces on board
    empty_count = np.count_nonzero(board_np == 0)
    if empty_count > 30:
        depth = 5
    elif empty_count > 20:
        depth = 6
    else:
        depth = 7
    
    # Try to get center column preference
    if 3 in valid_moves:
        preferred_moves = sorted(valid_moves, key=lambda x: -abs(x-3))
    else:
        preferred_moves = valid_moves
    
    # Use iterative deepening for better time management
    best_col = valid_moves[0]
    
    try:
        for d in range(4, depth + 1):
            col, score = minimax(board_np, d, -np.inf, np.inf, True, player, d)
            if col is not None:
                best_col = col
    except:
        # Fallback to first valid move if time runs out
        pass
    
    # Make sure we return a valid move
    if best_col not in valid_moves:
        best_col = valid_moves[0]
    
    return best_col
