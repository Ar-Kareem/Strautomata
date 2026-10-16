
def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    if not legal_moves:
        return ""
    
    # Piece values for evaluation
    piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 100}
    
    # Central squares bonus
    center_squares = {'e4', 'e5', 'd4', 'd5'}
    extended_center = {'c3', 'c4', 'c5', 'c6', 'd3', 'd6', 'e3', 'e6', 'f3', 'f4', 'f5', 'f6'}
    
    my_color = 'w' if to_play == 'white' else 'b'
    opp_color = 'b' if my_color == 'w' else 'w'
    
    def get_target_square(move: str) -> str:
        """Extract the destination square from a move."""
        # Remove check/mate symbols
        clean_move = move.rstrip('+#')
        
        # Handle castling
        if clean_move in ('O-O', 'O-O-O'):
            return ''
        
        # Handle promotion
        if '=' in clean_move:
            clean_move = clean_move.split('=')[0]
        
        # Last two characters should be the target square
        if len(clean_move) >= 2:
            target = clean_move[-2:]
            if target[0] in 'abcdefgh' and target[1] in '12345678':
                return target
        return ''
    
    def score_move(move: str) -> float:
        score = 0.0
        
        # Checkmate is the best
        if '#' in move:
            return 100000
        
        # Check is good
        if '+' in move:
            score += 50
        
        # Captures
        if 'x' in move:
            target = get_target_square(move)
            if target and target in pieces:
                captured_piece = pieces[target]
                if captured_piece[0] == opp_color:
                    captured_type = captured_piece[1]
                    score += piece_values.get(captured_type, 0) * 100
            else:
                # En passant or couldn't identify - still good
                score += 100
        
        # Promotions
        if '=' in move:
            if '=Q' in move:
                score += 800
            elif '=R' in move:
                score += 400
            elif '=B' in move or '=N' in move:
                score += 250
        
        # Castling is good for king safety
        if move in ('O-O', 'O-O-O'):
            score += 60
        
        # Center control
        target = get_target_square(move)
        if target:
            if target in center_squares:
                score += 15
            elif target in extended_center:
                score += 8
        
        # Prefer developing knights and bishops early
        if move[0] == 'N':
            score += 5
        elif move[0] == 'B':
            score += 4
        
        # Slight penalty for moving king (unless castling)
        if move[0] == 'K' and move not in ('O-O', 'O-O-O'):
            score -= 10
        
        # Prefer pawn moves in opening (control center)
        if move[0] in 'abcdefgh':
            if target in center_squares:
                score += 10
        
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
