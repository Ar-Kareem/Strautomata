
import random
from typing import List, Tuple

def policy(board: List[List[int]], legal_moves: List[int]) -> int:
    # Flatten the board to make it easier to work with
    flat_board = [board[i][j] for i in range(3) for j in range(3)]
    
    # Priority order: center, corners, edges
    priority_order = [4, 0, 2, 6, 8, 1, 3, 5, 7]
    
    # Find all available moves that are not yet confirmed ours (0s)
    available_moves = [move for move in legal_moves if flat_board[move] != 1]
    
    # If we can win in one move, take it
    for move in available_moves:
        row, col = divmod(move, 3)
        # Simulate placing our mark and check for win
        board_copy = [row[:] for row in board]
        board_copy[row][col] = 1
        if check_win(board_copy):
            return move
    
    # If opponent can win in next move, block it
    # But since we don't know opponent's marks, we can't directly see this
    # Instead, we look for moves where we have 2 in a row to block opponent
    # We'll do a basic strategy to avoid losing
    
    # If there are safe moves we should make, let's pick them 
    for move in priority_order:
        if move in available_moves:
            return move
    
    # Fallback to first available
    return legal_moves[0]

def check_win(board: List[List[int]]) -> bool:
    # Check rows
    for i in range(3):
        if board[i][0] == 1 and board[i][1] == 1 and board[i][2] == 1:
            return True
    # Check columns
    for j in range(3):
        if board[0][j] == 1 and board[1][j] == 1 and board[2][j] == 1:
            return True
    # Check diagonals
    if board[0][0] == 1 and board[1][1] == 1 and board[2][2] == 1:
        return True
    if board[0][2] == 1 and board[1][1] == 1 and board[2][0] == 1:
        return True
    return False
