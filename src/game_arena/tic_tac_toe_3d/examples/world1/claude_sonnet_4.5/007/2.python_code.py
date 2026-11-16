
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    import itertools
    
    # Get all possible winning lines in 3D tic-tac-toe
    def get_all_lines():
        lines = []
        
        # Lines along each axis
        for i in range(3):
            for j in range(3):
                # Along x-axis
                lines.append([(x, i, j) for x in range(3)])
                # Along y-axis
                lines.append([(i, y, j) for y in range(3)])
                # Along z-axis
                lines.append([(i, j, z) for z in range(3)])
        
        # Diagonals on planes perpendicular to each axis
        for i in range(3):
            # xy-plane (fixed z)
            lines.append([(j, j, i) for j in range(3)])
            lines.append([(j, 2-j, i) for j in range(3)])
            # xz-plane (fixed y)
            lines.append([(j, i, j) for j in range(3)])
            lines.append([(j, i, 2-j) for j in range(3)])
            # yz-plane (fixed x)
            lines.append([(i, j, j) for j in range(3)])
            lines.append([(i, j, 2-j) for j in range(3)])
        
        # Space diagonals (4 total)
        lines.append([(i, i, i) for i in range(3)])
        lines.append([(i, i, 2-i) for i in range(3)])
        lines.append([(i, 2-i, i) for i in range(3)])
        lines.append([(i, 2-i, 2-i) for i in range(3)])
        
        return lines
    
    def check_line_for_opportunity(line, player):
        """Check if a line has 2 of player's marks and 1 empty"""
        values = [board[x][y][z] for x, y, z in line]
        if values.count(player) == 2 and values.count(0) == 1:
            # Return the empty position
            for i, (x, y, z) in enumerate(line):
                if values[i] == 0:
                    return (x, y, z)
        return None
    
    lines = get_all_lines()
    
    # 1. Check if we can win
    for line in lines:
        move = check_line_for_opportunity(line, 1)
        if move:
            return move
    
    # 2. Check if we need to block opponent
    for line in lines:
        move = check_line_for_opportunity(line, -1)
        if move:
            return move
    
    # 3. Take center if available
    if board[1][1][1] == 0:
        return (1, 1, 1)
    
    # 4. Take corners
    corners = list(itertools.product([0, 2], repeat=3))
    for x, y, z in corners:
        if board[x][y][z] == 0:
            return (x, y, z)
    
    # 5. Take edges (positions with exactly one coordinate = 1)
    edges = [(x, y, z) for x, y, z in itertools.product(range(3), repeat=3)
             if [x, y, z].count(1) == 1]
    for x, y, z in edges:
        if board[x][y][z] == 0:
            return (x, y, z)
    
    # 6. Take face centers (positions with exactly two coordinates = 1)
    face_centers = [(x, y, z) for x, y, z in itertools.product(range(3), repeat=3)
                    if [x, y, z].count(1) == 2]
    for x, y, z in face_centers:
        if board[x][y][z] == 0:
            return (x, y, z)
    
    # 7. Take any available spot
    for x, y, z in itertools.product(range(3), repeat=3):
        if board[x][y][z] == 0:
            return (x, y, z)
    
    # Should never reach here in a valid game
    return (0, 0, 0)
