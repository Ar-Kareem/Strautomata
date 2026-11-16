
import re
from typing import Dict, List

# Classic piece values (in centipawns)
PIECE_VALUE = {
    'P': 100,
    'N': 320,
    'B': 330,
    'R': 500,
    'Q': 900,
    'K': 0,
}

def _strip_suffix(move: str) -> str:
    """Remove trailing check / mate symbols and promotion suffixes."""
    # Remove check (+) or mate (#) at the end
    move = move.rstrip('+#')
    # Remove promotion part (=Q, =R, =B, =N) if present
    # keep the promotion indicator for scoring, but strip it for square parsing
    return move

def _score_move(move: str, pieces: Dict[str, str]) -> float:
    """Assign a heuristic score to a SAN move."""
    score = 0.0

    # Immediate win?
    if '#' in move:
        return 1_000_000.0  # unbeatable

    # Check bonus
    if '+' in move:
        score += 10.0

    # Castling bonus
    if move.startswith('O-O'):
        score += 5.0

    # Promotion bonus
    if '=' in move:
        score += 800.0

    # Capture handling
    if 'x' in move:
        # Find the square immediately after the 'x'
        after_x = move.split('x', 1)[1]
        # The target square is the first two characters that match a board coordinate
        match = re.match(r'([a-h][1-8])', after_x)
        if match:
            target_sq = match.group(1)
            captured_piece = pieces.get(target_sq)
            if captured_piece:
                captured_type = captured_piece[1]  # e.g., 'Q' from 'bQ'
                score += PIECE_VALUE.get(captured_type, 0)

        # Small penalty for moving a valuable piece (optional, encourages trades)
        # Determine moving piece type (pawn if first char not uppercase piece letter)
        moving_piece_type = 'P'  # default pawn
        if move[0] in 'KQRBN':
            moving_piece_type = move[0]
        score -= 0.1 * PIECE_VALUE.get(moving_piece_type, 0)

    return score

def policy(pieces: Dict[str, str], to_play: str, legal_moves: List[str]) -> str:
    """
    Choose the best move from the list of legal SAN strings using a simple
    material‑and‑tactics heuristic.
    """
    best_move = legal_moves[0]
    best_score = -float('inf')

    for mv in legal_moves:
        sc = _score_move(mv, pieces)
        if sc > best_score:
            best_score = sc
            best_move = mv

    return best_move
