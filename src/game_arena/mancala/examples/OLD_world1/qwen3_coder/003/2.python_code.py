
import copy

def policy(you: list[int], opponent: list[int]) -> int:
    # Try to implement a simple but effective strategy:
    # 1. If we can get an extra turn, do so
    # 2. If we can capture, do so
    # 3. Otherwise choose the best-looking move according to some heuristic

    # Look ahead one move
    best_move = 0
    for move in range(6):
        if you[move] > 0:
            best_move = move
            break

    # Evaluate each possible move
    best_score = float('-inf')
    for move in range(6):
        if you[move] <= 0:
            continue

        # Simulate the move
        new_you, new_opponent, extra_turn = simulate_move(you, opponent, move)

        # Heuristic evaluation: our store minus their store, plus some future-looking terms
        score = new_you[6] - new_opponent[6]

        # Add a bonus for seeds closer to our store for us
        for i in range(6):
            score += new_you[i] * (i + 1) * 0.1
            score -= new_opponent[i] * (6 - i) * 0.1

        # Big bonus for getting an extra turn
        if extra_turn:
            score += 2

        # Bonus for captures (approximate)
        # When we would land in an empty house of ours and the opposite has seeds
        # In actuality, we should re-simulate each move carefully for this
        # But for efficiency, just give some positional bonuses

        if score > best_score:
            best_score = score
            best_move = move

    # Now do a quick look for any immediate capture or extra turn that's forced
    capture_move = None
    extra_turn_move = None

    for move in range(6):
        if you[move] <= 0:
            continue

        _, _, extra_turn = simulate_move(you, opponent, move)
        would_capture = will_capture(you, opponent, move)
        
        if extra_turn:
            extra_turn_move = move
        if would_capture:
            capture_move = move

    # Prioritize extra turn, then capture, then heuristic
    if extra_turn_move is not None:
        return extra_turn_move
    if capture_move is not None:
        return capture_move

    return best_move

def will_capture(you, opponent, move):
    seeds = you[move]
    if seeds == 0:
        return False

    # Where will the last seed land?
    # 0-5: your houses
    # 6: your store
    # 7-12: opponent houses
    # 13-18: your houses again (but 13=0, 14=1, etc.)
    # And so on...

    end_pos = move + seeds
    if end_pos > 12:
        return False  # Simplification, just ignore multi-lap captures

    if end_pos < 6:  # Landed in your house
        landing_house = end_pos
        if you[landing_house] == 0:  # Was empty
            opposite_house = 5 - landing_house
            if opponent[opposite_house] > 0:
                return True
    return False

def simulate_move(you, opponent, move):
    # Returns new_you, new_opponent, extra_turn
    if you[move] == 0:
        return you, opponent, False

    # Make copies
    new_you = copy.deepcopy(you)
    new_opponent = copy.deepcopy(opponent)
    
    seeds = new_you[move]
    new_you[move] = 0

    # Distribute seeds
    current_pos = move + 1
    extra_turn = False

    for _ in range(seeds):
        if 0 <= current_pos <= 5:  # Our house
            new_you[current_pos] += 1
        elif current_pos == 6:  # Our store
            new_you[6] += 1
        elif 7 <= current_pos <= 12:  # Opponent house
            new_opponent[current_pos - 7] += 1
        elif 13 <= current_pos <= 18:  # Back to our house
            new_you[current_pos - 13] += 1
        # We never place in opponent's store, so skip it
        # But for simplicity, the pattern is:
        # you[0..5], you[6], opponent[0..5], you[0..5], ...
        # So every 13 steps, we cycle
        
        # Increment and handle wrap-around but skip opponent store
        current_pos += 1
        if current_pos == 13:  # After opponent's houses, go back to ours
            current_pos = 0
        elif current_pos == 6:  # Landing in our store
            if _ == seeds - 1:  # Last seed
                extra_turn = True

    # Check for capture (only if last seed lands in our empty house and there were seeds in opponent's opposite)
    last_pos = move + seeds
    # Normalize last_pos to the board
    # 0-5 = your houses, 6 = your store, 7-11 = opponent houses, 12 = you[0], etc.
    # To keep it simple, we only check for captures in the first cycle (0 to 12)
    
    normalized_last_pos = last_pos
    while normalized_last_pos > 12:
        normalized_last_pos -= 13
        if normalized_last_pos < 0:
            normalized_last_pos = 0
            
    if normalized_last_pos < 6 and normalized_last_pos >= 0:
        landing_house = normalized_last_pos
        if new_you[landing_house] == 1:  # It was 0 before and we added 1
            if last_pos <= 12:  # Simple case: didn't cycle
                opposite_house = 5 - landing_house
                if opponent[opposite_house] > 0:
                    # Capture
                    captured_seeds = 1 + opponent[opposite_house]
                    new_you[6] += captured_seeds
                    new_you[landing_house] -= 1
                    new_opponent[opposite_house] = 0

    return new_you, new_opponent, extra_turn
