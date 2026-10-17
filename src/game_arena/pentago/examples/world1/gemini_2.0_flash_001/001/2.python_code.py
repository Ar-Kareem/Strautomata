
import numpy as np

def check_win(board):
    """Checks if there are 5 in a row (horizontally, vertically, or diagonally) on the board."""
    n = 6
    # Check horizontal
    for i in range(n):
        for j in range(n - 4):
            if all(board[i][j+k] == 1 for k in range(5)):
                return True

    # Check vertical
    for j in range(n):
        for i in range(n - 4):
            if all(board[i+k][j] == 1 for k in range(5)):
                return True

    # Check diagonal (top-left to bottom-right)
    for i in range(n - 4):
        for j in range(n - 4):
            if all(board[i+k][j+k] == 1 for k in range(5)):
                return True

    # Check diagonal (top-right to bottom-left)
    for i in range(n - 4):
        for j in range(4, n):
            if all(board[i+k][j-k] == 1 for k in range(5)):
                return True

    return False

def rotate_quadrant(board, quad, direction):
    """Rotates a quadrant of the board."""
    new_board = np.copy(board)
    if quad == 0:
        sub_board = board[0:3, 0:3]
        if direction == 'R':
            rotated_sub_board = np.rot90(sub_board, k=-1)
        else:
            rotated_sub_board = np.rot90(sub_board, k=1)
        new_board[0:3, 0:3] = rotated_sub_board
    elif quad == 1:
        sub_board = board[0:3, 3:6]
        if direction == 'R':
            rotated_sub_board = np.rot90(sub_board, k=-1)
        else:
            rotated_sub_board = np.rot90(sub_board, k=1)
        new_board[0:3, 3:6] = rotated_sub_board
    elif quad == 2:
        sub_board = board[3:6, 0:3]
        if direction == 'R':
            rotated_sub_board = np.rot90(sub_board, k=-1)
        else:
            rotated_sub_board = np.rot90(sub_board, k=1)
        new_board[3:6, 0:3] = rotated_sub_board
    elif quad == 3:
        sub_board = board[3:6, 3:6]
        if direction == 'R':
            rotated_sub_board = np.rot90(sub_board, k=-1)
        else:
            rotated_sub_board = np.rot90(sub_board, k=1)
        new_board[3:6, 3:6] = rotated_sub_board
    return new_board


def policy(you, opponent) -> str:
    """Chooses the next move for Pentago."""
    you = np.array(you)
    opponent = np.array(opponent)

    for row in range(6):
        for col in range(6):
            if you[row][col] == 0 and opponent[row][col] == 0:
                # Try placing a marble here
                temp_you = np.copy(you)
                temp_you[row][col] = 1

                for quad in range(4):
                    for direction in ['L', 'R']:
                        # Try rotating the quadrant
                        new_you = rotate_quadrant(temp_you, quad, direction)
                        new_opponent = rotate_quadrant(opponent, quad, direction)

                        # Check if this move wins
                        if check_win(new_you):
                            return f"{row+1},{col+1},{quad},{direction}"

    # Block opponent wins
    for row in range(6):
        for col in range(6):
            if you[row][col] == 0 and opponent[row][col] == 0:
                # Simulate placing opponent's marble here
                temp_opponent = np.copy(opponent)
                temp_opponent[row][col] = 1

                for quad in range(4):
                    for direction in ['L', 'R']:
                         # Try rotating the quadrant for opponent
                        new_you = rotate_quadrant(you, quad, direction)
                        new_opponent = rotate_quadrant(temp_opponent, quad, direction)

                        if check_win(new_opponent):
                            # Block the win by placing our marble and rotating
                            temp_you = np.copy(you)
                            temp_you[row][col] = 1
                            new_you = rotate_quadrant(temp_you, quad, direction)
                            return f"{row+1},{col+1},{quad},{direction}"

    # Create lines of 4
    for row in range(6):
        for col in range(6):
            if you[row][col] == 0 and opponent[row][col] == 0:
                # Try placing a marble here
                temp_you = np.copy(you)
                temp_you[row][col] = 1

                for quad in range(4):
                    for direction in ['L', 'R']:
                        # Try rotating the quadrant
                        new_you = rotate_quadrant(temp_you, quad, direction)
                        new_opponent = rotate_quadrant(opponent, quad, direction)

                        # Count lines of 4
                        lines_of_4 = 0
                        for i in range(6):
                            for j in range(2):
                                if all(new_you[i][j+k] == 1 for k in range(4)):
                                    lines_of_4 +=1

                            for j in range(6):
                                for i in range(2):
                                    if all(new_you[i+k][j] == 1 for k in range(4)):
                                        lines_of_4 +=1

                            for i in range(2):
                                for j in range(2):
                                    if all(new_you[i+k][j+k] == 1 for k in range(4)):
                                        lines_of_4+=1

                            for i in range(2):
                                for j in range(4, 6):
                                    if all(new_you[i+k][j-k] == 1 for k in range(4)):
                                        lines_of_4+=1
                        if lines_of_4 > 0:
                            return f"{row+1},{col+1},{quad},{direction}"



    # Random Legal Move (Fallback)
    for row in range(6):
        for col in range(6):
            if you[row][col] == 0 and opponent[row][col] == 0:
                for quad in range(4):
                    for direction in ['L', 'R']:
                        return f"{row+1},{col+1},{quad},{direction}"
    return "1,1,0,L"  # Should never reach here, but ensures a valid move when no moves are possible
