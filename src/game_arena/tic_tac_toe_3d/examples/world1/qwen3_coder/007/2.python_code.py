
import random
from typing import List, Tuple, Optional

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    # Check for immediate winning moves
    winning_move = find_winning_move(board, 1)
    if winning_move:
        return winning_move
    
    # Check for moves to block opponent's win
    blocking_move = find_winning_move(board, -1)
    if blocking_move:
        return blocking_move
    
    # Strategic moves: center, then corners, then edges
    # Center position
    if board[1][1][1] == 0:
        return (1, 1, 1)
    
    # Corners
    corners = [
        (0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),
        (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2)
    ]
    available_corners = [pos for pos in corners if board[pos[0]][pos[1]][pos[2]] == 0]
    if available_corners:
        return random.choice(available_corners)
    
    # Any available position
    available_positions = []
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    available_positions.append((i, j, k))
    
    if available_positions:
        return random.choice(available_positions)
    
    # Should never happen in a valid game
    raise Exception("No valid moves available")

def find_winning_move(board: List[List[List[int]]], player: int) -> Optional[Tuple[int, int, int]]:
    """Find a move that would result in a win for the given player"""
    # Check all possible lines in 3D tic-tac-toe
    
    # Lines along x-axis (rows)
    for z in range(3):
        for y in range(3):
            line = [(x, y, z) for x in range(3)]
            move = check_line_for_win(board, line, player)
            if move:
                return move
    
    # Lines along y-axis (columns)
    for z in range(3):
        for x in range(3):
            line = [(x, y, z) for y in range(3)]
            move = check_line_for_win(board, line, player)
            if move:
                return move
    
    # Lines along z-axis (depth)
    for y in range(3):
        for x in range(3):
            line = [(x, y, z) for z in range(3)]
            move = check_line_for_win(board, line, player)
            if move:
                return move
    
    # Diagonals in xy planes (for each z)
    for z in range(3):
        # Main diagonal
        line = [(i, i, z) for i in range(3)]
        move = check_line_for_win(board, line, player)
        if move:
            return move
        # Anti-diagonal
        line = [(i, 2-i, z) for i in range(3)]
        move = check_line_for_win(board, line, player)
        if move:
            return move
    
    # Diagonals in xz planes (for each y)
    for y in range(3):
        # Main diagonal
        line = [(i, y, i) for i in range(3)]
        move = check_line_for_win(board, line, player)
        if move:
            return move
        # Anti-diagonal
        line = [(i, y, 2-i) for i in range(3)]
        move = check_line_for_win(board, line, player)
        if move:
            return move
    
    # Diagonals in yz planes (for each x)
    for x in range(3):
        # Main diagonal
        line = [(x, i, i) for i in range(3)]
        move = check_line_for_win(board, line, player)
        if move:
            return move
        # Anti-diagonal
        line = [(x, i, 2-i) for i in range(3)]
        move = check_line_for_win(board, line, player)
        if move:
            return move
    
    # Space diagonals
    # Main space diagonal
    line = [(i, i, i) for i in range(3)]
    move = check_line_for_win(board, line, player)
    if move:
        return move
    
    # Other space diagonals
    line = [(i, i, 2-i) for i in range(3)]
    move = check_line_for_win(board, line, player)
    if move:
        return move
    
    line = [(i, 2-i, i) for i in range(3)]
    move = check_line_for_win(board, line, player)
    if move:
        return move
    
    line = [(i, 2-i, 2-i) for i in range(3)]
    move = check_line_for_win(board, line, player)
    if move:
        return move
    
    return None

def check_line_for_win(board: List[List[List[int]]], line: List[Tuple[int, int, int]], player: int) -> Optional[Tuple[int, int, int]]:
    """Check if a line has exactly 2 pieces of the player and one empty spot"""
    player_count = 0
    empty_spot = None
    
    for pos in line:
        x, y, z = pos
        if board[x][y][z] == player:
            player_count += 1
        elif board[x][y][z] == 0:
            empty_spot = pos
        else:  # opponent piece
            return None
    
    # If we have exactly 2 of player's pieces and one empty spot, that's a winning move
    if player_count == 2 and empty_spot is not None:
        return empty_spot
    
    return None
