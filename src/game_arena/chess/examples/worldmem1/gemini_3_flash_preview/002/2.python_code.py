
import random

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    # Material values
    values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 100}
    
    def get_piece_value(p_code):
        if not p_code or len(p_code) < 2:
            return 0
        return values.get(p_code[1], 0)

    best_move = legal_moves[0]
    best_score = -99999

    my_color_char = 'w' if to_play == 'white' else 'b'
    opp_color_char = 'b' if to_play == 'white' else 'w'

    for move in legal_moves:
        score = 0
        
        # 1. Checkmate is top priority
        if '#' in move:
            return move, memory
        
        # 2. Promotion preference
        if '=Q' in move:
            score += 8
        elif '=' in move:
            score += 1

        # 3. Capture evaluation
        # Logic: find if move involves 'x'. If moves like 'Bxf5', we look for piece at f5.
        if 'x' in move:
            # Basic parsing: the square being captured is usually the last 2 chars or before '+'
            target_sq = move.split('x')[-1][:2]
            target_piece = pieces.get(target_sq)
            if target_piece:
                score += get_piece_value(target_piece) * 10
            else:
                # En passant or edge case
                score += 1
        
        # 4. Check bonus
        if '+' in move:
            score += 0.5

        # 5. Position basics (Centralization for pieces, safety for king)
        # We look at the destination square in the move string
        # Very simple: favor moves that don't move the King early unless castling
        if move.startswith('K') and 'O-O' not in move:
            score -= 2
        if 'O-O' in move:
            score += 3

        # Add a tiny bit of randomness to break ties
        score += random.uniform(0, 0.1)

        if score > best_score:
            best_score = score
            best_move = move

    return best_move, memory
