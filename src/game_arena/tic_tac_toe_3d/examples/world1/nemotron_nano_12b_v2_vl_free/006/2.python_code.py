
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Generate all possible lines for win/block checks
    def generate_lines():
        lines = []
        # Orthogonal lines (axis-aligned)
        for y in range(3):
            for z in range(3):
                lines.append([(x, y, z) for x in range(3)])  # x-axis
        for x in range(3):
            for z in range(3):
                lines.append([(x, y, z) for y in range(3)])  # y-axis
        for x in range(3):
            for y in range(3):
                lines.append([(x, y, z) for z in range(3)])  # z-axis
                
        # Plane diagonals (2D diagonals in faces)
        for x in range(3):
            lines.append([(x, y, y) for y in range(3)])        # x-fixed diagonals
            lines.append([(x, y, 2 - y) for y in range(3)])    # x-fixed opposite diagonals
        for y in range(3):
            lines.append([(x, y, x) for x in range(3)])        # y-fixed diagonals
            lines.append([(x, y, 2 - x) for x in range(3)])    # y-fixed opposite diagonals
        for z in range(3):
            lines.append([(x, x, z) for x in range(3)])        # z-fixed diagonals
            lines.append([(x, 2 - x, z) for x in range(3)])    # z-fixed opposite diagonals
            
        # Space diagonals (4 main cube diagonals)
        space_diags = [
            [(i, i, i) for i in range(3)],                # Main space diagonal
            [(i, i, 2 - i) for i in range(3)],            # Top-back to bottom-front
            [(i, 2 - i, i) for i in range(3)],            # Top-front to bottom-back
            [(i, 2 - i, 2 - i) for i in range(3)]         # Top-right to bottom-left
        ]
        lines.extend(space_diags)
        
        return lines
    
    lines = generate_lines()
    
    # Check for immediate winning moves
    for line in lines:
        count = 0
        empty_pos = None
        for (x, y, z) in line:
            val = board[x][y][z]
            if val == 1:
                count += 1
            elif val == -1:
                count = -1  # Opponent's mark breaks this line
                break
            else:  # Val == 0
                if empty_pos is None:
                    empty_pos = (x, y, z)
        if count == 2 and empty_pos:
            return empty_pos
    
    # Check for opponent's blocking move
    for line in lines:
        count_neg = 0
        empty_pos = None
        for (x, y, z) in line:
            val = board[x][y][z]
            if val == -1:
                count_neg += 1
            elif val == 1:
                break  # Line contains my mark, can't block
            else:  # Val == 0
                if empty_pos is None:
                    empty_pos = (x, y, z)
        if count_neg == 2 and empty_pos:
            return empty_pos  # Block opponent's 3-in-a-row
    
    # Priority cell selection for optimal play
    candidates = [
        (1, 1, 1),  # Center cell (highest priority)
        # Corners (all available)
        (0, 0, 0), (0, 0, 2),
        (0, 2, 0), (0, 2, 2),
        (2, 0, 0), (2, 0, 2),
        (2, 2, 0), (2, 2, 2),
        # Edge center cells
        (0, 0, 1),
        (0, 1, 0), (0, 1, 2),
        (1, 0, 0), (1, 0, 2),
        (2, 0, 0), (2, 0, 2),
        (2, 1, 0), (2, 1, 2),
        (0, 2, 1),
        (2, 2, 1),
        # Face centers
        (0, 1, 1), (2, 1, 1),
        (1, 0, 1), (1, 2, 1),
        (1, 1, 0), (1, 1, 2)
    ]
    
    # Select first available cell in priority order
    for cell in candidates:
        if board[cell[0]][cell[1]][cell[2]] == 0:
            return cell
    
    # Fallback (should never reach here if board is valid)
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] == 0:
                    return (x, y, z)
    
    raise ValueError("No valid move found (should never occur)")
