
import random
from typing import List, Tuple

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    # All possible winning lines in 3D tic-tac-toe
    def get_winning_lines():
        lines = []
        
        # Lines along x-axis
        for y in range(3):
            for z in range(3):
                lines.append([(x, y, z) for x in range(3)])
        
        # Lines along y-axis
        for x in range(3):
            for z in range(3):
                lines.append([(x, y, z) for y in range(3)])
        
        # Lines along z-axis
        for x in range(3):
            for y in range(3):
                lines.append([(x, y, z) for z in range(3)])
        
        # Face diagonals on xy planes (z constant)
        for z in range(3):
            lines.append([(i, i, z) for i in range(3)])
            lines.append([(i, 2-i, z) for i in range(3)])
        
        # Face diagonals on xz planes (y constant)
        for y in range(3):
            lines.append([(i, y, i) for i in range(3)])
            lines.append([(i, y, 2-i) for i in range(3)])
        
        # Face diagonals on yz planes (x constant)
        for x in range(3):
            lines.append([(x, i, i) for i in range(3)])
            lines.append([(x, i, 2-i) for i in range(3)])
        
        # Space diagonals
        lines.append([(i, i, i) for i in range(3)])
        lines.append([(i, i, 2-i) for i in range(3)])
        lines.append([(i, 2-i, i) for i in range(3)])
        lines.append([(i, 2-i, 2-i) for i in range(3)])
        
        return lines
    
    def check_line(line, player):
        """Check if player has 2 pieces in line and one empty spot"""
        count_player = 0
        count_empty = 0
        empty_pos = None
        
        for pos in line:
            x, y, z = pos
            if board[x][y][z] == player:
                count_player += 1
            elif board[x][y][z] == 0:
                count_empty += 1
                empty_pos = pos
        
        # If player has 2 in a row and 1 empty, return the empty position to win/block
        if count_player == 2 and count_empty == 1:
            return empty_pos
        return None
    
    winning_lines = get_winning_lines()
    
    # Try to find a winning move
    for line in winning_lines:
        win_pos = check_line(line, 1)  # 1 is me
        if win_pos:
            return win_pos
    
    # Try to block opponent from winning
    for line in winning_lines:
        block_pos = check_line(line, -1)  # -1 is opponent
        if block_pos:
            return block_pos
    
    # Otherwise, choose strategically
    empty_positions = []
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] == 0:
                    empty_positions.append((x, y, z))
    
    if not empty_positions:
        # Should not happen in normal game flow
        return (0, 0, 0)
    
    # Prefer center, then corners, then edges
    center = (1, 1, 1)
    if center in empty_positions:
        return center
    
    # Corners in 3D
    corners = [
        (0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),
        (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2)
    ]
    
    corner_moves = [pos for pos in corners if pos in empty_positions]
    if corner_moves:
        return random.choice(corner_moves)
    
    # If no center or corners, return random empty position
    return random.choice(empty_positions)
