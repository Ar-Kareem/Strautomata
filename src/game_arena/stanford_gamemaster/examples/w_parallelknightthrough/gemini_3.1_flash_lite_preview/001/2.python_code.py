
def policy(state: list[list[object]], role: str) -> str:
    # Extract pieces for the current role
    pieces = {}
    for fact in state:
        if fact[0] == "cell":
            # fact format: ["cell", board_id, col, row, player]
            if fact[4] == role:
                pieces[(fact[1], fact[2], int(fact[3]))] = True
    
    # Identify occupied cells to prevent collisions
    occupied = {}
    for fact in state:
        if fact[0] == "cell":
            occupied[(fact[1], fact[2], int(fact[3]))] = fact[4]

    # Simple move generation logic for Knight-like move
    # White moves: row increases; Black moves: row decreases
    direction = 1 if role == "white" else -1
    
    # Look for a move that hasn't played in this step
    played_cols = {f[1] for f in state if f[0] == "played"}
    
    possible_moves = []
    for (b, c, r) in pieces.keys():
        if c in played_cols:
            continue
            
        # Possible knight moves: (delta_col, delta_row)
        # Assuming typical knight: 2 vertical, 1 horizontal
        for dc in [-1, 1]:
            dr = 2 * direction
            nc = chr(ord(c) + dc)
            nr = r + dr
            
            # Check boundaries (b: a/b/c, col: a/b/c, row: 1-8)
            if 'a' <= nc <= 'c' and 1 <= nr <= 8:
                if (b, nc, nr) not in occupied:
                    possible_moves.append(f"move({b},{c},{r},{nc},{nr})")
    
    # Strategy: execute a move if possible, else "tick"
    if possible_moves:
        return possible_moves[0]
    else:
        return "tick"
