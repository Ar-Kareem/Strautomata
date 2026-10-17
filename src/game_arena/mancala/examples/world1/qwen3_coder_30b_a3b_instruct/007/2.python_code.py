
def policy(you: list[int], opponent: list[int]) -> int:
    def simulate_move(house_index):
        # Simulate dropping seeds from house_index
        # Return (extra_turn, captures, new_you_store)
        n_seeds = you[house_index]
        if n_seeds == 0:
            return False, 0, 0
            
        # Make a copy to simulate
        you_copy = you[:]
        opponent_copy = opponent[:]
        you_copy[house_index] = 0
        
        # Place seeds
        seeds_placed = 0
        current_house = house_index + 1
        place_count = 0
        
        # Distribute the seeds
        while seeds_placed < n_seeds:
            # We are placing the next seed at current_house
            # For your houses (0-5) or store (6)
            if current_house <= 5:
                you_copy[current_house] += 1
                seeds_placed += 1
                place_count += 1
                # If we're done placing, check for special conditions
                if seeds_placed == n_seeds:
                    # Check for extra turn (last seed in your store)
                    if current_house == 6:
                        return True, 0, you_copy[6]
                    # Check for capture (last seed in your empty house with opposite containing seeds)
                    if you_copy[current_house] == 1:  # was empty before the drop
                        opposite_house = 5 - current_house
                        # If the opposite house is not empty
                        if opponent_copy[opposite_house] > 0:
                            # Collect seeds from both houses
                            captures = 1 + opponent_copy[opposite_house]
                            # Add to store
                            you_copy[6] += captures
                            # Clear the opponent's house
                            opponent_copy[opposite_house] = 0
                            # Clear the house we dropped into
                            you_copy[current_house] = 0
                            return False, captures, you_copy[6]
                    break  # End of distribution (we are done)
                # Move to next house in order
                current_house += 1
                # Don't let it wrap around
                if current_house > 5:  # If we went past your houses, go to store
                    current_house = 6
            elif current_house == 6:  # Store
                # Don't place in opponent's store!
                you_copy[current_house] += 1
                seeds_placed += 1
                place_count += 1
                if seeds_placed == n_seeds:
                    # Last seed is in store
                    return True, 0, you_copy[6]
                current_house = 0
            elif current_house <= 11:  # Opponent houses (0-5)
                # Place in opponent's house
                opponent_copy[current_house - 7] += 1  # -7 to convert to opponent index
                seeds_placed += 1
                place_count += 1
                if seeds_placed == n_seeds:
                    # Last seed is in opponent's house
                    # Check for capture
                    if you_copy[current_house - 7] == 0 and opponent_copy[current_house - 7] > 0:
                        # Could happen but this is only if it's already placed in an opponent's house
                        # Actually no, it's the position where final seed lands, it could be 0, but it's not your move...
                        pass
                    break  # We are placing seed in opponent's house and we finished
                current_house += 1
                if current_house == 7:  # Transition from opponent's to your houses
                    current_house = 0
            else:  # This shouldn't happen
                current_house = 0  # reset to beginning

        # Handle case where distribution loop continues (if seeds can go around)
        # Actually more careful approach:
        # Let's just simulate with simpler logic
        final_pos = (house_index + n_seeds) % 13
        # Adjust for the fact that we skip opponent's store
        if final_pos < 6:  # In your boxes (0-5)
            final_house = final_pos
        elif final_pos == 6:  # In your store
            return True, 0, you_copy[6]  # But we still need to simulate to properly calculate captures
        elif final_pos <= 12:  # In opponent's boxes
            final_house = final_pos - 7  # Convert 7-12 to 0-5 (opponent houses)
        
        # Simulate full drop for the final details
        # This is more complex; I'll simulate with careful step counting
        # Let's restart from scratch correctly
        # The problem is that we are using modular arithmetic but it is not that simple
        # due to the special skipping rule.
        # Let's recompute the position correctly by doing placement one by one:
        # Place each seed in sequence.
        you_pos = [] # Stores new positions for your houses 
        opponent_pos = [] # Stores new positions for opponent houses
        new_stores = [you_copy[6], opponent_copy[6]] # Store for you, then opponent
        
        # This is tricky to handle properly. Let's create a cleaner logic using index mapping
        # Let's make a function to simulate with proper indexing:
        
        you_sim = you[:]
        opp_sim = opponent[:]
        # Remove seeds from house_index
        seeds_to_drop = you_sim[house_index]
        you_sim[house_index] = 0
        
        # Place seeds in correct order
        current_index = house_index + 1
        seeds_placed = 0
        
        while seeds_placed < seeds_to_drop:
            # Place one more seed
            # Determine which player's section we are in:
            if current_index <= 5: # Your houses 0-5
                you_sim[current_index] += 1
                seeds_placed += 1
                if seeds_placed == seeds_to_drop:
                    # Last seed landed here
                    last_pos = current_index
                    break
                current_index += 1
            elif current_index == 6: # Your store (you[6])
                you_sim[current_index] += 1
                seeds_placed += 1
                if seeds_placed == seeds_to_drop:
                    # Last seed landed here (extra turn)
                    last_pos = 6
                    break
                current_index = 0
            elif current_index <= 12: # Opponent's house (7-12 become 0-5)
                # current_index is 7,8,9,10,11,12 -> opponent[0,1,2,3,4,5]
                opp_sim[current_index - 7] += 1
                seeds_placed += 1
                if seeds_placed == seeds_to_drop:
                    # Last seed landed here, 
                    last_pos = current_index  # Store as 7-12 for opponent
                    break
                current_index += 1
                if current_index == 13:  # Wrap around to 0 when 12 is full
                    current_index = 0
            elif current_index == 13:  # Wrap around
                current_index = 0
                
        # Check last_pos
        if last_pos == 6: # Extra turn
            return True, 0, you_sim[6]
        elif 0 <= last_pos <= 5:
            # If it landed in your house
            # Check for capture
            if you_sim[last_pos] == 1: # This seed was the only one placed, i.e., it was empty before
                # It's possible this was the only seed put there
                opposite_house = 5 - last_pos
                if opp_sim[opposite_house] > 0:
                    # Capture: move seeds to your store
                    total_captured = 1 + opp_sim[opposite_house]
                    you_sim[6] += total_captured
                    opp_sim[opposite_house] = 0
                    you_sim[last_pos] = 0  # clear the house
                    return False, total_captured, you_sim[6] 
            return False, 0, you_sim[6]  # No special
        else:  # Opponent's house (last_pos in 7-12)
            return False, 0, you_sim[6]  # Regular move

    # Try all possible moves, score them, and pick the best
    best_move = 0
    best_score = -1
    for i in range(6):
        if you[i] > 0:  # Legal move
            extra_turn, captures, store_gain = simulate_move(i)
            # Score this move
            score = 0
            if extra_turn:
                score += 1000  # High value for extra turn
            if captures > 0:
                score += 100  # Value for capture
            # Bonus for store_gain, if not capture
            if store_gain > 0 and captures == 0:
                score += 50
            # Penalize moves that leave opponent with good chance
            # Try to avoid moves that might help opponent (like emptying our side)
            # But be careful: we don't have access to opponent score directly
            
            # Prefer moves that do not leave many seeds in the house  
            # (less seeds left in the house suggests more moves ahead for opponent)
            if score > best_score:
                best_score = score
                best_move = i
    return best_move
