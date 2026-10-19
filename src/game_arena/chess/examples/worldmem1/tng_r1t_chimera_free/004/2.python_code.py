
import re
import random

piece_values = {'Q': 9, 'R': 5, 'B': 3, 'N': 3, 'P': 1, 'K': 0}

def extract_target_square(move):
    squares = re.findall(r'[a-h][1-8]', move)
    return squares[-1] if squares else None

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    max_score = -float('inf')
    best_moves = []
    
    player_color = to_play[0].lower()
    
    for move in legal_moves:
        score = 0
        
        # Capture evaluation
        if 'x' in move:
            parts = move.split('x')
            if len(parts) >= 2:
                target_part = parts[1]
                squares = re.findall(r'[a-h][1-8]', target_part)
                if squares:
                    target_square = squares[0]
                    if target_square in pieces:
                        captured_piece = pieces[target_square]
                        if captured_piece[0] != player_color:
                            piece_type = captured_piece[1]
                            score += piece_values.get(piece_type, 0)
                    else:
                        # En passant or other special capture (assume Pawn value)
                        score += 1
        
        # Promotion evaluation
        if '=Q' in move:
            score += 8
        elif '=R' in move:
            score += 4
        elif '=B' in move or '=N' in move:
            score += 2
        
        # Castling bonus
        if move in {'O-O', 'O-O-O'}:
            score += 2
        
        # Check bonus
        if '+' in move:
            score += 1
        
        # Central square bonus
        target_square = extract_target_square(move)
        if target_square in {'d4', 'e4', 'd5', 'e5'}:
            score += 0.5
        
        # Update best moves
        if score > max_score:
            max_score = score
            best_moves = [move]
        elif score == max_score:
            best_moves.append(move)
    
    # Select randomly among best moves
    selected_move = random.choice(best_moves)
    return (selected_move, memory)
