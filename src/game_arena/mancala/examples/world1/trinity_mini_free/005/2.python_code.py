
def policy(you, opponent):
    def simulate_move(you, opponent, i):
        seeds = you[i]
        you[i] = 0
        last_house = None
        current = (i + 1) % 7
        while seeds > 0:
            you[current] += 1
            seeds -= 1
            last_house = current
            current = (current + 1) % 7
        if 0 <= last_house <= 5:
            if opponent[5 - i] > 0:
                you[6] += 1 + opponent[5 - i]
                opponent[5 - i] = 0
                you[last_house] = 0
        return you, opponent, (last_house == 6)
    
    best_move = None
    best_gain = -1
    best_extra = False
    for i in range(7):
        if you[i] == 0:
            continue
        you_copy = you.copy()
        opponent_copy = opponent.copy()
        new_you, new_opponent, extra = simulate_move(you_copy, opponent_copy, i)
        gain = new_you[6] - you[6]
        if gain > best_gain:
            best_gain = gain
            best_move = i
            best_extra = extra
        elif gain == best_gain:
            if extra and not best_extra:
                best_move = i
                best_extra = extra
            elif extra and best_extra:
                if i < best_move:
                    best_move = i
            else:
                if i < best_move:
                    best_move = i
    return best_move
