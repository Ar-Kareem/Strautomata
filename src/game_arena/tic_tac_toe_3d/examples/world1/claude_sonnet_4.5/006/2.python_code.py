
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    import random
    
    # Generate all winning lines in 3D tic-tac-toe
    def get_all_lines():
        lines = []
        
        # Lines within each horizontal layer (z fixed)
        for z in range(3):
            # Rows (y fixed)
            for y in range(3):
                lines.append([(x, y, z) for x in range(3)])
            # Columns (x fixed)
            for x in range(3):
                lines.append([(x, y, z) for y in range(3)])
            # Diagonals in horizontal plane
            lines.append([(i, i, z) for i in range(3)])
            lines.append([(i, 2-i, z) for i in range(3)])
        
        # Vertical lines (through all z levels)
        for x in range(3):
            for y in range(3):
                lines.append([(x, y, z) for z in range(3)])
        
        # Diagonals in vertical planes parallel to xz (y fixed)
        for y in range(3):
            lines.append([(i, y, i) for i in range(3)])
            lines.append([(i, y, 2-i) for i in range(3)])
        
        # Diagonals in vertical planes parallel to yz (x fixed)
        for x in range(3):
            lines.append([(x, i, i) for i in range(3)])
            lines.append([(x, i, 2-i) for i in range(3)])
        
        # 4 space diagonals (corner to corner)
        lines.append([(i, i, i) for i in range(3)])
        lines.append([(i, i, 2-i) for i in range(3)])
        lines.append([(i, 2-i, i) for i in range(3)])
        lines.append([(2-i, i, i) for i in range(3)])
        
        return lines
    
    def check_line(line, board, player):
        """Check if a line has 2 of player's pieces and 1 empty, return empty position"""
        values = [board[x][y][z] for x, y, z in line]
        if values.count(player) == 2 and values.count(0) == 1:
            empty_idx = values.index(0)
            return line[empty_idx]
        return None
    
    lines = get_all_lines()
    
    # Check for winning move
    for line in lines:
        move = check_line(line, board, 1)
        if move:
            return move
    
    # Check for blocking move
    for line in lines:
        move = check_line(line, board, -1)
        if move:
            return move
    
    # Strategic positions: prefer center, then corners, then edges
    center = (1, 1, 1)
    if board[center[0]][center[1]][center[2]] == 0:
        return center
    
    # Corners of the cube
    corners = [
        (0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),
        (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2)
    ]
    empty_corners = [(x, y, z) for x, y, z in corners if board[x][y][z] == 0]
    if empty_corners:
        return random.choice(empty_corners)
    
    # Face centers
    face_centers = [
        (1, 1, 0), (1, 1, 2), (1, 0, 1), (1, 2, 1), (0, 1, 1), (2, 1, 1)
    ]
    empty_face_centers = [(x, y, z) for x, y, z in face_centers if board[x][y][z] == 0]
    if empty_face_centers:
        return random.choice(empty_face_centers)
    
    # Any remaining empty cell
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] == 0:
                    return (x, y, z)
    
    return (0, 0, 0)  # Should never reach here in a valid game
