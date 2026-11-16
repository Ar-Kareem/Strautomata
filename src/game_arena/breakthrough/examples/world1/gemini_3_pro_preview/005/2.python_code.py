
import time

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    """
    Breakthrough AI Policy using Iterative Deepening Minimax with Alpha-Beta Pruning.
    """
    
    # --- Constants & Config ---
    TIME_LIMIT = 0.9  # Seconds allowed for search to leave buffer for overhead
    WIN_SCORE = 1_000_000
    MAX_DEPTH = 50   # Theoretical max, effectively limited by time
    
    # Board Values for evaluation (Row 0 to 7 relative to player direction)
    # Exponential growth to encourage pushing pawns to the end
    ROW_VALUES = [0, 5, 15, 35, 70, 120, 300, WIN_SCORE]
    
    start_time = time.time()
    
    # --- 1. State Normalization ---
    # We normalize coordinates so that 'me' (Current Player) always moves from Row 0 -> Row 7.
    # If color is Black ('b'), we flip the board vertically for internal logic.
    should_flip = (color == 'b')
    
    def to_idx(r, c):
        if should_flip:
            return (7 - r) * 8 + c
        return r * 8 + c

    def from_idx(idx):
        r, c = divmod(idx, 8)
        if should_flip:
            r = 7 - r
        return (r, c)

    # Internal Board Representation: 1D list of 64 integers
    # 0 = Empty, 1 = Me, 2 = Opp
    board = [0] * 64
    
    for r, c in me:
        idx = to_idx(r, c)
        board[idx] = 1
        
    for r, c in opp:
        idx = to_idx(r, c)
        board[idx] = 2

    # --- 2. Move Generation ---
    def get_moves(bd, player):
        # player: 1 (Me, moves UP +8), 2 (Opp, moves DOWN -8 in normalized view)
        moves = []
        direction = 8 if player == 1 else -8
        targets = {2} if player == 1 else {1} # Targets for capture
        
        # Scan board for pieces of current player
        p_indices = [i for i, x in enumerate(bd) if x == player]
        
        for idx in p_indices:
            r, c = divmod(idx, 8)
            
            # 1. Forward Straight (Must be empty)
            fwd = idx + direction
            if 0 <= fwd < 64:
                if bd[fwd] == 0:
                    moves.append((idx, fwd))
            
            # 2. Diagonals (Capture or Move if empty)
            # Left Diagonal: col-1
            if c > 0:
                diag_l = idx + direction - 1
                if 0 <= diag_l < 64:
                    content = bd[diag_l]
                    if content == 0 or content in targets:
                        moves.append((idx, diag_l))
                        
            # Right Diagonal: col+1
            if c < 7:
                diag_r = idx + direction + 1
                if 0 <= diag_r < 64:
                    content = bd[diag_r]
                    if content == 0 or content in targets:
                        moves.append((idx, diag_r))
        
        return moves

    def sort_moves(moves, bd, player):
        # Heuristic Move Ordering: Win > Capture > Advance
        def score_move(m):
            frm, to = m
            tgt_r = to // 8
            
            # Immediate Win
            if player == 1 and tgt_r == 7: return 99999
            if player == 2 and tgt_r == 0: return 99999
            
            val = 0
            is_capture = (bd[to] != 0)
            if is_capture:
                val += 1000
            
            # Advance (closer to target row is better)
            # Player 1 wants row 7, Player 2 wants row 0
            row_score = tgt_r if player == 1 else (7 - tgt_r)
            val += row_score * 10
            
            return val
            
        moves.sort(key=score_move, reverse=True)

    # --- 3. Evaluation Function ---
    def evaluate(bd):
        score = 0
        p1_count = 0
        p2_count = 0
        
        for idx in range(64):
            piece = bd[idx]
            if piece == 0: continue
            
            r = idx // 8
            
            if piece == 1:
                p1_count += 1
                if r == 7: return WIN_SCORE # Win condition
                score += ROW_VALUES[r] + 50 # Base material + Positional
                
            elif piece == 2:
                p2_count += 1
                if r == 0: return -WIN_SCORE # Lose condition
                score -= (ROW_VALUES[7 - r] + 50)
        
        # Winning by eliminating all opponents
        if p2_count == 0: return WIN_SCORE
        if p1_count == 0: return -WIN_SCORE
        
        return score

    # --- 4. Alpha-Beta Search ---
    class SearchTimeout(Exception): pass

    def minimax(depth, alpha, beta, is_max):
        # Time check occasionally
        if (depth % 2 == 0) and (time.time() - start_time > TIME_LIMIT):
            raise SearchTimeout

        current_score = evaluate(board)
        
        # Check terminals (Win/Loss)
        if abs(current_score) >= WIN_SCORE - 2000:
            return current_score
        
        if depth == 0:
            return current_score
        
        player = 1 if is_max else 2
        moves = get_moves(board, player)
        
        if not moves:
            # If current player has no moves, check logic (usually covered by zero piece count)
            # For robustness: if I can't move, I lose or it's terminal bad
            return -WIN_SCORE if is_max else WIN_SCORE
            
        sort_moves(moves, board, player)
        
        if is_max:
            max_eval = -float('inf')
            for frm, to in moves:
                captured = board[to]
                board[to] = 1
                board[frm] = 0
                
                try:
                    eval_val = minimax(depth - 1, alpha, beta, False)
                finally:
                    # Undo
                    board[frm] = 1
                    board[to] = captured
                
                max_eval = max(max_eval, eval_val)
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for frm, to in moves:
                captured = board[to]
                board[to] = 2
                board[frm] = 0
                
                try:
                    eval_val = minimax(depth - 1, alpha, beta, True)
                finally:
                    # Undo
                    board[frm] = 2
                    board[to] = captured
                
                min_eval = min(min_eval, eval_val)
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break
            return min_eval

    # --- 5. Main Execution Loop (Iterative Deepening) ---
    best_move = None
    
    # Get initial legal moves
    initial_moves = get_moves(board, 1)
    
    # Safety fallback
    if not initial_moves:
        return ((0,0), (0,0))
    
    # Heuristic sort for initial Depth 1
    sort_moves(initial_moves, board, 1)
    best_move = initial_moves[0]
    
    try:
        for d in range(1, MAX_DEPTH + 1):
            alpha = -float('inf')
            beta = float('inf')
            
            # Root Search
            current_best = None
            current_max = -float('inf')
            
            for frm, to in initial_moves:
                captured = board[to]
                board[to] = 1
                board[frm] = 0
                
                try:
                    # Call Min (opp moves next)
                    score = minimax(d - 1, alpha, beta, False)
                finally:
                    # Undo
                    board[frm] = 1
                    board[to] = captured
                
                if score > current_max:
                    current_max = score
                    current_best = (frm, to)
                
                alpha = max(alpha, score)
                
                # Forced win found, return immediately
                if score >= WIN_SCORE - 2000:
                    best_move = current_best
                    raise SearchTimeout # Break cleanly
            
            best_move = current_best
            
            # Optimization: Move global best to front for next iteration
            if best_move in initial_moves:
                initial_moves.sort(key=lambda x: x == best_move, reverse=True)
            
    except SearchTimeout:
        pass
        
    # Format Return
    f_idx, t_idx = best_move
    return (from_idx(f_idx), from_idx(t_idx))
