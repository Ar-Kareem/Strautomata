
def policy(state: list[list[object]], role: str) -> str:
    # Parse piece locations from state
    locations = {}
    for prop in state:
        if prop[0] == "location":
            x, y, color = int(prop[1]), int(prop[2]), prop[3]
            locations[(x, y)] = color
    
    opponent = "red" if role == "black" else "black"
    my_pieces = [(x, y) for (x, y), color in locations.items() if color == role]
    opp_pieces = [(x, y) for (x, y), color in locations.items() if color == opponent]
    
    dy = 1 if role == "black" else -1  # My forward direction
    o_dy = -dy  # Opponent's forward direction
    
    def wrap_y(y):
        return ((y - 1) % 8) + 1
    
    # Generate all legal moves and jumps
    legal_moves = []
    legal_jumps = []
    
    for (x, y) in my_pieces:
        for dx in [-1, 1]:
            nx = x + dx
            ny = wrap_y(y + dy)
            
            if 1 <= nx <= 8:
                if (nx, ny) not in locations:
                    legal_moves.append((x, y, nx, ny))
                elif locations[(nx, ny)] == opponent:
                    jx = nx + dx
                    jy = wrap_y(ny + dy)
                    if 1 <= jx <= 8 and (jx, jy) not in locations:
                        legal_jumps.append((x, y, nx, ny, jx, jy))
    
    if not legal_moves and not legal_jumps:
        return "noop"
    
    def is_threatened(tx, ty, empty_squares):
        """Check if position (tx,ty) can be captured by opponent."""
        for dx in [-1, 1]:
            opp_x = tx - dx
            opp_y = wrap_y(ty - o_dy)
            if 1 <= opp_x <= 8 and (opp_x, opp_y) in opp_pieces:
                land_x = tx + dx
                land_y = wrap_y(ty + o_dy)
                if 1 <= land_x <= 8:
                    if (land_x, land_y) in empty_squares or (land_x, land_y) not in locations:
                        return True
        return False
    
    def score_jump(jump):
        x, y, mx, my, jx, jy = jump
        score = 1000  # Base value for capture
        if is_threatened(jx, jy, [(x, y), (mx, my)]):
            score -= 30  # Risk of recapture
        # Advancement bonus
        if role == "black":
            advance = (jy - y) if jy >= y else (jy + 8 - y)
        else:
            advance = (y - jy) if y >= jy else (y + 8 - jy)
        score += advance
        return score
    
    def score_move(move):
        x, y, nx, ny = move
        score = 0
        
        currently_threatened = is_threatened(x, y, [])
        
        # Advancement bonus
        if role == "black":
            advance = (ny - y) if ny >= y else (ny + 8 - y)
        else:
            advance = (y - ny) if y >= ny else (y + 8 - ny)
        score += advance * 3
        
        dest_threatened = is_threatened(nx, ny, [(x, y)])
        
        # Safety evaluation
        if currently_threatened and not dest_threatened:
            score += 60  # Escaping to safety
        elif not currently_threatened and dest_threatened:
            score -= 80  # Moving into danger
        elif currently_threatened and dest_threatened:
            score -= 30  # Still in danger
        else:
            score += 10  # Staying safe
        
        # Center control
        center_dist = abs(nx - 4.5) + abs(ny - 4.5)
        score += max(0, int(6 - center_dist))
        
        # Bonus for threatening opponent pieces
        for dx in [-1, 1]:
            threat_x = nx + dx
            threat_y = wrap_y(ny + dy)
            if 1 <= threat_x <= 8 and (threat_x, threat_y) in opp_pieces:
                land_x = threat_x + dx
                land_y = wrap_y(threat_y + dy)
                if 1 <= land_x <= 8 and (land_x, land_y) not in locations:
                    score += 15
        
        return score
    
    # Prioritize jumps over regular moves
    if legal_jumps:
        best = max(legal_jumps, key=score_jump)
        return f"jump({best[0]},{best[1]},{best[2]},{best[3]},{best[4]},{best[5]})"
    else:
        best = max(legal_moves, key=score_move)
        return f"move({best[0]},{best[1]},{best[2]},{best[3]})"
