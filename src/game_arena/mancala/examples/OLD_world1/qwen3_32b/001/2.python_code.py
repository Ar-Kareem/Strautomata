
from typing import List

def policy(you: List[int], opponent: List[int]) -> int:
    possible_moves = [i for i in range(6) if you[i] > 0]
    best_score = -float('inf')
    best_move = possible_moves[0]
    EXTRA_TURN_BONUS = 10  # Arbitrary value to prioritize extra turns

    for move in possible_moves:
        # Create copies to simulate the move
        you_copy = you[:]
        opponent_copy = opponent[:]
        seeds = you_copy[move]
        you_copy[move] = 0  # Sow the seeds from this house

        pos = move + 1  # Start distributing from the next position
        for _ in range(seeds):
            current_pos_13 = pos % 13
            if current_pos_13 == 6:
                you_copy[6] += 1  # Your store
            elif current_pos_13 <= 5:
                you_copy[current_pos_13] += 1  # Your houses
            else:
                opp_house_idx = current_pos_13 - 7
                opponent_copy[opp_house_idx] += 1  # Opponent's houses
            pos += 1

        # Determine last position and check for special effects
        last_pos_13 = (move + seeds) % 13
        extra_turn = False
        if last_pos_13 == 6:
            extra_turn = True
        elif last_pos_13 <= 5:
            y_idx = last_pos_13
            if (you_copy[y_idx] - 1) == 0:  # Check if the house was empty before the drop
                opp_idx = 5 - y_idx
                if opponent_copy[opp_idx] > 0:
                    you_copy[6] += you_copy[y_idx] + opponent_copy[opp_idx]
                    you_copy[y_idx] = 0
                    opponent_copy[opp_idx] = 0

        # Check if game ends after this move
        all_your_houses_empty = all(h == 0 for h in you_copy[:6])
        if all_your_houses_empty:
            opp_gain = sum(opponent_copy[:6])
            opponent_copy[6] += opp_gain
            for i in range(6):
                opponent_copy[i] = 0

        # Calculate score
        score = you_copy[6] - opponent_copy[6]
        if extra_turn:
            score += EXTRA_TURN_BONUS

        # Update best move
        if score > best_score or (score == best_score and move < best_move):
            best_score = score
            best_move = move

    return best_move
