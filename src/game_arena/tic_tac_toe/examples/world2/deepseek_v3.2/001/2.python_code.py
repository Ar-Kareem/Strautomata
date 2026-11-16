
import numpy as np
from typing import Optional, Tuple, List

def policy(board: list[list[int]]) -> tuple[int, int]:
    """Return the next move (row, col) for player 1 on a 4x4 board."""
    
    # Convert to numpy array for easier manipulation
    board_arr = np.array(board, dtype=int)
    
    # Get list of empty cells
    empty_cells = [(r, c) for r in range(4) for c in range(4) if board_arr[r, c] == 0]
    
    # If board is empty or almost empty, prefer center squares
    if len(empty_cells) >= 14:  # First two moves or similar
        # Center squares in 4x4: positions (1,1), (1,2), (2,1), (2,2)
        center_cells = [(1, 1), (1, 2), (2, 1), (2, 2)]
        available_centers = [cell for cell in center_cells if board_arr[cell] == 0]
        if available_centers:
            return available_centers[0]
    
    # Check for immediate win
    for r, c in empty_cells:
        board_arr[r, c] = 1
        if check_winner(board_arr) == 1:
            return (r, c)
        board_arr[r, c] = 0
    
    # Check for immediate block (opponent about to win)
    for r, c in empty_cells:
        board_arr[r, c] = -1
        if check_winner(board_arr) == -1:
            board_arr[r, c] = 0
            return (r, c)
        board_arr[r, c] = 0
    
    # Use minimax with alpha-beta pruning
    best_move = empty_cells[0]
    best_value = -float('inf')
    
    # Sort moves: center first, then corners, then edges
    def move_priority(cell):
        r, c = cell
        # Center region priority
        if 1 <= r <= 2 and 1 <= c <= 2:
            return 0
        # Corners
        elif (r == 0 or r == 3) and (c == 0 or c == 3):
            return 1
        # Edges
        else:
            return 2
    
    empty_cells.sort(key=move_priority)
    
    depth = min(6, len(empty_cells))
    for r, c in empty_cells:
        board_arr[r, c] = 1
        move_val = minimax(board_arr, depth-1, False, -float('inf'), float('inf'))
        board_arr[r, c] = 0
        
        if move_val > best_value:
            best_value = move_val
            best_move = (r, c)
    
    return best_move

def check_winner(board: np.ndarray) -> int:
    """Return 1 if player 1 wins, -1 if player -1 wins, 0 otherwise."""
    # Check rows
    for r in range(4):
        if all(board[r, c] == 1 for c in range(4)):
            return 1
        if all(board[r, c] == -1 for c in range(4)):
            return -1
    
    # Check columns
    for c in range(4):
        if all(board[r, c] == 1 for r in range(4)):
            return 1
        if all(board[r, c] == -1 for r in range(4)):
            return -1
    
    # Check main diagonal
    if all(board[i, i] == 1 for i in range(4)):
        return 1
    if all(board[i, i] == -1 for i in range(4)):
        return -1
    
    # Check anti-diagonal
    if all(board[i, 3-i] == 1 for i in range(4)):
        return 1
    if all(board[i, 3-i] == -1 for i in range(4)):
        return -1
    
    return 0

def evaluate(board: np.ndarray) -> int:
    """Heuristic evaluation of the board from player 1's perspective."""
    score = 0
    
    # Evaluate all possible lines
    lines = []
    
    # Rows
    for r in range(4):
        lines.append(board[r, :])
    
    # Columns
    for c in range(4):
        lines.append(board[:, c])
    
    # Diagonals
    lines.append([board[i, i] for i in range(4)])
    lines.append([board[i, 3-i] for i in range(4)])
    
    for line in lines:
        line_arr = np.array(line)
        p1_count = np.sum(line_arr == 1)
        p2_count = np.sum(line_arr == -1)
        
        if p1_count > 0 and p2_count == 0:
            score += 10 ** p1_count
        elif p2_count > 0 and p1_count == 0:
            score -= 10 ** p2_count
    
    return score

def minimax(board: np.ndarray, depth: int, is_maximizing: bool, alpha: float, beta: float) -> float:
    """Minimax with alpha-beta pruning."""
    winner = check_winner(board)
    if winner != 0:
        return winner * 1000  # Large value for win/loss
    
    if depth == 0:
        return evaluate(board)
    
    empty_cells = [(r, c) for r in range(4) for c in range(4) if board[r, c] == 0]
    
    if is_maximizing:
        max_eval = -float('inf')
        for r, c in empty_cells:
            board[r, c] = 1
            eval = minimax(board, depth-1, False, alpha, beta)
            board[r, c] = 0
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for r, c in empty_cells:
            board[r, c] = -1
            eval = minimax(board, depth-1, True, alpha, beta)
            board[r, c] = 0
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval
