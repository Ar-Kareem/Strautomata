
def policy(state: list[list[object]], role: str) -> str:
    # 1. Parse current active board
    target_br, target_bc = None, None
    for fact in state:
        if fact[0] == "current":
            target_br, target_bc = fact[1], fact[2]
            break
            
    # 2. Identify empty cells on target board
    legal_moves = []
    for fact in state:
        if fact[0] == "cell":
            br, bc, r, c, val = fact[1], fact[2], fact[3], fact[4], fact[5]
            if br == target_br and bc == target_bc and val == 'b':
                legal_moves.append(f"mark({br},{bc},{r},{c})")
    
    # 3. Fallback: If target board is full, find any empty cell in the game
    if not legal_moves:
        for fact in state:
            if fact[0] == "cell" and fact[5] == "b":
                br, bc, r, c = fact[1], fact[2], fact[3], fact[4]
                legal_moves.append(f"mark({br},{bc},{r},{c})")
                
    # 4. Strategy: Prefer center (2,2), then others
    # Heuristic: return the move containing 2,2 if available, else first
    for move in legal_moves:
        if ",2,2)" in move:
            return move
            
    return legal_moves[0] if legal_moves else ""
