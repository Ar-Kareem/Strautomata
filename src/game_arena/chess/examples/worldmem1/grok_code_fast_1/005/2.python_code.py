
import random

def policy(pieces, to_play, legal_moves, memory):
    mult = 1 if to_play == 'white' else -1
    piece_vals = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
    
    def get_val(p):
        sign = 1 if p[0] == 'w' else -1
        return sign * piece_vals[p[1]]
    
    def parse_target(move):
        move_clean = move.replace('+', '').replace('#', '').replace('++', '').replace(',', '')
        if 'O-' in move_clean:
            return None
        # Assume target is the last square (e.g., last two chars where second is digit)
        for i in range(len(move_clean) - 1, 1, -1):
            if move_clean[i].isdigit() and move_clean[i-1].islower():
                return move_clean[i-1:i+1]
        return None
    
    # Check for checkmate moves
    mates = [m for m in legal_moves if '#' in m or '++' in m]
    if mates:
        return random.choice(mates), memory
    
    # Compute scores for other moves
    scores = []
    for move in legal_moves:
        target = parse_target(move)
        score = 0
        if '=' in move:
            # Promotion bonus (rough estimate for queen)
            score += 6 * mult
        if '+' in move and '#' not in move and '++' not in move:
            # Check bonus
            score += 0.5 * mult
        if target and target in pieces and pieces[target][0] != to_play[0]:
            # Capture gain: removing enemy's negative value adds positive
            cap_val = -get_val(pieces[target])
            score += cap_val * mult  # Adjust for perspective
        scores.append(score)
    
    # Select move with max score
    max_score = max(scores) if scores else 0
    candidates = [m for m, s in zip(legal_moves, scores) if s == max_score]
    return random.choice(candidates), memory
