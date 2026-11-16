
import re

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    opponent_color = 'b' if to_play == 'white' else 'w'
    
    # Define piece values (centipawn-like for scoring)
    piece_values = {'P': 100, 'N': 300, 'B': 300, 'R': 500, 'Q': 900, 'K': 0}
    
    def parse_move(move: str) -> dict:
        """Parse move into dict with keys: dest, capture, promotion, check, mate"""
        result = {'dest': None, 'capture': False, 'promotion': None, 'check': False, 'mate': False}
        
        # Handle castling
        if move == 'O-O':
            result['dest'] = 'g1' if to_play == 'white' else 'g8'
            result['capture'] = False
            result['check'] = '+' in move
            result['mate'] = '#' in move
            return result
        elif move == 'O-O-O':
            result['dest'] = 'c1' if to_play == 'white' else 'c8'
            result['capture'] = False
            result['check'] = '+' in move
            result['mate'] = '#' in move
            return result
        
        # General parsing: find last square before =, +, #, or end
        match = re.findall(r'[a-h][1-8]', move)
        if match:
            result['dest'] = match[-1]  # Last square
        else:
            return None
        
        result['capture'] = 'x' in move
        if '=' in move:
            promo_part = move.split('=')[1].strip('+#')
            if len(promo_part) > 0:
                result['promotion'] = promo_part[0].upper()  # Q, R, etc.
        
        result['check'] = '+' in move
        result['mate'] = '#' in move
        return result
    
    # Score each move
    scored_moves = []
    for move in legal_moves:
        score = 0
        info = parse_move(move)
        if info is None:
            scored_moves.append((move, 0))
            continue
        
        # Prioritize checkmate and checks
        if info['mate']:
            score += 10000
        elif info['check']:
            score += 1000
        
        # Promotion value
        if info['promotion'] and info['promotion'] in piece_values:
            value = piece_values[info['promotion']]
            score += value
        
        # Capture value
        if info['capture'] and info['dest'] in pieces:
            captured_piece = pieces[info['dest']]
            if captured_piece[0] == opponent_color:
                captured_type = captured_piece[1]
                if captured_type in piece_values:
                    score += piece_values[captured_type]
        
        scored_moves.append((move, score))
    
    # Select the move with the highest score; tiebreak by first in list
    if not scored_moves:
        return legal_moves[0]  # Fallback, though should not happen
    
    best_move = max(scored_moves, key=lambda x: x[1])[0]
    return best_move
