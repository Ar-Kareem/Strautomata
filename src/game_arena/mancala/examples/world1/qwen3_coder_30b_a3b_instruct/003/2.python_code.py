
def policy(you: list[int], opponent: list[int]) -> int:
    def simulate_move(house_idx):
        # Create copies to avoid mutating original data
        my_board = you[:]
        opp_board = opponent[:]
        
        # Number of seeds in the chosen house
        seeds = my_board[house_idx]
        if seeds == 0:
            return -1  # Invalid move
        
        # Empty the chosen house
        my_board[house_idx] = 0
        
        # Distribute seeds
        position = house_idx + 1  # Position to start dropping seeds
        seeds_placed = 0
        
        # We place one seed in each position until we run out of seeds
        while seeds_placed < seeds:
            # Wrap around the board (you, store, opponent, you)
            # positions you[0] to you[5], you[6], opponent[0] to opponent[5], you[0] to you[5] (maybe)
            # Different segments: 
            # 1. houses 0-5 (your own)
            # 2. your store (index 6) 
            # 3. opponent houses 0-5
            # 4. your houses 0-5 (again - but we skip the opponent's store)
            
            # In this full cycle, we have 6 your houses, 1 your store, 6 opponent houses
            # For now, we'll simulate with the natural wraparound
            # Use modular arithmetic appropriately
            
            # Determine position to drop
            if position < 6:
                # Our own houses 0..5
                house_pos = position  
                my_board[house_pos] += 1
            elif position == 6:
                # Our store
                my_board[6] += 1
            else:
                # Opponent's houses: 0..5
                opp_house_idx = position - 7 
                opp_board[opp_house_idx] += 1
            
            # Move to next position (circular)
            position = (position + 1) % 13
            seeds_placed += 1
        
        # Determine where the last seed was placed
        # We start with position = house_idx + 1  
        # With `seeds` drops: final position is (house_idx + 1 + seeds - 1) % 13 = (house_idx + seeds) % 13
        final_pos = (house_idx + seeds) % 13
        
        extra_turn = False
        capture = False
        captured_seeds = 0
        new_store_seeds = 0
        
        # Check for extra turn: last seed lands in store (position 6)  
        if final_pos == 6:
            extra_turn = True
            
        # Check for capture
        # Last seed drops in one of our houses (0-5)
        if final_pos < 6:
            last_house = final_pos
            # If last house was empty before and corresponding opponent house has seeds
            if my_board[last_house] == 1:  # only one seed (was empty before we added 1)
                opp_mirror = 5 - last_house
                if opp_board[opp_mirror] > 0:
                    capture = True
                    captured_seeds = opp_board[opp_mirror] + 1  # the 1 dropped in, plus opponent's seeds
        elif final_pos == 6:
            # It went in our store; no capture possible
            pass
        else:
            # Ends in opponent's house (index: final_pos - 7)
            # Not a capture situation for our side
            pass

        # Compute score of this move
        score = 0
        # If it gives extra turn
        if extra_turn:
            score += 20
        # Add rewards for captures  
        if capture:
            score += captured_seeds * 10  # capture value is a multiple of seeds captured 
        # It's hard to give value to store for store at an intermediate phase
        # but let's simply consider if seeds end up in store (we want it to happen)
        # For now we just weight other factors
        
        # Don't give too big a penalty for placing seeds in opponent's houses
        # in many situations it's unavoidable - just not prefer it
        # Let's not add a big penalty for many opponent houses - instead consider 
        # the ratio of total seeds going to opponent vs you. But that's be complicated
        
        # A very simple valuation then
        return score
    
    # Choose the best legal move
    best_move = -1
    best_score = -1
    
    for i in range(6):
        if you[i] > 0:  # Legal move 
            score = simulate_move(i)
            if score > best_score:
                best_score = score
                best_move = i
    
    return best_move
