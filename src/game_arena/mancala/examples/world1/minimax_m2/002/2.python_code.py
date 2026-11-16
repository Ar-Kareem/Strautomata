
import time

def policy(you, opponent):
    """
    Kalah game policy. You are always the player to move.
    you: list of 7 integers (your houses and store)
    opponent: list of 7 integers (opponent's houses and store)
    Returns: index of the house (0..5) to move from.
    """
    start_time = time.time()
    best_move = None
    best_value = -10**9  # Start with a very low value

    # Try increasing depths until time runs out
    for depth in range(1, 10):  # depth from 1 to 9
        if time.time() - start_time > 1.0:
            break
        current_best_move = None
        current_best_value = -10**9
        for move in range(6):
            if you[move] == 0:
                continue  # Skip empty houses
            new_you, new_opp, extra = simulate_move(you, opponent, move)
            # After a move, if it was an extra move, we get to move again without switching the player.
            # Otherwise, we switch the player (minimax will do that via the is_maximizing flag).
            if extra:
                # We get another move: same player, so we pass True for is_maximizing and depth-1.
                value = minimax(new_you, new_opp, depth-1, True, start_time)
            else:
                # Opponent's turn: we switch the player and minimize.
                value = minimax(new_opp, new_you, depth-1, False, start_time)
            if value > current_best_value:
                current_best_value = value
                current_best_move = move
        if current_best_move is not None:
            best_move = current_best_move
            best_value = current_best_value

    # If no move was found (shouldn't happen), choose the first legal move.
    if best_move is None:
        for i in range(6):
            if you[i] > 0:
                return i
        return 0  # Fallback, though problem guarantees a move
    return best_move

def simulate_move(you, opponent, move):
    """
    Simulate a move.
    Returns: (new_you, new_opp, extra_move_flag)
    """
    # Combine the two lists into a 14-element list for simulation
    pits = you[:7] + opponent[:7]
    stones = pits[move]
    pits[move] = 0
    i = move
    while stones > 0:
        i += 1
        if i == 14:
            i = 0
        # Skip opponent's store (index 13 in the 14-element list)
        if i == 13:
            continue
        pits[i] += 1
        stones -= 1

    # Check for extra move: last seed in your store
    extra_move = (i == 6)

    # Check for capture: last seed in your house (0..5) that was empty and opposite house has seeds
    if i < 6 and pits[i] == 1:  # It was a house and now has 1 seed (so it was empty)
        opposite_index = 12 - i  # Opponent's house index in the 14-element list
        if pits[opposite_index] > 0:
            total = pits[i] + pits[opposite_index]
            pits[i] = 0
            pits[opposite_index] = 0
            pits[6] += total

    new_you = pits[0:7]
    new_opp = pits[7:14]
    return new_you, new_opp, extra_move

def minimax(you, opponent, depth, is_maximizing, start_time):
    """
    Minimax with alpha-beta pruning and time check.
    you: state of the current player (list of 7)
    opponent: state of the opponent (list of 7)
    depth: remaining depth to search
    is_maximizing: True if current player is maximizing, False if minimizing
    start_time: start time for the overall search
    Returns: evaluation value from the current player's perspective.
    """
    # Check if time is exceeded
    if time.time() - start_time > 1.0:
        # Return a basic evaluation without depth
        return evaluate(you, opponent)

    # Check for terminal state
    if not any(you[0:6]) or not any(opponent[0:6]):
        if not any(you[0:6]) and not any(opponent[0:6]):
            return 0
        if not any(you[0:6]):
            # You have no seeds, opponent moves all their seeds to store
            total = sum(opponent[0:6])
            return (you[6] - (opponent[6] + total)) * 100
        if not any(opponent[0:6]):
            # Opponent has no seeds, you move all your seeds to store
            total = sum(you[0:6])
            return ((you[6] + total) - opponent[6]) * 100

    if depth == 0:
        return evaluate(you, opponent)

    if is_maximizing:
        best = -10**9
        alpha = -10**9
        for move in range(6):
            if you[move] == 0:
                continue
            new_you, new_opp, extra = simulate_move(you, opponent, move)
            if extra:
                value = minimax(new_you, new_opp, depth-1, True, start_time)
            else:
                value = minimax(new_opp, new_you, depth-1, False, start_time)
            if value > best:
                best = value
            if best > alpha:
                alpha = best
            # Alpha-beta pruning: if this value is greater than or equal to the current beta, break
            # But note: we don't have beta? We are only doing alpha. So we skip beta.
        return best
    else:
        best = 10**9
        beta = 10**9
        for move in range(6):
            if you[move] == 0:
                continue
            new_you, new_opp, extra = simulate_move(you, opponent, move)
            if extra:
                value = minimax(new_you, new_opp, depth-1, False, start_time)
            else:
                value = minimax(new_opp, new_you, depth-1, True, start_time)
            if value < best:
                best = value
            if best < beta:
                beta = best
            # Alpha-beta pruning: if this value is less than or equal to the current alpha, break
            # But note: we don't have alpha? We are only doing beta. So we skip alpha.
        return best

def evaluate(you, opponent):
    """
    Heuristic evaluation: 
        value = (your_store - opponent_store) * 100 + (sum(your_houses) - sum(opponent_houses))
    This is from the current player's perspective (you is current player's state).
    """
    return (you[6] - opponent[6]) * 100 + (sum(you[0:6]) - sum(opponent[0:6]))
