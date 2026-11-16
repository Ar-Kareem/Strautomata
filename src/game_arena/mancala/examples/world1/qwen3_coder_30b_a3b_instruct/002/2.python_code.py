
def policy(you: list[int], opponent: list[int]) -> int:
    def simulate_move(you_state, opponent_state, move_index):
        # Create copies to avoid modifying original
        your_new = you_state[:]
        opponent_new = opponent_state[:]
        
        # Get seeds from the chosen house
        seeds = your_new[move_index]
        your_new[move_index] = 0
        
        if seeds == 0:
            return None, None, False, 0  # Should not happen according to problem statement
        
        # Distribution positions
        positions = []
        # From move_index+1 to 5 (your side)
        for i in range(move_index + 1, 6):
            positions.append(('you', i))
        # Your store
        positions.append(('you', 6))
        # Opponent's houses 0 to 5
        for i in range(0, 6):
            positions.append(('opponent', i))
        # Your houses 0 to move_index-1 (if move_index > 0)
        for i in range(0, move_index):
            positions.append(('you', i))
            
        # Distribute seeds
        current_pos = 0
        last_pos_type = None
        last_pos_index = None
        
        for seed in range(seeds):
            pos_type, pos_index = positions[current_pos]
            if pos_type == 'you':
                opponent_new[pos_index] += 1
            else:  # pos_type == 'opponent'
                opponent_new[pos_index] += 1
                
            last_pos_type = pos_type
            last_pos_index = pos_index
            
            current_pos = (current_pos + 1) % len(positions)
        
        # Check for captures
        extra_move = (last_pos_type == 'you' and last_pos_index == 6)
        captured_seeds = 0
        if last_pos_type == 'you' and last_pos_index < 6 and your_new[last_pos_index] == 0 and opponent_new[5 - last_pos_index] > 0:
            # Capture!
            captured_seeds = opponent_new[5 - last_pos_index]
            your_new[last_pos_index] = 0
            your_new[6] += captured_seeds + 1  # Plus the seed that landed
            opponent_new[5 - last_pos_index] = 0
            
        # Handle the case where the last seed lands in store and gets extra move  
        # (we already captured it above if it was an extra move)
        
        # Apply the final move
        for i in range(6):
            your_new[i] += opponent_new[i] if last_pos_type == 'you' and i == last_pos_index else 0
            opponent_new[i] = 0 if last_pos_type == 'you' and i == last_pos_index else opponent_new[i]
            
        # Actually, let me restructure this logic to be clearer and simulate the actual move
        # Perfect way: just directly simulate the spread and track final position
        
        your_new = you_state[:]
        opponent_new = opponent_state[:]
        seeds = your_new[move_index]
        your_new[move_index] = 0
        if seeds == 0:
            return None, None, False, 0

        # Simulate distributing from the move_index house
        current_pos = move_index + 1
        last_pos = None
        # Continue distributing
        for i in range(seeds):
            if current_pos == 6:
                # We will add to our store
                your_new[6] += 1;
                last_pos = ('you', 6)
            elif current_pos < 6:
                # We will add to our own houses (0 to 5)
                your_new[current_pos] += 1;
                last_pos = ('you', current_pos);
            else:
                # Add to opponent's houses 0-5 (since we wrapped around)
                # But position after 6 is 0, so we're going around
                opponent_new[current_pos - 7] += 1; 
                last_pos = ('opponent', current_pos - 7)
            current_pos = (current_pos + 1) % 13;
        
        # After distribution, if last seed was in our own house, check for capture
        extra_move = False
        captured = 0
        
        if last_pos[0] == 'you' and last_pos[1] < 6:  # Lands in our side
            if your_new[last_pos[1]] == 1 and opponent_new[5 - last_pos[1]] > 0:
                # This guarantees we captured all seeds in the opposite house
                captured = opponent_new[5 - last_pos[1]]
                your_new[6] += captured + 1  # Seed that landed + captured seeds
                your_new[last_pos[1]] = 0  # Empty our house
                opponent_new[5 - last_pos[1]] = 0  # Clear the captured opponent's house
        elif last_pos[0] == 'you' and last_pos[1] == 6:
            extra_move = True

        return your_new, opponent_new, extra_move, captured
    
    best_move = 0
    best_score = -1
    
    for move in range(6):
        if you[move] > 0:
            next_you, next_opponent, extra_turn, captured = simulate_move(you, opponent, move)
            # Score components
            score = captured * 10  # Capture gives more points
            if extra_turn:
                # Extra move is valuable, but not as much as capture
                score += 5
            # Also consider the resulting number of seeds in your store
            score += next_you[6] * 0.5
            # Penalize emptying own house if it makes resources available
            # But to keep it simple, the above score should work fine
            
            # Okay let's redefine scoring more simply and cleanly:
            # I will consider direct score points plus a bonus for captures and extra turns
            
            if score > best_score:
                best_score = score
                best_move = move

    return best_move
