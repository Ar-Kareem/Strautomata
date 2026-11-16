
import numpy as np

def policy(you: list[int], opponent: list[int]) -> int:
    best_move = -1
    best_score = -np.inf

    for i in range(6):
        if you[i] == 0:
            continue

        # Simulate the move
        temp_you = you.copy()
        temp_opponent = opponent.copy()
        seeds = temp_you[i]
        temp_you[i] = 0
        current_pos = i + 1
        last_pos = -1

        while seeds > 0:
            if current_pos < 6:  # Your houses
                temp_you[current_pos] += 1
                last_pos = current_pos
            elif current_pos == 6:  # Your store
                temp_you[current_pos] += 1
                last_pos = current_pos
            elif current_pos < 13:  # Opponent's houses
                temp_opponent[current_pos - 7] += 1
                last_pos = current_pos - 7
            else:  # Your houses again
                temp_you[current_pos - 13] += 1
                last_pos = current_pos - 13

            seeds -= 1
            current_pos += 1

        # Check for capture
        if last_pos != -1 and last_pos < 6 and temp_you[last_pos] == 1 and temp_opponent[5 - last_pos] > 0:
            temp_you[6] += temp_you[last_pos] + temp_opponent[5 - last_pos]
            temp_you[last_pos] = 0
            temp_opponent[5 - last_pos] = 0

        # Evaluate the move
        score = temp_you[6] - opponent[6]  # Immediate gain
        # Additional heuristic: prefer moves that lead to extra turns or captures
        if last_pos == 6:
            score += 10  # Extra move bonus
        if last_pos != -1 and last_pos < 6 and temp_you[last_pos] == 1 and temp_opponent[5 - last_pos] > 0:
            score += 5  # Capture bonus

        # Update best move
        if score > best_score:
            best_score = score
            best_move = i

    return best_move
