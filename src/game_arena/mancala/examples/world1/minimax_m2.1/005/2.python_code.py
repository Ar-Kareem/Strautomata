
def simulate_move(you: list[int], opponent: list[int], move: int) -> (list[int], list[int], bool):
    """
    Simulate a move for the current player.
    
    Args:
        you: Current player's state (7 elements: 6 houses + 1 store)
        opponent: Opponent's state (7 elements: 6 houses + 1 store)
        move: House index to move (0-5)
    
    Returns:
        new_you: Updated current player's state
        new_opp: Updated opponent's state
        extra_move: Whether the current player gets another move
    """
    you_new = you[:]
    opp_new = opponent[:]
    seeds = you_new[move]
    you_new[move] = 0
    
    # Total positions: 6 houses + 1 store for us, 6 houses for opponent = 13 positions
    total = 13
    current = move
    
    while seeds > 0:
        current = (current + 1) % total
        if current == 6:
            # Our store
            you_new[6] += 1
        elif current < 6:
            # Our houses
            you_new[current] += 1
        else:
            # Opponent's houses (positions 7-12)
            opp_new[current - 7] += 1
        seeds -= 1
    
    # Check for capture: last seed in our house, which was empty before drop, 
    # and opposite house has seeds
    if (current < 6 and you_new[current] == 1 and opp_new[5 - current] > 0):
        # Capture: take the seed and all opposite house seeds
        you_new[6] += 1  # The last seed
        you_new[6] += opp_new[5 - current]
        opp_new[5 - current] = 0
        you_new[current] = 0
    
    extra_move = (current == 6)
    return you_new, opp_new, extra_move

def policy(you: list[int], opponent: list[int]) -> int:
    """
    Determine the best move for the current player.
    
    Args:
        you: Current player's state (7 elements: 6 houses + 1 store)
        opponent: Opponent's state (7 elements: 6 houses + 1 store)
    
    Returns:
        int: House index to move (0-5)
    """
    best_move = -1
    best_score = -10**9
    
    for i in range(6):
        if you[i] == 0:
            continue  # Skip empty houses
            
        new_you, new_opp, extra_move = simulate_move(you, opponent, i)
        
        move_score = 0
        
        # Heavy bonus for extra moves (landing in store)
        if extra_move:
            move_score += 1000
        
        # Weight store seeds heavily
        gain = new_you[6] - you[6]
        move_score += gain * 10
        
        # Board control: minimize opponent's moves, maximize our moves
        move_score -= sum(new_opp[0:6])  # Penalty for opponent having many moves
        move_score += sum(new_you[0:6])  # Bonus for having many moves
        
        if move_score > best_score:
            best_score = move_score
            best_move = i
    
    return best_move
