
# Precomputed winning lines for 3x3x3 Tic Tac Toe
all_lines = []

# x-direction lines (fixed j, k)
for j in range(3):
    for k in range(3):
        line = [(0, j, k), (1, j, k), (2, j, k)]
        all_lines.append(line)

# y-direction lines (fixed i, k)
for i in range(3):
    for k in range(3):
        line = [(i, 0, k), (i, 1, k), (i, 2, k)]
        all_lines.append(line)

# z-direction lines (fixed i, j)
for i in range(3):
    for j in range(3):
        line = [(i, j, 0), (i, j, 1), (i, j, 2)]
        all_lines.append(line)

# xy-plane diagonals (fixed k)
for k in range(3):
    line1 = [(0, 0, k), (1, 1, k), (2, 2, k)]
    line2 = [(0, 2, k), (1, 1, k), (2, 0, k)]
    all_lines.append(line1)
    all_lines.append(line2)

# xz-plane diagonals (fixed j)
for j in range(3):
    line1 = [(0, j, 0), (1, j, 1), (2, j, 2)]
    line2 = [(0, j, 2), (1, j, 1), (2, j, 0)]
    all_lines.append(line1)
    all_lines.append(line2)

# yz-plane diagonals (fixed i)
for i in range(3):
    line1 = [(i, 0, 0), (i, 1, 1), (i, 2, 2)]
    line2 = [(i, 0, 2), (i, 1, 1), (i, 2, 0)]
    all_lines.append(line1)
    all_lines.append(line2)

# Space diagonals
all_lines.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
all_lines.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
all_lines.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
all_lines.append([(0, 2, 2), (1, 1, 1), (2, 0, 0)])

# Map each cell to the lines it belongs to
cell_to_lines = {}
for i in range(3):
    for j in range(3):
        for k in range(3):
            cell = (i, j, k)
            lines = []
            for line in all_lines:
                if cell in line:
                    lines.append(line)
            cell_to_lines[cell] = lines

def check_win_for_cell(board, cell, player):
    """Check if placing `player` at `cell` wins the game by checking only lines containing `cell`."""
    for line in cell_to_lines[cell]:
        win = True
        for (x, y, z) in line:
            if board[x][y][z] != player:
                win = False
                break
        if win:
            return True
    return False

def compute_score(board, cell):
    """Compute a score for a cell based on strategic value."""
    i, j, k = cell
    score = 0
    # Center cell bonus
    if (i, j, k) == (1, 1, 1):
        score += 10
    
    for line in cell_to_lines[cell]:
        count_our = 0
        count_opponent = 0
        for (x, y, z) in line:
            if board[x][y][z] == 1:
                count_our += 1
            elif board[x][y][z] == -1:
                count_opponent += 1
        
        # Skip blocked lines
        if count_opponent >= 1:
            continue
        
        # Score based on existing marks
        if count_our == 1:
            score += 3
        else:  # count_our == 0
            score += 1
    
    return score

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Step 1: Check for immediate win
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    board[i][j][k] = 1
                    if check_win_for_cell(board, (i, j, k), 1):
                        board[i][j][k] = 0
                        return (i, j, k)
                    board[i][j][k] = 0
    
    # Step 2: Check for opponent immediate wins
    threats = []
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    board[i][j][k] = -1
                    if check_win_for_cell(board, (i, j, k), -1):
                        threats.append((i, j, k))
                    board[i][j][k] = 0
    
    # Block a threat if found
    if threats:
        best_move = None
        best_score = -1
        for cell in threats:
            score = compute_score(board, cell)
            if score > best_score:
                best_score = score
                best_move = cell
        return best_move
    
    # Step 3: Choose best move by score
    best_move = None
    best_score = -1
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    score = compute_score(board, (i, j, k))
                    if score > best_score:
                        best_score = score
                        best_move = (i, j, k)
    return best_move
