
def policy(state: list[list[object]], role: str) -> str:
    """
    Returns a legal move for the given role in the given state.
    Implements minimax with alpha-beta pruning for Reversum (6x6 Reversi).
    """
    # Constants
    SIZE = 6
    DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    CORNERS = [(1, 1), (1, 6), (6, 1), (6, 6)]
    
    # Parse state
    board = {}  # (r, c) -> color
    current_control = None
    for fact in state:
        if fact[0] == "cell":
            r, c, color = int(fact[1]), int(fact[2]), fact[3]
            board[(r, c)] = color
        elif fact[0] == "control":
            current_control = fact[1]
    
    opponent = "blue" if role == "red" else "red"
    
    def in_bounds(r, c):
        return 1 <= r <= SIZE and 1 <= c <= SIZE
    
    def get_legal_moves(player, b):
        """Return list of (r, c) legal moves for player on board b."""
        moves = []
        opp = "blue" if player == "red" else "red"
        for r in range(1, SIZE + 1):
            for c in range(1, SIZE + 1):
                if (r, c) in b:
                    continue
                # Check if any direction brackets opponent pieces
                for dr, dc in DIRECTIONS:
                    nr, nc = r + dr, c + dc
                    if not in_bounds(nr, nc) or (nr, nc) not in b or b[(nr, nc)] != opp:
                        continue
                    # Move in direction looking for player piece
                    found_opp = True
                    while in_bounds(nr, nc) and (nr, nc) in b and b[(nr, nc)] == opp:
                        nr += dr
                        nc += dc
                    if in_bounds(nr, nc) and (nr, nc) in b and b[(nr, nc)] == player:
                        moves.append((r, c))
                        break
        return moves
    
    def simulate_move(r, c, player, b):
        """Return new board after player places disk at (r,c)."""
        new_b = dict(b)
        new_b[(r, c)] = player
        opp = "blue" if player == "red" else "red"
        for dr, dc in DIRECTIONS:
            nr, nc = r + dr, c + dc
            to_flip = []
            while in_bounds(nr, nc) and (nr, nc) in new_b and new_b[(nr, nc)] == opp:
                to_flip.append((nr, nc))
                nr += dr
                nc += dc
            if in_bounds(nr, nc) and (nr, nc) in new_b and new_b[(nr, nc)] == player:
                for pos in to_flip:
                    new_b[pos] = player
        return new_b
    
    def evaluate(b, root_player):
        """Static evaluation of board from root_player's perspective."""
        opp = "blue" if root_player == "red" else "red"
        score = 0
        
        # Corners are paramount
        for cor in CORNERS:
            if cor in b:
                if b[cor] == root_player:
                    score += 100
                else:
                    score -= 100
        
        # Penalize dangerous squares if adjacent corner is empty or enemy-owned
        # C-squares (edge adjacent to corner)
        c_squares = {
            (1, 1): [(1, 2), (2, 1)],
            (1, 6): [(1, 5), (2, 6)],
            (6, 1): [(6, 2), (5, 1)],
            (6, 6): [(6, 5), (5, 6)]
        }
        # X-squares (diagonal to corner)
        x_squares = {
            (1, 1): [(2, 2)],
            (1, 6): [(2, 5)],
            (6, 1): [(5, 2)],
            (6, 6): [(5, 5)]
        }
        
        for cor in CORNERS:
            cor_owner = b.get(cor)
            adj_c = c_squares.get(cor, [])
            adj_x = x_squares.get(cor, [])
            
            for sq in adj_c:
                if sq in b:
                    if cor_owner is None:
                        score += -30 if b[sq] == root_player else 30
                    elif cor_owner == root_player:
                        if b[sq] == root_player:
                            score += 2
                    else:
                        if b[sq] == root_player:
                            score -= 2
            
            for sq in adj_x:
                if sq in b:
                    if cor_owner is None:
                        score += -20 if b[sq] == root_player else 20
                    elif cor_owner == root_player:
                        if b[sq] == root_player:
                            score += 2
        
        # Mobility difference
        my_moves = len(get_legal_moves(root_player, b))
        opp_moves = len(get_legal_moves(opp, b))
        score += (my_moves - opp_moves) * 5
        
        # Late game piece count (only when board is > 50% full)
        total_pieces = len(b)
        if total_pieces > 18:
            my_pieces = sum(1 for p in b.values() if p == root_player)
            opp_pieces = sum(1 for p in b.values() if p == opp)
            score += (my_pieces - opp_pieces) * 2
        
        return score
    
    def final_evaluation(b, root_player):
        """Evaluation when game is over (no moves for either player)."""
        opp = "blue" if root_player == "red" else "red"
        my_pieces = sum(1 for p in b.values() if p == root_player)
        opp_pieces = sum(1 for p in b.values() if p == opp)
        if my_pieces > opp_pieces:
            return 100000 + my_pieces
        elif opp_pieces > my_pieces:
            return -100000 - opp_pieces
        else:
            return 0
    
    def minimax(b, depth, player_to_move, alpha, beta, root_player):
        """Minimax with alpha-beta pruning."""
        opp = "blue" if player_to_move == "red" else "red"
        
        if depth == 0:
            return evaluate(b, root_player)
        
        legal_moves = get_legal_moves(player_to_move, b)
        
        # Check for pass or game end
        if not legal_moves:
            opp_legal = get_legal_moves(opp, b)
            if not opp_legal:
                return final_evaluation(b, root_player)
            # Pass turn to opponent
            return minimax(b, depth - 1, opp, alpha, beta, root_player)
        
        if player_to_move == root_player:
            # Maximizing
            max_eval = float('-inf')
            for move in legal_moves:
                new_b = simulate_move(move[0], move[1], player_to_move, b)
                eval_score = minimax(new_b, depth - 1, opp, alpha, beta, root_player)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            # Minimizing
            min_eval = float('inf')
            for move in legal_moves:
                new_b = simulate_move(move[0], move[1], player_to_move, b)
                eval_score = minimax(new_b, depth - 1, root_player, alpha, beta, root_player)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    # Get legal moves for current role
    legal_moves = get_legal_moves(role, board)
    
    if not legal_moves:
        # Should not happen in valid gameplay, but return a dummy to avoid crash
        return "move(1,1)"
    
    # Fast path: take corner if available (corners are almost always optimal)
    for cor in CORNERS:
        if cor in legal_moves:
            return f"move({cor[0]},{cor[1]})"
    
    # Search for best move using minimax (depth 4)
    best_move = legal_moves[0]
    best_score = float('-inf')
    depth = 4
    
    # Sort moves to improve alpha-beta pruning (center first-ish, though corners already handled)
    # Actually, prioritize moves that flip more pieces? Or just random.
    # Let's prioritize edges and moves near center for better pruning.
    def move_priority(m):
        r, c = m
        if (r in [1, 6] or c in [1, 6]):
            return 0  # Edges are good
        return 1
    legal_moves.sort(key=move_priority)
    
    for move in legal_moves:
        new_b = simulate_move(move[0], move[1], role, board)
        score = minimax(new_b, depth - 1, opponent, float('-inf'), float('inf'), role)
        if score > best_score:
            best_score = score
            best_move = move
    
    return f"move({best_move[0]},{best_move[1]})"
