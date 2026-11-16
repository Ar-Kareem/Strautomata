
import numpy as np
from typing import List, Tuple

def policy(board: List[List[int]], legal_moves: List[int]) -> Tuple[int, int]:
    # Convert board to numpy array for easier processing
    np_board = np.array(board)
    moves = [(move // 3, move % 3) for move in legal_moves]
    
    # Check for immediate winning moves
    for row in range(3):
        for col in range(3):
            if (row, col) in moves and np_board[row, col] == 1:
                # Check if completing this line would win
                temp = np_board.copy()
                temp[row, col] = 1
                if check_win(temp, 1):
                    return (row, col)
    
    # Check for blocking moves (opponent might have two in a line)
    for row in range(3):
        for col in range(3):
            if (row, col) in moves:
                temp = np_board.copy()
                temp[row, col] = 0
                if check_win(temp, 0):
                    return (row, col)
    
    # Prefer center if available
    center = (1, 1)
    if center in moves:
        return center
    
    # Then prefer corners
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    for corner in corners:
        if corner in moves and np_board[corner] != 1:
            return corner
    
    # Then prefer edges
    edges = [(0, 1), (1, 0), (1, 2), (2, 1)]
    for edge in edges:
        if edge in moves and np_board[edge] != 1:
            return edge
    
    # Fallback - first legal move
    return moves[0]

def check_win(board: np.ndarray, player: int) -> bool:
    """Check if the given player has a winning line on the board"""
    # Check rows and columns
    for i in range(3):
        if np.all(board[i, :] == player) or np.all(board[:, i] == player):
            return True
    # Check diagonals
    if np.all(np.diag(board) == player) or np.all(np.diag(np.fliplr(board)) == player):
        return True
    return False
