
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    Determines the next move for a 3x3x3 Tic Tac Toe game.
    
    args:
        board: A 3x3x3 list of lists (int).
               0 = Empty, 1 = You, -1 = Opponent.
               
    returns:
        (i, j, k): Tuple of indices representing the move coordinates.
    """
    
    N = 3

    # Helper to access board value by tuple coordinate
    def get_val(c):
        return board[c[0]][c[1]][c[2]]

    # --- 1. Precompute all 49 Winning Lines ---
    # A line is represented as a list of 3 coordinate tuples [(x,y,z), ...]
    lines = []

    # 1a. Orthogonal Lines (along x, y, z axes) - 27 lines
    # Along k (3rd dim)
    for i in range(N):
        for j in range(N):
            lines.append([(i, j, k) for k in range(N)])
    # Along j (2nd dim)
    for i in range(N):
        for k in range(N):
            lines.append([(i, j, k) for j in range(N)])
    # Along i (1st dim)
    for j in range(N):
        for k in range(N):
            lines.append([(i, j, k) for i in range(N)])

    # 1b. Face Diagonals (Diagonals on 2D planes) - 18 lines
    # Planes i=0..2 (Fixed first dim)
    for i in range(N):
        lines.append([(i, k, k) for k in range(N)])
        lines.append([(i, k, N-1-k) for k in range(N)])
    # Planes j=0..2 (Fixed second dim)
    for j in range(N):
        lines.append([(k, j, k) for k in range(N)])
        lines.append([(k, j, N-1-k) for k in range(N)])
    # Planes k=0..2 (Fixed third dim)
    for k in range(N):
        lines.append([(p, p, k) for p in range(N)])
        lines.append([(p, N-1-p, k) for p in range(N)])

    # 1c. Space Diagonals (Through the cube center) - 4 lines
    lines.append([(p, p, p) for p in range(N)])
    lines.append([(p, p, N-1-p) for p in range(N)])
    lines.append([(p, N-1-p, p) for p in range(N)])
    lines.append([(p, N-1-p, N-1-p) for p in range(N)])

    # --- 2. Identify Empty Cells ---
    empty_cells = []
    for i in range(N):
        for j in range(N):
            for k in range(N):
                if board[i][j][k] == 0:
                    empty_cells.append((i, j, k))

    # Fallback if board is full (should not happen in game loop)
    if not empty_cells:
        return (0, 0, 0)

    # --- 3. Strategy Execution ---

    # Priority 1: WIN (Complete a line of two 1s)
    for c in empty_cells:
        for line in lines:
            if c in line:
                # Check other 2 cells in this line
                values = [get_val(p) for p in line if p != c]
                if values.count(1) == 2:
                    return c

    # Priority 2: BLOCK (Block opponent's line of two -1s)
    forced_blocks = []
    for c in empty_cells:
        for line in lines:
            if c in line:
                values = [get_val(p) for p in line if p != c]
                if values.count(-1) == 2:
                    forced_blocks.append(c)
                    break # Identify necessary block for this cell
    
    # If blocks are found, analyze best blocking position (if multiple threats, we likely lose anyway)
    if forced_blocks:
        best_block = forced_blocks[0]
        best_score = -float('inf')
        for c in forced_blocks:
            # Reuse heuristic scoring to pick the block that gives us best position
            score = 0
            if c == (1, 1, 1): score += 5 # Center bonus
            for line in lines:
                if c in line:
                    vals = [get_val(p) for p in line if p != c]
                    # If line is open for us, add value
                    if vals.count(-1) == 0:
                        score += (5 if vals.count(1) == 1 else 1)
            if score > best_score:
                best_score = score
                best_block = c
        return best_block

    # Priority 3: CREATE FORK (Create >=2 lines with 2 of my pieces)
    for c in empty_cells:
        winning_lines_created = 0
        for line in lines:
            if c in line:
                vals = [get_val(p) for p in line if p != c]
                # If I place here, line becomes [1, 1, 0] (assuming previous state was [1, 0, 0])
                if vals.count(1) == 1 and vals.count(-1) == 0:
                    winning_lines_created += 1
        if winning_lines_created >= 2:
            return c

    # Priority 4: BLOCK FORK (Prevent opponent from creating a fork)
    fork_blocks = []
    for c in empty_cells:
        opp_lines_created = 0
        for line in lines:
            if c in line:
                vals = [get_val(p) for p in line if p != c]
                if vals.count(-1) == 1 and vals.count(1) == 0:
                    opp_lines_created += 1
        if opp_lines_created >= 2:
            fork_blocks.append(c)
            
    if fork_blocks:
        # Pick best block via heuristic
        best_block = fork_blocks[0]
        best_score = -float('inf')
        for c in fork_blocks:
            score = 0
            if c == (1, 1, 1): score += 5
            for line in lines:
                if c in line:
                    vals = [get_val(p) for p in line if p != c]
                    if vals.count(-1) == 0:
                        score += (5 if vals.count(1) == 1 else 1)
            if score > best_score:
                best_score = score
                best_block = c
        return best_block

    # Priority 5: HEURISTIC MOVE
    # Score cells based on strategic value
    best_move = empty_cells[0]
    best_score = -float('inf')

    for c in empty_cells:
        score = 0.0
        
        # A. Position Value
        if c == (1, 1, 1): 
            score += 20.0 # Center is critical in 3D TTT
        elif sum(x in [0, 2] for x in c) == 3:
            score += 2.0 # Corners are decent

        # B. Line Potential
        for line in lines:
            if c in line:
                vals = [get_val(p) for p in line if p != c]
                my_count = vals.count(1)
                opp_count = vals.count(-1)
                
                if opp_count == 0:
                    # Offensive value
                    if my_count == 1: 
                        score += 10.0 # Extends a line to 2 (threat setup)
                    elif my_count == 0: 
                        score += 1.0 # Starts a new line
                elif my_count == 0:
                    # Defensive value (blocking potential growth)
                    if opp_count == 1:
                        score += 5.0 # Blocks opponent from creating a 2-line
        
        if score > best_score:
            best_score = score
            best_move = c

    return best_move
