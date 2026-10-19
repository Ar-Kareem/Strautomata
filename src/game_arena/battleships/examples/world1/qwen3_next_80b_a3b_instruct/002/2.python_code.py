
import random
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Implements a targeted strategy for Battleship:
    1. After a hit, hunt adjacent cells to determine ship orientation
    2. Use parity optimization (only shoot on i+j even) for initial searches
    3. If no strategic moves, fall back to random
    """
    n = 10
    hits = []  # List of known hit positions
    adjacent_candidates = set()  # Cells adjacent to hits that are still unknown
    
    # Collect all hit positions and identify adjacent unknown cells
    for i in range(n):
        for j in range(n):
            if board[i][j] == 1:  # Hit
                hits.append((i, j))
                # Check all 4 adjacent cells
                for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    ni, nj = i + di, j + dj
                    if 0 <= ni < n and 0 <= nj < n and board[ni][nj] == 0:
                        adjacent_candidates.add((ni, nj))
    
    # If we have adjacent candidates to known hits, prioritize them
    if adjacent_candidates:
        # Choose one of the adjacent cells
        return adjacent_candidates.pop()
    
    # If no adjacent candidates, look for potential ship lines
    # Try to find a row/column with multiple hits in line
    for i in range(n):
        for j in range(n):
            if board[i][j] == 1:
                # Look for horizontal potential
                if j > 0 and board[i][j-1] == 1:
                    # We have horizontal hit pattern, extend if possible
                    # Try to find the ends of this ship
                    left, right = j-1, j
                    while left >= 0 and board[i][left] == 1:
                        left -= 1
                    while right < n and board[i][right] == 1:
                        right += 1
                    
                    # Check left end
                    if left >= 0 and board[i][left] == 0:
                        return (i, left)
                    # Check right end
                    if right < n and board[i][right] == 0:
                        return (i, right)
                
                # Look for vertical potential
                if i > 0 and board[i-1][j] == 1:
                    # We have vertical hit pattern, extend if possible
                    up, down = i-1, i
                    while up >= 0 and board[up][j] == 1:
                        up -= 1
                    while down < n and board[down][j] == 1:
                        down += 1
                    
                    # Check top end
                    if up >= 0 and board[up][j] == 0:
                        return (up, j)
                    # Check bottom end
                    if down < n and board[down][j] == 0:
                        return (down, j)
    
    # Use parity strategy: only target (i+j) % 2 == 0 cells
    # This is efficient because any ship of length >=2 must cover both parities
    # So we only need to check half the board to guarantee hits
    
    parity_cells = []
    for i in range(n):
        for j in range(n):
            if board[i][j] == 0 and (i + j) % 2 == 0:
                parity_cells.append((i, j))
    
    if parity_cells:
        return random.choice(parity_cells)
    
    # Fallback: any unknown cell
    unknown_cells = [(i, j) for i in range(n) for j in range(n) if board[i][j] == 0]
    if unknown_cells:
        return random.choice(unknown_cells)
    
    # Should never reach here if game is still ongoing
    return (0, 0)
