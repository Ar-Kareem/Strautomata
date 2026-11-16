
import random
from typing import Dict, List

# Piece values used for scoring captures and promotions
PIECE_VALUE = {
    'P': 1,
    'N': 3,
    'B': 3,
    'R': 5,
    'Q': 9,
    'K': 0   # King capture is impossible; value kept for completeness
}

# Global variable that will be supplied by the arena.
# It must be a list of legal UCI strings for the side to move.
legal_moves: List[str] = []


def _dest_square(move: str) -> str:
    """Return the destination square of a UCI move (first two chars = source)."""
    # Promotion moves have length > 4, but still the destination is chars 2‑3
    return move[2:4]


def _is_capture(pieces: Dict[str, str], dest: str) -> bool:
    """True if the destination square currently holds an opponent piece."""
    return dest in pieces


def _capture_value(pieces: Dict[str, str], dest: str) -> int:
    """Value of the piece that would be captured on dest, 0 if empty."""
    if dest not in pieces:
        return 0
    piece_code = pieces[dest]
    # piece_code is like 'wQ' or 'bP'
    return PIECE_VALUE.get(piece_code[1], 0)


def _promotion_value(move: str) -> int:
    """Value added by a promotion move, 0 if not a promotion."""
    if len(move) > 4:
        promo_piece = move[4].upper()
        return PIECE_VALUE.get(promo_piece, 0)
    return 0


def policy(pieces: Dict[str, str], to_play: str) -> str:
    """
    Choose the best move from the globally supplied `legal_moves`.

    The heuristic prefers captures (higher material value) and promotions.
    If no capture exists, the first legal move is returned.
    """
    if not legal_moves:
        raise ValueError("legal_moves list is empty – cannot select a move.")

    best_score = -1
    best_moves: List[str] = []

    for mv in legal_moves:
        dest = _dest_square(mv)
        score = 0

        # Capture component
        if _is_capture(pieces, dest):
            score += _capture_value(pieces, dest)

        # Promotion component
        score += _promotion_value(mv)

        # Keep track of the best scoring moves
        if score > best_score:
            best_score = score
            best_moves = [mv]
        elif score == best_score:
            best_moves.append(mv)

    # If multiple moves share the top score, pick one randomly.
    # If no move gave a positive score (i.e., no captures/promotions),
    # best_score will be 0 and best_moves will contain all moves with score 0.
    chosen_move = random.choice(best_moves)
    return chosen_move
