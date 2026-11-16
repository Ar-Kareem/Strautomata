
import numpy as np
from typing import List, Tuple

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    # Convert to numpy array for easier manipulation
    board = np.array(board)
    
    # Get all possible winning lines (27 total: 3*3 rows, 3*3 cols, 3*3 pillars, plus diagonals)
    def get_winning_lines():
        lines = []
        
        # All rows (fix y,z and vary x)
        for y in range(3):
            for z in range(3):
                lines.append([(x, y, z) for x in range(3)])
        
        # All columns (fix x,z and vary y)
        for x in range(3):
            for z in range(3):
                lines.append([(x, y, z) for y in range(3)])
        
        # All pillars (fix x,y and vary z)
        for x in range(3):
            for y in range(3):
                lines.append([(x, y, z) for z in range(3)])
        
        # Face diagonals on each face
        # XY faces at each z level
        for z in range(3):
            lines.append([(0,0,z), (1,1,z), (2,2,z)])
            lines.append([(2,0,z), (1,1,z), (0,2,z)])
        
        # XZ faces at each y level
        for y in range(3):
            lines.append([(0,y,0), (1,y,1), (2,y,2)])
            lines.append([(2,y,0), (1,y,1), (0,y,2)])
        
        # YZ faces at each x level
        for x in range(3):
            lines.append([(x,0,0), (x,1,1), (x,2,2)])
            lines.append([(x,2,0), (x,1,1), (x,0,2)])
        
        # Main cube diagonals
        lines.append([(0,0,0), (1,1,1), (2,2,2)])
        lines.append([(2,0,0), (1,1,1), (0,2,2)])
        lines.append([(0,2,0), (1,1,1), (2,0,2)])
        lines.append([(0,0,2), (1,1,1), (2,2,0)])
        lines.append([(2,2,0), (1,1,1), (0,0,2)])
        lines.append([(2,0,2), (1,1,1), (0,2,0)])
        lines.append([(0,2,2), (1,1,1), (2,0,0)])
        lines.append([(2,2,2), (1,1,1), (0,0,0)])
        
        return lines
    
    def is_winning_move(pos, player):
        temp_board = board.copy()
        temp_board[pos] = player
        lines = get_winning_lines()
        
        for line in lines:
            if all(temp_board[cell] == player for cell in line):
                return True
        return False
    
    # Check for winning move
    empty_cells = []
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x, y, z] == 0:
                    empty_cells.append((x, y, z))
                    if is_winning_move((x, y, z), 1):
                        return (x, y, z)
    
    # Check for blocking opponent's winning move
    for x, y, z in empty_cells:
        if is_winning_move((x, y, z), -1):
            return (x, y, z)
    
    # If no immediate win or block, use strategic positioning
    # Score each empty cell by how many winning lines it belongs to
    lines = get_winning_lines()
    cell_scores = {}
    
    for x, y, z in empty_cells:
        score = 0
        for line in lines:
            if (x, y, z) in line:
                # Count how many of these lines have potential to be completed
                line_values = [board[cell] for cell in line]
                if 1 in line_values and -1 not in line_values:  # My mark present, opponent absent
                    score += 1
                elif -1 in line_values and 1 not in line_values:  # Opponent present, me absent
                    score += 1
                elif 1 not in line_values and -1 not in line_values:  # Empty line
                    score += 1
        
        # Bonus for center positions
        if (x, y, z) == (1, 1, 1):
            score += 5  # Center gets highest priority
        elif x == 1 or y == 1 or z == 1:
            score += 1  # Edge centers get small bonus
        
        cell_scores[(x, y, z)] = score
    
    # Return the empty cell with highest score
    return max(cell_scores.keys(), key=lambda k: cell_scores[k])
