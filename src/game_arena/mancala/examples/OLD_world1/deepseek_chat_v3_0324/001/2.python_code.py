
import copy

def policy(you: list[int], opponent: list[int]) -> int:
    """Selects the best move based on immediate rewards and potential captures."""
    best_move = -1
    best_score = -float('inf')
    
    for move in range(6):
        if you[move] == 0:
            continue
            
        # Simulate the move
        new_you, new_opponent, extra_move = simulate_move(you, opponent, move)
        
        # Calculate score for this move
        score = 0
        
        # Immediate store difference
        store_diff = new_you[6] - you[6]
        score += store_diff * 2  # Store seeds are more valuable
        
        # Check for extra move
        if extra_move:
            score += 10  # Bonus for extra move
            
        # Check for captures
        capture_diff = new_you[6] - (you[6] + store_diff)
        if capture_diff > 0:
            score += capture_diff * 3  # Captures are very valuable
            
        # Consider opponent's potential responses
        opponent_options = sum(1 for i in range(6) if new_opponent[i] > 0)
        if opponent_options == 0:
            # Game would end after our move, collect all remaining seeds
            remaining_seeds = sum(new_you[:6])
            score += remaining_seeds * 2
            
        # Prefer moves that leave opponent with fewer options
        score -= opponent_options * 0.1
        
        # Prefer moves that don't leave opponent with obvious captures
        for i in range(6):
            if new_opponent[i] == (5 - i):  # Potential capture
                score -= 2
        
        # Break ties by preferring rightmost moves (often better for board control)
        score += move * 0.01
        
        if score > best_score:
            best_score = score
            best_move = move
            
    return best_move

def simulate_move(you, opponent, move):
    """Simulates a move and returns the new state and whether an extra move is granted."""
    you = copy.deepcopy(you)
    opponent = copy.deepcopy(opponent)
    seeds = you[move]
    you[move] = 0
    current_pos = move + 1
    last_pos = None
    extra_move = False
    
    while seeds > 0:
        # Distribute in your houses
        while current_pos < 6 and seeds > 0:
            you[current_pos] += 1
            seeds -= 1
            last_pos = current_pos
            current_pos += 1
            
        # Distribute in your store
        if seeds > 0:
            you[6] += 1
            seeds -= 1
            last_pos = 6
            if seeds == 0:
                extra_move = True
                
        # Distribute in opponent's houses
        if seeds > 0:
            current_pos = 0
            while current_pos < 6 and seeds > 0:
                opponent[current_pos] += 1
                seeds -= 1
                last_pos = 'opponent_' + str(current_pos)
                current_pos += 1
                
        # Continue distributing in your houses if needed
        if seeds > 0:
            current_pos = 0
            
    # Check for capture
    if isinstance(last_pos, int) and last_pos < 6 and you[last_pos] == 1 and opponent[5 - last_pos] > 0:
        you[6] += you[last_pos] + opponent[5 - last_pos]
        you[last_pos] = 0
        opponent[5 - last_pos] = 0
        
    return you, opponent, extra_move
