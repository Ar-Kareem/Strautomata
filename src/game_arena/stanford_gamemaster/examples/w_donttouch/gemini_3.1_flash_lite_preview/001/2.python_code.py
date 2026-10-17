
def policy(state: list[list[object]], role: str) -> str:
    # Extract existing marks for the current player
    my_moves = []
    available_moves = []
    
    for item in state:
        if item[0] == "cell":
            r, c, val = int(item[1]), int(item[2]), item[3]
            if val == role:
                my_moves.append((r, c))
            elif val == "b":
                available_moves.append((r, c))
    
    # Try to find a move that is not adjacent to any of my previous moves
    # Adjacent means distance of 1 in either row or column (no diagonals)
    def is_safe(r, c):
        for mr, mc in my_moves:
            dist = abs(r - mr) + abs(c - mc)
            if dist == 1:
                return False
        return True
    
    safe_moves = [move for move in available_moves if is_safe(move[0], move[1])]
    
    # Choose a safe move if available, otherwise any legal move (first in list)
    if safe_moves:
        chosen = safe_moves[0]
    elif available_moves:
        chosen = available_moves[0]
    else:
        # Fallback (should not happen if game is not over)
        return ""
        
    return f"mark({chosen[0]},{chosen[1]})"
