
import copy

def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    
    def get_moves(m_men, m_kings, o_men, o_kings, p_color):
        jumps = []
        moves = []
        
        # Directions: white moves up (+1), black moves down (-1)
        m_dir = 1 if p_color == 'w' else -1
        opp_all = set(o_men) | set(o_kings)
        my_all = set(m_men) | set(m_kings)
        occupied = my_all | opp_all

        # Check Jumps first (Mandatory)
        for p in m_men + m_kings:
            is_king = p in m_kings
            dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)] if is_king else [(m_dir, -1), (m_dir, 1)]
            for dr, dc in dirs:
                mid = (p[0] + dr, p[1] + dc)
                end = (p[0] + 2 * dr, p[1] + 2 * dc)
                if 0 <= end[0] <= 7 and 0 <= end[1] <= 7:
                    if mid in opp_all and end not in occupied:
                        jumps.append((p, end))
        
        if jumps:
            return jumps, True
            
        # Check simple moves
        for p in m_men + m_kings:
            is_king = p in m_kings
            dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)] if is_king else [(m_dir, -1), (m_dir, 1)]
            for dr, dc in dirs:
                end = (p[0] + dr, p[1] + dc)
                if 0 <= end[0] <= 7 and 0 <= end[1] <= 7:
                    if end not in occupied:
                        moves.append((p, end))
        return moves, False

    def simulate_move(m_men, m_kings, o_men, o_kings, move, is_jump, p_color):
        new_m_men = [p for p in m_men if p != move[0]]
        new_m_kings = [p for p in m_kings if p != move[0]]
        new_o_men = list(o_men)
        new_o_kings = list(o_kings)
        
        end_pos = move[1]
        promoted = False
        if move[0] in m_men:
            if (p_color == 'w' and end_pos[0] == 7) or (p_color == 'b' and end_pos[0] == 0):
                new_m_kings.append(end_pos)
                promoted = True
            else:
                new_m_men.append(end_pos)
        else:
            new_m_kings.append(end_pos)
            
        if is_jump:
            mid = ((move[0][0] + end_pos[0]) // 2, (move[0][1] + end_pos[1]) // 2)
            if mid in new_o_men: new_o_men.remove(mid)
            elif mid in new_o_kings: new_o_kings.remove(mid)
            
        return new_m_men, new_m_kings, new_o_men, new_o_kings

    def evaluate(m_men, m_kings, o_men, o_kings, p_color):
        score = 0
        score += len(m_men) * 10 + len(m_kings) * 15
        score -= (len(o_men) * 10 + len(o_kings) * 15)
        # Position bonuses
        for r, c in m_men:
            score += (r if p_color == 'w' else 7 - r) * 0.1
        return score

    def minimax(m_men, m_kings, o_men, o_kings, depth, alpha, beta, maximizing, p_color):
        if depth == 0:
            return evaluate(m_men, m_kings, o_men, o_kings, p_color)
        
        opp_c = 'b' if p_color == 'w' else 'w'
        moves, is_jump = get_moves(m_men, m_kings, o_men, o_kings, p_color)
        
        if not moves:
            return -1000 if maximizing else 1000
        
        if maximizing:
            max_eval = -float('inf')
            for move in moves:
                nm, nk, om, ok = simulate_move(m_men, m_kings, o_men, o_kings, move, is_jump, p_color)
                eval = minimax(om, ok, nm, nk, depth - 1, -beta, -alpha, False, opp_c)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha: break
            return max_eval
        else:
            min_eval = float('inf')
            for move in moves:
                nm, nk, om, ok = simulate_move(m_men, m_kings, o_men, o_kings, move, is_jump, p_color)
                eval = minimax(om, ok, nm, nk, depth - 1, -beta, -alpha, True, opp_c)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha: break
            return min_eval

    # Root Level
    best_move = None
    best_val = -float('inf')
    legal_moves, is_jump = get_moves(my_men, my_kings, opp_men, opp_kings, color)
    
    if not legal_moves: return None
    if len(legal_moves) == 1: return legal_moves[0]

    opp_color = 'b' if color == 'w' else 'w'
    for move in legal_moves:
        nm, nk, om, ok = simulate_move(my_men, my_kings, opp_men, opp_kings, move, is_jump, color)
        val = -minimax(om, ok, nm, nk, 4, -float('inf'), float('inf'), False, opp_color)
        if val > best_val:
            best_val = val
            best_move = move
            
    return best_move or legal_moves[0]
