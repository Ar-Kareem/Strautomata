
import random
import time

# Helper function to check lines for threats or opportunities
def check_line_status(line):
    """
    Analyzes a line (list of 4 integers).
    Returns:
        0: neutral
        1: opponent threat (3 opponent, 0 player) -> danger
        2: player opportunity (3 player, 0 opponent) -> win
        3: player block (2 player, 2 opponent) -> likely block/strategic
    """
    p_count = line.count(1)
    o_count = line.count(-1)
    empty_count = line.count(0)
    
    if p_count == 3 and empty_count == 1:
        return 2
    if o_count == 3 and empty_count == 1:
        return 1
    if p_count == 2 and o_count == 2 and empty_count == 0:
        return 3
    return 0

def get_winning_move(board, player):
    """Returns (r, c) if player can win immediately, else None."""
    target = 3 if player == 1 else 3
    # Check rows
    for r in range(4):
        row = board[r]
        if row.count(player) == 3 and row.count(0) == 1:
            c = row.index(0)
            return (r, c)
    # Check cols
    for c in range(4):
        col = [board[r][c] for r in range(4)]
        if col.count(player) == 3 and col.count(0) == 1:
            r = col.index(0)
            return (r, c)
    # Check diag 1 (top-left to bottom-right)
    diag1 = [board[i][i] for i in range(4)]
    if diag1.count(player) == 3 and diag1.count(0) == 1:
        idx = diag1.index(0)
        return (idx, idx)
    # Check diag 2 (top-right to bottom-left)
    diag2 = [board[i][3-i] for i in range(4)]
    if diag2.count(player) == 3 and diag2.count(0) == 1:
        idx = diag2.index(0)
        return (idx, 3-idx)
    return None

def evaluate_position(board, player):
    """
    Heuristic evaluation function.
    Positive favors 'player'.
    """
    opp = -1 if player == 1 else 1
    
    # Immediate win is max score
    if get_winning_move(board, player):
        return 100000
        
    # Prevent immediate loss
    if get_winning_move(board, opp):
        return -100000
        
    score = 0
    
    # Evaluate all lines
    lines = []
    # Rows
    for r in range(4):
        lines.append([board[r][c] for c in range(4)])
    # Cols
    for c in range(4):
        lines.append([board[r][c] for r in range(4)])
    # Diag 1
    lines.append([board[i][i] for i in range(4)])
    # Diag 2
    lines.append([board[i][3-i] for i in range(4)])
    
    for line in lines:
        p_count = line.count(player)
        o_count = line.count(opp)
        empty = line.count(0)
        
        if p_count == 2 and empty == 2:
            score += 10
        elif p_count == 1 and empty == 3:
            score += 1
            
        if o_count == 2 and empty == 2:
            score -= 10
        elif o_count == 1 and empty == 3:
            score -= 1
            
    # Center control (optional)
    # In 4x4, center is 2x2 block (1,1), (1,2), (2,1), (2,2)
    if player == 1:
        if board[1][1] == 1: score += 2
        if board[1][2] == 1: score += 2
        if board[2][1] == 1: score += 2
        if board[2][2] == 1: score += 2
    else:
        if board[1][1] == -1: score -= 2
        if board[1][2] == -1: score -= 2
        if board[2][1] == -1: score -= 2
        if board[2][2] == -1: score -= 2
        
    return score

