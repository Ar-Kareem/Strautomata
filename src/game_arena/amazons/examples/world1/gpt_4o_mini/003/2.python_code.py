
import numpy as np

def is_path_clear(board, start, end):
    r1, c1 = start
    r2, c2 = end

    d_row = (r2 - r1) // max(1, abs(r2 - r1)) if r1 != r2 else 0
    d_col = (c2 - c1) // max(1, abs(c2 - c1)) if c1 != c2 else 0

    r, c = r1 + d_row, c1 + d_col
    while (r, c) != (r2, c2):
        if board[r, c] != 0:
            return False
        r += d_row
        c += d_col
    return True

def get_possible_moves(board):
    moves = []
    for r in range(6):
        for c in range(6):
            if board[r, c] == 1:  # Find my amazon
                # Checking all 8 directions
                for dr in range(-1, 2):
                    for dc in range(-1, 2):
                        if abs(dr) + abs(dc) == 1 or abs(dr) == abs(dc):  # Orthogonal or diagonal
                            for step in range(1, 6):
                                new_r = r + dr * step
                                new_c = c + dc * step
                                if 0 <= new_r < 6 and 0 <= new_c < 6:
                                    if board[new_r, new_c] == 0:  # Move to an empty square
                                        # Check for arrow shot
                                        for ar in range(-1, 2):
                                            for ac in range(-1, 2):
                                                if (ar != 0 or ac != 0) and (abs(ar) + abs(ac) == 1 or abs(ar) == abs(ac)):
                                                    arrow_r = new_r + ar
                                                    arrow_c = new_c + ac
                                                    if 0 <= arrow_r < 6 and 0 <= arrow_c < 6:
                                                        if board[arrow_r, arrow_c] == 0:  # Choose empty square for arrow
                                                            move = f"{r},{c}:{new_r},{new_c}:{arrow_r},{arrow_c}"
                                                            moves.append(move)
                                    else:
                                        break  # Blocked by an amazon or arrow
                                else:
                                    break  # Out of bounds
    return moves

def policy(board) -> str:
    possible_moves = get_possible_moves(board)
    # Prefer to return the first valid move found
    if possible_moves:
        return possible_moves[0]
    # Fallback if no moves are found for unexpected circumstances
    return "0,0:0,0:0,0"  # This should never happen according to the problem statement
