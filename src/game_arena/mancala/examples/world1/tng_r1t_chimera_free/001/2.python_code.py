
def policy(you: list[int], opponent: list[int]) -> int:
    import copy
    
    def simulate_move(y, o, move):
        new_y = copy.copy(y)
        new_o = copy.copy(o)
        seeds = new_y[move]
        if seeds == 0:
            return new_y, new_o, False, 0
        new_y[move] = 0
        current_side = 'you'
        current_pos = move + 1
        last_side = None
        last_pos = None

        for _ in range(seeds):
            if current_side == 'you':
                if current_pos == 6:
                    new_y[6] += 1
                    last_side = 'you'
                    last_pos = 6
                    current_side = 'opponent'
                    current_pos = 0
                else:
                    new_y[current_pos] += 1
                    last_side = 'you'
                    last_pos = current_pos
                    current_pos += 1
                    if current_pos > 5:
                        current_side = 'opponent'
                        current_pos = 0
            else:
                if current_pos == 6:
                    current_side = 'you'
                    current_pos = 0
                    new_y[current_pos] += 1
                    last_side = 'you'
                    last_pos = current_pos
                    current_pos += 1
                    if current_pos > 5:
                        current_side = 'opponent'
                        current_pos = 0
                else:
                    new_o[current_pos] += 1
                    last_side = 'opponent'
                    last_pos = current_pos
                    current_pos += 1
                    if current_pos > 5:
                        current_side = 'you'
                        current_pos = 0

        extra_move = (last_side == 'you' and last_pos == 6)
        captures = 0
        if last_side == 'you' and 0 <= last_pos <= 5:
            if new_y[last_pos] == 1:  # was empty before
                opposite_pos = 5 - last_pos
                if new_o[opposite_pos] > 0:
                    captures = new_y[last_pos] + new_o[opposite_pos]
                    new_y[6] += captures
                    new_y[last_pos] = 0
                    new_o[opposite_pos] = 0

        return new_y, new_o, extra_move, captures

    legal_moves = [i for i in range(6) if you[i] > 0]
    best_score = -float('inf')
    best_move = legal_moves[0]

    for move in legal_moves:
        new_you, new_opponent, extra_move, captures = simulate_move(you, opponent, move)
        store_diff = new_you[6] - new_opponent[6]
        your_seeds = sum(new_you[:6])
        opp_seeds = sum(new_opponent[:6])
        score = store_diff * 100 + (1000 if extra_move else 0) + captures * 10 + your_seeds * 0.1 - opp_seeds * 0.1

        if score > best_score or (score == best_score and move < best_move):
            best_score = score
            best_move = move

    return best_move
