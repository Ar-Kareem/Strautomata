
def policy(you: list[int], opponent: list[int]) -> int:
    def simulate_move(board, player_houses, opponent_houses, move_index):
        # Create copies to avoid modifying original
        you_copy = board[0][:]
        opponent_copy = board[1][:]
        
        # Get seeds from the chosen house
        seeds = you_copy[move_index]
        you_copy[move_index] = 0
        
        if seeds == 0:
            return None
            
        # Distribute seeds counter-clockwise:
        # 1. Your houses (move_index+1 to 5)
        # 2. Your store
        # 3. Opponent houses (0 to 5) 
        # 4. Your houses (0 to move_index-1)
        
        # Distribute all but the last seed first:
        pos = move_index + 1
        seeds_placed = 0
        while seeds_placed < seeds - 1:
            if pos == 6:
                you_copy[pos] += 1
                pos = 0
            elif pos == 12:
                opponent_copy[0] += 1
                pos = 0
            elif pos < 6:
                you_copy[pos] += 1
                pos += 1
            elif pos < 12:
                opponent_copy[pos-6] += 1
                pos += 1
            else:
                # pos >= 12 - go back to beginning of your houses
                you_copy[pos-12] += 1
                pos = 0
            seeds_placed += 1
            
        # Place the last seed and check what happens
        last_pos = pos
        if last_pos == 6:
            you_copy[last_pos] += 1
            extra_move = True
        elif last_pos == 12:
            opponent_copy[0] += 1
            extra_move = False
        elif last_pos < 6:
            you_copy[last_pos] += 1
            # Check capture condition
            if you_copy[last_pos] == 1 and opponent_copy[5 - last_pos] > 0:
                # Capture happened
                captured = opponent_copy[5 - last_pos]
                you_copy[6] += 1 + captured
                you_copy[last_pos] = 0
                opponent_copy[5 - last_pos] = 0
            extra_move = False
        else:
            opponent_copy[last_pos - 6] += 1
            extra_move = False
            
        return (you_copy, opponent_copy, extra_move)
    
    def simulate_game(initial_you, initial_opponent):
        current_you = initial_you[:]
        current_opponent = initial_opponent[:]
        
        while True:
            # Simulate all possible moves to get the result 
            best_store = -1
            best_move = None
            
            for i in range(6):
                if current_you[i] > 0:
                    # Simulate move i 
                    new_state = simulate_move([current_you, current_opponent], current_you, current_opponent, i)
                    if new_state is None:
                        continue
                        
                    new_you, new_opponent, extra_move = new_state
                    
                    # If we get an extra move, continue simulating
                    temp_you = new_you[:]
                    temp_opponent = new_opponent[:]
                    
                    # Just return the total seeds in store for simplicity
                    total_seeds = temp_you[6]
                    if total_seeds > best_store:
                        best_store = total_seeds
                        best_move = i
            if best_move is None:
                break
                
            # Apply the best move and see how it turns out
            result = simulate_move([current_you, current_opponent], current_you, current_opponent, best_move)
            if result is None:
                break
            current_you, current_opponent, extra_move = result
            
            # Check if game ended (either player has no seeds)
            you_empty = all(x == 0 for x in current_you[:6])
            opponent_empty = all(x == 0 for x in current_opponent[:6])
            
            if you_empty or opponent_empty:
                # Move remaining seeds to stores
                if you_empty:
                    current_opponent[6] += sum(current_opponent[:6])
                if opponent_empty:
                    current_you[6] += sum(current_you[:6])
                break
                
        return current_you[6]
    
    def eval_move(you, opponent, move_index):
        # Make a single move and see the outcome
        you_copy = you[:]
        opponent_copy = opponent[:]
        
        seeds = you_copy[move_index]
        if seeds == 0:
            return -1  # Invalid move
            
        # Simple distribution logic
        pos = move_index + 1
        seeds_placed = 0
        
        while seeds_placed < seeds:
            # We'll simulate in a simpler way for speed
            # Place seeds one by one
            if pos == 6:
                you_copy[pos] += 1
                pos = 0
            elif pos < 6:
                you_copy[pos] += 1
                pos += 1
            elif pos == 12:
                opponent_copy[0] += 1
                pos = 0
            else:  # pos > 6
                opponent_copy[pos - 6] += 1
                pos += 1
                
            seeds_placed += 1
            
        # Check if last seed landed in store or caused capture
        last_pos = pos - 1 if pos != 0 else 5
        if last_pos == 6:
            return 100  # Extra move is good
        elif last_pos < 6:
            # Capture scenario - but let's be simple and just return the store
            return you_copy[6]
        
        return you_copy[6]
    
    def simple_move_evaluation(you, opponent):
        best_score = -1
        best_move = 0
        for i in range(6):
            if you[i] > 0:
                score = eval_move(you, opponent, i)
                if score > best_score:
                    best_score = score
                    best_move = i
        return best_move
    
    # Return the move that results in the highest store value, or a safe move if none are clearly better
    best_move = 0
    best_score = -1
    
    for i in range(6):
        if you[i] > 0:
            # Just evaluate the score after the move
            # A simple heuristic: choose a move that gives us a good potential outcome
            
            # Try to prefer moves that:
            # 1. Put seeds in our store (if we can)
            # 2. Don't let opponent easily capture or gain an advantage
            # 3. Avoid emptying houses that might be valuable later
            
            # Simpler approach: basic scoring
            you_copy = you[:]
            opponent_copy = opponent[:]
            
            # Move the seeds
            seeds = you_copy[i]
            you_copy[i] = 0
            
            # Find where the last seed lands
            pos = i + 1
            seeds_placed = 0
            while seeds_placed < seeds - 1:
                if pos == 6:
                    you_copy[pos] += 1
                    pos = 0
                elif pos < 6:
                    you_copy[pos] += 1
                    pos += 1
                elif pos == 12:
                    opponent_copy[0] += 1
                    pos = 0
                else:
                    opponent_copy[pos - 6] += 1
                    pos += 1
                seeds_placed += 1
                
            # Place the last seed
            if pos == 6:
                score = 10  # Extra move!
            elif pos < 6:
                # See if it results in a capture (simple version)
                if you_copy[pos] == 1:  # Last seed lands in empty house
                    if opponent_copy[5 - pos] > 0:
                        score = 9 + opponent_copy[5 - pos]  # Capture points
                    else:
                        score = 5  # Just a regular move
                else:
                    score = 4
            else:
                score = 0
                
            if score > best_score:
                best_score = score
                best_move = i
                
    return best_move

