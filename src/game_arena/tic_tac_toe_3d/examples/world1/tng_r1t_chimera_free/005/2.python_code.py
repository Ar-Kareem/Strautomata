
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Generate all possible winning lines
    lines = []
    
    # Lines along the three axes
    for j in range(3):
        for k in range(3):
            lines.append([(i, j, k) for i in range(3)])
    for i in range(3):
        for k in range(3):
            lines.append([(i, j, k) for j in range(3)])
    for i in range(3):
        for j in range(3):
            lines.append([(i, j, k) for k in range(3)])
    
    # Face diagonals
    for k in range(3):
        lines.append([(0,0,k), (1,1,k), (2,2,k)])
        lines.append([(0,2,k), (1,1,k), (2,0,k)])
    for j in range(3):
        lines.append([(0,j,0), (1,j,1), (2,j,2)])
        lines.append([(0,j,2), (1,j,1), (2,j,0)])
    for i in range(3):
        lines.append([(i,0,0), (i,1,1), (i,2,2)])
        lines.append([(i,0,2), (i,1,1), (i,2,0)])
    
    # Space diagonals
    lines.append([(0,0,0), (1,1,1), (2,2,2)])
    lines.append([(0,0,2), (1,1,1), (2,2,0)])
    lines.append([(0,2,0), (1,1,1), (2,0,2)])
    lines.append([(0,2,2), (1,1,1), (2,0,0)])
    
    # Check for winning moves
    for line in lines:
        cells = [board[i][j][k] for (i,j,k) in line]
        if cells.count(1) == 2 and cells.count(0) == 1:
            for (i,j,k) in line:
                if board[i][j][k] == 0:
                    return (i, j, k)
    
    # Check for blocking opponent's wins
    for line in lines:
        cells = [board[i][j][k] for (i,j,k) in line]
        if cells.count(-1) == 2 and cells.count(0) == 1:
            for (i,j,k) in line:
                if board[i][j][k] == 0:
                    return (i, j, k)
    
    # Take center if available
    if board[1][1][1] == 0:
        return (1, 1, 1)
    
    # Check corners
    corners = [(0,0,0), (0,0,2), (0,2,0), (0,2,2),
               (2,0,0), (2,0,2), (2,2,0), (2,2,2)]
    for (i,j,k) in corners:
        if board[i][j][k] == 0:
            return (i, j, k)
    
    # Take any remaining empty cell
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    return (i, j, k)
    
    # Fallback (shouldn't be reached in a valid game)
    return (0, 0, 0)
