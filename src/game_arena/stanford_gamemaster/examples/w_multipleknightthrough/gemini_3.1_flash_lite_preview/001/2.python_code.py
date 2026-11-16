
def policy(state: list[list[object]], role: str) -> str:
    # Build a map of the board
    pieces = {}
    for fact in state:
        if fact[0] == "cell":
            # fact: ["cell", board, col, row, player]
            pieces[(fact[1], fact[2], int(fact[3]))] = fact[4]

    def is_legal(b, c, r, next_b, next_c, next_r, role):
        if not (1 <= next_r <= 8): return False
        if next_c not in ['a', 'b', 'c', 'd']: return False
        # Forward condition logic based on role
        if role == "white":
            if next_r <= r: return False
        else:
            if next_r >= r: return False
        
        # Check occupancy
        dest = (next_b, next_c, next_r)
        if pieces.get(dest) == role: return False
        
        return True

    # Offsets for knight movement
    offsets = [
        (1, 2), (1, -2), (-1, 2), (-1, -2),
        (2, 1), (2, -1), (-2, 1), (-2, -1)
    ]
    cols = ['a', 'b', 'c', 'd']
    
    candidates = []
    for (b, c, r), player in pieces.items():
        if player == role:
            col_idx = cols.index(c)
            for dc, dr in offsets:
                nc_idx = col_idx + dc
                nr = r + dr
                if 0 <= nc_idx < 4:
                    nc = cols[nc_idx]
                    # We can move between boards 'a', 'b', 'c' (arbitrary rule interpretation)
                    # Based on examples, knight moves seem to target any board
                    for next_b in ['a', 'b', 'c']:
                        if is_legal(b, c, r, next_b, nc, nr, role):
                            score = nr if role == "white" else (9 - nr)
                            # Primary board 'b' is the winning condition board
                            if next_b == 'b': score += 10
                            candidates.append((score, f"move({b},{c},{r},{next_b},{nr})"))

    if not candidates:
        return ""
    
    # Sort by score descending
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]
