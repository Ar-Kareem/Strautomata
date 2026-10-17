
def policy(board: list[list[int]]) -> tuple[int, int]:
    def check_win(board, row, col, player):
        """Check if placing player at (row, col) would result in a win"""
        # Temporarily place the piece
        board[row][col] = player
        
        # Check horizontal
        if all(board[row][c] == player for c in range(4)):
            board[row][col] = 0  # Restore
            return True
            
        # Check vertical
        if all(board[r][col] == player for r in range(4)):
            board[row][col] = 0  # Restore
            return True
            
        # Check main diagonal
        if row == col and all(board[i][i] == player for i in range(4)):
            board[row][col] = 0  # Restore
            return True
            
        # Check anti-diagonal
        if row + col == 3 and all(board[i][3-i] == player for i in range(4)):
            board[row][col] = 0  # Restore
            return True
            
        board[row][col] = 0  # Restore
        return False
    
    def get_empty_positions(board):
        """Get all empty positions on the board"""
        empty = []
        for i in range(4):
            for j in range(4):
                if board[i][j] == 0:
                    empty.append((i, j))
        return empty
    
    def position_value(row, col):
        """Heuristic value for position - center > corner > edge"""
        if (row, col) in [(1, 1), (1, 2), (2, 1), (2, 2)]:  # Center positions
            return 3
        elif (row, col) in [(0, 0), (0, 3), (3, 0), (3, 3)]:  # Corners
            return 2
        else:  # Edges
            return 1
    
    empty_positions = get_empty_positions(board)
    
    # Priority 1: Check if we can win
    for row, col in empty_positions:
        if check_win(board, row, col, 1):  # 1 is our player
            return (row, col)
    
    # Priority 2: Check if we need to block opponent
    for row, col in empty_positions:
        if check_win(board, row, col, -1):  # -1 is opponent
            return (row, col)
    
    # Priority 3: Choose best strategic position
    if empty_positions:
        best_move = max(empty_positions, key=lambda pos: position_value(pos[0], pos[1]))
        return best_move
    
    # Fallback (should never reach here in a valid game)
    return (0, 0)
