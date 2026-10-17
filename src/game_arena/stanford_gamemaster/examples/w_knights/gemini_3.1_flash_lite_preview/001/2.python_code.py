
def policy(state: list[list[object]], role: str) -> str:
    # Map letters to numbers for easier calculation
    cols = {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6}
    inv_cols = {v: k for k, v in cols.items()}
    
    board = {}
    for fact in state:
        if fact[0] == "cell":
            board[(fact[1], int(fact[2]))] = fact[3]
    
    direction = 1 if role == "white" else -1
    opponent = "black" if role == "white" else "white"
    
    possible_moves = []
    
    # Identify all current pieces belonging to the player
    my_pieces = [pos for pos, owner in board.items() if owner == role]
    
    # Possible knight jump offsets
    offsets = [(1, 2), (1, -2), (-1, 2), (-1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1)]
    
    for (c, r) in my_pieces:
        curr_c = cols[c]
        for dc, dr in offsets:
            # Game constraint: Cannot move backward
            if (role == "white" and dr < 0) or (role == "black" and dr > 0):
                continue
                
            nc, nr = curr_c + dc, r + dr
            if 1 <= nc <= 6 and 1 <= nr <= 6:
                target_col = inv_cols[nc]
                # Cannot move to a square occupied by my own piece
                if board.get((target_col, nr)) == role:
                    continue
                
                # Evaluation: Check win, then capture, then utility
                score = 0
                if (role == "white" and nr == 6) or (role == "black" and nr == 1):
                    score += 1000 # Winning move
                if board.get((target_col, nr)) == opponent:
                    score += 100  # Capture
                
                possible_moves.append((score, f"move({c},{r},{target_col},{nr})"))
    
    if not possible_moves:
        # Fallback (should not happen in legal state)
        return ""
        
    # Pick the move with the highest utility
    possible_moves.sort(key=lambda x: x[0], reverse=True)
    return possible_moves[0][1]
