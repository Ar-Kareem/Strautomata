
def policy(pieces: dict[str, str], to_play: str) -> str:
    # Assume legal_moves is available as a global list of strings (injected by the arena framework)
    global legal_moves
    if not legal_moves:
        raise ValueError("No legal moves available")
    
    color = 'w' if to_play == 'white' else 'b'
    value = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
    best_move = None
    best_gain = -float('inf')
    
    for move in legal_moves:
        from_sq = move[:2]
        to_sq = move[2:4]
        gain = 0
        
        # Check for capture
        if to_sq in pieces and not pieces[to_sq].startswith(color):
            gain = value[pieces[to_sq][1]]
        
        # Check for promotion (add promoted piece value as gain)
        if len(move) == 5:
            promo = move[4].upper()
            gain += value.get(promo, 0)
        
        # Update best if better gain
        if gain > best_gain:
            best_gain = gain
            best_move = move
    
    return best_move
