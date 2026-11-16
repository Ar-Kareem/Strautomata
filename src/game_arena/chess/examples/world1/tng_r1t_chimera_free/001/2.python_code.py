
import re

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    piece_values = {'Q': 9, 'R': 5, 'B': 3, 'N': 3, 'P': 1, 'K': 0}
    color = 'w' if to_play == 'white' else 'b'
    opponent_color = 'b' if color == 'w' else 'w'
    
    max_score = -float('inf')
    best_move = legal_moves[0]
    
    for move in legal_moves:
        score = 0
        
        # Check for check
        if move.endswith('+'):
            score += 5  # Prefer checks, but not over material
        
        # Capture evaluation
        if 'x' in move:
            parts = move.split('x')
            target_square = parts[-1][:2]
            captured_piece = pieces.get(target_square)
            if captured_piece and captured_piece[0] == opponent_color:
                score += piece_values.get(captured_piece[1], 0)
            elif captured_piece is None and target_square[1] in ('3', '6'):
                # Possible en passant (capturing pawn)
                score += piece_values['P']
        
        # Promotion evaluation
        if '=' in move:
            promo_piece = move.split('=')[1][0]
            score += piece_values[promo_piece] - piece_values['P']
        
        # Castling bonus
        if move in ('O-O', 'O-O-O'):
            score += 3  # Strong preference for castling
        
        # Center control
        squares = re.findall(r'[a-h][1-8]', move)
        if squares:
            target_sq = squares[-1]
            file, rank = target_sq[0], int(target_sq[1])
            if file in ('d', 'e') and rank in (4, 5):
                score += 1  # Bonus for central squares
        
        # Piece development
        first_char = move[0]
        piece_type = first_char if first_char.isupper() else 'P'
        if piece_type in ('N', 'B') and len(squares) > 0:
            score += 0.5  # Encourage developing minor pieces
        
        # Avoid pawn attacks
        if squares:
            target_sq = squares[-1]
            for pawn_sq, pc in pieces.items():
                if pc != opponent_color + 'P':
                    continue
                p_file, p_rank = pawn_sq[0], int(pawn_sq[1])
                t_file, t_rank = target_sq[0], int(target_sq[1])
                if opponent_color == 'w':
                    if abs(ord(p_file) - ord(t_file)) == 1 and t_rank == p_rank + 1:
                        score -= piece_values.get(piece_type, 1)
                else:
                    if abs(ord(p_file) - ord(t_file)) == 1 and t_rank == p_rank - 1:
                        score -= piece_values.get(piece_type, 1)
        
        # Update best move
        if score > max_score or (score == max_score and len(move) < len(best_move)):
            max_score = score
            best_move = move
    
    return best_move
