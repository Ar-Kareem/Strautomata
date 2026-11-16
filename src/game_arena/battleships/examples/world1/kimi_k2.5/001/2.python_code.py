
import numpy as np
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Determines the next move in a Battleship game.
    Board values: 0 = unknown, -1 = miss, 1 = hit
    """
    board_arr = np.array(board)
    
    # Phase 1: Target Mode - Finish sinking damaged ships
    target = _find_target(board_arr)
    if target:
        return target
    
    # Phase 2: Hunt Mode - Probability-based search
    return _find_hunt_move(board_arr)

def _find_target(board: np.ndarray) -> Tuple[int, int]:
    """Finds a cell adjacent to existing hits to continue sinking a ship."""
    rows, cols = board.shape
    
    # First, look for lines of 2+ hits to extend
    for r in range(rows):
        for c in range(cols):
            if board[r, c] == 1:
                # Check for horizontal line
                if (c > 0 and board[r, c-1] == 1) or (c < cols-1 and board[r, c+1] == 1):
                    left = c
                    while left > 0 and board[r, left-1] == 1:
                        left -= 1
                    right = c
                    while right < cols-1 and board[r, right+1] == 1:
                        right += 1
                    # Try extending left or right
                    if left > 0 and board[r, left-1] == 0:
                        return (r, left-1)
                    if right < cols-1 and board[r, right+1] == 0:
                        return (r, right+1)
                
                # Check for vertical line
                if (r > 0 and board[r-1, c] == 1) or (r < rows-1 and board[r+1, c] == 1):
                    top = r
                    while top > 0 and board[top-1, c] == 1:
                        top -= 1
                    bottom = r
                    while bottom < rows-1 and board[bottom+1, c] == 1:
                        bottom += 1
                    # Try extending up or down
                    if top > 0 and board[top-1, c] == 0:
                        return (top-1, c)
                    if bottom < rows-1 and board[bottom+1, c] == 0:
                        return (bottom+1, c)
    
    # If no lines found, look for isolated hits
    for r in range(rows):
        for c in range(cols):
            if board[r, c] == 1:
                for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols and board[nr, nc] == 0:
                        return (nr, nc)
    return None

def _identify_sunk_lengths(board: np.ndarray) -> List[int]:
    """Identifies ship lengths that are definitely sunk (closed lines of hits)."""
    rows, cols = board.shape
    sunk = []
    
    # Horizontal check
    visited = [[False]*cols for _ in range(rows)]
    for r in range(rows):
        c = 0
        while c < cols:
            if board[r, c] == 1 and not visited[r][c]:
                length = 0
                temp_c = c
                while temp_c < cols and board[r, temp_c] == 1:
                    visited[r][temp_c] = True
                    length += 1
                    temp_c += 1
                # Check if closed on both ends
                left_closed = (c == 0) or (board[r, c-1] == -1)
                right_closed = (temp_c == cols) or (board[r, temp_c] == -1)
                if left_closed and right_closed and length in [2,3,4,5]:
                    sunk.append(length)
                c = temp_c
            else:
                c += 1
    
    # Vertical check
    visited = [[False]*cols for _ in range(rows)]
    for c in range(cols):
        r = 0
        while r < rows:
            if board[r, c] == 1 and not visited[r][c]:
                length = 0
                temp_r = r
                while temp_r < rows and board[temp_r, c] == 1:
                    visited[temp_r][c] = True
                    length += 1
                    temp_r += 1
                top_closed = (r == 0) or (board[r-1, c] == -1)
                bottom_closed = (temp_r == rows) or (board[temp_r, c] == -1)
                if top_closed and bottom_closed and length in [2,3,4,5]:
                    sunk.append(length)
                r = temp_r
            else:
                r += 1
                
    return sunk

def _find_hunt_move(board: np.ndarray) -> Tuple[int, int]:
    """Uses probability density to find the best hunting cell."""
    rows, cols = board.shape
    
    # Determine remaining ships
    sunk = _identify_sunk_lengths(board)
    remaining = [5, 4, 3, 3, 2]
    for length in sunk:
        if length in remaining:
            remaining.remove(length)
    
    best_score = -1
    best_move = (0, 0)  # Default fallback
    
    for r in range(rows):
        for c in range(cols):
            if board[r, c] != 0:
                continue
                
            score = 0
            for length in remaining:
                # Horizontal placements covering (r,c)
                start_min = max(0, c - length + 1)
                start_max = min(c, cols - length)
                for start_c in range(start_min, start_max + 1):
                    valid = True
                    for k in range(start_c, start_c + length):
                        if board[r, k] == -1:
                            valid = False
                            break
                    if valid:
                        score += 1
                
                # Vertical placements covering (r,c)
                start_min = max(0, r - length + 1)
                start_max = min(r, rows - length)
                for start_r in range(start_min, start_max + 1):
                    valid = True
                    for k in range(start_r, start_r + length):
                        if board[k, c] == -1:
                            valid = False
                            break
                    if valid:
                        score += 1
            
            # Prefer checkerboard pattern (even parity) as tie-breaker
            if (r + c) % 2 == 0:
                score += 0.1
                
            if score > best_score:
                best_score = score
                best_move = (r, c)
    
    return best_move
