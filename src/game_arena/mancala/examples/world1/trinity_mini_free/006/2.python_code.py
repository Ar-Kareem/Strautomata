
def policy(you, opponent):
    def simulate_move(you, opponent, i):
        new_you = list(you)
        new_opponent = list(opponent)
        seeds = new_you[i]
        new_you[i] = 0
        current = i + 1
        while seeds > 0:
            if current == 6:
                current = 0
                continue
            if current < 6:
                new_you[current] += 1
                seeds -= 1
                current += 1
            else:
                new_opponent[current - 6] += 1
                seeds -= 1
                current += 1
        original_you = list(you)
        original_opponent = list(opponent)
        last_house = current - 1
        if 0 <= last_house < 6 and original_you[last_house] == 0:
            opposite_house = 5 - last_house
            captured_seeds = original_opponent[opposite_house]
            new_you[6] += captured_seeds
            new_opponent[opposite_house] = 0
        return new_you, new_opponent

    def evaluate(new_you, new_opponent):
        diff = new_you[6] - new_opponent[6]
        your_moves = sum(new_you[0:6])
        opponent_moves = sum(new_opponent[0:6])
        return diff + (your_moves - opponent_moves)

    best_move = None
    best_score = -10**9
    for i in range(6):
        if you[i] == 0:
            continue
        new_you, new_opponent = simulate_move(you, opponent, i)
        score = evaluate(new_you, new_opponent)
        if score > best_score:
            best_score = score
            best_move = i
    return best_move
