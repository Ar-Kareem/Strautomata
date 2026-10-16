
import numpy as np

def is_unblocked(board, start, end):
    """Check if the path from start to end is unobstructed."""
    r1, c1 = start
    r2, c2 = end
    dr = np.sign(r2 - r1)
    dc = np.sign(c2 - c1)

    r, c = r1 + dr, c1 + dc
    while (r, c) != (r2, c2):
        if board[r, c] != 0:
            return False
        r += dr
        c += dc

    return True

def get_possible_moves(board):
    """Generate all valid amazon moves and corresponding arrow shots."""
    moves = []
    for row in range(6):
        for col in range(6):
            if board[row, col] == 1:  # Our amazon
                # Check all possible directions
                for d_r in range(-1, 2):
                    for d_c in range(-1, 2):
                        if d_r == 0 and d_c == 0:
                            continue
                        for distance in range(1, 6):  # Move as far as allowed
                            new_row = row + d_r * distance
                            new_col = col + d_c * distance
                            if 0 <= new_row < 6 and 0 <= new_col < 6:
                                if board[new_row, new_col] == 0 and is_unblocked(board, (row, col), (new_row, new_col)):
                                    # Check for arrow shooting options from the new position
                                    for a_r in range(-1, 2):
                                        for a_c in range(-1, 2):
                                            if a_r == 0 and a_c == 0:
                                                continue
                                            # Arrow can also move multiple squares
                                            for arrow_distance in range(1, 6):
                                                arrow_row = new_row + a_r * arrow_distance
                                                arrow_col = new_col + a_c * arrow_distance
                                                if 0 <= arrow_row < 6 and 0 <= arrow_col < 6:
                                                    if board[arrow_row, arrow_col] == 0 and \
                                                       is_unblocked(board, (new_row, new_col), (arrow_row, arrow_col)):
                                                        move_str = f"{row},{col}:{new_row},{new_col}:{arrow_row},{arrow_col}"
                                                        moves.append(move_str)
                                else:
                                    break
                            else:
                                break

    return moves

def policy(board) -> str:
    """Select a move for the current player."""
    possible_moves = get_possible_moves(board)
    return possible_moves[0] if possible_moves else ""

