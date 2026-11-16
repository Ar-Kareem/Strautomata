
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Check all 8 lines (3 rows, 3 columns, 2 diagonals) for winning opportunities
    lines = [
        [(0,0), (0,1), (0,2)],  # Row 0
        [(1,0), (1,1), (1,2)],  # Row 1
        [(2,0), (2,1), (2,2)],  # Row 2
        [(0,0), (1,0), (2,0)],  # Column 0
        [(0,1), (1,1), (2,1)],  # Column 1
        [(0,2), (1,2), (2,2)],  # Column 2
        [(0,0), (1,1), (2,2)],  # Diagonal 1
        [(0,2), (1,1), (2,0)]   # Diagonal 2
    ]
    
    # Check for winning moves (2 of your marks + 1 empty cell)
    for line in lines:
        count_1 = 0
        empty_cell = None
        for (r, c) in line:
            if board[r][c] == 1:
                count_1 += 1
            elif board[r][c] == 0:
                empty_cell = (r, c)
        if count_1 == 2 and empty_cell is not None:
            return empty_cell
    
    # If no winning moves, select optimal cell based on strategic value
    # Prioritize center, corners, then edges
    priority_order = [
        (1,1),  # Center
        (0,0), (0,2), (2,0), (2,2),  # Corners
        (0,1), (1,0), (1,2), (2,1)   # Edges
    ]
    
    for (r, c) in priority_order:
        if board[r][c] == 0:
            return (r, c)
    
    # Fallback: return first available cell if all are occupied
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                return (r, c)
    
    # Should not reach here, but return safe default
    return (0, 0)
