
def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Battleship targeting policy for a 10x10 grid.
    
    Strategy:
    1. Target mode: When hits exist, fire at adjacent cells and extend aligned ships.
    2. Hunt mode: Otherwise, systematically cover the grid in a checkerboard pattern.
    
    Returns:
        (row, col): Next cell to fire at.
    """
    # Build set of current hit cells
    current_hits = set()
    for i in range(10):
        for j in range(10):
            if board[i][j] == 1:
                current_hits.add((i, j))
    
    # Initialize target queue as a set for uniqueness
    target_queue = set()
    
    # Step 1: Add adjacent cells to every hit
    for (r, c) in current_hits:
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                target_queue.add((nr, nc))
    
    # Step 2: Find connected components of hits
    components = []
    visited = set()
    for hit in current_hits:
        if hit in visited:
            continue
        stack = [hit]
        comp = set()
        while stack:
            cell = stack.pop()
            if cell in visited:
                continue
            visited.add(cell)
            comp.add(cell)
            r, c = cell
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if (nr, nc) in current_hits and (nr, nc) not in visited:
                    stack.append((nr, nc))
        components.append(comp)
    
    # Step 3: Extend aligned ships
    for comp in components:
        if len(comp) < 2:
            continue
        rows = {r for r, c in comp}
        cols = {c for r, c in comp}
        if len(rows) == 1:  # Horizontal alignment
            row = list(rows)[0]
            cols_list = sorted([c for r, c in comp])
            left = cols_list[0] - 1
            right = cols_list[-1] + 1
            if left >= 0 and board[row][left] == 0:
                target_queue.add((row, left))
            if right < 10 and board[row][right] == 0:
                target_queue.add((row, right))
        elif len(cols) == 1:  # Vertical alignment
            col = list(cols)[0]
            rows_list = sorted([r for r, c in comp])
            up = rows_list[0] - 1
            down = rows_list[-1] + 1
            if up >= 0 and board[up][col] == 0:
                target_queue.add((up, col))
            if down < 10 and board[down][col] == 0:
                target_queue.add((down, col))
    
    # If targets exist, return the first one in sorted order
    if target_queue:
        target_list = sorted(list(target_queue))
        return target_list[0]
    
    # Hunt mode: checkerboard pattern
    for i in range(10):
        for j in range(10):
            if (i + j) % 2 == 0 and board[i][j] == 0:
                return (i, j)
    # If no checkerboard cells found, use full grid
    for i in range(10):
        for j in range(10):
            if board[i][j] == 0:
                return (i, j)
