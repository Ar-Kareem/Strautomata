
def policy(you, opponent):
    def simulate_move(you_state, opponent_state, move_idx):
        new_you = you_state[:]
        new_opponent = opponent_state[:]
        seeds = new_you[move_idx]
        new_you[move_idx] = 0
        current = 'you'
        pos = move_idx + 1
        extra_move = 0
        last_drop = None
        
        while seeds > 0:
            if seeds == 1:
                last_drop = (current, pos)
                
            if current == 'you':
                if pos < 6:
                    if seeds == 1:
                        if new_you[pos] == 0 and new_opponent[5 - pos] > 0:
                            new_you[pos] = 1
                            captured = 1 + new_opponent[5 - pos]
                            new_you[6] += captured
                            new_you[pos] = 0
                            new_opponent[5 - pos] = 0
                        else:
                            new_you[pos] += 1
                    else:
                        new_you[pos] += 1
                    if pos < 5:
                        pos += 1
                    else:
                        pos = 6
                else:
                    new_you[6] += 1
                    current = 'opponent'
                    pos = 0
            else:
                new_opponent[pos] += 1
                if pos < 5:
                    pos += 1
                else:
                    current = 'you'
                    pos = 0
            seeds -= 1
                    
        if last_drop is not None and last_drop[0] == 'you' and last_drop[1] == 6:
            extra_move = 1
            
        if all(new_opponent[i] == 0 for i in range(6)):
            total = sum(new_you[0:6])
            new_you[6] += total
            new_you[0:6] = [0] * 6
            
        if all(new_you[i] == 0 for i in range(6)):
            total = sum(new_opponent[0:6])
            new_opponent[6] += total
            new_opponent[0:6] = [0] * 6
            
        return new_you, new_opponent, extra_move
    
    def evaluate(new_you, new_opponent, extra_move_bonus):
        store_score = new_you[6] - new_opponent[6]
        house_score = 0.1 * (sum(new_you[0:6]) - sum(new_opponent[0:6]))
        extra_move_score = 0.2 * extra_move_bonus
        return store_score + house_score + extra_move_score
        
    legal_moves = [i for i in range(6) if you[i] > 0]
    best_move = None
    best_score = -float('inf')
    
    for move_idx in legal_moves:
        new_you, new_opponent, extra_move = simulate_move(you, opponent, move_idx)
        score = evaluate(new_you, new_opponent, extra_move)
        if score > best_score:
            best_score = score
            best_move = move_idx
            
    return best_move
