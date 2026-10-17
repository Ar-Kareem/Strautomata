
import random
from typing import Dict, List, Tuple

# piece values
PIECE_VALUES = {
    'P': 1,
    'N': 3,
    'B': 3,
    'R': 5,
    'Q': 9,
    'K': 0,
}

def piece_value(piece_type: str) -> int:
    return PIECE_VALUES.get(piece_type.upper(), 0)

def get_destination(move: str) -> str:
    """
    Extract the destination square from a SAN move.
    Returns a string like 'e4' or None if not found.
    """
    # strip suffixes like +, #, !, ?
    m = move.rstrip('+#!?')
    # remove promotion part
    if '=' in m:
        m = m.split('=')[0]
    # search backwards for a file+rank pattern
    for i in range(len(m) - 2, -1, -1):
        if m[i] in 'abcdefgh' and m[i + 1] in '12345678':
            return m[i] + m[i + 1]
    return None

def evaluate_move(move: str, pieces: Dict[str, str], to_play: str) -> float:
    """
    Simple static evaluation of a single move.
    Higher scores correspond to more promising moves.
    """
    score = 0.0
    dest = get_destination(move)

    # Capture handling
    if 'x' in move:
        if dest and dest in pieces:
            # normal capture
            captured_piece = pieces[dest]
            score += piece_value(captured_piece[1])
        else:
            # possible en‑passant capture (destination empty)
            # en‑passant only occurs with pawn moves
            if move[0] in 'abcdefgh' and len(move) >= 4:
                # determine the square of the captured pawn
                if to_play == 'white':
                    cap_rank = str(int(dest[1]) - 1)
                else:
                    cap_rank = str(int(dest[1]) + 1)
                cap_sq = dest[0] + cap_rank
                if cap_sq in pieces and pieces[cap_sq][1] == 'P':
                    score += piece_value('P')

    # Promotion handling
    if '=' in move:
        promo_part = move.split('=')[1]
        promo_piece = promo_part[0]  # Q,R,B,N
        score += piece_value(promo_piece) - piece_value('P')

    # Check / check‑mate bonuses
    if '+' in move:
        score += 0.5
    if '#' in move:
        score += 10.0

    # Castling bonus (king safety)
    if move in ('O-O', 'O-O-O'):
        score += 0.2

    return score

def policy(pieces: dict[str, str],
           to_play: str,
           legal_moves: List[str],
           memory: dict) -> Tuple[str, dict]:
    """
    Choose the best move according to the static evaluation described above.
    Returns a tuple (chosen_move, updated_memory).
    """
    # Evaluate all legal moves
    best_score = -float('inf')
    best_moves = []

    for mv in legal_moves:
        sc = evaluate_move(mv, pieces, to_play)
        if sc > best_score:
            best_score = sc
            best_moves = [mv]
        elif sc == best_score:
            best_moves.append(mv)

    # Random tie‑break
    chosen = random.choice(best_moves) if best_moves else legal_moves[0]

    # Optionally store move history (not required for current logic)
    mem = memory.copy()
    mem.setdefault('history', []).append(chosen)

    return chosen, mem
