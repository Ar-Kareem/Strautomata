
def simulate_move(you, opponent, i):
    you_cpy = list(you)
    opponent_cpy = list(opponent)
    s = you_cpy[i]
    if s == 0:
        return new_you, new_opponent, False, 0

    y_copy = list(you_cpy)
    o_copy = list(opponent_cpy)
    taken_seeds = s
    y_copy[i] = 0
    current_pos = (i + 1) % 6
    last_pos = None

    for _ in range(s):
        owner = None
        if current_pos == 6:
            y_copy[6] += 1
            owner = 'store'
            last_pos = current_pos
            current_pos = 0
            new_pos = current_pos
        else:
            if current_pos > 5:
                current_pos = 0
                current_pos += 1
                continue

            if current_pos >= (i + 1):
                owner = 'you'
                y_copy[current_pos] += 1
            else:
                owner = 'opponent'
                o_copy[current_pos] += 1

            if current_pos == 5:
                next_p = 6
            else:
                next_p = current_pos + 1

            current_pos = next_pos
            if owner == 'your':
                last_pos = current_pos

    last_pos_after = current_pos
    extra = False
    capture = 0

    if last_pos_after == 6:
        extra = True
    elif last_pos_after < 6:
        if you_cpy[last_pos_after] == 1:
            opp_counter = new_opponent[5 - last_pos_after]
            if opp_counter > 0:
                y_store = y_copy[6]
                new_you[6] += opp_counter + 1
                new_opponent[last_pos_after] = 0
                new_opponent[5 - last_pos_after] = 0

    captured = capture

    return new_you, new_opponent, extra, captured
