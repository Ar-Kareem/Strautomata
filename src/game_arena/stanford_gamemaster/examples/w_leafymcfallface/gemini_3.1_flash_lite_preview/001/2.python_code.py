
def policy(state: list[list[object]], role: str) -> str:
    # 1. Identify current player position and all leaf positions
    player_pos = None
    leaves = set()
    
    for prop in state:
        if prop[0] == "isplayer":
            if prop[3] == role:
                player_pos = (int(prop[1]), int(prop[2]))
        elif prop[0] == "leaf":
            leaves.add((int(prop[1]), int(prop[2])))
            
    if not player_pos:
        return ""

    r, c = player_pos
    potential_moves = []
    
    # 2. Check 4-connectivity (horizontal/vertical moves)
    candidates = [(r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)]
    
    for nr, nc in candidates:
        if (nr, nc) in leaves:
            # Calculate "mobility": how many valid moves we have from the new position
            mobility = 0
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                if (nr + dr, nc + dc) in leaves:
                    mobility += 1
            potential_moves.append(((nr, nc), mobility))
            
    # 3. Choose the move with the highest mobility (most surrounding leaves)
    if not potential_moves:
        # If no legal moves remain, the game will end
        return ""
        
    # Sort by mobility descending
    best_move = sorted(potential_moves, key=lambda x: x[1], reverse=True)[0][0]
    
    return f"move({best_move[0]},{best_move[1]})"
