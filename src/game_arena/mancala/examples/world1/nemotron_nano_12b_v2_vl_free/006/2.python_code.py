
import copy

def simulate_move(start, you, opponent):
    new_you = copy.deepcopy(you)
    new_opponent = copy.deepcopy(opponent)
    
    if new_you[start] == 0:
        return new_you, new_opponent, False, 0, 0
    
    stones = new_you[start]
    new_you[start] = 0
    current_house = (start + 1) % 7  # 0-6: your house and store, 6 is store
    last_house = None
    new_stones = stones  # number of stones to sow
    
    while new_stones > 0:
        if current_house <= 5:  # Your own house
            new_you[current_house] += 1
            last_house = current_house
        elif current_house == 6:  # Your store
            new_you[current_house] += 1
            last_house = current_house
        else:  # Opponents house
            opp_idx = current_house - 6  # 7-11 maps to 0-5
            new_opponent[opp_idx] += 1
            last_house = None  # Not in your houses/store
        
        current_house = (current_house + 1) % 7
        new_stones -= 1
    
    # Check for capture
    captured_you = 0
    captured_opponent = 0
    is_capture = False
    if last_house is not None and last_house < 6:  # Last drop in your house
        if you[last_house] == 0:  # Was empty
            opposite = 5 - last_house
            opp_seeds = opponent[opposite]
            if opp_seeds > 0:
                captured = opp_seeds + 1  # Take opponent's seeds plus the one you just placed
                captured_you += captured
                new_you[6] += captured
                new_you[last_house] = 0
                new_opponent[opposite] = 0
                is_capture = True
    
    # Check for extra move (last stone in store)
    has_extra = new_you[6] > 0 and (stone_count -1 == current_house == 6)
    return new_you, new_opponent, is_capture, current_house, captured_you

def policy(you, opponent):
    best_move = None
    best_score = -float('inf')
    
    for move in range(6):
        if you[move] == 0:
            continue
        
        # Simulate move
        new_you, new_opp, is_capture, last_house, captured_you = simulate_move(move, you, opponent)
        
        # Evaluate the move based on captures and future score potential
        new_store_diff = new_you[6] - new_opponent[6]
        house_diff = sum(new_you[:6]) - sum(new_opp[:6])
        score = captured_you - new_opponent[6]  # Prioritize immediate capture gain
        
        # Adjust score based on heuristics
        eval_score = score + (new_store_diff * 2) + (house_diff * 1)
        
        if eval_score > best_score:
            best_score = eval_score
            best_move = move
    
    return best_move
