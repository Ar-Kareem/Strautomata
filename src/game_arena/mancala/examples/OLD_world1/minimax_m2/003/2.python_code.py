
def simulate_move(you, opponent, i):
    new_you = you[:]
    new_opponent = opponent[:]
    seeds = new_you[i]
    if seeds == 0:
        return None, None, False
    new_you[i] = 0
    current_player = 'you'
    current_index = i
    last_house = None
    
    while seeds > 0:
        current_index += 1
        if current_player == 'you':
            if current_index == 7:
                current_player = 'opponent'
                current_index = 0
            else:
                new_you[current_index] += 1
                seeds -= 1
                last_house = ('you', current_index)
        else:
            if current_index == 6:
                current_player = 'you'
                current_index = 0
            else:
                new_opponent[current_index] += 1
                seeds -= 1
                last_house = ('opponent', current_index)
                
    if last_house[0] == 'you' and 0 <= last_house[1] <= 5:
        if new_you[last_house[1]] == 1:
            opposite_index = 5 - last_house[1]
            if new_opponent[opposite_index] > 0:
                captured_seeds = new_you[last_house[1]] + new_opponent[opposite_index]
                new_you[6] += captured_seeds
                new_you[last_house[1]] = 0
                new_opponent[opposite_index] = 0
                
    extra_move = (last_house[0] == 'you' and last_house[1] == 6)
    return new_you, new_opponent, extra_move

def policy(you, opponent):
    best_move = -1
    best_score = -10**9
    
    for i in range(6):
        if you[i] == 0:
            continue
            
        new_you, new_opponent, extra_move = simulate_move(you, opponent, i)
        
        if sum(new_opponent[0:6]) == 0:
            our_remaining = sum(new_you[0:6])
            new_you[6] += our_remaining
            new_you[0:6] = [0] * 6
            score = (new_you[6] - new_opponent[6]) * 100
        elif sum(new_you[0:6]) == 0:
            opp_remaining = sum(new_opponent[0:6])
            new_opponent[6] += opp_remaining
            new_opponent[0:6] = [0] * 6
            score = (new_you[6] - new_opponent[6]) * 100
        else:
            score = (new_you[6] - new_opponent[6]) * 100 + (sum(new_you[0:6]) - sum(new_opponent[0:6]))
            
        if extra_move:
            score += 50
            
        if score > best_score:
            best_score = score
            best_move = i
            
    return best_move
