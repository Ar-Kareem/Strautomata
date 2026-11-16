
import random

def simulate_move(you, opponent, i):
    new_you = you.copy()
    new_opponent = opponent.copy()
    seeds = new_you[i]
    new_you[i] = 0
    capture = False
    captured_seeds = 0
    extra_move = False
    # Distribute seeds
    for j in range(1, seeds + 1):
        next_pos = (i + j) % 12
        if next_pos < 6:
            new_you[next_pos] += 1
        elif next_pos == 6:
            new_you[6] += 1
        else:  # next_pos > 6 and <=11
            new_opponent[next_pos - 7] += 1
    # Check for capture
    last_pos = (i + seeds) % 12
    if last_pos < 6 and you[last_pos] == 0 and new_opponent[5 - last_pos] > 0:
        opposite_house = opponent[5 - last_pos]
        captured_seeds = new_you[last_pos] + opposite_house
        new_you[6] += captured_seeds
        new_you[last_pos] = 0
        new_opponent[5 - last_pos] = 0
        capture = True
    # Check for extra move
    if last_pos == 6:
        extra_move = True
    return new_you, new_opponent, capture, captured_seeds, extra_move

def policy(you, opponent) -> int:
    legal_moves = [i for i in range(6) if you[i] > 0]
    # First, check for moves that trigger a capture
    capture_moves = []
    for i in legal_moves:
        new_you, new_opponent, capture, captured_seeds, extra_move = simulate_move(you, opponent, i)
        if capture:
            capture_moves.append((i, captured_seeds))
    if capture_moves:
        # Choose the capture move that captures the most seeds
        max_captured = max(move[1] for move in capture_moves)
        best_capture_moves = [move[0] for move in capture_moves if move[1] == max_captured]
        return random.choice(best_capture_moves)
    # Next, check for moves that give an extra move
    extra_move_moves = []
    for i in legal_moves:
        new_you, new_opponent, capture, captured_seeds, extra_move = simulate_move(you, opponent, i)
        if extra_move:
            extra_move_moves.append(i)
    if extra_move_moves:
        # Choose a random extra move move
        return random.choice(extra_move_moves)
    # Otherwise, choose the move that maximizes the store difference
    best_move = None
    best_score = -float('inf')
    for i in legal_moves:
        new_you, new_opponent, capture, captured_seeds, extra_move = simulate_move(you, opponent, i)
        score = new_you[6] - opponent[6]  # store difference
        # Also consider the number of seeds in my houses vs opponent's
        my_seeds = sum(new_you[0:6])
        opponent_seeds = sum(new_opponent[0:6])
        score += my_seeds - opponent_seeds  # prefer more seeds on my side
        # Avoid moves that leave opponent with a house that has many seeds
        max_opponent_house = max(new_opponent[0:6])
        score -= max_opponent_house * 0.1  # small penalty for opponent's large houses
        if score > best_score:
            best_score = score
            best_move = i
    if best_move is not None:
        return best_move
    # If no clear choice, pick a random move
    return random.choice(legal_moves)
