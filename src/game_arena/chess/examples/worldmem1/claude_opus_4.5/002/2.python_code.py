
def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    
    PIECE_VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}
    
    my_color = 'w' if to_play == 'white' else 'b'
    opp_color = 'b' if my_color == 'w' else 'w'
    
    def get_piece_value(piece_type):
        return PIECE_VALUES.get(piece_type.upper(), 0)
    
    def parse_move(move):
        """Extract information from a move string."""
        is_checkmate = '#' in move
        is_check = '+' in move or is_checkmate
        is_capture = 'x' in move
        is_castle = move.startswith('O-O')
        is_promotion = '=' in move
        promotion_piece = None
        if is_promotion:
            promotion_piece = move.split('=')[1][0]
        return {
            'checkmate': is_checkmate,
            'check': is_check,
            'capture': is_capture,
            'castle': is_castle,
            'promotion': is_promotion,
            'promotion_piece': promotion_piece
        }
    
    def get_target_square(move):
        """Extract target square from move."""
        clean = move.replace('+', '').replace('#', '').replace('x', '')
        if '=' in clean:
            clean = clean.split('=')[0]
        if clean.startswith('O-O-O'):
            return 'c1' if my_color == 'w' else 'c8'
        if clean.startswith('O-O'):
            return 'g1' if my_color == 'w' else 'g8'
        if len(clean) >= 2:
            return clean[-2:]
        return None
    
    def score_move(move):
        """Score a move for ordering."""
        info = parse_move(move)
        score = 0
        
        if info['checkmate']:
            return 1000000
        
        if info['check']:
            score += 500
        
        if info['capture']:
            target = get_target_square(move)
            if target and target in pieces:
                captured_piece = pieces[target]
                if captured_piece[0] == opp_color:
                    victim_value = get_piece_value(captured_piece[1])
                    # Determine attacker
                    if move[0].isupper() and move[0] != 'O':
                        attacker_type = move[0]
                    else:
                        attacker_type = 'P'
                    attacker_value = get_piece_value(attacker_type)
                    score += 10000 + victim_value - attacker_value // 10
        
        if info['promotion']:
            promo_val = get_piece_value(info['promotion_piece'])
            score += promo_val + 5000
        
        if info['castle']:
            score += 600
        
        target = get_target_square(move)
        if target:
            file, rank = target[0], target[1]
            # Central control bonus
            if file in 'de' and rank in '45':
                score += 50
            elif file in 'cdef' and rank in '3456':
                score += 25
        
        # Development bonus for knights and bishops
        if move[0] == 'N' or move[0] == 'B':
            score += 30
        
        return score
    
    # Score all moves and pick the best
    best_move = legal_moves[0]
    best_score = -float('inf')
    
    for move in legal_moves:
        score = score_move(move)
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move, memory
