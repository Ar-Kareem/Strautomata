
import random

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    # Material values
    VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}
    
    def get_piece_value(p_code):
        if not p_code: return 0
        return VALUES.get(p_code[1], 0)

    best_score = -float('inf')
    best_move = legal_moves[0]
    
    # Identify friendly and enemy prefixes
    f_pref = 'w' if to_play == 'white' else 'b'
    e_pref = 'b' if to_play == 'white' else 'w'

    for move in legal_moves:
        score = 0
        
        # 1. Immediate Goal: Checkmate
        if '#' in move:
            return move
        
        # 2. Material Gain / Captures
        if 'x' in move:
            # Basic MVV-LVA logic: capture high value with low value
            # Find the target square (usually after the 'x')
            parts = move.split('x')
            target_sq = parts[1][:2]
            target_piece = pieces.get(target_sq)
            
            if target_piece:
                score += get_piece_value(target_piece) * 10
            else:
                # En passant
                score += VALUES['P'] * 10
            
            # Penalize moving a high value piece into a trade
            moving_piece_type = move[0] if move[0].isupper() else 'P'
            score -= (VALUES.get(moving_piece_type, 100) / 10)
        
        # 3. Development and Center Control (Heuristics)
        if '+' in move:
            score += 50
        if 'O-O' in move:
            score += 60
        if '=' in move: # Promotions
            if '=Q' in move: score += 800
            elif '=N' in move: score += 300
        
        # 4. Position-Specific Move Logic
        # Prioritize central movement for knights and bishops early
        if move[0] in 'NB':
            if any(c in move for c in ['d4', 'e4', 'd5', 'e5']):
                score += 30
        
        # 5. Avoid obvious blunders (very basic check)
        # If the move length is short (pawn move), just a small bonus
        if len(move) == 2 or (len(move) == 3 and move[0].islower()):
            score += 10
            
        if score > best_score:
            best_score = score
            best_move = move
        elif score == best_score:
            # Deterministic tie-breaking
            if len(move) > len(best_move):
                best_move = move

    return best_move
