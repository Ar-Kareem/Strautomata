
def policy(you: list[int], opponent: list[int]) -> int:
    def simulate_move(you, opponent, move_idx):
        you_copy = list(you)
        opponent_copy = list(opponent)
        count = you_copy[move_idx]
        if count == 0:
            return (you, opponent, False, False)
        you_copy[move_idx] = 0
        current_side = 'you'
        current_pos = move_idx
        prev_last_value = 0
        for step in range(count):
            if current_side == 'you':
                if current_pos < 6:
                    if current_pos == 5:
                        next_side = 'you'
                        next_pos = 6
                    else:
                        next_side = 'you'
                        next_pos = current_pos + 1
                else:  # current_pos == 6 (store)
                    next_side = 'opponent'
                    next_pos = 0
            else:  # current_side is 'opponent'
                if current_pos < 5:
                    next_side = 'opponent'
                    next_pos = current_pos + 1
                else:  # current_pos == 5
                    next_side = 'you'
                    next_pos = 0

            is_last_step = (step == count - 1)
            if is_last_step:
                if next_side == 'you':
                    if next_pos == 6:
                        prev_last_value = you_copy[6]
                    else:
                        prev_last_value = you_copy[next_pos]
                else:  # opponent
                    if next_pos == 6:
                        prev_last_value = opponent_copy[6]
                    else:
                        prev_last_value = opponent_copy[next_pos]

            current_side, current_pos = next_side, next_pos

            if current_side == 'you':
                if current_pos == 6:
                    you_copy[6] += 1
                else:
                    you_copy[current_pos] += 1
            else:  # opponent
                if current_pos == 6:
                    pass  # invalid, but prevented by logic
                else:
                    opponent_copy[current_pos] += 1

        extra_turn = False
        if current_side == 'you' and current_pos == 6:
            extra_turn = True

        capture = False
        if current_side == 'you' and current_pos != 6:
            if prev_last_value == 0:
                opp_idx = 5 - current_pos
                if opponent_copy[opp_idx] > 0:
                    you_copy[6] += you_copy[current_pos] + opponent_copy[opp_idx]
                    you_copy[current_pos] = 0
                    opponent_copy[opp_idx] = 0
                    capture = True

        return (you_copy, opponent_copy, extra_turn, capture)

    def calculate_score(you, opponent, new_you, new_opponent, extra_turn, capture):
        original_store = you[6]
        new_store = new_you[6]
        store_gain = new_store - original_store
        score = store_gain * 10
        if capture:
            score += 50
        if extra_turn:
            score += 30
        my_seeds = sum(new_you[:6])
        opp_seeds = sum(new_opponent[:6])
        score += (my_seeds - opp_seeds) * 0.5
        return score

    best_move = -1
    best_score = -float('inf')
    for i in range(6):
        if you[i] == 0:
            continue
        new_you, new_opponent, extra_turn, capture = simulate_move(you, opponent, i)
        score = calculate_score(you, opponent, new_you, new_opponent, extra_turn, capture)
        if score > best_score or (best_move == -1 and score == best_score):
            best_score = score
            best_move = i
    return best_move
