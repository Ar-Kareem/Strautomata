
import random

def get_all_lines():
    lines = []
    # 1D lines (parallel to axes)
    for i in range(3):
        for j in range(3):
            lines.append([(i, j, k) for k in range(3)]) # x,y fixed
            lines.append([(i, k, j) for k in range(3)]) # x,z fixed
            lines.append([(k, i, j) for k in range(3)]) # y,z fixed
            
    # 2D diagonal lines
    for i in range(3):
        lines.append([(i, j, j) for j in range(3)])
        lines.append([(i, j, 2-j) for j in range(3)])
        lines.append([(j, i, j) for j in range(3)])
        lines.append([(j, i, 2-j) for j in range(3)])
        lines.append([(j, j, i) for j in range(3)])
        lines.append([(j, 2-j, i) for j in range(3)])
        
    # 3D space diagonals
    lines.append([(j, j, j) for j in range(3)])
    lines.append([(j, j, 2-j) for j in range(3)])
    lines.append([(j, 2-j, j) for j in range(3)])
    lines.append([(j, 2-j, 2-j) for j in range(3)])
    
    return lines

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    lines = get_all_lines()
    
    # Priority 1: Check if we can win in one move
    for line in lines:
        values = [board[p[0]][p[1]][p[2]] for p in line]
        if values.count(1) == 2 and values.count(0) == 1:
            idx = values.index(0)
            return line[idx]
            
    # Priority 2: Block opponent from winning
    for line in lines:
        values = [board[p[0]][p[1]][p[2]] for p in line]
        if values.count(-1) == 2 and values.count(0) == 1:
            idx = values.index(0)
            return line[idx]
            
    # Priority 3: Take the center if available
    if board[1][1][1] == 0:
        return (1, 1, 1)
        
    # Priority 4: Pick a move that has the most potential (exists in most non-blocked lines)
    best_move = None
    max_potential = -1
    
    empty_cells = []
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] == 0:
                    potential = 0
                    for line in lines:
                        if (x, y, z) in line:
                            line_vals = [board[p[0]][p[1]][p[2]] for p in line]
                            # Line is still viable if opponent has no pieces in it
                            if -1 not in line_vals:
                                potential += 1
                    empty_cells.append(((x, y, z), potential))
    
    if not empty_cells:
        return (0, 0, 0) # Should not happen in normal play
        
    # Return cell with highest potential
    empty_cells.sort(key=lambda x: x[1], reverse=True)
    return empty_cells[0][0]
