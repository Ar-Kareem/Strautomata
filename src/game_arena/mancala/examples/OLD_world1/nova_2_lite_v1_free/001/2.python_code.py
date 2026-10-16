
def policy(you: list[int], opponent: list[int]) -> int:
    import copy

    def simulate_move(you, opponent, i):
        new_you = copy.copy(you)
        new_opponent = copy.copy(opponent)
        seeds = new_you[i]
        new_you[i] = 0
        current = seeds
        order = []
        for j in range(i + 1, 6):
            order.append((0, j))
        order.append((0, 6))
        for j in range(6):
            order.append((1, j))
        for j in range(0, i):
            order.append((0, j))
        idx = 0
        while current > 0:
            type_, pos = order[idx % len(order)]
            if type_ == 0:
                if pos == 6:
                    new_you[6] += 1
                else:
                    new_you[pos] += 1
            else:
                new_opponent[pos] += 1
            current -= 1
            idx += 1
        last_type, last_pos = order[(idx - 1) % len(order)]
        extra_move = last_type == 0 and last_pos == 6
        capture = False
        captured = 0
        if last_type == 0 and last_pos < 6 and new_you[last_pos] == 1:
            opposite = 5 - last_pos
            if new_opponent[opposite] > 0:
                capture = True
                captured = new_you[last_pos] + new_opponent[opposite]
                new_you[6] += captured
                new_you[last_pos] = 0
                new_opponent[opposite] = 0
        return new_you, new_opponent, extra_move, capture, captured

    best_score = -float('inf')
    best_move = None
    for i in range(6):
        if you[i] == 0:
            continue
        new_you, new_opponent, extra, cap, cap_seeds = simulate_move(you, opponent, i)
        score = (new_you[6] - new_opponent[6])
        if cap:
            score += 10000 + cap_seeds
        if extra:
            score += 5000
        score += sum(new_you[:6]) - sum(new_opponent[:6])
        if score > best_score:
            best_score = score
            best_move = i
    return best_move
