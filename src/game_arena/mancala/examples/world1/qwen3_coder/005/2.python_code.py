
import copy

def policy(you: list[int], opponent: list[int]) -> int:
    # Look for immediate tactical advantages
    best_move = None
    best_score = float('-inf')
    
    # Try each legal move
    for i in range(6):
        if you[i] > 0:
            # Simulate the move
            new_you, new_opponent, extra_turn, captures = simulate_move(you, opponent, i)
            
            # Evaluate this move
            score = evaluate_move(you, opponent, i, new_you, new_opponent, extra_turn, captures)
            
            if score > best_score:
                best_score = score
                best_move = i
    
    return best_move

def simulate_move(you, opponent, move):
    # Create copies to avoid modifying originals
    new_you = you[:]
    new_opponent = opponent[:]
    
    seeds = new_you[move]
    new_you[move] = 0
    
    # Position tracking: 0-5 = my houses, 6 = my store, 7-12 = opponent houses
    position = move + 1
    extra_turn = False
    captures = 0
    
    for _ in range(seeds):
        if position == 6:  # My store
            new_you[6] += 1
            if _ == seeds - 1:  # Last seed
                extra_turn = True
        elif 0 <= position <= 5:  # My houses
            new_you[position] += 1
            if _ == seeds - 1:  # Last seed
                # Check for capture
                if new_you[position] == 1 and new_opponent[5 - position] > 0:  # Was empty before drop
                    captures = 1 + new_opponent[5 - position]
                    new_you[6] += captures
                    new_you[position] = 0
                    new_opponent[5 - position] = 0
        elif 7 <= position <= 12:  # Opponent houses
            opp_index = position - 7
            new_opponent[opp_index] += 1
        # Never place in opponent's store (position 13 in cycle)
        
        position = (position + 1) % 13
        if position == 13:  # Skip opponent's store
            position = 0
    
    return new_you, new_opponent, extra_turn, captures

def evaluate_move(you, opponent, move, new_you, new_opponent, extra_turn, captures):
    score = 0
    
    # Immediate tactical benefits
    if extra_turn:
        score += 100  # High value for extra turn
    
    if captures > 0:
        score += captures * 2  # Value captures
    
    # Net gain in store
    store_gain = new_you[6] - you[6]
    score += store_gain
    
    # Positional evaluation
    # Evaluate our board position after move
    my_seeds = sum(new_you[:6])
    opp_seeds = sum(new_opponent[:6])
    
    # Slightly prefer moves that maintain good board position
    seed_diff = my_seeds - opp_seeds
    score += seed_diff * 0.1
    
    # Prefer moves that don't give opponent easy captures
    # Check if this move creates vulnerable positions for us
    vulnerability = 0
    for i in range(6):
        # If we have 0 seeds in a house and opponent has seeds opposite
        if new_you[i] == 0 and you[i] > 0 and new_opponent[5-i] > 0:
            vulnerability -= 1
    score += vulnerability * 5  # Penalty for creating vulnerabilities
    
    # Prefer moves that keep seeds closer to store (more likely to score)
    weighted_seeds = 0
    for i in range(6):
        weighted_seeds += new_you[i] * (i + 1)  # Higher weight for houses closer to store
    score -= weighted_seeds * 0.05  # Lower weighted seeds is better
    
    return score
