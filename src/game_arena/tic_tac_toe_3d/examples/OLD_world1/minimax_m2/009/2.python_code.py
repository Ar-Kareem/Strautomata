
# Precompute the winning lines for a 3x3x3 Tic Tac Toe board
def precompute_winning_lines():
    lines = []
    # Axis lines (x-axis)
    for y in range(3):
        for z in range(3):
            lines.append([(x, y, z) for x in range(3)])
    # Axis lines (y-axis)
    for x in range(3):
        for z in range(3):
            lines.append([(x, y, z) for y in range(3)])
    # Axis lines (z-axis)
    for x in range(3):
        for y in range(3):
            lines.append([(x, y, z) for z in range(3)])
    # Planar diagonals (fixed z)
    for z in range(3):
        lines.append([(0,0,z), (1,1,z), (2,2,z)])
        lines.append([(0,2,z), (1,1,z), (2,0,z)])
    # Planar diagonals (fixed x)
    for x in range(3):
        lines.append([(x,0,0), (x,1,1), (x,2,2)])
        lines.append([(x,0,2), (x,1,1), (x,2,0)])
    # Planar diagonals (fixed y)
    for y in range(3):
        lines.append([(0,y,0), (1,y,1), (2,y,2)])
        lines.append([(0,y,2), (1,y,1), (2,y,0)])
    # Space diagonals
    lines.append([(0,0,0), (1,1,1), (2,2,2)])
    lines.append([(0,0,2), (1,1,1), (2,2,0)])
    lines.append([(0,2,0), (1,1,1), (2,0,2)])
    lines.append([(0,2,2), (1,1,1), (2,0,0)])
    
    # Precompute mapping from cell to line indices
    cell_to_lines = {}
    for idx, line in enumerate(lines):
        for cell in line:
            if cell not in cell_to_lines:
                cell_to_lines[cell] = []
            cell_to_lines[cell].append(idx)
    
    return lines, cell_to_lines

# Precompute winning lines and cell mappings
_WINNING_LINES, _CELL_TO_LINES = precompute_winning_lines()

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Step 1: Check for immediate win
    for line in _WINNING_LINES:
        count_us = 0
        count_empty = 0
        empty_pos = None
        for (x, y, z) in line:
            if board[x][y][z] == 1:
                count_us += 1
            elif board[x][y][z] == 0:
                count_empty += 1
                empty_pos = (x, y, z)
            else:
                break
        else:
            if count_us == 2 and count_empty == 1:
                return empty_pos
    
    # Step 2: Block opponent's immediate win
    threats_blocked = {}
    for line in _WINNING_LINES:
        count_opponent = 0
        count_empty = 0
        empty_pos = None
        for (x, y, z) in line:
            if board[x][y][z] == -1:
                count_opponent += 1
            elif board[x][y][z] == 0:
                count_empty += 1
                empty_pos = (x, y, z)
            else:
                break
        if count_opponent == 2 and count_empty == 1:
            if empty_pos in threats_blocked:
                threats_blocked[empty_pos] += 1
            else:
                threats_blocked[empty_pos] = 1
    
    if threats_blocked:
        best_move = None
        max_threats = 0
        for pos, cnt in threats_blocked.items():
            if cnt > max_threats:
                max_threats = cnt
                best_move = pos
        return best_move
    
    # Step 3: Choose a strategic move
    open_lines = set()
    for idx, line in enumerate(_WINNING_LINES):
        count_opponent = 0
        for (x, y, z) in line:
            if board[x][y][z] == -1:
                count_opponent += 1
                if count_opponent >= 2:
                    break
        if count_opponent < 2:
            open_lines.add(idx)
    
    best_move = None
    max_count = -1
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] == 0:
                    count = 0
                    for idx in _CELL_TO_LINES[(x, y, z)]:
                        if idx in open_lines:
                            count += 1
                    if count > max_count:
                        max_count = count
                        best_move = (x, y, z)
    
    if best_move is None:
        for x in range(3):
            for y in range(3):
                for z in range(3):
                    if board[x][y][z] == 0:
                        return (x, y, z)
    
    return best_move
