
import time

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    
    # Constants
    WHITE = 1
    BLACK = -1
    EMPTY = 0
    
    # Determine playing color integers and direction
    # White moves up (row +1), Black moves down (row -1)
    my_color = WHITE if color == 'w' else BLACK
    opp_color = -my_color
    
    # Initialize Board (1D array of 64 integers)
    # index = row * 8 + col
    board = [EMPTY] * 64
    for r, c in me:
        board[r * 8 + c] = my_color
    for r, c in opp:
        board[r * 8 + c] = opp_color

    start_time = time.time()
    time_limit = 0.90  # Safety buffer for 1s limit
    
    # --- Helper Functions ---

    def get_moves(board, p_color):
        """Generates all legal moves for p_color."""
        moves = []
        is_white = (p_color == WHITE)
        direction = 1 if is_white else -1
        
        # Iterating over the board to find pieces is fast for 64 squares
        for idx in range(64):
            if board[idx] == p_color:
                r, c = divmod(idx, 8)
                nr = r + direction
                
                # Check boundaries (0-7)
                if 0 <= nr <= 7:
                    # 1. Straight Move (must be empty)
                    nidx_straight = nr * 8 + c
                    if board[nidx_straight] == EMPTY:
                        moves.append(((r, c), (nr, c)))
                    
                    # 2. Diagonal Left (empty or opponent)
                    if c > 0:
                        nidx_left = nr * 8 + (c - 1)
                        content = board[nidx_left]
                        if content == EMPTY or content == -p_color:
                            moves.append(((r, c), (nr, c - 1)))

                    # 3. Diagonal Right (empty or opponent)
                    if c < 7:
                        nidx_right = nr * 8 + (c + 1)
                        content = board[nidx_right]
                        if content == EMPTY or content == -p_color:
                            moves.append(((r, c), (nr, c + 1)))
        return moves

    def evaluate(board, p_color):
        """Static evaluation of the board from p_color's perspective."""
        w_score = 0
        b_score = 0
        
        for idx in range(64):
            piece = board[idx]
            if piece == EMPTY:
                continue
            
            r = idx // 8
            if piece == WHITE:
                # Material + Advancement (Reward advancing squares exponentially)
                w_score += 20 + (r * r)
            else:
                # Material + Advancement (Reward advancing squares exponentially from top)
                dist = 7 - r
                b_score += 20 + (dist * dist)
        
        score = w_score - b_score
        return score if p_color == WHITE else -score

    class SearchTimeout(Exception):
        pass

    nodes_visited = 0

    def alphabeta(board, depth, alpha, beta, maximizing_player):
        nonlocal nodes_visited
        nodes_visited += 1
        
        # Check time periodically (every 2048 nodes)
        if nodes_visited & 2047 == 0:
            if time.time() - start_time > time_limit:
                raise SearchTimeout

        current_turn_color = my_color if maximizing_player else opp_color
        
        # Win Condition Check: Has anyone reached their target?
        # White target: Row 7 (indices 56-63)
        for i in range(56, 64):
            if board[i] == WHITE:
                val = 100000 + depth
                return val if my_color == WHITE else -val
        # Black target: Row 0 (indices 0-7)
        for i in range(8):
            if board[i] == BLACK:
                val = 100000 + depth
                return val if my_color == BLACK else -val
        
        if depth == 0:
            return evaluate(board, my_color)
            
        moves = get_moves(board, current_turn_color)
        
        # Terminal node check: No moves available (Loss)
        if not moves:
            return -100000 + depth if maximizing_player else 100000 - depth

        # Move Ordering Heuristic for Pruning
        # Sort by: Capture (1st), then Advancement score (2nd)
        def sort_key(m):
            (fr, fc), (tr, tc) = m
            score = 0
            tidx = tr * 8 + tc
            # Bonus for capture
            if board[tidx] != EMPTY:
                score += 100
            # Bonus for advancement
            if current_turn_color == WHITE: score += tr
            else: score += (7 - tr)
            return score

        moves.sort(key=sort_key, reverse=True)

        if maximizing_player:
            max_eval = -float('inf')
            for m in moves:
                (fr, fc), (tr, tc) = m
                fidx = fr*8 + fc
                tidx = tr*8 + tc
                
                # Execute Move
                captured = board[tidx]
                board[tidx] = board[fidx]
                board[fidx] = EMPTY
                
                eval_val = alphabeta(board, depth - 1, alpha, beta, False)
                
                # Undo Move
                board[fidx] = board[tidx]
                board[tidx] = captured
                
                if eval_val > max_eval:
                    max_eval = eval_val
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for m in moves:
                (fr, fc), (tr, tc) = m
                fidx = fr*8 + fc
                tidx = tr*8 + tc
                
                # Execute Move
                captured = board[tidx]
                board[tidx] = board[fidx]
                board[fidx] = EMPTY
                
                eval_val = alphabeta(board, depth - 1, alpha, beta, True)
                
                # Undo Move
                board[fidx] = board[tidx]
                board[tidx] = captured
                
                if eval_val < min_eval:
                    min_eval = eval_val
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break
            return min_eval

    # --- Iterative Deepening Search ---
    
    # Generate root moves
    root_moves = get_moves(board, my_color)
    
    # Check for immediate win
    for m in root_moves:
        (fr, fc), (tr, tc) = m
        if my_color == WHITE and tr == 7: return m
        if my_color == BLACK and tr == 0: return m
    
    # Prepare fallback move (heuristic sort)
    def root_sort_key(m):
        (fr, fc), (tr, tc) = m
        score = 0
        tidx = tr * 8 + tc
        # Capture?
        if board[tidx] != EMPTY: score += 50
        # Advancement?
        if my_color == WHITE: score += tr
        else: score += (7 - tr)
        return score
    
    if not root_moves:
        return ((0,0), (0,0)) # Should theoretically not happen unless game over
        
    root_moves.sort(key=root_sort_key, reverse=True)
    best_move_global = root_moves[0]
    
    try:
        # Iterative Deepening
        for depth in range(1, 20):
            best_val_this_depth = -float('inf')
            best_move_this_depth = None
            alpha = -float('inf')
            beta = float('inf')
            
            for m in root_moves:
                (fr, fc), (tr, tc) = m
                fidx = fr*8 + fc
                tidx = tr*8 + tc
                
                # Execute Move
                captured = board[tidx]
                board[tidx] = board[fidx]
                board[fidx] = EMPTY
                
                val = alphabeta(board, depth - 1, alpha, beta, False)
                
                # Undo Move
                board[fidx] = board[tidx]
                board[tidx] = captured
                
                if val > best_val_this_depth:
                    best_val_this_depth = val
                    best_move_this_depth = m
                
                alpha = max(alpha, best_val_this_depth)
            
            # Update global best only after completing full depth
            best_move_global = best_move_this_depth
            
            # If we see a winning score, we can stop early
            if best_val_this_depth > 50000:
                break
                
    except SearchTimeout:
        pass # Return the best move found in previous completed depths
    
    return best_move_global
