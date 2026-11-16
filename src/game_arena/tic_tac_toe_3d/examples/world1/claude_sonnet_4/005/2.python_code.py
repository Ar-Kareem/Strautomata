
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    def get_all_winning_lines():
        lines = []
        
        # Lines along each axis
        for i in range(3):
            for j in range(3):
                # Lines along x-axis
                lines.append([(x, i, j) for x in range(3)])
                # Lines along y-axis
                lines.append([(i, x, j) for x in range(3)])
                # Lines along z-axis
                lines.append([(i, j, x) for x in range(3)])
        
        # Diagonals in xy planes (fixed z)
        for z in range(3):
            lines.append([(0, 0, z), (1, 1, z), (2, 2, z)])  # main diagonal
            lines.append([(0, 2, z), (1, 1, z), (2, 0, z)])  # anti-diagonal
        
        # Diagonals in xz planes (fixed y)
        for y in range(3):
            lines.append([(0, y, 0), (1, y, 1), (2, y, 2)])  # main diagonal
            lines.append([(0, y, 2), (1, y, 1), (2, y, 0)])  # anti-diagonal
        
        # Diagonals in yz planes (fixed x)
        for x in range(3):
            lines.append([(x, 0, 0), (x, 1, 1), (x, 2, 2)])  # main diagonal
            lines.append([(x, 0, 2), (x, 1, 1), (x, 2, 0)])  # anti-diagonal
        
        # Space diagonals (corner to corner)
        lines.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
        lines.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
        lines.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
        lines.append([(0, 2, 2), (1, 1, 1), (2, 0, 0)])
        
        return lines
    
    def get_line_state(line):
        values = [board[x][y][z] for x, y, z in line]
        return values
    
    def get_empty_cells():
        empty = []
        for x in range(3):
            for y in range(3):
                for z in range(3):
                    if board[x][y][z] == 0:
                        empty.append((x, y, z))
        return empty
    
    def can_win_or_block(player):
        # Check if player can win in one move, or if we need to block
        for line in winning_lines:
            values = get_line_state(line)
            if values.count(player) == 2 and values.count(0) == 1:
                # Find the empty position
                for x, y, z in line:
                    if board[x][y][z] == 0:
                        return (x, y, z)
        return None
    
    def evaluate_position(pos):
        # Heuristic: prefer center positions, then corners, then edges
        x, y, z = pos
        score = 0
        
        # Center of cube is most valuable
        if (x, y, z) == (1, 1, 1):
            score += 10
        
        # Face centers are good
        elif (x == 1 and y == 1) or (x == 1 and z == 1) or (y == 1 and z == 1):
            score += 5
        
        # Edge centers
        elif x == 1 or y == 1 or z == 1:
            score += 3
        
        # Corners
        elif all(coord in [0, 2] for coord in [x, y, z]):
            score += 4
        
        return score
    
    winning_lines = get_all_winning_lines()
    empty_cells = get_empty_cells()
    
    if not empty_cells:
        return (0, 0, 0)  # Should not happen in valid game state
    
    # 1. Check if I can win
    winning_move = can_win_or_block(1)  # I am player 1
    if winning_move:
        return winning_move
    
    # 2. Check if I need to block opponent
    blocking_move = can_win_or_block(-1)  # Opponent is player -1
    if blocking_move:
        return blocking_move
    
    # 3. Choose best strategic position
    best_move = max(empty_cells, key=evaluate_position)
    return best_move
