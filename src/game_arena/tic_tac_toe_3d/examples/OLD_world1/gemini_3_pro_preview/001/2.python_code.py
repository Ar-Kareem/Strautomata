
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    Determines the next move for a 3x3x3 3D Tic Tac Toe game.
    Returns a tuple (z, y, x) indicating the chosen cell.
    Strategy:
    1. Check for immediate wins.
    2. Check for immediate forced blocks (opponent wins).
    3. Use Minimax (Depth 2) with Alpha-Beta pruning and heuristic evaluation
       to maximize winning chances and position strength.
    """
    
    # Board dimension
    N = 3
    
    # 1. Define all winning lines coordinates
    # A 3x3x3 board has 49 winning lines.
    lines = []
    
    # Axial lines (3 * 9 = 27)
    for i in range(N):
        for j in range(N):
            lines.append([(i, j, k) for k in range(N)]) # Varying x
            lines.append([(i, k, j) for k in range(N)]) # Varying y
            lines.append([(k, i, j) for k in range(N)]) # Varying z

    # Face diagonals (18 total)
    for k in range(N):
        # XY planes (z=k)
        lines.append([(k, 0, 0), (k, 1, 1), (k, 2, 2)])
        lines.append([(k, 0, 2), (k, 1, 1), (k, 2, 0)])
        # XZ planes (y=k)
        lines.append([(0, k, 0), (1, k, 1), (2, k, 2)])
        lines.append([(2, k, 0), (1, k, 1), (0, k, 2)])
        # YZ planes (x=k)
        lines.append([(0, 0, k), (1, 1, k), (2, 2, k)])
        lines.append([(2, 0, k), (1, 1, k), (0, 2, k)])

    # Space diagonals (4 total)
    lines.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
    lines.append([(2, 0, 0), (1, 1, 1), (0, 2, 2)])
    lines.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
    lines.append([(2, 2, 0), (1, 1, 1), (0, 0, 2)])

    # 2. Calculate static positional value map
    # (Cells involved in more winning lines are more valuable)
    pos_value = [[[0]*N for _ in range(N)] for _ in range(N)]
    for z in range(N):
        for y in range(N):
            for x in range(N):
                count = 0
                for ln in lines:
                    if (z, y, x) in ln:
                        count += 1
                pos_value[z][y][x] = count

    # 3. Find valid moves
    candidates = []
    for z in range(N):
        for y in range(N):
            for x in range(N):
                if board[z][y][x] == 0:
                    candidates.append((z, y, x))

    # Optimization: If center is empty, take it (strongest opening)
    if (1, 1, 1) in candidates:
        return (1, 1, 1)
    
    # Optimization: If only one move left, take it
    if len(candidates) == 1:
        return candidates[0]

    # 4. Immediate Critical Check (Win or Block)
    # Check if we can win immediately
    for (z, y, x) in candidates:
        board[z][y][x] = 1
        winning_move = False
        for ln in lines:
            if (z, y, x) in ln:
                if all(board[cz][cy][cx] == 1 for (cz, cy, cx) in ln):
                    winning_move = True
                    break
        board[z][y][x] = 0 # Backtrack
        if winning_move:
            return (z, y, x)
            
    # Check if we must block opponent immediately
    blocking_moves = []
    for (z, y, x) in candidates:
        board[z][y][x] = -1
        blocking_move = False
        for ln in lines:
            if (z, y, x) in ln:
                if all(board[cz][cy][cx] == -1 for (cz, cy, cx) in ln):
                    blocking_move = True
                    break
        board[z][y][x] = 0 # Backtrack
        if blocking_move:
            blocking_moves.append((z, y, x))
    
    if blocking_moves:
        # If opponent has multiple wins, we are likely lost, but must block one.
        return blocking_moves[0]

    # 5. Minimax with Alpha-Beta Pruning (Depth 2)
    
    def evaluate():
        """Heuristic scoring of the board state."""
        score = 0
        for ln in lines:
            # Count markers in this line
            vals = [board[z][y][x] for (z, y, x) in ln]
            my_count = vals.count(1)
            op_count = vals.count(-1)
            
            # Winning statuses
            if my_count == 3: return 1000000
            if op_count == 3: return -1000000
            
            # Threats (2 markers, 1 empty)
            if my_count == 2 and op_count == 0:
                score += 1000
            elif op_count == 2 and my_count == 0:
                score -= 1000
            
            # Potentials (1 marker, 2 empty)
            elif my_count == 1 and op_count == 0:
                score += 10
            elif op_count == 1 and my_count == 0:
                score -= 10
        
        # Add positional bias to differentiate otherwise equal moves
        for z in range(N):
            for y in range(N):
                for x in range(N):
                    v = board[z][y][x]
                    if v == 1: score += pos_value[z][y][x]
                    elif v == -1: score -= pos_value[z][y][x]
        
        return score

    def minimax(depth, alpha, beta, is_maximizing):
        current_score = evaluate()
        
        # Terminal states (Win/Loss specific thresholds)
        if abs(current_score) > 500000:
            return current_score
        
        if depth == 0:
            return current_score
            
        # Generate moves
        moves = []
        for z in range(N):
            for y in range(N):
                for x in range(N):
                    if board[z][y][x] == 0:
                        moves.append((z, y, x))
        
        if is_maximizing:
            max_eval = -float('inf')
            for (z, y, x) in moves:
                board[z][y][x] = 1
                eval_val = minimax(depth - 1, alpha, beta, False)
                board[z][y][x] = 0
                max_eval = max(max_eval, eval_val)
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for (z, y, x) in moves:
                board[z][y][x] = -1
                eval_val = minimax(depth - 1, alpha, beta, True)
                board[z][y][x] = 0
                min_eval = min(min_eval, eval_val)
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break
            return min_eval

    # Sort candidates by positional value for better pruning optimization
    candidates.sort(key=lambda m: pos_value[m[0]][m[1]][m[2]], reverse=True)
    
    best_val = -float('inf')
    best_move = candidates[0]
    alpha = -float('inf')
    beta = float('inf')
    
    # Root Maximize Step
    # We look 1 step ahead recursively (Me -> Opponent -> Score), effectively depth 2
    for (z, y, x) in candidates:
        board[z][y][x] = 1
        val = minimax(1, alpha, beta, False)
        board[z][y][x] = 0
        
        if val > best_val:
            best_val = val
            best_move = (z, y, x)
        
        alpha = max(alpha, val)
        
    return best_move
