
def policy(you: list[int], opponent: list[int]) -> int:
    def simulate_move(you_state, opp_state, move):
        # Create copies to avoid modifying original
        you_copy = you_state[:]
        opp_copy = opp_state[:]
        
        if you_copy[move] == 0:
            return None  # Invalid move
            
        # Pick up seeds
        seeds = you_copy[move]
        you_copy[move] = 0
        
        # Current position for seeding
        current_side = 'you'
        current_pos = move
        
        # Distribute seeds
        while seeds > 0:
            if current_side == 'you':
                if current_pos < 5:
                    current_pos += 1
                    you_copy[current_pos] += 1
                    seeds -= 1
                elif current_pos == 5:
                    current_pos = 6  # Move to store
                    you_copy[current_pos] += 1
                    seeds -= 1
                else:  # current_pos == 6 (store)
                    current_side = 'opponent'
                    current_pos = 0
                    if seeds > 0:
                        opp_copy[current_pos] += 1
                        seeds -= 1
            else:  # current_side == 'opponent'
                if current_pos < 5:
                    current_pos += 1
                    if current_pos == 6:  # Skip opponent's store
                        current_side = 'you'
                        current_pos = 0
                    else:
                        opp_copy[current_pos] += 1
                        seeds -= 1
                else:  # current_pos == 5
                    current_side = 'you'
                    current_pos = 0
                    you_copy[current_pos] += 1
                    seeds -= 1
        
        # Check for special effects
        extra_move = False
        
        # Extra move: last seed in my store
        if current_side == 'you' and current_pos == 6:
            extra_move = True
        
        # Capture: last seed in my empty house with opponent having seeds opposite
        if (current_side == 'you' and current_pos < 6 and 
            you_copy[current_pos] == 1 and opp_copy[5 - current_pos] > 0):
            # Capture
            captured = you_copy[current_pos] + opp_copy[5 - current_pos]
            you_copy[6] += captured
            you_copy[current_pos] = 0
            opp_copy[5 - current_pos] = 0
        
        return you_copy, opp_copy, extra_move
    
    def evaluate_position(you_state, opp_state):
        # Simple evaluation: score difference + positional factors
        score_diff = you_state[6] - opp_state[6]
        
        # Bonus for seeds close to store (easier to score)
        position_bonus = 0
        for i in range(6):
            position_bonus += you_state[i] * (6 - i) * 0.1
            position_bonus -= opp_state[i] * (6 - i) * 0.1
        
        # Bonus for having moves that could lead to extra turns
        extra_turn_potential = 0
        for i in range(6):
            if you_state[i] > 0:
                # Check if this move could land in store
                if you_state[i] == (6 - i):
                    extra_turn_potential += 2
                elif you_state[i] % 13 == (6 - i):  # Account for full cycles
                    extra_turn_potential += 1
        
        return score_diff + position_bonus + extra_turn_potential
    
    # Find all legal moves
    legal_moves = [i for i in range(6) if you[i] > 0]
    
    if not legal_moves:
        return 0  # Shouldn't happen based on problem statement
    
    best_move = legal_moves[0]
    best_score = float('-inf')
    
    # Evaluate each legal move
    for move in legal_moves:
        result = simulate_move(you, opponent, move)
        if result is None:
            continue
            
        new_you, new_opp, extra_move = result
        
        # Base evaluation
        score = evaluate_position(new_you, new_opp)
        
        # Bonus for extra moves
        if extra_move:
            score += 5
        
        # Immediate score gain bonus
        immediate_gain = new_you[6] - you[6]
        score += immediate_gain * 2
        
        # Check if this move wins the game
        if sum(new_you[0:6]) == 0:  # I emptied my side
            final_you_score = new_you[6]
            final_opp_score = new_opp[6] + sum(new_opp[0:6])
            if final_you_score > final_opp_score:
                score += 1000  # Winning move bonus
        
        # Check if opponent will be out of moves
        if sum(new_opp[0:6]) == 0:  # Opponent would be out of moves
            final_you_score = new_you[6] + sum(new_you[0:6])
            final_opp_score = new_opp[6]
            if final_you_score > final_opp_score:
                score += 1000  # Winning move bonus
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
