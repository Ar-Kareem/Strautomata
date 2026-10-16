
import random

def policy(you, opponent):
    best_move = None
    best_score = -1
    capture_priority = 1000
    store_priority = 100
    extra_priority = 10

    for move in range(6):
        if you[move] == 0:
            continue

        captured, store_gain, ends_in_store = simulate_move_scores(you, opponent, move)
        score = captured * capture_priority + ends_in_store * extra_priority + store_gain
        if score > best_score:
            best_score = score
            best_move = move

    return best_move


def simulate_move_scores(you, opponent, move_i):
    new_you = list(you)
    new_opponent = list(opponent)
    seeds = new_you[move_i]
    new_you[move_i] = 0
    current_pos = move + 1
    steps_done = 0

    while steps_done < seeds:
        current_pos %= 13
        if current_pos < 7:
            new_you[current_pos] += 1
        else:
            opp_idx = current_pos - 7
            new_opponent[opp_idx] += 1

        steps_done += 1
        current_pos += 1

    last_pos = (current_pos - 1) % 13
    ends_in_store = (last_pos == 6)
    captured = 0

    if last_pos < 6:
        j = last_pos
        if j != move_i and you[j] == 0:
            opp_house = 5 - j
            captured = 1 + opponent[opp_house]

    store_gain = 1 if ends_in_store else 0
    return captured, store_gain, ends_in_store
