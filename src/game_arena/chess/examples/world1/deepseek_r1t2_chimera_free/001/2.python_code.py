
def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    central_squares = {'d4', 'd5', 'e4', 'e5', 'c3', 'c6', 'd3', 'd6', 'e3', 'e6', 'f3', 'f6', 'c4', 'c5', 'f4', 'f5'}
    
    def piece_value(p_type: str) -> int:
        return {'Q': 9, 'R': 5, 'B': 3, 'N': 3, 'P': 1, 'K': 0}.get(p_type, 0)
    
    def get_destination(move_str: str) -> str:
        move = move_str.rstrip('+#')
        if '=' in move:
            eq_idx = move.index('=')
            return move[eq_idx-2:eq_idx]
        return move[-2:]
    
    opponent_color = 'b' if to_play == 'white' else 'w'
    scores = []
    
    for move in legal_moves:
        score = 0
        # Checkmate detection
        if move.endswith('#'):
            score += 1000
        # Check detection
        elif move.endswith('+'):
            score += 50
        # Promotion evaluation
        if '=' in move:
            promo_piece = move.split('=')[1][0]
            score += (piece_value(promo_piece) - 1) * 100
        # Capture evaluation
        if 'x' in move:
            dest = get_destination(move)
            if dest in pieces:
                target_piece = pieces[dest]
                if target_piece[0] == opponent_color:
                    score += piece_value(target_piece[1]) * 100
        # Castling bonus
        if move in ['O-O', 'O-O-O']:
            score += 40
        # Central square control bonus
        dest_sq = get_destination(move)
        if dest_sq in central_squares:
            score += 10
        scores.append(score)
        
    max_score = max(scores)
    return legal_moves[scores.index(max_score)]
