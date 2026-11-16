
import random
import copy

def deepcopy(board):
    return [[[board[z][y][x] for x in range(3)] for y in range(3)] for z in range(3)]

def has_win(board, player):
    # Check rows in XY planes (for each Z)
    for z in range(3):
        for y in range(3):
            if all(board[z][y][x] == player for x in range(3)):
                return True
        # Check columns in XY planes (for each Z)
        for x in range(3):
            if all(board[z][y][x] == player for y in range(3)):
                return True
        # Check main diagonal in XY plane (for each Z)
        if board[z][0][0] == player and board[z][1][1] == player and board[z][2][2] == player:
            return True
        # Check anti-diagonal in XY plane (for each Z)
        if board[z][0][2] == player and board[z][1][1] == player and board[z][2][0] == player:
            return True
    
    # Check depths (fixed Y, X, varying Z)
    for y in range(3):
        for x in range(3):
            if all(board[z][y][x] == player for z in range(3)):
                return True
    
    # Check diagonals in XZ planes (fixed Y)
    for y in range(3):
        # Main diagonal in XZ
        if board[0][y][0] == player and board[1][y][1] == player and board[2][y][2] == player:
            return True
        # Anti-diagonal in XZ
        if board[0][y][2] == player and board[1][y][1] == player and board[2][y][0] == player:
            return True
    
    # Check diagonals in YZ planes (fixed X)
    for x in range(3):
        # Main diagonal in YZ
        if board[0][0][x] == player and board[1][1][x] == player and board[2][2][x] == player:
            return True
        # Anti-diagonal in YZ
        if board[0][2][x] == player and board[1][1][x] == player and board[2][0][x] == player:
            return True
    
    # Check 3D space diagonals
    # Main space diagonal
    if all(board[z][z][z] == player for z in range(3)):
        return True
    # Space diagonal 1: varying Z, fixed (Y=Z, X=2-Z)
    if all(board[z][z][2-z] == player for z in range(3)):
        return True
    # Space diagonal 2: varying Z, fixed (Y=2-Z, X=Z)
    if all(board[z][2-z][z] == player for z in range(3)):
        return True
    # Space diagonal 3: varying Z, fixed (Y=2-Z, X=2-Z)
    if all(board[z][2-z][2-z] == player for z in range(3)):
        return True
    
    return False

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    empties = [(z, y, x) for z in range(3) for y in range(3) for x in range(3) if board[z][y][x] == 0]
    if not empties:
        # Should not happen in a valid game state, but return a valid tuple anyway
        return (0, 0, 0)
    
    # Try to win immediately (place to create a winning line)
    for move in empties:
        b = deepcopy(board)
        b[move[0]][move[1]][move[2]] = 1  # My player is 1
        if has_win(b, 1):
            return move
    
    # Block opponent's winning move
    for move in empties:
        b = deepcopy(board)
        b[move[0]][move[1]][move[2]] = -1  # Opponent is -1
        if has_win(b, -1):
            return move
    
    # Prefer the center of the cube if available
    if (1, 1, 1) in empties:
        return (1, 1, 1)
    
    # Otherwise, choose a random empty cell
    return random.choice(empties)
