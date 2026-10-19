
def policy(you: list[int], opponent: list[int]) -> int:
    # Try all possible moves and evaluate them
    best_move = 0
    best_score = float('-inf')
    
    for i in range(6):
        if you[i] == 0:
            continue
            
        # Make a copy of the state to simulate the move
        you_copy = you[:]
        opponent_copy = opponent[:]
        
        # Simulate the move
        seeds = you_copy[i]
        you_copy[i] = 0
        
        # Place seeds according to the rules
        pos = i + 1
        while seeds > 0:
            # Skip opponent's store
            if pos == 13:
                pos = 0
                
            # Determine which side we're on
            if pos < 6:
                # Your side
                opponent_copy[pos] = 0
                you_copy[pos] += 1
            elif pos == 6:
                # Your store
                you_copy[pos] += 1
            elif pos < 13:
                # Opponent's side
                you_copy[pos - 7] = 0
                opponent_copy[pos - 7] += 1
            else:
                # This shouldn't happen in normal flow
                pos = 0
                continue
                
            seeds -= 1
            pos += 1
            
        # Check if the last seed was placed in your store
        # If so, we get an extra move (for now just consider this a bonus)
        # Actually, let's track if it lands in your store
        landing_pos = (i + you[i] + 1) % 14
        if landing_pos == 6:
            # Extra move possible
            score = 1000
        else:
            # Evaluate based on immediate outcomes
            score = 0
            
            # Check for captures: last seed lands in one of your empty houses
            # The original house has (i+1) houses to the right, and then we might overshoot
            # In this case, it needs to be:
            # 1. Landing in your house (0-5)  
            # 2. That house was empty before the move
            # 3. And the opposite house has seeds

            # The actual landing index calculation
            landing_position = (i + you[i]) % 14
            
            if landing_position < 6 and landing_position != 6:
                if you_copy[landing_position] == 1 and you[i] > 0:
                    # Capture possible - check if the opposite house has seeds
                    opposite_house = 5 - landing_position
                    if opponent_copy[opposite_house] > 0:
                        # We capture seeds from opposite house and our house
                        score += 10 + opponent_copy[opposite_house]
                        
            # Bonus for increasing your store
            # And also punish moves that do not increase the number of seeds in your house
            score += you_copy[6]
            
            # Bonus for moving more seeds into later houses (lower priority)
            for j in range(6, -1, -1):
                if j == 0 and you_copy[0] > 0:
                    # Try to avoid emptying early houses
                    score -= you_copy[0]
                if j == 5 and you_copy[5] > 0:
                    score += you_copy[5]
                    
            # We want to encourage moves that puts seeds in later positions
            # Minimize the number of seeds in early positions to build continuity

    # We'll take a simpler heuristic approach
    # Prioritize moves that either:
    # 1. Provide extra turn
    # 2. Capture opponent's seeds
    # 3. Shift seeds to later houses (better continuity)
    
    # Let's be more careful
    for move in range(6):
        if you[move] == 0:
            continue
            
        # Just run simulation and judge effect on your store
        temp_you = you[:]
        temp_opponent = opponent[:]
        seeds = temp_you[move]
        temp_you[move] = 0
        
        pos = move + 1
        seeds_placed = 0
        
        # Move seeds along
        while seeds_placed < seeds:
            if pos == 13:
                pos = 0
                
            if pos == 6:
                # Your store
                temp_you[6] += 1
                
            elif pos < 6:
                # Your house
                temp_you[pos] += 1
                
            elif pos < 13:
                # Opponent's house
                temp_opponent[pos-7] += 1
                
            seeds_placed += 1
            pos += 1
            
        # Check if last seed went into store (extra move)
        last_pos = (move + seeds) % 14
        extra_move_bonus = 0
        if last_pos == 6:
            extra_move_bonus = 100
            
        # Check for capture potential
        capture_bonus = 0
        if last_pos < 6:  # Land on your side
            if temp_you[last_pos] == 1:  # Last seed into an empty spot
                opposite = 5 - last_pos
                if temp_opponent[opposite] > 0:
                    capture_bonus = temp_opponent[opposite] + 1
                    
        score = extra_move_bonus + capture_bonus
        
        # Prefer moves that put seeds in later houses
        if move > 0:
            # If it's a later move and there are seeds to be moved
            if you[move] > move and move != 5:
                score += you[move] * 20
                
        # Prefer covering future seeds
        if you[move] > 0 and move < 5:
            score += you[move] * 1000
        
        # Check number of seeds in future house at that position
        future_seeds = 0
        future_pos =	move + 1
        while future_pos < 6:
            future_seeds += temp_you[future_pos]
            future_pos += 1
            
        # Prefer moves that help build seeds in later positions
        seeds_in_later = sum(temp_you[i] for i in range(move + 1, 6))
        score += seeds_in_later * 0.01
        
        # Prefer moves that help control the board (like move into last position)
        # if move == 5:
        #     score += 500
        
        if score > best_score:
            best_score = score
            best_move = move
            
    return best_move
