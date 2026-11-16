
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    Determine the next move for 3D Tic Tac Toe using a simple heuristic.
    
    Args:
        board: 3x3x3 list representing the game state
               0 = empty, 1 = AI, -1 = opponent
        
    Returns:
        Tuple (x, y, z) representing the next move coordinates
    """
    import numpy as np
    
    # Flatten the board to make it easier to work with
    flat_board = np.array(board)
    
    # Check for winning moves or blocking moves
    # Try to win or block in all possible directions:
    # 1. Rows (x-axis)
    # 2. Columns (y-axis) 
    # 3. Layers (z-axis)
    # 4. Diagonals within layers
    # 5. 3D diagonals
    
    # Check for immediate win or block opportunities
    for i in range(3):
        for j in range(3):
            # Check rows in each layer
            if board[i][j].count(1) == 2 and board[i][j].count(0) == 1:
                k = board[i][j].index(0)
                return (i, j, k)
            if board[i][j].count(-1) == 2 and board[i][j].count(0) == 1:
                k = board[i][j].index(0)
                return (i, j, k)
            
            # Check columns in each layer (reading column-wise)
            col = [board[k][j][i] for k in range(3)]
            if col.count(1) == 2 and col.count(0) == 1:
                k = col.index(0)
                return (k, j, i)
            if col.count(-1) == 2 and col.count(0) == 1:
                k = col.index(0)
                return (k, j, i)
    
    # At layer level
    for k in range(3):
        for i in range(3):
            # Check rows in each layer
            layer = board[k][i]
            if layer.count(1) == 2 and layer.count(0) == 1:
                j = layer.index(0)
                return (i, j, k)
            if layer.count(-1) == 2 and layer.count(0) == 1:
                j = layer.index(0)
                return (i, j, k)
    
    # Check main diagonals
    # Main diagonal 1: (0,0,0)->(1,1,1)->(2,2,2) 
    diag1 = [board[i][i][i] for i in range(3)]
    if diag1.count(1) == 2 and diag1.count(0) == 1:
        i = diag1.index(0)
        return (i, i, i)
    if diag1.count(-1) == 2 and diag1.count(0) == 1:
        i = diag1.index(0)
        return (i, i, i)
    
    # Main diagonal 2: (0,0,2)->(1,1,1)->(2,2,0)
    diag2 = [board[i][i][2-i] for i in range(3)]
    if diag2.count(1) == 2 and diag2.count(0) == 1:
        i = diag2.index(0)
        return (i, i, 2-i)
    if diag2.count(-1) == 2 and diag2.count(0) == 1:
        i = diag2.index(0)
        return (i, i, 2-i)
    
    # If no immediate win/block, prefer center if available
    if board[1][1][1] == 0:
        return (1, 1, 1)
    
    # Prefer corners
    corners = [(0,0,0), (0,0,2), (0,2,0), (0,2,2), (2,0,0), (2,0,2), (2,2,0), (2,2,2)]
    for x, y, z in corners:
        if board[x][y][z] == 0:
            return (x, y, z)
    
    # If no corners are available, play anywhere
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    return (i, j, k)
    
    # Fallback (should not happen in valid game state)
    return (0, 0, 0)
