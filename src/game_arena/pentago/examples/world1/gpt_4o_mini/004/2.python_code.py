
import numpy as np

def check_win(board):
    for row in range(6):
        for col in range(2):
            if np.all(board[row, col:col + 5] == 1):
                return True
    for col in range(6):
        for row in range(2):
            if np.all(board[row:row + 5, col] == 1):
                return True
    for row in range(2):
        for col in range(2):
            if (board[row, col] == 1 and board[row + 1, col + 1] == 1 and
                board[row + 2, col + 2] == 1 and board[row + 3, col + 3] == 1 and
                board[row + 4, col + 4] == 1):
                return True
            if (board[row + 4, col] == 1 and board[row + 3, col + 1] == 1 and
                board[row + 2, col + 2] == 1 and board[row + 1, col + 3] == 1 and
                board[row, col + 4] == 1):
                return True
    return False

def policy(you, opponent) -> str:
    you = np.array(you)
    opponent = np.array(opponent)
    board = you + opponent
    
    for r in range(6):
        for c in range(6):
            if board[r, c] == 0:  # Empty cell
                you[r, c] = 1
                if check_win(you):
                    for quad in range(4):
                        for dir in ['L', 'R']:
                            return f"{r + 1},{c + 1},{quad},{dir}"
                you[r, c] = 0  # Reset position if no win achieved

    for r in range(6):
        for c in range(6):
            if board[r, c] == 0:  # Empty cell
                opponent[r, c] = 1
                if check_win(opponent):
                    for quad in range(4):
                        for dir in ['L', 'R']:
                            return f"{r + 1},{c + 1},{quad},{dir}"
                opponent[r, c] = 0  # Reset position if no win achieved
    
    # Place a piece in a strategic position
    for r in range(6):
        for c in range(6):
            if board[r, c] == 0:  # Empty cell
                you[r, c] = 1  # Temporarily place the piece
                possible_dirs = ['L', 'R']
                for quad in range(4):
                    dir = possible_dirs[np.random.randint(0, 2)]
                    return f"{r + 1},{c + 1},{quad},{dir}"
                    
    # Return a valid move in case no other move is found (should not happen)
    return "1,1,0,L"

