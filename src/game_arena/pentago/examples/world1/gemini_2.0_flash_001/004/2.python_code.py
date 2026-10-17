
import numpy as np

def check_win(board):
    """Checks if there are 5 in a row (horizontally, vertically, or diagonally)."""
    n = 6
    # Horizontal
    for r in range(n):
        for c in range(n - 4):
            if all(board[r, c + i] == 1 for i in range(5)):
                return True

    # Vertical
    for c in range(n):
        for r in range(n - 4):
            if all(board[r + i, c] == 1 for i in range(5)):
                return True

    # Diagonal (top-left to bottom-right)
    for r in range(n - 4):
        for c in range(n - 4):
            if all(board[r + i, c + i] == 1 for i in range(5)):
                return True

    # Diagonal (top-right to bottom-left)
    for r in range(n - 4):
        for c in range(4, n):
            if all(board[r + i, c - i] == 1 for i in range(5)):
                return True

    return False


def rotate_quadrant(board, quad, direction):
    """Rotates a quadrant of the board."""
    temp_board = np.copy(board)
    if quad == 0:
        sub_board = temp_board[0:3, 0:3]
    elif quad == 1:
        sub_board = temp_board[0:3, 3:6]
    elif quad == 2:
        sub_board = temp_board[3:6, 0:3]
    elif quad == 3:
        sub_board = temp_board[3:6, 3:6]
    else:
        raise ValueError("Invalid quadrant")

    if direction == 'R':
        rotated_sub_board = np.rot90(sub_board, k=-1)  # Clockwise
    elif direction == 'L':
        rotated_sub_board = np.rot90(sub_board, k=1)   # Anticlockwise
    else:
        raise ValueError("Invalid direction")

    if quad == 0:
        temp_board[0:3, 0:3] = rotated_sub_board
    elif quad == 1:
        temp_board[0:3, 3:6] = rotated_sub_board
    elif quad == 2:
        temp_board[3:6, 0:3] = rotated_sub_board
    elif quad == 3:
        temp_board[3:6, 3:6] = rotated_sub_board

    return temp_board

def policy(you, opponent):
    """Chooses the next move for Pentago."""
    you_board = np.array(you)
    opponent_board = np.array(opponent)
    empty_cells = np.where((you_board == 0) & (opponent_board == 0))
    empty_rows, empty_cols = empty_cells

    best_move = None
    
    # 1. Prioritize winning moves
    for row, col in zip(empty_rows, empty_cols):
        for quad in range(4):
            for direction in ['L', 'R']:
                temp_you_board = np.copy(you_board)
                temp_you_board[row, col] = 1
                rotated_you_board = rotate_quadrant(temp_you_board, quad, direction)
                
                combined_board = rotated_you_board + opponent_board
                you_only_board = np.where(combined_board == 1, rotated_you_board, 0)
                if check_win(you_only_board):
                    return f"{row + 1},{col + 1},{quad},{direction}"  # Found winning move

    # 2. Block opponent's winning moves
    for row, col in zip(empty_rows, empty_cols):
        for quad in range(4):
            for direction in ['L', 'R']:
                temp_opponent_board = np.copy(opponent_board)
                temp_opponent_board[row, col] = 1
                rotated_opponent_board = rotate_quadrant(temp_opponent_board, quad, direction)
                
                combined_board = you_board + rotated_opponent_board
                opponent_only_board = np.where(combined_board == 1, rotated_opponent_board, 0)

                if check_win(opponent_only_board):
                    return f"{row + 1},{col + 1},{quad},{direction}"  # Block winning move
    
    # 3. Strategic Placement and Rotation (Prioritize center positions and rotations that might lead to future wins)          
    for row, col in zip(empty_rows, empty_cols):
        for quad in range(4):
            for direction in ['L', 'R']:
                # Evaluation:
                # Place in center rows/cols:
                center_bonus = 0
                if 1 <= row <= 4 :
                  center_bonus += 1
                if 1 <= col <= 4:
                  center_bonus += 1
        
                if best_move is None or center_bonus > best_move[0]: # simple heuristic
                  best_move = (center_bonus,(row,col,quad,direction))

    if best_move:
        row, col, quad, direction = best_move[1]
        return f"{row + 1},{col + 1},{quad},{direction}"

    # 4. If all else fails, make a random legal move
    row, col = empty_rows[0], empty_cols[0]
    return f"{row + 1},{col + 1},0,L"
