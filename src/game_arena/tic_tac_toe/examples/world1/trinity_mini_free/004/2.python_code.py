
def check_win(board, player):
    # Check rows
    for i in range(3):
        if all(board[i][j] == player for j in range(3)):
            return True
    # Check columns
    for j in range(3):
        if all(board[i][j] == player for i in range(3)):
            return True
    # Check diagonals
    if all(board[i][i] == player for i in range(3)):
        return True
    if all(board[i][2-i] == player for i in range(3)):
        return True
    return False

def policy(board):
    # Check for winning move
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = 1
                if check_win(board, 1):
                    board[i][j] = 0
                    return (i, j)
                board[i][j] = 0
    
    # Check for blocking move
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = -1
                if check_win(board, -1):
                    board[i][j] = 0
                    return (i, j)
                board[i][j] = 0
    
    # Check center
    if board[1][1] == 0:
        return (1, 1)
    
    # Check corners
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    for (i, j) in corners:
        if board[i][j] == 0:
            return (i, j)
    
    # Check edges
    edges = [(0, 1), (1, 0), (1, 2), (2, 1)]
    for (i, j) in edges:
        if board[i][j] == 0:
            return (i, j)
    
    # Fallback: any available move
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                return (i, j)
    return (0, 0)  # Should never reach here in valid game
