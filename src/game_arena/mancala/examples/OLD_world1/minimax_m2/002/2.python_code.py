
def simulate_move(you, opponent, i):
    if you[i] == 0:
        return you, opponent, False
        
    seeds = you[i]
    new_you = you[:]
    new_opp = opponent[:]
    new_you[i] = 0
    
    pos = (i + 1) % 13
    for _ in range(seeds - 1):
        if pos == 0:
            new_you[0] += 1
        elif 1 <= pos <= 5:
            new_you[pos] += 1
        elif pos == 6:
            new_you[6] += 1
        else:
            new_opp[pos - 7] += 1
        pos = (pos + 1) % 13
        
    last_pos = pos
    if last_pos in [0, 1, 2, 3, 4, 5]:
        new_you[last_pos] += 1
        if new_you[last_pos] == 1:
            if new_opp[5 - last_pos] > 0:
                capture_seeds = new_you[last_pos] + new_opp[5 - last_pos]
                new_you[6] += capture_seeds
                new_you[last_pos] = 0
                new_opp[5 - last_pos] = 0
    elif last_pos == 6:
        new_you[6] += 1
    else:
        new_opp[last_pos - 7] += 1
        
    extra_move = (last_pos == 6)
    return new_you, new_opp, extra_move

def policy(you, opponent):
    best_move = None
    best_gain = -10**9
    
    for i in range(6):
        if you[i] == 0:
            continue
        new_you, new_opp, extra = simulate_move(you, opponent, i)
        gain = new_you[6] - you[6]
        if extra:
            gain += 10
        if gain > best_gain:
            best_gain = gain
            best_move = i
            
    return best_move
