
import sys

# Set recursion limit high for deep searches if needed
sys.setrecursionlimit(20000)

def policy(you_in: list[int], opponent_in: list[int]) -> int:
    """
    Implements a move-selection policy for Kalah (6 houses).
    Uses Iterative Deepening Alpha-Beta Pruning with a heuristic evaluation.
    
    Heuristics:
    1. Store difference (primary).
    2. Move advantage (potential for extra turns).
    3. Seed density (blocking opponents or setting up captures).
    4. Piece safety (avoiding captures).
    """
    
    # Constants
    HOUSES = 6
    TOTAL_HOUSES = 13
    MAX_DEPTH = 25  # Max depth for iterative deepening
    TIME_LIMIT = 0.9 # Time limit in seconds
    
    # --- Helper Functions for Board Simulation ---
    
    def get_next_idx(idx: int) -> int:
        """Returns the next index in the circular board (skips opponent store)."""
        if idx == TOTAL_HOUSES:
            return 0
        if idx == 6: # You store
            return 7 # Opponent h0
        if idx == 12: # Opponent store
            return 0 # You h0
        return idx + 1

    def simulate_move(you: list[int], opp: list[int], move: int, player: int):
        """
        Simulates a move.
        player: 0 for us, 1 for opponent.
        Returns (new_you, new_opp, extra_turn).
        """
        # Create copies
        curr_you = list(you)
        curr_opp = list(opp)
        
        if player == 0:
            house_list = curr_you
            op_list = curr_opp
            store_idx = 6
            my_store = 6
            op_store = 12
            # Check valid move (if we are simulating, we usually check before calling)
            # But to be safe, we return None if invalid
            if move < 0 or move > 5 or house_list[move] == 0:
                return None, None, False
        else:
            house_list = curr_opp
            op_list = curr_you
            store_idx = 12
            my_store = 12
            op_store = 6
            # In simulation, we might generate moves
            if move < 0 or move > 5 or house_list[move] == 0:
                return None, None, False
        
        seeds = house_list[move]
        house_list[move] = 0
        
        curr_idx = move
        last_idx = -1
        extra_turn = False
        
        while seeds > 0:
            curr_idx = get_next_idx(curr_idx)
            
            # Skip opponent's store
            if curr_idx == op_store:
                curr_idx = get_next_idx(curr_idx)
            
            # Distribute
            if curr_idx == my_store:
                house_list[6] += 1 # Store is always at relative index 6 in the passed list structure? No.
                # The list passed is [h0...h5, store]. 
                # If player=0, my_store maps to index 6.
                # If player=1, my_store maps to index 12.
                # But we are modifying curr_you/curr_opp which are [h0..h5, store].
                # So we need to handle index mapping carefully.
                
                # Let's map board index (0-12) to list index
                # Board: 0..5 (us), 6 (us store), 7..12 (opp), 13 (opp store - doesn't exist, it's 12)
                # Wait, standard board: 
                # 0..5 (You), 6 (You Store), 7..12 (Opp), 13 (Opp Store).
                # But we represent Opp as [h0..h5, store].
                # Mapping:
                # Board 0..5 -> You list 0..5
                # Board 6 -> You list 6
                # Board 7..12 -> Opp list 0..5
                # Board 13 -> Opp list 6
                
                if player == 0:
                    if curr_idx == 6: house_list[6] += 1
                    elif curr_idx <= 5: house_list[curr_idx] += 1
                    else: op_list[curr_idx - 7] += 1
                else:
                    # Player 1 (Opponent relative to us)
                    if curr_idx == 6: # This is opponent's store (Board 6 corresponds to Opp store? No)
                        # Board Indices:
                        # You: 0..5, 6
                        # Opp: 7..12, 13
                        # Wait, the get_next_idx logic skips 13 for Opp store.
                        # Let's use standard mapping: 
                        # 0-5: You Houses
                        # 6: You Store
                        # 7-12: Opp Houses
                        # 13: Opp Store
                        # But list size is 7.
                        pass
            else:
                # Logic fix: Direct array mapping is messy.
                # Let's use a flat array of size 14 for simulation, then convert back.
                pass
        
        # Re-implementation of simulation with flat board to avoid index hell
        # Flat board: 
        # 0..5: You Houses
        # 6: You Store
        # 7..12: Opp Houses
        # 13: Opp Store
        
        # 1. Populate flat board
        board = [0] * 14
        for k in range(6): board[k] = you[k]
        board[6] = you[6]
        for k in range(6): board[k+7] = opponent[k]
        board[13] = opponent[6]
        
        start_idx = move if player == 0 else move + 7
        
        if board[start_idx] == 0:
            return None, None, False
            
        seeds = board[start_idx]
        board[start_idx] = 0
        curr_idx = start_idx
        last_idx = -1
        
        # Sowing loop
        while seeds > 0:
            curr_idx += 1
            if curr_idx == 14: curr_idx = 0
            
            # Skip opponent's store based on player
            if player == 0:
                if curr_idx == 13: continue # Skip Opponent Store
            else:
                if curr_idx == 6: continue # Skip Opponent (You) Store - No, this is tricky.
                # Wait, if Player 1 is moving, Opponent is Us (from policy perspective).
                # Player 1 (Opp) skips their opponent's store, which is Our Store (idx 6).
                # Yes.
            
            if curr_idx == 13 and player == 0: continue
            if curr_idx == 6 and player == 1: continue
            
            board[curr_idx] += 1
            seeds -= 1
            last_idx = curr_idx
        
        # Post-move rules
        
        # 1. Extra Turn
        if player == 0 and last_idx == 6:
            return board[0:7], board[7:13] + [board[13]], True
        if player == 1 and last_idx == 13:
            # For simulation returning to us, we don't care much about opp extra turn for depth.
            # But we need to know state.
            return board[0:7], board[7:13] + [board[13]], True 
            
        # 2. Capture
        if player == 0 and last_idx <= 5 and board[last_idx] == 1:
            opp_idx = 12 - last_idx # Opposite house index (7..12)
            if board[opp_idx] > 0:
                # Capture
                captured = board[opp_idx]
                board[opp_idx] = 0
                board[6] += board[last_idx] + captured # Take mine + theirs
                board[last_idx] = 0
        
        elif player == 1 and 7 <= last_idx <= 12:
            # Opponent capture logic
            if board[last_idx] == 1:
                # Opposite of Opp House is Your House
                opp_idx = 12 - last_idx # If last_idx=7, opp_idx=5. If last_idx=12, opp_idx=0.
                if board[opp_idx] > 0:
                    captured = board[opp_idx]
                    board[opp_idx] = 0
                    board[13] += board[last_idx] + captured
                    board[last_idx] = 0
        
        return board[0:7], board[7:13] + [board[13]], False

    def is_game_over(you: list[int], opp: list[int]) -> bool:
        return sum(you[:6]) == 0 or sum(opp[:6]) == 0

    def calculate_final_score(you: list[int], opp: list[int]) -> int:
        """Returns you_store - opp_store, adjusted for remaining seeds."""
        my_seeds = sum(you[:6]) + you[6]
        opp_seeds = sum(opp[:6]) + opp[6]
        return my_seeds - opp_seeds

    # --- Evaluation Function ---
    
    def evaluate(you: list[int], opp: list[int], depth: int) -> int:
        # Immediate end state
        if is_game_over(you, opp):
            score = calculate_final_score(you, opp)
            # Big win bonus, inversely proportional to depth (prefer faster wins)
            if score > 0: return 1000000 - depth
            if score < 0: return -1000000 + depth
            return 0
        
        # Heuristics
        my_store = you[6]
        op_store = opp[6]
        
        # 1. Store Difference (Primary)
        score = (my_store - op_store) * 100
        
        # 2. Move Advantage (Free turns)
        # Count seeds in houses that would land in store if picked up
        # If you pick up S seeds from house i, they go to (6-i) houses then store.
        # Lands in store if S <= (6 - i)
        my_moves = 0
        for i in range(6):
            if you[i] > 0:
                if you[i] <= (6 - i):
                    my_moves += 1
                # Bonus if it allows capture
                if i + you[i] == 6: # Lands in store (extra turn)
                    my_moves += 2 # Weight extra turns heavily
                elif you[i] == 1 and sum(opponent[5 - (i + you[i]) % 6] for _ in range(1)) > 0: # Simplified capture check
                     # This is complex to check accurately without full sowing, 
                     # but simply checking if landing spot is near empty house
                     pass
        
        # Opponent move potential
        op_moves = 0
        for i in range(6):
            if opp[i] > 0:
                if opp[i] <= (6 - i):
                    op_moves += 1
                if i + opp[i] == 6:
                    op_moves += 2
        
        score += (my_moves - op_moves) * 5
        
        # 3. Seed Density & Safety
        # We want to avoid having 1 seed in a house if opponent can capture
        my_risk = 0
        for i in range(6):
            if you[i] == 1:
                # Check if opp house opposite has seeds
                if opp[5 - i] > 0:
                    my_risk += 10
        score -= my_risk
        
        # We want opponent to have seeds in capture positions (risk for them)
        op_risk = 0
        for i in range(6):
            if opp[i] == 1:
                if you[5 - i] > 0:
                    op_risk += 10
        score += op_risk
        
        # 4. Distance to store (Aim to clear right side)
        # Weights: (1, 2, 3, 4, 5, 6) or similar. 
        # Prefer seeds closer to store to clear them faster.
        # Reverse: prefer seeds further (to keep store empty for captures?)
        # Usually, bring seeds home.
        my_dist_score = sum(you[i] * (6-i) for i in range(6))
        op_dist_score = sum(opp[i] * (6-i) for i in range(6))
        # We want to reduce our distance, increase opponent distance
        score -= my_dist_score * 0.1
        score += op_dist_score * 0.1
        
        return int(score)

    # --- Alpha-Beta Search ---
    
    # Transposition Table: dict of (hash) -> (depth, value, flag, best_move)
    # Hashing: tuple of 14 ints
    tt = {}
    
    def get_tt_entry(you: tuple, opp: tuple):
        return tt.get((you, opp))
    
    def set_tt_entry(you: tuple, opp: tuple, depth, value, flag, best_move):
        tt[(you, opp)] = (depth, value, flag, best_move)

    def ab_search(you, opp, depth, alpha, beta, maximizing_player, root=False):
        # Time check
        if root:
            pass # Check only in loop
        
        # TT lookup
        # Since we modify lists, convert to tuple for hashing
        you_t = tuple(you)
        opp_t = tuple(opp)
        tt_entry = get_tt_entry(you_t, opp_t)
        if tt_entry and tt_entry[0] >= depth:
            stored_depth, stored_val, stored_flag, stored_move = tt_entry
            if stored_flag == 0: return stored_val
            if stored_flag == 1 and stored_val >= beta: return stored_val # Lower bound
            if stored_flag == 2 and stored_val <= alpha: return stored_val # Upper bound
        
        # Leaf conditions
        if is_game_over(you, opp):
            score = calculate_final_score(you, opp)
            return 1000000 if score > 0 else -1000000 if score < 0 else 0
            
        if depth == 0:
            return evaluate(you, opp, depth)
            
        best_value = -float('inf') if maximizing_player else float('inf')
        best_move_local = -1
        
        # Move Generation
        # If root, we iterate main moves. 
        # If maximizing_player (Us), moves 0..5.
        # If minimizing_player (Opp), moves 0..5 (mapped to their board).
        
        # Optimization: Move ordering
        # 1. Moves that land in store (extra turn)
        # 2. Moves that capture
        # 3. Other moves
        
        moves = []
        if maximizing_player:
            for i in range(6):
                if you[i] > 0:
                    is_extra = (i + you[i] == 6) # Lands in store
                    is_capture = False
                    if you[i] == 1 and (5 - i) >= 0 and (5 - i) < 6 and opp[5 - i] > 0:
                        is_capture = True
                    
                    score_priority = 0
                    if is_extra: score_priority += 100
                    if is_capture: score_priority += 50
                    
                    # Tie break: choose further houses? Or closer? Closer to clear.
                    score_priority += (6-i)
                    
                    moves.append((i, score_priority))
            
            moves.sort(key=lambda x: x[1], reverse=True)
            
            for move, _ in moves:
                # Apply move
                # We need to be careful with returns. 
                # simulate_move returns (you_new, opp_new, extra_turn)
                # But for recursive search, we handle extra turn by calling ourselves again on same player
                # simulate_move handles the sowing and capture.
                
                y_new, o_new, extra = simulate_move(you, opp, move, 0)
                if y_new is None: continue
                
                # Handle Extra Turn
                # If extra is True, we effectively increase depth or recurse without switching player
                # To prevent infinite loops (rare in Kalah but possible), we check if board changed.
                
                # Standard approach: If extra turn, call search with same player (maximizing) and same depth (or depth-1? usually depth-1)
                # Let's say we consume depth on turn.
                if extra:
                    val = ab_search(y_new, o_new, depth - 1, alpha, beta, True)
                else:
                    val = ab_search(y_new, o_new, depth - 1, alpha, beta, False)
                
                if val > best_value:
                    best_value = val
                    best_move_local = move
                alpha = max(alpha, best_value)
                if alpha >= beta:
                    break # Prune
        
        else: # Minimizing Player (Opponent)
            for i in range(6):
                if opp[i] > 0:
                    is_extra = (i + opp[i] == 6)
                    is_capture = False
                    if opp[i] == 1 and (5 - i) >= 0 and (5 - i) < 6 and you[5 - i] > 0:
                        is_capture = True
                    
                    score_priority = 0
                    if is_extra: score_priority += 100
                    if is_capture: score_priority += 50
                    
                    moves.append((i, score_priority))
            
            moves.sort(key=lambda x: x[1], reverse=True) # Higher is better for them too? 
            # Actually, from our perspective, we want to evaluate their best moves (to minimize our result).
            # They will play their best moves. 
            # So sorting helps pruning.
            
            for move, _ in moves:
                y_new, o_new, extra = simulate_move(you, opp, move, 1)
                if y_new is None: continue
                
                if extra:
                    val = ab_search(y_new, o_new, depth - 1, alpha, beta, False)
                else:
                    val = ab_search(y_new, o_new, depth - 1, alpha, beta, True)
                
                if val < best_value:
                    best_value = val
                    # Don't need best_move for minimizing player in recursion
                beta = min(beta, best_value)
                if beta <= alpha:
                    break # Prune

        # Store in TT
        flag = 0
        if best_value <= alpha: flag = 2 # Upper bound
        elif best_value >= beta: flag = 1 # Lower bound
        set_tt_entry(you_t, opp_t, depth, best_value, flag, best_move_local)
        
        if root:
            return best_move_local
        return best_value

    # --- Main Execution Loop ---
    
    # 1. Immediate Win/Loss/Draw Check
    # If we can end the game or force a win immediately?
    
    # 2. Iterative Deepening
    best_move = -1
    start_time = 0 # We can't import time, but we can assume standard python time works if allowed? 
    # "You may use any standard Python imports". Yes, time is standard.
    import time
    start_time = time.time()
    
    # Heuristic greedy check for instant win/extra turn
    # Check for moves that land in store (extra turn) or clear board
    # Priority 1: Land in store (Immediate extra turn)
    candidates = []
    for i in range(6):
        if you[i] > 0:
            if sum(you[:6]) == you[i]: # Last seed clears board
                return i
            if i + you[i] == 6: # Lands in store
                candidates.append(i)
    
    if candidates:
        # If we have an extra turn move, pick the best one based on simple look-ahead?
        # Or just pick the one with most seeds (to bring them home).
        # Actually, extra turn moves are strong.
        # Let's do a quick shallow search on these candidates.
        best_extra_score = -float('inf')
        best_extra_move = candidates[0]
        # Simple eval of resulting state
        for m in candidates:
            y_new, o_new, _ = simulate_move(you, opp, m, 0)
            # Evaluate quickly
            # Since it's our turn again, we can count how many moves we have?
            # Or just eval function.
            sc = evaluate(y_new, o_new, 0)
            if sc > best_extra_score:
                best_extra_score = sc
                best_extra_move = m
        # If we have extra turn, we might win. 
        # Let's verify with ID.
        best_move = best_extra_move
        
    # Start ID
    # Max depth 20, but check time
    for depth in range(1, MAX_DEPTH + 1):
        if time.time() - start_time > TIME_LIMIT:
            break
        
        try:
            move = ab_search(you, opp, depth, -float('inf'), float('inf'), True, root=True)
            if move != -1:
                best_move = move
        except RecursionError:
            break
        except Exception:
            break
            
    return best_move
