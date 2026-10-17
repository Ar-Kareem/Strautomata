
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert board to numpy array for easier manipulation
    import numpy as np
    
    # Check for winning move
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                # Try placing our piece here
                board[i][j] = 1
                if check_win(board, 1):
                    return (i, j)
                # Reset the board
                board[i][j] = 0
    
    # Check for blocking opponent's winning move
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                # Try placing opponent's piece here
                board[i][j] = -1
                if check_win(board, -1):
                    return (i, j)
                # Reset the board
                board[i][j] = 0
    
    # Try to take center if available
    if board[1][1] == 0:
        return (1, 1)
    
    # Try to take corners
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    available_corners = [(i, j) for i, j in corners if board[i][j] == 0]
    if available_corners:
        return available_corners[0]
    
    # Take any available side
    sides = [(0, 1), (1, 0), (1, 2), (2, 1)]
    available_sides = [(i, j) for i, j in sides if board[i][j] == 0]
    if available_sides:
        return available_sides[0]
    
    # Fallback (should never happen in a valid game)
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                return (i, j)


def check_win(board, player):
    # Check rows
    for row in board:
        if all(cell == player for cell in row):
            return True
    
    # Check columns
    for col in range(3):
        if all(board[row][col] == player for row in range(3)):
            return True
    
    # Check diagonals
    if all(board[i][i] == player for i in range(3)):
        return True
    if all(board[i][2-i] == player for i in range(3)):
        return True
    
    return False
