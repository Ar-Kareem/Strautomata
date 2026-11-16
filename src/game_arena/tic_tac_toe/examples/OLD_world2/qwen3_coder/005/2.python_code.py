
import random
from typing import List, Tuple, Optional

def policy(board: List[List[int]]) -> Tuple[int, int]:
    # Check for winning move
    move = find_winning_move(board, 1)
    if move:
        return move
    
    # Check for blocking opponent's winning move
    move = find_winning_move(board, -1)
    if move:
        return move
    
    # Try to take center positions
    center_moves = [(1, 1), (1, 2), (2, 1), (2, 2)]
    empty_center_moves = [move for move in center_moves if board[move[0]][move[1]] == 0]
    if empty_center_moves:
        return random.choice(empty_center_moves)
    
    # Try to take corner positions
    corner_moves = [(0, 0), (0, 3), (3, 0), (3, 3)]
    empty_corner_moves = [move for move in corner_moves if board[move[0]][move[1]] == 0]
    if empty_corner_moves:
        return random.choice(empty_corner_moves)
    
    # Make any valid move
    empty_positions = [(i, j) for i in range(4) for j in range(4) if board[i][j] == 0]
    if empty_positions:
        return random.choice(empty_positions)
    
    # Should never happen in a valid game state
    raise Exception("No valid moves available")

def find_winning_move(board: List[List[int]], player: int) -> Optional[Tuple[int, int]]:
    # Check rows
    for i in range(4):
        count = 0
        empty_pos = None
        for j in range(4):
            if board[i][j] == player:
                count += 1
            elif board[i][j] == 0:
                empty_pos = (i, j)
        if count == 3 and empty_pos:
            return empty_pos
    
    # Check columns
    for j in range(4):
        count = 0
        empty_pos = None
        for i in range(4):
            if board[i][j] == player:
                count += 1
            elif board[i][j] == 0:
                empty_pos = (i, j)
        if count == 3 and empty_pos:
            return empty_pos
    
    # Check main diagonal
    count = 0
    empty_pos = None
    for i in range(4):
        if board[i][i] == player:
            count += 1
        elif board[i][i] == 0:
            empty_pos = (i, i)
    if count == 3 and empty_pos:
        return empty_pos
    
    # Check anti-diagonal
    count = 0
    empty_pos = None
    for i in range(4):
        if board[i][3-i] == player:
            count += 1
        elif board[i][3-i] == 0:
            empty_pos = (i, 3-i)
    if count == 3 and empty_pos:
        return empty_pos
    
    return None
