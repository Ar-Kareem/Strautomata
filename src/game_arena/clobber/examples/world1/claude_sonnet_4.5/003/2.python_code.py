
def policy(you: list[int], opponent: list[int]) -> str:
    import numpy as np
    
    you = np.array(you)
    opponent = np.array(opponent)
    
    def get_legal_moves(player, other):
        """Get all legal moves for player."""
        moves = []
        directions = [(-1, 0, 'U'), (1, 0, 'D'), (0, -1, 'L'), (0, 1, 'R')]
        
        for r in range(5):
            for c in range(6):
                if player[r, c] == 1:
                    for dr, dc, dir_name in directions:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < 5 and 0 <= nc < 6 and other[nr, nc] == 1:
                            moves.append((r, c, dir_name))
        return moves
    
    def apply_move(player, other, move):
        """Apply a move and return new board states."""
        new_player = player.copy()
        new_other = other.copy()
        r, c, direction = move
        
        dr, dc = {'U': (-1, 0), 'D': (1, 0), 'L': (0, -1), 'R': (0, 1)}[direction]
        nr, nc = r + dr, c + dc
        
        new_player[r, c] = 0
        new_player[nr, nc] = 1
        new_other[nr, nc] = 0
        
        return new_player, new_other
    
    def evaluate(player, other):
        """Evaluate board position from player's perspective."""
        player_moves = len(get_legal_moves(player, other))
        other_moves = len(get_legal_moves(other, player))
        
        # Win/loss detection
        if player_moves == 0:
            return -10000
        if other_moves == 0:
            return 10000
        
        # Mobility advantage (most important)
        mobility_score = (player_moves - other_moves) * 100
        
        # Material count
        material_score = (np.sum(player) - np.sum(other)) * 50
        
        # Centrality bonus
        center_weights = np.array([
            [1, 2, 2, 2, 2, 1],
            [2, 3, 3, 3, 3, 2],
            [2, 3, 4, 4, 3, 2],
            [2, 3, 3, 3, 3, 2],
            [1, 2, 2, 2, 2, 1]
        ])
        centrality = np.sum(player * center_weights) - np.sum(other * center_weights)
        
        return mobility_score + material_score + centrality
    
    def minimax(player, other, depth, alpha, beta, maximizing):
        """Minimax with alpha-beta pruning."""
        if depth == 0:
            return evaluate(player, other), None
        
        moves = get_legal_moves(player, other)
        if not moves:
            return -10000 if maximizing else 10000, None
        
        # Move ordering: prioritize central captures
        def move_priority(move):
            r, c, d = move
            dr, dc = {'U': (-1, 0), 'D': (1, 0), 'L': (0, -1), 'R': (0, 1)}[d]
            nr, nc = r + dr, c + dc
            # Prioritize capturing central pieces
            return -(abs(nr - 2) + abs(nc - 2.5))
        
        moves.sort(key=move_priority)
        
        best_move = moves[0]
        
        if maximizing:
            max_eval = -float('inf')
            for move in moves:
                new_player, new_other = apply_move(player, other, move)
                eval_score, _ = minimax(new_other, new_player, depth - 1, alpha, beta, False)
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for move in moves:
                new_player, new_other = apply_move(player, other, move)
                eval_score, _ = minimax(new_other, new_player, depth - 1, alpha, beta, True)
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval, best_move
    
    # Get all legal moves as fallback
    legal_moves = get_legal_moves(you, opponent)
    
    if not legal_moves:
        # Should never happen, but return something valid
        return "0,0,R"
    
    # Use minimax to find best move
    depth = 4  # Adjust based on performance
    _, best_move = minimax(you, opponent, depth, -float('inf'), float('inf'), True)
    
    if best_move is None:
        best_move = legal_moves[0]
    
    return f"{best_move[0]},{best_move[1]},{best_move[2]}"
