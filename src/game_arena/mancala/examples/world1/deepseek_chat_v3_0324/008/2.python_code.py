
import numpy as np

def policy(you: list[int], opponent: list[int]) -> int:
    best_move = None
    best_score = -np.inf
    
    for move in range(6):
        if you[move] == 0:
            continue
        
        # Simulate the move
        temp_you = you.copy()
        temp_opp = opponent.copy()
        seeds = temp_you[move]
        temp_you[move] = 0
        pos = move + 1
        
        last_pos = None
        for _ in range(seeds):
            # Distribute seeds
            if pos < 6:
                temp_you[pos] += 1
                last_pos = ('you', pos)
                pos += 1
            elif pos == 6:
                temp_you[6] += 1
                last_pos = ('store', 6)
                pos += 1
            else:
                # Opponent's side
                opp_pos = pos - 7
                if opp_pos < 6:
                    temp_opp[opp_pos] += 1
                    last_pos = ('opp', opp_pos)
                    pos += 1
                else:
                    # Skip opponent's store
                    pos = 0
                    temp_you[0] += 1
                    last_pos = ('you', 0)
                    pos += 1
        
        # Check for extra move
        if last_pos == ('store', 6):
            score = 1000  # Highest priority
        else:
            # Check for capture
            capture_score = 0
            if last_pos[0] == 'you' and last_pos[1] < 6:
                if temp_you[last_pos[1]] == 1 and temp_opp[5 - last_pos[1]] > 0:
                    capture_score = 500 + temp_opp[5 - last_pos[1]]
            
            # Base score is seeds added to store
            base_score = temp_you[6] - you[6]
            
            score = base_score + capture_score
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
