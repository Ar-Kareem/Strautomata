
import random
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    # Check for immediate winning move
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                # Test if this move wins
                board[i][j] = 1
                if check_win(board, 1):
                    board[i][j] = 0  # undo test move
                    return (i, j)
                board[i][j] = 0  # undo test move
    
    # Check for opponent's immediate winning move
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                # Test if opponent would win here
                board[i][j] = -1
                if check_win(board, -1):
                    board[i][j] = 0  # undo test move
                    return (i, j)
                board[i][j] = 0  # undo test move
    
    # Prefer center squares if available
    center_squares = [(1, 1), (1, 2), (2, 1), (2, 2)]
    for i, j in center_squares:
        if board[i][j] == 0:
            return (i, j)
    
    # If no strategic moves, choose random available square
    available_moves = []
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                available_moves.append((i, j))
    
    if available_moves:
        return random.choice(available_moves)
    
    # Shouldn't reach here if board isn't full
    return (0, 0)

def check_win(board: List[List[int]], player: int) -> bool:
    # Check rows
    for row in board:
        if all(cell == player for cell in row):
            return True
    
    # Check columns
    for j in range(4):
        if all(board[i][j] == player for i in range(4)):
            return True
    
    # Check diagonals
    if all(board[i][i] == player for i in range(4)):
        return True
    if all(board[i][3-i] == player for i in range(4)):
        return True
    
    return False
