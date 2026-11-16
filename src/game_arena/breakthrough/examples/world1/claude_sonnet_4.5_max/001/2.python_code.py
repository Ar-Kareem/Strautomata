
def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    
    if not me:
        return ((0, 0), (0, 1))
    
    forward = 1 if color == 'w' else -1
    goal_row = 7 if color == 'w' else 0
    opp_goal = 0 if color == 'w' else 7
    
    def get_moves(pieces, opponent_pieces, direction):
        me_set = set(pieces)
        opp_set = set(opponent_pieces)
        all_pieces = me_set | opp_set
        
        moves = []
        for row, col in pieces:
            new_row = row + direction
            if 0 <= new_row <= 7:
                if (new_row, col) not in all_pieces:
                    moves.append(((row, col), (new_row, col)))
                for dc in [-1, 1]:
                    new_col = col + dc
                    if 0 <= new_col <= 7 and (new_row, new_col) not in me_set:
                        moves.append(((row, col), (new_row, new_col)))
        return moves
    
    def order_moves(moves, opp_set, target_row):
        def move_score(move):
            to_pos = move[1]
            score = 0
            if to_pos[0] == target_row:
                score += 100000
            if to_pos in opp_set:
                score += 1000
            score -= abs(to_pos[0] - target_row)
            return -score
        return sorted(moves, key=move_score)
    
    def is_passed(row, col, opp_set, direction, target_row):
        check_row = row + direction
        while 0 <= check_row <= 7 and check_row != target_row + direction:
            for check_col in [col - 1, col, col + 1]:
                if 0 <= check_col <= 7 and (check_row, check_col) in opp_set:
                    return False
            check_row += direction
        return True
    
    def evaluate(my_pieces, opp_pieces):
        if not opp_pieces:
            return 999999
        if not my_pieces:
            return -999999
        
        my_set = set(my_pieces)
        opp_set = set(opp_pieces)
        
        for r, c in my_pieces:
            if r == goal_row:
                return 999999
        for r, c in opp_pieces:
            if r == opp_goal:
                return -999999
        
        score = 0
        score += (len(my_pieces) - len(opp_pieces)) * 200
        
        my_min_dist = 8
        for r, c in my_pieces:
            dist = abs(r - goal_row)
            my_min_dist = min(my_min_dist, dist)
            score += (7 - dist) * 10
            
            if is_passed(r, c, opp_set, forward, goal_row):
                score += 100 + (7 - dist) * 30
        
        opp_min_dist = 8
        for r, c in opp_pieces:
            dist = abs(r - opp_goal)
            opp_min_dist = min(opp_min_dist, dist)
            score -= (7 - dist) * 10
            
            if is_passed(r, c, my_set, -forward, opp_goal):
                score -= 100 + (7 - dist) * 30
        
        score += (8 - my_min_dist) * 50
        score -= (8 - opp_min_dist) * 50
        
        return score
    
    def minimax(my_pieces, opp_pieces, depth, alpha, beta, is_max):
        if depth == 0:
            return evaluate(my_pieces, opp_pieces), None
        
        if is_max:
            moves = get_moves(my_pieces, opp_pieces, forward)
            if not moves:
                return -999999, None
            
            opp_set = set(opp_pieces)
            moves = order_moves(moves, opp_set, goal_row)
            
            max_eval = float('-inf')
            best_move = None
            
            for move in moves:
                from_pos, to_pos = move
                
                if to_pos[0] == goal_row:
                    return 999999, move
                
                new_my = [p for p in my_pieces if p != from_pos] + [to_pos]
                new_opp = [p for p in opp_pieces if p != to_pos]
                
                eval_val, _ = minimax(new_my, new_opp, depth - 1, alpha, beta, False)
                
                if eval_val > max_eval:
                    max_eval = eval_val
                    best_move = move
                
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break
            
            return max_eval, best_move
        else:
            moves = get_moves(opp_pieces, my_pieces, -forward)
            if not moves:
                return 999999, None
            
            my_set = set(my_pieces)
            moves = order_moves(moves, my_set, opp_goal)
            
            min_eval = float('inf')
            
            for move in moves:
                from_pos, to_pos = move
                
                if to_pos[0] == opp_goal:
                    eval_val = -999999
                else:
                    new_opp = [p for p in opp_pieces if p != from_pos] + [to_pos]
                    new_my = [p for p in my_pieces if p != to_pos]
                    eval_val, _ = minimax(new_my, new_opp, depth - 1, alpha, beta, True)
                
                min_eval = min(min_eval, eval_val)
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break
            
            return min_eval, None
    
    total = len(me) + len(opp)
    depth = 2 if total > 24 else 3 if total > 12 else 4
    
    _, best_move = minimax(me, opp, depth, float('-inf'), float('inf'), True)
    
    if best_move is None:
        moves = get_moves(me, opp, forward)
        best_move = moves[0] if moves else ((me[0][0], me[0][1]), (me[0][0] + forward, me[0][1]))
    
    return best_move
