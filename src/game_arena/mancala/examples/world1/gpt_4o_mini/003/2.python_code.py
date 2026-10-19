
def policy(you: list[int], opponent: list[int]) -> int:
    def calculate_move_result(start_index: int):
        seeds = you[start_index]
        you[start_index] = 0  # Simulate taking seeds from the house
        total_seeds = seeds
        position = start_index

        # Distribute seeds
        while total_seeds > 0:
            position += 1
            if position == 6:  # Drop into store
                if position < 7:  # Our store
                    you[6] += 1  # One seed into our store
                else:  # Opponent's store, skip it
                    position = 0
                total_seeds -= 1
                continue
            
            if position < 7:  # our houses
                you[position] += 1
            else:  # opponent's houses
                if position < 13:  # Opponent's houses (skip opponent store)
                    opponent[position - 7] += 1
            total_seeds -= 1

        last_position = position % 14  # Find where the last seed landed
        capture_possible = last_position < 6 and you[last_position] == 1 and opponent[5 - last_position] > 0
        extra_move = last_position == 6

        you[start_index] = seeds  # Restore the state
        return extra_move, capture_possible

    best_move = -1
    for i in range(6):
        if you[i] > 0:  # If this house has seeds
            extra, capture = calculate_move_result(i)
            if capture:
                return i  # Capture is priority
            if extra and best_move == -1:
                best_move = i  # Store move if it gives extra turn

    # If no captures or extra moves available, just return the first valid move
    for i in range(6):
        if you[i] > 0:
            return i

    return best_move  # This line should be unreachable given the constraints
