
def policy(state: list[list[object]], role: str) -> str:
    """
    Policy for Chinook game.
    Strategy: Maximize progress toward target zones, prefer jumps for faster advancement.
    """
    # Parse board state
    board = {}
    for fact in state:
        if isinstance(fact, list) and len(fact) >= 4 and fact[0] == "cell":
            col, row, piece = fact[1], fact[2], fact[3]
            try:
                board[(col, int(row))] = piece
            except (ValueError, TypeError):
                continue
    
    if not board:
        return "move(a,1,b,2)"
    
    # Board utilities with wrap
    cols = ['a', 'b', 'c', 'd']
    
    def adj_col(c, delta):
        return cols[(cols.index(c) + delta) % 4]
    
    def adj_row(r, delta):
        return ((r - 1 + delta) % 8) + 1
    
    # Movement direction and target based on role
    if role == "red":
        directions = [(-1, 1), (1, 1)]  # Up-left, Up-right diagonals
        target_rows = {6, 7, 8}
    else:  # blue
        directions = [(-1, -1), (1, -1)]  # Down-left, Down-right diagonals
        target_rows = {1, 2, 3}
    
    # Generate all legal actions
    moves = []
    jumps = []
    
    for (col, row), piece in board.items():
        if piece != role:
            continue
        
        for dc, dr in directions:
            nc, nr = adj_col(col, dc), adj_row(row, dr)
            
            # Simple move to empty square
            if board.get((nc, nr)) == 'b':
                moves.append((col, row, nc, nr))
            
            # Jump over own piece to empty square beyond
            jc, jr = adj_col(nc, dc), adj_row(nr, dr)
            if board.get((nc, nr)) == role and board.get((jc, jr)) == 'b':
                jumps.append((col, row, nc, nr, jc, jr))
    
    # Scoring function for action selection
    def action_score(from_row, to_row, is_jump):
        score = 0
        
        # Big bonus for landing in target zone
        if to_row in target_rows:
            score += 50
        
        # Progress toward target
        if role == "red" and to_row > from_row:
            score += 10 * (to_row - from_row)
        elif role == "blue" and to_row < from_row:
            score += 10 * (from_row - to_row)
        
        # Jump bonus (jumps advance faster)
        if is_jump:
            score += 20
        
        return score
    
    # Score all actions
    actions = []
    for c, r, nc, nr, jc, jr in jumps:
        actions.append((action_score(r, jr, True), f"jump({c},{r},{nc},{nr},{jc},{jr})"))
    for c, r, nc, nr in moves:
        actions.append((action_score(r, nr, False), f"move({c},{r},{nc},{nr})"))
    
    # Select best action (highest score, alphabetically first on ties)
    if actions:
        actions.sort(key=lambda x: (-x[0], x[1]))
        return actions[0][1]
    
    return "move(a,1,b,2)"
