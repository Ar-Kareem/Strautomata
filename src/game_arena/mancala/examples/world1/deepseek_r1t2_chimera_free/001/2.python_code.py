
def policy(you: list[int], opponent: list[int]) -> int:
    # Define the order of houses and store for seed distribution
    flat_order = []
    for idx in range(6):
        flat_order.append(('you', idx))
    flat_order.append(('you', 6))  # player's store
    for idx in range(6):
        flat_order.append(('opponent', idx))  # opponent's houses (skip their store)

    best_move = None
    best_score = -float('inf')
    
    for move_i in range(6):
        if you[move_i] == 0:
            continue  # Skip empty houses
        
        # Create copies to simulate the move
        new_you = you.copy()
        new_opponent = opponent.copy()
        seeds_to_sow = new_you[move_i]
        new_you[move_i] = 0  # Remove seeds from the selected house
        
        current_pos = (move_i + 1) % 14  # Start sowing from the next position
        house_before = None  # To track state before placing the last seed
        last_cell = None     # To track where the last seed lands
        
        for j in range(seeds_to_sow):
            # Record state before placing the last seed
            if j == seeds_to_sow - 1:
                who, pos = flat_order[current_pos]
                if who == 'you' and pos != 6:
                    house_before = new_you[pos]
                else:
                    house_before = None
            
            # Place the seed
            who, pos = flat_order[current_pos]
            if who == 'you':
                if pos == 6:
                    new_you[6] += 1
                else:
                    new_you[pos] += 1
            else:  # 'opponent'
                new_opponent[pos] += 1
            
            # Record last seed's position
            if j == seeds_to_sow - 1:
                last_cell = (who, pos)
            
            current_pos = (current_pos + 1) % 14  # Move to next position
        
        # Check for extra move
        extra_move = (last_cell == ('you', 6))
        
        # Check for capture
        captured = 0
        if not extra_move and last_cell[0] == 'you' and last_cell[1] != 6:
            pos = last_cell[1]
            # If the house was empty before placing the last seed and now has one seed
            if house_before == 0 and new_you[pos] == 1:
                opp_pos = 5 - pos
                if new_opponent[opp_pos] > 0:
                    captured = new_you[pos] + new_opponent[opp_pos]
                    new_you[6] += captured  # Capture seeds
                    new_you[pos] = 0
                    new_opponent[opp_pos] = 0
        
        # Calculate net gain (including captures)
        net_gain = new_you[6] - you[6]
        
        # Score the move: net gain + bonus for extra move
        score = net_gain
        if extra_move:
            score += 1000  # High bonus for extra move
        
        # Update best move if current score is higher or leftmost in case of tie
        if score > best_score or (score == best_score and move_i < best_move):
            best_score = score
            best_move = move_i
    
    return best_move
