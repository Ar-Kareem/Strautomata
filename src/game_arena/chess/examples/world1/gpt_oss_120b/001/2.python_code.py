
import random
import re

# Piece values (king is given a very high value just for completeness)
PIECE_VALUE = {
    'P': 1,
    'N': 3,
    'B': 3,
    'R': 5,
    'Q': 9,
    'K': 1000
}

# Central squares that are good to occupy
CENTRAL_SQUARES = {'d4', 'e4', 'd5', 'e5'}

def _strip_suffix(move: str) -> str:
    """Remove trailing check/mate symbols."""
    return move.rstrip('+#')

def _extract_destination(move: str) -> str:
    """
    Return the destination square of a move.
    Handles normal moves, captures, promotions and castling.
    """
    if move in ('O-O', 'O-O-O'):
        # No destination square for castling; return a placeholder.
        return ''
    clean = _strip_suffix(move)
    # Promotion strings look like e8=Q, so the square is still the first two chars.
    # For long algebraic like Nxe5 or Be3, the destination is always the last two chars.
    # Disambiguation may precede it (e.g., Nbd7), but the last two chars are still the square.
    return clean[-2:]

def _is_capture(move: str) -> bool:
    return 'x' in move

def _is_promotion(move: str) -> str:
    """
    Return the promoted piece type (Q,R,B,N) if the move is a promotion,
    otherwise return an empty string.
    """
    if '=' in move:
        # The character after '=' is the promotion piece.
        return move.split('=')[1][0]
    return ''

def _is_check(move: str) -> bool:
    return move.endswith('+')

def _is_mate(move: str) -> bool:
    return move.endswith('#')

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    """
    Choose a move from `legal_moves` using a lightweight heuristic.
    Always returns a legal move.
    """
    best_score = -float('inf')
    best_moves = []

    for mv in legal_moves:
        score = 0

        # 1. Immediate mate
        if _is_mate(mv):
            score += 100000
        # 2. Check
        elif _is_check(mv):
            score += 500

        # 3. Castling – safe for the king
        if mv in ('O-O', 'O-O-O'):
            score += 30

        # 4. Promotion
        promo_piece = _is_promotion(mv)
        if promo_piece:
            promo_val = PIECE_VALUE.get(promo_piece, 0)
            # Bonus for becoming a queen is biggest, but all promotions are good.
            score += 800 + promo_val * 10

        # 5. Captures
        if _is_capture(mv):
            dest = _extract_destination(mv)
            captured = pieces.get(dest)
            if captured:
                cap_val = PIECE_VALUE.get(captured[1], 0)
                score += cap_val * 10

        # 6. Centralisation (non‑capture moves)
        else:
            dest = _extract_destination(mv)
            if dest in CENTRAL_SQUARES:
                score += 50

        # Keep track of the best scoring moves
        if score > best_score:
            best_score = score
            best_moves = [mv]
        elif score == best_score:
            best_moves.append(mv)

    # Choose randomly among equally good moves
    return random.choice(best_moves)
