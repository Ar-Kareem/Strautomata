
from collections import defaultdict

def policy(you, opponent):
    best_move = -1
    best_heuristic = -float('inf')
    
    for i in range(6):
        if you[i] == 0:
            continue
        
        # Simulate the move
        new_you = list(you)
        new_opponent = opponent[:]
        s = new_you[i]
        new_you[i] = 0
        
        pits_order = []
        # Step 1: Your own houses from i+1 to 5
        for j in range(move_i + 1, 6):
            pits_order.append(('you', j))
        # Step 2: Your store
        pits_order.append(('you', 6))
        # Step 3: Opponent's houses 0 to 5
        for j in range(6):
            pits_order.append(('opponent', j))
        # Step 4: Your houses 0 to 5
        for j in range(6):
            pits_order.append(('you', j))
        
        len_pits = len(pits_order)
        cycles, rem = divmod(s, len_pits)
        
        # Distribute seeds efficiently
        new_you_sim = new_you.copy()
        new_opp_sim = new_opponent.copy()
        last_pit = None
        
        for idx_in_pits in range(len(pits_order)):
            house_type, idx = pits_order[idx_in_pits]
            count = cycles
            if idx_in_pits < rem:
                count += 1
            
            if house_type == 'you':
                if idx == 6:
                    new_you_sim[6] += count
                else:
                    new_you_sim[idx] += count
            elif house_type == 'opponent':
                new_opponent[idx] += count
            
            last_pit = (house_type, idx)
        
        # Calculate captured seeds and extra move
        captured = 0
        extra_move = False
        if len_pits > 0:
            last_pit_type, last_idx = pits_order[last_pit_in_order]
            if last_pit_type == 'you' and last_idx < 6:
                if (last_idx == move_i and you[last_idx] == 0) or (last_idx != move_i and you[last_idx] == 0):
                    opponent_opposite = 5 - last_idx
                    if new_opponent[opponent_opposite] > 0:
                        captured = new_you[last_idx] + new_opponent[opponent_opposite]
                        new_you[6] += captured
                        new_you[last_idx] = 0
                        new_opponent[opponent_opposite] = 0
                elif (last_idx != move_i and you[last_idx] == 0) and new_opponent[5 - last_idx] > 0:
                    captured = new_you[last_idx] + new_opponent[5 - last_idx]
                    new_you[6] += captured
                    new_you[last_idx] = 0
                    new_opponent[5 - last_idx] = 0
            
            if last_pit_type == 'you' and last_idx == 6:
                extra_move = True
        
        # Heuristic score
        score = captured * 100 + (1000 if extra_move else 0)
        if score > best_heuristic or (score == best_heuristic and captured > best_captured):
            best_heuristic = score
            best_move = i
    
    return best_move
