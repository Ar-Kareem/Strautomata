
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Flatten the board for easier processing
    # Check all possible lines for winning opportunities
    
    # Helper to check if a line of 3 positions is all the same (and not empty)
    def is_winning_line(line):
        if len(set(line)) == 1 and line[0] != 0:
            return line[0]
        return 0
    
    # Helper to get positions given indices
    def get_pos(x, y, z):
        return board[x][y][z]
    
    # Helper to set position (this won't be used but for reference)
    def set_pos(x, y, z, value):
        board[x][y][z] = value
    
    # Check all possible winning lines
    lines = []
    
    # Rows (3 per layer, 3 layers)
    for z in range(3):
        for y in range(3):
            line = [get_pos(x, y, z) for x in range(3)]
            lines.append(line)
    
    # Columns (3 per layer, 3 layers)
    for z in range(3):
        for x in range(3):
            line = [get_pos(x, y, z) for y in range(3)]
            lines.append(line)
    
    # Depth-wise lines (3 per row, 3 columns)
    for y in range(3):
        for x in range(3):
            line = [get_pos(x, y, z) for z in range(3)]
            lines.append(line)
    
    # Diagonals in each layer (2 per layer, 3 layers)
    # Main diagonal in X (0,0,0) -> (1,1,1) -> (2,2,2) for each layer
    for z in range(3):
        line = [get_pos(i, i, z) for i in range(3)]
        lines.append(line)
    # Anti-diagonal in X (0,2,0) -> (1,1,1) -> (2,0,2) for each layer  
    for z in range(3):
        line = [get_pos(i, 2-i, z) for i in range(3)]
        lines.append(line)
        
    # Space diagonals (4 main ones)
    # (0,0,0) -> (1,1,1) -> (2,2,2)
    line = [get_pos(i, i, i) for i in range(3)]
    lines.append(line)
    # (0,0,2) -> (1,1,1) -> (2,2,0)  
    line = [get_pos(i, i, 2-i) for i in range(3)]
    lines.append(line)
    # (0,2,0) -> (1,1,1) -> (2,0,2)
    line = [get_pos(i, 2-i, i) for i in range(3)]
    lines.append(line)
    # (0,2,2) -> (1,1,1) -> (2,0,0)
    line = [get_pos(i, 2-i, 2-i) for i in range(3)]
    lines.append(line)
        
    # Check if we can win or need to block
    # Look for lines with 2 of our marks and one empty spot
    for i, line in enumerate(lines):
        if line.count(1) == 2 and line.count(0) == 1:
            # We can win - find the empty spot
            empty_index = line.index(0)
            # This is a bit tricky due to line format, so let's recalculate more carefully
            pass
        if line.count(-1) == 2 and line.count(0) == 1:
            # Need to block - find the empty spot
            empty_index = line.index(0)
            pass
    
    # Simpler approach: go through all lines and positions, 
    # find the first winning or blocking opportunity
    
    # Function to get all positions in a specific line type
    def check_lines():
        # Check for win or block opportunity in all lines
        # For each line, if it has 2 of the same player and 1 empty, 
        # return the position of that empty space
        # Check horizontal lines (z-layer)
        for z in range(3):
            for y in range(3):
                positions = [(x, y, z) for x in range(3)]
                values = [get_pos(x, y, z) for x in range(3)]
                if values.count(1) == 2 and values.count(0) == 1:
                    empty_index = values.index(0)
                    return positions[empty_index]
                if values.count(-1) == 2 and values.count(0) == 1:
                    empty_index = values.index(0)
                    return positions[empty_index] 
        
        # Check vertical lines (y-layer)
        for z in range(3):
            for x in range(3):
                positions = [(x, y, z) for y in range(3)]
                values = [get_pos(x, y, z) for y in range(3)]
                if values.count(1) == 2 and values.count(0) == 1:
                    empty_index = values.index(0)
                    return positions[empty_index]
                if values.count(-1) == 2 and values.count(0) == 1:
                    empty_index = values.index(0)
                    return positions[empty_index]
        
        # Check depth-wise lines (x-layer)
        for y in range(3):
            for x in range(3):
                positions = [(x, y, z) for z in range(3)]
                values = [get_pos(x, y, z) for z in range(3)]
                if values.count(1) == 2 and values.count(0) == 1:
                    empty_index = values.index(0)
                    return positions[empty_index]
                if values.count(-1) == 2 and values.count(0) == 1:
                    empty_index = values.index(0)
                    return positions[empty_index]
        
        # Check diagonals in each layer
        for z in range(3):
            # Main diagonal
            positions = [(i, i, z) for i in range(3)]
            values = [get_pos(i, i, z) for i in range(3)]
            if values.count(1) == 2 and values.count(0) == 1:
                empty_index = values.index(0)
                return positions[empty_index]
            if values.count(-1) == 2 and values.count(0) == 1:
                empty_index = values.index(0)
                return positions[empty_index]
            
            # Anti-diagonal
            positions = [(i, 2-i, z) for i in range(3)]
            values = [get_pos(i, 2-i, z) for i in range(3)]
            if values.count(1) == 2 and values.count(0) == 1:
                empty_index = values.index(0)
                return positions[empty_index]
            if values.count(-1) == 2 and values.count(0) == 1:
                empty_index = values.index(0)
                return positions[empty_index]
        
        # Check space diagonals
        # (0,0,0) -> (1,1,1) -> (2,2,2)
        positions = [(i, i, i) for i in range(3)]
        values = [get_pos(i, i, i) for i in range(3)]
        if values.count(1) == 2 and values.count(0) == 1:
            empty_index = values.index(0)
            return positions[empty_index]
        if values.count(-1) == 2 and values.count(0) == 1:
            empty_index = values.index(0)
            return positions[empty_index]
        
        # (0,0,2) -> (1,1,1) -> (2,2,0)  
        positions = [(i, i, 2-i) for i in range(3)]
        values = [get_pos(i, i, 2-i) for i in range(3)]
        if values.count(1) == 2 and values.count(0) == 1:
            empty_index = values.index(0)
            return positions[empty_index]
        if values.count(-1) == 2 and values.count(0) == 1:
            empty_index = values.index(0)
            return positions[empty_index]
        
        # (0,2,0) -> (1,1,1) -> (2,0,2)
        positions = [(i, 2-i, i) for i in range(3)]
        values = [get_pos(i, 2-i, i) for i in range(3)]
        if values.count(1) == 2 and values.count(0) == 1:
            empty_index = values.index(0)
            return positions[empty_index]
        if values.count(-1) == 2 and values.count(0) == 1:
            empty_index = values.index(0)
            return positions[empty_index]
        
        # (0,2,2) -> (1,1,1) -> (2,0,0)
        positions = [(i, 2-i, 2-i) for i in range(3)]
        values = [get_pos(i, 2-i, 2-i) for i in range(3)]
        if values.count(1) == 2 and values.count(0) == 1:
            empty_index = values.index(0)
            return positions[empty_index]
        if values.count(-1) == 2 and values.count(0) == 1:
            empty_index = values.index(0)
            return positions[empty_index]
        
        # No immediate threat, return a good strategic move
        return None
    
    # Try to win, otherwise block, otherwise play strategically
    # Start with checking for immediate opportunities
    move = check_lines()
    if move is not None:
        return move
    
    # No winning/blocking move, play strategically
    # Prefer center
    if board[1][1][1] == 0:
        return (1, 1, 1)
    
    # Prefer corners if available
    corners = [(0,0,0), (0,0,2), (0,2,0), (0,2,2), (2,0,0), (2,0,2), (2,2,0), (2,2,2)]
    for x, y, z in corners:
        if board[x][y][z] == 0:
            return (x, y, z)
    
    # No strategic spots, pick first available cell
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] == 0:
                    return (x, y, z)
    
    # Should not reach here if board is valid
    return (0, 0, 0)
