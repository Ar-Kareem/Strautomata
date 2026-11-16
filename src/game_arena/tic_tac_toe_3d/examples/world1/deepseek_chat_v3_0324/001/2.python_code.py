
import random
from typing import List, Tuple

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    # First check if we can win immediately
    move = find_winning_move(board, 1)
    if move is not None:
        return move
    
    # Then check if opponent can win and block them
    move = find_winning_move(board, -1)
    if move is not None:
        return move
    
    # Try to take the center if available
    if board[1][1][1] == 0:
        return (1, 1, 1)
    
    # Then try to take a corner
    corners = [
        (0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),
        (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2)
    ]
    for corner in corners:
        z, y, x = corner
        if board[z][y][x] == 0:
            return corner
    
    # If all else fails, choose a random available move
    available_moves = []
    for z in range(3):
        for y in range(3):
            for x in range(3):
                if board[z][y][x] == 0:
                    available_moves.append((z, y, x))
    return random.choice(available_moves)

def find_winning_move(board: List[List[List[int]]], player: int) -> None:
    # Check all possible lines for a winning move
    lines = []
    
    # Layer rows, columns, and diagonals (3 layers x 8 lines)
    for z in range(3):
        # Rows
        for y in range(3):
            lines.append([(z, y, x) for x in range(3)])
        # Columns
        for x in range(3):
            lines.append([(z, y, x) for y in range(3)])
        # Diagonals
        lines.append([(z, y, y) for y in range(3)])
        lines.append([(z, y, 2-y) for y in range(3)])
    
    # Vertical columns (9 lines)
    for y in range(3):
        for x in range(3):
            lines.append([(z, y, x) for z in range(3)])
    
    # Space diagonals (6 lines)
    lines.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
    lines.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
    lines.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
    lines.append([(0, 2, 2), (1, 1, 1), (2, 0, 0)])
    # Additional space diagonals
    lines.append([(0, 0, 1), (1, 1, 1), (2, 2, 1)])
    lines.append([(0, 1, 0), (1, 1, 1), (2, 1, 2)])
    lines.append([(0, 1, 2), (1, 1, 1), (2, 1, 0)])
    lines.append([(0, 2, 1), (1, 1, 1), (2, 0, 1)])
    lines.append([(1, 0, 0), (1, 1, 1), (1, 2, 2)])
    lines.append([(1, 0, 2), (1, 1, 1), (1, 2, 0)])
    lines.append([(0, 1, 1), (1, 1, 1), (2, 1, 1)])
    lines.append([(0, 0, 0), (0, 1, 1), (0, 2, 2)])
    
    for line in lines:
        # Count how many cells are occupied by player and how many are empty
        count = sum(1 for z, y, x in line if board[z][y][x] == player)
        empty = [(z, y, x) for z, y, x in line if board[z][y][x] == 0]
        
        if count == 2 and len(empty) == 1:
            return empty[0]
    
    return None
