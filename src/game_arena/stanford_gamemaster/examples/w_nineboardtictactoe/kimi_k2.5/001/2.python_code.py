
def policy(state: list[list[object]], role: str) -> str:
    # Parse state
    grid = {}  # key: (sr, sc, r, c) -> 'x', 'o', or 'b'
    current_board = None
    
    for prop in state:
        if prop[0] == "cell":
            # Format: ["cell", super_r, super_c, sub_r, sub_c, value]
            _, sr, sc, r, c, val = prop
            grid[(int(sr), int(sc), int(r), int(c))] = val
        elif prop[0] == "current":
            # Format: ["current", super_r, super_c]
            current_board = (int(prop[1]), int(prop[2]))
    
    if current_board is None:
        # Should not happen in valid state, but fallback to center
        return "mark(2,2,2,2)"
    
    sr, sc = current_board
    opponent = 'o' if role == 'x' else 'x'
    
    # Generate legal moves (empty cells on current board)
    legal_moves = []
    for r in [1, 2, 3]:
        for c in [1, 2, 3]:
            if grid.get((sr, sc, r, c), 'b') == 'b':
                legal_moves.append((r, c))
    
    if not legal_moves:
        # No legal moves (should imply game over), return dummy
        return f"mark({sr},{sc},1,1)"
    
    # Helper: Check if player wins board (bsr, bsc) given a grid state
    def check_win(bsr, bsc, player, g):
        lines = [
            [(1,1),(1,2),(1,3)], [(2,1),(2,2),(2,3)], [(3,1),(3,2),(3,3)],
            [(1,1),(2,1),(3,1)], [(1,2),(2,2),(3,2)], [(1,3),(2,3),(3,3)],
            [(1,1),(2,2),(3,3)], [(1,3),(2,2),(3,1)]
        ]
        for line in lines:
            if all(g.get((bsr, bsc, rr, cc), 'b') == player for rr, cc in line):
                return True
        return False
    
    # Helper: Check if board is full
    def is_board_full(bsr, bsc):
        for r in [1, 2, 3]:
            for c in [1, 2, 3]:
                if grid.get((bsr, bsc, r, c), 'b') == 'b':
                    return False
        return True
    
    # Helper: Find moves that give player immediate win on board (bsr, bsc)
    def winning_moves(bsr, bsc, player):
        wins = []
        for r in [1, 2, 3]:
            for c in [1, 2, 3]:
                if grid.get((bsr, bsc, r, c), 'b') == 'b':
                    # Simulate
                    test_grid = {**grid, (bsr, bsc, r, c): player}
                    if check_win(bsr, bsc, player, test_grid):
                        wins.append((r, c))
        return wins
    
    # Check for immediate win on current board
    my_wins = winning_moves(sr, sc, role)
    if my_wins:
        r, c = my_wins[0]
        return f"mark({sr},{sc},{r},{c})"
    
    # Check for opponent threats on current board (to block)
    opp_threats = winning_moves(sr, sc, opponent)
    
    # Evaluate all legal moves
    candidates = []
    for r, c in legal_moves:
        score = 0
        
        # 1. Blocking opponent win on current board
        if (r, c) in opp_threats:
            score += 1000  # High priority, but less than winning (which we checked above)
        
        # 2. Positional value within current board
        if (r, c) == (2, 2):
            score += 10  # Center
        elif r in [1, 3] and c in [1, 3]:
            score += 5   # Corner
        else:
            score += 1   # Edge
        
        # 3. Target board analysis (opponent plays on board (r,c))
        tr, tc = r, c
        
        # Check if target board is dead (full or won)
        target_dead = (is_board_full(tr, tc) or 
                      check_win(tr, tc, role, grid) or 
                      check_win(tr, tc, opponent, grid))
        
        if target_dead:
            # Sending to dead board ends game in draw
            score -= 500
        else:
            # Check if opponent can win immediately on target board (bad)
            opp_wins_next = winning_moves(tr, tc, opponent)
            if opp_wins_next:
                score -= 200  # Avoid giving opponent winning board
            
            # Check if we have threats on target board (good, forces opponent to block)
            my_threats_there = winning_moves(tr, tc, role)
            if my_threats_there:
                score += 50   # We set up a win on the next meta-move
        
        candidates.append((score, r, c))
    
    # Select best move (highest score)
    candidates.sort(reverse=True, key=lambda x: x[0])
    best_r, best_c = candidates[0][1], candidates[0][2]
    
    return f"mark({sr},{sc},{best_r},{best_c})"
