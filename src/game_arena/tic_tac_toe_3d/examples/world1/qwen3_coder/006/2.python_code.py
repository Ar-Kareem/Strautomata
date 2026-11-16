
import itertools

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Convert to more convenient format for checking
    # Check for immediate wins
    for x, y, z in itertools.product(range(3), range(3), range(3)):
        if board[x][y][z] == 0:  # Empty cell
            # Try placing our piece here and check for win
            board[x][y][z] = 1
            if check_win(board, 1):
                board[x][y][z] = 0  # Reset
                return (x, y, z)
            board[x][y][z] = 0  # Reset
    
    # Check for opponent wins to block
    for x, y, z in itertools.product(range(3), range(3), range(3)):
        if board[x][y][z] == 0:  # Empty cell
            # Try placing opponent piece here and check if they'd win
            board[x][y][z] = -1
            if check_win(board, -1):
                board[x][y][z] = 0  # Reset
                return (x, y, z)
            board[x][y][z] = 0  # Reset
    
    # No immediate win or block, use heuristic
    # Priority: center, corners, edges
    center = (1, 1, 1)
    if board[center[0]][center[1]][center[2]] == 0:
        return center
    
    # Check corners
    corners = [(0,0,0), (0,0,2), (0,2,0), (0,2,2), (2,0,0), (2,0,2), (2,2,0), (2,2,2)]
    for corner in corners:
        if board[corner[0]][corner[1]][corner[2]] == 0:
            return corner
    
    # Check edges (middle of faces)
    edges = [
        (0,1,1), (2,1,1), (1,0,1), (1,2,1), (1,1,0), (1,1,2),
        (0,0,1), (0,2,1), (2,0,1), (2,2,1), (0,1,0), (0,1,2), 
        (2,1,0), (2,1,2), (1,0,0), (1,0,2), (1,2,0), (1,2,2)
    ]
    for edge in edges:
        if board[edge[0]][edge[1]][edge[2]] == 0:
            return edge
    
    # Fallback: first available spot
    for x, y, z in itertools.product(range(3), range(3), range(3)):
        if board[x][y][z] == 0:
            return (x, y, z)
    
    # Should never reach here if board isn't full
    return (0, 0, 0)

def check_win(board, player):
    # Check all possible winning lines
    # Rows in each layer (x direction)
    for z in range(3):
        for y in range(3):
            if board[0][y][z] == player and board[1][y][z] == player and board[2][y][z] == player:
                return True
    
    # Columns in each layer (y direction)
    for z in range(3):
        for x in range(3):
            if board[x][0][z] == player and board[x][1][z] == player and board[x][2][z] == player:
                return True
    
    # Pillars through layers (z direction)
    for x in range(3):
        for y in range(3):
            if board[x][y][0] == player and board[x][y][1] == player and board[x][y][2] == player:
                return True
    
    # Diagonals in xy planes (constant z)
    for z in range(3):
        if board[0][0][z] == player and board[1][1][z] == player and board[2][2][z] == player:
            return True
        if board[0][2][z] == player and board[1][1][z] == player and board[2][0][z] == player:
            return True
    
    # Diagonals in xz planes (constant y)
    for y in range(3):
        if board[0][y][0] == player and board[1][y][1] == player and board[2][y][2] == player:
            return True
        if board[0][y][2] == player and board[1][y][1] == player and board[2][y][0] == player:
            return True
    
    # Diagonals in yz planes (constant x)
    for x in range(3):
        if board[x][0][0] == player and board[x][1][1] == player and board[x][2][2] == player:
            return True
        if board[x][0][2] == player and board[x][1][1] == player and board[x][2][0] == player:
            return True
    
    # Space diagonals
    if board[0][0][0] == player and board[1][1][1] == player and board[2][2][2] == player:
        return True
    if board[0][0][2] == player and board[1][1][1] == player and board[2][2][0] == player:
        return True
    if board[0][2][0] == player and board[1][1][1] == player and board[2][0][2] == player:
        return True
    if board[0][2][2] == player and board[1][1][1] == player and board[2][0][0] == player:
        return True
    
    return False
