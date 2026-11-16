
import numpy as np
from typing import List, Tuple

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    # Convert to numpy array for easier manipulation
    board_array = np.array(board)
    
    # All possible winning lines in 3D tic-tac-toe
    def get_all_lines():
        lines = []
        
        # Lines along x-axis (rows)
        for z in range(3):
            for y in range(3):
                lines.append([(x, y, z) for x in range(3)])
        
        # Lines along y-axis (columns) 
        for z in range(3):
            for x in range(3):
                lines.append([(x, y, z) for y in range(3)])
        
        # Lines along z-axis (depth)
        for x in range(3):
            for y in range(3):
                lines.append([(x, y, z) for z in range(3)])
        
        # Diagonals in xy planes
        for z in range(3):
            lines.append([(i, i, z) for i in range(3)])
            lines.append([(i, 2-i, z) for i in range(3)])
        
        # Diagonals in xz planes
        for y in range(3):
            lines.append([(i, y, i) for i in range(3)])
            lines.append([(i, y, 2-i) for i in range(3)])
        
        # Diagonals in yz planes
        for x in range(3):
            lines.append([(x, i, i) for i in range(3)])
            lines.append([(x, i, 2-i) for i in range(3)])
        
        # 3D diagonals
        lines.append([(i, i, i) for i in range(3)])
        lines.append([(i, i, 2-i) for i in range(3)])
        lines.append([(i, 2-i, i) for i in range(3)])
        lines.append([(i, 2-i, 2-i) for i in range(3)])
        
        return lines
    
    def evaluate_line(line):
        """Returns (my_count, opponent_count, empty_positions) for a line"""
        my_count = 0
        opponent_count = 0
        empty_positions = []
        
        for pos in line:
            value = board_array[pos]
            if value == 1:  # Me
                my_count += 1
            elif value == -1:  # Opponent
                opponent_count += 1
            else:  # Empty
                empty_positions.append(pos)
        
        return my_count, opponent_count, empty_positions
    
    all_lines = get_all_lines()
    
    # 1. Check for winning moves
    for line in all_lines:
        my_count, opponent_count, empty_positions = evaluate_line(line)
        if my_count == 2 and opponent_count == 0 and len(empty_positions) == 1:
            return empty_positions[0]
    
    # 2. Check for blocking opponent wins
    for line in all_lines:
        my_count, opponent_count, empty_positions = evaluate_line(line)
        if opponent_count == 2 and my_count == 0 and len(empty_positions) == 1:
            return empty_positions[0]
    
    # 3. Strategic moves - prioritize center, then corners
    empty_positions = []
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board_array[x, y, z] == 0:
                    empty_positions.append((x, y, z))
    
    if not empty_positions:
        # Shouldn't happen if game is still ongoing
        return (0, 0, 0)
    
    # Check for center
    center = (1, 1, 1)
    if center in empty_positions:
        return center
    
    # Check for corners
    corners = [(0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),
               (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2)]
    
    for corner in corners:
        if corner in empty_positions:
            return corner
    
    # Check for edge centers
    edge_centers = [(0, 1, 1), (1, 0, 1), (1, 1, 0), 
                    (1, 1, 2), (1, 2, 1), (2, 1, 1)]
    
    for edge_center in edge_centers:
        if edge_center in empty_positions:
            return edge_center
    
    # If all else fails, return first available position
    return empty_positions[0]
