
import numpy as np
from typing import List, Tuple

def generate_winning_lines() -> List[List[Tuple[int, int, int]]]:
    """Generate all 49 winning lines in a 3x3x3 tic-tac-toe board."""
    lines = []
    
    # Lines parallel to axes (27 lines)
    # x-direction
    for y in range(3):
        for z in range(3):
            lines.append([(0, y, z), (1, y, z), (2, y, z)])
    # y-direction
    for x in range(3):
        for z in range(3):
            lines.append([(x, 0, z), (x, 1, z), (x, 2, z)])
    # z-direction
    for x in range(3):
        for y in range(3):
            lines.append([(x, y, 0), (x, y, 1), (x, y, 2)])
    
    # Face diagonals (18 lines)
    # xy-plane diagonals
    for z in range(3):
        lines.append([(0, 0, z), (1, 1, z), (2, 2, z)])
        lines.append([(0, 2, z), (1, 1, z), (2, 0, z)])
    # xz-plane diagonals
    for y in range(3):
        lines.append([(0, y, 0), (1, y, 1), (2, y, 2)])
        lines.append([(0, y, 2), (1, y, 1), (2, y, 0)])
    # yz-plane diagonals
    for x in range(3):
        lines.append([(x, 0, 0), (x, 1, 1), (x, 2, 2)])
        lines.append([(x, 0, 2), (x, 1, 1), (x, 2, 0)])
    
    # Space diagonals (4 lines)
    lines.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
    lines.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
    lines.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
    lines.append([(0, 2, 2), (1, 1, 1), (2, 0, 0)])
    
    return lines

WINNING_LINES = generate_winning_lines()

# Precompute which lines each cell belongs to for faster lookup
CELL_TO_LINES = {}
for i in range(3):
    for j in range(3):
        for k in range(3):
            CELL_TO_LINES[(i, j, k)] = []

for line_idx, line in enumerate(WINNING_LINES):
    for cell in line:
        CELL_TO_LINES[cell].append(line_idx)

def check_win(board: List[List[List[int]]], player: int) -> bool:
    """Check if player has won."""
    for line in WINNING_LINES:
        if all(board[i][j][k] == player for (i, j, k) in line):
            return True
    return False

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    Smart policy for 3x3x3 Tic Tac Toe.
    Strategy:
    1. Win if possible
    2. Block opponent's win
    3. Create a fork (two threats)
    4. Block opponent's fork
    5. Take center
    6. Take corners
    7. Take any available cell
    """
    # Get all empty cells
    empty_cells = [(i, j, k) for i in range(3) for j in range(3) for k in range(3) if board[i][j][k] == 0]
    
    if not empty_cells:
        return (0, 0, 0)  # Should not happen in valid game state
    
    # 1. Check for immediate win
    for cell in empty_cells:
        i, j, k = cell
        board[i][j][k] = 1
        if check_win(board, 1):
            board[i][j][k] = 0
            return cell
        board[i][j][k] = 0
    
    # 2. Check for immediate block
    for cell in empty_cells:
        i, j, k = cell
        board[i][j][k] = -1
        if check_win(board, -1):
            board[i][j][k] = 0
            return cell
        board[i][j][k] = 0
    
    # 3. Look for fork opportunities (create two threats)
    best_fork_cell = None
    max_threats = 0
    
    for cell in empty_cells:
        threats = 0
        
        for line_idx in CELL_TO_LINES[cell]:
            line = WINNING_LINES[line_idx]
            our_marks = 0
            empties = 0
            
            for (x, y, z) in line:
                val = board[x][y][z]
                if val == 1:
                    our_marks += 1
                elif val == 0:
                    empties += 1
            
            # If we play here, does this line become a threat?
            # (1 of our marks + this cell makes 2, with 1 other empty)
            if our_marks == 1 and empties == 2:
                threats += 1
        
        if threats > max_threats:
            max_threats = threats
            best_fork_cell = cell
    
    if best_fork_cell and max_threats >= 2:
        return best_fork_cell
    
    # 4. Block opponent's forks
    best_block_cell = None
    max_opp_threats = 0
    
    for cell in empty_cells:
        threats = 0
        
        for line_idx in CELL_TO_LINES[cell]:
            line = WINNING_LINES[line_idx]
            opp_marks = 0
            empties = 0
            
            for (x, y, z) in line:
                val = board[x][y][z]
                if val == -1:
                    opp_marks += 1
                elif val == 0:
                    empties += 1
            
            # If opponent plays here, does this line become a threat?
            if opp_marks == 1 and empties == 2:
                threats += 1
        
        if threats > max_opp_threats:
            max_opp_threats = threats
            best_block_cell = cell
    
    if best_block_cell and max_opp_threats >= 2:
        return best_block_cell
    
    # 5. Take center if available
    if board[1][1][1] == 0:
        return (1, 1, 1)
    
    # 6. Take corners
    corners = [(0,0,0), (0,0,2), (0,2,0), (0,2,2),
               (2,0,0), (2,0,2), (2,2,0), (2,2,2)]
    for corner in corners:
        i, j, k = corner
        if board[i][j][k] == 0:
            return corner
    
    # 7. Take any available cell
    return empty_cells[0]
