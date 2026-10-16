
import numpy as np
from typing import List, Tuple, Optional

def policy(board: List[List[int]]) -> int:
    """Return the best column to play in Connect 4."""
    
    # Convert to numpy for easier manipulation
    board_np = np.array(board, dtype=int)
    rows, cols = 6, 7
    
    # 1. Check for immediate winning move
    win_move = find_winning_move(board_np, 1)
    if win_move is not None:
        return win_move
    
    # 2. Check if opponent can win next move and block
    block_move = find_winning_move(board_np, -1)
    if block_move is not None:
        return block_move
    
    # 3. Use minimax with alpha-beta pruning for deeper lookahead
    depth = 3  # Adjust based on time constraints
    best_col = -1
    best_score = -float('inf')
    
    # Get all legal moves
    legal_moves = [c for c in range(cols) if board_np[0, c] == 0]
    
    # Sort moves by center preference for better pruning
    legal_moves.sort(key=lambda x: abs(x - 3))
    
    for col in legal_moves:
        # Make the move
        row = get_drop_row(board_np, col)
        board_np[row, col] = 1
        
        # Evaluate this position
        score = minimax(board_np, depth-1, -float('inf'), float('inf'), False, -1)
        
        # Undo the move
        board_np[row, col] = 0
        
        if score > best_score:
            best_score = score
            best_col = col
    
    # If minimax didn't find a move (shouldn't happen), use heuristic fallback
    if best_col == -1 or board_np[0, best_col] != 0:
        best_col = heuristic_fallback(board_np)
    
    return best_col


def find_winning_move(board: np.ndarray, player: int) -> Optional[int]:
    """Return column where player can win immediately, or None."""
    rows, cols = board.shape
    
    for col in range(cols):
        if board[0, col] != 0:
            continue
            
        row = get_drop_row(board, col)
        
        # Temporarily place the disc
        board[row, col] = player
        
        # Check if this creates a win
        if check_win(board, row, col):
            board[row, col] = 0  # Undo
            return col
        
        # Undo
        board[row, col] = 0
    
    return None


def get_drop_row(board: np.ndarray, col: int) -> int:
    """Return the row where a disc would drop in given column."""
    rows = board.shape[0]
    for row in range(rows-1, -1, -1):
        if board[row, col] == 0:
            return row
    return -1  # Column is full


def check_win(board: np.ndarray, row: int, col: int) -> bool:
    """Check if the last move at (row, col) is a winning move."""
    player = board[row, col]
    if player == 0:
        return False
    
    rows, cols = board.shape
    
    # Check horizontal
    for c in range(max(0, col-3), min(cols-3, col+1)):
        if all(board[row, c+i] == player for i in range(4)):
            return True
    
    # Check vertical
    for r in range(max(0, row-3), min(rows-3, row+1)):
        if all(board[r+i, col] == player for i in range(4)):
            return True
    
    # Check diagonal (down-right)
    for offset in range(-3, 1):
        r, c = row + offset, col + offset
        if 0 <= r <= rows-4 and 0 <= c <= cols-4:
            if all(board[r+i, c+i] == player for i in range(4)):
                return True
    
    # Check diagonal (down-left)
    for offset in range(-3, 1):
        r, c = row + offset, col - offset
        if 0 <= r <= rows-4 and 0 <= c <= cols-4:
            if all(board[r+i, c-i] == player for i in range(4)):
                return True
    
    return False


