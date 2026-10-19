
import collections

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    # Directions based on color
    # white: moves row index +1
    # black: moves row index -1
    direction = 1 if color == 'w' else -1
    home_row = 0 if color == 'w' else 7
    goal_row = 7 if color == 'w' else 0
    opp_color = 'b' if color == 'w' else 'w'

    def get_legal_moves(current_me, current_opp, is_white):
        moves = []
        d = 1 if is_white else -1
        g_row = 7 if is_white else 0
        opp_set = set(current_opp)
        me_set = set(current_me)
        
        for r, c in current_me:
            # Straight move
            nr, nc = r + d, c
            if 0 <= nr <= 7 and (nr, nc) not in me_set and (nr, nc) not in opp_set:
                moves.append(((r, c), (nr, nc)))
            
            # Diagonal moves
            for dc in [-1, 1]:
                nr, nc = r + d, c + dc
                if 0 <= nr <= 7 and 0 <= nc <= 7:
                    # Can move to diagonal if empty or contains opponent (capture)
                    if (nr, nc) not in me_set:
                        moves.append(((r, c), (nr, nc)))
        return moves

    def evaluate(p_me, p_opp, p_color):
        # material + distance to goal
        score = 0
        is_w = (p_color == 'w')
        m_goal = 7 if is_w else 0
        o_goal = 0 if is_w else 7
        
        # Win condition
        for r, c in p_me:
            if r == m_goal: return 10000
        for r, c in p_opp:
            if r == o_goal: return -10000
            
        score += len(p_me) * 100
        score -= len(p_opp) * 100
        
        for r, c in p_me:
            dist = abs(r - (0 if is_w else 7))
            score += dist * 10
            # Defense bonus
            if r == (0 if is_w else 7): score += 5
            
        for r, c in p_opp:
            dist = abs(r - (7 if is_w else 0))
            score -= dist * 10
            if r == (7 if is_w else 0): score -= 5
            
        return score

    def move_piece(pieces, target, is_capture, opp_pieces=None):
        new_me = [p for p in pieces if p != target[0]]
        new_me.append(target[1])
        if is_capture:
            new_opp = [p for p in opp_pieces if p != target[1]]
            return new_me, new_opp
        return new_me, opp_pieces

    # Simple Alpha-Beta Minimax
    def minimax(p_me, p_opp, depth, alpha, beta, maximizing, p_col):
        if depth == 0:
            return evaluate(p_me, p_opp, p_col if maximizing else ('b' if p_col == 'w' else 'w')), None
        
        legal = get_legal_moves(p_me, p_opp, p_col == 'w')
        if not legal:
            return (-9999 if maximizing else 9999), None

        # Move ordering: prioritize captures and goal proximity
        legal.sort(key=lambda x: abs(x[1][0] - (7 if p_col == 'w' else 0)))

        best_move = legal[0]
        if maximizing:
            max_eval = -float('inf')
            for move in legal:
                is_cap = move[1] in p_opp
                nm, no = move_piece(p_me, move, is_cap, p_opp)
                # Check win
                if move[1][0] == (7 if p_col == 'w' else 0):
                    return 10000, move
                
                eval_val, _ = minimax(no, nm, depth - 1, -beta, -alpha, False, 'b' if p_col == 'w' else 'w')
                eval_val = -eval_val
                if eval_val > max_eval:
                    max_eval = eval_val
                    best_move = move
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            # This branch logic is handled by the negation in the recursive call
            return 0, None

    # Check for immediate win
    legal_moves = get_legal_moves(me, opp, color == 'w')
    for m in legal_moves:
        if m[1][0] == goal_row:
            return m
            
    # Search
    _, best = minimax(me, opp, 3, -float('inf'), float('inf'), True, color)
    return best if best else legal_moves[0]
