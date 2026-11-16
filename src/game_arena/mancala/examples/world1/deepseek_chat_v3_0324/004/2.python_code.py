
import numpy as np

def policy(you: list[int], opponent: list[int]) -> int:
    best_move = 0
    max_score = -float('inf')
    
    for i in range(6):
        if you[i] == 0:
            continue
            
        # Simulate the move
        temp_you = you.copy()
        temp_opp = opponent.copy()
        seeds = temp_you[i]
        temp_you[i] = 0
        pos = i + 1
        last_pos_store = False
        last_pos_house = -1
        
        # Distribute seeds
        while seeds > 0:
            # Your houses
            while pos < 6 and seeds > 0:
                temp_you[pos] += 1
                seeds -= 1
                last_pos_store = False
                last_pos_house = pos
                pos += 1
                
            # Your store
            if seeds > 0:
                temp_you[6] += 1
                seeds -= 1
                last_pos_store = True
                last_pos_house = -1
                pos = 0
                
            # Opponent's houses (skip their store)
            if seeds > 0:
                for j in range(6):
                    if seeds == 0:
                        break
                    temp_opp[j] += 1
                    seeds -= 1
                    last_pos_store = False
                    last_pos_house = -1  # opponent's side doesn't count for capture
        
        # Evaluate the move
        score = 0
        
        # Extra turn bonus
        if last_pos_store:
            score += 1000  # high priority for extra moves
            
        # Capture opportunity
        if (not last_pos_store) and (0 <= last_pos_house < 6):
            if temp_you[last_pos_house] == 1 and temp_opp[5 - last_pos_house] > 0:
                captured = 1 + temp_opp[5 - last_pos_house]
                score += captured * 100  # high priority for captures
        
        # Seed gain difference (store and potential captures)
        score += (temp_you[6] - you[6]) * 10
        
        # Prefer moves that leave opponent with fewer options
        opponent_houses = sum(temp_opp[:6])
        score -= opponent_houses * 0.1  # small penalty for giving opponent seeds
        
        # Update best move
        if score > max_score or (score == max_score and you[i] > you[best_move]):
            max_score = score
            best_move = i
            
    return best_move
