
def policy(you: list[int], opponent: list[int]) -> int:
    best_score = -10**9
    best_move = None
    for i in range(6):
        if you[i] == 0:
            continue
        # Simulate the move
        seeds = you[i]
        new_you = you.copy()
        new_opponent = opponent.copy()
        new_you[i] = 0
        current_index = i + 1
        last_position = None
        captures = 0
        
        while seeds > 0:
            if 0 <= current_index <= 5:
                if new_you[current_index] == 0:
                    opp_index = 5 - current_index
                    if new_opponent[opp_index] > 0:
                        captures += 1
                        new_you[6] += 1 + new_opponent[opp_index]
                        new_you[current_index] = 0
                        new_opponent[opp_index] = 0
                else:
                    new_you[current_index] += 1
                last_position = current_index
                seeds -= 1
                current_index += 1
            elif current_index == 6:
                new_you[6] += 1
                last_position = 6
                seeds -= 1
                current_index = 0
            elif 7 <= current_index <= 12:
                opp_index = current_index - 7
                new_opponent[opp_index] += 1
                last_position = opp_index
                seeds -= 1
                current_index += 1
            else:
                current_index = 0
        
        extra_move = (last_position == 6)
        seeds_in_your_houses = sum(new_you[:6])
        score = (new_you[6] - new_opponent[6]) + seeds_in_your_houses + captures + (1 if extra_move else 0)
        
        if score > best_score:
            best_score = score
            best_move = i
    
    return best_move
