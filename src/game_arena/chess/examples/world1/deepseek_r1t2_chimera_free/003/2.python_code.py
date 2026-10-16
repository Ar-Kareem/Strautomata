
import re

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    # Immediate checkmate detection
    for move in legal_moves:
        if move.endswith('#'):
            return move
    
    piece_values = {'Q': 9, 'R': 5, 'B': 3, 'N': 3, 'P': 1, 'K': 0}
    my_color = 'w' if to_play == 'white' else 'b'
    best_move = legal_moves[0]
    max_score = -float('inf')
    
    for move in legal_moves:
        score = 0
        # Castling priority
        if move in {'O-O', 'O-O-O'}:
            score = 200  # High priority for king safety
        else:
            # Extract destination square from move notation
            dest_match = re.findall(r'([a-h][1-8])', move)
            dest = dest_match[-1] if dest_match else None
            
            if not dest:
                continue  # Fallback to default
            
            # Determine moving piece type
            if move[0] in 'KQRBN':
                moving_piece = move[0]
            else:
                moving_piece = 'P'  # Pawn move
            piece_val = piece_values[moving_piece]
            
            # Base positional score (centrality)
            file = ord(dest[0]) - ord('a')
            rank = int(dest[1]) - 1
            centrality = 14 - (abs(file - 3.5) + abs(rank - 3.5))
            score = piece_val * 15 + centrality  # Weight piece value heavier
            
            # Promotion bonus
            if '=' in move:
                promo_piece = move.split('=')[1][0]
                score += (piece_values[promo_piece] - 1) * 20 + 1500
            
            # Capture evaluation
            if dest in pieces:
                target_piece = pieces[dest]
                if target_piece[0] != my_color:
                    captured_val = piece_values.get(target_piece[1], 0)
                    score += captured_val * 15 - piece_val  # Aggressive capture weighting
            
            # Check bonus
            if '+' in move:
                score += 150  # Significant bonus for checks
            
            # King move penalty
            if moving_piece == 'K':
                score -= 50  # Discourage unnecessary king moves
        
        # Update best move
        if score > max_score:
            max_score = score
            best_move = move
    
    return best_move
