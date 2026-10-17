
def policy(you: list[int], opponent: list[int]) -> int:
    def simulate_move(i, you_state, opponent_state):
        # Make a copy to avoid modifying the original
        you_copy = you_state[:]
        opponent_copy = opponent_state[:]
        
        seeds = you_copy[i]
        you_copy[i] = 0
        
        # Distribute seeds
        pos = i + 1
        while seeds > 0:
            # Skip opponent's store (index 6)
            if pos == 7:
                pos = 0
            if pos == 13:
                pos = 0
                
            # Check if we're at opponent's store
            if pos == 7:
                # Skip and continue to next position
                pos = 0
                continue
                
            # Check for opponent's store (we shouldn't distribute there)
            if pos == 13:
                # This means we've gone through all positions
                # Actually, let's do a better simulation
                # Distribute across 13 total positions (6 you, 1 you-store, 6 opponent)
                # So we cycle through: 0,1,2,3,4,5,6,0,1,2,3,4,5,0...
                pos = 0
                continue
            
            # For now, let's simulate the proper distribution logic:
            # we have 13 total positions (6 you houses + 1 you store + 6 opponent houses)
            # distribution order: you[0],you[1],you[2],you[3],you[4],you[5],you[6],opponent[0],opponent[1],opponent[2],opponent[3],opponent[4],opponent[5]
            # but we don't place in opponent[6] (their store)
            
            # The total positions: [0,1,2,3,4,5,6,0,1,2,3,4,5] (you's houses, you's store, opponent's houses)
            effective_pos = pos % 13
            if effective_pos <= 5:  # You house
                you_copy[effective_pos] += 1
            elif effective_pos == 6:  # Your store
                you_copy[6] += 1
            else:  # Opponent house
                opponent_copy[effective_pos - 7] += 1
            
            # Increment the next position (wrapping around)
            pos += 1
            seeds -= 1
            
        # Now handle capture condition
        # Last seed landed in your house (0-5)
        final_pos = (i + 1 + (you_state[i] - 1)) % 13  # This is a simplified way
        # Correct simulation for position: 
        # We start at i+1, and we have you[i] seeds to distribute
        # Last seed ends at position (i+1+you[i]-1) % 13
        final_pos = (i + you_state[i]) % 13
        extra_move = False
        
        if final_pos <= 5:  # Last seed in your house
            pos_in_your_house = final_pos
            if you_copy[pos_in_your_house] == 1 and pos_in_your_house != 6:  # It was 0 before (we just placed 1)
                if opponent_copy[5 - pos_in_your_house] > 0:  # Opposite house has seeds
                    captured = opponent_copy[5 - pos_in_your_house]
                    you_copy[6] += captured + 1  # Add the captured seeds and the last one
                    opponent_copy[5 - pos_in_your_house] = 0
                    you_copy[pos_in_your_house] = 0
        elif final_pos == 6:  # Last seed in your store
            extra_move = True
        elif final_pos >= 7:  # Last seed in opponent's house (pos=7 to 12)
            pos_in_opponent = final_pos - 7
            # Not a capture case or extra move in this branch
        
        return you_copy, opponent_copy, extra_move
    
    best_move = -1
    best_score = -1
    
    # Try all possible moves
    for i in range(6):
        if you[i] == 0:
            continue
            
        # Simulate the move
        new_you, new_opponent, extra = simulate_move(i, you, opponent)
        
        # Evaluate the result
        # Score is based on immediate benefits
        score = 0
        
        # Capture bonus
        # We can't easily detect captures here without more complex logic
        # Let's just check if the last seed was in our store (extra move)
        # or in our house with zero previous seeds and opponent has seeds there
        final_pos = (i + you[i]) % 13
        
        # Simplified scoring for now
        # Prefer moves that give extra moves
        if extra:
            score += 100
        
        # Prefer moves that give captures or increase your store
        # We'll evaluate how much your store increased
        score += (new_you[6] - you[6]) * 5
        
        # Prefer moves that increase your seed count in your houses and reduce opponent's
        # Add some heuristics for position in board
        # Prefer moves on higher-numbered houses 
        score += new_you[i] * 3  # Prefer moves where own house still has seeds
        
        # Prefer moves that reduce opponent house seeds
        # This is a simplified evaluation
        # We could compare total seeds in opponent houses, but let's keep simple
        if i == 0:  # Prefer houses that are not rightmost
            score += 1
        elif i == 1:
            score += 2
        elif i == 2:
            score += 3
        elif i == 3:
            score += 4
        elif i == 4:
            score += 5
        else:  # i == 5, prefer that it gives opportunities
            score += 6
            
        # Prefer moves that don't leave low-value seeds
        # But just avoid giving up too many seeds at least
        
        if score > best_score:
            best_score = score
            best_move = i
        
    # If no move is chosen, return 0
    if best_move == -1:
        for i in range(6):
            if you[i] > 0:
                return i
    return best_move
