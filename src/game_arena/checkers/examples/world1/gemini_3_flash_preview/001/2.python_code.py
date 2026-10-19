
import time

def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple:
    start_time = time.time()
    
    is_white = (color == 'w')
    
    def get_legal_moves(player_men, player_kings, enemy_men, enemy_kings, is_white_turn):
        jumps = []
        moves = []
        
        direction = 1 if is_white_turn else -1
        p_pieces = [(p, False) for p in player_men] + [(p, True) for p in player_kings]
        enemies = set(enemy_men) | set(enemy_kings)
        occupied = set(player_men) | set(player_kings) | enemies
        
        for (r, c), is_king in p_pieces:
            # Check for jumps
            dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)] if is_king else [(direction, -1), (direction, 1)]
            for dr, dc in dirs:
                mid = (r + dr, c + dc)
                end = (r + 2 * dr, c + 2 * dc)
                if 0 <= end[0] <= 7 and 0 <= end[1] <= 7:
                    if mid in enemies and end not in occupied:
                        jumps.append(((r, c), end))
            
            # Check for simple moves (only if no jumps found globally)
            if not jumps:
                for dr, dc in dirs:
                    end = (r + dr, c + dc)
                    if 0 <= end[0] <= 7 and 0 <= end[1] <= 7:
                        if end not in occupied:
                            moves.append(((r, c), end))
                            
        return jumps if jumps else moves

    def evaluate(m_men, m_kings, o_men, o_kings):
        # Material and positional scoring
        score = 0
        score += len(m_men) * 100
        score += len(m_kings) * 160
        score -= len(o_men) * 100
        score -= len(o_kings) * 160
        
        # Simple positional bonuses
        for r, c in m_men:
            dist = r if is_white else (7 - r)
            score += dist * 5 # Encourage moving forward
        return score

    def get_state_after_move(move, m_men, m_kings, o_men, o_kings, is_white_turn):
        start, end = move
        new_m_men = set(m_men)
        new_m_kings = set(m_kings)
        new_o_men = set(o_men)
        new_o_kings = set(o_kings)
        
        is_king = start in new_m_kings
        if is_king:
            new_m_kings.remove(start)
            new_m_kings.add(end)
        else:
            new_m_men.remove(start)
            if (is_white_turn and end[0] == 7) or (not is_white_turn and end[0] == 0):
                new_m_kings.add(end)
            else:
                new_m_men.add(end)
        
        # Handle capture
        if abs(start[0] - end[0]) == 2:
            mid = ((start[0] + end[0]) // 2, (start[1] + end[1]) // 2)
            if mid in new_o_men: new_o_men.remove(mid)
            elif mid in new_o_kings: new_o_kings.remove(mid)
            
        return list(new_m_men), list(new_m_kings), list(new_o_men), list(new_o_kings)

    def minimax(m_men, m_kings, o_men, o_kings, depth, alpha, beta, maximizing, is_white_turn):
        if depth == 0:
            return evaluate(m_men, m_kings, o_men, o_kings) if maximizing else -evaluate(o_men, o_kings, m_men, m_kings)
        
        moves = get_legal_moves(m_men, m_kings, o_men, o_kings, is_white_turn)
        if not moves:
            return -10000 # Loss
            
        if maximizing:
            max_eval = -float('inf')
            for move in moves:
                nm, nk, om, ok = get_state_after_move(move, m_men, m_kings, o_men, o_kings, is_white_turn)
                eval = minimax(om, ok, nm, nk, depth - 1, -beta, -alpha, False, not is_white_turn)
                max_eval = max(max_eval, -eval)
                alpha = max(alpha, -eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            # Symmetrical because we swap perspectives in call
            return -1

    # Main search entry
    best_move = None
    legal_moves = get_legal_moves(my_men, my_kings, opp_men, opp_kings, is_white)
    
    if len(legal_moves) == 1:
        return legal_moves[0]

    max_val = -float('inf')
    # Search depth depends on number of moves to ensure stability within 1s
    depth = 4 if len(legal_moves) > 5 else 6
    
    for move in legal_moves:
        nm, nk, om, ok = get_state_after_move(move, my_men, my_kings, opp_men, opp_kings, is_white)
        # Flip perspective: opponent is maximizing their score
        val = -minimax(om, ok, nm, nk, depth, -float('inf'), float('inf'), True, not is_white)
        if val > max_val:
            max_val = val
            best_move = move
            
    return best_move if best_move else legal_moves[0]
