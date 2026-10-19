
import re

PIECE_VALUES = {
    'P': 1,
    'N': 3,
    'B': 3,
    'R': 5,
    'Q': 9,
    'K': 100
}

def _strip_suffix(move: str) -> str:
    # remove check/mate symbols
    return move.replace('+', '').replace('#', '')

def _get_target_square(move: str):
    if move.startswith('O-O'):
        return None
    s = _strip_suffix(move)
    # remove promotion part
    if '=' in s:
        s = s.split('=')[0]
    squares = re.findall(r'[a-h][1-8]', s)
    if squares:
        return squares[-1]
    return None

def _promotion_value(move: str) -> int:
    if '=' in move:
        promo = move.split('=')[-1]
        promo = promo.replace('+','').replace('#','')
        if promo and promo[0] in PIECE_VALUES:
            return PIECE_VALUES[promo[0]]
    return 0

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    best_move = legal_moves[0]
    best_score = -1e9

    for mv in legal_moves:
        score = 0

        # Checkmate
        if '#' in mv:
            score += 10000

        # Check
        if '+' in mv:
            score += 200

        # Castling bonus
        if mv.startswith('O-O'):
            score += 50

        # Promotion bonus
        promo_val = _promotion_value(mv)
        if promo_val:
            # promotion gain relative to pawn
            score += (promo_val - 1) * 100

        # Capture bonus
        if 'x' in mv:
            target = _get_target_square(mv)
            if target and target in pieces:
                captured_piece = pieces[target][1]
                score += PIECE_VALUES.get(captured_piece, 0) * 100
            else:
                score += 50  # unknown capture (e.g., en passant)

        # small preference for developing moves (heuristic)
        if mv[0] in "NBRQ":
            score += 5

        if score > best_score:
            best_score = score
            best_move = mv

    return best_move
