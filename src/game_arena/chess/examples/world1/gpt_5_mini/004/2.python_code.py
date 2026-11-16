
import re
import random
from typing import Dict, List

# Piece values for quick heuristic evaluation
_PIECE_VALUES = {
    'P': 1,
    'N': 3,
    'B': 3,
    'R': 5,
    'Q': 9,
    'K': 0
}

_dest_re = re.compile(r'([a-h][1-8])')  # find squares like e4

def _find_destination(move: str) -> str:
    """Return the destination square (last file+rank) in the algebraic move string."""
    matches = _dest_re.findall(move)
    if matches:
        return matches[-1]
    return ""

def _move_piece_type(move: str) -> str:
    """Return the moving piece letter (K,Q,R,B,N) or 'P' for pawn or 'O' for castling."""
    if move.startswith('O'):  # O-O or O-O-O
        return 'O'
    first = move[0]
    if first in 'KQRBN':
        return first
    return 'P'

def policy(pieces: Dict[str, str], to_play: str, legal_moves: List[str]) -> str:
    # Always return a legal move; if nothing else, return the first legal move
    if not legal_moves:
        raise ValueError("No legal moves provided")

    # Quick immediate mate detection (choose it right away)
    for mv in legal_moves:
        if '#' in mv:  # mate annotation
            return mv

    # Deterministic tie-break: seed from position (so it's stable across runs)
    seed_tuple = (to_play, tuple(sorted(pieces.items())), tuple(legal_moves))
    random.seed(hash(seed_tuple))

    best_moves = []
    best_score = -10**9

    for mv in legal_moves:
        score = 0

        # Big bonus for check; (mate already handled)
        if '+' in mv:
            score += 800

        # Castling bonus for king safety
        if mv.startswith('O-O'):
            score += 120

        # Destination square
        dest = _find_destination(mv)

        # Moving piece type and its value
        mover = _move_piece_type(mv)
        mover_value = _PIECE_VALUES.get(mover, 1)  # pawns default 1

        # Detect capture
        is_capture = 'x' in mv
        captured_value = 0
        if is_capture:
            # General case: piece at destination belongs to opponent
            if dest and dest in pieces:
                occupant = pieces[dest]
                # occupant like 'wR' or 'bN'
                occ_color = occupant[0]
                occ_type = occupant[1]
                # Only treat as capture if it's opponent's piece (legal moves guarantee this)
                if (to_play == 'white' and occ_color == 'b') or (to_play == 'black' and occ_color == 'w'):
                    captured_value = _PIECE_VALUES.get(occ_type, 0)
                else:
                    # Uncommon; fallback to pawn value (possible en-passant case)
                    captured_value = 1
            else:
                # En-passant or capture of piece not present at dest: assume pawn capture
                captured_value = 1

            # Add capture score scaled
            score += captured_value * 1000

        # Promotion handling
        promo_bonus = 0
        # detect =Q, =R, =B, =N
        if '=' in mv:
            if '=Q' in mv:
                promo_gain = _PIECE_VALUES['Q'] - _PIECE_VALUES['P']
                promo_bonus += 900 + promo_gain * 100  # strong bonus for queen prom
            elif '=R' in mv:
                promo_gain = _PIECE_VALUES['R'] - _PIECE_VALUES['P']
                promo_bonus += 400 + promo_gain * 100
            elif '=B' in mv:
                promo_gain = _PIECE_VALUES['B'] - _PIECE_VALUES['P']
                promo_bonus += 250 + promo_gain * 100
            elif '=N' in mv:
                promo_gain = _PIECE_VALUES['N'] - _PIECE_VALUES['P']
                promo_bonus += 200 + promo_gain * 100
            # promotions are also captures sometimes; those captured_value already counted
        score += promo_bonus

        # Material exchange heuristic: reward profitable captures (captured - mover)
        # If it's a capture, compute net material change
        if is_capture:
            net = captured_value - mover_value
            score += net * 600  # emphasize favorable trades
        else:
            # For non-captures, small preference for developing/moving minor pieces and centralization
            if mover in ('N', 'B'):
                score += 50
            if mover == 'P':
                score += 10

        # Centralization: reward moves that go to central squares
        if dest:
            file = dest[0]
            rank = dest[1]
            central_bonus = 0
            if file in ('d', 'e') and rank in ('4', '5'):
                central_bonus += 60
            elif file in ('c', 'f') and rank in ('3', '4', '5', '6'):
                central_bonus += 30
            elif file in ('b', 'g'):
                central_bonus += 5
            score += central_bonus

        # Slight randomness for move ordering stability but nondeterministic tie-breaking avoided by seed
        score += random.uniform(0, 1)

        # Track best
        if score > best_score:
            best_score = score
            best_moves = [mv]
        elif abs(score - best_score) < 1e-9:
            best_moves.append(mv)

    # Choose one of the best moves deterministically (sort then pick first)
    best_moves.sort()
    return best_moves[0]
