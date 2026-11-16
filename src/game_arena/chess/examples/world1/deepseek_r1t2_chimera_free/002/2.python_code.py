
import re

PIECE_VALUES = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    player_color = 'w' if to_play == 'white' else 'b'
    opponent_color = 'b' if player_color == 'w' else 'w'
    scores = {}
    
    for move in legal_moves:
        score = 0
        # Extract destination square using regex (last occurrence of square pattern)
        squares = re.findall(r'[a-h][1-8]', move)
        dest = squares[-1] if squares else None
        
        # Promotion scoring (Queen highest)
        if '=Q' in move:
            score += 900
        elif '=R' in move:
            score += 500
        elif '=B' in move or '=N' in move:
            score += 300
        
        # Castling priority
        if move == 'O-O' or move == 'O-O-O':
            score += 200
        
        # Check bonus (even if not mate)
        if move.endswith('+'):
            score += 100
        
        # Determine moving piece type (K, Q, R, B, N, P) from move string
        if move.startswith('O-O'):
            moving_piece_type = 'K'
        elif move[0] in 'KQRBN':
            moving_piece_type = move[0]
        else:
            moving_piece_type = 'P'
        moving_value = PIECE_VALUES.get(moving_piece_type, 0)
        
        # Capture evaluation (includes en passant heuristic)
        if 'x' in move:
            # Assume capture; determine captured piece
            if dest in pieces and pieces[dest][0] == opponent_color:
                captured_type = pieces[dest][1]
            else:
                captured_type = 'P'  # Default to pawn (e.g., en passant)
            captured_value = PIECE_VALUES.get(captured_type, 0)
            delta = captured_value - moving_value
            score += delta * 50  # Weighted material gain
        
        # Center control: preference for central squares
        if dest in ['d4', 'd5', 'e4', 'e5']:
            score += 30
        elif dest in ['c3', 'c6', 'd3', 'd6', 'e3', 'e6', 'f3', 'f6', 'c4', 'c5', 'f4', 'f5']:
            score += 15
        
        # Penalize moving king (non-castling)
        if moving_piece_type == 'K' and not move.startswith('O-O'):
            score -= 20
        
        # Pawn attack vulnerability penalty
        if dest and moving_piece_type != 'K':  # King moves handled separately
            dirs = [(-1, -1), (1, -1)] if player_color == 'w' else [(-1, 1), (1, 1)]
            for f_dir, r_dir in dirs:
                try:
                    f_ord = ord(dest[0]) + f_dir
                    if f_ord < ord('a') or f_ord > ord('h'):
                        continue
                    adj_file = chr(f_ord)
                    adj_rank = int(dest[1]) + r_dir
                    if adj_rank < 1 or adj_rank > 8:
                        continue
                    adj_square = f"{adj_file}{adj_rank}"
                    piece = pieces.get(adj_square)
                    if piece and piece[0] == opponent_color and piece[1] == 'P':
                        score -= moving_value // 2  # Penalty for being attacked by pawn
                        break
                except:
                    pass
        
        scores[move] = score
    
    # Select move with highest score (lex order tiebreaker)
    return max(legal_moves, key=lambda m: (scores[m], m))
