
import itertools

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Generate all possible winning lines in 3D Tic Tac Toe
    all_lines = []

    # Rows (fixed j, k)
    for k in range(3):
        for j in range(3):
            all_lines.append([(i, j, k) for i in range(3)])
    
    # Columns (fixed i, k)
    for k in range(3):
        for i in range(3):
            all_lines.append([(i, j, k) for j in range(3)])
    
    # Pillars (fixed i, j)
    for i in range(3):
        for j in range(3):
            all_lines.append([(i, j, k) for k in range(3)])
    
    # Layer diagonals (fixed k)
    for k in range(3):
        all_lines.append([(i, i, k) for i in range(3)])
        all_lines.append([(i, 2-i, k) for i in range(3)])
    
    # Space diagonals (through the cube)
    all_lines.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
    all_lines.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
    all_lines.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
    all_lines.append([(0, 2, 2), (1, 1, 1), (2, 0, 0)])
    
    # 1. Check for winning move
    for line in all_lines:
        my_count = 0
        empty = None
        valid = True
        for (i, j, k) in line:
            val = board[i][j][k]
            if val == 1:
                my_count += 1
            elif val == 0:
                if empty is None:
                    empty = (i, j, k)
                else:
                    valid = False  # More than one empty
                    break
            else:  # Opponent's cell
                valid = False
                break
        if valid and my_count == 2 and empty is not None:
            return empty
    
    # 2. Check for opponent's winning move
    for line in all_lines:
        opp_count = 0
        empty = None
        valid = True
        for (i, j, k) in line:
            val = board[i][j][k]
            if val == -1:
                opp_count += 1
            elif val == 0:
                if empty is None:
                    empty = (i, j, k)
                else:
                    valid = False
                    break
            else:  # My cell
                valid = False
                break
        if valid and opp_count == 2 and empty is not None:
            return empty
    
    # 3. Take the center if available
    if board[1][1][1] == 0:
        return (1, 1, 1)
    
    # 4. Find all empty cells
    empty_cells = []
    for i, j, k in itertools.product(range(3), repeat=3):
        if board[i][j][k] == 0:
            empty_cells.append((i, j, k))
    
    # Evaluate each empty cell by the number of open lines (no opponent marks)
    best_cell = None
    best_score = -1
    for cell in empty_cells:
        i, j, k = cell
        score = 0
        # Check each line that passes through this cell
        for line in all_lines:
            if cell in line:
                # Check if line is open (no opponent marks)
                if all(board[x][y][z] != -1 for (x, y, z) in line):
                    score += 1
        if score > best_score:
            best_score = score
            best_cell = cell
    
    return best_cell
