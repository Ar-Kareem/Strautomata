
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Generate all possible winning lines in 3D tic-tac-toe
    def get_all_lines():
        lines = []
        
        # Lines parallel to each axis
        for i in range(3):
            for j in range(3):
                # Lines parallel to z-axis
                lines.append([(i, j, k) for k in range(3)])
                # Lines parallel to y-axis
                lines.append([(i, k, j) for k in range(3)])
                # Lines parallel to x-axis
                lines.append([(k, i, j) for k in range(3)])
        
        # Face diagonals
        for i in range(3):
            # Diagonals on faces perpendicular to x-axis
            lines.append([(i, j, j) for j in range(3)])
            lines.append([(i, j, 2-j) for j in range(3)])
            
            # Diagonals on faces perpendicular to y-axis
            lines.append([(j, i, j) for j in range(3)])
            lines.append([(j, i, 2-j) for j in range(3)])
            
            # Diagonals on faces perpendicular to z-axis
            lines.append([(j, j, i) for j in range(3)])
            lines.append([(j, 2-j, i) for j in range(3)])
        
        # Space diagonals (4 total)
        lines.append([(i, i, i) for i in range(3)])
        lines.append([(i, i, 2-i) for i in range(3)])
        lines.append([(i, 2-i, i) for i in range(3)])
        lines.append([(2-i, i, i) for i in range(3)])
        
        # Remove duplicates
        unique_lines = []
        for line in lines:
            if line not in unique_lines:
                unique_lines.append(line)
        
        return unique_lines
    
    def get_line_state(line):
        values = [board[x][y][z] for x, y, z in line]
        return values
    
    def find_winning_move(player):
        for line in all_lines:
            values = get_line_state(line)
            if values.count(player) == 2 and values.count(0) == 1:
                # Found a winning/blocking opportunity
                for i, (x, y, z) in enumerate(line):
                    if values[i] == 0:
                        return (x, y, z)
        return None
    
    def get_empty_positions():
        positions = []
        for x in range(3):
            for y in range(3):
                for z in range(3):
                    if board[x][y][z] == 0:
                        positions.append((x, y, z))
        return positions
    
    all_lines = get_all_lines()
    
    # 1. Check if I can win immediately
    winning_move = find_winning_move(1)
    if winning_move:
        return winning_move
    
    # 2. Check if I need to block opponent
    blocking_move = find_winning_move(-1)
    if blocking_move:
        return blocking_move
    
    # 3. Strategic moves - prefer center positions and corners
    empty_positions = get_empty_positions()
    
    if not empty_positions:
        return (0, 0, 0)  # Shouldn't happen in a valid game
    
    # Priority order: center, corners, edges
    strategic_order = [
        (1, 1, 1),  # Center of cube
        (0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),  # Corners
        (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2),
        (1, 1, 0), (1, 1, 2), (1, 0, 1), (1, 2, 1),  # Face centers
        (0, 1, 1), (2, 1, 1),
    ]
    
    for pos in strategic_order:
        if pos in empty_positions:
            return pos
    
    # If none of the strategic positions are available, take the first empty position
    return empty_positions[0]
