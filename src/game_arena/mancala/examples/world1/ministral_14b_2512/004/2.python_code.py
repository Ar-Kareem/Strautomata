
def policy(you, opponent):
    legal_moves = [i for i in range(6) if you[i] > 0]
    best_score = -float('inf')
    best_move = legal_moves[0]

    for i in legal_moves:
        # Simulate the move
        new_you = you.copy()
        new_opponent = opponent.copy()
        seeds = new_you[i]
        new_you[i] = 0
        index = i
        last_seed_pos = None
        # Distribute seeds
        while seeds > 0:
            if index == 6:  # your store
                index = 0
            elif index == 7:  # opponent's store (skip)
                index = 0
            else:
                if index < 6:
                    new_you[index] += 1
                else:  # opponent's houses
                    new_opponent[index - 7] += 1
                seeds -= 1
                if seeds == 0:
                    last_seed_pos = index
                index += 1
                if index > 7:  # wrap around
                    index = 0
        # Check for capture
        capture = False
        if last_seed_pos != 6 and last_seed_pos != 7 and new_you[last_seed_pos] == 1:
            opposite_pos = 5 - last_seed_pos
            if new_opponent[opposite_pos] > 0:
                new_you[6] += new_you[last_seed_pos] + new_opponent[opposite_pos]
                new_you[last_seed_pos] = 0
                new_opponent[opposite_pos] = 0
                capture = True
        # Calculate score
        score = 0
        if capture:
            score += 100
        if last_seed_pos == 6:
            score += 50
        # Prefer moves that leave opponent with fewer seeds
        opponent_seed_count = sum(new_opponent[:6])
        score -= opponent_seed_count
        # Prefer moves that leave you with more seeds
        your_seed_count = sum(new_you[:6])
        score += your_seed_count
        # Prefer moves that increase your store
        score += new_you[6] - you[6]

        if score > best_score:
            best_score = score
            best_move = i

    return best_move
