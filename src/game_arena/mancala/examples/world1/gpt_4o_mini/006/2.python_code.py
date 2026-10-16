
def policy(you: list[int], opponent: list[int]) -> int:
    # Returns the index of the move that maximizes my advantage
    best_move = -1
    best_eval = -1
    
    # Evaluate all possible moves (0 to 5)
    for move in range(6):
        if you[move] > 0:  # Only consider legal moves
            # Create a copy of the current state to simulate the move
            temp_you = you[:]
            temp_opponent = opponent[:]

            # Perform the sowing logic starting from selected move
            seeds = temp_you[move]
            temp_you[move] = 0

            position = move
            while seeds > 0:
                position = (position + 1) % 14  # Move counter-clockwise around the board
                # Skip opponent's store
                if position == 13:
                    continue
                if position < 7:
                    temp_you[position] += 1
                else:
                    temp_opponent[position - 7] += 1
                seeds -= 1
            
            # Check for capture
            if position < 6 and temp_you[position] == 1:  # Last seed lands in my house and it was empty
                # Capture the seeds from the opponent's corresponding house
                temp_you[6] += 1 + temp_opponent[5 - position]  # My seeded + Opponent seeds
                temp_opponent[5 - position] = 0
            
            # Evaluate the result for this move based on my store size
            store_value = temp_you[6]
            if store_value > best_eval:
                best_eval = store_value
                best_move = move
    
    return best_move
