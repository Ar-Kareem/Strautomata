
import numpy as np
from collections import defaultdict

def policy(board: list[list[int]]) -> int:
    board_array = np.array(board)
    rows, cols = board_array.shape
    
    # First, check if we can win immediately
    for col in range(cols):
        if can_win(board_array, col, 1):
            return col
    
    # Then, check if opponent can win next move and block them
    for col in range(cols):
        if can_win(board_array, col, -1):
            return col
    
    # If no immediate win/block, use heuristic to choose best column
    return heuristic_choice(board_array)

def can_win(board: np.ndarray, col: int, player: int) -> bool:
    """Check if dropping a disc in this column would result in a win."""
    if board[0, col] != 0:
        return False  # Column is full
    
    # Find the first empty row in the column
    row = np.max(np.where(board[:, col] == 0))
    
    # Temporarily place the disc
    board[row, col] = player
    
    # Check if this move creates a line of four
    if check_win(board, row, col, player):
        board[row, col] = 0  # Undo the move
        return True
    
    board[row, col] = 0  # Undo the move
    return False

def check_win(board: np.ndarray, row: int, col: int, player: int) -> bool:
    """Check if the disc at (row, col) completes a four-in-a-row."""
    directions = [
        (0, 1),  # Horizontal
        (1, 0),   # Vertical
        (1, 1),   # Diagonal down-right
        (1, -1)   # Diagonal down-left
    ]
    
    rows, cols = board.shape
    for dr, dc in directions:
        count = 1
        # Search in positive direction
        r, c = row + dr, col + dc
        while 0 <= r < rows and 0 <= c < cols and board[r, c] == player:
            count += 1
            r += dr
            c += dc
        # Search in negative direction
        r, c = row - dr, col - dc
        while 0 <= r < rows and 0 <= c < cols and board[r, c] == player:
            count += 1
            r -= dr
            c -= dc
        if count >= 4:
            return True
    return False

def heuristic_choice(board: np.ndarray) -> int:
    """Choose the best column based on heuristic evaluation."""
    cols = board.shape[1]
    valid_cols = [c for c in range(cols) if board[0, c] == 0]
    
    # Prefer center columns for better strategic position
    center_cols = sorted(valid_cols, key=lambda x: abs(x - cols//2))
    
    # Evaluate potential moves based on potential to create opportunities
    scores = defaultdict(int)
    for col in valid_cols:
        row = np.max(np.where(board[:, col] == 0))
        
        # Score based on potential to create lines
        scores[col] += evaluate_position(board, row, col, 1)
        # Penalize moves that give opponent opportunities
        scores[col] -= 0.5 * evaluate_position(board, row, col, -1)
        
        # Bonus for center columns
        scores[col] += (cols//2 - abs(col - cols//2)) * 0.2
    
    # Return column with highest score, preferring center columns in case of tie
    return max(valid_cols, key=lambda c: (scores[c], -abs(c - cols//2)))

def evaluate_position(board: np.ndarray, row: int, col: int, player: int) -> int:
    """Evaluate how good this position is for the given player."""
    directions = [
        (0, 1),  # Horizontal
        (1, 0),   # Vertical
        (1, 1),   # Diagonal down-right
        (1, -1)   # Diagonal down-left
    ]
    
    score = 0
    rows, cols = board.shape
    
    for dr, dc in directions:
        # Count consecutive discs in this direction
        line = []
        # Positive direction
        r, c = row, col
        for _ in range(3):
            r += dr
            c += dc
            if 0 <= r < rows and 0 <= c < cols:
                line.append(board[r, c])
            else:
                line.append(-player)  # Blocked by edge
        
        # Negative direction
        r, c = row, col
        for _ in range(3):
            r -= dr
            c -= dc
            if 0 <= r < rows and 0 <= c < cols:
                line.insert(0, board[r, c])
            else:
                line.insert(0, -player)  # Blocked by edge
        
        # Evaluate the potential of this line
        count = line.count(player)
        empty = line.count(0)
        if count == 3 and empty >= 1:
            score += 100  # Immediate win potential
        elif count == 2 and empty >= 2:
            score += 10   # Potential to build a line
        elif count == 1 and empty >= 3:
            score += 1    # Starting a new line
    
    return score
