
def policy(you: list[int], opponent: list[int]) -> int:
    best_move = -1
    max_score = -1

    for i in range(6):
        if you[i] > 0:
            # Simulate the move
            new_you = you[:]
            new_opponent = opponent[:]
            seeds = new_you[i]
            new_you[i] = 0
            
            position = i
            while seeds > 0:
                position += 1
                if position == 6:  # After your last house, go to your store
                    new_you[6] += 1
                    seeds -= 1
                    if seeds == 0:  # Last seed in the store, get an extra turn
                        break
                elif position < 12:  # Go through opponent houses
                    if position < 6:
                        new_you[position] += 1
                    else:
                        new_opponent[position - 7] += 1
                else:
                    position = -1  # Wrap around to your first house (0)
                seeds -= 1

            # Check for captures
            if position >= 0 and position < 6 and new_you[position] == 1:
                opp_index = 5 - position
                if new_opponent[opp_index] > 0:
                    # Capture seeds
                    captured = new_opponent[opp_index] + 1  # +1 for the seed we just placed
                    new_you[6] += captured
                    new_opponent[opp_index] = 0
            
            # Score the move based on how many seeds would be in the store
            score = new_you[6] - sum(new_opponent)

            # Prefer this move if it has a higher score
            if score > max_score:
                max_score = score
                best_move = i

    return best_move
