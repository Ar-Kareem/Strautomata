
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    def get_all_winning_lines():
        """Generate all possible winning lines in 3D tic tac toe"""
        lines = []
        
        # Lines parallel to x-axis
        for y in range(3):
            for z in range(3):
                lines.append([(x, y, z) for x in range(3)])
        
        # Lines parallel to y-axis
        for x in range(3):
            for z in range(3):
                lines.append([(x, y, z) for y in range(3)])
        
        # Lines parallel to z-axis
        for x in range(3):
            for y in range(3):
                lines.append([(x, y, z) for z in range(3)])
        
        # Face diagonals on xy-planes (fixed z)
        for z in range(3):
            lines.append([(0, 0, z), (1, 1, z), (2, 2, z)])  # main diagonal
            lines.append([(0, 2, z), (1, 1, z), (2, 0, z)])  # anti diagonal
        
        # Face diagonals on xz-planes (fixed y)
        for y in range(3):
            lines.append([(0, y, 0), (1, y, 1), (2, y, 2)])  # main diagonal
            lines.append([(0, y, 2), (1, y, 1), (2, y, 0)])  # anti diagonal
        
        # Face diagonals on yz-planes (fixed x)
        for x in range(3):
            lines.append([(x, 0, 0), (x, 1, 1), (x, 2, 2)])  # main diagonal
            lines.append([(x, 0, 2), (x, 1, 1), (x, 2, 0)])  # anti diagonal
        
        # Space diagonals (corner to corner)
        lines.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
        lines.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
        lines.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
        lines.append([(2, 0, 0), (1, 1, 1), (0, 2, 2)])
        
        return lines
    
    def evaluate_line(line, board):
        """Evaluate a line and return (my_count, opponent_count, empty_positions)"""
        my_count = 0
        opponent_count = 0
        empty_positions = []
        
        for x, y, z in line:
            if board[x][y][z] == 1:
                my_count += 1
            elif board[x][y][z] == -1:
                opponent_count += 1
            else:
                empty_positions.append((x, y, z))
        
        return my_count, opponent_count, empty_positions
    
    def find_empty_cells(board):
        """Find all empty cells"""
        empty = []
        for x in range(3):
            for y in range(3):
                for z in range(3):
                    if board[x][y][z] == 0:
                        empty.append((x, y, z))
        return empty
    
    winning_lines = get_all_winning_lines()
    
    # Check for immediate win
    for line in winning_lines:
        my_count, opponent_count, empty_positions = evaluate_line(line, board)
        if my_count == 2 and opponent_count == 0 and len(empty_positions) == 1:
            return empty_positions[0]
    
    # Check for blocks needed (opponent about to win)
    for line in winning_lines:
        my_count, opponent_count, empty_positions = evaluate_line(line, board)
        if opponent_count == 2 and my_count == 0 and len(empty_positions) == 1:
            return empty_positions[0]
    
    # Strategic moves - prioritize center, then corners, then edges
    empty_cells = find_empty_cells(board)
    
    if not empty_cells:
        # Should not happen in a valid game state
        return (0, 0, 0)
    
    # Prioritize center
    if (1, 1, 1) in empty_cells:
        return (1, 1, 1)
    
    # Prioritize corners
    corners = [(0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),
               (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2)]
    for corner in corners:
        if corner in empty_cells:
            return corner
    
    # Take any remaining cell
    return empty_cells[0]
