
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    def get_all_lines():
        """Get all possible winning lines in 3D tic-tac-toe"""
        lines = []
        
        # Lines within each layer
        for z in range(3):
            # Rows
            for y in range(3):
                lines.append([(x, y, z) for x in range(3)])
            # Columns
            for x in range(3):
                lines.append([(x, y, z) for y in range(3)])
            # Diagonals
            lines.append([(i, i, z) for i in range(3)])
            lines.append([(i, 2-i, z) for i in range(3)])
        
        # Vertical lines through layers
        for x in range(3):
            for y in range(3):
                lines.append([(x, y, z) for z in range(3)])
        
        # Diagonals through layers (same row/column)
        for x in range(3):
            for y in range(3):
                lines.append([(x, y, z) for z in range(3)])
        
        # Actually, let me redo this more systematically
        lines = []
        
        # All lines parallel to x-axis
        for y in range(3):
            for z in range(3):
                lines.append([(x, y, z) for x in range(3)])
        
        # All lines parallel to y-axis  
        for x in range(3):
            for z in range(3):
                lines.append([(x, y, z) for y in range(3)])
        
        # All lines parallel to z-axis
        for x in range(3):
            for y in range(3):
                lines.append([(x, y, z) for z in range(3)])
        
        # Diagonals in xy-plane for each z
        for z in range(3):
            lines.append([(i, i, z) for i in range(3)])
            lines.append([(i, 2-i, z) for i in range(3)])
        
        # Diagonals in xz-plane for each y
        for y in range(3):
            lines.append([(i, y, i) for i in range(3)])
            lines.append([(i, y, 2-i) for i in range(3)])
        
        # Diagonals in yz-plane for each x
        for x in range(3):
            lines.append([(x, i, i) for i in range(3)])
            lines.append([(x, i, 2-i) for i in range(3)])
        
        # Main space diagonals (corner to corner)
        lines.append([(i, i, i) for i in range(3)])
        lines.append([(i, i, 2-i) for i in range(3)])
        lines.append([(i, 2-i, i) for i in range(3)])
        lines.append([(2-i, i, i) for i in range(3)])
        
        return lines
    
    def get_line_state(line):
        """Get the state of a line: (my_count, opponent_count, empty_positions)"""
        my_count = 0
        opponent_count = 0
        empty_positions = []
        
        for x, y, z in line:
            cell = board[x][y][z]
            if cell == 1:
                my_count += 1
            elif cell == -1:
                opponent_count += 1
            else:
                empty_positions.append((x, y, z))
        
        return my_count, opponent_count, empty_positions
    
    def get_empty_positions():
        """Get all empty positions on the board"""
        empty = []
        for x in range(3):
            for y in range(3):
                for z in range(3):
                    if board[x][y][z] == 0:
                        empty.append((x, y, z))
        return empty
    
    lines = get_all_lines()
    empty_positions = get_empty_positions()
    
    if not empty_positions:
        return (0, 0, 0)  # Should not happen in a valid game state
    
    # Strategy 1: Win if possible
    for line in lines:
        my_count, opponent_count, empty_pos = get_line_state(line)
        if my_count == 2 and opponent_count == 0 and len(empty_pos) == 1:
            return empty_pos[0]
    
    # Strategy 2: Block opponent from winning
    for line in lines:
        my_count, opponent_count, empty_pos = get_line_state(line)
        if opponent_count == 2 and my_count == 0 and len(empty_pos) == 1:
            return empty_pos[0]
    
    # Strategy 3: Create multiple threats or take good positions
    # Score each empty position based on strategic value
    position_scores = {}
    
    for pos in empty_positions:
        score = 0
        x, y, z = pos
        
        # Center of cube is most valuable
        if (x, y, z) == (1, 1, 1):
            score += 100
        
        # Face centers are valuable
        elif (x == 1 and y == 1) or (x == 1 and z == 1) or (y == 1 and z == 1):
            score += 50
        
        # Edge centers are somewhat valuable
        elif [x, y, z].count(1) >= 1:
            score += 20
        
        # Corners can be good
        elif all(coord in [0, 2] for coord in [x, y, z]):
            score += 30
        
        # Count how many lines this position could help us win
        for line in lines:
            if pos in line:
                my_count, opponent_count, empty_pos = get_line_state(line)
                if opponent_count == 0:  # Only consider lines opponent doesn't control
                    if my_count == 1:  # We have one piece in this line
                        score += 10
                    elif my_count == 0:  # Empty line we could start
                        score += 3
        
        position_scores[pos] = score
    
    # Return the position with the highest score
    best_pos = max(position_scores.items(), key=lambda x: x[1])[0]
    return best_pos
