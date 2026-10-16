
def policy(you: list[int], opponent: list[int]) -> int:
    for i in range(6):  # Check each house from 0 to 5
        if you[i] > 0:  # We can only select non-empty houses
            # Calculate the last seed position after the move
            last_seed_position = (i + you[i]) % 14
            
            # Check if we can capture seeds
            if last_seed_position < 6 and you[last_seed_position] == 0:  # Last seed lands in our empty house
                opposite_house_index = 5 - last_seed_position
                if opponent[opposite_house_index] > 0:  # There are seeds to capture
                    return i
            
            # Check for an extra move (last seed lands in our store)
            if last_seed_position == 6:
                return i
            
    # If no capturing or extra moves, return the first valid move
    for i in range(6):
        if you[i] > 0:
            return i

    # This case should never occur in a well-defined game, as we assume there's always a move.
    raise Exception("Unexpected state: No legal moves available")  # Fallback
