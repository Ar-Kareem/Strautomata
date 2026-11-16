
def simulate_move(you, opp, move):
    y = [a for a in you]
    o = [a for a in opp]
    seeds = y[move]
    y[move] = 0
    
    pos_to_coords = [
        (0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), 
        (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (1, 5)
    ]
    
    if move < 5:
        from_index = move + 1
    else:
        from_index = 6
    
    last_pos = from_index
    for i in range(seeds):
        current_pos = (from_index + i) % 12
        last_pos = current_pos
        if pos_to_coords[current_pos][0] == 0:
            y[pos_to_coords[current_pos][1]] += 1
        else:
            o[pos_to_coords[current_pos][1]] += 1
    
    extra = (last_pos == 6)
    
    if 0 <= last_pos <= 5 and you[last_pos] == 0 and opp[5 - last_pos] > 0:
        y[6] += y[last_pos] + opp[5 - last_pos]
        y[last_pos] = 0
        opp[5 - last_pos] = 0
    
    return y, o, extra

def policy(you, opponent):
    legal = [i for i in range(6) if you[i] > 0]
    best_score = -500
    best_move = legal[0]
    
    for move in legal:
        y2, o2, extra = simulate_move(you, opponent, move)
        score = y2[6] - o2[6]
        if extra:
            score += 50
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
