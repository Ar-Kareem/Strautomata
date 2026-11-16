
def policy(you: list[int], opponent: list[int]) -> int:
    def simulate_move(i, you_state, opponent_state):
        # Make a copy to avoid modifying originals
        you_copy = you_state[:]
        opponent_copy = opponent_state[:]
        
        # Get seeds from house i
        seeds = you_copy[i]
        you_copy[i] = 0
        
        # Distribute seeds
        # Start position is i + 1 (following the rules)
        pos = i + 1
        remaining = seeds
        
        # Distribute in the pattern: your houses (0-5), your store, opponent houses (0-5), back to your houses (0-5)
        # We need to be careful about wrap-around and skipping opponent store (index 6)
        
        while remaining > 0:
            # Determine next position  
            if pos == 7:  # You store (index 6)
                if pos == len(you_copy) - 1:  # This is your store (index 6)
                    opponent_copy[0] += 1
                else:
                    you_copy[0] += 1
                pos = 0
                remaining -= 1
                continue
                
            # You store reached, switch to opponent
            if pos == 6:  # You're at your store (index 6)
                # This is not a valid starting point for distribution
                # So if we hit this, it means the last move was from your store
                # But that would only happen if i == 6, but i is in 0-5
                # The logic in the rules suggests the actual distribution goes:
                # your houses [i+1 to 5] then your store [6] then opponent houses [0 to 5] then your houses [0 to 5], etc.
                # The real issue is how to simulate the loop properly.
                # If we're at pos=6, we actually need to start at opponent[0] (which is pos=0 in opponent houses)
                
                # Actually let me re-read the rules again.
                # Move from house[i] - remove seeds from it and distribute them one by one
                # 1. from i+1 to 5 (your other houses)
                # 2. Your store  (index 6)  
                # 3. Opponent house 0 to 5
                # 4. Your house 0 to 5 (and then possibly repeat)

                # When distributing from house 0, after 0 to 5, wrap to opponent 0, etc.
                
                # To get around the loop cleanly, I'll distribute seeds in sequence and compute position correctly
                pos = 0
                if pos <= 5:
                    you_copy[pos] += 1
                elif pos == 6:
                    you_copy[6] += 1
                elif pos <= 11:  # Opponent houses (6 to 11) -> 0 to 5
                    opponent_copy[pos - 7] += 1 
                # But to simulate correctly with position tracking, let's compute the full path:
                
                pos = 0  
                # This is getting complex - let me just simulate with proper indexing
                # If I'm at position i+1 and there are S seeds,
                # I'll place 1 seed to position i+1,
                # then to i+2, ..., to 5, then 6 (your store), 0, 1, ..., 5, 0, 1, ...
                # This is modular arithmetic, so I'll do it properly:
                
                # We are distributing the S seeds starting at position (i+1) which maps to:
                # If we go to pos in your houses [0 to 5], pos = (i+1 + seed_count) % 12 if seed_count >= 0
                # But there are two cases: if pos == 6, and we're going to opponent's houses

                # But let's simplify the approach: 
                # After removing seeds from your house i,
                # we distribute to positions: 
                # (i+1)%12, (i+2)%12, ..., up to (i+seeds)%12 
                # Special case for position 6 (your store): skip it for distribution but allow to land there.
                # Position mapping: 0 to 5 = your houses, 6 = your store, 7 to 11 = opponent houses (0 to 5)
                
                pos = (i + 1) % 12
                if pos == 6:
                    # Skip opponent store, go to 0
                    pos = 0
                
                # Actually let's re-read:  when seeds are placed from house i, we go:
                # i+1 to 5, then store, then 0-5, then 0-5...
                # So 12 positions total: 0-5 (your), 6 (store), 7-11 (opponent houses)
                # But if position > 11 we continue cycling
                # But the key is: when we go from i to i+1, i+2, ..., the positions are: 0 to 11 cycling

                # Simplified approach: 
                # Each seed goes to consecutive positions: (i+1) % 12, (i+2) % 12, ...
                # When it lands on 6, it goes to your store (we can't skip it, it's in the normal sequence)
                # But there's a special rule: we skip the opponent's store (index 12)  

                # Let me restart with correct understanding:
                # We start from house i (you[i] seeds) and move clockwise around the board
                # So seed 0 goes to house (i+1) % 12, seed 1 goes to (i+2) % 12, ...
                # Position mapping:
                # 0,1,2,3,4,5 -> your houses
                # 6            -> your store  
                # 7,8,9,10,11,12 -> opponent houses  
                # But we actually only have 7 positions each, so: 
                # 0,1,2,3,4,5 (your), 6 (your store), 7,8,9,10,11,12 (opponent) -> that's 13 positions
                # Actually, no, the standard Kalah board is 6 houses per player + 1 store for each.
                # So your board has 7 cells indexed 0-6 (0-5 = houses, 6 = store)
                # Opponent board also 7 cells indexed 0-6 
                # But in the simulation we're placing seeds across the board in a cycle
                # 0,1,2,3,4,5,6,7,8,9,10,11,12 = your 0-5, store 6, opponent 0-5  
                # So for 12 positions we can just use modulo 12
                # The special case is: 
                # - When we land on index 12, it should be treated as opponent store -> but our opponent store is at index 6.
                # I think the board in the simulated sequence is:
                # 0 1 2 3 4 5 6  7 8 9 10 11 12 (0 1 2 3 4 5) - your houses, your store, opponent houses
                # But we must ignore opponent's store in distribution 
                # So we are distributing across 12 slots: 0 1 2 3 4 5 6 7 8 9 10 11 
                # (0=house[0], 1=house[1], ..., 5=house[5], 6=store, 7=opponent_house[0], 8=opponent_house[1], ..., 11=opponent_house[5])
                # Note: opponent's store is at index 12 (7+5 = 12).  
                # That is, if we have 12 positions for the board.
                # So, when we land at position 12, that is the opponent's store which we skip.
                # So we're placing seeds at positions 0-11, skipping 12 which is the opponent store.
                # When placing, we land on position (i+1+k) % 12 where k = 0 to seeds-1
                # But the game is a bit non-standard in the way it loops - maybe let me take it step by step.

                # Simpler implementation approach:
                # From house i, place seeds one by one clockwise around the loop.
                # The sequence is: for k from 0 to seeds-1: place at ((i+1+k) % 12)  
                # But index 6 (your store) and index 0 (first house of opponent) need some special care.
                # Wait - I read it wrong.
                
                # Let me read this one more time:
                # "The rules state: the house you move from has its seeds removed, and then distributed in sequence:
                # 1. your houses i+1 through 5  
                # 2. your store (index 6) 
                # 3. opponent houses 0 through 5
                # 4. your houses 0 through 5
                # ..." repeating as needed (which is implied)
                
                # Okay, now I understand the pattern. 
                # So:
                # from house i (you[i]), we place S seeds (where S = you[i])
                # The locations are (using 0-based):
                # house i+1, i+2, ..., 5, store(6), 0, 1, ..., 5, 0, 1, ..., 5, 0, ..., etc. 
                # The key is that this "distribution" continues for S seeds
                # The tricky part is the cycling when it reaches 5, then 6, then 0, 1, 2, 3, 4, 5, 0, ...
                # We need special handling for store index 6

                # But there's a problem: we have 7 positions for each player: 0 1 2 3 4 5 6
                # So in the final board, if we have positions from 0 to 12:
                # Index 0=house0, 1=house1, ..., 5=house5, 6=your store, 7=opponent house0, 8=opponent house1, ..., 12=opponent house5
                # We are placing seeds in that circular fashion but must not skip or include the opponent's store (index 12).
                # But if opponent is index 12, we are in opponent's side.
                # If the last seed lands on index 12, that's opponent.store, which we should not place any seeds there.
                
                # Simpler idea: 
                # The final board is 13 positions:
                # 0 1 2 3 4 5 6 7 8 9 10 11 12
                # Your houses: 0 to 5 (6 seeds total)  
                # Your store:     6 (1 seed)
                # Opponent houses: 7 to 12 (6 seeds)
                # If we land on 12, that is opposite of house 5 (the house opposite in terms of board),
                # which is house 0 of opponent (which should be at index 7).  
                # But this doesn't match my earlier understanding.

                # Let's go back to the rule as written:
                # The positions we distribute to are: 
                # [i+1, i+2, ..., 5] + [6] + [0, 1, ..., 5] + [0, 1, ..., 5] ... as long as there are seeds
                # This is an intuitive way it might work. 
                # So the cycle is:
                # 1. your houses (i+1) to 5  
                # 2. your store (6)  
                # 3. opponent houses (0 to 5) 
                # 4. your houses (0 to 5) again (and repeat)
                # This is easier with index tracking.

                # Now let's simulate step by step carefully:
                # 1. You have you[i] seeds to place
                # 2. Start at position (i+1)
                # 3. Loop through all seeds and place on one position at a time (0 to seeds)
                # 4. The logic for the position is:
                #    a. If it's 6, that's your store
                #    b. If it's 7-12, that's the opponent house (7 = opponent house 0, 8 = opponent house 1, etc)
                #    c. If it's 0-5, that's your house
                #    d. But this makes more sense for a 13-index board, not a 12-index. 
                #    e. Let's stick with 12 positions (index 0-11) and interpret positions as:
                #       0,1,2,3,4,5 = your houses  
                #       6 = your store (we're skipping 6) 
                #       7,8,9,10,11 = opponent houses (opponent index 0 is 7, opponent index 1 is 8, etc)
                #       But 12-13 are not needed as the sequence of 0-11 repeats and covers all.
                #       This is wrong interpretation, let me start with simpler.

                # Let's think: if we start at i=0 and place 1 seed, it goes to i+1=1  
                # If we have 6 seeds from house 0, they go to:  
                # house 1, house 2, house 3, house 4, house 5, store
                # So 0 to 11 represent:
                # 0 1 2 3 4 5 6 7 8 9 10 11  
                # houses 0 1 2 3 4 5 store opponent0 opponent1 opponent2 opponent3 opponent4 opponent5 
                # 12 positions total
                #  But the distribution goes:
                # house (i+1) to 5
                # then store (6)  
                # then opponent 0 to 5 
                # then your 0 to 5, again...  

                # Let's simplify by doing a manual simulation:
                # We place 6 seeds from house 0, we have 0,1,2,3,4,5,6,7,8,9,10,11  
                # The seed goes to:
                # from seed k=0 to 5:
                # pos = (i+1+k) % 12 (this simulates going around and wrapping) 
                # But when pos=6, it's special because that's your store  
                
                # Actually let me not overthink.
                # I'll directly implement the move simulation with clear indexing:
                # The board is a 12 slot circular distribution:
                #  0,1,2,3,4,5 (you houses)  
                #  6 (your store - special) 
                #  7,8,9,10,11 (opponent houses)
                # But when simulating, for example, placing from house 0, we must go:
                # 0+1=1, 0+2=2, 0+3=3, 0+4=4, 0+5=5, 0+6=6, 0+7=7, ..., 0+11=11, then 0+12=0,...
                # The rule is:  
                # place seeds starting from position (i+1) 
                # and place each one to pos=(current_pos + 1) % 12   
                # but the last one we need to check for special behavior (capture, extra turn)
                # The last one to fall determines the rule action.

                # So I'll proceed with simulation:
                
                # Place seeds from i+1 to 5 first
                # Then store (6)
                # Then opponent side, then your side, etc.
                # I'll just implement the simple modular loop.
                
                # Reset pos
                pos = 0
                for seed_index in range(seeds):
                    # Distribute seed_number k to position (i+1+k) % 12  
                    pos = (i + 1 + seed_index) % 12
                    # Place the seed
                    if pos <= 5:
                        you_copy[pos] += 1
                    elif pos == 6:
                        you_copy[6] += 1
                    elif pos <= 11:
                        opponent_copy[pos - 7] += 1  # Opponent houses are position 7 to 11 -> 0 to 5
                    # No need to check pos >= 12, since pos is %12, it will be in 0 to 11

                # We placed all seeds, so pos holds the position of the last seed
                final_position = pos
                return you_copy, opponent_copy, final_position, seeds
            
        # Normal case: place seeds in a loop, skipping invalid positions
        # We are in the middle of placing, so we can distribute.
        for k in range(remaining):
            # Next position (after skipping 6 which is your store - no need to check here as it is part of the sequence)
            pos = (pos + 1) % 12
            
            # Special case: if we land on your store (pos=6), it should be allowed.
            # And it's a position in this cycle
            
            if pos < 6:
                you_copy[pos] += 1
            elif pos == 6: 
                you_copy[6] += 1  # your store
            elif pos <= 11:
                opponent_copy[pos - 7] += 1  # opponent houses at index [0 - 5]

        # The final position of last seed  
        # Final logic for where the seed lands:
        final_pos = (i + 1 + seeds - 1) % 12  # (i+1) + (seeds-1) = position of last seed
        return you_copy, opponent_copy, final_pos, seeds
                
    
    # Simplified version of move simulation - just distribute in the correct order without the overly complex modulo logic
    # The sequence of placing seeds is i+1, i+2, ..., i+seeds
    # but we must be careful:
    # - if i+1 to 5, that's all within your houses
    # - then goes to your store (index 6) if available, 
    # - then to opponent houses (0-5)
    # - then back to your houses (0-5) in a cycle
    
    def simulate_move_simple(i, you_state, opponent_state):
        you_copy = you_state[:] 
        opponent_copy = opponent_state[:]
        seeds = you_copy[i]
        you_copy[i] = 0

        # We'll simulate with position on a 12-slot board:
        # position: 0 1 2 3 4 5 6 7 8 9 10 11  
        # meaning:  house[0] .. house[5] store opponent[0] .. opponent[5] 
        # 0-5 are your houses, 6 is store, 7-11 are opponent houses
        # we simulate placing seeds on each position in turn

        pos = i + 1  # Start just after the house we picked
        for k in range(seeds):
            # Place one seed
            pos = (pos + k) % 12  # Position after k steps = (i+1 + k) 
            # That's not right. 
            # Let's say k=0: position (i+1) % 12  
            # k=1: position (i+2) % 12  
            # We'll keep a running position for clarity
            if k > 0:
                pos = (pos + 1) % 12  # Next seed after previous place (i+1 + k) % 12  

            # But it's easier just to calculate:
            current_pos = (i + 1 + k) % 12
            if current_pos <= 5:
                you_copy[current_pos] += 1
            elif current_pos == 6:
                you_copy[current_pos] += 1
            else:  # current_pos >= 7, <= 11  
                opponent_copy[current_pos - 7] += 1

        # Now we need to know the final position for the action:
        final_position = (i + 1 + seeds - 1) % 12
        
        return you_copy, opponent_copy, final_position, seeds

    # A much simpler and clearer simulation  
    def get_move_result(i, you_state, opponent_state):
        you_copy = you_state[:]
        opponent_copy = opponent_state[:]
        seeds = you_copy[i]
        you_copy[i] = 0
        
        # Positions in board sequence: 0 1 2 3 4 5 (you houses) 6 (your store) 7 8 9 10 11 (opponent houses)
        # For a move from house i (0-5)
        # we distribute seeds in sequence from position (i+1) to (i+seeds) % 12
        pos = (i + 1) % 12
        # Simulate placing each seed  
        for _ in range(seeds):
            # Place seed on current pos  
            if pos <= 5:
                you_copy[pos] += 1
            elif pos == 6:
                you_copy[pos] += 1  # your store
            else:  # pos >= 7
                opponent_copy[pos - 7] += 1  # opponent house
            # Next position
            pos = (pos + 1) % 12
            
        final_pos = (i + 1 + seeds - 1) % 12
        return you_copy, opponent_copy, final_pos
    
    # Heuristic to score a move
    def score_move(i, you_state, opponent_state):
        new_you, new_opponent, final_pos = get_move_result(i, you_state, opponent_state)
        
        # Score components: 
        # Extra turn if lands in your store
        extra_turn = 1 if final_pos == 6 else 0
        
        # Capture if lands in your empty house and opposite has seeds
        capture_seeds = 0
        if 0 <= final_pos <= 5 and new_you[final_pos] == 1 and new_opponent[5 - final_pos] > 0:
            # The capture rule: if final_pos is in your house (0-5) and was empty (so only 1 seed now) and the opposite house has seeds
            capture_seeds = 1 + new_opponent[5 - final_pos]  # 1 from final_pos + all from opposite
        
        # Store increase
        store_increase = new_you[6] - you_state[6]
        
        # Prefer capture over extra_turn
        if capture_seeds > 0:
            return capture_seeds * 100 + extra_turn * 10 + store_increase
        elif extra_turn > 0:
            return 100 + extra_turn * 10 + store_increase
        else:
            return store_increase
    
    # Find the best move
    best_move = -1
    best_score = -1
    
    # Iterate through all possible moves
    for i in range(6):
        if you[i] > 0:  # You have seeds in house i
            score = score_move(i, you, opponent)
            if score > best_score:
                best_score = score
                best_move = i
    
    return best_move
