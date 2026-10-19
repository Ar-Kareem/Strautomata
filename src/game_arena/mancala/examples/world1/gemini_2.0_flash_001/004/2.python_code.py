
def policy(you: list[int], opponent: list[int]) -> int:
    """
    Selects a move in the Kalah game.

    Args:
        you: A list representing your side of the board (houses 0-5, store 6).
        opponent: A list representing the opponent's side of the board (houses 0-5, store 6).

    Returns:
        An integer representing the index of the house to move (0-5).
    """

    def simulate_move(move: int, you: list[int], opponent: list[int]) -> tuple[int, list[int], list[int]]:
        """Simulates a move and returns the landing position of the last seed."""
        seeds = you[move]
        you = you[:]
        opponent = opponent[:]
        you[move] = 0
        current_index = move + 1
        current_player = 'you'

        while seeds > 0:
            if current_player == 'you':
                if current_index == 6:
                    you[6] += 1
                    seeds -= 1
                else:
                    you[current_index] += 1
                    seeds -= 1
            else:
                if current_index == 6:
                    current_index = 0
                    current_player = 'you'
                    continue
                opponent[current_index] += 1
                seeds -= 1

            current_index += 1
            if current_player == 'you' and current_index > 6:
                current_index = 0
                current_player = 'opponent'
            elif current_player == 'opponent' and current_index > 6:
                current_index = 0
                current_player = 'you'

        if current_player == 'you':
            landing_index = current_index - 1 if current_index > 0 else 6  # landing in store
        else:
            landing_index = current_index - 1
            
        return landing_index, you, opponent

    def check_capture(landing_index: int, you: list[int], opponent: list[int]) -> bool:
        """Checks if a capture is possible."""
        if landing_index >= 0 and landing_index <= 5:
            if you[landing_index] == 1 and opponent[5 - landing_index] > 0: # was empty == 1 because the seeds landed there.
                return True
        return False
    
    # Iterate through possible moves
    for move in range(6):
        if you[move] > 0:
            # Simulate the move
            landing_index, new_you, new_opponent = simulate_move(move, you[:], opponent[:])

            # Check for extra move (landing in store)
            if landing_index == 6 and simulate_move(move, you[:], opponent[:])[0] == 6:
                return move

            # Check for capture
            if landing_index >=0 and landing_index <= 5:
                temp_you = you[:]
                landing_index_sim, new_temp_you, new_opponent = simulate_move(move, temp_you, opponent[:]) # new board before update, to check the landing position of empty house.
                if temp_you[landing_index_sim] - you[move] == 0:  ## Checking empty slot
                    if check_capture(landing_index_sim, new_temp_you, new_opponent):
                        storeIndex, new_temp_you, new_opponent = simulate_move(move, you[:], opponent[:])
                        return move

    # If no special move found, return the first valid move
    for move in range(6):
        if you[move] > 0:
            return move

    return -1 # Should never happen because policy not called when all empty.
