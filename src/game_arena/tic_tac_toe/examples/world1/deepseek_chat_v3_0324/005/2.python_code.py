
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Check for immediate winning move
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                # Test if this move would win
                board[i][j] = 1
                if is_winner(board, 1):
                    board[i][j] = 0  # undo test move
                    return (i, j)
                board[i][j] = 0  # undo test move
    
    # Check for opponent's winning move to block
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                # Test if opponent would win here
                board[i][j] = -1
                if is_winner(board, -1):
                    board[i][j] = 0  # undo test move
                    return (i, j)
                board[i][j] = 0  # undo test move
    
    # Strategic moves when no immediate win/block
    # Prefer center
    if board[1][1] == 0:
        return (1, 1)
    
    # Then prefer corners
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    for i, j in corners:
        if board[i][j] == 0:
            return (i, j)
    
    # Finally take any edge
    edges = [(0, 1), (1, 0), (1, 2), (2, 1)]
    for i, j in edges:
        if board[i][j] == 0:
            return (i, j)
    
    # Should never reach here if board isn't full
    return (0, 0)

def is_winner(board, player):
    # Check rows
    for row in board:
        if all(cell == player for cell in row):
            return True
    # Check columns
    for col in range(3):
        if all(board[row][col] == player for row in range(3)):
            return True
    # Check diagonals
    if (board[0][0] == player and board[1][1] == player and board[2][2] == player):
        return True
    if (board[0][2] == player and board[1][1] == player and board[2][0] == player):
        return True
    return False
