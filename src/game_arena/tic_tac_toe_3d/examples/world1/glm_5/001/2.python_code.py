
import sys

# Precompute all 49 winning lines (3 rows, 3 columns, 3 pillars, 6 diagonals per plane, 4 space diagonals)
LINES = []
# Rows (x varies)
for y in range(3):
    for z in range(3):
        LINES.append([(x, y, z) for x in range(3)])
# Columns (y varies)
for x in range(3):
    for z in range(3):
        LINES.append([(x, y, z) for y in range(3)])
# Pillars (z varies)
for x in range(3):
    for y in range(3):
        LINES.append([(x, y, z) for z in range(3)])
# XY Plane Diagonals
for z in range(3):
    LINES.append([(i, i, z) for i in range(3)])
    LINES.append([(i, 2 - i, z) for i in range(3)])
# XZ Plane Diagonals
for y in range(3):
    LINES.append([(i, y, i) for i in range(3)])
    LINES.append([(i, y, 2 - i) for i in range(3)])
# YZ Plane Diagonals
for x in range(3):
    LINES.append([(x, i, i) for i in range(3)])
    LINES.append([(x, i, 2 - i) for i in range(3)])
# Space Diagonals
LINES.append([(i, i, i) for i in range(3)])
LINES.append([(i, i, 2 - i) for i in range(3)])
LINES.append([(i, 2 - i, i) for i in range(3)])
LINES.append([(i, 2 - i, 2 - i) for i in range(3)])

# Map each cell to the lines it belongs to for faster win checking
LINES_PER_CELL = {}
for r in range(3):
    for c in range(3):
        for d in range(3):
            LINES_PER_CELL[(r, c, d)] = []
            
for line in LINES:
    for cell in line:
        LINES_PER_CELL[cell].append(line)

def check_win(board, last_move, player):
    """Checks if the player has won by checking only lines passing through last_move."""
    if last_move is None:
        return False
    for line in LINES_PER_CELL[last_move]:
        if all(board[x][y][z] == player for x, y, z in line):
            return True
    return False

def evaluate(board):
    """Heuristic evaluation of the board state."""
    score = 0
    for line in LINES:
        p1_count = 0
        p2_count = 0
        for x, y, z in line:
            val = board[x][y][z]
            if val == 1:
                p1_count += 1
            elif val == -1:
                p2_count += 1
        
        # If a line is mixed, it is worthless to both
        if p1_count > 0 and p2_count > 0:
            continue
            
        # Weight for lines with potential
        if p1_count == 2:
            score += 50
        elif p1_count == 1:
            score += 2
            
        if p2_count == 2:
            score -= 50
        elif p2_count == 1:
            score -= 2
            
    # Bonus for center control
    if board[1][1][1] == 1:
        score += 10
    elif board[1][1][1] == -1:
        score -= 10
        
    return score

def minimax(board, depth, alpha, beta, maximizing_player, last_move):
    """Minimax algorithm with alpha-beta pruning."""
    
    # Check terminal states based on the last move made
    if last_move:
        if maximizing_player: # Min just moved
            if check_win(board, last_move, -1):
                return -100000 - depth # Min wins
        else: # Max just moved
            if check_win(board, last_move, 1):
                return 100000 + depth # Max wins
    
    if depth == 0:
        return evaluate(board)
    
    # Generate moves
    moves = []
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] == 0:
                    moves.append((x, y, z))
    
    if not moves:
        return 0 # Draw

    # Move ordering: prioritize center, then corners, then edges
    def move_priority(m):
        x, y, z = m
        if x == 1 and y == 1 and z == 1: return 3 # Center
        if (x in [0,2] and y in [0,2] and z in [0,2]): return 2 # Corners
        return 1 # Edges
    
    moves.sort(key=move_priority, reverse=True)
    
    if maximizing_player:
        max_eval = -float('inf')
        for x, y, z in moves:
            board[x][y][z] = 1
            eval_val = minimax(board, depth - 1, alpha, beta, False, (x, y, z))
            board[x][y][z] = 0
            if eval_val > max_eval:
                max_eval = eval_val
            alpha = max(alpha, eval_val)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for x, y, z in moves:
            board[x][y][z] = -1
            eval_val = minimax(board, depth - 1, alpha, beta, True, (x, y, z))
            board[x][y][z] = 0
            if eval_val < min_eval:
                min_eval = eval_val
            beta = min(beta, eval_val)
            if beta <= alpha:
                break
        return min_eval

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Find all empty cells
    empty_cells = []
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    empty_cells.append((i, j, k))
    
    # 1. Opening move: Take center if available (strongest position)
    if len(empty_cells) == 27:
        return (1, 1, 1)
    
    # 2. Check for immediate win (depth 1)
    for r, c, d in empty_cells:
        board[r][c][d] = 1
        if check_win(board, (r, c, d), 1):
            board[r][c][d] = 0
            return (r, c, d)
        board[r][c][d] = 0
        
    # 3. Check for immediate block (opponent win)
    blocks = []
    for r, c, d in empty_cells:
        board[r][c][d] = -1
        if check_win(board, (r, c, d), -1):
            blocks.append((r, c, d))
        board[r][c][d] = 0
    
    if len(blocks) > 0:
        # If multiple threats, we might lose, but we must block one.
        # Prioritize blocking a cell that also gives us value? 
        # Simple fallback: just block the first one found.
        return blocks[0]

    # 4. Minimax Search
    # Adjust depth based on game progress
    if len(empty_cells) > 20:
        depth = 3
    elif len(empty_cells) > 15:
        depth = 4
    elif len(empty_cells) > 10:
        depth = 5
    else:
        depth = 6
        
    best_move = empty_cells[0]
    max_eval = -float('inf')
    
    # Order moves for root search as well
    def move_priority(m):
        x, y, z = m
        if x == 1 and y == 1 and z == 1: return 3
        if (x in [0,2] and y in [0,2] and z in [0,2]): return 2
        return 1
    empty_cells.sort(key=move_priority, reverse=True)
    
    for r, c, d in empty_cells:
        board[r][c][d] = 1
        # We are maximizing, next is minimizing (False)
        cur_eval = minimax(board, depth, -float('inf'), float('inf'), False, (r, c, d))
        board[r][c][d] = 0
        
        if cur_eval > max_eval:
            max_eval = cur_eval
            best_move = (r, c, d)
            
    return best_move
