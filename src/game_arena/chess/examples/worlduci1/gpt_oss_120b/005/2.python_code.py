
# chess_policy.py
import random
from typing import Dict, List, Tuple

# Piece values for material evaluation
PIECE_VALUE = {
    'P': 1,
    'N': 3,
    'B': 3,
    'R': 5,
    'Q': 9,
    'K': 0,
}

def manhattan(a: str, b: str) -> int:
    """Manhattan distance between two squares given in algebraic notation."""
    file_a, rank_a = ord(a[0]) - ord('a'), int(a[1]) - 1
    file_b, rank_b = ord(b[0]) - ord('a'), int(b[1]) - 1
    return abs(file_a - file_b) + abs(rank_a - rank_b)

def evaluate_move(move: str, pieces: Dict[str, str],
                  opponent_king: str, to_play: str) -> Tuple[int, int]:
    """
    Returns a tuple (material_gain, distance_to_king) for the move.
    Higher material_gain is better; lower distance_to_king is better.
    """
    src = move[:2]
    dst = move[2:4]
    promotion = move[4] if len(move) > 4 else None

    mover = pieces.get(src)
    if mover is None:
        # Illegal move (should not happen); treat as worst.
        return (-9999, 9999)

    # Material gain from capture
    captured_piece = pieces.get(dst)
    capture_gain = 0
    if captured_piece and captured_piece[0] != mover[0]:
        capture_gain = PIECE_VALUE[captured_piece[1]]

    # Promotion bonus
    promo_gain = 0
    if promotion:
        # pawn is replaced by the promoted piece
        promo_gain = PIECE_VALUE[promotion.upper()] - PIECE_VALUE['P']

    material_gain = capture_gain + promo_gain

    # New location of the moving piece (after promotion it is the promoted piece)
    new_sq = dst

    # Distance from the moved piece to the opponent king
    distance = manhattan(new_sq, opponent_king)

    return (material_gain, distance)

def policy(pieces: dict[str, str], to_play: str) -> str:
    """
    Choose the best move from the globally supplied list `legal_moves`.
    The function is pure; it only reads the global `legal_moves` and returns
    a single UCI move string that is guaranteed to be in that list.
    """
    # `legal_moves` is expected to be defined by the arena before calling policy.
    global legal_moves  # type: ignore
    if not legal_moves:
        raise ValueError("No legal moves provided.")

    # Determine opponent king square
    opp_color = 'b' if to_play == 'white' else 'w'
    opponent_king = None
    for sq, code in pieces.items():
        if code == f'{opp_color}K':
            opponent_king = sq
            break
    if opponent_king is None:
        # Should never happen in a legal position; pick a random move.
        return random.choice(legal_moves)

    # Evaluate all moves
    best_gain = -float('inf')
    best_distance = float('inf')
    best_moves: List[str] = []

    for mv in legal_moves:
        gain, dist = evaluate_move(mv, pieces, opponent_king, to_play)

        if gain > best_gain:
            best_gain = gain
            best_distance = dist
            best_moves = [mv]
        elif gain == best_gain:
            if dist < best_distance:
                best_distance = dist
                best_moves = [mv]
            elif dist == best_distance:
                best_moves.append(mv)

    # If multiple equally good moves remain, pick one at random for variety
    return random.choice(best_moves)

# The arena will set `legal_moves` before invoking `policy`.
# Example (not part of the submitted file):
# legal_moves = ['e2e4', 'g1f3', ...]
# move = policy(current_board, 'white')
