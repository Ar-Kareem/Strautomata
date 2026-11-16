
import numpy as np
import random
from typing import List, Tuple

def policy(board: List[List[int]]) -> int:
    """
    Implements a Connect 4 AI using minimax with alpha-beta pruning.
    
    Args:
        board: 6x7 grid representing the game state
               0 = empty, 1 = current player, -1 = opponent
    
    Returns:
        Column index (0-6) where to drop the disc
    """
    
    # Convert to numpy array for easier manipulation
    board_np = np.array(board)
    
    # Check if we can win immediately
    for col in range(7):
        if is_valid_move(board_np, col):
            row = get_next_open_row(board_np, col)
            board_np[row][col] = 1
            if winning_move(board_np, 1):
                return col
            board_np[row][col] = 0  # Reset the move
    
    # Check if opponent can win next turn and block them
    for col in range(7):
        if is_valid_move(board_np, col):
            row = get_next_open_row(board_np, col)
            board_np[row][col] = -1
            if winning_move(board_np, -1):
                return col
            board_np[row][col] = 0  # Reset the move
    
    # Use minimax with a reasonable depth
    try:
        _, col = minimax(board_np, 5, -np.inf, np.inf, True)
        if col is not None and is_valid_move(board_np, col):
            return col
    except:
        pass
    
    # Fallback to center-favoring strategy
    valid_moves = [c for c in range(7) if is_valid_move(board_np, c)]
    if not valid_moves:
        return 0
    
    # Prefer center columns
    center_columns = [3, 2, 4, 1, 5, 0, 6]
    for col in center_columns:
        if col in valid_moves:
            return col
    
    # Last resort: random valid move
    return random.choice(valid_moves)


def is_valid_move(board: np.ndarray, col: int) -> bool:
    """Check if a move is valid (column not full)"""
    return board[0][col] == 0


def get_next_open_row(board: np.ndarray, col: int) -> int:
    """Get the next available row in a column"""
    for r in range(5, -1, -1):
        if board[r][col] == 0:
            return r
    return -1


def winning_move(board: np.ndarray, piece: int) -> bool:
    """Check if the given piece has a winning position"""
    # Check horizontal locations
    for c in range(4):
        for r in range(6):
            if (board[r][c] == piece and 
                board[r][c+1] == piece and 
                board[r][c+2] == piece and 
                board[r][c+3] == piece):
                return True

    # Check vertical locations
    for c in range(7):
        for r in range(3):
            if (board[r][c] == piece and 
                board[r+1][c] == piece and 
                board[r+2][c] == piece and 
                board[r+3][c] == piece):
                return True

    # Check positively sloped diagonals
    for c in range(4):
        for r in range(3):
            if (board[r][c] == piece and 
                board[r+1][c+1] == piece and 
                board[r+2][c+2] == piece and 
                board[r+3][c+3] == piece):
                return True

    # Check negatively sloped diagonals
    for c in range(4):
        for r in range(3, 6):
            if (board[r][c] == piece and 
                board[r-1][c+1] == piece and 
                board[r-2][c+2] == piece and 
                board[r-3][c+3] == piece):
                return True

    return False


def evaluate_window(window: np.ndarray, piece: int) -> int:
    """Evaluate a window of 4 positions"""
    score = 0
    opp_piece = -1 if piece == 1 else 1

    if list(window).count(piece) == 4:
        score += 100
    elif list(window).count(piece) == 3 and list(window).count(0) == 1:
        score += 5
    elif list(window).count(piece) == 2 and list(window).count(0) == 2:
        score += 2

    if list(window).count(opp_piece) == 3 and list(window).count(0) == 1:
        score -= 4

    return score


def score_position(board: np.ndarray, piece: int) -> int:
    """Score the entire board position"""
    score = 0

    # Score center column
    center_array = [int(i) for i in list(board[:, 3])]
    center_count = center_array.count(piece)
    score += center_count * 3

    # Score Horizontal
    for r in range(6):
        row_array = [int(i) for i in list(board[r, :])]
        for c in range(4):
            window = row_array[c:c+4]
            score += evaluate_window(np.array(window), piece)

    # Score Vertical
    for c in range(7):
        col_array = [int(i) for i in list(board[:, c])]
        for r in range(3):
            window = col_array[r:r+4]
            score += evaluate_window(np.array(window), piece)

    # Score positive diagonal
    for r in range(3):
        for c in range(4):
            window = [board[r+i][c+i] for i in range(4)]
            score += evaluate_window(np.array(window), piece)

    # Score negative diagonal
    for r in range(3):
        for c in range(4):
            window = [board[r+3-i][c+i] for i in range(4)]
            score += evaluate_window(np.array(window), piece)

    return score


def is_terminal_node(board: np.ndarray) -> bool:
    """Check if the game has ended"""
    return (winning_move(board, 1) or 
            winning_move(board, -1) or 
            len([c for c in range(7) if is_valid_move(board, c)]) == 0)


def minimax(board: np.ndarray, depth: int, alpha: float, beta: float, maximizing_player: bool) -> Tuple[int, int]:
    """Minimax algorithm with alpha-beta pruning"""
    valid_locations = [c for c in range(7) if is_valid_move(board, c)]
    is_terminal = is_terminal_node(board)
    
    if depth == 0 or is_terminal:
        if is_terminal:
            if winning_move(board, 1):  # AI wins
                return (10000000000000, None)
            elif winning_move(board, -1):  # Opponent wins
                return (-10000000000000, None)
            else:  # Game over, no more moves
                return (0, None)
        else:  # Depth is zero
            return (score_position(board, 1), None)
    
    if maximizing_player:
        value = -np.inf
        column = random.choice(valid_locations) if valid_locations else 0
        for col in valid_locations:
            row = get_next_open_row(board, col)
            b_copy = board.copy()
            b_copy[row][col] = 1
            new_score, _ = minimax(b_copy, depth-1, alpha, beta, False)
            if new_score > value:
                value = new_score
                column = col
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value, column
    else:  # Minimizing player
        value = np.inf
        column = random.choice(valid_locations) if valid_locations else 0
        for col in valid_locations:
            row = get_next_open_row(board, col)
            b_copy = board.copy()
            b_copy[row][col] = -1
            new_score, _ = minimax(b_copy, depth-1, alpha, beta, True)
            if new_score < value:
                value = new_score
                column = col
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value, column
