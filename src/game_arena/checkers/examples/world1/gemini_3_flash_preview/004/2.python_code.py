
import time

def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    start_time = time.time()
    
    # Square color check: pieces should only be on (r + c) % 2 == 0
    # Black moves downwards (rows decrease), White moves upwards (rows increase)
    is_white = (color == 'w')
    
    def get_legal_moves(m_men, m_kings, o_men, o_kings, side_white):
        jump_moves = []
        simple_moves = []
        
        my_all = set(m_men) | set(m_kings)
        opp_all = set(o_men) | set(o_kings)
        occupied = my_all | opp_all
        
        forward = 1 if side_white else -1
        
        # Check for jumps first (mandatory)
        for p in m_men:
            for dr, dc in [(forward, 1), (forward, -1)]:
                mid = (p[0] + dr, p[1] + dc)
                end = (p[0] + 2 * dr, p[1] + 2 * dc)
                if 0 <= end[0] <= 7 and 0 <= end[1] <= 7:
                    if mid in opp_all and end not in occupied:
                        jump_moves.append((p, end))
        
        for p in m_kings:
            for dr, dc in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
                mid = (p[0] + dr, p[1] + dc)
                end = (p[0] + 2 * dr, p[1] + 2 * dc)
                if 0 <= end[0] <= 7 and 0 <= end[1] <= 7:
                    if mid in opp_all and end not in occupied:
                        jump_moves.append((p, end))
        
        if jump_moves:
            return jump_moves, True
        
        # Simple moves
        for p in m_men:
            for dr, dc in [(forward, 1), (forward, -1)]:
                end = (p[0] + dr, p[1] + dc)
                if 0 <= end[0] <= 7 and 0 <= end[1] <= 7 and end not in occupied:
                    simple_moves.append((p, end))
                    
        for p in m_kings:
            for dr, dc in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
                end = (p[0] + dr, p[1] + dc)
                if 0 <= end[0] <= 7 and 0 <= end[1] <= 7 and end not in occupied:
                    simple_moves.append((p, end))
                    
        return simple_moves, False

    def simulate_move(m_men, m_kings, o_men, o_kings, move, is_jump, side_white):
        new_m_men = set(m_men)
        new_m_kings = set(m_kings)
        new_o_men = set(o_men)
        new_o_kings = set(o_kings)
        
        start, end = move
        piece_king = start in new_m_kings
        
        if piece_king:
            new_m_kings.remove(start)
            new_m_kings.add(end)
        else:
            new_m_men.remove(start)
            if (side_white and end[0] == 7) or (not side_white and end[0] == 0):
                new_m_kings.add(end)
            else:
                new_m_men.add(end)
                
        if is_jump:
            mid = ((start[0] + end[0]) // 2, (start[1] + end[1]) // 2)
            if mid in new_o_men: new_o_men.remove(mid)
            elif mid in new_o_kings: new_o_kings.remove(mid)
            
        return list(new_m_men), list(new_m_kings), list(new_o_men), list(new_o_kings)

    def evaluate(m_men, m_kings, o_men, o_kings, side_white):
        score = 0
        # Material
        score += len(m_men) * 10 + len(m_kings) * 15
        score -= len(o_men) * 10 + len(o_kings) * 15
        
        # Position
        for r, c in m_men:
            dist = r if not side_white else 7 - r
            score += (7 - dist) * 0.1
        
        return score

    def alphabeta(m_men, m_kings, o_men, o_kings, depth, alpha, beta, maximizing, side_white):
        if depth == 0:
            return evaluate(m_men, m_kings, o_men, o_kings, side_white)
        
        moves, is_jump = get_legal_moves(m_men, m_kings, o_men, o_kings, side_white)
        if not moves:
            return -1000 if maximizing else 1000
        
        if maximizing:
            v = -float('inf')
            for move in moves:
                nm, nk, om, ok = simulate_move(m_men, m_kings, o_men, o_kings, move, is_jump, side_white)
                v = max(v, alphabeta(om, ok, nm, nk, depth - 1, -beta, -alpha, False, not side_white))
                alpha = max(alpha, v)
                if beta <= alpha: break
            return v
        else:
            v = float('inf')
            for move in moves:
                nm, nk, om, ok = simulate_move(m_men, m_kings, o_men, o_kings, move, is_jump, side_white)
                v = min(v, alphabeta(om, ok, nm, nk, depth - 1, -beta, -alpha, True, not side_white))
                beta = min(beta, v)
                if beta <= alpha: break
            return v

    # Root search
    best_move = None
    best_val = -float('inf')
    moves, is_jump = get_legal_moves(my_men, my_kings, opp_men, opp_kings, is_white)
    
    if not moves: return None # Should not happen in legal game
    if len(moves) == 1: return moves[0]

    depth = 4
    for move in moves:
        nm, nk, om, ok = simulate_move(my_men, my_kings, opp_men, opp_kings, move, is_jump, is_white)
        # Flip perspective: opponent is now 'maximizing' from their view
        val = -alphabeta(om, ok, nm, nk, depth, -float('inf'), float('inf'), False, not is_white)
        if val > best_val:
            best_val = val
            best_move = move
            
    return best_move if best_move else moves[0]
