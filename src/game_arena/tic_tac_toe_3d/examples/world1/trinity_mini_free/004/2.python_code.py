
import numpy as np

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Precompute all 27 lines in the 3x3x3 cube
    lines = []
    # Lines along x-axis (fixed y, z)
    for j in range(3):
        for k in range(3):
            lines.append([(0, j, k), (1, j, k), (2, j, k)])
    # Lines along y-axis (fixed x, z)
    for i in range(3):
        for k in range(3):
            lines.append([(i, 0, k), (i, 1, k), (i, 2, k)])
    # Lines along z-axis (fixed x, y)
    for i in range(3):
        for j in range(3):
            lines.append([(i, j, 0), (i, j, 1), (i, j, 2)])
    
    # Step 1: Check for winning move (two 1s and one empty)
    for line in lines:
        count = 0
        empty_index = -1
        for idx, coord in enumerate(line):
            x, y, z = coord
            if board[x][y][z] == 1:
                count += 1
            elif board[x][y][z] == 0:
                empty_index = idx
        if count == 2 and empty_index != -1:
            return line[empty_index]
    
    # Step 2: Check for blocking move (two -1s and one empty)
    for line in lines:
        count = 0
        empty_index = -1
        for idx, coord in enumerate(line):
            x, y, z = coord
            if board[x][y][z] == -1:
                count += 1
            elif board[x][y][z] == 0:
                empty_index = idx
        if count == 2 and empty_index != -1:
            return line[empty_index]
    
    # Step 3: Check for fork (creates two winning opportunities)
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    count_win = 0
                    for line in lines:
                        if (i, j, k) in line:
                            line_count = 0
                            empty_count = 0
                            for coord in line:
                                x, y, z = coord
                                if board[x][y][z] == 1:
                                    line_count += 1
                                elif board[x][y][z] == 0:
                                    empty_count += 1
                            if line_count == 1 and empty_count == 2:
                                count_win += 1
                    if count_win >= 2:
                        return (i, j, k)
    
    # Step 4: Check for winning opportunity (one 1 and two empties)
    for line in lines:
        count = 0
        empty_count = 0
        for coord in line:
            x, y, z = coord
            if board[x][y][z] == 1:
                count += 1
            elif board[x][y][z] == 0:
                empty_count += 1
        if count == 1 and empty_count == 2:
            for coord in line:
                x, y, z = coord
                if board[x][y][z] == 0:
                    return (x, y, z)
    
    # Step 5: Prioritize center (1,1,1)
    if board[1][1][1] == 0:
        return (1, 1, 1)
    
    # Step 6: Prioritize corners
    corners = [(0,0,0), (0,0,2), (0,2,0), (0,2,2),
               (2,0,0), (2,0,2), (2,2,0), (2,2,2)]
    for corner in corners:
        i, j, k = corner
        if board[i][j][k] == 0:
            return (i, j, k)
    
    # Step 7: Prioritize edges
    edges = [(0,0,1), (0,1,0), (0,1,2), (0,2,1),
             (1,0,0), (1,0,2), (1,2,0), (1,2,2),
             (2,0,1), (2,1,0), (2,1,2), (2,2,1)]
    for edge in edges:
        i, j, k = edge
        if board[i][j][k] == 0:
            return (i, j, k)
    
    # Fallback: Return any empty cell
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    return (i, j, k)
    return (0, 0, 0)  # Should not reach here
