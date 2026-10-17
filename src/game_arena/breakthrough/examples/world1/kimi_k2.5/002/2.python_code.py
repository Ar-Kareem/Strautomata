
def policy(me, opp, color):
    # Convert to sets for O(1) operations
    me_set = set(me)
    opp_set = set(opp)
    
    # Determine directions and target row
    dr = -1 if color == 'b' else 1
    target_row = 0 if color == 'b' else 7
    opp_color = 'w' if color == 'b' else 'b'
    
    def generate_moves(cur_me, cur_opp, cur_color):
        moves = []
        cur_dr = -1 if cur_color == 'b' else 1
        for r, c in cur_me:
            # Forward move
            nr, nc = r + cur_dr, c
            if 0 <= nr < 8 and (nr, nc) not in cur_me and (nr, nc) not in cur_opp:
                moves.append(((r, c), (nr, nc)))
            # Left diagonal
            nr, nc = r + cur_dr, c - 1
            if 0 <= nr < 8 and 0 <= nc < 8:
                if (nr, nc) in cur_opp:
                    moves.append(((r, c), (nr, nc)))
                elif (nr, nc) not in cur_me:
                    moves.append(((r, c), (nr, nc)))
            # Right diagonal
            nr, nc = r + cur_dr, c + 1
            if 0 <= nr < 8 and 0 <= nc < 8:
                if (nr, nc) in cur_opp:
                    moves.append(((r, c), (nr, nc)))
                elif (nr, nc) not in cur_me:
                    moves.append(((r, c), (nr, nc)))
        return moves
    
    def apply_move(move, cur_me, cur_opp):
        fr, to = move
        new_me = set(cur_me)
        new_opp = set(cur_opp)
        new_me.remove(fr)
        new_me.add(to)
        new_opp.discard(to)
        return new_me, new_opp
    
    def evaluate(cur_me, cur_opp, cur_color):
        # Material
        score = (len(cur_me) - len(cur_opp)) * 100
        
        # Advancement and position
        my_val = 0
        opp_val = 0
        
        if cur_color == 'b':
            for r, c in cur_me:
                my_val += (7 - r) * 10
                if 2 <= c <= 5:
                    my_val += 1
            for r, c in cur_opp:
                opp_val += r * 10
                if 2 <= c <= 5:
                    opp_val += 1
        else:
            for r, c in cur_me:
                my_val += r * 10
                if 2 <= c <= 5:
                    my_val += 1
            for r, c in cur_opp:
                opp_val += (7 - r) * 10
                if 2 <= c <= 5:
                    opp_val += 1
        
        return score + my_val - opp_val
    
    def negamax(cur_me, cur_opp, cur_color, depth, alpha, beta):
        if depth == 0:
            return evaluate(cur_me, cur_opp, cur_color)
        
        moves = generate_moves(cur_me, cur_opp, cur_color)
        if not moves:
            return -10000
        
        cur_target = 0 if cur_color == 'b' else 7
        next_color = 'w' if cur_color == 'b' else 'b'
        
        # Move ordering: prioritize captures and advanced moves
        def priority(m):
            to = m[1]
            if to in cur_opp:
                return 1000 + (7 - to[0] if cur_color == 'b' else to[0])
            return 100 + (7 - to[0] if cur_color == 'b' else to[0])
        
        moves.sort(key=priority, reverse=True)
        
        for m in moves:
            # Check immediate win
            if m[1][0] == cur_target:
                return 10000
            
            new_me, new_opp = apply_move(m, cur_me, cur_opp)
            
            # Check win by capture
            if not new_opp:
                return 10000
            
            val = -negamax(new_opp, new_me, next_color, depth - 1, -beta, -alpha)
            
            if val > alpha:
                alpha = val
            if alpha >= beta:
                break
        
        return alpha
    
    # Get all legal moves
    moves = generate_moves(me_set, opp_set, color)
    
    if not moves:
        # Should not happen in valid game, but return first piece as fallback
        # (This line is theoretically unreachable in a valid game state)
        return ((0, 0), (0, 0))
    
    # Check for immediate winning move (reach home row)
    for m in moves:
        if m[1][0] == target_row:
            return m
    
    # Determine search depth based on piece count
    total_pieces = len(me_set) + len(opp_set)
    if total_pieces <= 6:
        depth = 5
    elif total_pieces <= 10:
        depth = 4
    else:
        depth = 3
    
    best_move = moves[0]
    best_val = -float('inf')
    
    # Sort initial moves
    def init_priority(m):
        to = m[1]
        if to in opp_set:
            return 1000 + (7 - to[0] if color == 'b' else to[0])
        return 100 + (7 - to[0] if color == 'b' else to[0])
    
    moves.sort(key=init_priority, reverse=True)
    
    for m in moves:
        new_me, new_opp = apply_move(m, me_set, opp_set)
        
        # Immediate win by capture of last piece
        if not new_opp:
            return m
        
        val = -negamax(new_opp, new_me, opp_color, depth - 1, -float('inf'), float('inf'))
        
        if val > best_val:
            best_val = val
            best_move = m
    
    return best_move
