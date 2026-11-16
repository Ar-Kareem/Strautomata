
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    Policy for 3D Tic Tac Toe on a 3x3x3 board.
    Returns the best move as (z, y, x) coordinates.
    """
    
    def get_all_lines():
        """Generate all 49 winning lines in 3D tic-tac-toe."""
        lines = []
        
        # Lines parallel to each axis
        for i in range(3):
            for j in range(3):
                # Parallel to x-axis
                lines.append([(i, j, k) for k in range(3)])
                # Parallel to y-axis
                lines.append([(i, k, j) for k in range(3)])
                # Parallel to z-axis
                lines.append([(k, i, j) for k in range(3)])
        
        # Face diagonals
        for i in range(3):
            # xy-plane diagonals (fixed z)
            lines.append([(i, j, j) for j in range(3)])
            lines.append([(i, j, 2-j) for j in range(3)])
            # xz-plane diagonals (fixed y)
            lines.append([(j, i, j) for j in range(3)])
            lines.append([(j, i, 2-j) for j in range(3)])
            # yz-plane diagonals (fixed x)
            lines.append([(j, j, i) for j in range(3)])
            lines.append([(j, 2-j, i) for j in range(3)])
        
        # Space diagonals
        lines.append([(i, i, i) for i in range(3)])
        lines.append([(i, i, 2-i) for i in range(3)])
        lines.append([(i, 2-i, i) for i in range(3)])
        lines.append([(i, 2-i, 2-i) for i in range(3)])
        
        return lines
    
    def check_line_for_win(line, player):
        """Check if a player can win by completing this line."""
        values = [board[z][y][x] for z, y, x in line]
        if values.count(player) == 2 and values.count(0) == 1:
            # Find the empty spot
            for z, y, x in line:
                if board[z][y][x] == 0:
                    return (z, y, x)
        return None
    
    def get_empty_cells():
        """Get all empty cells."""
        empty = []
        for z in range(3):
            for y in range(3):
                for x in range(3):
                    if board[z][y][x] == 0:
                        empty.append((z, y, x))
        return empty
    
    lines = get_all_lines()
    
    # 1. Check if we can win
    for line in lines:
        move = check_line_for_win(line, 1)
        if move:
            return move
    
    # 2. Check if we need to block opponent
    for line in lines:
        move = check_line_for_win(line, -1)
        if move:
            return move
    
    # 3. Take center if available
    if board[1][1][1] == 0:
        return (1, 1, 1)
    
    # 4. Take corners
    corners = [
        (0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),
        (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2)
    ]
    for corner in corners:
        z, y, x = corner
        if board[z][y][x] == 0:
            return corner
    
    # 5. Take any available move
    empty_cells = get_empty_cells()
    if empty_cells:
        return empty_cells[0]
    
    # Fallback (should never reach here in a valid game)
    return (0, 0, 0)
