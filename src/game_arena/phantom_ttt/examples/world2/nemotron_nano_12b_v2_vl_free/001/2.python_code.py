
def policy(board):
    def is_win(temp_board):
        for i in range(3):
            if all(temp_board[i][j] == 1 for j in range(3)):
                return True
            if all(temp_board[j][i] == 1 for j in range(3)):
                return True
        if all(board[i][i] == 1 for i in range(3)):
            return True
        if all(board[i][2 - i] == 1 for i in range(3)):
            return True
        return False

    available = [(i, j) for i in range(3) for j in range(3) if board[i][j] == 0]
    
    # Check for immediate winning moves
    for r, c in available:
        temp_board = [row.copy() for row in board]
        temp_board[r][c] = 1
        if is_win(temp_board):
            return (r, c)
    
    # Prioritize moves based on cell importance
    def cell_priority(cell):
        i, j = cell
        if (i, j) == (1, 1):  # Center
            return 0
        elif cell in [(0, 0), (0, 2), (2, 0), (2, 2)]:  # Corners
            return 1
        else:  # Edges
            return 2
    
    # Sort available cells by priority (ascending)
    available.sort(key=lambda cell: (cell_priority(cell), random.random()))
    
    # Return the highest priority move
    return available[0] if available else (0, 0)
