
def policy(board: list[list[int]]) -> tuple[int, int]:
    import time
    import sys

    # Constants
    PLAYER = 1
    OPPONENT = -1
    EMPTY = 0
    SIZE = 4
    WIN_LEN = 4
    
    # Time limit buffer (seconds)
    TIME_LIMIT = 0.8 

    def check_win(b, player):
        # Check Rows
        for r in range(SIZE):
            for c in range(SIZE - WIN_LEN + 1):
                if all(b[r][c+i] == player for i in range(WIN_LEN)):
                    return True
        # Check Cols
        for c in range(SIZE):
            for r in range(SIZE - WIN_LEN + 1):
                if all(b[r+i][c] == player for i in range(WIN_LEN)):
                    return True
        # Check Diagonals
        for r in range(SIZE - WIN_LEN + 1):
            for c in range(SIZE - WIN_LEN + 1):
                if all(b[r+i][c+i] == player for i in range(WIN_LEN)):
                    return True
                if all(b[r+WIN_LEN-1-i][c+i] == player for i in range(WIN_LEN)):
                    return True
        return False

    def evaluate_board(b):
        # Heuristic evaluation based on lines
        score = 0
        
        # Helper to score a sequence
        def score_seq(seq):
            p_count = seq.count(PLAYER)
            o_count = seq.count(OPPONENT)
            if p_count > 0 and o_count > 0: return 0 # Blocked line
            if p_count == 4: return 100000 # Win (should be caught earlier)
            if o_count == 4: return -100000 # Loss (should be caught earlier)
            
            val = 0
            if p_count == 3: val += 1000
            elif p_count == 2: val += 100
            elif p_count == 1: val += 10
            
            if o_count == 3: val -= 1200 # Slightly stronger threat
            elif o_count == 2: val -= 120
            elif o_count == 1: val -= 12
            return val

        # Rows
        for r in range(SIZE):
            for c in range(SIZE - WIN_LEN + 1):
                score += score_seq([b[r][c+i] for i in range(WIN_LEN)])
        # Cols
        for c in range(SIZE):
            for r in range(SIZE - WIN_LEN + 1):
                score += score_seq([b[r+i][c] for i in range(WIN_LEN)])
        # Diagonals
        for r in range(SIZE - WIN_LEN + 1):
            for c in range(SIZE - WIN_LEN + 1):
                score += score_seq([b[r+i][c+i] for i in range(WIN_LEN)])
                score += score_seq([b[r+WIN_LEN-1-i][c+i] for i in range(WIN_LEN)])
        return score

    def get_valid_moves(b):
        moves = []
        for r in range(SIZE):
            for c in range(SIZE):
                if b[r][c] == EMPTY:
                    # Move ordering priority
                    priority = 0
                    # Center priority (2x2 block)
                    if 1 <= r <= 2 and 1 <= c <= 2: priority = 3
                    # Corner priority
                    elif (r == 0 or r == 3) and (c == 0 or c == 3): priority = 2
                    else: priority = 1
                    moves.append((priority, r, c))
        # Sort by priority descending
        moves.sort(key=lambda x: x[0], reverse=True)
        return [(r, c) for _, r, c in moves]

    # --- Step 1: Immediate Win/Block (O(1) Checks) ---
    
    # Check for immediate win
    for r, c in get_valid_moves(board):
        board[r][c] = PLAYER
        if check_win(board, PLAYER):
            board[r][c] = EMPTY
            return (r, c)
        board[r][c] = EMPTY

    # Check for immediate opponent threat (block)
    for r, c in get_valid_moves(board):
        board[r][c] = OPPONENT
        if check_win(board, OPPONENT):
            board[r][c] = EMPTY
            return (r, c)
        board[r][c] = EMPTY

    # --- Step 2: Minimax with Iterative Deepening ---

    start_time = time.time()
    best_move = get_valid_moves(board)[0] # Default to best ordered move
    max_depth = 1
    depth_reached = 0

    def minimax(b, depth, alpha, beta, is_maximizing, start_t):
        # Timeout check
        if time.time() - start_t > TIME_LIMIT:
            raise TimeoutError()

        if depth == 0:
            return evaluate_board(b), None

        valid_moves = get_valid_moves(b)
        
        # Terminal state check (draw or win already happened)
        if not valid_moves:
            return evaluate_board(b), None

        # Optimization: If only one move, don't waste time
        if len(valid_moves) == 1:
            return 0, valid_moves[0]

        if is_maximizing:
            max_eval = -float('inf')
            best_m = valid_moves[0]
            for r, c in valid_moves:
                b[r][c] = PLAYER
                if check_win(b, PLAYER):
                    b[r][c] = EMPTY
                    return 100000 + depth, (r, c) # Prefer faster wins
                
                eval_score, _ = minimax(b, depth - 1, alpha, beta, False, start_t)
                b[r][c] = EMPTY
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_m = (r, c)
                
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval, best_m
        else:
            min_eval = float('inf')
            best_m = valid_moves[0]
            for r, c in valid_moves:
                b[r][c] = OPPONENT
                if check_win(b, OPPONENT):
                    b[r][c] = EMPTY
                    return -100000 - depth, (r, c) # Prefer slower opponent wins
                
                eval_score, _ = minimax(b, depth - 1, alpha, beta, True, start_t)
                b[r][c] = EMPTY
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_m = (r, c)
                
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval, best_m

    try:
        while True:
            # Check if we have time for another iteration
            if time.time() - start_time > TIME_LIMIT * 0.5: # Buffer
                break
            
            score, move = minimax(board, max_depth, -float('inf'), float('inf'), True, start_time)
            
            # If we finished a depth iteration successfully, update best_move
            if move:
                best_move = move
                depth_reached = max_depth
            
            # If score is extremely high/low, we found a forced win/loss, stop searching
            if score > 50000 or score < -50000:
                break
                
            # Stop increasing depth if we are hitting 6 (too expensive usually)
            if max_depth >= 5: 
                break
                
            max_depth += 1
            
    except TimeoutError:
        pass # Return best move found so far

    return best_move
