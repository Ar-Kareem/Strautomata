
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Define all possible lines (rows, columns, diagonals)
    lines = [
        [(0,0), (0,1), (0,2)],
        [(1,0), (1,1), (1,2)],
        [(2,0), (2,1), (2,2)],
        [(0,0), (1,0), (2,0)],
        [(0,1), (1,1), (2,1)],
        [(0,2), (1,2), (2,2)],
        [(0,0), (1,1), (2,2)],
        [(0,2), (1,1), (2,0)]
    ]
    
    # Step 1: Check for immediate winning move (two of our marks and one empty)
    for line in lines:
        count_our_marks = 0
        empty_cells = []
        for r, c in line:
            if board[r][c] == 1:
                count_our_marks += 1
            elif board[r][c] == 0:
                empty_cells.append((r, c))
        if count_our_marks == 2 and len(empty_cells) == 1:
            return empty_cells[0]
    
    # Step 2: Check for potential opponent winning moves (no our marks and at least two empty)
    for line in lines:
        count_our_marks = 0
        empty_cells = []
        for r, c in line:
            if board[r][c] == 1:
                count_our_marks += 1
            elif board[r][c] == 0:
                empty_cells.append((r, c))
        if count_our_marks == 0 and len(empty_cells) >= 2:
            return empty_cells[0]
    
    # Step 3: If no threats, play safe moves (center, corners, edges)
    # Preferred order: center, then corners, then edges
    preferred_moves = [
        (1,1),  # center
        (0,0), (0,2), (2,0), (2,2),  # corners
        (0,1), (1,0), (1,2), (2,1)   # edges
    ]
    
    for r, c in preferred_moves:
        if board[r][c] == 0:
            return (r, c)
    
    # Fallback: return any empty cell (shouldn't happen if board isn't full)
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                return (r, c)
    # In case of full board (unlikely), return (0,0)
    return (0,0)
