
def policy(you, opponent):
    best_move = -1
    best_score = -float('inf')

    for i in range(6):
        if you[i] == 0:
            continue

        # Simulate the move
        new_you = you.copy()
        new_opponent = opponent.copy()
        seeds = new_you[i]
        new_you[i] = 0

        # Distribute seeds
        pos = i
        for seed in range(seeds):
            pos = (pos + 1) % 14
            if pos < 6:
                new_you[pos] += 1
            elif pos < 12:
                new_opponent[pos - 6] += 1

        # Check for capture or extra move
        last_pos = (i + seeds) % 14
        if last_pos < 6:
            if new_you[last_pos] == 1 and new_opponent[5 - last_pos] > 0:
                # Capture
                captured = new_opponent[5 - last_pos] + 1
                new_you[6] += captured
                new_you[last_pos] = 0
                new_opponent[5 - last_pos] = 0
                score = captured * 100
            else:
                score = 0
        elif last_pos == 6:
            # Extra move
            score = 10
        else:
            score = 0

        # Additional scoring: prefer moves that leave opponent with fewer seeds
        opponent_total = sum(new_opponent[:6])
        score += -opponent_total

        # Prefer moves that leave my houses more balanced
        you_sum = sum(new_you[:6])
        if you_sum > 0:
            avg = you_sum / 6
            variance = sum((x - avg) ** 2 for x in new_you[:6])
            score += -variance / 100  # Lower variance is better

        # Update best move
        if score > best_score:
            best_score = score
            best_move = i

    return best_move
