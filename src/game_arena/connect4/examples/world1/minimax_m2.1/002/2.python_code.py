
import math
from typing import List, Tuple

def policy(board: List[List[int]]) -> int:
    """
    Connect 4 AI Policy
    Returns the column index (0-6) for the next move
    """
    
    # Get valid moves (columns that aren't full)
    valid_moves = get_valid_moves(board)
    if not valid_moves:
        return 0  # No valid moves (shouldn't happen in valid game states)
    
    # Check for immediate winning moves
    for col in valid_moves:
        if is_winning_move(board, col, 1):
            return col
    
    # Check if opponent has winning move next turn - must block
    opponent_win_col = None
    for col in valid_moves:
        if is_winning_move(board, col, -1):
            opponent_win_col = col
            break
    
    # Use minimax with alpha-beta pruning to find best move
    depth = 4  # Search depth
    
    # Move ordering: try center columns first for better pruning
    sorted_moves = sorted(valid_moves, key=lambda x: abs(3 - x))
    
    best_score = -math.inf
    best_move = sorted_moves[0]
    alpha = -math.inf
    beta = math.inf
    
    for col in sorted_moves:
        # Make move
        row = get_next_open_row(board, col)
        new_board = [row[:] for row in board]
        new_board[row][col] = 1
        
        # Recursive search
        score = minimax(new_board, depth - 1, alpha, beta, False, col)
        
        # Undo move (implicit by using new_board)
        
        if score > best_score:
            best_score = score
            best_move = col
        
        alpha = max(alpha, score)
    
    # If opponent has winning move and we didn't find better, block it
    if opponent_win_col is not None and best_move != opponent_win_col:
        # Check if our best move also blocks or is better
        row = get_next_open_row(board, best_move)
        test_board = [r[:] for r in board]
        test_board[row][best_move] = 1
        
        # If our best move doesn't block and isn't winning, block opponent
        if not is_winning_move(test_board, opponent_win_col, -1):
            return opponent_win_col
    
    return best_move


def minimax(board: List[List[int]], depth: int, alpha: float, beta: float, 
            maximizing_player: bool, last_col: int) -> float:
    """
    Minimax algorithm with alpha-beta pruning
    """
    valid_moves = get_valid_moves(board)
    
    # Terminal states
    if depth == 0 or len(valid_moves) == 0:
        return evaluate_position(board)
    
    # Check for immediate win/loss
    if is_winning_move(board, last_col, 1 if maximizing_player else -1):
        return 10000000 if maximizing_player else -10000000
    
    if maximizing_player:
        max_eval = -math.inf
        for col in valid_moves:
            row = get_next_open_row(board, col)
            new_board = [r[:] for r in board]
            new_board[row][col] = 1
            
            eval_score = minimax(new_board, depth - 1, alpha, beta, False, col)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            
            if beta <= alpha:
                break
        
        return max_eval
    else:
        min_eval = math.inf
        for col in valid_moves:
            row = get_next_open_row(board, col)
            new_board = [r[:] for r in board]
            new_board[row][col] = -1
            
            eval_score = minimax(new_board, depth - 1, alpha, beta, True, col)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            
            if beta <= alpha:
                break
        
        return min_eval


def evaluate_position(board: List[List[int]]) -> float:
    """
    Evaluate the board position from current player's perspective
    Returns a score (higher is better for current player)
    """
    score = 0
    
    # Center column preference
    center_array = [board[row][3] for row in range(6)]
    center_count = center_array.count(1)
    score += center_count * 3
    
    # Evaluate all windows of 4 cells
    for row in range(6):
        for col in range(7 - 3):
            # Horizontal windows
            if col + 3 < 7:
                score += evaluate_window([board[row][col + i] for i in range(4)])
    
    for row in range(6 - 3):
        for col in range(7):
            # Vertical windows
            score += evaluate_window([board[row + i][col] for i in range(4)])
    
    for row in range(6 - 3):
        for col in range(7 - 3):
            # Positive diagonal windows
            score += evaluate_window([board[row + i][col + i] for i in range(4)])
            # Negative diagonal windows
            score += evaluate_window([board[row + i][col + 3 - i] for i in range(4)])
    
    return score


def evaluate_window(window: List[int]) -> float:
    """
    Evaluate a window of 4 cells
    """
    score = 0
    piece_count = window.count(1)
    empty_count = window.count(0)
    opponent_count = window.count(-1)
    
    # Current player opportunities
    if piece_count == 4:
        score += 100
    elif piece_count == 3 and empty_count == 1:
        score += 5
    elif piece_count == 2 and empty_count == 2:
        score += 2
    
    # Opponent threats (negative score)
    if opponent_count == 3 and empty_count == 1:
        score -= 4
    
    return score


def get_valid_moves(board: List[List[int]]) -> List[int]:
    """
    Get list of valid column moves (columns that aren't full)
    """
    valid_moves = []
    for col in range(7):
        if board[0][col] == 0:  # Top row is empty
            valid_moves.append(col)
    return valid_moves


def get_next_open_row(board: List[List[int]], col: int) -> int:
    """
    Find the lowest empty row in a column
    """
    for row in range(5, -1, -1):
        if board[row][col] == 0:
            return row
    return -1  # Column is full


def is_winning_move(board: List[List[int]], col: int, piece: int) -> bool:
    """
    Check if placing a piece in the column wins the game
    """
    if col < 0 or col >= 7:
        return False
    
    # Check if column is valid
    if board[0][col] != 0:
        return False
    
    # Make temporary move
    row = get_next_open_row(board, col)
    temp_board = [r[:] for r in board]
    temp_board[row][col] = piece
    
    # Check all directions for 4 in a row
    return (check_direction(temp_board, row, col, 1, 0) or  # Horizontal
            check_direction(temp_board, row, col, 0, 1) or  # Vertical
            check_direction(temp_board, row, col, 1, 1) or  # Positive diagonal
            check_direction(temp_board, row, col, 1, -1))   # Negative diagonal


def check_direction(board: List[List[int]], row: int, col: int, 
                   row_dir: int, col_dir: int) -> bool:
    """
    Check if there's a 4-in-a-row starting from (row, col) in given direction
    """
    piece = board[row][col]
    if piece == 0:
        return False
    
    count = 1
    
    # Check positive direction
    r, c = row + row_dir, col + col_dir
    while (0 <= r < 6 and 0 <= c < 7 and 
           board[r][c] == piece):
        count += 1
        r += row_dir
        c += col_dir
    
    # Check negative direction
    r, c = row - row_dir, col - col_dir
    while (0 <= r < 6 and 0 <= c < 7 and 
           board[r][c] == piece):
        count += 1
        r -= row_dir
        c -= col_dir
    
    return count >= 4
