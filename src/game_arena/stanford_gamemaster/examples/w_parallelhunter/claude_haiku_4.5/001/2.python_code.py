
def policy(state: list[list[object]], role: str) -> str:
    # Check if we need to tick
    for fact in state:
        if fact[0] == "played" and fact[1] == role:
            return "tick"
    
    # Find our knight position
    knight_pos = None
    for fact in state:
        if fact[0] == "cell" and fact[1] == role and fact[4] == "knight":
            knight_pos = (int(fact[2]), int(fact[3]))
            break
    
    if knight_pos is None:
        return "tick"
    
    # Build set of opponent pawns
    opponent = "right" if role == "left" else "left"
    opponent_pawns = set()
    for fact in state:
        if fact[0] == "cell" and fact[1] == opponent and fact[4] == "pawn":
            opponent_pawns.add((int(fact[2]), int(fact[3])))
    
    # Generate all possible knight moves (L-shaped)
    x, y = knight_pos
    knight_moves = [
        (x+2, y+1), (x+2, y-1), (x-2, y+1), (x-2, y-1),
        (x+1, y+2), (x+1, y-2), (x-1, y+2), (x-1, y-2)
    ]
    
    # Filter valid moves (within board bounds)
    legal_moves = []
    for nx, ny in knight_moves:
        if 1 <= nx <= 5 and 1 <= ny <= 3:
            legal_moves.append((nx, ny))
    
    if not legal_moves:
        return "tick"
    
    # Rank moves: captures first, then closest to opponent pawns
    best_move = None
    best_score = (-1, float('inf'))  # (has_capture, distance_to_nearest_pawn)
    
    for nx, ny in legal_moves:
        has_capture = 1 if (nx, ny) in opponent_pawns else 0
        
        # Distance to nearest opponent pawn
        if opponent_pawns:
            min_dist = min(abs(nx - px) + abs(ny - py) for px, py in opponent_pawns)
        else:
            min_dist = 0
        
        score = (-has_capture, min_dist)  # Negative for capture so higher captures rank first
        
        if score > best_score:
            best_score = score
            best_move = (nx, ny)
    
    if best_move is None:
        best_move = legal_moves[0]
    
    return f"move({role},{x},{y},{best_move[0]},{best_move[1]})"
