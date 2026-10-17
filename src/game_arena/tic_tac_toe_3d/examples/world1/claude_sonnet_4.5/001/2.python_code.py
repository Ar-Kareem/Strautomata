
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    import random
    
    # Define all 49 winning lines in 3D Tic Tac Toe
    winning_lines = []
    
    # Lines within each layer (z-plane)
    for z in range(3):
        # Rows
        for x in range(3):
            winning_lines.append([(x, 0, z), (x, 1, z), (x, 2, z)])
        # Columns
        for y in range(3):
            winning_lines.append([(0, y, z), (1, y, z), (2, y, z)])
        # Diagonals
        winning_lines.append([(0, 0, z), (1, 1, z), (2, 2, z)])
        winning_lines.append([(0, 2, z), (1, 1, z), (2, 0, z)])
    
    # Lines within each x-plane
    for x in range(3):
        # Rows (along z)
        for y in range(3):
            winning_lines.append([(x, y, 0), (x, y, 1), (x, y, 2)])
        # Diagonals
        winning_lines.append([(x, 0, 0), (x, 1, 1), (x, 2, 2)])
        winning_lines.append([(x, 0, 2), (x, 1, 1), (x, 2, 0)])
    
    # Lines within each y-plane
    for y in range(3):
        # Diagonals (rows and columns already counted)
        winning_lines.append([(0, y, 0), (1, y, 1), (2, y, 2)])
        winning_lines.append([(0, y, 2), (1, y, 1), (2, y, 0)])
    
    # 4 space diagonals
    winning_lines.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
    winning_lines.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
    winning_lines.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
    winning_lines.append([(0, 2, 2), (1, 1, 1), (2, 0, 0)])
    
    def check_line(line, player):
        """Check if a line has 2 of player's pieces and 1 empty spot. Return empty spot if so."""
        values = [board[x][y][z] for x, y, z in line]
        if values.count(player) == 2 and values.count(0) == 1:
            for i, (x, y, z) in enumerate(line):
                if values[i] == 0:
                    return (x, y, z)
        return None
    
    # 1. Check for winning move
    for line in winning_lines:
        move = check_line(line, 1)
        if move:
            return move
    
    # 2. Check for blocking move
    for line in winning_lines:
        move = check_line(line, -1)
        if move:
            return move
    
    # 3. Strategic moves
    # Prefer center, then corners, then edges
    
    # Center
    if board[1][1][1] == 0:
        return (1, 1, 1)
    
    # Corners
    corners = [
        (0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),
        (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2)
    ]
    random.shuffle(corners)
    for x, y, z in corners:
        if board[x][y][z] == 0:
            return (x, y, z)
    
    # Face centers
    face_centers = [
        (1, 1, 0), (1, 1, 2), (1, 0, 1), (1, 2, 1), (0, 1, 1), (2, 1, 1)
    ]
    random.shuffle(face_centers)
    for x, y, z in face_centers:
        if board[x][y][z] == 0:
            return (x, y, z)
    
    # Any remaining move
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] == 0:
                    return (x, y, z)
    
    # Should never reach here if there's a valid move
    return (0, 0, 0)
