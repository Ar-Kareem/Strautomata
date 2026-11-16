
import re

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    my_color = 'w' if to_play == 'white' else 'b'
    opponent_color = 'b' if my_color == 'w' else 'w'
    
    piece_values = {'Q': 9, 'R': 5, 'B': 3, 'N': 3, 'P': 1, 'K': 0}
    center_squares = {'c3', 'd4', 'e4', 'f3', 'c6', 'd5', 'e5', 'f6'}
    
    scored_moves = []
    
    for move in legal_moves:
        score = 0
        
        # Prioritize castling
        if move in ('O-O', 'O-O-O'):
            score += 3
            scored_moves.append((score, move))
            continue
        
        # Extract destination square
        squares = re.findall(r'[a-h][1-8]', move)
        if not squares:
            scored_moves.append((score, move))
            continue
        dest_square = squares[-1]
        
        # Evaluate captures
        if 'x' in move:
            if dest_square in pieces:
                captured_piece = pieces[dest_square]
                if captured_piece[0] == opponent_color:
                    score += piece_values.get(captured_piece[1], 0)
        
        # Evaluate promotions
        if '=' in move:
            promo_part = move.split('=')[1][0]
            score += piece_values.get(promo_part, 0) - 1  # Pawn promotion value
        
        # Check bonus
        if '+' in move:
            score += 2
        
        # Center control bonus
        if dest_square in center_squares:
            score += 1
        
        scored_moves.append((score, move))
    
    # Select move with highest score, using lex order as tiebreaker
    scored_moves.sort(key=lambda x: (-x[0], x[1]))
    return scored_moves[0][1]
