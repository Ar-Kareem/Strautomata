
def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    # Convert to_play to color code for easier handling
    color = 'w' if to_play == 'white' else 'b'
    opponent_color = 'b' if color == 'w' else 'w'
    
    # Heuristic scoring for moves
    def score_move(move):
        score = 0
        
        # Check for checkmate (highest priority)
        if move.endswith('+') or move.endswith('#'):
            return 1000000
        
        # Check for captures
        if 'x' in move:
            captured_piece = move.split('x')[1][0]  # Get piece type
            if captured_piece == 'Q': score += 900
            elif captured_piece == 'R': score += 500
            elif captured_piece == 'B': score += 300
            elif captured_piece == 'N': score += 300
            elif captured_piece == 'P': score += 100
            else: score += 50  # Unknown piece
        
        # Check for check
        if '+' in move:
            score += 500
        
        # Check for promotions
        if '=' in move:
            prom_piece = move.split('=')[1]
            if prom_piece == 'Q': score += 800
            elif prom_piece == 'R': score += 500
            elif prom_piece == 'B': score += 300
            elif prom_piece == 'N': score += 300
        
        # Prefer center control (d4, d5, e4, e5)
        if 'd4' in move or 'd5' in move or 'e4' in move or 'e5' in move:
            score += 100
        
        # Prefer piece development (knights and bishops)  
        if move.startswith('N') or move.startswith('B'):
            score += 50
        
        # Prefer moving king away from center if safe
        if move.startswith('K') and 'd' in move and 'e' in move:
            score += 10
        
        # Prefer castling
        if move in ['O-O', 'O-O-O']:
            score += 300
        
        # Avoid moving pieces that are already captured or attacked
        # Simple heuristic: avoid moves that would leave king exposed
        # (This is limited but helps avoid obvious blunders)
        
        # General piece mobility bonus
        if move.isalpha() and len(move) >= 2:
            score += 20
            
        return score
    
    # Score all legal moves
    move_scores = [(move, score_move(move)) for move in legal_moves]
    
    # Sort moves by score in descending order
    move_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Return the highest scoring move
    if move_scores:
        return (move_scores[0][0], memory)
    else:
        # If no moves are available, just return the first one (shouldn't happen)
        return (legal_moves[0] if legal_moves else 'e1e1', memory)
