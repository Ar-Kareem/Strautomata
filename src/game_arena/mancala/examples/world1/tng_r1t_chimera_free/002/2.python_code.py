
def policy(you: list[int], opponent: list[int]) -> int:
    import copy

    def simulate_move(you_state, opponent_state, move_i):
        you_copy = copy.copy(you_state)
        opp_copy = copy.copy(opponent_state)
        seeds = you_copy[move_i]
        you_copy[move_i] = 0
        current_pos = move_i + 1
        last_seed = None
        extra_turn = False
        captured = 0

        while seeds > 0:
            if current_pos < 6:
                you_copy[current_pos] += 1
                seeds -= 1
                last_seed = ('you', current_pos)
                current_pos += 1
            elif current_pos == 6:
                you_copy[6] += 1
                seeds -= 1
                last_seed = ('you', 6)
                current_pos += 1
            elif 7 <= current_pos <= 12:
                opp_pos = current_pos - 7
                opp_copy[opp_pos] += 1
                seeds -= 1
                last_seed = ('opponent', opp_pos)
                current_pos += 1
            else:
                current_pos = 0

            if current_pos > 13:
                current_pos = 0

        if last_seed and last_seed[0] == 'you':
            pos = last_seed[1]
            if pos == 6:
                extra_turn = True
            elif pos < 6 and you_copy[pos] == 1:
                opp_pos = 5 - pos
                if opp_copy[opp_pos] > 0:
                    captured = 1 + opp_copy[opp_pos]
                    you_copy[6] += captured
                    you_copy[pos] = 0
                    opp_copy[opp_pos] = 0

        return you_copy, opp_copy, extra_turn, captured

    original_store = you[6]
    best_move = -1
    best_score = -float('inf')

    for i in range(6):
        if you[i] == 0:
            continue

        new_you, new_opp, extra, capt = simulate_move(you, opponent, i)
        if extra:
            score = 1000 + capt
        elif capt > 0:
            score = 500 + capt
        else:
            score = new_you[6] - original_store

        if score > best_score or (score == best_score and i < best_move):
            best_score = score
            best_move = i

    return best_move
