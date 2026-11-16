
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    def is_winning_move(i: int, j: int, k: int, player: int) -> bool:
        lines = []
        # Axis-aligned lines
        lines.append([(x, j, k) for x in range(3)])
        lines.append([(i, y, k) for y in range(3)])
        lines.append([(i, j, z) for z in range(3)])
        
        # Face diagonals for x = i
        if j == k:
            lines.append([(i, 0, 0), (i, 1, 1), (i, 2, 2)])
        if j + k == 2:
            lines.append([(i, 0, 2), (i, 1, 1), (i, 2, 0)])
        
        # Face diagonals for y = j
        if i == k:
            lines.append([(0, j, 0), (1, j, 1), (2, j, 2)])
        if i + k == 2:
            lines.append([(0, j, 2), (1, j, 1), (2, j, 0)])
        
        # Face diagonals for z = k
        if i == j:
            lines.append([(0, 0, k), (1, 1, k), (2, 2, k)])
        if i + j == 2:
            lines.append([(0, 2, k), (1, 1, k), (2, 0, k)])
        
        # Space diagonals
        if i == j == k:
            lines.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
        if i == j and k == 2 - i:
            lines.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
        if j == 2 - i and k == i:
            lines.append([(0, 2, 0), (1, 1, 1), (2, 0, 0)])
        if j == 2 - i and k == 2 - i:
            lines.append([(0, 2, 2), (1, 1, 1), (2, 0, 0)])
        
        # Check each line for a win
        for line in lines:
            others = [(x, y, z) for (x, y, z) in line if not (x == i and y == j and z == k)]
            if all(board[x][y][z] == player for (x, y, z) in others):
                return True
        return False

    # Check for win
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0 and is_winning_move(i, j, k, 1):
                    return (i, j, k)
    
    # Block opponent's win
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0 and is_winning_move(i, j, k, -1):
                    return (i, j, k)
    
    # Prioritize center
    if board[1][1][1] == 0:
        return (1, 1, 1)
    
    # Prioritize corners
    corners = [(0,0,0), (0,0,2), (0,2,0), (0,2,2), (2,0,0), (2,0,2), (2,2,0), (2,2,2)]
    for corner in corners:
        if board[corner[0]][corner[1]][corner[2]] == 0:
            return corner
    
    # Any empty cell
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    return (i, j, k)
    
    return (0, 0, 0)
