
import time

def policy(you: list[int], opponent: list[int]) -> int:
    # Start time to enforce the 1-second limit
    start_time = time.time()
    TIME_LIMIT = 0.95

    # ---------------------------------------------------------
    # Helper functions for game logic and search
    # ---------------------------------------------------------

    def get_valid_moves(board):
        return [i for i in range(6) if board[i] > 0]

    def simulate_move(me, opp, move_idx):
        """
        Simulates a move from the perspective of 'me'.
        Returns: (new_me, new_opp, extra_turn, game_over)
        """
        seeds = me[move_idx]
        if seeds == 0:
            return me, opp, False, False

        # Create copies to avoid modifying original state
        me = me[:]
        opp = opp[:]

        me[move_idx] = 0
        pos = move_idx
        
        # Sow seeds
        for _ in range(seeds):
            pos = (pos + 1) % 13
            if pos < 6:
                me[pos] += 1
            elif pos == 6:
                me[6] += 1
            else:
                # Position 7..12 maps to opponent houses 0..5
                opp[pos - 7] += 1

        extra_turn = (pos == 6)
        
        # Capture logic
        # Check if landed on own side (0..5), not the store, and house is now 1 (was empty)
        # Note: pos != move_idx check handles the case where we loop back to start with 13+ seeds
        if not extra_turn and pos < 6:
            if me[pos] == 1 and pos != move_idx and opp[5 - pos] > 0:
                capture_count = 1 + opp[5 - pos]
                me[6] += capture_count
                me[pos] = 0
                opp[5 - pos] = 0

        # Game over check
        my_seeds = sum(me[:6])
        opp_seeds = sum(opp[:6])
        
        if my_seeds == 0 or opp_seeds == 0:
            # Game ends: collect all remaining seeds into stores
            me[6] += my_seeds
            opp[6] += opp_seeds
            for i in range(6):
                me[i] = 0
                opp[i] = 0
            return me, opp, False, True

        return me, opp, extra_turn, False

    def evaluate(me, opp):
        """
        Heuristic evaluation of the board state from perspective of 'me'.
        """
        # Score difference is primary
        score = me[6] - opp[6]
        # Add heuristic for seeds in play
        score += (sum(me[:6]) - sum(opp[:6])) * 0.1
        return score

    def negamax(me, opp, depth, alpha, beta):
        """
        Negamax search with Alpha-Beta pruning.
        Returns (score, best_move).
        """
        # Check timeout
        if time.time() - start_time > TIME_LIMIT:
            return -10000, -1

        # Terminal or depth limit
        if depth == 0:
            return evaluate(me, opp), -1
        
        moves = get_valid_moves(me)
        if not moves:
            return evaluate(me, opp), -1

        # Move Ordering heuristic
        # Priority: Extra Turn > Capture > Most Seeds
        def move_score(i):
            s = me[i]
            land = (i + s) % 13
            # Extra turn?
            if land == 6: 
                return 1000
            # Capture?
            if land < 6 and me[land] == 0 and opp[5 - land] > 0:
                # Heuristic: larger capture is better, but ensure valid landing
                # Note: This is an approximation for ordering; actual capture depends on path
                return 500 + opp[5 - land]
            # Default: prioritize spreading seeds
            return s

        moves.sort(key=move_score, reverse=True)

        best_move = moves[0]
        max_eval = -float('inf')

        for move in moves:
            # Check timeout frequently
            if time.time() - start_time > TIME_LIMIT:
                break

            new_me, new_opp, extra, over = simulate_move(me, opp, move)

            if over:
                val = evaluate(new_me, new_opp)
            elif extra:
                # Same player moves again (depth-1 because we used a move?)
                # Usually we do not decrement depth on extra turns to see full sequence
                val, _ = negamax(new_me, new_opp, depth, alpha, beta)
            else:
                # Switch sides: invert perspective
                val, _ = negamax(new_opp, new_me, depth - 1, -beta, -alpha)
                val = -val

            if val > max_eval:
                max_eval = val
                best_move = move

            alpha = max(alpha, val)
            if alpha >= beta:
                break

        return max_eval, best_move

    # ---------------------------------------------------------
    # Main execution logic with Iterative Deepening
    # ---------------------------------------------------------
    
    best_move = -1
    moves = get_valid_moves(you)
    
    # Fallback: if only one move, play it immediately
    if len(moves) == 1:
        return moves[0]
    
    # Default to first valid move in case of immediate timeout
    best_move = moves[0]

    # Iterative Deepening Loop
    try:
        for depth in range(1, 25):
            if time.time() - start_time > TIME_LIMIT:
                break
            
            # Perform search
            # We use a wide initial window (alpha, beta)
            score, move = negamax(you, opponent, depth, -float('inf'), float('inf'))
            
            if move != -1:
                best_move = move
            
            # If we found a winning line or lost line, we can stop early?
            # Not necessarily, but good for performance.
            
    except Exception:
        # Safety catch for any unexpected errors
        pass

    return best_move
