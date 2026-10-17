
import re
import random
from typing import Dict, Tuple, List

# piece values (king is 0 because it cannot be captured)
PIECE_VALUE = {
    'P': 1,
    'N': 3,
    'B': 3,
    'R': 5,
    'Q': 9,
    'K': 0,
}

def _color(to_play: str) -> str:
    return 'w' if to_play == 'white' else 'b'

def _opponent(color: str) -> str:
    return 'b' if color == 'w' else 'w'

def _extract_destination(move: str) -> str:
    """Return the destination square (e.g. 'e4') from a SAN move."""
    m = re.search(r'([a-h][1-8])', move)
    return m.group(1) if m else ''

def _is_pawn_move(move: str) -> bool:
    """In SAN a pawn move never starts with an uppercase piece letter or 'O'."""
    return not (move.startswith(('K', 'Q', 'R', 'B', 'N', 'O')))

def _score_move(move: str, pieces: Dict[str, str], to_play: str) -> int:
    """Assign a heuristic score to a move."""
    score = 0
    color = _color(to_play)
    opp = _opponent(color)

    # Checks / mates
    if '+' in move:
        score += 5
    if '#' in move:
        score += 20

    # Castling
    if move.startswith('O-O'):
        score += 3

    # Promotions
    if '=' in move:
        promo_piece = move.split('=')[1][0]  # the piece after '='
        promo_val = PIECE_VALUE.get(promo_piece, 0)
        score += promo_val * 10  # strong incentive

    # Captures
    if 'x' in move:
        dest = _extract_destination(move)
        if dest:
            captured = pieces.get(dest)
            if captured and captured[0] == opp:
                captured_val = PIECE_VALUE.get(captured[1], 0)
                score += captured_val * 10
            else:
                # en‑passant capture – destination empty, treat as generic capture
                score += 5

    # Quiet pawn pushes toward the centre
    if _is_pawn_move(move) and 'x' not in move and '=' not in move:
        dest = _extract_destination(move)
        if dest and dest[0] in 'de' and dest[1] in '45':
            score += 2

    return score

def policy(pieces: dict[str, str],
           to_play: str,
           legal_moves: list[str],
           memory: dict) -> Tuple[str, dict]:
    """
    Choose the move with the highest heuristic score.
    Returns (chosen_move, memory).  Memory is passed through unchanged.
    """
    best_move = None
    best_score = -float('inf')

    for mv in legal_moves:
        sc = _score_move(mv, pieces, to_play)
        if sc > best_score:
            best_score = sc
            best_move = mv

    # Fallback – should never happen because legal_moves is non‑empty
    if best_move is None:
        best_move = legal_moves[0]

    return best_move, memory
