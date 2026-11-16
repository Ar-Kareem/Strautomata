
import random

def get_all_lines():
    lines = []
    # Orthogonal lines
    for i in range(3):
        for j in range(3):
            lines.append([(i, j, k) for k in range(3)]) # x, y fixed
            lines.append([(i, k, j) for k in range(3)]) # x, z fixed
            lines.append([(k, i, j) for k in range(3)]) # y, z fixed
    
    # Plane diagonals
    for i in range(3):
        # Diagonals in x-y planes
        lines.append([(j, j, i) for j in range(3)])
        lines.append([(j, 2-j, i) for j in range(3)])
        # Diagonals in x-z planes
        lines.append([(j, i, j) for j in range(3)])
        lines.append([(j, i, 2-j) for j in range(3)])
        # Diagonals in y-z planes
        lines.append([(i, j, j) for j in range(3)])
        lines.append([(i, j, 2-j) for j in range(3)])
        
    # Space diagonals
    lines.append([(j, j, j) for j in range(3)])
    lines.append([(j, j, 2-j) for j in range(3)])
    lines.append([(j, 2-j, j) for j in range(3)])
    lines.append([(2-j, j, j) for j in range(3)])
    
    return lines

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    lines = get_all_lines()
    
    def get_val(coords):
        z, y, x = coords # Mapping depth, row, col
        return board[z][y][x]

    # 1. Check for immediate win (Player 1)
    for line in lines:
        vals = [get_val(p) for p in line]
        if vals.count(1) == 2 and vals.count(0) == 1:
            idx = vals.index(0)
            return line[idx]

    # 2. Block opponent's win (Player -1)
    for line in lines:
        vals = [get_val(p) for p in line]
        if vals.count(-1) == 2 and vals.count(0) == 1:
            idx = vals.index(0)
            return line[idx]

    # 3. Priority move: Center (1, 1, 1)
    if board[1][1][1] == 0:
        return (1, 1, 1)

    # 4. Try to setup a line
    for line in lines:
        vals = [get_val(p) for p in line]
        if vals.count(1) == 1 and vals.count(0) == 2:
            for p in line:
                if get_val(p) == 0:
                    return p
                    
    # 5. Last resort: Any empty spot
    empty_spots = []
    for z in range(3):
        for y in range(3):
            for x in range(3):
                if board[z][y][x] == 0:
                    empty_spots.append((z, y, x))
    
    if empty_spots:
        return random.choice(empty_spots)
        
    return (0, 0, 0) # Should never reach here in a valid game
