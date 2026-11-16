
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    import itertools
    
    # Generate all possible winning lines in 3D Tic Tac Toe
    def get_all_lines():
        lines = []
        
        # Rows in each layer (z constant, y constant, x varies)
        for z in range(3):
            for y in range(3):
                lines.append([(z, y, x) for x in range(3)])
        
        # Columns in each layer (z constant, x constant, y varies)
        for z in range(3):
            for x in range(3):
                lines.append([(z, y, x) for y in range(3)])
        
        # Vertical pillars (x and y constant, z varies)
        for x in range(3):
            for y in range(3):
                lines.append([(z, y, x) for z in range(3)])
        
        # Diagonals in each layer
        for z in range(3):
            lines.append([(z, i, i) for i in range(3)])  # main diagonal
            lines.append([(z, i, 2-i) for i in range(3)])  # anti-diagonal
        
        # Diagonals in vertical planes (x constant)
        for x in range(3):
            lines.append([(i, i, x) for i in range(3)])
            lines.append([(i, 2-i, x) for i in range(3)])
        
        # Diagonals in vertical planes (y constant)
        for y in range(3):
            lines.append([(i, y, i) for i in range(3)])
            lines.append([(i, y, 2-i) for i in range(3)])
        
        # Space diagonals (4 main diagonals through the cube)
        lines.append([(i, i, i) for i in range(3)])
        lines.append([(i, i, 2-i) for i in range(3)])
        lines.append([(i, 2-i, i) for i in range(3)])
        lines.append([(2-i, i, i) for i in range(3)])
        
        return lines
    
    lines = get_all_lines()
    
    def get_cell(pos):
        z, y, x = pos
        return board[z][y][x]
    
    def check_line(line, player):
        """Check if a line has 2 of player and 1 empty, return empty position"""
        values = [get_cell(pos) for pos in line]
        if values.count(player) == 2 and values.count(0) == 1:
            for pos in line:
                if get_cell(pos) == 0:
                    return pos
        return None
    
    # 1. Try to win
    for line in lines:
        move = check_line(line, 1)
        if move:
            return move
    
    # 2. Block opponent from winning
    for line in lines:
        move = check_line(line, -1)
        if move:
            return move
    
    # 3. Take center if available
    if board[1][1][1] == 0:
        return (1, 1, 1)
    
    # 4. Take corners
    corners = list(itertools.product([0, 2], repeat=3))
    for corner in corners:
        if get_cell(corner) == 0:
            return corner
    
    # 5. Take any available move
    for z in range(3):
        for y in range(3):
            for x in range(3):
                if board[z][y][x] == 0:
                    return (z, y, x)
    
    # Should never reach here in a valid game
    return (0, 0, 0)
