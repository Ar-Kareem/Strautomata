
def generate_order(i):
    order = []
    # Add your houses from i+1 to 5
    start = i + 1
    if start <= 5:
        order.extend(range(start, 6))
    # Add your store
    order.append(6)
    # Add opponent's houses 0-5
    order.extend(range(6))
    # Add your houses 0-5
    order.extend(range(6))
    return order

def simulate_move(original_you, original_opponent, move_i):
    new_you = list(original_you)
    new_opponent = list(original_opponent)
    count = new_you[move_i]
    if count == 0:
        return (new_you, new_opponent, False)
    
    # Empty the chosen house
    new_you[move_i] = 0
    
    # Generate the distribution order and get its length
    order = generate_order(move_i)
    len_order = len(order)
    if len_order == 0:
        return (new_you, new_opponent, False)
    
    q, rem = divmod(count, len_order)
    
    # Distribute q full rounds
    for idx, house in enumerate(order):
        if house == 6:
            new_you[6] += q
        elif house < 6:
            new_you[house] += q
        else:
            opp_house = house - 6
            new_opponent[opp_house] += q
    
    # Distribute the remaining seeds
    for idx in range(rem):
        house = order[idx]
        if house == 6:
            new_you[6] += 1
        elif house < 6:
            new_you[house] += 1
        else:
            opp_house = house - 6
            new_opponent[opp_house] += 1
    
    # Determine the last position where a seed was placed
    last_step = count - 1
    last_house = order[last_step % len_order]
    
    # Check for capture
    captured = False
    if last_house < 6:
        j = last_house
        if new_you[j] > 0 and original_you[j] == 0:
            opp_idx = 5 - j
            if new_opponent[opp_idx] > 0:
                captured_seeds = new_you[j] + new_opponent[opp_idx]
                new_you[6] += captured_seeds
                new_you[j] = 0
                new_opponent[opp_idx] = 0
                captured = True
    
    # Determine if extra move is allowed
    if last_house == 6:
        extra_move = True
    else:
        extra_move = False
    
    return (new_you, new_opponent, extra_move)

def policy(you, opponent):
    best_move = -1
    best_score = float('-inf')
    for i in range(6):
        if you[i] == 0:
            continue
        
        new_you, new_opponent, extra_move = simulate_move(you, opponent, i)
        score = new_you[6] - new_opponent[6]
        if last_seeded_in_store and extra_move:
            score += 1000  # Prioritize moves that allow extra turns
        
        if score > best_score or (score == best_score and i < best_move):
            best_score = score
            best_move = i
    
    return best_move
