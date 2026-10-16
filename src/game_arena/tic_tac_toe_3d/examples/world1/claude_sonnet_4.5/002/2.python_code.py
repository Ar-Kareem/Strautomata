
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    def get_all_lines():
        lines = []
        
        # Lines parallel to each axis (27 lines)
        for i in range(3):
            for j in range(3):
                # Parallel to x-axis (z varies)
                lines.append([(i, j, k) for k in range(3)])
                # Parallel to y-axis (i varies)
                lines.append([(k, i, j) for k in range(3)])
                # Parallel to z-axis (j varies)
                lines.append([(i, k, j) for k in range(3)])
        
        # Face diagonals (18 lines)
        # xy-plane diagonals (z fixed)
        for k in range(3):
            lines.append([(i, i, k) for i in range(3)])
            lines.append([(i, 2-i, k) for i in range(3)])
        
        # xz-plane diagonals (y fixed)
        for j in range(3):
            lines.append([(i, j, i) for i in range(3)])
            lines.append([(i, j, 2-i) for i in range(3)])
        
        # yz-plane diagonals (x fixed)
        for i in range(3):
            lines.append([(i, j, j) for j in range(3)])
            lines.append([(i, j, 2-j) for j in range(3)])
        
        # Space diagonals (4 lines)
        lines.append([(i, i, i) for i in range(3)])
        lines.append([(i, i, 2-i) for i in range(3)])
        lines.append([(i, 2-i, i) for i in range(3)])
        lines.append([(2-i, i, i) for i in range(3)])
        
        return lines
    
    lines = get_all_lines()
    
    def check_line_for_move(line, player):
        """Returns position to play if line has 2 of player and 1 empty"""
        values = [board[x][y][z] for x, y, z in line]
        if values.count(player) == 2 and values.count(0) == 1:
            for x, y, z in line:
                if board[x][y][z] == 0:
                    return (x, y, z)
        return None
    
    # 1. Try to win
    for line in lines:
        move = check_line_for_move(line, 1)
        if move:
            return move
    
    # 2. Block opponent from winning
    for line in lines:
        move = check_line_for_move(line, -1)
        if move:
            return move
    
    # 3. Take center
    if board[1][1][1] == 0:
        return (1, 1, 1)
    
    # 4. Take corners
    corners = [
        (0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),
        (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2)
    ]
    for x, y, z in corners:
        if board[x][y][z] == 0:
            return (x, y, z)
    
    # 5. Take any available position
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] == 0:
                    return (x, y, z)
    
    return (0, 0, 0)
