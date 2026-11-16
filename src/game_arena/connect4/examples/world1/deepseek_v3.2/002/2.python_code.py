
import numpy as np
from copy import deepcopy

def policy(board: list[list[int]]) -> int:
    """Return the best column to play in Connect 4."""
    # Convert to numpy for easier manipulation
    board_array = np.array(board, dtype=int)
    
    # Check for immediate win
    for col in range(7):
        if is_valid_move(board_array, col):
            new_board = make_move(board_array, col, 1)
            if check_winner(new_board, 1):
                return col
    
    # Check for immediate block (opponent about to win)
    for col in range(7):
        if is_valid_move(board_array, col):
            new_board = make_move(board_array, col, -1)
            if check_winner(new_board, -1):
                return col
    
    # Use minimax with alpha-beta pruning to find best move
    depth = 5  # Search depth
    best_move = 3  # Default to center column
    best_score = float('-inf')
    
    valid_moves = get_valid_moves(board_array)
    
    # Order moves: center first for better pruning
    move_order = sorted(valid_moves, key=lambda x: abs(x - 3))
    
    for col in move_order:
        new_board = make_move(board_array, col, 1)
        score = minimax(new_board, depth - 1, float('-inf'), float('inf'), False)
        
        if score > best_score:
            best_score = score
            best_move = col
    
    return best_move


def is_valid_move(board: np.ndarray, col: int) -> bool:
    """Check if a column has an empty space."""
    return board[0, col] == 0


def make_move(board: np.ndarray, col: int, player: int) -> np.ndarray:
    """Return a new board with the move made."""
    new_board = board.copy()
    for row in range(5, -1, -1):  # From bottom to top
        if new_board[row, col] == 0:
            new_board[row, col] = player
            break
    return new_board


def check_winner(board: np.ndarray, player: int) -> bool:
    """Check if the given player has won."""
    # Check horizontal
    for row in range(6):
        for col in range(4):
            if all(board[row, col + i] == player for i in range(4)):
                return True
    
    # Check vertical
    for row in range(3):
        for col in range(7):
            if all(board[row + i, col] == player for i in range(4)):
                return True
    
    # Check diagonal (down-right)
    for row in range(3):
        for col in range(4):
            if all(board[row + i, col + i] == player for i in range(4)):
                return True
    
    # Check diagonal (up-right)
    for row in range(3, 6):
        for col in range(4):
            if all(board[row - i, col + i] == player for i in range(4)):
                return True
    
    return False


def get_valid_moves(board: np.ndarray) -> list:
    """Get list of columns with available moves."""
    return [col for col in range(7) if is_valid_move(board, col)]


def evaluate_board(board: np.ndarray) -> int:
    """Evaluate the board from the perspective of player 1."""
    score = 0
    
    # Center column preference
    center_array = board[:, 3]
    score += np.sum(center_array == 1) * 3
    score -= np.sum(center_array == -1) * 3
    
    # Check all possible 4-in-a-row lines
    for player in [1, -1]:
        player_multiplier = 1 if player == 1 else -1
        
        # Horizontal
        for row in range(6):
            for col in range(4):
                window = board[row, col:col+4]
                score += evaluate_window(window, player) * player_multiplier
        
        # Vertical
        for row in range(3):
            for col in range(7):
                window = board[row:row+4, col]
                score += evaluate_window(window, player) * player_multiplier
        
        # Diagonal (down-right)
        for row in range(3):
            for col in range(4):
                window = [board[row+i, col+i] for i in range(4)]
                score += evaluate_window(window, player) * player_multiplier
        
        # Diagonal (up-right)
        for row in range(3, 6):
            for col in range(4):
                window = [board[row-i, col+i] for i in range(4)]
                score += evaluate_window(window, player) * player_multiplier
    
    return score


def evaluate_window(window, player):
    """Evaluate a 4-cell window."""
    opponent = -player
    my_count = np.sum(window == player)
    opp_count = np.sum(window == opponent)
    empty_count = np.sum(window == 0)
    
    if my_count == 4:
        return 100
    elif opp_count == 4:
        return -100
    elif my_count == 3 and empty_count == 1:
        return 5
    elif opp_count == 3 and empty_count == 1:
        return -5
    elif my_count == 2 and empty_count == 2:
        return 2
    elif opp_count == 2 and empty_count == 2:
        return -2
    return 0


def minimax(board: np.ndarray, depth: int, alpha: float, beta: float, maximizing_player: bool) -> float:
    """Minimax algorithm with alpha-beta pruning."""
    # Check terminal states
    if check_winner(board, 1):
        return 1000 + depth  # Prefer quicker wins
    if check_winner(board, -1):
        return -1000 - depth  # Prefer slower losses
    
    if depth == 0:
        return evaluate_board(board)
    
    valid_moves = get_valid_moves(board)
    if not valid_moves:  # Board is full
        return 0
    
    if maximizing_player:
        max_eval = float('-inf')
        for col in valid_moves:
            new_board = make_move(board, col, 1)
            eval_score = minimax(new_board, depth - 1, alpha, beta, False)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for col in valid_moves:
            new_board = make_move(board, col, -1)
            eval_score = minimax(new_board, depth - 1, alpha, beta, True)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval
