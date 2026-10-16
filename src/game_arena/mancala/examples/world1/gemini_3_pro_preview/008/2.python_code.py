
import time

def policy(you: list[int], opponent: list[int]) -> int:
    """
    Kalah move selection policy.
    Uses Iterative Deepening Minimax with Alpha-Beta pruning.
    """
    # Combine input lists into a single board representation
    # Indices: 0-5 (P0 pits), 6 (P0 store), 7-12 (P1 pits), 13 (P1 store)
    board = you + opponent
    
    # Time management constraints
    TIME_LIMIT = 0.92  # Seconds. Safety buffer for function overhead.
    start_time = time.time()
    
    # Constants
    MY_STORE = 6
    OPP_STORE = 13
    
    # --- Helper Functions ---

    def get_valid_moves(b, player):
        offset = 0 if player == 0 else 7
        return [i for i in range(6) if b[offset + i] > 0]

    def evaluate(b):
        """
        Heuristic evaluation from the perspective of Player 0.
        """
        # Calculate scores
        score_diff = b[MY_STORE] - b[OPP_STORE]
        
        # Calculate material on board (potential score)
        my_seeds = sum(b[0:6])
        opp_seeds = sum(b[7:13])
        
        # Weight secured seeds (store) significantly higher than board seeds
        # to ensure the bot prioritizes winning conditions.
        # However, board seeds are material advantage.
        # Heuristic: 100 * secured_diff + 1 * potential_diff
        return score_diff * 100 + (my_seeds - opp_seeds)

    def make_move_inplace(b, move_idx, player):
        """
        Executes a move on list 'b' in-place.
        Returns tuple: (repeat_turn: bool, game_over: bool, final_score_diff: int)
        """
        # Determine strict offsets and indices based on player
        if player == 0:
            offset = 0
            store_idx = MY_STORE
            skip_idx = OPP_STORE
        else:
            offset = 7
            store_idx = OPP_STORE
            skip_idx = MY_STORE
        
        pit = offset + move_idx
        seeds = b[pit]
        b[pit] = 0
        
        pos = pit
        while seeds > 0:
            pos = (pos + 1) % 14
            if pos == skip_idx:
                continue
            b[pos] += 1
            seeds -= 1
            
        # -- Check Rules --
        
        repeat_turn = False
        
        # 1. Extra Turn: Last seed lands in own store
        if pos == store_idx:
            repeat_turn = True
        
        # 2. Capture: Last seed lands in empty own pit (and opposite is not empty)
        # Check if pos is in player's pits range
        if offset <= pos < offset + 6:
            if b[pos] == 1: # Was empty before this single seed arrived
                # Opposite index in 14-pit array is 12 - index
                opp_pos = 12 - pos
                if b[opp_pos] > 0:
                    captured = b[pos] + b[opp_pos]
                    b[pos] = 0
                    b[opp_pos] = 0
                    b[store_idx] += captured
                    
        # 3. Game Over Check
        # Game ends if one player has no seeds in their houses (0-5 or 7-12)
        p0_pits = sum(b[0:6])
        p1_pits = sum(b[7:13])
        
        game_over = False
        final_val = 0
        
        if p0_pits == 0 or p1_pits == 0:
            game_over = True
            repeat_turn = False
            
            # Move remaining seeds to respective stores
            if p0_pits == 0:
                # P0 empty, P1 takes P1 remainder
                b[13] += p1_pits
                for i in range(7, 13): b[i] = 0
            else:
                # P1 empty, P0 takes P0 remainder
                b[6] += p0_pits
                for i in range(6): b[i] = 0
            
            # Determine absolute final score difference for termination
            # Multiply by large constant to prioritize winning over heuristic
            final_val = (b[MY_STORE] - b[OPP_STORE]) * 10000
            
        return repeat_turn, game_over, final_val

    # --- Search ---
    
    nodes_visited = 0
    
    def alphabeta(b, depth, alpha, beta, player):
        nonlocal nodes_visited
        nodes_visited += 1
        
        # Periodically check time to fail fast
        if (nodes_visited & 1023) == 0:
            if time.time() - start_time > TIME_LIMIT:
                raise TimeoutError

        # Base case
        if depth <= 0:
            return evaluate(b)
        
        valid_moves = get_valid_moves(b, player)
        if not valid_moves:
            # Should normally be caught by game_over logic in make_move
            return evaluate(b)
        
        is_maximizing = (player == 0)
        
        # Simple move ordering: try moves closer to store (indices 5..0) first
        # This is a common heuristic in Mancala to keep seeds circulating
        valid_moves.sort(reverse=True)
        
        best_val = -float('inf') if is_maximizing else float('inf')
        
        for m in valid_moves:
            # Create a copy for the child state
            new_b = b[:]
            repeat, over, score = make_move_inplace(new_b, m, player)
            
            if over:
                val = score
            elif repeat:
                # If extra turn, continue with same depth and player
                val = alphabeta(new_b, depth, alpha, beta, player)
            else:
                # Standard turn switch, decrease depth
                val = alphabeta(new_b, depth - 1, alpha, beta, 1 - player)
            
            if is_maximizing:
                if val > best_val: best_val = val
                alpha = max(alpha, best_val)
                if beta <= alpha: break
            else:
                if val < best_val: best_val = val
                beta = min(beta, best_val)
                if beta <= alpha: break
                
        return best_val

    # --- Root Execution (Iterative Deepening) ---
    
    initial_moves = get_valid_moves(board, 0)
    
    # Fallback if logic somehow fails or time is instant
    if not initial_moves:
        return 0
        
    best_move_global = initial_moves[0]
    
    try:
        # Depth 1 to 20 should be sufficient range for 1s
        for d in range(1, 25):
            
            # Check time at start of deepening
            if time.time() - start_time > TIME_LIMIT:
                break
                
            current_iter_best_move = best_move_global
            current_iter_best_val = -float('inf')
            
            # Sort moves to try the previous best move first (Principal Variation)
            initial_moves.sort(key=lambda x: x == best_move_global, reverse=True)
            
            for m in initial_moves:
                b_copy = board[:]
                repeat, over, score = make_move_inplace(b_copy, m, 0)
                
                if over:
                    val = score
                elif repeat:
                    val = alphabeta(b_copy, d, -float('inf'), float('inf'), 0)
                else:
                    val = alphabeta(b_copy, d - 1, -float('inf'), float('inf'), 1)
                
                if val > current_iter_best_val:
                    current_iter_best_val = val
                    current_iter_best_move = m
                
                # Check timer tightly inside the root loop
                if time.time() - start_time > TIME_LIMIT:
                    raise TimeoutError

            # Iteration complete, verify result
            best_move_global = current_iter_best_move
            
            # Stop if we found a guaranteed Winning path (very high score)
            if current_iter_best_val > 5000:
                break
                
    except TimeoutError:
        pass # Return the best move found in the last simplified depth
        
    return best_move_global
