
import numpy as np

def policy(you, opponent) -> str:
    you_np = np.array(you)
    opponent_np = np.array(opponent)

    empty_cells = []
    for r in range(6):
        for c in range(6):
            if you_np[r][c] == 0 and opponent_np[r][c] == 0:
                empty_cells.append((r, c))

    def check_win(board):
        for r in range(6):
            for c in range(2):
                if all(board[r][c + i] for i in range(5)):
                    return True
        for c in range(6):
            for r in range(2):
                if all(board[r + i][c] for i in range(5)):
                    return True
        for r in range(2):
            for c in range(2):
                if all(board[r + i][c + i] for i in range(5)):
                    return True
        for r in range(2):
            for c in range(4, 6):
                if all(board[r + i][c - i] for i in range(5)):
                    return True
        return False

    def apply_rotation(you_board, opponent_board, quad, direction):
        you_copy = you_board.copy()
        opponent_copy = opponent_board.copy()
        top_row = 3 * (quad // 2)
        top_col = 3 * (quad % 2)
        quadrant_you = you_copy[top_row:top_row+3, top_col:top_col+3]
        quadrant_opponent = opponent_copy[top_row:top_row+3, top_col:top_col+3]
        if direction == 'R':
            rotated_you = np.rot90(quadrant_you, -1)
            rotated_opponent = np.rot90(quadrant_opponent, -1)
        else:
            rotated_you = np.rot90(quadrant_you, 1)
            rotated_opponent = np.rot90(quadrant_opponent, 1)
        you_copy[top_row:top_row+3, top_col:top_col+3] = rotated_you
        opponent_copy[top_row:top_row+3, top_col:top_col+3] = rotated_opponent
        return you_copy, opponent_copy

    # Immediate win check
    for r, c in empty_cells:
        for quad in range(4):
            for direction in ['L', 'R']:
                you_copy = you_np.copy()
                you_copy[r][c] = 1
                new_you, new_opponent = apply_rotation(you_copy, opponent_np.copy(), quad, direction)
                if check_win(new_you):
                    return f"{r+1},{c+1},{quad},{direction}"

    # Block opponent's win
    def is_opponent_win_possible(new_you, new_opponent):
        empty_for_opponent = []
        for orow in range(6):
            for ocol in range(6):
                if new_you[orow][ocol] == 0 and new_opponent[orow][ocol] == 0:
                    empty_for_opponent.append((orow, ocol))
        for orow, ocol in empty_for_opponent:
            for oquad in range(4):
                for odir in ['L', 'R']:
                    opponent_copy = new_opponent.copy()
                    opponent_copy[orow][ocol] = 1
                    ny, no = apply_rotation(new_you.copy(), opponent_copy, oquad, odir)
                    if check_win(no):
                        return True
        return False

    for r, c in empty_cells:
        for quad in range(4):
            for direction in ['L', 'R']:
                you_copy = you_np.copy()
                you_copy[r][c] = 1
                new_you, new_opponent = apply_rotation(you_copy, opponent_np.copy(), quad, direction)
                if not is_opponent_win_possible(new_you, new_opponent):
                    return f"{r+1},{c+1},{quad},{direction}"

    # Fallback: choose first possible move
    for r, c in empty_cells:
        for quad in range(4):
            for direction in ['L', 'R']:
                return f"{r+1},{c+1},{quad},{direction}"

    return "1,1,0,L"
