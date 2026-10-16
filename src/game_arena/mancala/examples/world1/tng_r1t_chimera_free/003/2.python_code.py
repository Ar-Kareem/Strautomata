
import copy

def policy(you: list[int], opponent: list[int]) -> int:
    best_move = -1
    highest_score = -float('inf')
    
    for i in [i for i in range(6) if you[i] > 0]:
        sim_you = copy.deepcopy(you)
        sim_opp = copy.deepcopy(opponent)
        seeds = sim_you[i]
        sim_you[i] = 0
        current_side = 'you'
        current_pos = i + 1
        last_house = None
        last_idx = -1
        
        for _ in range(seeds):
            if current_side == 'you':
                if current_pos < 6:
                    sim_you[current_pos] += 1
                    last_house = 'you'
                    last_idx = current_pos
                    current_pos += 1
                elif current_pos == 6:
                    sim_you[6] += 1
                    last_house = 'store'
                    last_idx = 6
                    current_side = 'opponent'
                    current_pos = 0
                else:
                    current_side = 'opponent'
                    current_pos = 0
                    sim_you[6] += 1
                    last_house = 'store'
                    last_idx = 6
            else:
                if current_pos < 6:
                    sim_opp[current_pos] += 1
                    last_house = 'opponent'
                    last_idx = current_pos
                    current_pos += 1
                else:
                    current_side = 'you'
                    current_pos = 0
                    sim_you[current_pos] += 1
                    last_house = 'you'
                    last_idx = current_pos
                    current_pos += 1
        
        extra_turn = (last_house == 'store')
        capture = 0
        if last_house == 'you' and sim_you[last_idx] == 1 and sim_opp[5 - last_idx] > 0:
            capture = sim_you[last_idx] + sim_opp[5 - last_idx]
            sim_you[6] += capture
            sim_you[last_idx] = 0
            sim_opp[5 - last_idx] = 0
        
        store_gain = sim_you[6] - you[6]
        
        score = 0
        if extra_turn:
            score += 1000
        if capture > 0:
            score += 500 + capture * 2
        score += store_gain
        
        if score > highest_score:
            highest_score = score
            best_move = i
            
    return best_move
