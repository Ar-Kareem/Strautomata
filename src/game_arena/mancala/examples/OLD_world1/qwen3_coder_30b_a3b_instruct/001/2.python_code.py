
import numpy as np

def policy(you: list[int], opponent: list[int]) -> int:
    # Simulate all possible moves and evaluate them
    best_move = 0
    best_score = -float('inf')
    
    for i in range(6):
        if you[i] == 0:
            continue
            
        # Make a copy of the board state
        you_copy = you[:]
        opponent_copy = opponent[:]
        
        # Simulate the move
        seeds = you_copy[i]
        you_copy[i] = 0
        
        # Distribute seeds
        pos = i + 1
        while seeds > 0:
            # Skip opponent's store
            if pos == 13:
                pos = 0
                
            # If we're at opponent's store, skip it
            if pos == 7:
                pos += 1
                
            # Place one seed
            if pos < 7:
                you_copy[pos] += 1
            else:
                opponent_copy[pos - 7] += 1
                
            seeds -= 1
            pos += 1
            
        # Determine if this is the last seed and what happens
        last_pos = (i + you[i]) % 14
        extra_move = False
        capture = False
        captured_seeds = 0
        
        if last_pos < 7 and last_pos != 6:
            # Last seed is in your house
            if you_copy[last_pos] == 1:  # Only one seed was placed
                # Check for capture
                if opponent_copy[5 - last_pos] > 0:
                    capture = True
                    captured_seeds = 1 + opponent_copy[5 - last_pos]
                    opponent_copy[5 - last_pos] = 0
        elif last_pos == 6:
            extra_move = True
            
        # Calculate score for this move
        score = 0
        
        # If it's an extra move, we get another chance (this will be more valuable)
        if extra_move:
            score += 100
            
        # If it's a capture, prioritize it
        if capture:
            score += captured_seeds * 10
            
        # Add the number of seeds that end up in your store after the move
        # This is the easiest way to assess value of the move
        score += you_copy[6]
        
        # Additional heuristic: if we can win by capturing all the remaining seeds, 
        # we should choose that move
        # But since we can't see the end game, we prioritize moves that give 
        # us immediate benefits
        
        # Prefer moves that add to our store
        # And prefer moves that make more seeds available for future turns
        score += sum(you_copy[:6]) * 0.1
        
        # Prefer moves that don't get the opponent close to taking over
        # Only add a slight preference for maintaining some balance
        for j in range(6):
            if you_copy[j] == 0 and opponent_copy[5 - j] > 0:
                score -= 5  # Penalty for leaving opponent a captures
            elif you_copy[j] == 1 and opponent_copy[5 - j] > 0:
                score -= 2  # Slight penalty for giving away capture opportunity
                
        # Prefer moves that don't empty house 5 or 4 in case of overloading
        if you_copy[5] == 1:
            score += 2  # Have potential for a re-capture
        if you_copy[4] == 1:
            score += 1  # Some potential benefit
            
        # Prefer moves that keep some seeds in early houses
        if you_copy[0] + you_copy[1] + you_copy[2] > 1:
            score += 3  # Keep options open
            
        # Prefer moves that won't prevent us from having a seed in a house
        if sum(you_copy[:6]) == 1 and you_copy[i] == 0:
            score -= 7  # More likely to prevent future moves
            
        # Check if this move wins the game (game ends because all houses have zero seeds)
        # or allows more moves in the next turn (if we can use extra move)
        
        # Comparing moves - higher score is better
        if score > best_score:
            best_score = score
            best_move = i
            
    return best_move
