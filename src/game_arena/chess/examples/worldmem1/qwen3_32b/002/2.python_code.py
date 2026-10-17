
import re

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    # Check for checkmate moves first
    for move in legal_moves:
        if move.endswith('#'):
            return (move, memory)
    
    best_move = None
    best_score = -float('inf')

    for move in legal_moves:
        current_score = 0

        # Castling is valued at 50 points
        if move == 'O-O' or move == 'O-O-O':
            current_score += 50

        # Check for captures
        if 'x' in move:
            dest_part = move.split('x')[-1]
            match = re.match(r"[a-h][1-8]", dest_part)
            if match:
                destination = match.group(0)
                if destination in pieces:
                    captured_type = pieces[destination][1]
                    current_score += {'P':1, 'N':3, 'B':3, 'R':5, 'Q':9}[captured_type]
        
        # Check if move gives check
        if move.endswith('+'):
            current_score += 5
        
        # Check for promotions
        if '=' in move:
            promo_part = move.split('=')[-1]
            promo_piece = promo_part[0]
            current_score += {'Q':9, 'R':5, 'B':3, 'N':3}.get(promo_piece, 0)

        # Update best move
        if current_score > best_score:
            best_move = move
            best_score = current_score
    
    return (best_move, memory)
