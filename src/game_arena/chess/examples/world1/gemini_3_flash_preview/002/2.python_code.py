
import random

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    piece_values = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}
    
    def get_piece_at(sq):
        return pieces.get(sq)

    def evaluate_move(move):
        score = 0
        
        # 1. Immediate Checkmate
        if move.endswith('#'):
            return 99999
        
        # 2. Captures
        if 'x' in move:
            # Extract target square
            # Usually the square after 'x', e.g., Bxe5 or Nexd4
            parts = move.split('x')
            target_sq = parts[1][:2].replace('+', '').replace('#', '')
            captured_piece = get_piece_at(target_sq)
            if captured_piece:
                target_type = captured_piece[1]
                score += piece_values.get(target_type, 0)
        
        # 3. Promotions
        if '=' in move:
            if '=Q' in move: score += 800
            elif '=R' in move: score += 400
            else: score += 200

        # 4. Give Check
        if '+' in move:
            score += 50
            
        # 5. Position Heuristics (Simple)
        # Favor center for minor pieces/pawns
        if any(center in move for center in ['d4', 'e4', 'd5', 'e5']):
            score += 30
        
        # Castling is good
        if move in ['O-O', 'O-O-O']:
            score += 60

        # Penalize moving King early unless necessary
        if move.startswith('K') and not move.startswith('Ke2') and len(pieces) > 10:
            score -= 20

        return score

    # Shuffle to avoid deterministic behavior in equal positions
    random.shuffle(legal_moves)
    
    best_move = legal_moves[0]
    best_score = -float('inf')
    
    for move in legal_moves:
        current_score = evaluate_move(move)
        if current_score > best_score:
            best_score = current_score
            best_move = move
            
    return best_move
