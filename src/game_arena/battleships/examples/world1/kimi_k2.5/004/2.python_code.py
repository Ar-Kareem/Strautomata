
import numpy as np
from collections import deque
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Battleship policy implementing Target mode for finishing ships and 
    Hunt mode with probability density and parity optimization.
    """
    board = np.array(board, dtype=int)
    rows, cols = 10, 10
    
    # Phase 1: Target Mode - Find active hits and extend them
    visited = np.zeros((rows, cols), dtype=bool)
    targets = []
    
    for r in range(rows):
        for c in range(cols):
            if board[r, c] == 1 and not visited[r, c]:
                # BFS to find connected component of hits
                queue = deque([(r, c)])
                visited[r, c] = True
                cells = [(r, c)]
                
                while queue:
                    cr, cc = queue.popleft()
                    for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                        nr, nc = cr + dr, cc + dc
                        if (0 <= nr < rows and 0 <= nc < cols and 
                            board[nr, nc] == 1 and not visited[nr, nc]):
                            visited[nr, nc] = True
                            queue.append((nr, nc))
                            cells.append((nr, nc))
                
                # Determine extensions based on component shape
                if len(cells) == 1:
                    # Isolated hit: check all 4 directions
                    cr, cc = cells[0]
                    for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < rows and 0 <= nc < cols and board[nr, nc] == 0:
                            targets.append((nr, nc))
                else:
                    # Linear ship: check ends
                    rows_set = {cell[0] for cell in cells}
                    cols_set = {cell[1] for cell in cells}
                    
                    if len(rows_set) == 1:  # Horizontal
                        row = next(iter(rows_set))
                        min_c, max_c = min(cols_set), max(cols_set)
                        if min_c > 0 and board[row, min_c - 1] == 0:
                            targets.append((row, min_c - 1))
                        if max_c < cols - 1 and board[row, max_c + 1] == 0:
                            targets.append((row, max_c + 1))
                    else:  # Vertical
                        col = next(iter(cols_set))
                        min_r, max_r = min(rows_set), max(rows_set)
                        if min_r > 0 and board[min_r - 1, col] == 0:
                            targets.append((min_r - 1, col))
                        if max_r < rows - 1 and board[max_r + 1, col] == 0:
                            targets.append((max_r + 1, col))
    
    if targets:
        # Remove duplicates while preserving order
        seen = set()
        for t in targets:
            if t not in seen:
                seen.add(t)
                return t
    
    # Phase 2: Hunt Mode - Probability density with parity
    ship_lengths = [5, 4, 3, 3, 2]
    prob = np.zeros((rows, cols))
    
    for L in ship_lengths:
        # Horizontal placements
        for r in range(rows):
            for c in range(cols - L + 1):
                valid = True
                for k in range(L):
                    if board[r, c + k] == -1:
                        valid = False
                        break
                if valid:
                    for k in range(L):
                        if board[r, c + k] == 0:
                            prob[r, c + k] += 1
        
        # Vertical placements
        for c in range(cols):
            for r in range(rows - L + 1):
                valid = True
                for k in range(L):
                    if board[r + k, c] == -1:
                        valid = False
                        break
                if valid:
                    for k in range(L):
                        if board[r + k, c] == 0:
                            prob[r + k, c] += 1
    
    # Apply parity mask (checkerboard) - keep only even parity
    for r in range(rows):
        for c in range(cols):
            if (r + c) % 2 == 1:
                prob[r, c] = 0
    
    # Find cell with maximum probability
    best_val = -1
    best_cell = None
    for r in range(rows):
        for c in range(cols):
            if board[r, c] == 0 and prob[r, c] > best_val:
                best_val = prob[r, c]
                best_cell = (r, c)
    
    if best_cell:
        return best_cell
    
    # Fallback: return first available cell
    for r in range(rows):
        for c in range(cols):
            if board[r, c] == 0:
                return (r, c)
    
    return (0, 0)
