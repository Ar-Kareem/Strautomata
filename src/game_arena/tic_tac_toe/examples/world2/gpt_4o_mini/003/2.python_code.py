
import numpy as np
import random

def check_win_or_block(board, player):
    # Check rows and columns
    for i in range(4):
        if np.sum(board[i, :]) == player * 3 and np.sum(board[i, :] == 0) == 1:
            return (i, np.where(board[i, :] == 0)[0][0])
        if np.sum(board[:, i]) == player * 3 and np.sum(board[:, i] == 0) == 1:
            return (np.where(board[:, i] == 0)[0][0], i)

    # Check diagonals
    if np.sum(board.diagonal()) == player * 3 and np.sum(board.diagonal() == 0) == 1:
        idx = np.where(board.diagonal() == 0)[0][0]
        return (idx, idx)
    
    if np.sum(np.fliplr(board).diagonal()) == player * 3 and np.sum(np.fliplr(board).diagonal() == 0) == 1:
        idx = np.where(np.fliplr(board).diagonal() == 0)[0][0]
        return (idx, 3 - idx)

    return None

def policy(board: list[list[int]]) -> tuple[int, int]:
    np_board = np.array(board)
    
    # Check for winning move
    move = check_win_or_block(np_board, 1)
    if move is not None:
        return move
    
    # Check for blocking move
    move = check_win_or_block(np_board, -1)
    if move is not None:
        return move

    # Else pick a random empty space
    empty_positions = np.argwhere(np_board == 0)
    if empty_positions.size > 0:
        return tuple(random.choice(empty_positions))
    
    # Should never reach here in a normal game (as there would be no empty spaces)
    raise Exception("No moves available")
