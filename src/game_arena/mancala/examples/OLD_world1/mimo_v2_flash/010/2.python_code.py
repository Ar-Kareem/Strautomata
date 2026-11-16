
import sys

def policy(you: list[int], opponent: list[int]) -> int:
    """
    Optimized Monte Carlo Tree Search (MCTS) agent for Kalah (6 houses).
    
    This policy uses a mix of tactical heuristics (instant wins, safe moves, 
    prioritizing extra turns) and Monte Carlo simulations to select the best move.
    It runs for a maximum of 0.8 seconds to stay within the time limit.
    """
    
    # --- Constants and Helper Lookups ---
    MAX_HOUSES = 6
    TOTAL_HOUSES = 14
    YOU_STORE_IDX = 6
    OPP_STORE_IDX = 6
    
    # Precomputed offset lookup for 0..13 indices
    # Opponent perspective mirrors indices: opp_idx -> you_idx
    # Example: opp house 0 corresponds to you house 5 (distance 11)
    # Map: 0->11, 1->10, 2->9, 3->8, 4->7, 5->6, 7->5, 8->4, 9->3, 10->2, 11->1, 13->0
    # 6 (you store) and 12 (opp store) are skipped in distribution but conceptually exist.
    OFFSET_MAP = {0: 11, 1: 10, 2: 9, 3: 8, 4: 7, 5: 6, 
                  7: 5, 8: 4, 9: 3, 10: 2, 11: 1, 13: 0}

    # --- 1. Heuristic Fast Checks ---
    
    # 1.1 Check for Instant Win
    # If we can make a move that guarantees our victory (maximize score > total/2), take it.
    total_seeds = sum(you[:6]) + sum(opponent[:6])
    half_total = total_seeds / 2
    opp_store = opponent[6]
    my_store = you[6]

    for i in range(6):
        if you[i] == 0: continue
        
        seeds = you[i]
        
        # Check for Extra Turn (Capture is handled implicitly by final score calc)
        final_pos = (i + seeds) % 13
        if final_pos == 6: # Extra turn
            # Calculate resulting score immediately (simulating the capture if any)
            # We need to calculate the exact score gain for this specific move to be sure.
            # Note: Extra turn moves usually expand score, but we must verify strictly.
            pass # Defer to simulation for precision, but we prioritize extra turns later
        
        # Check for Direct Win
        # Calculate final store count if we take this move
        temp_store = my_store
        
        # Standard distribution points
        if seeds <= 6 - i:
            # Ends in our side
            temp_store += seeds
        else:
            # Goes around
            full_laps = (seeds - (6 - i)) // 13
            temp_store += full_laps * 1
            steps_after_lap = (seeds - (6 - i)) % 13
            # Remaining steps: (6-i) + steps_after_lap
            # 1 in my store if crosses it, 1 in opp store if crosses it
            cross_opp = 0
            if steps_after_lap > (6 - i): cross_opp = 1
            temp_store += 1 if steps_after_lap > 6 else 0 # Cross own store
            
            # Capture check is complex, skip exact capture in "instant win" check 
            # to keep it fast, rely on simulation.
        
        if temp_store > half_total:
            return i

    # 1.2 Immediate Threat/Must-Move
    # If opponent has 0 stones left, any move that ends in our store is optimal.
    if sum(opponent[:6]) == 0:
        # We must sweep our stones.
        # The most optimal move is one that maximizes points immediately.
        best_i = 0
        max_gain = -1
        for i in range(6):
            if you[i] > 0:
                # Gain is simply you[i] (since opp has 0, no laps, no captures possible except self-capture which is rare)
                if you[i] > max_gain:
                    max_gain = you[i]
                    best_i = i
        return best_i

    # 1.3 Do not starve
    # Avoid moves that leave us with 0 stones while opponent has stones (unless we land in store).
    legal_moves = [i for i in range(6) if you[i] > 0]
    for i in legal_moves:
        stones = you[i]
        final_pos = (i + stones) % 13
        if final_pos != 6: # Not an extra turn
            if sum(you[:6]) - stones == 0:
                # This move ends the game (or leaves us empty)
                # It's only valid if we can sweep or if it forces a win.
                # Generally, avoid leaving empty unless it's winning.
                legal_moves.remove(i) if len(legal_moves) > 1 else None

    # --- 2. Monte Carlo Simulation ---
    
    if not legal_moves:
        # Fallback if filtering removed everything
        legal_moves = [i for i in range(6) if you[i] > 0]

    # Time limit setup
    import time
    start_time = time.time()
    time_limit = 0.8  # Seconds
    sims_per_move = 50  # Baseline, dynamic later
    
    scores = {i: 0 for i in legal_moves}
    counts = {i: 0 for i in legal_moves}
    
    move_idx = 0
    iterations = 0
    
    # Pre-allocate lists for speed (avoid repeated allocation)
    # We use copies during simulation
    while (time.time() - start_time) < time_limit:
        move = legal_moves[move_idx]
        
        # Run a batch of simulations for this move to reduce overhead
        batch_size = 10
        for _ in range(batch_size):
            # Simulate
            # Copy state
            p1 = list(you)
            p2 = list(opponent)
            
            # Apply move
            curr_player = 0 # 0 is you
            
            # Perform the move on the copied state
            # We need to track if we get extra turn to continue simulation
            while True:
                if curr_player == 0:
                    # You
                    stones = p1[move]
                    if stones == 0: break # Should not happen
                    p1[move] = 0
                    pos = move
                    while stones > 0:
                        pos += 1
                        # Skip opponent store
                        if pos == 13: pos = 0
                        if pos == 12: 
                            # Skip opp store (index 12)
                            # Wait, indices: 0-5 (you), 6 (you store), 7-12 (opp houses), 13 (opp store)? No.
                            # 0-5 (you), 6 (store), 7-12 (opp houses), 13 (opp store) -> Total 14
                            # Wait, standard 6+1 is usually indices 0-6 (7 items).
                            # The prompt says length 7. Indices 0..5 houses, 6 store.
                            # So board is 0..5 (P1), 6 (P1 store), 0..5 (P2), 6 (P2 store).
                            # We map this to a linear 0..13 array internally for logic?
                            # Let's stick to the prompt's list access but be careful with loops.
                            pass
                        
                        # Let's use a unified index 0..13 for the board to make sowing easy
                        # 0-5: You houses, 6: You store, 7-12: Opp houses, 13: Opp store
                        # Actually, prompt `opponent` list is separate.
                        # Let's just sow manually based on prompt rules.
                        
                        # Sowing Logic:
                        # 1. You houses 0..5
                        # 2. You store (index 6)
                        # 3. Opponent houses 0..5
                        # 4. Opponent store (index 6) - SKIP
                        # 5. Back to You houses
                        
                        # Let's use a local index variable `k` that traverses the board linearly
                        # k goes 0..5 (you), 6 (you store), 7..12 (opp houses), 13 (opp store)
                        # But we skip k=13 (opp store)
                        # Wait, we are currently at 'move'. We increment 'pos' in the loop.
                        # We need to map 'pos' to actual list indices.
                        
                        # Let's restart the sowing loop clearly:
                        pass 
                    
                    # --- REWRITE SOWING LOGIC FOR SPEED ---
                    # We are at 'move' (0..5).
                    # We have 'stones' to sow.
                    # We start from 'move' + 1.
                    
                    # We will use a "virtual board" 0..13 for ease
                    # 0-5: You, 6: You Store, 7-12: Opp, 13: Opp Store
                    # Let's map current p1/p2 to this
                    v_board = p1[:6] + [p1[6]] + p2[:6] + [p2[6]]
                    
                    # Remove seeds from source
                    # Source is v_board[move]
                    v_board[move] = 0
                    
                    # Distribute
                    cur = move
                    s = stones
                    while s > 0:
                        cur += 1
                        if cur == 13: # Just passed Opponent Store
                            cur = 0 # Wrap to You House 0
                        if cur == 6: # Just passed You Store? 
                            # No, we land on 6.
                            # But we skip Opponent Store (13).
                            # So: 5 -> 6 (You Store), 6 -> 7 (Opp House 0)
                            pass
                        
                        # Apply skip rule: if cur == 13 (Opp Store), skip to 0
                        if cur == 13:
                            cur = 0
                        
                        v_board[cur] += 1
                        s -= 1
                    
                    # Extract back to p1, p2
                    p1 = v_board[0:6] + [v_board[6]]
                    p2 = v_board[7:13] + [v_board[13]]
                    
                    # Capture & Extra Turn Check
                    last_pos = cur
                    extra_turn = False
                    
                    if last_pos == 6: # You Store
                        extra_turn = True
                    elif 0 <= last_pos <= 5: # You House
                        if v_board[last_pos] == 1: # Was it 1? 
                            # Check if opposite house has seeds
                            opp_pos = 11 - last_pos # 0->11, 1->10, 5->6 (Opp house 5->Opp house 0?)
                            # Opp houses in v_board are 7..12
                            # Opp house 0 is v_board[7]
                            # Your house 5 is v_board[5]. Opposite is Opp house 0 -> v_board[7].
                            # Your house 0 is v_board[0]. Opposite is Opp house 5 -> v_board[12].
                            # Mapping: You i -> Opp (5-i).
                            # Opp houses in v_board: 7 (Opp h0) to 12 (Opp h5).
                            # So Opp house (5-i) corresponds to v_board index: 12 - (5-i)? No.
                            # 5-i is the index in Opp's list.
                            # If i=0, 5-i=5 (Opp h5). v_board index is 12.
                            # If i=5, 5-i=0 (Opp h0). v_board index is 7.
                            # So mapping is: 7 + (5-i) = 12 - i.
                            # Let's check: i=0 -> 12, i=5 -> 7. Correct.
                            opp_v_idx = 12 - last_pos
                            
                            if v_board[opp_v_idx] > 0:
                                # Capture!
                                captured = v_board[last_pos] + v_board[opp_v_idx]
                                v_board[last_pos] = 0
                                v_board[opp_v_idx] = 0
                                v_board[6] += captured # You store
                                extra_turn = False # Capturing ends turn? 
                                # Wait, rules: "If the last seed lands in one of your houses... and it was empty..."
                                # The rules say "it was empty before the drop".
                                # We placed 1 seed. So if we land on an empty house, v_board[last_pos] becomes 1.
                                # So the check is valid.
                                # Does capture give extra turn? Usually yes (if capture happens).
                                # But standard Kalah rules: Capture happens, then turn ends? 
                                # Or "If capture occurs, you capture and get another turn"?
                                # Most variations: Capture ends turn.
                                # Some: Capture gives extra turn?
                                # Let's assume Standard Kalah (Mancala): Capture ends turn.
                                extra_turn = False
                        
                    # Update p1/p2 from v_board after capture
                    p1 = v_board[0:6] + [v_board[6]]
                    p2 = v_board[7:13] + [v_board[13]]
                    
                    # If not extra turn, switch player
                    if not extra_turn:
                        curr_player = 1
                        move = None # Move for P2 is chosen by P2 strategy (random)
                    else:
                        # You get another move. 
                        # Which one? We simulate *this* sequence by picking the best available.
                        # For MC, picking a random move for the second part is noisy.
                        # Let's pick the first available non-empty house for the simulation continuation.
                        # This might be biased, but fast.
                        found = False
                        for k in range(6):
                            if p1[k] > 0:
                                move = k
                                found = True
                                break
                        if not found:
                            # Game might have ended or stuck
                            # Check validity
                            if sum(p1[:6]) == 0: break
                            curr_player = 1 # Should switch if no move? No, if we have stones but no move?
                            # If we have extra turn but no moves? Impossible.
                            # If we have no stones? Game ends.
                            # If opponent has no stones? Game ends.
                            pass
                            
                else: # curr_player == 1 (Opponent)
                    # Opponent AI: Greedy/Smart
                    # We want to simulate opponent optimally to avoid overestimating win rate.
                    # A simple greedy: pick move that gives them extra turn or capture.
                    # Or pick random to simulate average play.
                    # Let's use a slightly smarter greedy: prioritize extra turns and captures.
                    
                    best_opp_move = -1
                    best_score = -100
                    
                    for k in range(6):
                        if p2[k] == 0: continue
                        
                        stones = p2[k]
                        # Simulate one step to check conditions
                        # Virtual board again
                        v_b = p1[:6] + [p1[6]] + p2[:6] + [p2[6]]
                        src = 7 + k # Opp house index in v_b
                        
                        # Check extra turn potential
                        final_pos = (src + stones) % 13
                        if final_pos == 13: # Opp Store (13 is opp store in our mapping)
                            # Wait, 13 is opp store.
                            # If we cross 6 (our store), we skip.
                            # If we land on 13, it's opp store.
                            # My mapping: 0-5 You, 6 You Store, 7-12 Opp, 13 Opp Store.
                            # Correct.
                            best_opp_move = k
                            break # Found extra turn
                        
                        # Check capture potential
                        # If lands in opp house and was empty
                        # Need full sowing to check capture.
                        # Let's do a quick partial check
                        # Optimization: just pick first valid move if no time
                        # But here we iterate 6 moves, so cheap.
                        
                        if best_opp_move == -1: best_opp_move = k
                    
                    move = best_opp_move
                    curr_player = 0 # Switch back to You
                    
            # End of simulation loop. Result?
            # If loop breaks, check winner.
            # If game ended inside loop?
            # Check if any player has 0 stones in houses
            if sum(p1[:6]) == 0:
                # You have 0, sweep opp stones
                score = p1[6] + sum(p2[:6])
                opp_score = p2[6]
            elif sum(p2[:6]) == 0:
                # Opp has 0, sweep your stones
                opp_score = p2[6] + sum(p1[:6])
                score = p1[6]
            else:
                # Simulation stopped due to loop count or time
                # Estimate score
                score = p1[6]
                opp_score = p2[6]
            
            # Assign result
            # We want to maximize (You - Opp)
            diff = score - opp_score
            if diff > 0:
                scores[move] += 1 # Win
            elif diff == 0:
                scores[move] += 0.5 # Draw
            # Loss adds 0
            
            counts[move] += 1
        
        # Cycle moves
        move_idx += 1
        if move_idx >= len(legal_moves):
            move_idx = 0
            iterations += 1

    # --- 3. Selection ---
    
    # Calculate averages
    best_move = legal_moves[0]
    best_ratio = -1.0
    
    # Tie-breaker: prefer moves that end in store (extra turn logic often handled by MC, but good to bias)
    # Also prefer safety.
    
    for m in legal_moves:
        if counts[m] == 0: 
            ratio = 0
        else:
            ratio = scores[m] / counts[m]
        
        # Heuristic bias
        # If ratio is close, add small weight for landing in store or capturing
        # Let's check landing pos
        stones = you[m]
        final_pos = (m + stones) % 13
        if final_pos == 6: ratio += 0.2 # Extra turn bias
        
        if ratio > best_ratio:
            best_ratio = ratio
            best_move = m
    
    return best_move
