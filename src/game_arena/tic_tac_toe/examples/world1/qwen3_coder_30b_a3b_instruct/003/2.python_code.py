
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Check for winning move or blocking move
    def get_winning_move(player):
        # Check rows, columns and diagonals
        for i in range(3):
            # Check rows
            if board[i].count(player) == 2 and board[i].count(0) == 1:
                return (i, board[i].index(0))
            
            # Check columns  
            col = [board[j][i] for j in range(3)]
            if col.count(player) == 2 and col.count(0) == 1:
                return (col.index(0), i)
        
        # Check main diagonal
        diag1 = [board[i][i] for i in range(3)]
        if diag1.count(player) == 2 and diag1.count(0) == 1:
            idx = diag1.index(0)
            return (idx, idx)
        
        # Check anti-diagonal
        diag2 = [board[i][2-i] for i in range(3)]
        if diag2.count(player) == 2 and diag2.count(0) == 1:
            idx = diag2.index(0)
            return (idx, 2-idx)
        
        return None
    
    # Try to win first
    win_move = get_winning_move(1)
    if win_move:
        return win_move
    
    # Try to block opponent from winning
    block_move = get_winning_move(-1) 
    if block_move:
        return block_move
    
    # Take center if available
    if board[1][1] == 0:
        return (1, 1)
    
    # Take a corner if available
    corners = [(0,0), (0,2), (2,0), (2,2)]
    for r, c in corners:
        if board[r][c] == 0:
            return (r, c)
    
    # Take any available spot
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                return (i, j)
    
    # Should never reach here in valid game state
    return (0, 0)
