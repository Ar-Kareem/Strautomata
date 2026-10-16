
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Generate all possible winning lines in 3D tic tac toe
    def get_all_lines():
        lines = []
        
        # Lines parallel to axes
        for i in range(3):
            for j in range(3):
                # Lines parallel to x-axis
                lines.append([(k, i, j) for k in range(3)])
                # Lines parallel to y-axis  
                lines.append([(i, k, j) for k in range(3)])
                # Lines parallel to z-axis
                lines.append([(i, j, k) for k in range(3)])
        
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
        
        # Space diagonals (corner to corner)
        lines.append([(i, i, i) for i in range(3)])
        lines.append([(i, i, 2-i) for i in range(3)])
        lines.append([(i, 2-i, i) for i in range(3)])
        lines.append([(2-i, i, i) for i in range(3)])
        
        return lines
    
    def get_line_state(line):
        """Return the state of a line: (my_count, opponent_count, empty_positions)"""
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
    
    def find_move_by_priority():
        all_lines = get_all_lines()
        
        # Priority 1: Win immediately
        for line in all_lines:
            my_count, opp_count, empty_pos = get_line_state(line)
            if my_count == 2 and opp_count == 0 and len(empty_pos) == 1:
                return empty_pos[0]
        
        # Priority 2: Block opponent's win
        for line in all_lines:
            my_count, opp_count, empty_pos = get_line_state(line)
            if opp_count == 2 and my_count == 0 and len(empty_pos) == 1:
                return empty_pos[0]
        
        # Priority 3: Create winning opportunities (two ways to win)
        for line in all_lines:
            my_count, opp_count, empty_pos = get_line_state(line)
            if my_count == 1 and opp_count == 0 and len(empty_pos) == 2:
                # Check if any of these positions would create multiple winning opportunities
                for pos in empty_pos:
                    win_opportunities = 0
                    for other_line in all_lines:
                        if pos in other_line:
                            other_my, other_opp, other_empty = get_line_state(other_line)
                            if other_opp == 0 and other_my >= 1 and len(other_empty) <= 2:
                                win_opportunities += 1
                    if win_opportunities >= 2:
                        return pos
        
        # Priority 4: Take center positions
        center_positions = [(1, 1, 1)]  # Absolute center
        for pos in center_positions:
            if board[pos[0]][pos[1]][pos[2]] == 0:
                return pos
        
        # Priority 5: Take face centers
        face_centers = [(1, 1, 0), (1, 1, 2), (1, 0, 1), (1, 2, 1), (0, 1, 1), (2, 1, 1)]
        for pos in face_centers:
            if board[pos[0]][pos[1]][pos[2]] == 0:
                return pos
        
        # Priority 6: Take corners
        corners = [(0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2), 
                  (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2)]
        for pos in corners:
            if board[pos[0]][pos[1]][pos[2]] == 0:
                return pos
        
        # Priority 7: Take any available position
        for x in range(3):
            for y in range(3):
                for z in range(3):
                    if board[x][y][z] == 0:
                        return (x, y, z)
        
        # Should never reach here in a valid game
        return (0, 0, 0)
    
    return find_move_by_priority()
