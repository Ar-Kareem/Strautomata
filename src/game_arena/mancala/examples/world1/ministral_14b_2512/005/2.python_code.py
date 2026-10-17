
import random

def policy(you: list[int], opponent: list[int]) -> int:
    # List of available moves (houses with seeds)
    available_moves = [i for i in range(6) if you[i] > 0]

    # Check for capturing moves (highest priority)
    capturing_moves = []
    for i in available_moves:
        seeds = you[i]
        # Simulate sowing from house i
        temp_you = you.copy()
        temp_opponent = opponent.copy()
        temp_you[i] = 0
        pos = i
        while seeds > 0:
            pos += 1
            if pos > 5:  # Move to store
                temp_you[6] += 1
            elif pos == 6:  # Skip opponent's store
                pos += 1
            elif pos > 6:  # Move to opponent's houses
                temp_opponent[pos - 7] += 1
            else:  # Move to your houses
                temp_you[pos] += 1
            seeds -= 1
        # Check if last seed landed in your empty house and opponent's opposite has seeds
        last_pos = (i + you[i] - 1) % 13  # Simplified: 6 houses + 1 store + 6 opponent houses
        if last_pos <= 5 and temp_you[last_pos] == 1 and temp_opponent[5 - last_pos] > 0:
            capturing_moves.append(last_pos)

    if capturing_moves:
        # Choose the best capturing move (e.g., highest opponent seeds to capture)
        return max(capturing_moves, key=lambda x: opponent[5 - x])

    # Avoid giving opponent an extra move (if they have a house with 1 seed)
    opponent_single_seed = [i for i in range(6) if opponent[i] == 1]
    if opponent_single_seed:
        # Filter moves that would not land in opponent's store (to avoid extra move)
        safe_moves = []
        for i in available_moves:
            seeds = you[i]
            last_pos = (i + seeds - 1) % 13
            if last_pos != 6:  # Would not land in opponent's store
                safe_moves.append(i)
        if safe_moves:
            available_moves = safe_moves

    # Bias toward disrupting opponent's strong houses (e.g., take a house if opponent has many seeds nearby)
    opponent_strong_positions = []
    for i in range(6):
        if opponent[i] >= 3:  # Opponent has a strong position
            opposite_house = 5 - i
            if you[opposite_house] > 0:
                opponent_strong_positions.append(opposite_house)

    if opponent_strong_positions:
        # Prefer moves that can disrupt opponent's strong positions
        return random.choice(opponent_strong_positions)

    # Randomized move with bias toward:
    # 1. Houses with fewer seeds (to avoid predictability)
    # 2. Houses that do not allow opponent to capture immediately (if they have a strong position)
    weights = []
    for i in available_moves:
        seeds = you[i]
        # Lower weight for houses with many seeds (avoid greedy)
        weight = 1.0 / (seeds + 1)
        # Additional penalty if opponent can capture immediately after your move
        last_pos = (i + seeds - 1) % 13
        if last_pos <= 5 and you[last_pos] == 1 and opponent[5 - last_pos] > 0:
            weight *= 0.5  # Less likely to choose this move
        weights.append(weight)

    # Choose move with weighted randomness
    return random.choices(available_moves, weights=weights, k=1)[0]
