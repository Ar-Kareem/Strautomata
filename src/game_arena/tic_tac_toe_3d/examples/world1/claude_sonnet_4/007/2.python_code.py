
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    def get_all_lines():
        """Generate all possible winning lines in 3D tic-tac-toe"""
        lines = []
        
        # Straight lines along each axis
        for i in range(3):
            for j in range(3):
                # Lines along z-axis
                lines.append([(i, j, 0), (i, j, 1), (i, j, 2)])
                # Lines along y-axis  
                lines.append([(i, 0, j), (i, 1, j), (i, 2, j)])
                # Lines along x-axis
                lines.append([(0, i, j), (1, i, j), (2, i, j)])
        
        # Face diagonals
        for i in range(3):
            # XY plane diagonals (fixed z)
            lines.append([(0, 0, i), (1, 1, i), (2, 2, i)])
            lines.append([(0, 2, i), (1, 1, i), (2, 0, i)])
            # XZ plane diagonals (fixed y)
            lines.append([(0, i, 0), (1, i, 1), (2, i, 2)])
            lines.append([(0, i, 2), (1, i, 1), (2, i, 0)])
            # YZ plane diagonals (fixed x)
            lines.append([(i, 0, 0), (i, 1, 1), (i, 2, 2)])
            lines.append([(i, 0, 2), (i, 1, 1), (i, 2, 0)])
        
        # Space diagonals
        lines.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
        lines.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
        lines.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
        lines.append([(2, 0, 0), (1, 1, 1), (0, 2, 2)])
        
        return lines
    
    def get_line_state(line):
        """Get the state of a line: (my_count, opp_count, empty_positions)"""
        my_count = 0
        opp_count = 0
        empty_pos = []
        
        for x, y, z in line:
            val = board[x][y][z]
            if val == 1:
                my_count += 1
            elif val == -1:
                opp_count += 1
            else:
                empty_pos.append((x, y, z))
        
        return my_count, opp_count, empty_pos
    
    def evaluate_position(pos):
        """Evaluate how good a position is"""
        x, y, z = pos
        if board[x][y][z] != 0:
            return -1000  # Position is occupied
        
        score = 0
        win_move = False
        block_move = False
        
        for line in lines:
            if pos in line:
                my_count, opp_count, empty_pos = get_line_state(line)
                
                # Check if this move wins the game
                if my_count == 2 and opp_count == 0 and len(empty_pos) == 1:
                    win_move = True
                    score += 1000
                
                # Check if this move blocks opponent win
                elif opp_count == 2 and my_count == 0 and len(empty_pos) == 1:
                    block_move = True
                    score += 500
                
                # Evaluate other strategic positions
                elif my_count > 0 and opp_count == 0:
                    score += my_count * 10
                elif my_count == 0 and opp_count == 0:
                    score += 1
        
        # Bonus for center position
        if pos == (1, 1, 1):
            score += 20
        
        # Bonus for corner positions
        elif all(coord in [0, 2] for coord in pos):
            score += 5
        
        return score
    
    lines = get_all_lines()
    
    # Get all empty positions
    empty_positions = []
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    empty_positions.append((i, j, k))
    
    if not empty_positions:
        return (0, 0, 0)  # Shouldn't happen in a valid game
    
    # Evaluate all positions and choose the best one
    best_pos = None
    best_score = -2000
    
    for pos in empty_positions:
        score = evaluate_position(pos)
        if score > best_score:
            best_score = score
            best_pos = pos
    
    return best_pos if best_pos else empty_positions[0]
