
import copy

def policy(you: list[int], opponent: list[int]) -> int:
    best_score = -float('inf')
    best_move = 0

    for move_i in range(6):
        if you[move_i] == 0:
            continue

        # Simulate the move
        you_copy = list(you)
        opponent_copy = list(opponent)
        seeds = you_copy[move_i]
        you_copy[move_i] = 0

        current_side = 'you'
        current_index = move_i

        for _ in range(seeds):
            if current_side == 'you':
                if current_index < 5:
                    next_side = 'you'
                    next_index = current_index + 1
                elif current_index == 5:
                    next_side = 'you'
                    next_index = 6
                else:  # current_side is 'you' and current_index == 6 (your store)
                    next_side = 'opponent'
                    next_index = 0
            else:  # current_side is 'opponent'
                if current_index < 5:
                    next_side = 'opponent'
                    next_index = current_index + 1
                else:  # current_index == 5 (opponent's last house)
                    next_side = 'you'
                    next_index = 0

            # Place the seed
            if next_side == 'you':
                you_copy[next_index] += 1
            else:
                opponent_copy[next_index] += 1

            current_side, current_index = next_side, next_index

        # Check for extra move or capture
        extra_move = False
        captured_seeds = 0
        if current_side == 'you' and current_index == 6:
            extra_move = True
        elif current_side == 'you' and current_index <= 5:
            if you_copy[current_index] - 1 == 0:
                opposite = 5 - current_index
                if opponent_copy[opposite] > 0:
                    captured_seeds = 1 + opponent_copy[opposite]
                    you_copy[6] += captured_seeds
                    you_copy[current_index] = 0
                    opponent_copy[opposite] = 0

        # Check for game end and handle accordingly
        you_zero = all(x == 0 for x in you_copy[:6])
        opponent_zero = all(x == 0 for x in opponent_copy[:6])

        if you_zero and not opponent_zero:
            opponent_houses_sum = sum(opponent_copy[:6])
            opponent_copy[6] += opponent_houses_sum
            for i in range(6):
                opponent_copy[i] = 0
        elif opponent_zero and not you_zero:
            you_houses_sum = sum(you_copy[:6])
            you_copy[6] += you_houses_sum
            for i in range(6):
                you_copy[i] = 0

        # Calculate score
        original_store = you[6]
        new_store = you_copy[6]
        delta_store = new_store - original_store
        extra_move_bonus = 100 if extra_move else 0
        score = delta_store + extra_move_bonus

        # Update best move
        if score > best_score or (score == best_score and move_i < best_move):
            best_score = score
            best_move = move_i

    return best_move
