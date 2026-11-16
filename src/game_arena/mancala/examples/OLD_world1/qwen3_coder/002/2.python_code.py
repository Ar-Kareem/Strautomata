
import numpy as np

def policy(you: list[int], opponent: list[int]) -> int:
    """
    Implements a Kalah move-selection policy.
    
    Strategy:
    1. Look for immediate captures
    2. Look for extra turns
    3. Avoid giving captures to opponent
    4. Maximize seeds moved
    5. Fallback to first available move
    """
    you = np.array(you)
    opponent = np.array(opponent)
    
    # Valid moves are non-empty houses
    valid_moves = [i for i in range(6) if you[i] > 0]
    
    if not valid_moves:
        # Should not happen according to problem statement
        return 0
    
    # 1. Check for moves that result in capture
    capture_moves = []
    for move in valid_moves:
        # Simulate the move
        seeds = you[move]
        if seeds == 0:
            continue
            
        # Calculate where the last seed will land
        # Positions: 0-5 = your houses, 6 = your store, 7-12 = opponent houses
        end_pos = move + seeds
        
        # Check for capture: last seed in your empty house, opponent has seeds in opposite house
        if move <= end_pos <= 5:  # Last seed lands in your house
            final_house = end_pos
            # Need to check what the house count would be after sowing
            # This requires a more detailed simulation
            
            # Let's do a detailed simulation for this move
            new_you = you.copy()
            new_opponent = opponent.copy()
            last_pos = simulate_move_detailed(new_you, new_opponent, move, True)
            
            # Check if it's a capture
            if last_pos[0] == 'you' and 0 <= last_pos[1] <= 5:
                if new_you[last_pos[1]] == 1 and you[last_pos[1]] == 0 and opponent[5-last_pos[1]] > 0:
                    # This was a capture!
                    capture_moves.append((move, opponent[5-last_pos[1]] + 1))  # Value is captured seeds
    
    # Pick the capture with the most seeds
    if capture_moves:
        capture_moves.sort(key=lambda x: x[1], reverse=True)
        return capture_moves[0][0]
    
    # 2. Check for extra turn (last seed in store)
    extra_turn_moves = []
    for move in valid_moves:
        seeds = you[move]
        end_pos = move + seeds
        if end_pos == 6:  # Last seed lands in your store
            extra_turn_moves.append(move)
    
    if extra_turn_moves:
        # Prefer extra turn that also maximizes seed distribution
        best_extra = None
        max_seeds = -1
        for move in extra_turn_moves:
            seeds = you[move]
            if seeds > max_seeds:
                max_seeds = seeds
                best_extra = move
        return best_extra
    
    # 3. Avoid giving opponent easy captures
    # Try to avoid moves that end in opponent houses when they're empty on our side
    
    # 4. Evaluate moves by some heuristic
    move_scores = []
    for move in valid_moves:
        # Simulate move to get more info
        new_you = you.copy()
        new_opponent = opponent.copy()
        last_pos = simulate_move_detailed(new_you, new_opponent, move, True)
        
        score = 0
        seeds_moved = you[move]
        
        # Bonus for seeds moved
        score += seeds_moved * 0.1
        
        # Bonus for ending close to store (seeds closer to scoring)
        if last_pos[0] == 'you' and 0 <= last_pos[1] <= 5:
            distance_to_store = 6 - last_pos[1]
            score += (6 - distance_to_store) * 0.05
            
            # Bonus for potential future captures
            if new_you[last_pos[1]] == 1 and opponent[5-last_pos[1]] > 0:
                score += (opponent[5-last_pos[1]] + 1) * 0.5
                
        move_scores.append((move, score))
    
    # Sort by score descending
    move_scores.sort(key=lambda x: x[1], reverse=True)
    
    # 5. Return the best move
    if move_scores:
        return move_scores[0][0]
    
    # Fallback
    return valid_moves[0]


def simulate_move_detailed(you, opponent, move, update_arrays=False):
    """
    Simulate a move and return where the last seed was placed.
    Returns tuple: ('you'|'opponent', position_index) or ('store', 6)
    If update_arrays is True, modifies the arrays with the result.
    """
    if you[move] == 0:
        return ('you', move)
    
    seeds = you[move]
    if update_arrays:
        you[move] = 0
    
    current_pos = move + 1  # Next position after the moved house
    side = 'you'  # 'you', 'opponent', 'you_store'
    
    for _ in range(seeds):
        if side == 'you':
            if current_pos < 6:  # Your houses
                if update_arrays:
                    you[current_pos] += 1
                current_pos += 1
            elif current_pos == 6:  # Your store
                if update_arrays:
                    you[6] += 1
                # Move to opponent side
                side = 'opponent'
                current_pos = 0
            else:
                # Should not happen
                side = 'opponent'
                current_pos = 0
                
        elif side == 'opponent':
            if current_pos < 6:  # Opponent houses
                if update_arrays:
                    opponent[current_pos] += 1
                current_pos += 1
            else:
                # Back to your side
                side = 'you'
                current_pos = 0
    
    # Adjust position to be the last position where seed was placed
    if side == 'you' and current_pos > 0:
        return ('you', current_pos - 1)
    elif side == 'you' and current_pos == 0:
        # We moved past our houses, but didn't reach store - should cycle back,
        # but we just placed in our last house (5)
        return ('you', 5)
    elif side == 'opponent' and current_pos > 0:
        return ('opponent', current_pos - 1)
    elif side == 'opponent' and current_pos == 0:
        # Just placed in opponent's last house (5)
        return ('opponent', 5)
    elif side == 'you_store':
        return ('store', 6)
    else:  # Last seed in your store
        return ('store', 6)

