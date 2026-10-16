
import re

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    piece_values = {'P':1, 'N':3, 'B':3.2, 'R':5, 'Q':9, 'K':100}
    
    def target_square(move: str):
        # remove check/mate markers for parsing
        m = re.findall(r'([a-h][1-8])', move)
        if m:
            return m[-1]
        return None

    def promotion_value(move: str):
        if '=' in move:
            promo = move.split('=')[-1][0]
            return piece_values.get(promo, 0)
        return 0

    def capture_value(move: str):
        if 'x' not in move:
            return 0
        sq = target_square(move)
        if sq and sq in pieces:
            return piece_values.get(pieces[sq][1], 1)
        # en passant or unknown: assume pawn
        return 1

    def central_bonus(sq: str):
        if not sq:
            return 0.0
        file = ord(sq[0]) - ord('a')
        rank = int(sq[1]) - 1
        # center squares around d4/e4/d5/e5
        return 0.1 * (4 - abs(file - 3.5)) + 0.1 * (4 - abs(rank - 3.5))

    best_move = legal_moves[0]
    best_score = -1e9
    
    for move in legal_moves:
        if '#' in move:
            return move  # immediate mate
        
        score = 0.0
        if '+' in move:
            score += 5
        if move in ('O-O', 'O-O-O'):
            score += 3
        
        cap_val = capture_value(move)
        score += cap_val * 10
        
        promo_val = promotion_value(move)
        score += promo_val * 8
        
        sq = target_square(move)
        score += central_bonus(sq)
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
