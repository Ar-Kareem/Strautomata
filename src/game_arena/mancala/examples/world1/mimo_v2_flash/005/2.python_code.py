
def policy(you: list[int], opponent: list[int]) -> int:
    """
    Kalah AI Policy:
    1. Prioritize landing in the store (extra turn).
    2. Prioritize captures (landing in empty house with opponent seeds opposite).
    3. Prioritize moves with the longest reach (progressive sowing).
    """
    
    def simulate_sow(board_you, board_opp, start_index):
        """
        Returns (final_index, landed_in_store, captured_amount, is_capture_move)
        final_index: The house index where the last seed lands (0-5 for houses, 6 for store).
        landed_in_store: True if the last seed landed in the player's store.
        captured_amount: Amount of seeds added to store during capture (0 if no capture).
        is_capture_move: True if the move resulted in a capture.
        """
        seeds = board_you[start_index]
        current_pos = start_index
        temp_you = list(board_you)
        temp_opp = list(board_opp)
        
        # Remove seeds from source (do this virtually or on a copy)
        # Note: In simulation, we work on a copy.
        temp_you[start_index] = 0
        
        # Sowing loop
        for _ in range(seeds):
            current_pos += 1
            
            # Wrap around logic
            # If we pass index 5 (last house), we go to index 6 (store)
            # If we pass index 6 (store), we go to index 0 (opponent's first house)
            
            if current_pos == 6:
                # Landing in Player's Store
                temp_you[6] += 1
                final_pos = 6
                continue
            
            if current_pos == 7:
                # Wrapped around to Opponent's houses
                current_pos = 0
            
            if current_pos < 6:
                # Landing in Opponent's House
                temp_opp[current_pos] += 1
                final_pos = current_pos # 0-5 indicates opponent house
            else:
                # This should technically not happen given the logic above
                # but keeping for safety.
                pass

        # Determine results
        landed_in_store = (final_pos == 6)
        
        # Capture Logic
        # Only valid if last seed landed in YOUR house (0-5) and was empty before drop
        # Note: final_pos 0-5 here refers to the index on the board being interacted with.
        # However, 'final_pos' in the loop tracks the *relative* position. 
        # We need to map 'final_pos' back to the actual board array indices.
        
        # Correction: The loop logic above produced 'final_pos' as 0-5 for opponent houses
        # or 6 for store. It did not track landing in *your* houses because the loop
        # sequence for 13 seeds (standard board) is:
        # You[0..5] -> You[6] -> Opp[0..5] -> You[0..5]...
        
        # Let's refine the simulation to be exact to the prompt's rules:
        # 1. you[i+1]...you[5], then you[6], then opponent[0]...opponent[5], then you[0]...
        
        # Re-implementing simplified simulation for accuracy:
        seeds = board_you[start_index]
        pos = start_index
        temp_you = list(board_you)
        temp_opp = list(board_opp)
        temp_you[start_index] = 0
        
        landed_in_store = False
        capture_performed = False
        
        for s in range(seeds):
            pos += 1
            
            # Check for store (index 6)
            if pos == 6:
                temp_you[6] += 1
                if s == seeds - 1:
                    landed_in_store = True
                continue
            
            # Check for wrap to opponent (index 7 -> 0)
            if pos == 7:
                pos = 0
            
            if pos < 6:
                # Opponent side
                temp_opp[pos] += 1
            else:
                # This block is unreachable because pos resets to 0 at 7
                pass
        
        # To correctly identify capture, we need to know the final landing spot
        # relative to the original board configuration.
        # The variable 'pos' at the end of the loop represents the index 
        # of the last seed dropped, relative to opponent's start (0).
        # To get the board index:
        # The sequence is: You[Start...5], You[6], Opp[0...5], You[0...Start-1]
        
        # Let's calculate the final board index cleanly:
        seeds = board_you[start_index]
        
        # Total positions in play: 14 (0..13)
        # Player houses: 0..5 (Indices 0..5)
        # Player Store: 6 (Index 6)
        # Opponent houses: 7..12 (Indices 0..5 relative to opponent)
        # Opponent Store: 13 (Index 6 relative to opponent) - SKIPPED
        
        # Move sequence logic:
        # Start at index 'start_index' (0..5).
        # The seeds are removed.
        # We distribute 1 by 1.
        
        # Current absolute index (0..12, skipping opponent store 13)
        # Mapping:
        # 0-5: You
        # 6: You Store
        # 7-12: Opponent
        # 13: Opponent Store (Skip)
        
        current_abs = start_index
        
        for _ in range(seeds):
            # Increment
            current_abs += 1
            
            # Wrap around logic for absolute index (0..13)
            if current_abs == 14:
                current_abs = 0
            
            # Skip Opponent Store (13)
            if current_abs == 13:
                current_abs = 0 # Jump to 0 (You[0])
            
            # Now current_abs is the target slot (0..12)
            
            # If this is the last seed, check conditions
            if _ == seeds - 1:
                final_abs = current_abs
                
                # Check Store Landing
                if final_abs == 6:
                    landed_in_store = True
                    return final_abs, landed_in_store, 0, False
                
                # Check Capture
                # Condition: Last seed lands in YOUR house (0..5)
                # AND that house was EMPTY before the drop
                # AND opponent house (5 - index) has seeds
                
                if final_abs <= 5:
                    # It's a house on your side
                    if board_you[final_abs] == 0: # Was empty before drop
                        opp_idx = 5 - final_abs
                        if board_opp[opp_idx] > 0:
                            # Capture occurs
                            capture_performed = True
                            return final_abs, landed_in_store, (1 + board_opp[opp_idx]), True
        
        # If loop finishes without return (no store, no capture)
        return final_abs, landed_in_store, 0, False

    best_move = -1
    best_score = -float('inf')
    
    # Iterate through all legal moves
    for i in range(6):
        if you[i] == 0:
            continue
            
        # Simulate the move
        final_pos, is_store, capture_amt, is_capture = simulate_sow(you, opponent, i)
        
        score = 0
        
        # 1. Priority: Extra Turn (Store Landing)
        if is_store:
            # Always take a free turn immediately
            return i
        
        # 2. Priority: Capture
        if is_capture:
            # We prefer captures. 
            # Give a high base score + the amount captured.
            # Ensure we don't suicide (leave own side empty) if possible,
            # but generally captures are good.
            
            # Check for suicide: If this move leaves all houses empty?
            # It's a capture, so we added 1 seed + opponent seeds.
            # We remove seeds from 'i'. 
            # If all other houses are 0 and 'i' had 1 seed, we empty our side.
            # However, Kalah rules usually say if you capture and leave yourself empty,
            # opponent captures remaining. It's situational.
            # We will take the capture anyway as it's a strong mechanic.
            
            score = 1000 + capture_amt
            
            # Slight preference for captures closer to store (easier to protect)
            # or that open up lanes.
            if final_pos > 2: score += 10 
            
            if score > best_score:
                best_score = score
                best_move = i
            continue # Don't overwrite a capture with a normal move
            
        # 3. Priority: Progressive Sowing (Reach)
        # Calculate how far the seeds travel.
        # We want to reach the store or wrap around to hit opponent seeds.
        seeds = you[i]
        
        # Calculate effective distance to store
        # Distance to store from index i is (6 - i)
        dist_to_store = 6 - i
        
        if seeds >= dist_to_store:
            # Can reach store (but didn't land there, so overshot)
            # This is a "near miss" which is good because it circulates seeds deep.
            score = 500 + seeds
        else:
            # Didn't reach store. 
            # Calculate how far it went.
            # We prefer moving seeds to the right (higher indices) 
            # because they are closer to the store for future moves.
            score = 100 + (i + seeds)
            
        if score > best_score:
            best_score = score
            best_move = i

    # Fallback (should not happen if legal moves exist)
    if best_move == -1:
        for i in range(6):
            if you[i] > 0:
                return i
                
    return best_move
