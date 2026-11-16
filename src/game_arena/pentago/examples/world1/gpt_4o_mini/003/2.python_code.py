
import numpy as np

def check_win(board):
    # Check all rows, columns, and diagonals for a win
    for r in range(6):
        for c in range(2):  # Check only up to column 2 (5 in a row)
            if np.all(board[r, c:c+5] == 1):  # Check horizontal
                return True
        for r2 in range(3):  # Check only up to row 3 (5 in a row)
            if np.all(board[r2:r2+5, r] == 1):  # Check vertical
                return True
    # Check diagonals
    for r in range(2):
        for c in range(2):
            if np.all(np.diag(board[r:r+5, c:c+5]) == 1):  # Check main diagonal
                return True
            if np.all(np.diag(np.fliplr(board[r:r+5, c:c+5])) == 1):  # Check anti diagonal
                return True
    return False

def rotate_board(board, quad, direction):
    # Clone the board to avoid modifying the original
    new_board = board.copy()
    if direction == 'L':
        if quad == 0:
            new_board[0:3, 0:3] = np.rot90(board[0:3, 0:3], k=1)
        elif quad == 1:
            new_board[0:3, 3:6] = np.rot90(board[0:3, 3:6], k=1)
        elif quad == 2:
            new_board[3:6, 0:3] = np.rot90(board[3:6, 0:3], k=1)
        elif quad == 3:
            new_board[3:6, 3:6] = np.rot90(board[3:6, 3:6], k=1)
    else:  # direction 'R'
        if quad == 0:
            new_board[0:3, 0:3] = np.rot90(board[0:3, 0:3], k=3)
        elif quad == 1:
            new_board[0:3, 3:6] = np.rot90(board[0:3, 3:6], k=3)
        elif quad == 2:
            new_board[3:6, 0:3] = np.rot90(board[3:6, 0:3], k=3)
        elif quad == 3:
            new_board[3:6, 3:6] = np.rot90(board[3:6, 3:6], k=3)
    return new_board

def policy(you, opponent) -> str:
    you_board = np.array(you)
    opponent_board = np.array(opponent)
    
    # Combined board
    combined_board = you_board + opponent_board

    for r in range(6):
        for c in range(6):
            if combined_board[r, c] == 0:  # Find an empty cell
                # Try placing the marble here
                for quad in range(4):
                    for dir in ['L', 'R']:
                        # Simulate the placement
                        test_board = you_board.copy()
                        test_board[r, c] = 1
                        # Simulate the rotation
                        rotated_board = rotate_board(test_board, quad, dir)
                        
                        # Check for win
                        if check_win(rotated_board):
                            return f"{r + 1},{c + 1},{quad},{dir}"  # Return win move

    # Fallback move: if no win is found, just place the first available cell and rotate quad 0 to the right 
    for r in range(6):
        for c in range(6):
            if combined_board[r, c] == 0:  # Find an empty cell
                return f"{r + 1},{c + 1},0,R"

