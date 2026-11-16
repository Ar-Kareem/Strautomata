
def policy(pieces, to_play, legal_moves, memory):
    scores = {}
    promo_values = {
        'Q': 900,
        'R': 500,
        'B': 300,
        'N': 300
    }
    
    for move in legal_moves:
        if move.endswith('#'):
            score = 1000000
        elif '=' in move:
            promo_part = move.split('=')[1]
            promo_piece = promo_part[0] if promo_part else None
            promo_value = promo_values.get(promo_piece, 0)
            if 'x' in move:
                score = 1000 + promo_value
            else:
                score = promo_value
        elif 'x' in move:
            score = 1000
        elif move in ['O-O', 'O-O-O']:
            score = 500
        elif move.startswith('K'):
            score = 1
        else:
            score = 10
        
        scores[move] = score
    
    best_move = max(legal_moves, key=lambda m: scores[m])
    return (best_move, memory)
