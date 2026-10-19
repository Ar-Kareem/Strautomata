
import numpy as np
from typing import Tuple, List

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Optimal Tic Tac Toe policy using minimax algorithm.
    
    Args:
        board: 3x3 list of lists with 0 (empty), 1 (player), -1 (opponent)
    
    Returns:
        Tuple of (row, col) for the next move
    """
    # Convert to numpy array for easier manipulation
    board_array = np.array(board)
    current_player = 1  # AI is player 1
    
    # Check if there's an immediate winning move
    winning_move = find_winning_move(board_array, current_player)
    if winning_move:
        return winning_move
    
    # Check if opponent has a winning move and block it
    opponent_winning_move = find_winning_move(board_array, -current_player)
    if opponent_winning_move:
        return opponent_winning_move
    
    # If center is available, take it
    if board_array[1, 1] == 0:
        return (1, 1)
    
    # Check for available corners
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    available_corners = [corner for corner in corners if board_array[corner[0], corner[1]] == 0]
    if available_corners:
        # Prefer corners that don't give opponent advantage
        return available_corners[0]
    
    # Take any available edge
    edges = [(0, 1), (1, 0), (1, 2), (2, 1)]
    available_edges = [edge for edge in edges if board_array[edge[0], edge[1]] == 0]
    if available_edges:
        return available_edges[0]
    
    # Fallback: take any available move
    for i in range(3):
        for j in range(3):
            if board_array[i, j] == 0:
                return (i, j)
    
    # This should never happen if called correctly
    return (0, 0)


def find_winning_move(board: np.ndarray, player: int) -> None:
    """
    Check if the given player has a winning move and return its coordinates.
    
    Args:
        board: Current board state
        player: Player to check for winning moves
    
    Returns:
        Coordinates of winning move if exists, None otherwise
    """
    # Check rows
    for i in range(3):
        if np.sum(board[i, :]) == 2 * player and 0 in board[i, :]:
            return (i, np.where(board[i, :] == 0)[0][0])
    
    # Check columns
    for j in range(3):
        if np.sum(board[:, j]) == 2 * player and 0 in board[:, j]:
            return (np.where(board[:, j] == 0)[0][0], j)
    
    # Check diagonals
    if np.sum(np.diag(board)) == 2 * player and 0 in np.diag(board):
        diag_indices = np.where(np.diag(board) == 0)[0]
        if len(diag_indices) > 0:
            idx = diag_indices[0]
            return (idx, idx)
    
    if np.sum(np.diag(np.fliplr(board))) == 2 * player and 0 in np.diag(np.fliplr(board)):
        anti_diag = np.diag(np.fliplr(board))
        anti_diag_indices = np.where(anti_diag == 0)[0]
        if len(anti_diag_indices) > 0:
            idx = anti_diag_indices[0]
            return (idx, 2 - idx)
    
    return None
