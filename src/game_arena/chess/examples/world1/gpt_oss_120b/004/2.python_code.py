
import re
from typing import Dict, List

# piece values for material gain evaluation
PIECE_VALUE = {
    'P': 1,
    'N': 3,
    'B': 3,
    'R': 5,
    'Q': 9,
    'K': 0  # king cannot be captured
}

def _dest_square(move: str) -> str:
    """
    Extract the destination square from a SAN move.
    Returns a two‑character string like 'e4' or '' if not found.
    """
    m = re.search(r'([a-h][1-8])$', move)
    return m.group(1) if m else ''

def _captured_piece_value(move: str, pieces: Dict[str, str]) -> int:
    """
    Return the value of the captured piece for a given move,
    or 0 if the move does not capture (or the captured piece is unknown).
    """
    if 'x' not in move:
        return 0
    dest = _dest_square(move)
    if not dest:
        return 0
    piece = pieces.get(dest)
    if not piece:
        return 0
    return PIECE_VALUE.get(piece[1], 0)  # piece[1] is the type letter

def policy(pieces: Dict[str, str], to_play: str, legal_moves: List[str]) -> str:
    """
    Choose the best move based on simple heuristics:
    - immediate checkmate,
    - checks,
    - promotions,
    - material captures,
    - castling.
    Returns one move string that is guaranteed to be in `legal_moves`.
    """
    best_move = None
    best_score = -float('inf')

    for move in legal_moves:
        # Immediate checkmate wins the game
        if '#' in move:
            return move

        score = 0.0

        # Check bonus
        if '+' in move:
            score += 0.5

        # Promotion bonus
        if '=' in move:
            score += 0.4

        # Capture value
        capture_val = _captured_piece_value(move, pieces)
        if capture_val:
            score += capture_val

        # Castling safety bonus
        if move in ('O-O', 'O-O-O'):
            score += 0.1

        # Update best move
        if score > best_score:
            best_score = score
            best_move = move

    # Fallback – there should always be at least one legal move
    return best_move if best_move is not None else legal_moves[0]
