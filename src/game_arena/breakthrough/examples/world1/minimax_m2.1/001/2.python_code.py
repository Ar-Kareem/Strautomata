
def policy(me, opp, color):
    def generate_moves(pieces, opponent_pieces, color):
        moves = []
        if color == 'b':
            delta = -1
        else:
            delta = 1
        
        for (r, c) in pieces:
            # Straight forward
            new_r = r + delta
            if 0 <= new_r < 8:
                if (new_r, c) not in pieces and (new_r, c) not in opponent_pieces:
                    moves.append(((r, c), (new_r, c)))
            
            # Diagonally forward
            for dc in [-1, 1]:
                new_c = c + dc
                if 0 <= new_c < 8:
                    # Non-capturing move
                    if (new_r, new_c) not in pieces and (new_r, new_c) not in opponent_pieces:
                        moves.append(((r, c), (new_r, new_c)))
                    # Capturing move
                    elif (new_r, new_c) in opponent_pieces:
                        moves.append(((r, c), (new_r, new_c)))
        
        return moves

    def static_evaluation(me, opp, our_color):
        # Check if we have won
        for (r, c) in me:
            if our_color == 'b' and r == 0:
                return 10000
            if our_color == 'w' and r == 7:
                return 10000
        
        # Check if opponent has won
        if our_color == 'b':
            if any(r == 7 for (r, c) in opp):
                return -10000
        else:
            if any(r == 0 for (r, c) in opp):
                return -10000
        
        # Check for captures
        if not opp:
            return 10000
        if not me:
            return -10000
        
        # Calculate advancement scores
        if our_color == 'b':
            our_adv = sum(7 - r for (r, c) in me)
            opp_adv = sum(r for (r, c) in opp)
        else:
            our_adv = sum(r for (r, c) in me)
            opp_adv = sum(7 - r for (r, c) in opp)
        
        piece_diff = (len(me) - len(opp)) * 100
        return our_adv - opp_adv + piece_diff

    our_moves = generate_moves(me, opp, color)
    
    if not our_moves:
        return (me[0], (me[0][0], me[0][1]))
    
    best_move = None
    best_value = -float('inf')
    
    for move in our_moves:
        from_sq, to_sq = move
        new_me = [p for p in me if p != from_sq] + [to_sq]
        new_opp = [p for p in opp]
        
        if to_sq in opp:
            new_opp = [p for p in opp if p != to_sq]
        
        # Check win conditions
        won = False
        if color == 'b' and to_sq[0] == 0:
            won = True
        if color == 'w' and to_sq[0] == 7:
            won = True
        if not new_opp:
            won = True
        
        if won:
            value = 10000
        else:
            opp_color = 'b' if color == 'w' else 'w'
            opp_moves = generate_moves(new_opp, new_me, opp_color)
            
            if not opp_moves:
                value = 10000
            else:
                min_eval = float('inf')
                for opp_move in opp_moves:
                    opp_from, opp_to = opp_move
                    temp_opp = [p for p in new_opp if p != opp_from] + [opp_to]
                    temp_me = new_me[:]
                    
                    if opp_to in new_me:
                        temp_me = [p for p in new_me if p != opp_to]
                    
                    eval_val = static_evaluation(temp_me, temp_opp, color)
                    min_eval = min(min_eval, eval_val)
                
                value = min_eval
        
        if value > best_value:
            best_value = value
            best_move = move
    
    return best_move
