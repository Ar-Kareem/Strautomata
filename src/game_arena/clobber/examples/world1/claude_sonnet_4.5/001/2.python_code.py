
def policy(you: list[int], opponent: list[int]) -> str:
    import numpy as np
    
    you = np.array(you)
    opponent = np.array(opponent)
    rows, cols = you.shape
    
    # Direction mappings
    directions = {
        'U': (-1, 0),
        'D': (1, 0),
        'L': (0, -1),
        'R': (0, 1)
    }
    dir_names = ['U', 'D', 'L', 'R']
    
    def get_legal_moves(my_pieces, opp_pieces):
        """Generate all legal moves for my_pieces"""
        moves = []
        for r in range(rows):
            for c in range(cols):
                if my_pieces[r, c] == 1:
                    for dir_name in dir_names:
                        dr, dc = directions[dir_name]
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < rows and 0 <= nc < cols and opp_pieces[nr, nc] == 1:
                            moves.append((r, c, dir_name))
        return moves
    
    def count_mobility(my_pieces, opp_pieces):
        """Count number of legal moves"""
        return len(get_legal_moves(my_pieces, opp_pieces))
    
    def apply_move(my_pieces, opp_pieces, move):
        """Apply a move and return new board states"""
        my_new = my_pieces.copy()
        opp_new = opp_pieces.copy()
        r, c, dir_name = move
        dr, dc = directions[dir_name]
        nr, nc = r + dr, c + dc
        
        my_new[r, c] = 0
        my_new[nr, nc] = 1
        opp_new[nr, nc] = 0
        
        return my_new, opp_new
    
    def count_neighbors(pieces, r, c):
        """Count friendly neighbors for clustering"""
        count = 0
        for dr, dc in directions.values():
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and pieces[nr, nc] == 1:
                count += 1
        return count
    
    def evaluate_move(move, my_pieces, opp_pieces):
        """Evaluate the quality of a move"""
        r, c, dir_name = move
        dr, dc = directions[dir_name]
        nr, nc = r + dr, c + dc
        
        # Apply move
        my_new, opp_new = apply_move(my_pieces, opp_pieces, move)
        
        # Calculate mobility difference after move
        my_mobility = count_mobility(my_new, opp_new)
        opp_mobility = count_mobility(opp_new, my_new)
        
        # If opponent has no moves, we win immediately
        if opp_mobility == 0:
            return 10000
        
        # If we have no moves after opponent's best response, avoid
        if my_mobility == 0:
            return -10000
        
        score = 0
        
        # Mobility advantage (most important)
        score += (my_mobility - opp_mobility) * 100
        
        # Center control bonus
        center_r, center_c = rows / 2, cols / 2
        dist_to_center = abs(nr - center_r) + abs(nc - center_c)
        score -= dist_to_center * 5
        
        # Clustering - prefer staying connected
        neighbors_before = count_neighbors(my_pieces, r, c)
        neighbors_after = count_neighbors(my_new, nr, nc)
        score += (neighbors_after - neighbors_before) * 10
        
        # Prefer positions with flexibility
        score += neighbors_after * 15
        
        # Piece count advantage
        my_count = np.sum(my_new)
        opp_count = np.sum(opp_new)
        score += (my_count - opp_count) * 20
        
        return score
    
    # Get all legal moves
    legal_moves = get_legal_moves(you, opponent)
    
    # Should never happen, but ensure we don't crash
    if not legal_moves:
        # Return any formatted string (we've already lost)
        return "0,0,R"
    
    # Evaluate all moves
    best_move = None
    best_score = float('-inf')
    
    for move in legal_moves:
        score = evaluate_move(move, you, opponent)
        if score > best_score:
            best_score = score
            best_move = move
    
    # Format and return the best move
    r, c, dir_name = best_move
    return f"{r},{c},{dir_name}"
