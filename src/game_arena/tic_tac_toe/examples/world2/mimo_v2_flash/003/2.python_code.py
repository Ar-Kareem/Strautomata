
def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Smart policy for 4x4 Tic Tac Toe.
    Priorities:
    1. Win if possible
    2. Block opponent's immediate win
    3. Take center positions
    4. Take corners
    5. Take remaining empty cells
    """
    
    # Helper to find a winning move in a line
    def find_winning_move(line, player):
        count = sum(1 for cell in line if cell == player)
        empty_count = sum(1 for cell in line if cell == 0)
        if count == 3 and empty_count == 1:
            for i, cell in enumerate(line):
                if cell == 0:
                    return i
        return None
    
    # Check rows for winning move (1 = me)
    for row in range(4):
        line = [board[row][col] for col in range(4)]
        col = find_winning_move(line, 1)
        if col is not None:
            return (row, col)
    
    # Check columns for winning move
    for col in range(4):
        line = [board[row][col] for row in range(4)]
        row = find_winning_move(line, 1)
        if row is not None:
            return (row, col)
    
    # Check main diagonal
    line = [board[i][i] for i in range(4)]
    pos = find_winning_move(line, 1)
    if pos is not None:
        return (pos, pos)
    
    # Check anti-diagonal
    line = [board[i][3-i] for i in range(4)]
    pos = find_winning_move(line, 1)
    if pos is not None:
        return (pos, 3-pos)
    
    # Block opponent's winning move
    for row in range(4):
        line = [board[row][col] for col in range(4)]
        col = find_winning_move(line, -1)
        if col is not None:
            return (row, col)
    
    for col in range(4):
        line = [board[row][col] for row in range(4)]
        row = find_winning_move(line, -1)
        if row is not None:
            return (row, col)
    
    line = [board[i][i] for i in range(4)]
    pos = find_winning_move(line, -1)
    if pos is not None:
        return (pos, pos)
    
    line = [board[i][3-i] for i in range(4)]
    pos = find_winning_move(line, -1)
    if pos is not None:
        return (pos, 3-pos)
    
    # Strategic positioning
    # Center cells are most valuable
    center_cells = [(1,1), (1,2), (2,1), (2,2)]
    for r, c in center_cells:
        if board[r][c] == 0:
            return (r, c)
    
    # Corners are next best
    corners = [(0,0), (0,3), (3,0), (3,3)]
    for r, c in corners:
        if board[r][c] == 0:
            return (r, c)
    
    # Any remaining cell
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                return (r, c)
    
    # Fallback (shouldn't reach here)
    return (0, 0)
