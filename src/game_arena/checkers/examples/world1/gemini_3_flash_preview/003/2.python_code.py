
import random

def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    # Configuration
    MAX_DEPTH = 4
    
    direction = 1 if color == 'w' else -1
    promo_row = 7 if color == 'w' else 0
    opp_promo_row = 0 if color == 'w' else 7

    def get_legal_moves(men, kings, o_men, o_kings, is_white):
        dir_val = 1 if is_white else -1
        p_row = 7 if is_white else 0
        all_my = set(men) | set(kings)
        all_opp = set(o_men) | set(o_kings)
        occupied = all_my | all_opp
        
        captures = []
        
        def find_jumps(curr_pos, current_men, current_kings, is_k):
            found_any = False
            r, c = curr_pos
            # Directions: kings move any way, men move based on color
            dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)] if is_k else [(dir_val, -1), (dir_val, 1)]
            # Note: in checkers, men can actually jump backwards if it's a capture, 
            # but standard US rules usually only allow kings to jump backwards.
            # We follow standard: men jump forward, kings jump any way.
            if not is_k:
                dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)] # Competitive engines allow man-back-captures

            for dr, dc in dirs:
                mid = (r + dr, c + dc)
                end = (r + 2 * dr, c + 2 * dc)
                if 0 <= end[0] <= 7 and 0 <= end[1] <= 7:
                    if mid in (set(o_men) | set(o_kings)) and end not in occupied:
                        # This is a valid jump. For the "greedy" capture rule:
                        # We return the first step, but a real engine would look for sequences.
                        captures.append((curr_pos, end))
                        found_any = True
            return found_any

        # Check for mandatory captures
        for m in men:
            find_jumps(m, men, kings, False)
        for k in kings:
            find_jumps(k, men, kings, True)
            
        if captures:
            return captures, True
        
        # Slides
        slides = []
        for r, c in men:
            for dc in [-1, 1]:
                nr, nc = r + dir_val, c + dc
                if 0 <= nr <= 7 and 0 <= nc <= 7 and (nr, nc) not in occupied:
                    slides.append(((r, c), (nr, nc)))
        for r, c in kings:
            for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr <= 7 and 0 <= nc <= 7 and (nr, nc) not in occupied:
                    slides.append(((r, c), (nr, nc)))
        
        return slides, False

    def evaluate(m_men, m_kings, o_men, o_kings):
        # Weighted material
        score = len(m_men) * 10 + len(m_kings) * 18
        score -= (len(o_men) * 10 + len(o_kings) * 18)
        
        # Position bonuses
        for (r, c) in m_men:
            # Advance men
            dist = r if color == 'b' else 7 - r
            score += (7 - dist) * 0.5
            # Center control
            if 2 <= c <= 5 and 2 <= r <= 5:
                score += 0.2
        
        for (r, c) in m_kings:
            if 2 <= c <= 5 and 2 <= r <= 5:
                score += 0.5
                
        # Back row protection
        for (r, c) in m_men:
            if r == (0 if color == 'w' else 7):
                score += 0.3
                
        return score

    def minimax(m_men, m_kings, o_men, o_kings, depth, alpha, beta, maximizing):
        if depth == 0:
            return evaluate(m_men, m_kings, o_men, o_kings)
        
        moves, is_cap = get_legal_moves(m_men, m_kings, o_men, o_kings, maximizing)
        if not moves:
            return -1000 if maximizing else 1000
            
        if maximizing:
            max_eval = -float('inf')
            for move in moves:
                # Basic simulate
                new_m = [m for m in m_men if m != move[0]]
                new_k = [k for k in m_kings if k != move[0]]
                if move[0] in m_men:
                    if move[1][0] == promo_row: new_k.append(move[1])
                    else: new_m.append(move[1])
                else:
                    new_k.append(move[1])
                
                # If capture, remove opponent piece
                new_o_men, new_o_kings = list(o_men), list(o_kings)
                if is_cap:
                    mid = ((move[0][0] + move[1][0]) // 2, (move[0][1] + move[1][1]) // 2)
                    if mid in new_o_men: new_o_men.remove(mid)
                    elif mid in new_o_kings: new_o_kings.remove(mid)

                eval = minimax(new_m, new_k, new_o_men, new_o_kings, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha: break
            return max_eval
        else:
            min_eval = float('inf')
            # For simplicity, treat opponent as simple logic within minimax
            for move in moves:
                new_o_m = [m for m in o_men if m != move[0]]
                new_o_k = [k for k in o_kings if k != move[0]]
                if move[0] in o_men:
                    if move[1][0] == opp_promo_row: new_o_k.append(move[1])
                    else: new_o_m.append(move[1])
                else: new_o_k.append(move[1])
                
                new_m_men, new_m_kings = list(m_men), list(m_kings)
                if is_cap:
                    mid = ((move[0][0] + move[1][0]) // 2, (move[0][1] + move[1][1]) // 2)
                    if mid in new_m_men: new_m_men.remove(mid)
                    elif mid in new_m_kings: new_m_kings.remove(mid)

                eval = minimax(new_m_men, new_m_kings, new_o_m, new_o_k, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha: break
            return min_eval

    # Root Level
    legal_moves, _ = get_legal_moves(my_men, my_kings, opp_men, opp_kings, True)
    if not legal_moves:
        return None # Should not happen in legal game
        
    best_move = legal_moves[0]
    best_val = -float('inf')
    
    for move in legal_moves:
        # Simulate and evaluate
        n_m = [m for m in my_men if m != move[0]]
        n_k = [k for k in my_kings if k != move[0]]
        if move[0] in my_men:
            if move[1][0] == promo_row: n_k.append(move[1])
            else: n_m.append(move[1])
        else: n_k.append(move[1])
        
        n_o_m, n_o_k = list(opp_men), list(opp_kings)
        if abs(move[0][0] - move[1][0]) > 1:
            mid = ((move[0][0] + move[1][0]) // 2, (move[0][1] + move[1][1]) // 2)
            if mid in n_o_m: n_o_m.remove(mid)
            elif mid in n_o_k: n_o_k.remove(mid)
            
        val = minimax(n_m, n_k, n_o_m, n_o_k, MAX_DEPTH - 1, -float('inf'), float('inf'), False)
        if val > best_val:
            best_val = val
            best_move = move
            
    return best_move
