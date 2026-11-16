
import numpy as np
from typing import Tuple, List

# Precompute all winning lines as lists of (i,j,k) tuples
WINNING_LINES = [
    # Rows along i (for each j,k)
    *[[[(i, j, k) for i in range(3)] for j in range(3)] for k in range(3)],
    # Columns along j (for each i,k)
    *[[[(i, j, k) for j in range(3)] for i in range(3)] for k in range(3)],
    # Depths along k (for each i,j)
    *[[[(i, j, k) for k in range(3)] for i in range(3)] for j in range(3)],
    # Face diagonals (i-j pool for each k)
    [[(i, j, k) for i, j in zip(range(3), range(3))] for k in range(3)],
    [[(i, j, k) for i, j in zip(range(3), range(2, -1, -1))] for k in range(3)],
    # Face diagonals (i-k pool for each j)
    [[(i, j, k) for i, k in zip(range(3), range(3))] for j in range(3)],
    [[(i, j, k) for i, k in zip(range(3), range(2, -1, -1))] for j in range(3)],
    # Face diagonals (j-k pool for each i)
    [[(i, j, k) for j, k in zip(range(3), range(3))] for i in range(3)],
    [[(i, j, k) for j, k in zip(range(3), range(2, -1, -1))] for i in range(3)],
    # Space diagonals
    [[(i, i, i) for i in range(3)]],
    [[(i, i, 2-i) for i in range(3)]],
    [[(i, 2-i, i) for i in range(3)]],
    [[(i, 2-i, 2-i) for i in range(3)]],
    [[(2-i, i, i) for i in range(3)]],
    [[(2-i, i, 2-i) for i in range(3)]],
    [[(2-i, 2-i, i) for i in range(3)]],
    [[(2-i, 2-i, 2-i) for i in range(3)]]
]
# Flatten the list
WINNING_LINES = [line for sublist in WINNING_LINES for line in sublist]

def count_in_line(board: np.ndarray, line: List[Tuple[int,int,int]], player: int) -> int:
    """Count how many cells in this line are occupied by the given player."""
    return sum(1 for pos in line if board[pos] == player)

def is_winnable(board: np.ndarray, line: List[Tuple[int,int,int]], player: int) -> bool:
    """Check if the line can be won by the player (has 2 occupied and 1 empty)."""
    if count_in_line(board, line, player) == 2 and count_in_line(board, line, 0) == 1:
        return True
    return False

def get_empty_in_line(board: np.ndarray, line: List[Tuple[int,int,int]]) -> Tuple[int,int,int]:
    """Get the empty cell in the line (assuming exactly one empty)."""
    for pos in line:
        if board[pos] == 0:
            return pos
    # Should not happen if winnable, but just in case
    return None

def score_move(board: np.ndarray, move: Tuple[int,int,int]) -> int:
    """Score a move based on how many lines it affects."""
    # Count how many winning lines this move belongs to
    score = 0
    for line in WINNING_LINES:
        if move in line:
            score += 1
    return score

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    board = np.array(board)
    
    # Step 1: Check for a winning move for us
    for line in WINNING_LINES:
        if is_winnable(board, line, 1):
            move = get_empty_in_line(board, line)
            if move:
                return move
    
    # Step 2: Block opponent's winning move
    for line in WINNING_LINES:
        if is_winnable(board, line, -1):
            move = get_empty_in_line(board, line)
            if move:
                return move
    
    # Step 3: Strategic move - choose the empty cell that appears in the most winning lines
    best_move = None
    best_score = -1
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i, j, k] == 0:
                    score = score_move(board, (i, j, k))
                    if score > best_score:
                        best_score = score
                        best_move = (i, j, k)
    if best_move:
        return best_move
    
    # Fallback: Should not reach here if board has empty cells, but just in case, pick first empty
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i, j, k] == 0:
                    return (i, j, k)
    # Impossible, but return arbitrary
    return (0, 0, 0)
