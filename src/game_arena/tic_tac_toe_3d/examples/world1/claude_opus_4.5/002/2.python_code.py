
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Generate all 49 winning lines in 3D tic-tac-toe
    lines = []
    
    # Rows, columns, pillars (27 lines)
    for i in range(3):
        for j in range(3):
            lines.append([(i, j, 0), (i, j, 1), (i, j, 2)])  # along z (pillars)
            lines.append([(i, 0, j), (i, 1, j), (i, 2, j)])  # along y
            lines.append([(0, i, j), (1, i, j), (2, i, j)])  # along x
    
    # Face diagonals on each z-layer (6 lines)
    for z in range(3):
        lines.append([(0, 0, z), (1, 1, z), (2, 2, z)])
        lines.append([(0, 2, z), (1, 1, z), (2, 0, z)])
    
    # Face diagonals on each y-layer (6 lines)
    for y in range(3):
        lines.append([(0, y, 0), (1, y, 1), (2, y, 2)])
        lines.append([(0, y, 2), (1, y, 1), (2, y, 0)])
    
    # Face diagonals on each x-layer (6 lines)
    for x in range(3):
        lines.append([(x, 0, 0), (x, 1, 1), (x, 2, 2)])
        lines.append([(x, 0, 2), (x, 1, 1), (x, 2, 0)])
    
    # Space diagonals (4 lines)
    lines.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
    lines.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
    lines.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
    lines.append([(0, 2, 2), (1, 1, 1), (2, 0, 0)])
    
    def get_val(pos):
        return board[pos[0]][pos[1]][pos[2]]
    
    def get_line_values(line):
        return [get_val(p) for p in line]
    
    # Check for immediate winning move
    for line in lines:
        vals = get_line_values(line)
        if vals.count(1) == 2 and vals.count(0) == 1:
            idx = vals.index(0)
            return line[idx]
    
    # Check for blocking move (opponent about to win)
    for line in lines:
        vals = get_line_values(line)
        if vals.count(-1) == 2 and vals.count(0) == 1:
            idx = vals.index(0)
            return line[idx]
    
    # Find all empty cells
    empty_cells = [(x, y, z) for x in range(3) for y in range(3) for z in range(3) if board[x][y][z] == 0]
    
    if not empty_cells:
        return (0, 0, 0)  # Should never happen in a valid game
    
    # Score each empty cell
    best_score = -float('inf')
    best_move = empty_cells[0]
    
    for cell in empty_cells:
        score = 0
        for line in lines:
            if cell in line:
                vals = get_line_values(line)
                my_count = vals.count(1)
                opp_count = vals.count(-1)
                
                # Line is only valuable if opponent hasn't blocked it
                if opp_count == 0:
                    # More of my pieces on line = better
                    score += (my_count + 1) ** 2
                # Consider defensive value
                elif my_count == 0:
                    score += opp_count * 1.5
        
        # Strong preference for center (on most lines)
        if cell == (1, 1, 1):
            score += 15
        # Preference for corners (on more lines than edges)
        elif cell[0] != 1 and cell[1] != 1 and cell[2] != 1:
            score += 5
        # Slight preference for face centers
        elif (cell[0] == 1 and cell[1] == 1) or (cell[1] == 1 and cell[2] == 1) or (cell[0] == 1 and cell[2] == 1):
            score += 3
        
        if score > best_score:
            best_score = score
            best_move = cell
    
    return best_move
