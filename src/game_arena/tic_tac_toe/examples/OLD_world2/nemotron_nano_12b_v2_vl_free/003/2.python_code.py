
def policy(board):
    def is_win(player, row, col):
        # Check row
        row_count = 0
        for c in range(4):
            if c == col:
                continue
            if board[row][c] == player:
                row_count += 1
        if row_count == 3:
            return True
        
        # Check column
        col_count = 0
        for r in range(4):
            if r == row:
                continue
            if board[r][col] == player:
                col_count += 1
        if col_count == 3:
            return True
        
        # Check main diagonal (row == col)
        if row == col:
            diag_count = 0
            for i in range(4):
                if (i, i) == (row, col):
                    continue
                if board[i][i] == player:
                    diag_count += 1
            if diag_count == 3:
                return True
        
        # Check anti-diagonal (row + col == 3)
        if row + col == 3:
            anti_count = 0
            for i in range(4):
                j = 3 - i
                if (i, j) == (row, col):
                    continue
                if board[i][j] == player:
                    anti_count += 1
            if anti_count == 3:
                return True
        
        return False
    
    # Step 1: Check if current player can win immediately
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0 and is_win(1, r, c):
                return (r, c)
    
    # Step 2: Check if opponent can win and block it
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0 and is_win(-1, r, c):
                return (r, c)
    
    # Step 3: Choose best move based on predefined priority order
    priority_order = [
        (1, 1), (1, 2), (2, 1), (2, 2),  # Center cells
        (0, 0), (0, 3), (3, 0), (3, 3),  # Corners
        (0, 1), (0, 2), (3, 1), (3, 2),  # Top and bottom edge centers
        (1, 0), (1, 3), (2, 0), (2, 3)   # Side edges
    ]
    
    # Find the first empty cell in the priority order
    for r, c in priority_order:
        if board[r][c] == 0:
            return (r, c)
    
    # Fallback (should not occur)
    return (-1, -1)
