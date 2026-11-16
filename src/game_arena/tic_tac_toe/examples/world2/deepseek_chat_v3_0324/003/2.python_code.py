
import numpy as np
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    board_array = np.array(board)
    
    # Check for immediate winning move
    move = find_winning_move(board_array, 1)
    if move:
        return move
    
    # Check for opponent's winning move to block
    move = find_winning_move(board_array, -1)
    if move:
        return move
    
    # Prioritize center squares
    center_squares = [(1, 1), (1, 2), (2, 1), (2, 2)]
    for i, j in center_squares:
        if board_array[i, j] == 0:
            return (i, j)
    
    # Then check corners
    corners = [(0, 0), (0, 3), (3, 0), (3, 3)]
    random.shuffle(corners)  # Randomize corner selection
    for i, j in corners:
        if board_array[i, j] == 0:
            return (i, j)
    
    # Finally, pick any available move
    available_moves = []
    for i in range(4):
        for j in range(4):
            if board_array[i, j] == 0:
                available_moves.append((i, j))
    return random.choice(available_moves)

def find_winning_move(board: np.ndarray, player: int) -> None:
    # Check rows
    for i in range(4):
        row = board[i, :]
        if np.sum(row == player) == 3 and np.sum(row == 0) == 1:
            j = np.where(row == 0)[0][0]
            return (i, j)
    
    # Check columns
    for j in range(4):
        col = board[:, j]
        if np.sum(col == player) == 3 and np.sum(col == 0) == 1:
            i = np.where(col == 0)[0][0]
            return (i, j)
    
    # Check main diagonal
    diag = np.diag(board)
    if np.sum(diag == player) == 3 and np.sum(diag == 0) == 1:
        idx = np.where(diag == 0)[0][0]
        return (idx, idx)
    
    # Check anti-diagonal
    anti_diag = np.diag(np.fliplr(board))
    if np.sum(anti_diag == player) == 3 and np.sum(anti_diag == 0) == 1:
        idx = np.where(anti_diag == 0)[0][0]
        return (idx, 3 - idx)
    
    return None
