
def policy(me, opponent, memory):
    # Initialize 19x19 board: 0=empty, 1=my stones, 2=opponent stones
    board = [[0]*19 for _ in range(19)]
    for r, c in me:
        board[r-1][c-1] = 1
    for r, c in opponent:
        board[r-1][c-1] = 2
    
    # Opening book: start at a corner star point
    if len(me) + len(opponent) == 0:
        return (4, 4), memory
    
    # Helper: generate valid neighbors
    def neighbors(r, c):
        for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)):
            nr, nc = r+dr, c+dc
            if 0 <= nr < 19 and 0 <= nc < 19:
                yield nr, nc
    
    # Helper: get liberties for a stone group using DFS
    def get_liberties(r, c, color):
        visited = set()
        stack = [(r, c)]
        liberties = set()
        while stack:
            cr, cc = stack.pop()
            if (cr, cc) in visited:
                continue
            visited.add((cr, cc))
            for nr, nc in neighbors(cr, cc):
                if board[nr][nc] == 0:
                    liberties.add((nr, nc))
                elif board[nr][nc] == color and (nr, nc) not in visited:
                    stack.append((nr, nc))
        return list(liberties)
    
    # Phase 1: Look for capture moves
    for r, c in opponent:
        r0, c0 = r-1, c-1
        if board[r0][c0] != 2:
            continue
        libs = get_liberties(r0, c0, 2)
        if len(libs) == 1:
            lr, lc = libs[0]
            # Test move legality
            board[lr][lc] = 1
            captured = any(len(get_liberties(nr, nc, 2)) == 0 
                          for nr, nc in neighbors(lr, lc) if board[nr][nc] == 2)
            our_libs = get_liberties(lr, lc, 1)
            board[lr][lc] = 0
            if captured or len(our_libs) > 0:
                return (lr+1, lc+1), memory
    
    # Phase 2: Look for defense moves (our stones in atari)
    for r, c in me:
        r0, c0 = r-1, c-1
        if board[r0][c0] != 1:
            continue
        libs = get_liberties(r0, c0, 1)
        if len(libs) == 1:
            lr, lc = libs[0]
            if board[lr][lc] != 0:
                continue
            # Test move legality
            board[lr][lc] = 1
            captured = any(len(get_liberties(nr, nc, 2)) == 0 
                          for nr, nc in neighbors(lr, lc) if board[nr][nc] == 2)
            our_libs = get_liberties(lr, lc, 1)
            board[lr][lc] = 0
            if captured or len(our_libs) > 0:
                return (lr+1, lc+1), memory
    
    # Phase 3: Evaluate all legal moves heuristically
    best_move = None
    best_score = -float('inf')
    total_stones = len(me) + len(opponent)
    
    for r in range(19):
        for c in range(19):
            if board[r][c] != 0:
                continue
            
            # Check move legality (no suicide without capture)
            board[r][c] = 1
            captured = any(len(get_liberties(nr, nc, 2)) == 0 
                          for nr, nc in neighbors(r, c) if board[nr][nc] == 2)
            our_libs = get_liberties(r, c, 1)
            board[r][c] = 0
            
            if not captured and len(our_libs) == 0:
                continue  # Illegal suicide move
            
            # Calculate heuristic score
            score = 0
            
            # Game stage positional preference
            center_dist = max(abs(r-9), abs(c-9))
            if total_stones < 60:  # Early/mid game
                score += 10 - center_dist
            else:  # Late game
                score -= center_dist
            
            # Bonus for adjacent opponent stones (pressure)
            opp_adj = sum(1 for nr, nc in neighbors(r, c) if board[nr][nc] == 2)
            score += opp_adj * 2
            
            # Bonus for adjacent empty points (territory)
            empty_adj = sum(1 for nr, nc in neighbors(r, c) if board[nr][nc] == 0)
            score += empty_adj
            
            # Star points bonus for good opening/honored points
            if r in (3, 9, 15) and c in (3, 9, 15):
                score += 5
            
            # Early game edge penalty
            if total_stones < 40 and (r in (0, 18) or c in (0, 18)):
                score -= 3
            
            if score > best_score:
                best_score = score
                best_move = (r+1, c+1)
    
    # If no good move found, pass
    return best_move or (0, 0), memory
