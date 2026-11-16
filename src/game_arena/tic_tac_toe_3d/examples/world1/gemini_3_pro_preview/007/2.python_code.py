
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    Determines the next move for a 3x3x3 Tic Tac Toe game.
    Board: 3x3x3 list, 1=Self, -1=Opponent, 0=Empty.
    Returns: (x, y, z) tuple indicating the move.
    """
    
    # 1. Flatten the board for efficient logic
    # Mapping: index = 9*x + 3*y + z
    flat_board = [cell for layer in board for row in layer for cell in row]
    
    # Identify legal moves
    possible_moves = [i for i, v in enumerate(flat_board) if v == 0]
    
    # Fallback for full board (should not happen in standard flow)
    if not possible_moves:
        return (0, 0, 0)

    # Helper to convert index back to coordinates
    def to_coords(idx):
        return (idx // 9, (idx // 3) % 3, idx % 3)

    # 2. Precompute Winning Lines (Indices 0-26)
    # Total 49 lines in 3x3x3
    lines = []
    
    # Axis-aligned lines (3 axes * 9 lines = 27)
    # x-lines (varying x, fixed y, z)
    for y in range(3):
        for z in range(3):
            lines.append([9 * x + 3 * y + z for x in range(3)])
    # y-lines (varying y, fixed x, z)
    for x in range(3):
        for z in range(3):
            lines.append([9 * x + 3 * y + z for y in range(3)])
    # z-lines (varying z, fixed x, y)
    for x in range(3):
        for y in range(3):
            lines.append([9 * x + 3 * y + z for z in range(3)])
            
    # Face diagonals (18 lines)
    # Perpendicular to x-axis
    for x in range(3):
        base = 9 * x
        lines.append([base + 0, base + 4, base + 8])
        lines.append([base + 2, base + 4, base + 6])
    # Perpendicular to y-axis
    for y in range(3):
        # Indices: (x,y,z) -> (0,y,0), (1,y,1), (2,y,2) => 0+3y, 10+3y, 20+3y
        base = 3 * y
        lines.append([base + 0, base + 10, base + 20])
        lines.append([base + 2, base + 10, base + 18])
    # Perpendicular to z-axis
    for z in range(3):
        base = z
        lines.append([base + 0, base + 12, base + 24]) # 0, 13-1, 26-2? No. 0, 13 (center), 26 is space.
        # Logic: (0,0,z) -> z. (1,1,z) -> 9+3+z=12+z. (2,2,z) -> 18+6+z=24+z.
        lines.append([base + 6, base + 12, base + 18]) # (0,2,z) -> 6+z. (1,1,z)->12+z. (2,0,z)->18+z.

    # Space diagonals (4 lines)
    lines.append([0, 13, 26])
    lines.append([2, 13, 24])
    lines.append([6, 13, 20])
    lines.append([8, 13, 18])

    # 3. Check for Immediate Win or Block
    # Win?
    for m in possible_moves:
        flat_board[m] = 1
        for line in lines:
            if m in line and all(flat_board[i] == 1 for i in line):
                return to_coords(m)
        flat_board[m] = 0
        
    # Block? (Opponent has 2 in a row)
    for m in possible_moves:
        flat_board[m] = -1
        for line in lines:
            if m in line and all(flat_board[i] == -1 for i in line):
                return to_coords(m)
        flat_board[m] = 0

    # 4. Minimax Search (Depth 2: Self -> Opponent -> Heuristic)
    # Depth 2 is chosen for efficiency and is sufficient to prevent simple forks.
    
    # Priority Move Sorting: Center (13) > Corners > Others
    # This helps Alpha-Beta pruning find good branches early.
    center = {13}
    corners = {0, 2, 6, 8, 18, 20, 24, 26}
    
    def get_priority(m):
        if m in center: return 0
        if m in corners: return 1
        return 2

    sorted_moves = sorted(possible_moves, key=get_priority)

    # Heuristic Weights
    W_2_ME = 100       # Creating a threat
    W_1_ME = 10        # Potential
    W_2_OPP = -500     # Warning: Opponent has a threat (allowable if blocked next turn, but risky)
    W_1_OPP = -10
    
    def evaluate(board_state):
        score = 0
        for line in lines:
            me_cnt = 0
            opp_cnt = 0
            for i in line:
                v = board_state[i]
                if v == 1: me_cnt += 1
                elif v == -1: opp_cnt += 1
            
            if opp_cnt == 0:
                if me_cnt == 3: return 100000 # Won (should be caught earlier)
                elif me_cnt == 2: score += W_2_ME
                elif me_cnt == 1: score += W_1_ME
            elif me_cnt == 0:
                if opp_cnt == 3: return -100000
                elif opp_cnt == 2: score += W_2_OPP
                elif opp_cnt == 1: score += W_1_OPP
        return score

    best_val = -float('inf')
    best_move = sorted_moves[0]
    alpha = -float('inf')
    
    # Maximize self
    for m in sorted_moves:
        flat_board[m] = 1
        
        # Minimize opponent
        # We assume opponent responds optimally to minimize our score
        min_val = float('inf')
        opp_moves = [i for i, v in enumerate(flat_board) if v == 0]
        
        if not opp_moves:
            min_val = evaluate(flat_board)
        else:
            for om in opp_moves:
                flat_board[om] = -1
                
                # Leaf Evaluation
                val = evaluate(flat_board)
                
                flat_board[om] = 0 # Backtrack Opp
                
                if val < min_val:
                    min_val = val
                
                # Alpha Pruning
                # If the opponent can force a score 'min_val' which is worse than 
                # a score we can definitely get elsewhere ('alpha'), stop evaluating this move 'm'.
                if min_val <= alpha:
                    break
        
        flat_board[m] = 0 # Backtrack Self
        
        if min_val > best_val:
            best_val = min_val
            best_move = m
            alpha = max(alpha, best_val)
            
    return to_coords(best_move)
