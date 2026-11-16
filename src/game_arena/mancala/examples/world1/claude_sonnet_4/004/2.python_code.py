
def policy(you: list[int], opponent: list[int]) -> int:
    def simulate_move(you_state, opp_state, house):
        """Simulate a move and return the resulting state and whether we get an extra move."""
        new_you = you_state.copy()
        new_opp = opp_state.copy()
        
        # Pick up seeds from chosen house
        seeds = new_you[house]
        new_you[house] = 0
        
        # Distribute seeds
        pos = house
        current_side = 0  # 0 = you, 1 = opponent
        
        while seeds > 0:
            pos += 1
            
            if current_side == 0:  # Your side
                if pos <= 5:  # Your houses 0-5
                    new_you[pos] += 1
                elif pos == 6:  # Your store
                    new_you[6] += 1
                else:  # pos > 6, switch to opponent side
                    pos = 0
                    current_side = 1
                    new_opp[0] += 1
            else:  # Opponent side
                if pos <= 4:  # Opponent houses 0-4
                    new_opp[pos] += 1
                elif pos == 5:  # Opponent house 5
                    new_opp[5] += 1
                elif pos == 6:  # Skip opponent store, go to your side
                    pos = 0
                    current_side = 0
                    new_you[0] += 1
            
            seeds -= 1
        
        # Check for special effects
        extra_move = False
        
        # Extra move if landed in your store
        if current_side == 0 and pos == 6:
            extra_move = True
        
        # Capture if landed in your empty house with opponent seeds opposite
        elif current_side == 0 and 0 <= pos <= 5 and new_you[pos] == 1:
            opposite_house = 5 - pos
            if new_opp[opposite_house] > 0:
                # Capture: move your seed and all opposite seeds to your store
                captured = new_you[pos] + new_opp[opposite_house]
                new_you[6] += captured
                new_you[pos] = 0
                new_opp[opposite_house] = 0
        
        return new_you, new_opp, extra_move
    
    def evaluate_position(you_state, opp_state):
        """Evaluate the position from your perspective."""
        # Store difference is most important
        store_diff = you_state[6] - opp_state[6]
        
        # Total seeds on your side vs opponent side
        your_seeds = sum(you_state[:6])
        opp_seeds = sum(opp_state[:6])
        side_diff = your_seeds - opp_seeds
        
        # Bonus for having moves available
        your_moves = sum(1 for i in range(6) if you_state[i] > 0)
        opp_moves = sum(1 for i in range(6) if opp_state[i] > 0)
        mobility = your_moves - opp_moves
        
        return store_diff * 10 + side_diff * 2 + mobility
    
    def get_legal_moves(state):
        """Get all legal moves (non-empty houses)."""
        return [i for i in range(6) if state[i] > 0]
    
    # Get all legal moves
    legal_moves = get_legal_moves(you)
    if not legal_moves:
        return 0  # Shouldn't happen according to problem statement
    
    best_move = legal_moves[0]
    best_score = float('-inf')
    
    # Evaluate each possible move
    for move in legal_moves:
        new_you, new_opp, extra_move = simulate_move(you, opponent, move)
        
        # Base score from immediate position
        score = evaluate_position(new_you, new_opp)
        
        # Bonus for extra moves
        if extra_move:
            score += 20
        
        # If we get an extra move, try to look ahead one more level
        if extra_move:
            next_moves = get_legal_moves(new_you)
            if next_moves:
                best_followup = float('-inf')
                for followup in next_moves:
                    follow_you, follow_opp, _ = simulate_move(new_you, new_opp, followup)
                    followup_score = evaluate_position(follow_you, follow_opp)
                    best_followup = max(best_followup, followup_score)
                score += best_followup * 0.5  # Discount future moves
        
        # Prefer moves that land in store or create captures
        if move < 6 and you[move] == (6 - move + 1):  # Lands in store
            score += 15
        
        # Check for immediate capture potential
        landing_pos = (move + you[move]) % 13
        if landing_pos < 6:  # Lands on your side
            house_after_move = landing_pos
            if you[house_after_move] == 0:  # Empty house
                opposite = 5 - house_after_move
                if opponent[opposite] > 0:  # Can capture
                    score += opponent[opposite] * 3
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
