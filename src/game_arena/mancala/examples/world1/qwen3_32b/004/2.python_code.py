
def policy(you: list[int], opponent: list[int]) -> int:
    legal_moves = [i for i in range(6) if you[i] > 0]
    best_move = legal_moves[0]
    best_score = -float('inf')
    BONUS_EXTRA_TURN = 10  # Heuristic bonus for moves that allow an extra turn

    for move in legal_moves:
        you_copy = you.copy()
        opp_copy = opponent.copy()
        seeds = you_copy[move]
        you_copy[move] = 0
        current_side = 'you'
        current_house = move + 1
        last_pos_side = None
        last_pos_house = None
        last_old_val = 0

        for s in range(seeds):
            is_last = (s == seeds - 1)
            if current_side == 'you':
                if current_house == 6:
                    you_copy[6] += 1
                    current_side = 'opponent'
                    current_house = 0
                    if is_last:
                        last_pos_side = 'you'
                        last_pos_house = 6
                else:
                    old_val = you_copy[current_house]
                    if is_last:
                        last_old_val = old_val
                    you_copy[current_house] += 1
                    current_house += 1
                    if current_house > 5:
                        current_house = 6
            else:  # opponent's side
                if current_house <= 5:
                    old_val = opp_copy[current_house]
                    if is_last:
                        last_old_val = old_val
                    opp_copy[current_house] += 1
                    current_house += 1
                    if current_house > 5:
                        current_side = 'you'
                        current_house = 0
            if is_last:
                if current_side == 'you':
                    if current_house == 6:
                        last_pos_side = 'you'
                        last_pos_house = 6
                    else:
                        last_pos_side = 'you'
                        last_pos_house = current_house
                else:
                    last_pos_side = 'opponent'
                    last_pos_house = current_house

        # Check for capture and extra turn
        extra_turn = False
        captured_seeds = 0

        if last_pos_side == 'you' and last_pos_house == 6:
            extra_turn = True

        if last_pos_side == 'you' and last_pos_house != 6:
            if last_old_val == 0:
                opp_house_idx = 5 - last_pos_house
                if opp_copy[opp_house_idx] > 0:
                    captured_seeds = you_copy[last_pos_house] + opp_copy[opp_house_idx]
                    you_copy[6] += captured_seeds
                    you_copy[last_pos_house] = 0
                    opp_copy[opp_house_idx] = 0

        # Check if game has ended
        you_houses_empty = all(x == 0 for x in you_copy[:6])
        opp_houses_empty = all(x == 0 for x in opp_copy[:6])
        if you_houses_empty or opp_houses_empty:
            if you_houses_empty:
                for i in range(6):
                    opp_copy[6] += opp_copy[i]
                    opp_copy[i] = 0
            if opp_houses_empty:
                for i in range(6):
                    you_copy[6] += you_copy[i]
                    you_copy[i] = 0

        # Calculate score
        score = you_copy[6] - opp_copy[6] + (BONUS_EXTRA_TURN if extra_turn else 0)
        if score > best_score:
            best_score = score
            best_move = move

    return best_move
