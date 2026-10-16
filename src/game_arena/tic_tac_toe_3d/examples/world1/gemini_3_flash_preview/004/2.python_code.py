
import random

def get_all_lines():
    lines = []
    # Orthogonal lines
    for i in range(3):
        for j in range(3):
            lines.append([(i, j, k) for k in range(3)]) # depth
            lines.append([(i, k, j) for k in range(3)]) # column
            lines.append([(k, i, j) for k in range(3)]) # row

    # Face diagonals
    for i in range(3):
        lines.append([(i, j, j) for j in range(3)])
        lines.append([(i, j, 2 - j) for j in range(3)])
        lines.append([(j, i, j) for j in range(3)])
        lines.append([(j, i, 2 - j) for j in range(3)])
        lines.append([(j, j, i) for j in range(3)])
        lines.append([(j, 2 - j, i) for j in range(3)])

    # Space diagonals
    lines.append([(i, i, i) for i in range(3)])
    lines.append([(i, i, 2 - i) for i in range(3)])
    lines.append([(i, 2 - i, i) for i in range(3)])
    lines.append([(i, 2 - i, 2 - i) for i in range(3)])
    
    return lines

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    lines = get_all_lines()
    
    def get_val(coord):
        return board[coord[0]][coord[1]][coord[2]]

    # 1. Check for immediate win
    for line in lines:
        values = [get_val(c) for c in line]
        if values.count(1) == 2 and values.count(0) == 1:
            idx = values.index(0)
            return line[idx]

    # 2. Block opponent's immediate win
    for line in lines:
        values = [get_val(c) for c in line]
        if values.count(-1) == 2 and values.count(0) == 1:
            idx = values.index(0)
            return line[idx]

    # 3. Create a fork or strategic move
    # Score empty cells based on how many "open" lines they belong to
    cell_scores = {}
    for z in range(3):
        for y in range(3):
            for x in range(3):
                if board[z][y][x] == 0:
                    cell_scores[(z, y, x)] = 0

    for line in lines:
        values = [get_val(c) for c in line]
        # If the line is potentially winnable (no opponent marks)
        if values.count(-1) == 0:
            for c in line:
                if get_val(c) == 0:
                    cell_scores[c] += (1 + values.count(1))
        # If we need to block an opponent's developing line
        if values.count(1) == 0:
            for c in line:
                if get_val(c) == 0:
                    cell_scores[c] += (1 + values.count(-1))

    if cell_scores:
        # Heavily prioritize the center
        if board[1][1][1] == 0:
            return (1, 1, 1)
            
        best_move = max(cell_scores, key=cell_scores.get)
        return best_move

    # Fallback to first empty
    for z in range(3):
        for y in range(3):
            for x in range(3):
                if board[z][y][x] == 0:
                    return (z, y, x)
    
    return (0, 0, 0)
