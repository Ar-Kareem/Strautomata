
import numpy as np

def policy(you: list[int], opponent: list[int]) -> int:
    """
    Selects the best move according to the following priorities:
    1. Moves that give an extra turn
    2. Moves that capture opponent's seeds
    3. Moves that maximize immediate store gain
    4. Rightmost legal move (house 5) as default
    """
    best_move = None
    max_gain = -1
    best_score = -1
    
    for i in [5, 4, 3, 2, 1, 0]:  # Check right to left
        if you[i] == 0:
            continue
            
        # Simulate the move
        seeds = you[i]
        new_you = you.copy()
        new_opp = opponent.copy()
        new_you[i] = 0
        pos = i + 1
        
        # Distribute seeds
        last_pos = None
        for _ in range(seeds):
            # Your houses
            while pos <= 5:
                if seeds == 0:
                    break
                new_you[pos] += 1
                seeds -= 1
                last_pos = ('you', pos)
                pos += 1
                if seeds == 0:
                    break
            
            # Your store
            if seeds > 0:
                new_you[6] += 1
                seeds -= 1
                last_pos = ('you', 6)
                if seeds == 0:
                    break
            
            # Opponent's houses
            if seeds > 0:
                pos = 0
                while pos <= 5:
                    if seeds == 0:
                        break
                    new_opp[pos] += 1
                    seeds -= 1
                    last_pos = ('opp', pos)
                    pos += 1
                    if seeds == 0:
                        break
        
        # Check for extra turn
        if last_pos == ('you', 6):
            return i  # Always take the extra move
        
        # Check for capture
        if (last_pos[0] == 'you' and last_pos[1] != 6 and 
            new_you[last_pos[1]] == 1 and you[last_pos[1]] == 0 and
            new_opp[5 - last_pos[1]] > 0):
            capture_score = 1 + new_opp[5 - last_pos[1]]
            if capture_score > best_score:
                best_move = i
                best_score = capture_score
        
        # Check store gain
        store_gain = new_you[6] - you[6]
        if best_move is None or store_gain > max_gain:
            max_gain = store_gain
            if best_score == -1:  # Only overwrite if no capture was found
                best_move = i
    
    # Return best move found (extra turn, capture, or max gain)
    return best_move if best_move is not None else max([i for i in range(6) if you[i] > 0], key=lambda x: you[x])
