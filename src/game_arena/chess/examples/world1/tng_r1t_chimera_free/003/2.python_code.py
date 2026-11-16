
import random

piece_values = {'Q': 9, 'R': 5, 'B': 3, 'N': 3, 'P': 1, 'K': 0}

def extract_target_square(move):
    if move in ['O-O', 'O-O-O']:
        return None
    cleaned = move.rstrip('+#')
    candidates = []
    for i in range(len(cleaned)):
        for j in range(i+1, len(cleaned)+1):
            part = cleaned[i:j]
            if len(part) == 2 and part[0].lower() in 'abcdefgh' and part[1] in '12345678':
                candidates.append(part.lower())
    return candidates[-1] if candidates else None

def calculate_score(move, pieces, current_color):
    score = 0
    if move.endswith('#'):
        return 1000000
    if move in ['O-O', 'O-O-O']:
        score += 200
    if '=' in move:
        promo = move.split('=')[1][0]
        score += piece_values.get(promo, 0) - piece_values['P']
    target_square = extract_target_square(move)
    if target_square and target_square in pieces:
        target_piece = pieces[target_square]
        if target_piece[0] != current_color:
            captured_value = piece_values.get(target_piece[1], 0)
            if move[0].isupper() and move[0] != 'O':
                moving_piece = move[0]
            else:
                moving_piece = 'P'
            moving_value = piece_values.get(moving_piece, 0)
            score += (captured_value - moving_value) * 10
    if '+' in move:
        score += 1
    if target_square in {'d4', 'e4', 'd5', 'e5'}:
        score += 0.5
    return score

def policy(pieces, to_play, legal_moves):
    current_color = 'w' if to_play == 'white' else 'b'
    best_score = -float('inf')
    best_moves = []
    for move in legal_moves:
        score = calculate_score(move, pieces, current_color)
        if score > best_score:
            best_score = score
            best_moves = [move]
        elif score == best_score:
            best_moves.append(move)
    return random.choice(best_moves)
