
import time

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    start_time = time.time()
    
    me_set = set(me)
    opp_set = set(opp)
    
    if color == 'w':
        direction = 1
        goal_row = 7
        opp_color = 'b'
    else:
        direction = -1
        goal_row = 0
        opp_color = 'w'

    def get_opp_color(c):
        return 'b' if c == 'w' else 'w'

    def get_moves(pieces, opp_pieces, player_color):
        moves = []
        d = 1 if player_color == 'w' else -1
        p_goal = 7 if player_color == 'w' else 0
        
        p_set = set(pieces)
        o_set = set(opp_pieces)
        occupied = p_set | o_set
        
        for r, c in pieces:
            # Straight move
            nr, nc = r + d, c
            if 0 <= nr < 8 and 0 <= nc < 8:
                if (nr, nc) not in occupied:
                    moves.append(((r, c), (nr, nc)))
            
            # Diagonal moves
            for dc in [-1, 1]:
                nc = c + dc
                nr = r + d
                if 0 <= nr < 8 and 0 <= nc < 8:
                    target = (nr, nc)
                    if target in o_set:
                        moves.append(((r, c), (nr, nc)))
                    elif target not in occupied:
                        moves.append(((r, c), (nr, nc)))
        
        # Order moves: Wins > Captures > Forward
        def move_score(move):
            f, t = move
            if t[0] == p_goal:
                return -10000
            if t in o_set:
                return -1000
            # Priorize forward progress
            dist = abs(f[0] - p_goal) - abs(t[0] - p_goal)
            return -dist * 10
            
        moves.sort(key=move_score)
        return moves

    def evaluate(my_pieces, opponent_pieces, my_color):
        score = (len(my_pieces) - len(opponent_pieces)) * 10000
        
        my_goal = 7 if my_color == 'w' else 0
        opp_goal = 0 if my_color == 'w' else 7
        
        for r, c in my_pieces:
            dist = abs(my_goal - r)
            score -= dist * 100
            if 2 <= c <= 5:
                score += 10
                
        for r, c in opponent_pieces:
            dist = abs(opp_goal - r)
            score += dist * 100
            
        return score

    def minimax(my_p, opp_p, turn, depth, alpha, beta, root_color):
        my_g = 7 if root_color == 'w' else 0
        opp_g = 0 if root_color == 'w' else 7
        
        # Check for wins
        for r, c in my_p:
            if r == my_g: return 100000 + depth
        for r, c in opp_p:
            if r == opp_g: return -100000 - depth
            
        if depth == 0:
            return evaluate(my_p, opp_p, root_color)
            
        is_max = (turn == root_color)
        current_pieces = my_p if is_max else opp_p
        opponent_pieces = opp_p if is_max else my_p
        
        moves = get_moves(current_pieces, opponent_pieces, turn)
        
        if not moves:
            return -100000 if is_max else 100000
            
        if is_max:
            max_eval = float('-inf')
            for from_pos, to_pos in moves:
                n_my = set(my_p)
                n_opp = set(opp_p)
                
                n_my.remove(from_pos)
                n_my.add(to_pos)
                if to_pos in n_opp:
                    n_opp.remove(to_pos)
                
                eval_val = minimax(n_my, n_opp, get_opp_color(turn), depth - 1, alpha, beta, root_color)
                max_eval = max(max_eval, eval_val)
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for from_pos, to_pos in moves:
                n_my = set(my_p)
                n_opp = set(opp_p)
                
                n_opp.remove(from_pos)
                n_opp.add(to_pos)
                if to_pos in n_my:
                    n_my.remove(to_pos)
                    
                eval_val = minimax(n_my, n_opp, get_opp_color(turn), depth - 1, alpha, beta, root_color)
                min_eval = min(min_eval, eval_val)
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break
            return min_eval

    legal_moves = get_moves(me_set, opp_set, color)
    
    if not legal_moves:
        return ((0,0), (0,0))
        
    # Check for immediate win
    for move in legal_moves:
        if move[1][0] == goal_row:
            return move
            
    best_move = legal_moves[0]
    max_time = 0.9
    
    # Iterative Deepening
    for depth in range(1, 7):
        current_best_move = None
        max_eval = float('-inf')
        
        for move in legal_moves:
            if time.time() - start_time > max_time:
                break
                
            from_pos, to_pos = move
            
            new_me = set(me_set)
            new_opp = set(opp_set)
            
            new_me.remove(from_pos)
            new_me.add(to_pos)
            if to_pos in new_opp:
                new_opp.remove(to_pos)
                
            score = minimax(new_me, new_opp, opp_color, depth - 1, float('-inf'), float('inf'), color)
            
            if score > max_eval:
                max_eval = score
                current_best_move = move
        
        if current_best_move:
            best_move = current_best_move
            
        if max_eval >= 100000:
            break
            
        if time.time() - start_time > max_time:
            break
            
    return best_move
