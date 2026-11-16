
import numpy as np
from typing import List, Tuple, Optional

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    """
    Determines the next move for 3D Tic Tac Toe using minimax with alpha-beta pruning.
    
    Args:
        board: 3x3x3 list of lists representing the game board
               0 = empty, 1 = player (us), -1 = opponent
    
    Returns:
        Tuple of (x, y, z) coordinates for the next move
    """
    # Convert board to numpy array for easier manipulation
    board_array = np.array(board)
    
    # Check if we can win immediately
    win_move = find_winning_move(board_array, 1)
    if win_move:
        return win_move
    
    # Check if we need to block opponent's winning move
    block_move = find_winning_move(board_array, -1)
    if block_move:
        return block_move
    
    # Use minimax to find the best move
    best_score = -float('inf')
    best_move = None
    
    # Get all possible moves (empty cells)
    moves = get_empty_cells(board_array)
    
    # If board is empty, take center for first move
    if len(moves) == 27:
        return (1, 1, 1)
    
    for move in moves:
        x, y, z = move
        board_array[x, y, z] = 1  # Make the move
        score = minimax(board_array, 4, -float('inf'), float('inf'), False)
        board_array[x, y, z] = 0  # Undo the move
        
        if score > best_score:
            best_score = score
            best_move = move
    
    # Fallback to first available move if minimax didn't find anything
    return best_move if best_move else moves[0]

def get_empty_cells(board: np.ndarray) -> List[Tuple[int, int, int]]:
    """Returns a list of all empty cell coordinates."""
    empty_cells = []
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x, y, z] == 0:
                    empty_cells.append((x, y, z))
    return empty_cells

def check_win(board: np.ndarray, player: int) -> bool:
    """Check if the specified player has won."""
    # Check all possible winning lines in 3D tic-tac-toe
    # Rows in each layer
    for z in range(3):
        for x in range(3):
            if all(board[x, y, z] == player for y in range(3)):
                return True
        for y in range(3):
            if all(board[x, y, z] == player for x in range(3)):
                return True
    
    # Columns through layers
    for x in range(3):
        for y in range(3):
            if all(board[x, y, z] == player for z in range(3)):
                return True
    
    # Diagonals in each layer
    for z in range(3):
        if all(board[i, i, z] == player for i in range(3)):
            return True
        if all(board[i, 2-i, z] == player for i in range(3)):
            return True
    
    # Diagonals through layers
    if all(board[i, i, i] == player for i in range(3)):
        return True
    if all(board[i, i, 2-i] == player for i in range(3)):
        return True
    if all(board[i, 2-i, i] == player for i in range(3)):
        return True
    if all(board[i, 2-i, 2-i] == player for i in range(3)):
        return True
    
    # Other diagonals
    if all(board[0, i, i] == player for i in range(3)) or \
       all(board[2, i, i] == player for i in range(3)) or \
       all(board[1, i, i] == player for i in range(3)):
        return True
    
    if all(board[0, i, 2-i] == player for i in range(3)) or \
       all(board[2, i, 2-i] == player for i in range(3)) or \
       all(board[1, i, 2-i] == player for i in range(3)):
        return True
    
    if all(board[i, 0, i] == player for i in range(3)) or \
       all(board[i, 2, i] == player for i in range(3)) or \
       all(board[i, 1, i] == player for i in range(3)):
        return True
    
    if all(board[i, 0, 2-i] == player for i in range(3)) or \
       all(board[i, 2, 2-i] == player for i in range(3)) or \
       all(board[i, 1, 2-i] == player for i in range(3)):
        return True
    
    return False

def find_winning_move(board: np.ndarray, player: int) -> Optional[Tuple[int, int, int]]:
    """Find a winning move for the specified player, if one exists."""
    empty_cells = get_empty_cells(board)
    for cell in empty_cells:
        x, y, z = cell
        board[x, y, z] = player
        if check_win(board, player):
            board[x, y, z] = 0  # Undo move
            return cell
        board[x, y, z] = 0  # Undo move
    return None

def evaluate_board(board: np.ndarray) -> int:
    """Evaluate the board position from player 1's perspective."""
    if check_win(board, 1):
        return 100
    elif check_win(board, -1):
        return -100
    else:
        return 0

def minimax(board: np.ndarray, depth: int, alpha: float, beta: float, maximizing: bool) -> int:
    """Minimax algorithm with alpha-beta pruning."""
    score = evaluate_board(board)
    
    # If we have a winner or reached max depth, return score
    if score == 100 or score == -100 or depth == 0:
        return score
    
    # Check for draw (no empty cells)
    if len(get_empty_cells(board)) == 0:
        return 0
    
    if maximizing:  # Player 1's turn (us)
        max_eval = -float('inf')
        for x, y, z in get_empty_cells(board):
            board[x, y, z] = 1
            eval_score = minimax(board, depth - 1, alpha, beta, False)
            board[x, y, z] = 0
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break  # Beta cutoff
        return max_eval
    else:  # Player -1's turn (opponent)
        min_eval = float('inf')
        for x, y, z in get_empty_cells(board):
            board[x, y, z] = -1
            eval_score = minimax(board, depth - 1, alpha, beta, True)
            board[x, y, z] = 0
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break  # Alpha cutoff
        return min_eval
