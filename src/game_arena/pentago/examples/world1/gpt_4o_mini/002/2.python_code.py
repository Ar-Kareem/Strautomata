
import numpy as np

def check_win(board):
    # Check for a win in rows, columns and diagonals
    for r in range(6):
        for c in range(6):
            if (c + 4 < 6 and np.sum(board[r, c:c+5]) == 5) or\
               (r + 4 < 6 and np.sum(board[r:r+5, c]) == 5) or\
               (r + 4 < 6 and c + 4 < 6 and np.sum(np.diag(board[r:r+5, c:c+5])) == 5) or\
               (r + 4 < 6 and c - 4 >= 0 and np.sum(np.diag(np.fliplr(board[r:r+5, c-4:c+1]))) == 5):
                return True
    return False

def rotate_quad(board, quad, dir):
    row_start = (quad // 2) * 3
    col_start = (quad % 2) * 3
    sub_board = board[row_start:row_start + 3, col_start:col_start + 3]
    
    if dir == 'R':
        # Rotate clockwise
        rotated = np.array([[sub_board[2, 0], sub_board[1, 0], sub_board[0, 0]],
                            [sub_board[2, 1], sub_board[1, 1], sub_board[0, 1]],
                            [sub_board[2, 2], sub_board[1, 2], sub_board[0, 2]]])
    else:
        # Rotate anticlockwise
        rotated = np.array([[sub_board[0, 2], sub_board[1, 2], sub_board[2, 2]],
                            [sub_board[0, 1], sub_board[1, 1], sub_board[2, 1]],
                            [sub_board[0, 0], sub_board[1, 0], sub_board[2, 0]]])
    
    # Paste rotated back into the board
    new_board = board.copy()
    new_board[row_start:row_start + 3, col_start:col_start + 3] = rotated
    return new_board

def policy(you, opponent) -> str:
    you = np.array(you)
    opponent = np.array(opponent)
    empty_cells = [(r, c) for r in range(6) for c in range(6) if you[r][c] == 0 and opponent[r][c] == 0]
    
    for (r, c) in empty_cells:
        # Place my marble
        temp_board = you.copy()
        temp_board[r, c] = 1
        
        for quad in range(4):
            for direction in ['L', 'R']:
                # Rotate quadrant
                new_board = rotate_quad(temp_board, quad, direction)

                # Check for win
                if check_win(new_board):
                    return f"{r+1},{c+1},{quad},{direction}"
    
    # If no immediate win found, place in a random available spot and rotate any quadrant
    r, c = empty_cells[0]  # Just take the first available empty cell
    quad = 0  # Choose first quadrant
    direction = 'R'  # Default to a clockwise rotation
    return f"{r+1},{c+1},{quad},{direction}"

