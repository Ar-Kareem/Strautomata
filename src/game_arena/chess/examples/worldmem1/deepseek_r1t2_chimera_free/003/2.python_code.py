
import re

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
    color = 'w' if to_play == 'white' else 'b'
    opponent_color = 'b' if color == 'w' else 'w'
    
    best_move = legal_moves[0]  # default to first move
    best_score = float('-inf')
    
    for move in legal_moves:
        score = 0
        original_move = move
        clean_move = move.replace('+', '').replace('#', '')
        
        # Castling bonus
        if clean_move == 'O-O' or clean_move == 'O-O-O':
            score += 50
        
        # Promotion bonus
        if '=' in clean_move:
            promo_piece = clean_move.split('=')[1][0]
            score += piece_values.get(promo_piece, 0) * 100
            clean_move = clean_move.split('=')[0]
        
        # Capture evaluation
        if 'x' in clean_move:
            parts = clean_move.split('x')
            if len(parts) < 2:
                captured_square = None
            else:
                sq_candidate = parts[-1]
                match = re.search(r'([a-h][1-8])', sq_candidate)
                captured_square = match.group(0) if match else None
            
            if captured_square:
                captured_piece = pieces.get(captured_square, None)
                if captured_piece and captured_piece[0] == opponent_color:
                    captured_val = piece_values.get(captured_piece[1], 0)
                else:  # En passant assumed
                    captured_val = 1
            else:
                captured_val = 0
            
            # Moving piece value
            first_char = clean_move[0]
            if first_char in piece_values:
                moving_val = piece_values[first_char]
            else:
                moving_val = 1  # Pawn
            
            score += 10 * (captured_val - moving_val)
        
        # Piece-square bonuses
        if clean_move in ['O-O', 'O-O-O']:
            target_sq = 'g1' if color == 'w' else 'g8' if clean_move == 'O-O' else 'c1' if color == 'w' else 'c8'
        else:
            match = re.search(r'([a-h][1-8])$', clean_move)
            target_sq = match.group(0) if match else None
        
        if target_sq:
            piece_type = clean_move[0] if clean_move[0] in piece_values else 'P'
            file, rank = target_sq[0], int(target_sq[1])
            
            # Knight centralization
            if piece_type == 'N':
                file_penalty = abs(ord(file) - ord('e'))
                rank_penalty = abs(rank - 4)
                score -= (file_penalty + rank_penalty) * 5
            
            # Pawn advancement
            elif piece_type == 'P':
                advance_bonus = (rank - 2) * 10 if color == 'w' else (7 - rank) * 10
                center_bonus = 20 if file in ['d','e'] else 10 if file in ['c','f'] else 0
                score += advance_bonus + center_bonus
            
            # King safety (castling squares)
            elif piece_type == 'K':
                if target_sq in ['g1','c1','g8','c8']:
                    score += 50
        
        if score > best_score:
            best_score = score
            best_move = original_move
    
    return (best_move, memory)
