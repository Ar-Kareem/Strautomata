
def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    if not legal_moves:
        return ""
    
    # Piece values
    PIECE_VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}
    
    my_color = 'w' if to_play == 'white' else 'b'
    opp_color = 'b' if my_color == 'w' else 'w'
    
    # Check for checkmate immediately
    for move in legal_moves:
        if '#' in move:
            return move
    
    def parse_move(move, pieces, my_color):
        """Parse a move and return (from_sq, to_sq, promotion, is_capture, is_castle)"""
        clean = move.replace('+', '').replace('#', '')
        
        # Castling
        if clean == 'O-O':
            rank = '1' if my_color == 'w' else '8'
            return (f'e{rank}', f'g{rank}', None, False, True)
        if clean == 'O-O-O':
            rank = '1' if my_color == 'w' else '8'
            return (f'e{rank}', f'c{rank}', None, False, True)
        
        is_capture = 'x' in clean
        clean = clean.replace('x', '')
        
        promotion = None
        if '=' in clean:
            idx = clean.index('=')
            promotion = clean[idx+1]
            clean = clean[:idx]
        
        # Destination is last 2 chars
        to_sq = clean[-2:]
        rest = clean[:-2]
        
        if not rest:  # Pawn move
            piece_type = 'P'
            disambig = ''
        elif rest[0].isupper():
            piece_type = rest[0]
            disambig = rest[1:]
        else:  # Pawn capture with file
            piece_type = 'P'
            disambig = rest
        
        # Find source square
        from_sq = None
        for sq, pc in pieces.items():
            if pc[0] == my_color and pc[1] == piece_type:
                if disambig:
                    if len(disambig) == 2:
                        if sq != disambig:
                            continue
                    elif disambig.isdigit():
                        if sq[1] != disambig:
                            continue
                    else:
                        if sq[0] != disambig:
                            continue
                from_sq = sq
                break
        
        if from_sq is None:
            for sq, pc in pieces.items():
                if pc[0] == my_color and pc[1] == piece_type:
                    from_sq = sq
                    break
        
        return (from_sq, to_sq, promotion, is_capture, False)
    
    def evaluate_position(pieces, my_color):
        score = 0
        opp = 'b' if my_color == 'w' else 'w'
        
        center_squares = {'d4', 'd5', 'e4', 'e5'}
        extended_center = {'c3', 'c4', 'c5', 'c6', 'd3', 'd6', 'e3', 'e6', 'f3', 'f4', 'f5', 'f6'}
        
        for sq, pc in pieces.items():
            val = PIECE_VALUES.get(pc[1], 0)
            if pc[0] == my_color:
                score += val
                if sq in center_squares:
                    score += 10
                elif sq in extended_center:
                    score += 5
            else:
                score -= val
                if sq in center_squares:
                    score -= 10
                elif sq in extended_center:
                    score -= 5
        
        return score
    
    def score_move(move):
        score = 0
        
        # Big bonus for checks
        if '+' in move:
            score += 50
        
        # Castling bonus
        if 'O-O' in move:
            score += 60
        
        parsed = parse_move(move, pieces, my_color)
        from_sq, to_sq, promotion, is_capture, is_castle = parsed
        
        # Capture scoring
        if is_capture and to_sq in pieces:
            captured = pieces[to_sq]
            score += PIECE_VALUES.get(captured[1], 0)
            if from_sq and from_sq in pieces:
                attacker = pieces[from_sq]
                score -= PIECE_VALUES.get(attacker[1], 0) // 10  # Small penalty for using valuable pieces
        
        # Promotion
        if promotion:
            score += PIECE_VALUES.get(promotion, 0) - 100
        
        # Center control
        if to_sq in {'d4', 'd5', 'e4', 'e5'}:
            score += 15
        elif to_sq in {'c3', 'c4', 'c5', 'c6', 'd3', 'd6', 'e3', 'e6', 'f3', 'f4', 'f5', 'f6'}:
            score += 8
        
        # Simulate the move
        new_pieces = dict(pieces)
        if is_castle:
            rank = '1' if my_color == 'w' else '8'
            if 'O-O-O' in move:
                new_pieces[f'c{rank}'] = new_pieces.pop(f'e{rank}')
                new_pieces[f'd{rank}'] = new_pieces.pop(f'a{rank}')
            else:
                new_pieces[f'g{rank}'] = new_pieces.pop(f'e{rank}')
                new_pieces[f'f{rank}'] = new_pieces.pop(f'h{rank}')
        elif from_sq and from_sq in new_pieces:
            piece = new_pieces.pop(from_sq)
            if promotion:
                piece = my_color + promotion
            new_pieces[to_sq] = piece
            
            # En passant capture
            if piece[1] == 'P' and is_capture and to_sq not in pieces:
                ep_sq = to_sq[0] + from_sq[1]
                if ep_sq in new_pieces:
                    del new_pieces[ep_sq]
        
        pos_score = evaluate_position(new_pieces, my_color)
        score += pos_score / 10
        
        return score
    
    # Score all moves and pick best
    best_move = legal_moves[0]
    best_score = float('-inf')
    
    for move in legal_moves:
        try:
            s = score_move(move)
            if s > best_score:
                best_score = s
                best_move = move
        except:
            continue
    
    return best_move
