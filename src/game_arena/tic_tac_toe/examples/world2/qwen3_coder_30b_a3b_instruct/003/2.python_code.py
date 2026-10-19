
import numpy as np
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    # Convert to numpy array for easier handling
    board = np.array(board)
    
    # Get all empty positions
    empty_positions = [(i, j) for i in range(4) for j in range(4) if board[i, j] == 0]
    
    # If no empty positions, return invalid move (shouldn't happen in valid game)
    if not empty_positions:
        return (0, 0)
    
    # Check for winning moves first
    for i, j in empty_positions:
        # Try placing our mark
        board[i, j] = 1
        if is_winning_move(board, i, j):
            board[i, j] = 0  # Reset
            return (i, j)
        board[i, j] = 0  # Reset
    
    # Check for blocking moves
    for i, j in empty_positions:
        # Try placing opponent's mark to see if they'd win
        board[i, j] = -1
        if is_winning_move(board, i, j):
            board[i, j] = 0  # Reset
            return (i, j)
        board[i, j] = 0  # Reset
    
    # If no immediate win/block, use heuristic evaluation
    best_move = None
    best_score = -float('inf')
    
    for i, j in empty_positions:
        # Calculate heuristic score for this position
        score = evaluate_position(board, i, j)
        
        # Prefer center positions
        center_distance = abs(i - 1.5) + abs(j - 1.5)
        score += 0.1 * (4 - center_distance)
        
        # Prefer corners
        if (i in [0, 3]) and (j in [0, 3]):
            score += 0.2
            
        if score > best_score:
            best_score = score
            best_move = (i, j)
    
    # Return best move found or first available if none found
    return best_move if best_move else empty_positions[0]

def is_winning_move(board: np.ndarray, row: int, col: int) -> bool:
    """Check if placing at (row, col) creates a winning line"""
    player = board[row, col]
    
    # Check row
    if all(board[row, j] == player for j in range(4)):
        return True
    
    # Check column
    if all(board[i, col] == player for i in range(4)):
        return True
    
    # Check main diagonal
    if row == col and all(board[i, i] == player for i in range(4)):
        return True
    
    # Check anti-diagonal
    if row + col == 3 and all(board[i, 3-i] == player for i in range(4)):
        return True
    
    return False

def evaluate_position(board: np.ndarray, row: int, col: int) -> float:
    """Evaluate the heuristic value of placing at (row, col)"""
    score = 0
    player = 1  # Our player
    
    # Create a temporary board to evaluate
    temp_board = board.copy()
    temp_board[row, col] = player
    
    # Evaluate potential lines that include this position
    # Row
    row_line = [temp_board[row, j] for j in range(4)]
    score += evaluate_line(row_line)
    
    # Column
    col_line = [temp_board[i, col] for i in range(4)]
    score += evaluate_line(col_line)
    
    # Diagonals
    if row == col:  # Main diagonal
        diag1 = [temp_board[i, i] for i in range(4)]
        score += evaluate_line(diag1)
    if row + col == 3:  # Anti-diagonal
        diag2 = [temp_board[i, 3-i] for i in range(4)]
        score += evaluate_line(diag2)
    
    return score

def evaluate_line(line: List[int]) -> float:
    """Evaluate a 4-element line for potential"""
    score = 0
    player_count = line.count(1)
    opponent_count = line.count(-1)
    empty_count = line.count(0)
    
    # Favor lines with 2 or more of our pieces (but not winning yet)
    if player_count == 2 and empty_count == 2:
        score += 10
    elif player_count == 3 and empty_count == 1:
        score += 50
    elif player_count == 1 and empty_count == 3:
        score += 5
    elif player_count == 2 and empty_count == 2:
        score += 10
    elif opponent_count == 2 and empty_count == 2:
        score += 40  # Block opponent
    elif opponent_count == 3 and empty_count == 1:
        score += 100  # Strong block
    
    return score
