
import random

def get_winning_lines():
    lines = []
    # 1D Lines (Rows, Columns, Pillars)
    for i in range(3):
        for j in range(3):
            lines.append([(i, j, k) for k in range(3)]) # x, y fixed
            lines.append([(i, k, j) for k in range(3)]) # x, z fixed
            lines.append([(k, i, j) for k in range(3)]) # y, z fixed
    
    # 2D Diagonals
    for i in range(3):
        # Plane x=i
        lines.append([(i, k, k) for k in range(3)])
        lines.append([(i, k, 2-k) for k in range(3)])
        # Plane y=i
        lines.append([(k, i, k) for k in range(3)])
        lines.append([(k, i, 2-k) for k in range(3)])
        # Plane z=i
        lines.append([(k, k, i) for k in range(3)])
        lines.append([(k, 2-k, i) for k in range(3)])
        
    # 3D Diagonals (Space Diagonals)
    lines.append([(k, k, k) for k in range(3)])
    lines.append([(k, k, 2-k) for k in range(3)])
    lines.append([(k, 2-k, k) for k in range(3)])
    lines.append([(2-k, k, k) for k in range(3)])
    
    return lines

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    lines = get_winning_lines()
    
    # 1. Check if we can win in this move
    for line in lines:
        values = [board[c[0]][c[1]][c[2]] for c in line]
        if values.count(1) == 2 and values.count(0) == 1:
            idx = values.index(0)
            return line[idx]
            
    # 2. Check if we need to block the opponent
    for line in lines:
        values = [board[c[0]][c[1]][c[2]] for c in line]
        if values.count(-1) == 2 and values.count(0) == 1:
            idx = values.index(0)
            return line[idx]
            
    # 3. Try to take the absolute center
    if board[1][1][1] == 0:
        return (1, 1, 1)
    
    # 4. Try to take corners (historically strong in Tic Tac Toe)
    corners = [(i, j, k) for i in [0, 2] for j in [0, 2] for k in [0, 2]]
    random.shuffle(corners)
    for c in corners:
        if board[c[0]][c[1]][c[2]] == 0:
            return c
            
    # 5. Take any available spot
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] == 0:
                    return (x, y, z)
                    
    return (0, 0, 0) # Should not be reachable
