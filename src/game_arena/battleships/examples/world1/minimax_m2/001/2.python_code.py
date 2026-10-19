
# Global variable for the hunt pattern: cells where (i+j) is even
hunt_pattern = [(i, j) for i in range(10) for j in range(10) if (i + j) % 2 == 0]
hunt_pattern.sort(key=lambda x: (x[0], x[1]))  # Sort by row, then column

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Returns the next cell to fire at based on the current board state.
    Targets adjacent cells to hits when possible, otherwise uses a checkerboard hunt pattern.
    """
    # Find all hit cells
    hits = []
    for i in range(10):
        for j in range(10):
            if board[i][j] == 1:
                hits.append((i, j))
    
    # Compute candidate cells: unknown cells adjacent to hits
    candidates = []
    for (i, j) in hits:
        for di, dj in [(0, 1), (0, -1), (1, 0), (-1, 0)]:  # right, left, down, up
            ni, nj = i + di, j + dj
            if 0 <= ni < 10 and 0 <= nj < 10:
                if board[ni][nj] == 0:  # Unknown cell
                    if (ni, nj) not in candidates:  # Avoid duplicates
                        candidates.append((ni, nj))
    
    # If candidates exist, choose the one with smallest row, then column
    if candidates:
        candidates.sort(key=lambda x: (x[0], x[1]))
        return candidates[0]
    else:
        # Hunt mode: find the first unshot cell in the hunt pattern
        for (i, j) in hunt_pattern:
            if board[i][j] == 0:
                return (i, j)
        # If all hunt pattern cells are shot, shoot the first unshot cell in row-major order
        unshot_cells = []
        for i in range(10):
            for j in range(10):
                if board[i][j] == 0:
                    unshot_cells.append((i, j))
        if unshot_cells:
            unshot_cells.sort(key=lambda x: (x[0], x[1]))
            return unshot_cells[0]
        else:
            # No unshot cells left (game should be over), return arbitrary cell
            return (0, 0)
