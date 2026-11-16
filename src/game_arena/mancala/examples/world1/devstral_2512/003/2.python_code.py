
import numpy as np

def policy(you: list[int], opponent: list[int]) -> int:
    best_move = -1
    best_score = -np.inf

    for i in range(6):
        if you[i] == 0:
            continue

        # Simulate the move
        seeds = you[i]
        you_copy = you.copy()
        opponent_copy = opponent.copy()
        you_copy[i] = 0

        current_pos = i + 1
        while seeds > 0:
            # Distribute to your houses
            while seeds > 0 and current_pos < 6:
                you_copy[current_pos] += 1
                seeds -= 1
                current_pos += 1

            # If no seeds left, break
            if seeds == 0:
                break

            # Distribute to your store
            if seeds > 0:
                you_copy[6] += 1
                seeds -= 1
                if seeds == 0:
                    # Extra move condition
                    break

            # Distribute to opponent's houses
            while seeds > 0 and current_pos < 6:
                opponent_copy[current_pos] += 1
                seeds -= 1
                current_pos += 1

            # Reset current_pos to start of your houses
            current_pos = 0

        # Check for capture
        if seeds == 0 and current_pos < 6 and you_copy[current_pos] == 1:
            opposite_pos = 5 - current_pos
            if opponent_copy[opposite_pos] > 0:
                # Capture seeds
                you_copy[6] += you_copy[current_pos] + opponent_copy[opposite_pos]
                you_copy[current_pos] = 0
                opponent_copy[opposite_pos] = 0

        # Evaluate the move
        score = you_copy[6] - you[6]  # Immediate gain

        # Prioritize captures and extra moves
        if seeds == 0 and current_pos == 6:
            score += 10  # Extra move bonus
        elif seeds == 0 and current_pos < 6 and you_copy[current_pos] == 1 and opponent_copy[5 - current_pos] > 0:
            score += 5  # Capture bonus

        # Update best move
        if score > best_score:
            best_score = score
            best_move = i

    return best_move
