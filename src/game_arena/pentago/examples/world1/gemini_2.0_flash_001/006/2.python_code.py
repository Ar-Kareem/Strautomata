
import random
import numpy as np

def check_win(board):
    """Checks for a 5-in-a-row win on the given board."""
    n = 6
    # Horizontal
    for r in range(n):
        for c in range(n - 4):
            if all(board[r][c+i] == 1 for i in range(5)):
                return True
    # Vertical
    for c in range(n):
        for r in range(n - 4):
            if all(board[r+i][c] == 1 for i in range(5)):
                return True
    # Diagonal (top-left to bottom-right)
    for r in range(n - 4):
        for c in range(n - 4):
            if all(board[r+i][c+i] == 1 for i in range(5)):
                return True
    # Diagonal (top-right to bottom-left)
    for r in range(n - 4):
        for c in range(4, n):
            if all(board[r+i][c-i] == 1 for i in range(5)):
                return True
    return False

def rotate_quadrant(board, quad, direction):
    """Rotates a quadrant of the board."""
    new_board = np.copy(board)
    if quad == 0:
        sub_board = board[0:3, 0:3]
    elif quad == 1:
        sub_board = board[0:3, 3:6]
    elif quad == 2:
        sub_board = board[3:6, 0:3]
    else:  # quad == 3
        sub_board = board[3:6, 3:6]

    if direction == 'L':
        rotated_sub_board = np.rot90(sub_board, k=1)  # Rotate 90 degrees counterclockwise
    else:
        rotated_sub_board = np.rot90(sub_board, k=-1)  # Rotate 90 degrees clockwise

    if quad == 0:
        new_board[0:3, 0:3] = rotated_sub_board
    elif quad == 1:
        new_board[0:3, 3:6] = rotated_sub_board
    elif quad == 2:
        new_board[3:6, 0:3] = rotated_sub_board
    else:  # quad == 3
        new_board[3:6, 3:6] = rotated_sub_board

    return new_board

def policy(you, opponent):
    """Chooses the next move for Pentago."""
    you = np.array(you)
    opponent = np.array(opponent)
    empty_cells = np.where((you == 0) & (opponent == 0))
    empty_indices = list(zip(empty_cells[0], empty_cells[1]))

    best_move = None
    
    # 1. Block opponent's winning move
    for r, c in empty_indices:
        for quad in range(4):
            for direction in ['L', 'R']:
                temp_you = np.copy(you)
                temp_you[r][c] = 1
                
                temp_opponent = np.copy(opponent)

                temp_opponent_board = np.copy(temp_opponent)
                temp_you_board = np.copy(temp_you)
                combined_board = temp_you_board + temp_opponent_board
                
                rotated_you = rotate_quadrant(temp_you, quad, direction)
                rotated_opponent = rotate_quadrant(temp_opponent, quad, direction)

                rotated_opponent_board = np.copy(rotated_opponent)
                rotated_you_board = np.copy(rotated_you)
                combined_rotated_board = rotated_you_board + rotated_opponent_board

                if check_win(rotated_opponent):
                    continue  # Do not allow opponent to have 5 in a row after our move.

                if check_win(rotate_quadrant(opponent, quad, direction)):
                   best_move = f"{r+1},{c+1},{quad},{direction}"
                   return best_move
    
    # 2. Create winning move
    for r, c in empty_indices:
        for quad in range(4):
            for direction in ['L', 'R']:
                temp_you = np.copy(you)
                temp_you[r][c] = 1

                temp_opponent = np.copy(opponent)

                rotated_you = rotate_quadrant(temp_you, quad, direction)
                rotated_opponent = rotate_quadrant(temp_opponent, quad, direction)

                if check_win(rotated_you):
                    best_move = f"{r+1},{c+1},{quad},{direction}"
                    return best_move
    
    # 3. Occupy center positions
    center_moves = []
    for r, c in empty_indices:
        if (r in [2,3]) and (c in [2,3]):
            for quad in range(4):
                for direction in ['L', 'R']:
                    center_moves.append(f"{r+1},{c+1},{quad},{direction}")
    if center_moves:
        return random.choice(center_moves)

    # 4. Random legal move
    r, c = random.choice(empty_indices)
    quad = random.randint(0, 3)
    direction = random.choice(['L', 'R'])
    return f"{r+1},{c+1},{quad},{direction}"
