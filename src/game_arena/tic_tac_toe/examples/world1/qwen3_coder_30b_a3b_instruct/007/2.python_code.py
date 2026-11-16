
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Check for immediate winning move or blocking move
    # Scan all rows, columns, and diagonals
    empty_positions = []
    
    # Check rows
    for i in range(3):
        row = board[i]
        if row.count(1) == 2 and row.count(0) == 1:
            # I can win
            col = row.index(0)
            return (i, col)
        elif row.count(-1) == 2 and row.count(0) == 1:
            # Block opponent
            col = row.index(0)
            return (i, col)
    
    # Check columns
    for j in range(3):
        col = [board[i][j] for i in range(3)]
        if col.count(1) == 2 and col.count(0) == 1:
            # I can win
            row = col.index(0)
            return (row, j)
        elif col.count(-1) == 2 and col.count(0) == 1:
            # Block opponent
            row = col.index(0)
            return (row, j)
    
    # Check main diagonal
    diag1 = [board[i][i] for i in range(3)]
    if diag1.count(1) == 2 and diag1.count(0) == 1:
        idx = diag1.index(0)
        return (idx, idx)
    elif diag1.count(-1) == 2 and diag1.count(0) == 1:
        idx = diag1.index(0)
        return (idx, idx)
    
    # Check anti-diagonal
    diag2 = [board[i][2-i] for i in range(3)]
    if diag2.count(1) == 2 and diag2.count(0) == 1:
        idx = diag2.index(0)
        return (idx, 2-idx)
    elif diag2.count(-1) == 2 and diag2.count(0) == 1:
        idx = diag2.index(0)
        return (idx, 2-idx)
    
    # No immediate win or block, so play strategically
    # Check center
    if board[1][1] == 0:
        return (1, 1)
    
    # Check corners
    corners = [(0,0), (0,2), (2,0), (2,2)]
    for r, c in corners:
        if board[r][c] == 0:
            return (r, c)
    
    # Check edges
    edges = [(0,1), (1,0), (1,2), (2,1)]
    for r, c in edges:
        if board[r][c] == 0:
            return (r, c)
    
    # Fallback - return the first empty position (shouldn't happen in normal play)
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                return (i, j)
