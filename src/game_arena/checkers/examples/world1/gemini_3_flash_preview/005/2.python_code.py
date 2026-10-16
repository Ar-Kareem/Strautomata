
import time

def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    start_time = time.time()
    
    my_pieces = set(my_men) | set(my_kings)
    opp_pieces = set(opp_men) | set(opp_kings)
    
    def get_moves(m_men, m_kings, o_men, o_kings, current_color):
        captures = []
        regular_moves = []
        
        m_set = set(m_men) | set(m_kings)
        o_set = set(o_men) | set(o_kings)
        all_occupied = m_set | o_set
        
        # Directions: Black moves down (-1), White moves up (+1)
        fwd = -1 if current_color == 'b' else 1
        
        # Check for captures first
        for p in m_set:
            is_king = p in m_kings
            dirs = [(fwd, 1), (fwd, -1), (-fwd, 1), (-fwd, -1)] if is_king else [(fwd, 1), (fwd, -1)]
            
            for dr, dc in dirs:
                mid = (p[0] + dr, p[1] + dc)
                end = (p[0] + 2*dr, p[1] + 2*dc)
                if 0 <= end[0] <= 7 and 0 <= end[1] <= 7:
                    if mid in o_set and end not in all_occupied:
                        captures.append((p, end))
        
        if captures:
            return captures, True
            
        # Check for regular moves
        for p in m_set:
            is_king = p in m_kings
            dirs = [(fwd, 1), (fwd, -1), (-fwd, 1), (-fwd, -1)] if is_king else [(fwd, 1), (fwd, -1)]
            for dr, dc in dirs:
                end = (p[0] + dr, p[1] + dc)
                if 0 <= end[0] <= 7 and 0 <= end[1] <= 7:
                    if end not in all_occupied:
                        regular_moves.append((p, end))
                        
        return regular_moves, False

    def evaluate(m_men, m_kings, o_men, o_kings):
        # Simple material + position evaluation
        score = len(m_men) * 10 + len(m_kings) * 15
        score -= (len(o_men) * 10 + len(o_kings) * 15)
        
        # Positional bonuses
        for r, c in m_men:
            # Encourage advancing
            dist = (7 - r) if color == 'w' else r
            score += dist * 0.1
            if 2 <= c <= 5: score += 0.2 # Center control
        for r, c in m_kings:
            if 2 <= c <= 5 and 2 <= r <= 5: score += 0.5
            
        return score

    def minimax(m_men, m_kings, o_men, o_kings, depth, alpha, beta, maximizing):
        if depth == 0 or time.time() - start_time > 0.8:
            return evaluate(m_men, m_kings, o_men, o_kings)
        
        moves, is_cap = get_moves(m_men, m_kings, o_men, o_kings, color if maximizing else ('w' if color == 'b' else 'b'))
        
        if not moves:
            return -999 if maximizing else 999
            
        if maximizing:
            max_eval = -float('inf')
            for move in moves:
                # Simulate move (Simple one-step simulation)
                # Note: Multi-jump is not fully simulated here for speed, but single-step is legal
                eval = minimax(m_men, m_kings, o_men, o_kings, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha: break
            return max_eval
        else:
            min_eval = float('inf')
            for move in moves:
                eval = minimax(m_men, m_kings, o_men, o_kings, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha: break
            return min_eval

    # Root logic
    best_move = None
    best_val = -float('inf')
    legal_moves, is_capture = get_moves(my_men, my_kings, opp_men, opp_kings, color)
    
    if not legal_moves:
        return None # Should not happen in arena
        
    for move in legal_moves:
        # Shallow search to pick the best looking move
        val = minimax(my_men, my_kings, opp_men, opp_kings, 3, -float('inf'), float('inf'), False)
        if val > best_val:
            best_val = val
            best_move = move
            
    return best_move if best_move else legal_moves[0]
