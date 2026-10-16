
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Targeting policy for the Battleship-like game.
    
    Args:
        board: 10x10 list of lists. 0=unknown, -1=miss, 1=hit.
        
    Returns:
        Tuple (row, col) of the next cell to fire at.
    """
    # Get all cells that are hits
    hits = []
    for r in range(10):
        for c in range(10):
            if board[r][c] == 1:
                hits.append((r, c))
    
    # If we have hits, prioritise adjacent cells
    if hits:
        # Define the four directions
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        
        # Try to find a valid adjacent cell
        for r, c in hits:
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                    return (nr, nc)
    
    # If no hits or no valid adjacent cells, scan the board
    # We'll use a simple deterministic scan: row by row
    for r in range(10):
        for c in range(10):
            if board[r][c] == 0:
                return (r, c)
    
    # This should never happen if the game is valid, but just in case
    # Return a random valid cell
    valid_cells = []
    for r in range(10):
        for c in range(10):
            if board[r][c] == 0:
                valid_cells.append((r, c))
    if valid_cells:
        return random.choice(valid_cells)
    
    # If no valid cells found (should not happen)
    return (0, 0)

