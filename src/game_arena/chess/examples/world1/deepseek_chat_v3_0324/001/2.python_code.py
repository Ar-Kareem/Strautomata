
import numpy as np

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    piece_values = {'Q': 9, 'R': 5, 'B': 3, 'N': 3, 'P': 1, 'K': 0}
    color = 'w' if to_play == 'white' else 'b'
    opponent_color = 'b' if color == 'w' else 'w'
    
    def evaluate_move(move):
        score = 0
        
        # Check for checkmate
        if move.endswith('#'):
            return 10000
        
        # Check for check
        if move.endswith('+'):
            score += 50
        
        # Prioritize castling
        if move in ('O-O', 'O-O-O'):
            score += 100
        
        # Evaluate captures
        if 'x' in move:
            target_square = move.split('x')[1][:2]
            if target_square in pieces:
                captured_piece = pieces[target_square]
                if captured_piece[0] == opponent_color:
                    score += piece_values.get(captured_piece[1], 0) * 10
        
        # Evaluate promotions
        if '=Q' in move:
            score += 80
        elif '=R' in move:
            score += 50
        elif '=B' in move or '=N' in move:
            score += 30
        
        # Evaluate center control
        center_squares = ['d4', 'e4', 'd5', 'e5']
        target_square = move[-2:] if len(move) >= 2 else ''
        if target_square in center_squares:
            score += 15
        
        # Penalize moving pieces to squares where they can be captured
        if target_square:
            for opp_move in legal_moves:
                if 'x' + target_square in opp_move:
                    moving_piece = move[0] if move[0].isupper() else 'P'
                    score -= piece_values.get(moving_piece, 0) * 8
        
        return score
    
    # Find the move with highest score
    best_move = legal_moves[0]
    best_score = -9999
    
    for move in legal_moves:
        current_score = evaluate_move(move)
        if current_score > best_score:
            best_score = current_score
            best_move = move
    
    return best_move
