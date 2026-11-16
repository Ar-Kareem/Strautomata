
import numpy as np

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    3D Tic-Tac-Toe AI for a 3x3x3 board.
    - 0: Empty
    - 1: Me
    - -1: Opponent
    """
    b = np.array(board)
    
    # Generate all possible winning lines as coordinate sets
    lines = []
    
    # Orthogonal lines
    for i in range(3):
        for j in range(3):
            lines.append([(i, j, k) for k in range(3)]) # x,y fixed
            lines.append([(i, k, j) for k in range(3)]) # x,z fixed
            lines.append([(k, i, j) for k in range(3)]) # y,z fixed
            
    # Face diagonals
    for i in range(3):
        lines.append([(i, j, j) for j in range(3)])
        lines.append([(i, j, 2-j) for j in range(3)])
        lines.append([(j, i, j) for j in range(3)])
        lines.append([(j, i, 2-j) for j in range(3)])
        lines.append([(j, j, i) for j in range(3)])
        lines.append([(j, 2-j, i) for j in range(3)])
        
    # Space diagonals
    lines.append([(i, i, i) for i in range(3)])
    lines.append([(i, i, 2-i) for i in range(3)])
    lines.append([(i, 2-i, i) for i in range(3)])
    lines.append([(i, 2-i, 2-i) for i in range(3)])

    def find_move(target_sum):
        """
        Finds a line where the sum of values equals target_sum.
        target_sum=2 means I have two and one empty (Win).
        target_sum=-2 means opponent has two and one empty (Block).
        """
        for line in lines:
            vals = [b[coords] for coords in line]
            if sum(vals) == target_sum:
                for i, coords in enumerate(line):
                    if vals[i] == 0:
                        return coords
        return None

    # 1. Check for immediate win
    move = find_move(2)
    if move: return move
    
    # 2. Block opponent win
    move = find_move(-2)
    if move: return move
    
    # 3. Take the absolute center if available
    if b[1, 1, 1] == 0:
        return (1, 1, 1)
    
    # 4. Take corners if available (corners have most connectivity after center)
    corners = [(0,0,0), (0,0,2), (0,2,0), (0,2,2), (2,0,0), (2,0,2), (2,2,0), (2,2,2)]
    for c in corners:
        if b[c] == 0:
            return c
            
    # 5. Play anywhere else
    empty_cells = np.argwhere(b == 0)
    if len(empty_cells) > 0:
        return tuple(empty_cells[0])
    
    return (0, 0, 0)
