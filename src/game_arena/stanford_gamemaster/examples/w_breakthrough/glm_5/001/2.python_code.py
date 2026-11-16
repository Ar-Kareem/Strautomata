
def policy(state: list[list[object]], role: str) -> str:
    """
    Breakthrough policy using minimax with alpha-beta pruning.
    Optimized for the race-to-finish nature of the game.
    """
    
    # Parse board state
    board = {}
    for prop in state:
        if len(prop) >= 4 and prop[0] == "cell":
            board[(int(prop[1]), int(prop[2]))] = prop[3]
    
    # Game parameters
    if role == "white":
        direction = 1
        my_goal, opp_goal = 8, 1
    else:
        direction = -1
        my_goal, opp_goal = 1, 8
    opponent = "black" if role == "white" else "white"
    
    def get_moves(b, color):
        """Generate all legal moves for the given color."""
        d = 1 if color == "white" else -1
        opp = "black" if color == "white" else "white"
        moves = []
        for (c, r), pc in list(b.items()):
            if pc != color:
                continue
            nr = r + d
            if not (1 <= nr <= 8):
                continue
            # Forward move
            if (c, nr) not in b:
                moves.append((c, r, c, nr))
            # Diagonal moves (including captures)
            for dc in [-1, 1]:
                nc = c + dc
                if 1 <= nc <= 8:
                    tgt = (nc, nr)
                    if tgt not in b or b.get(tgt) == opp:
                        moves.append((c, r, nc, nr))
        return moves
    
    def apply(b, m):
        """Apply move and return new board state."""
        nb = dict(b)
        fc, fr, tc, tr = m
        p = nb[(fc, fr)]
        del nb[(fc, fr)]
        nb[(tc, tr)] = p
        return nb
    
    def terminal(b):
        """Check for game winner."""
        for (c, r), col in b.items():
            if col == "white" and r == 8:
                return "white"
            if col == "black" and r == 1:
                return "black"
        return None
    
    def evaluate(b, my_color):
        """Heuristic evaluation from my_color's perspective."""
        opp = "black" if my_color == "white" else "white"
        goal = 8 if my_color == "white" else 1
        opp_goal = 1 if my_color == "white" else 8
        
        w = terminal(b)
        if w == my_color:
            return 100000
        if w == opp:
            return -100000
        
        score = 0
        my_min_dist, opp_min_dist = 8, 8
        
        for (c, r), col in b.items():
            if col == my_color:
                dist = abs(goal - r)
                my_min_dist = min(my_min_dist, dist)
                score += (8 - dist) * 30  # Advancement value
                if dist <= 3:
                    score += (4 - dist) * 150  # Close to winning bonus
                if dist <= 2:
                    score += 250
                if dist == 1:
                    score += 500  # One move from victory
                if 3 <= c <= 6:
                    score += 10  # Center control
            else:
                dist = abs(opp_goal - r)
                opp_min_dist = min(opp_min_dist, dist)
                score -= (8 - dist) * 30
                if dist <= 3:
                    score -= (4 - dist) * 150
                if dist <= 2:
                    score -= 250
                if dist == 1:
                    score -= 500
        
        # Race advantage bonus
        if my_min_dist < opp_min_dist:
            score += (opp_min_dist - my_min_dist) * 80
        
        return score
    
    def order_moves(moves, b, color):
        """Order moves for better alpha-beta pruning."""
        goal = 8 if color == "white" else 1
        opp_goal = 1 if color == "white" else 8
        opp = "black" if color == "white" else "white"
        
        def move_score(m):
            fc, fr, tc, tr = m
            s = 0
            # Winning move
            if (color == "white" and tr == 8) or (color == "black" and tr == 1):
                s += 100000
            # Capture bonus (especially advanced pieces)
            if (tc, tr) in b and b[(tc, tr)] == opp:
                adv = abs(opp_goal - tr)
                s += 200 + adv * 40
            # Progress toward goal
            s += (8 - abs(goal - tr)) * 25
            return s
        return sorted(moves, key=move_score, reverse=True)
    
    def minimax(b, depth, alpha, beta, is_max, my_color):
        """Minimax with alpha-beta pruning."""
        if depth == 0 or terminal(b):
            return evaluate(b, my_color), None
        
        cur = my_color if is_max else ("black" if my_color == "white" else "white")
        moves = get_moves(b, cur)
        if not moves:
            return evaluate(b, my_color), None
        
        ordered = order_moves(moves, b, cur)
        best = ordered[0]
        
        if is_max:
            max_val = float('-inf')
            for m in ordered:
                val, _ = minimax(apply(b, m), depth - 1, alpha, beta, False, my_color)
                if val > max_val:
                    max_val = val
                    best = m
                alpha = max(alpha, val)
                if beta <= alpha:
                    break
            return max_val, best
        else:
            min_val = float('inf')
            for m in ordered:
                val, _ = minimax(apply(b, m), depth - 1, alpha, beta, True, my_color)
                if val < min_val:
                    min_val = val
                    best = m
                beta = min(beta, val)
                if beta <= alpha:
                    break
            return min_val, best
    
    # Adaptive search depth based on game phase
    piece_count = len(board)
    depth = 6 if piece_count <= 6 else 5 if piece_count <= 12 else 4 if piece_count <= 20 else 3
    
    # Run minimax search
    _, best_move = minimax(board, depth, float('-inf'), float('inf'), True, role)
    
    # Fallback to best immediate move
    if best_move is None:
        moves = get_moves(board, role)
        if moves:
            best_move = order_moves(moves, board, role)[0]
        else:
            best_move = (1, 2, 1, 3)  # Should never reach here in valid game
    
    return f"move({best_move[0]},{best_move[1]},{best_move[2]},{best_move[3]})"
