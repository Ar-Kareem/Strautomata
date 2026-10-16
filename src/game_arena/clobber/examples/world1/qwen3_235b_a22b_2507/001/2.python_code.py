
def policy(you: list[int], opponent: list[int]) -> str:
    # Directions: U, R, D, L
    dirs = [(-1, 0), (0, 1), (1, 0), (0, -1)]
    dir_names = ['U', 'R', 'D', 'L']
    
    rows, cols = 5, 6
    legal_moves = []
    
    # Convert flat lists to 2D if needed? Wait: the input is 5x6, but are they flat?
    # The problem says "5x6 arrays", but Python type hint is list[int]. 
    # It's ambiguous, but from context, we assume they are flat lists of 30 elements in row-major order.
    # But let's read the problem again: it says `you[row, col]` — this suggests 2D indexing.
    # However, the type is `list[int]`, which is 1D.
    # This is a conflict. But in competitive settings, often flat arrays are used.
    # But the example uses 2D indexing. So likely, it's a 2D list of lists.
    # But the type hint is `list[int]`, which is 1D.
    # Let me re-read: "you: list[int]", so it must be 1D array of 30 integers.
    # So we must index as: you[row * 6 + col]
    
    def get(grid, r, c):
        if 0 <= r < 5 and 0 <= c < 6:
            return grid[r * 6 + c]
        return 0  # out of bounds is 0 (no piece)
    
    # Find all legal moves and collect them
    for r in range(5):
        for c in range(6):
            if get(you, r, c):  # if we have a piece here
                for (dr, dc), dname in zip(dirs, dir_names):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 5 and 0 <= nc < 6:
                        if get(opponent, nr, nc):  # opponent piece at destination
                            legal_moves.append((r, c, dname, nr, nc))
    
    # If no legal moves, this shouldn't happen, but in case:
    if not legal_moves:
        # This is invalid, but we must return something
        # Fallback: scan for any of our pieces and any adjacent opponent? but problem says at least one exists.
        # So we just return a dummy
        for r in range(5):
            for c in range(6):
                if get(you, r, c):
                    for (dr, dc), dname in zip(dirs, dir_names):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < 5 and 0 <= nc < 6 and get(opponent, nr, nc):
                            return f"{r},{c},{dname}"
        # last resort:
        return "0,0,R"
    
    best_move = None
    best_score = float('-inf')
    
    for (r, c, dname, nr, nc) in legal_moves:
        # Count how many of our pieces are adjacent to the *target* cell (nr, nc)
        # The idea: if many of our pieces are attacking the same opponent, we can leave that capture for later.
        # So we prefer to capture an opponent piece that is attacked by fewer of our pieces.
        attackers = 0
        for dr2, dc2 in dirs:
            r2, c2 = nr + dr2, nc + dc2
            if get(you, r2, c2):
                attackers += 1
        
        # Count how many moves our current piece (r,c) has before moving (excluding this move)
        mobility_here = 0
        for (dr2, dc2), dname2 in zip(dirs, dir_names):
            nr2, nc2 = r + dr2, c + dc2
            if 0 <= nr2 < 5 and 0 <= nc2 < 6 and get(opponent, nr2, nc2):
                mobility_here += 1
        
        # But after moving, we leave (r,c) and go to (nr,nc). We could compute future mobility, but that's heavier.
        # Instead, we prefer to move pieces that have low current mobility (so we "free" them)
        
        # Score: we want to minimize the number of attackers on the target (so less competition for this capture)
        # And we want to maximize the mobility of the piece we're moving? Or prefer moving low-mobility pieces?
        # If a piece has only one move, we should probably do it before we lose the chance.
        # So: higher score for lower attackers on target, and higher for lower mobility (meaning we have to take the chance now)
        # But if mobility is 1, we have only this one move, so we must do it. So we prioritize such moves.
        # So: score = (some measure of urgency)
        
        # We design score as:
        #   score = -attackers + 10 * (1 if mobility_here == 1 else 0)  # urgency if only one move
        # But simpler: prefer moves that are the only move for that piece.
        # But what if multiple pieces have only one move? then we prefer the one with least attacked target.
        
        score = -attackers
        if mobility_here == 1:
            score += 10  # strong bonus to take a piece's only move
        
        if score > best_score:
            best_score = score
            best_move = (r, c, dname)
    
    # best_move is guaranteed to be set because legal_moves is non-empty
    r, c, dname = best_move
    return f"{r},{c},{dname}"
