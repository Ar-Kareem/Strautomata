
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Get all empty positions
    empty_positions = []
    for z in range(3):
        for y in range(3):
            for x in range(3):
                if board[z][y][x] == 0:
                    empty_positions.append((z, y, x))
    
    if not empty_positions:
        return (0, 0, 0)  # Should not happen in valid game
    
    # Define all possible winning lines in 3D tic-tac-toe
    def get_all_lines():
        lines = []
        
        # Lines parallel to x-axis (rows)
        for z in range(3):
            for y in range(3):
                lines.append([(z, y, 0), (z, y, 1), (z, y, 2)])
        
        # Lines parallel to y-axis (columns)
        for z in range(3):
            for x in range(3):
                lines.append([(z, 0, x), (z, 1, x), (z, 2, x)])
        
        # Lines parallel to z-axis (depth)
        for y in range(3):
            for x in range(3):
                lines.append([(0, y, x), (1, y, x), (2, y, x)])
        
        # Face diagonals in xy planes
        for z in range(3):
            lines.append([(z, 0, 0), (z, 1, 1), (z, 2, 2)])
            lines.append([(z, 0, 2), (z, 1, 1), (z, 2, 0)])
        
        # Face diagonals in xz planes
        for y in range(3):
            lines.append([(0, y, 0), (1, y, 1), (2, y, 2)])
            lines.append([(0, y, 2), (1, y, 1), (2, y, 0)])
        
        # Face diagonals in yz planes
        for x in range(3):
            lines.append([(0, 0, x), (1, 1, x), (2, 2, x)])
            lines.append([(0, 2, x), (1, 1, x), (2, 0, x)])
        
        # Space diagonals (4 total)
        lines.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
        lines.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
        lines.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
        lines.append([(0, 2, 2), (1, 1, 1), (2, 0, 0)])
        
        return lines
    
    all_lines = get_all_lines()
    
    # Check if a line can lead to immediate win or needs immediate block
    def analyze_line(line, player):
        positions = [board[pos[0]][pos[1]][pos[2]] for pos in line]
        player_count = positions.count(player)
        opponent_count = positions.count(-player)
        empty_count = positions.count(0)
        
        # Can win (2 of mine, 1 empty)
        if player_count == 2 and empty_count == 1:
            empty_pos_idx = positions.index(0)
            return 'win', line[empty_pos_idx]
        
        # Must block (2 of opponent, 1 empty)
        if opponent_count == 2 and empty_count == 1:
            empty_pos_idx = positions.index(0)
            return 'block', line[empty_pos_idx]
            
        return None, None
    
    # Check for immediate wins
    for line in all_lines:
        action, pos = analyze_line(line, 1)  # I am player 1
        if action == 'win':
            return pos
    
    # Check for necessary blocks
    for line in all_lines:
        action, pos = analyze_line(line, 1)  # I am player 1, so opponent is -1
        if action == 'block':
            return pos
    
    # Strategic moves: prefer center, then corners, then edges
    def position_priority(pos):
        z, y, x = pos
        # Center of cube
        if (z, y, x) == (1, 1, 1):
            return 10
        # Face centers
        if sum([z == 1, y == 1, x == 1]) == 2:
            return 8
        # Corners of cube
        if all(coord in [0, 2] for coord in [z, y, x]):
            return 7
        # Edge centers
        if sum([coord == 1 for coord in [z, y, x]]) == 1:
            return 6
        # Face corners (corners of faces but not cube corners)
        return 5
    
    # Choose position with highest priority
    best_pos = max(empty_positions, key=position_priority)
    return best_pos
