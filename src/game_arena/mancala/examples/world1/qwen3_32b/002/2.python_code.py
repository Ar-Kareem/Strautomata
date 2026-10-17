
def policy(you: list[int], opponent: list[int]) -> int:
    
    def simulate_move(you_state, opp_state, move_index):
        new_you = you_state.copy()
        new_opponent = opp_state.copy()
        s = new_you[move_index]
        if s == 0:
            return (new_you, new_opponent, False)
        new_you[move_index] = 0
        seeds_left = s
        last_seed_before_value = -1
        last_seed_pos_info = None
        current_house = move_index + 1
        phase = 'your_initial'
        while seeds_left > 0:
            is_last_seed = (seeds_left == 1)
            if phase == 'your_initial':
                if current_house <= 5:
                    prev_val = new_you[current_house]
                    new_you[current_house] += 1
                    if is_last_seed:
                        last_seed_before_value = prev_val
                        last_seed_pos_info = ('you', current_house)
                    current_house += 1
                    seeds_left -= 1
                else:
                    phase = 'your_store'
            elif phase == 'your_store':
                prev_val = new_you[6]
                new_you[6] += 1
                if is_last_seed:
                    last_seed_before_value = prev_val
                    last_seed_pos_info = ('you_store', 6)
                seeds_left -= 1
                phase = 'opponent'
                current_house = 0
            elif phase == 'opponent':
                if current_house <= 5:
                    prev_val = new_opponent[current_house]
                    new_opponent[current_house] += 1
                    if is_last_seed:
                        last_seed_before_value = prev_val
                        last_seed_pos_info = ('opponent', current_house)
                    current_house += 1
                    seeds_left -= 1
                else:
                    phase = 'your_again'
                    current_house = 0
            elif phase == 'your_again':
                if current_house <= 5:
                    prev_val = new_you[current_house]
                    new_you[current_house] += 1
                    if is_last_seed:
                        last_seed_before_value = prev_val
                        last_seed_pos_info = ('you', current_house)
                    current_house += 1
                    seeds_left -= 1
                else:
                    phase = 'your_store_again'
            elif phase == 'your_store_again':
                prev_val = new_you[6]
                new_you[6] += 1
                if is_last_seed:
                    last_seed_before_value = prev_val
                    last_seed_pos_info = ('you_store', 6)
                seeds_left -= 1
                phase = 'opponent'
                current_house = 0
            else:
                raise ValueError(f"Unknown phase: {phase}")
        # Check for capture or extra move
        extra_move = False
        if last_seed_pos_info is not None:
            if last_seed_pos_info[0] == 'you':
                house_idx = last_seed_pos_info[1]
                if last_seed_before_value == 0:
                    opposite_idx = 5 - house_idx
                    if new_opponent[opposite_idx] > 0:
                        # perform capture
                        captured_seeds = new_you[house_idx] + new_opponent[opposite_idx]
                        new_you[6] += captured_seeds
                        new_you[house_idx] = 0
                        new_opponent[opposite_idx] = 0
            elif last_seed_pos_info[0] == 'you_store':
                extra_move = True
        return (new_you, new_opponent, extra_move)
    
    def evaluate(you_state, opp_state):
        my_store = you_state[6]
        opp_store = opp_state[6]
        my_houses = sum(you_state[:6])
        opp_houses = sum(opp_state[:6])
        return (my_store - opp_store) + (my_houses - opp_houses)
    
    legal_moves = [i for i in range(6) if you[i] > 0]
    best_score = -float('inf')
    best_move = legal_moves[0]
    for move in legal_moves:
        new_you, new_opponent, extra_move = simulate_move(you, opponent, move)
        score = evaluate(new_you, new_opponent)
        if extra_move:
            score += 10  # bonus for extra move
        if score > best_score:
            best_score = score
            best_move = move
    return best_move
