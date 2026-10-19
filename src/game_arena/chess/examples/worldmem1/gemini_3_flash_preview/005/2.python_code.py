
import random

def policy(pieces, to_play, legal_moves, memory):
    # Material values
    vals = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}
    
    def get_move_score(move):
        score = 0
        
        # 1. Prioritize Checkmate
        if '#' in move:
            return 100000
        
        # 2. Capture evaluation
        if 'x' in move:
            # Extract target square (usually after the 'x')
            # Example: 'Bxf5' -> 'f5', 'exd5' -> 'd5'
            # Check for pieces ending in '+', '#' or promotions
            clean_move = move.replace('+', '').replace('#', '')
            if '=' in clean_move:
                target_sq = clean_move.split('=')[0][-2:]
            else:
                target_sq = clean_move[-2:]
                
            captured_piece = pieces.get(target_sq)
            if captured_piece:
                target_type = captured_piece[1]
                score += vals.get(target_type, 0)
        
        # 3. Promotion Logic
        if '=Q' in move:
            score += 800
        elif '=' in move:
            score += 200
            
        # 4. Positional/Check bonuses
        if '+' in move:
            score += 50
        if move in ['O-O', 'O-O-O']:
            score += 40
            
        # 5. Piece movement (Centralization/Development)
        # Favor moves that end on 'd4', 'd5', 'e4', 'e5'
        if any(center in move for center in ['d4', 'd5', 'e4', 'e5']):
            score += 20
            
        # 6. Randomness to avoid deterministic loops
        score += random.randint(0, 10)
        
        return score

    # Find the move with the highest score
    best_move = legal_moves[0]
    max_score = -float('inf')
    
    for move in legal_moves:
        current_score = get_move_score(move)
        if current_score > max_score:
            max_score = current_score
            best_move = move
            
    return best_move, memory
