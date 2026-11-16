
def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    if not legal_moves:
        return ""
    
    # Piece values
    PIECE_VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}
    
    my_color = 'w' if to_play == 'white' else 'b'
    opp_color = 'b' if my_color == 'w' else 'w'
    
    # Check for checkmate
    for move in legal_moves:
        if '#' in move:
            return move
    
    def get_piece_at(square, board):
        return board.get(square, None)
    
    def parse_move(move):
        """Parse move to get destination square and other info"""
        clean = move.replace('+', '').replace('#', '')
        
        # Castling
        if clean == 'O-O' or clean == 'O-O-O':
            return {'type': 'castle', 'move': move}
        
        # Promotion
        promotion = None
        if '=' in clean:
            idx = clean.index('=')
            promotion = clean[idx+1]
            clean = clean[:idx]
        
        # Capture
        is_capture = 'x' in move
        clean = clean.replace('x', '')
        
        # Destination is last 2 chars
        dest = clean[-2:]
        
        # Piece type
        if clean[0] in 'KQRBN':
            piece_type = clean[0]
        else:
            piece_type = 'P'
        
        return {
            'dest': dest,
            'piece': piece_type,
            'capture': is_capture,
            'promotion': promotion,
            'move': move
        }
    
    def score_move(move):
        score = 0
        parsed = parse_move(move)
        
        # Check bonus
        if '+' in move:
            score += 50
        
        # Castling bonus
        if parsed.get('type') == 'castle':
            return score + 60
        
        dest = parsed.get('dest', '')
        
        # Capture scoring (MVV-LVA style)
        if parsed['capture'] and dest:
            victim = get_piece_at(dest, pieces)
            if victim:
                victim_val = PIECE_VALUES.get(victim[1], 0)
                attacker_val = PIECE_VALUES.get(parsed['piece'], 0)
                # MVV-LVA: prioritize capturing high value with low value
                score += victim_val * 10 - attacker_val
        
        # Promotion (queen promotion is best)
        if parsed.get('promotion'):
            promo_vals = {'Q': 800, 'R': 400, 'B': 250, 'N': 250}
            score += promo_vals.get(parsed['promotion'], 0)
        
        # Center control bonus
        center_squares = {'e4', 'e5', 'd4', 'd5'}
        extended_center = {'c3', 'c4', 'c5', 'c6', 'd3', 'd6', 'e3', 'e6', 'f3', 'f4', 'f5', 'f6'}
        
        if dest in center_squares:
            score += 30
        elif dest in extended_center:
            score += 15
        
        # Development bonus (minor pieces off back rank)
        if parsed['piece'] in 'NB':
            back_rank = '1' if my_color == 'w' else '8'
            if dest and dest[1] != back_rank:
                score += 20
        
        # Avoid moving king early (small penalty) unless castling
        if parsed['piece'] == 'K':
            score -= 10
        
        return score
    
    # Score all moves and pick the best
    best_move = legal_moves[0]
    best_score = float('-inf')
    
    for move in legal_moves:
        s = score_move(move)
        if s > best_score:
            best_score = s
            best_move = move
    
    return best_move
