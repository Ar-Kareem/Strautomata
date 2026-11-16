
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Constants
    SIZE = 3
    ME = 1
    OPP = -1
    
    # Flatten the board for easier processing
    # Map (z, y, x) -> index 0..26
    # z is dim 0, y is dim 1, x is dim 2
    flat_board = []
    for z in range(SIZE):
        for y in range(SIZE):
            for x in range(SIZE):
                flat_board.append(board[z][y][x])
    
    # Helper to convert linear index back to (z, y, x) tuple
    def to_coords(idx):
        z = idx // 9
        y = (idx % 9) // 3
        x = idx % 3
        return (z, y, x)

    # Helper to convert coords to linear index
    def to_index(z, y, x):
        return z * 9 + y * 3 + x

    # 1. Precompute all winning lines (indices)
    # A line is formed by 3 collinear cells.
    # We scan all cells and all 13 unique directions.
    lines = set()
    directions = [
        (dz, dy, dx)
        for dz in (-1, 0, 1)
        for dy in (-1, 0, 1)
        for dx in (-1, 0, 1)
        if not (dz == 0 and dy == 0 and dx == 0)
    ]
    
    for z in range(SIZE):
        for y in range(SIZE):
            for x in range(SIZE):
                for dz, dy, dx in directions:
                    # Check if a line of length 3 exists starting here
                    if 0 <= z + 2*dz < SIZE and \
                       0 <= y + 2*dy < SIZE and \
                       0 <= x + 2*dx < SIZE:
                        p1 = to_index(z, y, x)
                        p2 = to_index(z + dz, y + dy, x + dx)
                        p3 = to_index(z + 2*dz, y + 2*dy, x + 2*dx)
                        # Store as sorted tuple to ensure uniqueness
                        lines.add(tuple(sorted((p1, p2, p3))))
    
    lines = list(lines) # 49 lines for 3x3x3 specific case

    # Identify empty cells (candidates)
    empties = [i for i, val in enumerate(flat_board) if val == 0]
    
    # 2. Heuristics and Moves
    
    # Optimization: First move
    if len(empties) == 27:
        # Take center
        return (1, 1, 1)
    
    # Helper to find if a player can complete a line immediately
    def find_winning_move_idx(bd, player):
        for line in lines:
            # Check content of the line
            values = [bd[i] for i in line]
            if values.count(player) == 2 and values.count(0) == 1:
                # Find the index of the 0
                for idx in line:
                    if bd[idx] == 0:
                        return idx
        return None

    # Priority 1: Take Immediate Win
    win_idx = find_winning_move_idx(flat_board, ME)
    if win_idx is not None:
        return to_coords(win_idx)
        
    # Priority 2: Block Immediate Loss
    block_idx = find_winning_move_idx(flat_board, OPP)
    if block_idx is not None:
        return to_coords(block_idx)
        
    # Priority 3: 2-ply Minimax (Max Me, Min Opp)
    # We want to choose a move that maximizes the state value after opponent's best response.
    # This depth allows finding moves that create Forks (double threats).
    
    # Static board evaluation function
    # Higher score = better for ME
    def evaluate(bd):
        score = 0
        for line in lines:
            line_vals = [bd[i] for i in line]
            c_me = line_vals.count(ME)
            c_opp = line_vals.count(OPP)
            
            # If line is mixed, it's blocked (value 0 usually, or small).
            if c_me > 0 and c_opp > 0:
                continue
            
            if c_me == 3: return 100000  # Me Win
            if c_opp == 3: return -100000 # Me Loss
            
            # Potentials
            # Reward having potential lines. Strong reward for 2-in-row (threats).
            # Note: This is a static eval of a leaf node.
            # We must incentivize Forks. A fork results in two lines of score 100. Sum = 200.
            if c_me == 2: score += 100
            elif c_me == 1: score += 10
            
            if c_opp == 2: score -= 100
            elif c_opp == 1: score -= 10
            
        return score

    best_score = -float('inf')
    best_move = empties[0]
    
    for m in empties:
        # Execute Move (Me)
        flat_board[m] = ME
        
        # Now find best response for opponent (Minimizer)
        # Scan Opponent's moves
        current_branch_min = float('inf')
        
        candidates_opp = [e for e in empties if e != m]
        
        # Optimization: Check if Opponent has a winning move immediately (Block/Win Logic for Opp)
        # If Opp can win, he will -> Value is -100000.
        opp_wins_immediately = False
        for line in lines:
            vals = [flat_board[i] for i in line]
            if vals.count(OPP) == 2 and vals.count(0) == 1:
                current_branch_min = -100000
                opp_wins_immediately = True
                break
        
        if not opp_wins_immediately:
            if not candidates_opp:
                # Board full
                current_branch_min = evaluate(flat_board)
            else:
                # Check all opponent moves
                for om in candidates_opp:
                    flat_board[om] = OPP
                    val = evaluate(flat_board)
                    if val < current_branch_min:
                        current_branch_min = val
                    flat_board[om] = 0
        
        # Backtrack Move (Me)
        flat_board[m] = 0
        
        if current_branch_min > best_score:
            best_score = current_branch_min
            best_move = m
            
    return to_coords(best_move)
