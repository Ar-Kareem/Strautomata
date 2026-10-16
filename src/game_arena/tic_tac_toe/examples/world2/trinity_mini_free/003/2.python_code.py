
def check_win(board, player):
    # Check rows
    for i in range(4):
        if all(board[i][j] == player for j in range(4)):
            return True
    # Check columns
    for j in range(4):
        if all(board[i][j] == player for i in range(4)):
            return True
    # Check main diagonal
    if all(board[i][i] == player for i in range(4)):
        return True
    # Check anti-diagonal
    if all(board[i][3-i] == player for i in range(4)):
        return True
    return False

def policy(board):
    # Check for winning moves
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                board[i][j] = 1
                if check_win(board, 1):
                    board[i][j] = 0
                    return (i, j)
                board[i][j] = 0
    
    # Check for blocking opponent's win
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                board[i][j] = -1
                if check_win(board, -1):
                    board[i][j] = 0
                    return (i, j)
                board[i][j] = 0
    
    # Check for forks (two winning threats)
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                board[i][j] = 1
                # Check if this move creates two winning threats
                threats = 0
                # Check rows
                for k in range(4):
                    if board[k][j] == 1 and board[k][0] == 1 and board[k][1] == 1 and board[k][2] == 1 and board[k][3] == 1:
                        threats += 1
                # Check columns
                for k in range(4):
                    if board[k][j] == 1 and board[0][k] == 1 and board[1][k] == 1 and board[2][k] == 1 and board[3][k] == 1:
                        threats += 1
                # Check diagonals
                if board[0][0] == 1 and board[1][1] == 1 and board[2][2] == 1 and board[3][3] == 1:
                    threats += 1
                if board[0][3] == 1 and board[1][2] == 1 and board[2][1] == 1 and board[3][0] == 1:
                    threats += 1
                if threats >= 2:
                    board[i][j] = 0
                    return (i, j)
                board[i][j] = 0
    
    # Place in center cells
    centers = [(1,1), (1,2), (2,1), (2,2)]
    for pos in centers:
        i, j = pos
        if board[i][j] == 0:
            return (i, j)
    
    # Place in corners
    corners = [(0,0), (0,3), (3,0), (3,3)]
    for pos in corners:
        i, j = pos
        if board[i][j] == 0:
            return (i, j)
    
    # Place in edges
    edges = [(0,1), (0,2), (1,0), (1,3), (2,0), (2,3), (3,1), (3,2)]
    for pos in edges:
        i, j = pos
        if board[i][j] == 0:
            return (i, j)
    
    # Fallback: return any empty cell
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                return (i, j)
    return (0, 0)  # Should not reach here
