
import random
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert board to numpy array for easier manipulation
    board_np = np.array(board, dtype=int)

    # Get all empty or uncertain cells (0 or -1, but -1 is not in input; 0 is uncertain)
    empty_cells = [(i, j) for i in range(3) for j in range(3) if board_np[i, j] != 1]

    # Check for immediate win (3 in a row with 1s)
    def check_win(player):
        # Check rows, columns, diagonals
        for i in range(3):
            if all(board_np[i, j] == player for j in range(3)):
                return True
            if all(board_np[j, i] == player for j in range(3)):
                return True
        if all(board_np[i, i] == player for i in range(3)) or all(board_np[i, 2-i] == player for i in range(3)):
            return True
        return False

    # Check if current player can win in next move
    for (i, j) in empty_cells:
        board_np[i, j] = 1
        if check_win(1):
            board_np[i, j] = 0  # revert
            return (i, j)
        board_np[i, j] = 0  # revert

    # Check if opponent could win next turn (assuming they play optimally)
    # Opponent's marks are unknown, but we can infer based on uncertainty
    # Simulate opponent's possible moves (assuming they have 1s in some cells)
    # This is tricky; instead, we'll assume opponent is trying to win and block accordingly
    # For simplicity, we'll assume opponent has placed in some cells (0s could be theirs)
    # We'll try to block any potential 2-in-a-row for opponent (assuming 0s are theirs)
    # This is imperfect but better than nothing
    for (i, j) in empty_cells:
        # Assume opponent has placed in this cell (temporarily)
        board_np[i, j] = -1  # mark as opponent's (but input only has 0/1)
        # Check if opponent would win
        # Since we don't know opponent's marks, we'll check if two 0s are in a row/col/diag
        # and the third is empty (could be opponent's)
        # This is a heuristic
        # Check rows
        for k in range(3):
            if board_np[k, j] == 0 and board_np[k, (j+1)%3] == 0 and board_np[k, (j+2)%3] == 0:
                board_np[i, j] = 0  # revert
                return (k, j)  # block
        # Check columns
        for k in range(3):
            if board_np[i, k] == 0 and board_np[(i+1)%3, k] == 0 and board_np[(i+2)%3, k] == 0:
                board_np[i, j] = 0  # revert
                return (i, k)  # block
        # Check diagonals
        if i == j and board_np[0, 0] == 0 and board_np[1, 1] == 0 and board_np[2, 2] == 0:
            board_np[i, j] = 0  # revert
            return (0, 0)  # block
        if i == 2-j and board_np[0, 2] == 0 and board_np[1, 1] == 0 and board_np[2, 0] == 0:
            board_np[i, j] = 0  # revert
            return (0, 2)  # block
        board_np[i, j] = 0  # revert

    # Prefer center, then corners, then edges
    priority = [
        (1, 1),  # center
        (0, 0), (0, 2), (2, 0), (2, 2),  # corners
        (0, 1), (1, 0), (1, 2), (2, 1)   # edges
    ]

    # Filter priority moves to only those in empty_cells
    valid_priority = [(i, j) for (i, j) in priority if (i, j) in empty_cells]

    if valid_priority:
        return valid_priority[0]  # pick highest priority

    # Fallback: random valid move
    return random.choice(empty_cells)
