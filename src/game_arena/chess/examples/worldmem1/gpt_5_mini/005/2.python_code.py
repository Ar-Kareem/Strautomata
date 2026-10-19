
import re
import random
from typing import Tuple, Dict, List

# Chess piece values for heuristic evaluation
PIECE_VALUES = {
    'Q': 9,
    'R': 5,
    'B': 3,
    'N': 3,
    'P': 1,
    'K': 1000  # extremely high so captures of king (mate) prioritized
}

CENTRAL_PAWNS = {'d4', 'e4', 'd5', 'e5', 'd3', 'e3', 'd6', 'e6'}
DEVELOPMENT_BONUS = 0.1
CHECK_BONUS = 0.5
CASTLE_BONUS = 0.25
PROMOTION_BONUS = {'Q': 9.0, 'R': 5.0, 'B': 3.0, 'N': 3.0}
MATE_BONUS = 10000.0

_square_re = re.compile(r'([a-h][1-8])')

def _last_square(move: str):
    """Return the last algebraic square in the move string, or None (for castling)."""
    matches = _square_re.findall(move)
    if matches:
        return matches[-1]
    return None

def _promotion_piece(move: str):
    """Return promotion piece letter if move promotes, else None."""
    # promotion format like b8=Q or bxa8=R
    m = re.search(r'=[QRBN]', move)
    if m:
        return m.group(0)[1]
    return None

def _is_capture(move: str):
    return 'x' in move

def _is_castle(move: str):
    return move.startswith('O-O')

def _is_check(move: str):
    return '+' in move or '#' in move

def _captured_value(move: str, dest: str, pieces: Dict[str, str], to_play: str):
    """Estimate the value of the captured piece for a capture move."""
    # to_play is 'white' or 'black'; opponent color letter is:
    opp = 'b' if to_play == 'white' else 'w'
    if dest and dest in pieces:
        piece_code = pieces[dest]
        if piece_code and piece_code[0] == opp:
            return PIECE_VALUES.get(piece_code[1], 0)
    # possible en-passant or capture where dest is empty in pieces list:
    # fallback: assume capture of a pawn (common) if 'x' present
    return PIECE_VALUES['P']

def _move_score(move: str, pieces: Dict[str, str], to_play: str) -> float:
    """
    Heuristic scoring:
    - Very large bonus for mate ('#').
    - Value for captured piece if 'x'.
    - Promotion bonuses for promoting to strong pieces.
    - Bonus for check.
    - Bonus for castling.
    - Minor bonuses for developing knights/bishops or moving central pawns.
    """
    score = 0.0

    # Immediate mate
    if '#' in move:
        return MATE_BONUS

    # Destination square
    dest = _last_square(move)

    # Capture value
    if _is_capture(move):
        cap_val = _captured_value(move, dest, pieces, to_play)
        # prefer capturing higher-value pieces; small extra for captures that also give check
        score += cap_val * 10.0  # weight captures strongly
        if '+' in move:
            score += CHECK_BONUS

    # Promotion
    prom = _promotion_piece(move)
    if prom:
        # reward promotion to stronger pieces
        score += PROMOTION_BONUS.get(prom, 0.0) * 10.0

    # Check bonus (non-capture)
    if '+' in move:
        score += CHECK_BONUS * 2.0

    # Castling bonus
    if _is_castle(move):
        score += CASTLE_BONUS * 5.0

    # Encourage development: moving knights/bishops (start with uppercase letter except 'O')
    # Pawn moves are lowercase starting char like 'e4'
    first_char = move[0]
    if first_char in ('N', 'B'):
        score += DEVELOPMENT_BONUS * 5.0
    elif first_char == 'R':
        score += DEVELOPMENT_BONUS * 1.5
    elif first_char == 'Q':
        # usually avoid early queen moves, small penalty
        score -= DEVELOPMENT_BONUS * 0.5
    elif first_char == 'K':
        # moving king usually bad unless castling handled earlier
        if not _is_castle(move):
            score -= DEVELOPMENT_BONUS * 2.0
    else:
        # pawn move: give small bonus if moving to central squares or advancing
        if dest and dest in CENTRAL_PAWNS:
            score += DEVELOPMENT_BONUS * 4.0
        else:
            score += DEVELOPMENT_BONUS * 0.5

    # Slight tie-breaker preference: longer algebraic string (captures and disambiguation often stronger)
    score += len(move) * 0.001

    return score

def policy(pieces: Dict[str, str], to_play: str, legal_moves: List[str], memory: Dict) -> Tuple[str, Dict]:
    """
    Select a move from legal_moves according to heuristics:
    - Immediately take mate if available.
    - Maximize weighted material gain (captures, promotions).
    - Prefer checks, castling, and development.
    Returns (move, memory).
    """
    # Defensive: if no moves (shouldn't happen), return empty string
    if not legal_moves:
        return ("", memory)

    best_moves = []
    best_score = -1e9

    # Evaluate each legal move
    for mv in legal_moves:
        try:
            score = _move_score(mv, pieces, to_play)
        except Exception:
            score = -1e9
        # track best
        if score > best_score:
            best_score = score
            best_moves = [mv]
        elif score == best_score:
            best_moves.append(mv)

    # Deterministic tie-break: sort best_moves and choose first
    best_moves.sort()

    chosen = best_moves[0]

    # store last move for possible future use
    memory = memory.copy() if memory is not None else {}
    memory['last_move'] = chosen
    memory['to_play'] = to_play

    return (chosen, memory)