# Let's simplify the simulation
def simulate_move_detailed(you, opponent, move, update_arrays=False):
    """
    Simulate a move and return where the last seed was placed.
    Returns ('you', index) or ('opponent', index) or ('store', 6)
    """
    # Create copies if not updating originals
    if not update_arrays:
        you = you.copy()
        opponent = opponent.copy()
    
    seeds = you[move]
    you[move] = 0
    
    # Position tracking: 0-5=your houses, 6=your store, 7-12=opponent houses, 13-18=your houses, etc.
    current_pos = move
    
    for i in range(seeds):
        current_pos += 1
        
        # Handle position mapping
        if current_pos < 6:  # Your houses
            you[current_pos] += 1
        elif current_pos == 6:  # Your store
            you[6] += 1
        elif 7 <= current_pos <= 12:  # Opponent houses
            opponent[current_pos - 7] += 1
        elif current_pos == 13:  # Back to your houses
            you[0] += 1
            current_pos = 0  # Reset position tracking after wrapping
        elif current_pos > 13:
            # Wrap around again
            pos_in_cycle = (current_pos - 7) % 13  # Remove the first 7 positions (0-6)
            if pos_in_cycle < 6:  # Your houses
                you[pos_in_cycle] += 1
                # Adjust current_pos for next iteration
                cycle_index = (current_pos - 7) // 13
                current_pos = pos_in_cycle
            elif pos_in_cycle == 6:  # Your store again
                you[6] += 1
                cycle_index = (current_pos - 7) // 13
                current_pos = 6
            else:  # Opponent houses again
                opponent[pos_in_cycle - 7] += 1
                cycle_index = (current_pos - 7) // 13
                current_pos = pos_in_cycle
    
    # Determine where the last seed landed
    final_pos = move + seeds
    if move + seeds < 6:
        return ('you', move + seeds)
    elif move + seeds == 6:
        return ('store', 6)
    else:
        effective_pos = (move + seeds - 7) % 13
        if effective_pos < 6:
            return ('you', effective_pos)
        elif effective_pos == 6:
            return ('store', 6)
        else:
            return ('opponent', effective_pos - 7)

# Even simpler implementation:
def simulate_move_detailed(you, opponent, move, update_arrays=False):
    you_copy = you.copy()
    opponent_copy = opponent.copy()
    
    if not update_arrays:
        you = you_copy
        opponent = opponent_copy
    
    seeds = you[move]
    you[move] = 0
    
    position = move
    side = "you"  # 'you', 'you_store', 'opponent'
    
    for i in range(seeds):
        position += 1
        
        if side == "you":
            if position < 6:
                you[position] += 1
            elif position == 6:
                you[6] += 1
                side = "opponent"
                position = -1  # Will become 0 after increment
            else:
                side = "opponent"
                position = 0
                opponent[position] += 1
                
        elif side == "opponent":
            if position < 6:
                opponent[position] += 1
            else:
                side = "you"
                position = 0
                you[position] += 1
    
    # Return the final position
    if side == "you":
        return ("you", position)
    elif side == "opponent":
        return ("opponent", position)
    else:
        return ("store", 6)

def policy(you: list[int], opponent: list[int]) -> int:
    """
    Implements a Kalah move-selection policy.
    """
    # Valid moves
    valid_moves = [i for i in range(6) if you[i] > 0]
    if not valid_moves:
        return 0

    # Prioritize captures
    for move in valid_moves:
        # Calculate where last seed lands
        seeds = you[move]
        end_pos = move + seeds
        
        # Handle wrapping
        # Positions: 0-5 (your houses), 6 (your store), 7-12 (opponent houses), 
        # 13-18 (your houses), 19 (your store), etc.
        
        # Check if it's a capture
        if move <= end_pos <= 5:  # Ends in your house
            # Simulate to see if house was empty before capture
            new_you = you.copy()
            new_opponent = opponent.copy()
            
            # Do the sowing
            seeds_to_sow = new_you[move]
            new_you[move] = 0
            pos = move
            side = 'you'
            
            for _ in range(seeds_to_sow):
                pos += 1
                if side == 'you':
                    if pos < 6:
                        new_you[pos] += 1
                    elif pos == 6:
                        new_you[6] += 1
                        side = 'opponent'
                        pos = -1
                    else:
                        side = 'opponent'
                        pos = 0
                        new_opponent[pos] += 1
                elif side == 'opponent':
                    if pos < 5:
                        pos += 1
                        new_opponent[pos] += 1
                    elif pos == 5:
                        pos = 6
                        new_opponent[5] += 1
                        side = 'you'
                        pos = -1
                    else:
                        side = 'you'
                        pos = 0
                        new_you[pos] += 1
                        
            # Check for capture
            end_side = side
            end_index = pos
            
            if end_side == 'you' and 0 <= end_index <= 5:
                if new_you[end_index] == 1 and you[end_index] == 0 and opponent[5 - end_index] > 0:
                    return move

    # Look for extra turn
    for move in valid_moves:
        seeds = you[move]
        if (move + seeds) % 13 == 6 or (move + seeds) % 14 == 6:  # Lands in store
            return move
    
    # Prefer moves that score more points or advance position
    best_move = valid_moves[0]
    max_seeds = -1
    
    for move in valid_moves:
        if you[move] > max_seeds:
            max_seeds = you[move]
            best_move = move
            
    return best_move
