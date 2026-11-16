
def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    PIECE_VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}
    
    my_color = 'w' if to_play == 'white' else 'b'
    opp_color = 'b' if my_color == 'w' else 'w'
    
    # Check for checkmate moves first
    for move in legal_moves:
        if '#' in move:
            return (move, memory)
    
    def get_piece_at(sq):
        return pieces.get(sq)
    
    def parse_destination(move):
        """Extract destination square from move string."""
        clean = move.replace('+', '').replace('#', '').replace('x', '')
        # Handle castling
        if move == 'O-O':
            return 'g1' if my_color == 'w' else 'g8'
        if move == 'O-O-O':
            return 'c1' if my_color == 'w' else 'c8'
        # Handle promotion
        if '=' in clean:
            clean = clean.split('=')[0]
        # Destination is last 2 chars
        if len(clean) >= 2:
            return clean[-2:]
        return None
    
    def get_moving_piece_type(move):
        """Determine what piece type is moving."""
        if move.startswith('O-O'):
            return 'K'
        first_char = move[0]
        if first_char in 'KQRBN':
            return first_char
        return 'P'  # Pawn moves start with file letter or destination
    
    def score_move(move):
        score = 0
        dest = parse_destination(move)
        piece_type = get_moving_piece_type(move)
        
        # Checks are good (forcing)
        if '+' in move:
            score += 50
        
        # Captures - use MVV-LVA
        if 'x' in move:
            # Find what we're capturing
            captured_piece = get_piece_at(dest)
            if captured_piece:
                victim_value = PIECE_VALUES.get(captured_piece[1], 0)
                attacker_value = PIECE_VALUES.get(piece_type, 0)
                # MVV-LVA: prefer capturing high value with low value
                score += victim_value + (1000 - attacker_value) // 10
        
        # Promotions
        if '=' in move:
            if '=Q' in move:
                score += 800
            elif '=R' in move:
                score += 400
            elif '=B' in move or '=N' in move:
                score += 300
        
        # Castling is good for king safety
        if move.startswith('O-O'):
            score += 60
        
        # Center control
        if dest in ['d4', 'd5', 'e4', 'e5']:
            score += 30
        elif dest in ['c3', 'c4', 'c5', 'c6', 'd3', 'd6', 'e3', 'e6', 'f3', 'f4', 'f5', 'f6']:
            score += 15
        
        # Development bonus for knights and bishops
        if piece_type in ['N', 'B']:
            # Bonus for developing from back rank
            score += 10
        
        # Slight randomness to avoid predictability
        import random
        score += random.random() * 5
        
        return score
    
    # Score all moves and pick the best
    best_move = legal_moves[0]
    best_score = -float('inf')
    
    for move in legal_moves:
        s = score_move(move)
        if s > best_score:
            best_score = s
            best_move = move
    
    return (best_move, memory)
