
def policy(state: list[list[object]], role: str) -> str:
    # Identify occupied cells and find empty ones
    occupied = set()
    for prop in state:
        if prop[0] == "cell":
            occupied.add((prop[1], prop[2]))
    
    # Board dimensions based on game rules and observations (a-i, 1-9)
    letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i']
    numbers = ['1', '2', '3', '4', '5', '6', '7', '8', '9']
    
    # Find all possible moves
    legal_moves = []
    for l in letters:
        for n in numbers:
            if (l, n) not in occupied:
                # The game forbids placing in certain unusable cells; 
                # we just check against the 'occupied' set.
                legal_moves.append((l, n))
    
    # Simple evaluation: calculate how many lines the move improves
    # We look for the best move by checking which one increases our line_count
    def evaluate_move(l, n, role):
        score = 0
        # Check current line counts for this cell to see if we are close to a majority
        for prop in state:
            if prop[0] == "line_count":
                # If the line already has high counts, taking it is good
                if (prop[1] == l or prop[1] == n) and prop[2] == role:
                    score += int(prop[3])
        return score

    best_move = None
    best_score = -1
    
    for l, n in legal_moves:
        score = evaluate_move(l, n, role)
        if score > best_score:
            best_score = score
            best_move = (l, n)
            
    # Default selection if no heuristic score difference
    if not best_move and legal_moves:
        best_move = legal_moves[0]
        
    return f"place({best_move[0]},{best_move[1]})"
