
def policy(you: list[int], opponent: list[int]) -> int:
    """
    Select a move for Kalah based on strategic evaluation.
    
    Args:
        you: List of 7 integers [h0,h1,h2,h3,h4,h5,store] for your side
        opponent: List of 7 integers [h0,h1,h2,h3,h4,h5,store] for opponent's side
    
    Returns:
        int: Index (0-5) of the house to play
    """
    
    # Find all legal moves
    legal_moves = [i for i in range(6) if you[i] > 0]
    
    if not legal_moves:
        raise ValueError("No legal moves available")
    
    best_move = legal_moves[0]
    best_score = -float('inf')
    
    # Evaluate each legal move
    for move in legal_moves:
        score = evaluate_move(move, you, opponent)
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move


def evaluate_move(move: int, you: list[int], opponent: list[int]) -> float:
    """
    Evaluate a move and return a score based on strategic value.
    """
    seeds = you[move]
    if seeds == 0:
        return -float('inf')
    
    # Calculate where the last seed will land
    # Positions are: you[0]..you[5], you[6](store), opponent[0]..opponent[5]
    # So positions 0-12 represent one full cycle (13 positions)
    start_pos = move + 1  # Where first seed goes
    end_pos = start_pos + seeds - 1  # Where last seed goes
    
    # Normalize to cycle of 13 positions (0-12)
    last_pos = end_pos % 13
    
    score = 0
    
    # Extra turn bonus (landing exactly in your store)
    if last_pos == 6:
        score += 100
    
    # Capture opportunity
    elif 0 <= last_pos <= 5:  # Landing in your house
        landing_house = last_pos
        # Check if this house was empty before sowing
        if you[landing_house] == 0:
            opposite_house = 5 - landing_house
            if opponent[opposite_house] > 0:
                # This is a capture!
                capture_value = 1 + opponent[opposite_house]  # captured seeds + the seed that landed
                score += capture_value * 10
    
    # Sowing more seeds generally gives more flexibility
    score += seeds * 0.1
    
    # Avoid moves that send seeds directly to opponent's houses without strategy
    # Unless it's setting up a capture or extra move in future
    
    return score
