
def policy(you: list[int], opponent: list[int]) -> int:
    """
    Choose a move for Kalah game.
    
    Args:
        you: [h0,h1,h2,h3,h4,h5,store] - your houses and store
        opponent: [h0,h1,h2,h3,h4,h5,store] - opponent's houses and store
        
    Returns:
        int: index (0-5) of the house to play
    """
    
    # Try to find moves that give extra turn (land in your store)
    extra_turn_moves = []
    capture_moves = []
    
    for i in range(6):
        if you[i] == 0:
            continue
            
        # Calculate where the last seed would land
        # Total positions = 13 (your 6 houses + your store + opponent 6 houses)
        # Position 6 is your store
        # Starting position for first seed is (i+1), so last seed lands at (i + you[i]) % 13
        final_pos = (i + you[i]) % 13
        
        if final_pos == 6:
            # Extra turn!
            extra_turn_moves.append(i)
        elif 0 <= final_pos <= 5:
            # Final position is in your house
            # Check if it was empty before the move and opponent has seeds opposite
            if you[final_pos] == 0 and opponent[5 - final_pos] > 0:
                # We can capture
                capture_moves.append((i, opponent[5 - final_pos]))  # prefer captures with more seeds
    
    # If we have extra turn moves, pick the best one
    if extra_turn_moves:
        # You might prefer the one that moves more seeds or creates better future positions
        return extra_turn_moves[0]
    
    # If we have capture moves, pick the one with most captured seeds
    if capture_moves:
        capture_moves.sort(key=lambda x: x[1], reverse=True)
        return capture_moves[0][0]
    
    # Heuristic: avoid moves that leave single seeds capturable
    safe_moves = []
    for i in range(6):
        if you[i] > 0:
            safe_moves.append(i)
            
    # Find moves that don't put seeds in vulnerable positions
    good_moves = []
    for i in safe_moves:
        seeds = you[i]
        # See where this move puts seeds
        positions_affected = []
        for seed in range(seeds):
            pos = (i + 1 + seed) % 13
            if pos < 6:  # Your house
                positions_affected.append(pos)
        
        # Avoid moves that leave opponent with easy captures
        seems_safe = True
        if positions_affected and positions_affected[-1] <= 5:
            final_house = positions_affected[-1]
            if you[final_house] == 0 and opponent[5 - final_house] > 0:
                # Could allow capture next turn
                seems_safe = False
                
        if seems_safe:
            good_moves.append(i)
    
    if good_moves:
        return good_moves[0]
    
    # Otherwise, just return first valid move
    for i in range(6):
        if you[i] > 0:
            return i
            
    # Shouldn't happen due to problem constraints
    return 0
