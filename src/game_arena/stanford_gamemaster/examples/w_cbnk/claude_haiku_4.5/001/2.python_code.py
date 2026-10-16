
def policy(state: list[list[object]], role: str) -> str:
    # Parse the state
    pieces = {}
    for fact in state:
        if fact[0] == "location":
            x, y, color = int(fact[1]), int(fact[2]), fact[3]
            if color not in pieces:
                pieces[color] = []
            pieces[color].append((x, y))
    
    my_pieces = pieces.get(role, [])
    opp_role = "red" if role == "black" else "black"
    opp_pieces = pieces.get(opp_role, [])
    
    if not my_pieces:
        return "noop"
    
    opp_set = set(opp_pieces)
    my_set = set(my_pieces)
    
    # Direction based on role: black moves down (y increases or wraps), red moves up (y decreases or wraps)
    if role == "black":
        directions = [(1, 1), (-1, 1), (1, -1), (-1, -1)]
    else:
        directions = [(1, -1), (-1, -1), (1, 1), (-1, 1)]
    
    def wrap(pos):
        """Wrap coordinates to 1-8 range"""
        x, y = pos
        x = ((x - 1) % 8) + 1
        y = ((y - 1) % 8) + 1
        return (x, y)
    
    # First, look for jumps (captures)
    jumps = []
    for px, py in my_pieces:
        for dx, dy in directions:
            # Check for opponent piece to jump over
            jx, jy = wrap((px + dx, py + dy))
            if (jx, jy) in opp_set:
                # Can we land on the other side?
                lx, ly = wrap((jx + dx, jy + dy))
                if (lx, ly) not in my_set and (lx, ly) not in opp_set:
                    jumps.append(f"jump({px},{py},{jx},{jy},{lx},{ly})")
    
    if jumps:
        return jumps[0]
    
    # If no jumps, look for regular moves
    moves = []
    for px, py in my_pieces:
        for dx, dy in directions:
            nx, ny = wrap((px + dx, py + dy))
            if (nx, ny) not in my_set and (nx, ny) not in opp_set:
                moves.append(f"move({px},{py},{nx},{ny})")
    
    if moves:
        return moves[0]
    
    # No moves available
    return "noop"
