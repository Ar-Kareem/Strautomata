
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    import numpy as np
    
    # Check if a player has won
    def check_winner(board_state, player):
        # Check all possible lines (rows, columns, diagonals)
        # 3D lines in each dimension
        for i in range(3):
            # Check slices along x-axis
            if all(board_state[i][j][k] == player for j in range(3) for k in range(3)):
                return True
            # Check slices along y-axis
            if all(board_state[j][i][k] == player for j in range(3) for k in range(3)):
                return True
            # Check slices along z-axis
            if all(board_state[j][k][i] == player for j in range(3) for k in range(3)):
                return True

        # Check face diagonals and 3D diagonals
        # Main diagonals through center
        # Diagonal from (0,0,0) to (2,2,2)
        if all(board_state[i][i][i] == player for i in range(3)):
            return True
        # Diagonal from (0,0,2) to (2,2,0)
        if all(board_state[i][i][2-i] == player for i in range(3)):
            return True
        # Diagonal from (0,2,0) to (2,0,2)
        if all(board_state[i][2-i][i] == player for i in range(3)):
            return True
        # Diagonal from (0,2,2) to (2,0,0)
        if all(board_state[i][2-i][2-i] == player for i in range(3)):
            return True

        # Other 3D diagonals and planar diagonals
        if all(board_state[0][j][j] == player for j in range(3)):
            return True
        if all(board_state[2][j][j] == player for j in range(3)):
            return True
        if all(board_state[j][0][j] == player for j in range(3)):
            return True
        if all(board_state[j][2][j] == player for j in range(3)):
            return True
        if all(board_state[j][j][0] == player for j in range(3)):
            return True
        if all(board_state[j][j][2] == player for j in range(3)):
            return True
            
        return False

    # Check if center is available
    def center_available(board_state):
        return board_state[1][1][1] == 0

    # Check if any corner is available
    def get_available_corners(board_state):
        corners = [
            (0,0,0), (0,0,2), (0,2,0), (0,2,2),
            (2,0,0), (2,0,2), (2,2,0), (2,2,2)
        ]
        available = []
        for x,y,z in corners:
            if board_state[x][y][z] == 0:
                available.append((x,y,z))
        return available

    # Look for winning move
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] == 0:
                    # Temporarily place my move
                    board[x][y][z] = 1
                    if check_winner(board, 1):
                        # Reset and return this position
                        board[x][y][z] = 0
                        return (x, y, z)
                    # Reset
                    board[x][y][z] = 0

    # Look for blocking move
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] == 0:
                    # Temporarily place opponent's move
                    board[x][y][z] = -1
                    if check_winner(board, -1):
                        # Reset and return this position to block
                        board[x][y][z] = 0
                        return (x, y, z)
                    # Reset
                    board[x][y][z] = 0

    # Take center if available
    if center_available(board):
        return (1, 1, 1)

    # Take any corner
    available_corners = get_available_corners(board)
    if available_corners:
        return available_corners[0]

    # Otherwise, take any available square
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] == 0:
                    return (x, y, z)
