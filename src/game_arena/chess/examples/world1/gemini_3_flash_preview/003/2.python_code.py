
import random

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    if not legal_moves:
        return ""

    # Piece values for evaluation
    values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
    
    def get_move_score(move):
        score = 0
        
        # 1. Checkmate is top priority
        if move.endswith('#'):
            return 1000
        
        # 2. Captures
        if 'x' in move:
            # Extract target square
            # Simplified: finding the part after 'x'
            parts = move.split('x')
            target_sq_str = parts[1][:2]
            # Handle potential disambiguation or checks at end
            target_sq = "".join([c for c in target_sq_str if c.isalnum()])
            
            target_piece = pieces.get(target_sq)
            if target_piece:
                captured_type = target_piece[1]
                score += values.get(captured_type, 0) * 10
        
        # 3. Promotions
        if '=' in move:
            if '=Q' in move:
                score += 8
            else:
                score += 1

        # 4. Checks
        if '+' in move:
            score += 0.5
            
        # 5. Central positioning (basic heuristic)
        # Identify destination square
        dest = ""
        if move == "O-O" or move == "O-O-O":
            dest = "g1" if to_play == 'white' else "g8"
        else:
            # Get last two chars often representing sq (excluding +, #)
            clean_move = move.replace('+', '').replace('#', '')
            if '=' in clean_move:
                dest = clean_move.split('=')[0][-2:]
            else:
                dest = clean_move[-2:]
        
        # Favor center squares
        if len(dest) == 2:
            file, rank = dest[0], dest[1]
            if file in 'def' and rank in '3456':
                score += 0.2
                
        return score

    # Evaluate all moves
    scored_moves = []
    for m in legal_moves:
        scored_moves.append((get_move_score(m), m))
    
    # Sort by score descending
    scored_moves.sort(key=lambda x: x[0], reverse=True)
    
    # Pick the best move (or a random one among tied best)
    max_score = scored_moves[0][0]
    best_moves = [m for s, m in scored_moves if s == max_score]
    
    return random.choice(best_moves)