def evaluate_position(board: np.ndarray, player: int) -> float:
    """Evaluate the board position for the given player."""
    if player == 1:
        opponent = -1
    else:
        opponent = 1
    
    rows, cols = board.shape
    score = 0
    
    # Center control bonus
    center_col = cols // 2
    for col in [center_col-1, center_col, center_col+1]:
        for row in range(rows):
            if board[row, col] == player:
                score += 3
            elif board[row, col] == opponent:
                score -= 3
    
    # Evaluate all possible 4-in-a-row windows
    for r in range(rows):
        for c in range(cols):
            # Horizontal window
            if c <= cols - 4:
                window = board[r, c:c+4]
                score += evaluate_window(window, player)
            
            # Vertical window
            if r <= rows - 4:
                window = board[r:r+4, c]
                score += evaluate_window(window, player)
            
            # Diagonal down-right
            if r <= rows - 4 and c <= cols - 4:
                window = [board[r+i, c+i] for i in range(4)]
                score += evaluate_window(window, player)
            
            # Diagonal down-left
            if r <= rows - 4 and c >= 3:
                window = [board[r+i, c-i] for i in range(4)]
                score += evaluate_window(window, player)
    
    return score


def evaluate_window(window, player: int) -> float:
    """Evaluate a 4-cell window."""
    if player == 1:
        opponent = -1
    else:
        opponent = 1
    
    player_count = np.sum(window == player)
    opponent_count = np.sum(window == opponent)
    empty_count = 4 - player_count - opponent_count
    
    if player_count == 4:
        return 10000
    elif opponent_count == 4:
        return -10000
    elif player_count == 3 and empty_count == 1:
        return 500
    elif opponent_count == 3 and empty_count == 1:
        return -1000  # Higher penalty for opponent's threat
    elif player_count == 2 and empty_count == 2:
        return 10
    elif opponent_count == 2 and empty_count == 2:
        return -5
    elif player_count == 1 and empty_count == 3:
        return 1
    else:
        return 0


def minimax(board: np.ndarray, depth: int, alpha: float, beta: float, 
            maximizing: bool, player: int) -> float:
    """Minimax algorithm with alpha-beta pruning."""
    rows, cols = board.shape
    
    # Terminal conditions
    # Check if current player (based on maximizing) has won
    current_player = 1 if maximizing else -1
    
    # Check all positions for a win (simplified for speed)
    if check_any_win(board, current_player):
        return 10000 if maximizing else -10000
    
    if depth == 0:
        return evaluate_position(board, 1)  # Evaluate from perspective of player 1
    
    if maximizing:
        max_eval = -float('inf')
        for col in range(cols):
            if board[0, col] != 0:
                continue
                
            row = get_drop_row(board, col)
            if row == -1:
                continue
                
            board[row, col] = 1
            eval_score = minimax(board, depth-1, alpha, beta, False, -1)
            board[row, col] = 0
            
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for col in range(cols):
            if board[0, col] != 0:
                continue
                
            row = get_drop_row(board, col)
            if row == -1:
                continue
                
            board[row, col] = -1
            eval_score = minimax(board, depth-1, alpha, beta, True, 1)
            board[row, col] = 0
            
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval


def check_any_win(board: np.ndarray, player: int) -> bool:
    """Check if the given player has won anywhere on the board."""
    rows, cols = board.shape
    
    # Check horizontally
    for r in range(rows):
        for c in range(cols-3):
            if all(board[r, c+i] == player for i in range(4)):
                return True
    
    # Check vertically
    for r in range(rows-3):
        for c in range(cols):
            if all(board[r+i, c] == player for i in range(4)):
                return True
    
    # Check diagonally (down-right)
    for r in range(rows-3):
        for c in range(cols-3):
            if all(board[r+i, c+i] == player for i in range(4)):
                return True
    
    # Check diagonally (down-left)
    for r in range(rows-3):
        for c in range(3, cols):
            if all(board[r+i, c-i] == player for i in range(4)):
                return True
    
    return False


def heuristic_fallback(board: np.ndarray) -> int:
    """Fallback heuristic when no clear move found."""
    rows, cols = board.shape
    
    # Priority order: center columns first
    center_cols = [3, 2, 4, 1, 5, 0, 6]
    
    for col in center_cols:
        if board[0, col] == 0:
            return col
    
    # Last resort: first available column
    for col in range(cols):
        if board[0, col] == 0:
            return col
    
    return 3  # Default to center if all else fails
