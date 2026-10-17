
def policy(state, role):
    # Parse state
    phase = None
    board = {}  # (q, r, c) -> color, 1-indexed
    
    for prop in state:
        if prop[0] == "phase":
            phase = prop[1]
        elif prop[0] == "cellholds":
            q, r, c = int(prop[1]), int(prop[2]), int(prop[3])
            color = prop[4]
            board[(q, r, c)] = color
    
    if phase == "place":
        return choose_place(board, role)
    else:
        return choose_rotate(board, role)

def choose_place(board, role):
    # Find all empty cells
    empty = []
    for q in range(1, 5):
        for r in range(1, 4):
            for c in range(1, 4):
                if (q, r, c) not in board:
                    empty.append((q, r, c))
    
    if not empty:
        return "place(1,1,1)"  # Should not happen
    
    best_score = -float('inf')
    best_cell = empty[0]
    
    for cell in empty:
        q, r, c = cell
        # Simulate placing
        new_board = dict(board)
        new_board[cell] = role
        
        # Evaluate after best rotation (since we control the next rotation)
        best_rot_score = -float('inf')
        for rot_q in range(1, 5):
            for direction in ["clockwise", "counterclockwise"]:
                rot_board = simulate_rotate(new_board, rot_q, direction)
                score = evaluate(rot_board, role)
                if score > best_rot_score:
                    best_rot_score = score
        
        if best_rot_score > best_score:
            best_score = best_rot_score
            best_cell = cell
    
    q, r, c = best_cell
    return f"place({q},{r},{c})"

def choose_rotate(board, role):
    best_score = -float('inf')
    best_move = (1, "clockwise")
    
    for q in range(1, 5):
        for direction in ["clockwise", "counterclockwise"]:
            new_board = simulate_rotate(board, q, direction)
            score = evaluate(new_board, role)
            
            # Immediate win priority
            if has_five(new_board, role):
                return f"rotate({q},{direction})"
            
            if score > best_score:
                best_score = score
                best_move = (q, direction)
    
    q, direction = best_move
    return f"rotate({q},{direction})"

def simulate_rotate(board, quadrant, direction):
    """Simulate rotating a quadrant. Returns new board dict."""
    new_board = dict(board)
    q = quadrant
    
    # Find cells in this quadrant
    cells_to_rotate = []
    for r in range(1, 4):
        for c in range(1, 4):
            if (q, r, c) in board:
                cells_to_rotate.append((r, c))
    
    # Remove old positions
    for r, c in cells_to_rotate:
        del new_board[(q, r, c)]
    
    # Add at new positions
    for r, c in cells_to_rotate:
        color = board[(q, r, c)]
        if direction == "clockwise":
            # (r, c) -> (c, 4-r)
            new_r, new_c = c, 4 - r
        else:  # counterclockwise
            # (r, c) -> (4-c, r)
            new_r, new_c = 4 - c, r
        new_board[(q, new_r, new_c)] = color
    
    return new_board

def to_global(board):
    """Convert quadrant-based board to 6x6 grid (0-indexed)."""
    grid = [[None for _ in range(6)] for _ in range(6)]
    
    for (q, r, c), color in board.items():
        # Convert to 0-indexed
        q0, r0, c0 = q - 1, r - 1, c - 1
        
        if q0 == 0:      # Q1: top-left
            gr, gc = r0, c0
        elif q0 == 1:    # Q2: top-right
            gr, gc = r0, c0 + 3
        elif q0 == 2:    # Q3: bottom-left
            gr, gc = r0 + 3, c0
        else:            # Q4: bottom-right
            gr, gc = r0 + 3, c0 + 3
        
        grid[gr][gc] = color
    
    return grid

# Precompute all lines of 5 in a 6x6 grid
LINES = []
# Horizontal
for r in range(6):
    for c in range(2):
        line = [(r, c + i) for i in range(5)]
        LINES.append(line)
# Vertical
for c in range(6):
    for r in range(2):
        line = [(r + i, c) for i in range(5)]
        LINES.append(line)
# Diagonal down-right
for r in range(2):
    for c in range(2):
        line = [(r + i, c + i) for i in range(5)]
        LINES.append(line)
# Diagonal down-left
for r in range(2):
    for c in range(4, 6):
        line = [(r + i, c - i) for i in range(5)]
        LINES.append(line)

def has_five(board, role):
    """Check if role has 5 in a row."""
    grid = to_global(board)
    for line in LINES:
        cells = [grid[r][c] for r, c in line]
        if all(cell == role for cell in cells):
            return True
    return False

def evaluate(board, role):
    """Heuristic evaluation of board state."""
    grid = to_global(board)
    opp = "black" if role == "red" else "red"
    score = 0
    
    for line in LINES:
        cells = [grid[r][c] for r, c in line]
        my_count = sum(1 for cell in cells if cell == role)
        op_count = sum(1 for cell in cells if cell == opp)
        
        if my_count > 0 and op_count == 0:
            if my_count == 5:
                score += 100000
            elif my_count == 4:
                score += 1000
            elif my_count == 3:
                score += 100
            elif my_count == 2:
                score += 10
            else:
                score += 1
        elif op_count > 0 and my_count == 0:
            if op_count == 5:
                score -= 100000
            elif op_count == 4:
                score -= 1000
            elif op_count == 3:
                score -= 100
            elif op_count == 2:
                score -= 10
            else:
                score -= 1
    
    return score
