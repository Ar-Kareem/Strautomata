
def policy(you: list[int], opponent: list[int]) -> int:
    def simulate_move(you_state, opp_state, house):
        # Make copies to avoid modifying original
        new_you = you_state[:]
        new_opp = opp_state[:]
        
        # Pick up seeds from chosen house
        seeds = new_you[house]
        new_you[house] = 0
        
        # Distribute seeds counter-clockwise
        current_pos = house
        
        for _ in range(seeds):
            current_pos += 1
            
            # My houses (0-5)
            if current_pos <= 5:
                new_you[current_pos] += 1
                last_pos = ('you', current_pos)
            # My store (6)
            elif current_pos == 6:
                new_you[6] += 1
                last_pos = ('you', 6)
            # Opponent houses (7-12 mapped to 0-5)
            elif current_pos <= 12:
                opp_house = current_pos - 7
                new_opp[opp_house] += 1
                last_pos = ('opp', opp_house)
            # Back to my houses, skip opponent store
            else:
                current_pos = current_pos - 13
                new_you[current_pos] += 1
                last_pos = ('you', current_pos)
        
        # Check for special effects
        extra_turn = False
        captured = False
        
        # Extra turn: last seed in my store
        if last_pos == ('you', 6):
            extra_turn = True
        
        # Capture: last seed in my empty house with opponent opposite house having seeds
        elif last_pos[0] == 'you' and 0 <= last_pos[1] <= 5:
            if new_you[last_pos[1]] == 1:  # Was empty before this seed
                opposite_house = 5 - last_pos[1]
                if new_opp[opposite_house] > 0:
                    # Capture both seeds
                    captured_seeds = new_you[last_pos[1]] + new_opp[opposite_house]
                    new_you[6] += captured_seeds
                    new_you[last_pos[1]] = 0
                    new_opp[opposite_house] = 0
                    captured = True
        
        return new_you, new_opp, extra_turn, captured
    
    def evaluate_position(you_state, opp_state):
        # Evaluation based on store difference and positional factors
        store_diff = you_state[6] - opp_state[6]
        
        # Slight preference for seeds in houses closer to store
        positional_bonus = sum(you_state[i] * (i * 0.05) for i in range(6))
        positional_penalty = sum(opp_state[i] * ((5-i) * 0.05) for i in range(6))
        
        return store_diff + positional_bonus - positional_penalty
    
    # Get all legal moves
    legal_moves = [i for i in range(6) if you[i] > 0]
    
    if len(legal_moves) == 1:
        return legal_moves[0]
    
    best_move = legal_moves[0]
    best_score = float('-inf')
    
    for move in legal_moves:
        new_you, new_opp, extra_turn, captured = simulate_move(you, opponent, move)
        
        # Base evaluation
        score = evaluate_position(new_you, new_opp)
        
        # Bonuses and penalties
        if extra_turn:
            score += 8  # Extra turns are very valuable
        
        if captured:
            score += 5  # Captures are valuable
        
        # Check if this move sets up opponent for easy captures
        opponent_capture_threat = 0
        for opp_move in range(6):
            if new_opp[opp_move] > 0:
                _, test_you, _, opp_captured = simulate_move(new_opp, new_you, opp_move)
                if opp_captured:
                    opponent_capture_threat += 3
        
        score -= opponent_capture_threat
        
        # Prefer moves that don't leave single seeds in houses close to opponent
        for i in range(3):  # Houses 0, 1, 2 are vulnerable
            if new_you[i] == 1:
                score -= 1
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
