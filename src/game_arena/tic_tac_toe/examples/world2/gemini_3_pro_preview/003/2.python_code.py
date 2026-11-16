
import time

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Determines the best move for a 4x4 Tic Tac Toe game.
    AI is 1, Opponent is -1. 
    """
    ME = 1
    OPPONENT = -1
    EMPTY = 0
    N = 4
    TIME_LIMIT = 0.95  # Slightly under 1s buffer
    
    start_time = time.time()
    
    # Precompute lines (rows, cols, diags) indices for efficiency? 
    # For simplicity in logic, we'll iterate or generate them.
    # Actually, flattening the board helps with performance.
    
    def get_lines(b):
        # Rows
        for r in range(N):
            yield b[r]
        # Cols
        for c in range(N):
            yield [b[r][c] for r in range(N)]
        # Diagonals
        yield [b[i][i] for i in range(N)]
        yield [b[i][N-1-i] for i in range(N)]

    def evaluate(b):
        score = 0
        # Check all 10 lines
        for line in get_lines(b):
            count_me = line.count(ME)
            count_opp = line.count(OPPONENT)
            
            # If line has both, it's dead, score 0 (lines with both contribute nothing to potential win)
            if count_me > 0 and count_opp > 0:
                continue
            
            if count_me > 0:
                # Award points for progress
                if count_me == 4: return 1000000
                score += (10 ** count_me)
            elif count_opp > 0:
                # Subtract points for opponent progress
                if count_opp == 4: return -1000000
                score -= (10 ** count_opp)
                
        return score

    def get_possible_moves(b):
        # Order moves: Center first, then others to improve pruning
        moves = []
        center_indices = [(1,1), (1,2), (2,1), (2,2)]
        
        for r in range(N):
            for c in range(N):
                if b[r][c] == EMPTY:
                    if (r, c) in center_indices:
                        moves.insert(0, (r, c))
                    else:
                        moves.append((r, c))
        return moves

    def minimax(b, depth, alpha, beta, maximizing_player):
        # Check time
        if time.time() - start_time > TIME_LIMIT:
            raise TimeoutError
            
        # Check terminal by heuristic score for wins
        # (Optimized: usually we check is_terminal, but evaluate handles win scores)
        current_score = evaluate(b)
        if abs(current_score) > 100000: # Win detected
            return current_score
        
        if depth == 0:
            return current_score
        
        avail_moves = get_possible_moves(b)
        if not avail_moves:
            return 0 # Draw

        if maximizing_player:
            max_eval = -float('inf')
            for r, c in avail_moves:
                b[r][c] = ME
                try:
                    eval_val = minimax(b, depth - 1, alpha, beta, False)
                except TimeoutError:
                    b[r][c] = EMPTY
                    raise # Propagate up
                b[r][c] = EMPTY
                max_eval = max(max_eval, eval_val)
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for r, c in avail_moves:
                b[r][c] = OPPONENT
                try:
                    eval_val = minimax(b, depth - 1, alpha, beta, True)
                except TimeoutError:
                    b[r][c] = EMPTY
                    raise
                b[r][c] = EMPTY
                min_eval = min(min_eval, eval_val)
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break
            return min_eval

    # --- Main Logic ---
    possible_moves = get_possible_moves(board)
    if not possible_moves:
        return (0, 0) # Should not happen unless board full
    
    # If first move of game, take center
    if len(possible_moves) == 16:
        return (1, 1)

    best_move = possible_moves[0]
    
    # Iterative Deepening
    try:
        for d in range(1, 10): # 10 is arbitrary max depth, time will cut it short
            score = -float('inf')
            alpha = -float('inf')
            beta = float('inf')
            
            # Optimize: sort moves based on previous iteration score? 
            # For simplicity, we stick to heuristic order.
            
            current_best_in_depth = best_move
            
            for r, c in possible_moves:
                board[r][c] = ME
                val = minimax(board, d, alpha, beta, False)
                board[r][c] = EMPTY
                
                if val > score:
                    score = val
                    current_best_in_depth = (r, c)
                
                # Update alpha
                alpha = max(alpha, score)
                
            best_move = current_best_in_depth
            
            # If we found a forced win, execute it immediately
            if score > 100000:
                break
                
    except TimeoutError:
        pass # Return the best move found in the last fully completed depth

    return best_move
