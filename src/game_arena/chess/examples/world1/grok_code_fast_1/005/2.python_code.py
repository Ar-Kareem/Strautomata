
import random

def get_value(piece_type: str) -> int:
    return {'P': 1, 'B': 3, 'N': 3, 'R': 5, 'Q': 9, 'K': 0}[piece_type]

def extract_target_and_promo(move: str, color: str) -> None:
    if move.startswith('O-O'):
        rank = '1' if color == 'w' else '8'
        return f'g{rank}', None
    elif move.startswith('O-O-O'):
        rank = '1' if color == 'w' else '8'
        return f'c{rank}', None
    else:
        if '=' in move:
            parts = move.split('=')
            promo = parts[1][0]  # e.g., 'Q'
            m = parts[0]
            target = m[-2:]  # last two chars of move part
            return target, promo
        else:
            m = move.rstrip('+#')
            target = m[-2:]
            return target, None

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    if not legal_moves:
        return ''  # Though input assumes at least one legal move
    color = 'w' if to_play == 'white' else 'b'
    scores = []
    for move in legal_moves:
        target, promo = extract_target_and_promo(move, color)
        captured_val = 0
        if target in pieces and pieces[target][0] != color:
            captured_val = get_value(pieces[target][1])
        promo_gain = 0
        if promo:
            promo_gain = get_value(promo) - 1  # Gain from promoting pawn (P=1)
        check_score = 0
        if move.endswith('#'):
            check_score = 1000
        elif move.endswith('+'):
            check_score = 100
        elif move.startswith('O-O') or move.startswith('O-O-O'):
            check_score = 10
        total_score = check_score + captured_val + promo_gain
        scores.append((total_score, move))
    # Sort by score descending, stable sort so ties keep order
    scores.sort(reverse=True, key=lambda x: x[0])
    return scores[0][1]
