
def policy(board: list[list[int]]) -> tuple[int, int]:
    import math

    ME = 1
    OPP = -1
    EMPTY = 0
    N = 4
    
    # Precompute lines (rows, cols, diags) for fast access
    lines = []
    # Rows
    for r in range(N):
        lines.append([(r, c) for c in range(N)])
    # Cols
    for c in range(N):
        lines.append([(r, c) for r in range(N)])
    # Diagonals
    lines.append([(i, i) for i in range(N)])
    lines.append([(i, N - 1 - i) for i in range(N)])

    def get_valid_moves(b):
        return [(r, c) for r in range(N) for c in range(N) if b[r][c] == EMPTY]

    def evaluate_line(line_vals):
        count_me = line_vals.count(ME)
        count_opp = line_vals.count(OPP)

        if count_me == 4:
            return 100000
        if count_opp == 4:
            return -100000
        
        # Heuristic scoring
        if count_opp == 0:
            if count_me == 3: return 1000
            if count_me == 2: return 100
            if count_me == 1: return 10
        elif count_me == 0:
            if count_opp == 3: return -1000
            if count_opp == 2: return -100
            if count_opp == 1: return -10
            
        return 0

    def evaluate(b):
        score = 0
        for line in lines:
            vals = [b[r][c] for r, c in line]
            s = evaluate_line(vals)
            # If terminal state found in eval, return immediately heavily weighted
            if abs(s) >= 100000:
                return s
            score += s
        return score

    def is_game_over(b):
        # Returns (True/False, winner or 0)
        # Check lines for win
        empty_spots = 0
        for line in lines:
            vals = [b[r][c] for r, c in line]
            if all(v == ME for v in vals): return True, ME
            if all(v == OPP for v in vals): return True, OPP
            if EMPTY in vals: empty_spots += 1
        
        if empty_spots == 0:
            return True, 0 # Draw
        return False, 0

    def minimax(b, depth, alpha, beta, is_maximizing):
        game_over, winner = is_game_over(b)
        if game_over:
            if winner == ME: return 1000000 + depth # Prefer faster wins
            elif winner == OPP: return -1000000 - depth # Prefer slower losses
            else: return 0

        if depth == 0:
            return evaluate(b)

        valid_moves = get_valid_moves(b)
        
        # Move ordering: prioritize center
        center_priority = []
        outer = []
        for r, c in valid_moves:
            if 1 <= r <= 2 and 1 <= c <= 2:
                center_priority.append((r,c))
            else:
                outer.append((r,c))
        sorted_moves = center_priority + outer

        if is_maximizing:
            max_eval = -math.inf
            for r, c in sorted_moves:
                b[r][c] = ME
                eval_val = minimax(b, depth - 1, alpha, beta, False)
                b[r][c] = EMPTY
                max_eval = max(max_eval, eval_val)
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = math.inf
            for r, c in sorted_moves:
                b[r][c] = OPP
                eval_val = minimax(b, depth - 1, alpha, beta, True)
                b[r][c] = EMPTY
                min_eval = min(min_eval, eval_val)
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break
            return min_eval

    # 1. Quick check for immediate win
    moves = get_valid_moves(board)
    if not moves: return (0,0) # Should not happen

    # Win immediately?
    for r, c in moves:
        board[r][c] = ME
        over, winner = is_game_over(board)
        board[r][c] = EMPTY
        if over and winner == ME:
            return (r, c)

    # Block immediate loss?
    for r, c in moves:
        board[r][c] = OPP
        over, winner = is_game_over(board)
        board[r][c] = EMPTY
        if over and winner == OPP:
            return (r, c)

    # 2. Run Minimax
    best_score = -math.inf
    best_move = moves[0]
    
    # Depth 3 is generally safe for Python in 1s for 4x4
    depth = 3

    # Optimization: If very early game, pick center
    count_pieces = sum(row.count(ME) + row.count(OPP) for row in board)
    if count_pieces == 0: return (1, 1)
    if count_pieces == 1 and board[1][1] == EMPTY: return (1, 1)

    alpha = -math.inf
    beta = math.inf

    for r, c in moves:
        board[r][c] = ME
        score = minimax(board, depth - 1, alpha, beta, False)
        board[r][c] = EMPTY
        
        if score > best_score:
            best_score = score
            best_move = (r, c)
        
        alpha = max(alpha, score)
    
    return best_move
