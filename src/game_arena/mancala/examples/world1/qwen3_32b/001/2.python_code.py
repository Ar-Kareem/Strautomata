
def policy(you: list[int], opponent: list[int]) -> int:
    def simulate_move(i):
        you_copy = you.copy()
        opponent_copy = opponent.copy()
        
        seeds = you_copy[i]
        you_copy[i] = 0
        current_pos = i
        
        for _ in range(seeds):
            current_pos = (current_pos + 1) % 13  # 13 total positions: 6 houses, 1 store, 6 opponent houses
            
            if current_pos == 6:
                you_copy[6] += 1
            elif current_pos < 6:
                you_copy[current_pos] += 1
            else:
                idx = current_pos - 7
                opponent_copy[idx] += 1
                
        last_pos = current_pos
        extra_turn = False
        
        if last_pos == 6:
            extra_turn = True
        else:
            if last_pos < 6:
                prev_value = you_copy[last_pos] - 1
                if prev_value == 0:  # House was empty before drop
                    opposite_house = 5 - last_pos
                    if opponent_copy[opposite_house] > 0:
                        you_copy[6] += 1 + opponent_copy[opposite_house]
                        you_copy[last_pos] = 0
                        opponent_copy[opposite_house] = 0
        
        # Check if game ended
        your_houses_sum = sum(you_copy[:6])
        opp_houses_sum = sum(opponent_copy[:6])
        game_ended = False
        
        if your_houses_sum == 0 or opp_houses_sum == 0:
            game_ended = True
            if your_houses_sum == 0:
                # Opponent adds their remaining seeds to store
                opponent_copy[6] += sum(opponent_copy[:6])
                for j in range(6):
                    opponent_copy[j] = 0
            else:
                # You add your remaining seeds to store
                you_copy[6] += sum(you_copy[:6])
                for j in range(6):
                    you_copy[j] = 0
        
        return (you_copy, opponent_copy, extra_turn, game_ended)
    
    def evaluate(you_state, opp_state, extra_turn, game_ended):
        you_store = you_state[6]
        opp_store = opp_state[6]
        base_score = you_store - opp_store
        
        if game_ended:
            return base_score
        
        your_houses = sum(you_state[:6])
        opp_houses = sum(opp_state[:6])
        house_diff = (your_houses - opp_houses) * 0.5
        extra_turn_bonus = 10 if extra_turn else 0
        
        # Prefer positions where you have more options or can block opponent
        if your_houses > 0 and opp_houses == 0:
            return float('inf')  # Winning immediately is best
            
        return base_score + house_diff + extra_turn_bonus
    
    best_score = -float('inf')
    best_move = -1
    
    for i in range(6):
        if you[i] == 0:
            continue
        
        you_new, opp_new, extra, game = simulate_move(i)
        score = evaluate(you_new, opp_new, extra, game)
        
        if score > best_score:
            best_score = score
            best_move = i
    
    return best_move
