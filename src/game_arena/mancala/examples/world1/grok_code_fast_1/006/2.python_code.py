
def simulate_move(you, opp, move):
    y = you.copy()
    o = opp.copy()
    s = y[move]
    y[move] = 0
    last_pos = 0
    last_side = 'none'
    if move == 5:
        if s >= 1:
            y[6] += 1
            s -= 1
            side = 'opp'
            current_pos = 0
    else:
        side = 'my'
        current_pos = move + 1
    for _ in range(s):
        last_pos = current_pos
        last_side = side
        if side == 'my':
            y[current_pos] += 1
            if current_pos < 5:
                current_pos += 1
            else:
                side = 'store'
                current_pos = 6
        elif side == 'store':
            y[6] += 1
            side = 'opp'
            current_pos = 0
        else:  # 'opp'
            o[current_pos] += 1
            if current_pos < 5:
                current_pos += 1
            else:
                side = 'my'
                current_pos = 0
    # Capture logic
    if last_side == 'my' and 0 <= last_pos <= 5 and y[last_pos] == 1 and o[5 - last_pos] > 0:
        captured = 1 + o[5 - last_pos]
        y[6] += captured
        y[last_pos] = 0
        o[5 - last_pos] = 0
    return y, o, last_side, last_pos

def policy(you: list[int], opponent: list[int]) -> int:
    best_move = -1
    best_score = -1
    for i in range(6):
        if you[i] == 0:
            continue
        new_y, new_o, last_side, last_pos = simulate_move(you, opponent, i)
        if new_y is None:
            continue
        capture = (last_side == 'my' and 0 <= last_pos <= 5 and new_y[last_pos] == 1 and new_o[5 - last_pos] > 0)
        score = 0
        if last_side == 'my' and last_pos == 6:
            score += 100
        if capture:
            score += 50
        if score > best_score or (score == best_score and (best_move == -1 or i < best_move)):
            best_score = score
            best_move = i
    if best_move == -1:
        # Fallback: pick the fist available
        for i in range(6):
            if you[i] > 0:
                return i
    return best_move
