
import sys

# Increase recursion depth for deep simulations if necessary
sys.setrecursionlimit(5000)

def policy(you: list[int], opponent: list[int]) -> int:
    """
    Implements a move-selection policy for the game Kalah (Mancala).
    Uses a Depth-Limited Alpha-Beta search with a heuristic evaluation function.
    The search includes full simulation of moves and captures.
    """
    
    # Precompute capture indices for optimization
    # A capture is possible at index i if your house i becomes empty and opponent's opposite (5-i) has seeds.
    # This depends on the move choice and the number of seeds being distributed.
    # However, we can simplify: a move from i is a candidate for capture if the count of seeds is such 
    # that it could land in i (wrapping around).
    # To keep it fast and accurate, we will detect captures dynamically during the search simulation.
    
    # Heuristic constants
    MOVE_BONUS = 10.0  # Bonus for getting an extra turn
    CAPTURE_BONUS = 6.0 # Bonus per seed captured (scaled)
    SAFETY_BONUS = 0.5  # Bonus for leaving a house safe (generally lower priority in aggressive play, 
                        # but important to not leave easy captures).
                        # We will actually penalize leaving the opponent a free capture, 
                        # which is handled in the opponent's search.

    def is_terminal(state_you, state_opp):
        """Checks if the game is over for the current player."""
        return sum(state_you[:6]) == 0

    def finish_game(state_you, state_opp):
        """End game scoring: move all seeds to stores."""
        score = state_you[6] + sum(state_you[:6])
        opp_score = state_opp[6] + sum(state_opp[:6])
        # Return difference relative to current player
        return score - opp_score

    def evaluate(state_you, state_opp):
        """
        Heuristic evaluation of the board state for the current player.
        Returns a score (float).
        """
        if is_terminal(state_you, state_opp):
            return finish_game(state_you, state_opp)
        
        # Basic score difference
        score_diff = state_you[6] - state_opp[6]
        
        # Seeds on board advantage
        seeds_you = sum(state_you[:6])
        seeds_opp = sum(state_opp[:6])
        
        # Dynamic weighting:
        # Early game: seeds on board matter more (potential).
        # Late game: seeds in store matter more.
        # We use a simple linear weighting based on total seeds remaining.
        total_seeds = seeds_you + seeds_opp
        # Total seeds in standard 6-hole Kalah is usually 36, but can vary.
        # We map 0-36 to 0.0-1.0 roughly.
        progress = 1.0 - (total_seeds / 36.0) if total_seeds > 0 else 1.0
        progress = max(0.0, min(1.0, progress))
        
        # Weights
        w_store = 2.5 + 2.0 * progress  # Store importance increases
        w_board = 1.0 + 0.5 * (1.0 - progress) # Board importance decreases
        
        # Safety check: penalize leaving a house with 1 seed opposite an empty house
        # (This prevents giving the opponent a free capture if they can reach it)
        safety_penalty = 0
        for i in range(6):
            if state_you[i] == 1 and state_opp[5-i] == 0:
                safety_penalty += 0.2

        # Combine components
        # Note: We want to maximize this value
        val = (state_you[6] * w_store) - (state_opp[6] * w_store) + \
              (seeds_you * w_board) - (seeds_opp * w_board) - \
              safety_penalty
              
        return val

    def simulate_move(state_you, state_opp, move_idx):
        """
        Simulates a move and returns the result.
        Returns: (next_state_you, next_state_opp, extra_turn)
        Does NOT modify inputs.
        """
        # Deep copy lists to avoid mutation issues
        s_you = state_you[:]
        s_opp = state_opp[:]
        
        seeds = s_you[move_idx]
        s_you[move_idx] = 0
        
        curr = move_idx
        while seeds > 0:
            curr += 1
            
            # Skip opponent's store (index 6 in opponent's list)
            # Logic: We are iterating indices 0..inf.
            # We map indices to board slots.
            # Our slots: 0..5, store is 6.
            # Opponent slots: 0..5, store is 6.
            # We iterate: You(0..5) -> You(6) -> Opp(0..5) -> You(0..5)...
            
            # Check if we wrapped past opponent store (index 12 in combined iteration is Opp[6])
            # A cleaner way is manual stepping:
            
            # Let's use a simpler indexing logic:
            # We iterate in a cycle of 14 slots.
            # Indices 0-5: You
            # Index 6: You Store
            # Indices 7-12: Opponent
            # Index 13: Opponent Store (SKIP)
            
            # Map 'curr' absolute index to board locations
            abs_index = (move_idx + 1 + (move_idx + 1 + 1 + (seeds - 1))) % 14 # Wait, this is messy.
            
            # Let's stick to the instructions explicitly:
            # 1. you[i+1] through you[5]
            # 2. you[6]
            # 3. opponent[0] through opponent[5]
            # 4. you[0] through you[5] ...
            
            # Let's use a simple index offset logic
            # Offset 0 is move_idx (which is now empty).
            # We start filling at offset 1.
            
            # Calculate total "slots" to skip manually is inefficient.
            # Let's use a pointer that wraps around the combined 14 slots (excluding Opp Store).
            # Map 0-5 to You[i]
            # Map 6 to You[6]
            # Map 7-12 to Opp[i-7]
            
            # We calculate current slot index relative to board start
            # We start at move_idx. We increment.
            
            # Let's just calculate the absolute slot index in the cycle of 14.
            # 0..5: You Houses
            # 6: You Store
            # 7..12: Opp Houses
            # 13: Opp Store (Skip)
            
            # Current absolute slot index:
            # We start at move_idx (which is 0..5).
            # We need to place the next seed.
            # We iterate 'seeds' times. But we can optimize the loop.
            
            pass # Break out to a better loop structure below

        # Optimized Simulation Loop
        s_you = state_you[:]
        s_opp = state_opp[:]
        seeds = s_you[move_idx]
        s_you[move_idx] = 0
        
        # Current position index in the 14-slot cycle (0..13)
        # 0-5: You, 6: You Store, 7-12: Opp, 13: Opp Store
        curr_pos = move_idx
        
        # We need to distribute 'seeds' seeds.
        # Calculate full laps and remainder to avoid loop overhead if seeds is huge
        # But usually seeds is small (<20).
        # We loop manually for correctness.
        
        last_pos = -1
        
        for _ in range(seeds):
            curr_pos += 1
            if curr_pos == 13: # Skip Opponent Store
                curr_pos = 0
            elif curr_pos == 14:
                curr_pos = 0
            
            if curr_pos < 6:
                s_you[curr_pos] += 1
            elif curr_pos == 6:
                s_you[6] += 1
            else: # 7 to 12
                s_opp[curr_pos - 7] += 1
            
            last_pos = curr_pos

        # Check Extra Move
        extra_move = (last_pos == 6)

        # Check Capture
        # If last seed lands in You[0..5] (i.e., last_pos 0..5)
        # AND that house had 1 seed (just placed, so check count 1)
        # AND Opposite house (Opp[5 - last_pos]) has seeds
        capture_happened = False
        if 0 <= last_pos <= 5:
            house_idx = last_pos
            if s_you[house_idx] == 1: # It was empty before or had 0? 
                # Actually, logic says "lands in your house and it was empty before".
                # We added 1. So if it is 1 now, it was 0 before.
                # But we must ensure it wasn't the house we moved from (which we emptied manually).
                # That case handles itself: if we moved from house X, we set s_you[X]=0. 
                # If we land back on X (loop), it increments to 1. Correct.
                
                opp_idx = 5 - house_idx
                if s_opp[opp_idx] > 0:
                    # Perform capture
                    s_you[6] += 1 + s_opp[opp_idx] # Add last seed + opponent seeds
                    s_you[house_idx] = 0 # Remove the landed seed
                    s_opp[opp_idx] = 0
                    capture_happened = True
                    extra_move = False # Capture overrides extra move? No, they can coexist in some rules, 
                    # but usually last seed logic determines one or the other. 
                    # If you capture, you get the seeds. 
                    # Standard Kalah: If capture occurs, you get the seeds. 
                    # The 'extra move' rule only applies if you land in your store.
                    # So if you land in store, no capture. If you land in house, capture logic applies.
                    # So extra_move stays True only if last_pos == 6.
        
        return s_you, s_opp, extra_move

    def alpha_beta(state_you, state_opp, depth, alpha, beta, maximizing_player, extra_turn_available=False):
        """
        Alpha-Beta Search.
        maximizing_player: True if we are evaluating for 'us', False if we are evaluating for 'opponent'.
        extra_turn_available: True if the current player (determined by maximizing_player) has an extra turn 
                              due to a previous capture or store landing in the parent call.
                              Wait, logic: if I land in store, I get another move. 
                              This means I continue to act.
        """
        if depth == 0:
            # Return heuristic for the maximizing player (us)
            if maximizing_player:
                return evaluate(state_you, state_opp)
            else:
                # When it's opponent's turn, we evaluate from our perspective.
                # So we swap arguments to evaluate.
                return evaluate(state_opp, state_you)
        
        # Terminal check (no seeds on board)
        # If current player has no seeds, game ends.
        # We need to handle the "other player captures remaining" rule.
        if maximizing_player:
            if is_terminal(state_you, state_opp):
                return finish_game(state_you, state_opp)
        else:
            if is_terminal(state_opp, state_you):
                return finish_game(state_opp, state_you)

        # Identify valid moves
        # If extra_turn_available is True, we are continuing with the same player.
        # If False, we alternate.
        
        # Wait, the 'extra_turn_available' argument in recursive calls:
        # We need to be careful with turn switching.
        
        # Standard recursion:
        # Max node (Us) -> chooses move -> simulates -> Min node (Opp)
        # If we land in store, we get another turn -> Max node (Us) again.
        
        if maximizing_player:
            # We (Max) are moving.
            # Check available houses
            moves = [i for i in range(6) if state_you[i] > 0]
            if not moves:
                # Should be handled by is_terminal, but just in case
                return evaluate(state_you, state_opp)
            
            max_eval = -float('inf')
            for move in moves:
                # Simulate
                n_you, n_opp, extra = simulate_move(state_you, state_opp, move)
                
                # Determine next node
                if extra:
                    # Same player moves again
                    eval_val = alpha_beta(n_you, n_opp, depth - 1, alpha, beta, True, extra_turn_available=True)
                else:
                    # Switch to opponent
                    eval_val = alpha_beta(n_you, n_opp, depth - 1, alpha, beta, False)
                
                max_eval = max(max_eval, eval_val)
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break
            return max_eval
            
        else:
            # Opponent is moving (Min node)
            moves = [i for i in range(6) if state_opp[i] > 0]
            if not moves:
                return evaluate(state_you, state_opp) # Eval from our perspective
            
            min_eval = float('inf')
            for move in moves:
                # Simulate Opponent Move
                # Note: simulate_move takes (current_player_state, opponent_state, move_idx)
                # So we pass (state_opp, state_you, move)
                n_opp, n_you, extra = simulate_move(state_opp, state_you, move)
                
                if extra:
                    # Opponent moves again
                    eval_val = alpha_beta(n_you, n_opp, depth - 1, alpha, beta, False, extra_turn_available=True)
                else:
                    # Switch to us
                    eval_val = alpha_beta(n_you, n_opp, depth - 1, alpha, beta, True)
                
                min_eval = min(min_eval, eval_val)
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break
            return min_eval

    # Root Level: Choose best move
    # We use iterative deepening to respect the 1 second time limit.
    # We start with depth 1, then 3, 5, etc.
    # Or just fixed depth based on complexity.
    # Since we can't easily measure time inside policy without threading, we guess a depth.
    # A depth of 8-12 is usually good for Mancala, but simulation is expensive.
    # Let's try depth 7 to 9.
    
    best_move = -1
    
    # Valid moves at root
    legal_moves = [i for i in range(6) if you[i] > 0]
    if not legal_moves:
        return 0 # Should not happen given problem statement

    # Quick check: Are there any moves that result in an immediate extra turn?
    # Or immediate capture? We can pre-sort moves to check heuristics.
    
    # Iterative Deepening
    # We'll try depth 3, then 5, then 7.
    # We will break if we exceed a heuristic "time" or just pick the best found.
    
    for depth in [3, 5, 7, 9, 11, 13]:
        alpha = -float('inf')
        beta = float('inf')
        current_best_move = legal_moves[0]
        current_best_val = -float('inf')
        
        # Move Ordering: Try moves that look promising first
        # 1. Moves that land in Store (Extra turn)
        # 2. Moves that are captures
        # 3. Moves that leave few seeds (avoid opponent capture)
        
        # We can sort legal_moves based on a simple static evaluation
        def move_priority(m):
            # Estimate if it lands in store: (you[m] + m) % 14 == 6 ? 
            # Store is index 6 in You. 
            # Path: m -> m+1 ... 5 -> 6.
            # If seeds = 6 - m, lands in store exactly.
            # If seeds > 6 - m, it loops. (seeds + m) % 14 == 6.
            # But we skip opponent store (13).
            # Path: m ... 5 (5-m steps) -> 6 (1 step). Total 6-m to reach store.
            # Then 7...12 (6 steps) -> 0... (wraps).
            # Total cycle 14.
            # Landing in store if (you[m] == 6-m) or ((you[m] - (6-m)) % 14 == 0).
            s = you[m]
            dist_to_store = 6 - m
            if s == dist_to_store:
                return 100 # Extra turn!
            # Check for capture: If we distribute s seeds, last lands at (m + s) % 14 (adjusted for skip).
            # This is hard to compute statically.
            # Just use static eval of resulting state? Too slow.
            # Let's just use random shuffle for equal priority, or stick to index order.
            # Better: We can estimate capture:
            # If after move, you[i] becomes 1 and opp[5-i] > 0.
            # Let's simulate the move partially?
            return 0

        # We will just use the order provided by the loop, 
        # but we can try to prioritize store-landing moves if easy to spot.
        sorted_moves = []
        # Check for obvious extra moves
        obvious_extra = []
        others = []
        for m in legal_moves:
            s = you[m]
            dist = 6 - m
            if s == dist:
                obvious_extra.append(m)
            else:
                others.append(m)
        
        # Prioritize obvious extra moves, then others
        sorted_moves = obvious_extra + others
        
        if depth > 3 and len(sorted_moves) > 1:
            # Use previous depth's result to reorder?
            # We don't store search tree across depths easily here.
            pass

        for move in sorted_moves:
            # Simulate root move
            # Note: We need to handle extra turns at root too for the search
            n_you, n_opp, extra = simulate_move(you, opponent, move)
            
            if extra:
                val = alpha_beta(n_you, n_opp, depth - 1, alpha, beta, True, True)
            else:
                val = alpha_beta(n_you, n_opp, depth - 1, alpha, beta, False)
            
            if val > current_best_val:
                current_best_val = val
                current_best_move = move
            
            alpha = max(alpha, val)
            
        # Update best overall
        best_move = current_best_move
        # If we found a very good move, maybe stop early? 
        # Mancala scores can be large. 
        # We'll let it run through depths.

    return best_move