# Actually, let me write a cleaner version that works correctly
def policy(you: list[int], opponent: list[int]) -> int:
    def simulate_game(you_state, opponent_state):
        # Create copies to avoid side effects
        you_curr = you_state[:]
        opponent_curr = opponent_state[:]
        
        # Simulate all moves possible, then take the one with highest resulting store
        # But for better performance, just simulate one move
        max_store = -1
        best_move = 0
        
        # Try all legal moves
        for i in range(6):
            if you_curr[i] > 0:
                # Make a copy of the board for simulation
                you_copy = you_curr[:]
                opponent_copy = opponent_curr[:]
                
                # Pick and remove seeds from house i
                seeds = you_copy[i]
                you_copy[i] = 0
                
                # Distribute the seeds
                pos = i + 1  # where to start distributing
                
                seeds_placed = 0
                while seeds_placed < seeds:
                    # Place seed at current position, skipping opponent's store (index 6)
                    if pos == 6:  # Go to your store
                        you_copy[pos] += 1
                        pos = 0
                    elif pos == 12:  # Go to opponent's first house
                        opponent_copy[0] += 1
                        pos = 0
                    elif pos < 6:  # Your houses
                        you_copy[pos] += 1
                        pos += 1
                    else:  # Opponent's houses (pos 6-11)
                        opponent_copy[pos - 6] += 1
                        pos += 1
                    
                    seeds_placed += 1
                
                # The index of the last seed placed
                last_pos = pos - 1
                
                # If last seed lands in store, we get another move
                extra_move = (last_pos == 6)
                
                # Check capture condition: landed in our house that was previously empty
                if last_pos < 6 and you_copy[last_pos] == 1:
                    # Opponent's house opposite to this one
                    opp_index = 5 - last_pos
                    if opponent_copy[opp_index] > 0:
                        # Capture the seeds
                        you_copy[6] += you_copy[last_pos] + opponent_copy[opp_index]
                        you_copy[last_pos] = 0
                        opponent_copy[opp_index] = 0
                        
                # Update score (return total in store)
                score = you_copy[6]
                
                if score > max_store:
                    max_store = score
                    best_move = i
                    
        return best_move
                      
    # Return the move that maximizes resulting store count
    return simulate_game(you, opponent)

# Even more simplified and robust solution:
def policy(you: list[int], opponent: list[int]) -> int:
    def get_move_score(you_state, opponent_state, move_index):
        # Simulate move and compute resulting store count
        you_copy = you_state[:]
        opponent_copy = opponent_state[:]
        
        seeds = you_copy[move_index]
        if seeds == 0:
            return -1
            
        # Get the starting position for seeds to be placed
        pos = move_index + 1
        
        # Distribute all seeds
        for i in range(seeds):
            if pos == 6:
                you_copy[pos] += 1
                pos = 0
            elif pos == 12:
                opponent_copy[0] += 1
                pos = 0
            elif pos < 6:
                you_copy[pos] += 1
                pos += 1
            else:
                opponent_copy[pos - 6] += 1
                pos += 1
                
        # Check if last seed lands in store - extra move
        last_pos = pos - 1 if pos != 0 else 5
        
        # Apply capture logic if applicable
        if last_pos < 6 and you_copy[last_pos] == 1:
            opp_index = 5 - last_pos
            if opponent_copy[opp_index] > 0:
                you_copy[6] += you_copy[last_pos] + opponent_copy[opp_index]
                you_copy[last_pos] = 0
                opponent_copy[opp_index] = 0
                
        return you_copy[6]
        
    # Find best move - prefer ones that give high store counts
    best_move = 0
    best_score = -1
    
    for i in range(6):
        if you[i] > 0:
            score = get_move_score(you, opponent, i)
            if score > best_score:
                best_score = score
                best_move = i
                
    return best_move
