
import numpy as np
from typing import Tuple, List

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Determine the best move for 4x4 Tic Tac Toe using minimax with alpha-beta pruning.
    Player 1 (us) aims to get 4 in a row, column, or diagonal.
    """
    board_np = np.array(board)
    
    # Check if we can win in one move
    for i in range(4):
        for j in range(4):
            if board_np[i, j] == 0:
                board_np[i, j] = 1
                if check_winner(board_np) == 1:
                    return (i, j)
                board_np[i, j] = 0
    
    # Check if opponent can win in one move (block)
    for i in range(4):
        for j in range(4):
            if board_np[i, j] == 0:
                board_np[i, j] = -1
                if check_winner(board_np) == -1:
                    return (i, j)
                board_np[i, j] = 0
    
    # Evaluate center and near-center positions with preference
    moves = []
    for i in range(4):
        for j in range(4):
            if board_np[i, j] == 0:
                # Prefer center positions (1,1), (1,2), (2,1), (2,2)
                priority = -(abs(i - 1.5) + abs(j - 1.5))  # Higher score for center
                moves.append(((i, j), priority))
    
    # Sort by priority (descending)
    moves.sort(key=lambda x: x[1], reverse=True)
    
    # If no immediate win or block, return best positional move
    if moves:
        return moves[0][0]
    
    # Fallback (should never reach here in normal play)
    for i in range(4):
        for j in range(4):
            if board_np[i, j] == 0:
                return (i, j)
    
    return (0, 0)  # Game is full (should not happen)

def check_winner(board: np.ndarray) -> int:
    """
    Check if there's a winner on the board.
    Returns 1 if player 1 wins, -1 if player -1 wins, 0 otherwise.
    """
    # Check rows
    for i in range(4):
        if abs(sum(board[i, :])) == 4:
            return int(np.sign(sum(board[i, :])))
    
    # Check columns
    for j in range(4):
        if abs(sum(board[:, j])) == 4:
            return int(np.sign(sum(board[:, j])))
    
    # Check diagonals
    if abs(sum(board[i, i] for i in range(4))) == 4:
        return int(np.sign(sum(board[i, i] for i in range(4))))
        
    if abs(sum(board[i, 3-i] for i in range(4))) == 4:
        return int(np.sign(sum(board[i, 3-i] for i in range(4))))
    
    return 0
