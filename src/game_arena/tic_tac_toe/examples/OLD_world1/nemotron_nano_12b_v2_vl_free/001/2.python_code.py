
def policy(board):
    def is_winning(row, col, player):
        # Check row
        count_row = sum(board[row][j] == player for j in range(3) if j != col)
        if count_row == 2:
            return True
        # Check column
        count_col = sum(board[i][col] == player for i in range(3) if i != row)
        if count_col == 2:
            return True
        # Check main diagonal
        if row == col:
            count_diag = sum(board[i][i] == player for i in (0, 1, 2) if i != row)
            if count_diag == 2:
                return True
        # Check anti-diagonal
        if row + col == 2:
            count_anti_diag = sum(board[i][2 - i] == player for i in range(3) if i != row)
            if count_anti_diag == 2:
                return True
        return False

    # Check for winning moves (player 1)
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0 and is_winning(r, c, 1):
                return (r, c)
    # Check for blocking moves (opponent -1)
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0 and is_winning(r, c, -1):
                return (r, c)
    # Heuristic selection
    priority_positions = [(1,1), (0,0), (0,2), (2,0), (2,2), (0,1), (1,0), (1,2), (2,1)]
    for pos in priority_positions:
        r, c = pos
        if board[r][c] == 0:
            return (r, c)
    # Fallback (shouldn't be needed as board is assumed to have a move)
    return (0, 0)