def minimax(board, depth, alpha, beta, maximizing_player, player, start_time, time_limit):
    """
    Minimax with Alpha-Beta Pruning.
    Returns (value, move).
    """
    # Check time
    if time.time() - start_time > time_limit:
        return None, None
        
    opp = -1 if player == 1 else 1
    
    # Check terminal states
    win_p = get_winning_move(board, player)
    win_o = get_winning_move(board, opp)
    
    if win_p: return 100000, win_p
    if win_o: return -100000, win_o
    
    # Check draw
    empty_count = 0
    for r in range(4):
        empty_count += board[r].count(0)
    if empty_count == 0:
        return 0, None
        
    if depth == 0:
        return evaluate_position(board, player), None
        
    # Optimization: Order moves to improve pruning
    # Prefer center and corners
    moves = []
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                moves.append((r, c))
    
    # Sort moves heuristically
    def move_ordering(m):
        r, c = m
        # Center weight
        center_dist = abs(r-1.5) + abs(c-1.5)
        return center_dist
    
    moves.sort(key=move_ordering)
    
    best_move = moves[0] if moves else None
    
    if maximizing_player:
        max_eval = -float('inf')
        for r, c in moves:
            # Optimization: Check basic threats to avoid wasting time
            board[r][c] = player
            # If we can win, return immediately
            if get_winning_move(board, player):
                board[r][c] = 0
                return 100000, (r, c)
            
            eval_score, _ = minimax(board, depth-1, alpha, beta, False, player, start_time, time_limit)
            board[r][c] = 0
            
            if eval_score is None: return None, None # Timeout
            
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = (r, c)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval, best_move
    else:
        min_eval = float('inf')
        for r, c in moves:
            board[r][c] = opp
            if get_winning_move(board, opp):
                board[r][c] = 0
                return -100000, (r, c)
                
            eval_score, _ = minimax(board, depth-1, alpha, beta, True, player, start_time, time_limit)
            board[r][c] = 0
            
            if eval_score is None: return None, None
            
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = (r, c)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval, best_move

def policy(board: list[list[int]]) -> tuple[int, int]:
    # 1. Identify who we are
    # We can deduce player by counting moves if the game is ongoing
    p1_count = 0
    p2_count = 0
    for r in range(4):
        for c in range(4):
            if board[r][c] == 1: p1_count += 1
            elif board[r][c] == -1: p2_count += 1
    
    # If counts are equal, we are likely P1 (1). If P1 has one more, we are likely P2 (-1).
    # Note: In some simulators, the agent is always assigned '1'. 
    # However, to be robust against standard implementations where the prompt says "1 (you)", 
    # we will assume we are 1. 
    # BUT the prompt says: "1 (you), -1 (opponent)".
    # So we are definitely 1.
    my_player = 1
    opponent = -1
    
    # 2. Check for immediate winning move
    winning_move = get_winning_move(board, my_player)
    if winning_move:
        return winning_move
        
    # 3. Check for immediate opponent win and block it
    opponent_winning_move = get_winning_move(board, opponent)
    if opponent_winning_move:
        return opponent_winning_move
        
    # 4. Look for forks (creating two winning threats)
    # We will simulate a move and see if it creates multiple winning opportunities for us
    # This is expensive, so we do it only for a few good candidates
    moves = []
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                moves.append((r, c))
                
    # Prioritize strategic moves (Center > Corners > Edges)
    # Sort moves by center proximity
    moves.sort(key=lambda m: (abs(m[0]-1.5) + abs(m[1]-1.5)))
    
    # Find Fork
    for r, c in moves:
        board[r][c] = my_player
        # Count how many winning lines this move completes or creates
        # We can check by seeing if we have other "2 in a row" lines that are open
        win_threats = 0
        
        # Check rows/cols/diags involving (r,c)
        # Row
        row = board[r]
        if row.count(my_player) >= 2: win_threats += 1
        
        # Col
        col = [board[i][c] for i in range(4)]
        if col.count(my_player) >= 2: win_threats += 1
        
        # Diag 1
        if r == c:
            diag1 = [board[i][i] for i in range(4)]
            if diag1.count(my_player) >= 2: win_threats += 1
            
        # Diag 2
        if r == 3 - c:
            diag2 = [board[i][3-i] for i in range(4)]
            if diag2.count(my_player) >= 2: win_threats += 1
            
        board[r][c] = 0
        
        if win_threats >= 2:
            return (r, c)
            
    # 5. Heuristic Best Move with Depth-Limited Search (Minimax)
    # Time allocation: We have 1 second. We can likely do depth 4 or 5 on empty board.
    # As board fills, depth increases.
    start_time = time.time()
    time_limit = 0.9
    
    # Determine depth based on empty cells
    empty_count = sum(row.count(0) for row in board)
    
    # If few moves left, search deeper
    if empty_count > 10: depth = 3
    elif empty_count > 6: depth = 4
    elif empty_count > 2: depth = 6
    else: depth = 10
    
    _, best_move = minimax(board, depth, -float('inf'), float('inf'), True, my_player, start_time, time_limit)
    
    if best_move:
        return best_move
        
    # Fallback (should not happen unless board is full or timeout)
    if moves:
        return moves[0]
        
    return (0, 0)
