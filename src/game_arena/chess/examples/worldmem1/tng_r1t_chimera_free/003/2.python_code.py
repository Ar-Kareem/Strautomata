
import re

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    piece_values = {'Q': 9, 'R': 5, 'B': 3, 'N': 3, 'P': 1, 'K': 0}
    best_move = legal_moves[0]
    best_score = -float('inf')
    opponent_color = 'b' if to_play == 'white' else 'w'
    
    for move in legal_moves:
        score = 0
        # Castling bonus
        if move.startswith('O-O'):
            score += 50
        else:
            # Determine moving piece type
            first_char = move[0]
            if first_char in 'KQRBN':
                piece_type = first_char
            else:
                piece_type = 'P'
            
            # Promotion bonus
            if '=' in move:
                promoted_piece = move.split('=')[1][0]
                score += piece_values.get(promoted_piece, 0) - piece_values['P']
            
            # Extract destination square
            dest_match = re.search(r'([a-h][1-8])(?=[+#=]?|$)', move)
            dest_square = dest_match.group(1) if dest_match else ''
            
            # Capture evaluation
            if 'x' in move and dest_square:
                dest_piece = pieces.get(dest_square, '')
                if dest_piece and dest_piece[0] == opponent_color:
                    captured_value = piece_values.get(dest_piece[1], 0)
                    moving_value = piece_values.get(piece_type, 0)
                    score += captured_value - moving_value  # Net material gain
            
            # Center control bonus
            if dest_square:
                file, rank = dest_square[0], dest_square[1]
                if file in {'c', 'd', 'e', 'f'} and rank in {'3', '4', '5', '6'}:
                    score += 2 if piece_type in {'N', 'B'} else 1
            
            # Check bonus
            if '+' in move:
                score += 5
        
        # Update best move
        if score > best_score:
            best_score = score
            best_move = move
    
    return (best_move, memory)
