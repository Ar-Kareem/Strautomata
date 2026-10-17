
import re
from typing import Dict, List

# Piece values (centipawn-style, scaled)
PIECE_VALUES = {
    'K': 100000,
    'Q': 900,
    'R': 500,
    'B': 330,
    'N': 320,
    'P': 100,
}

CENTER_SQUARES = {'d4', 'd5', 'e4', 'e5'}

def _extract_dest_square(move: str) -> str:
    """
    Extract the destination square (like 'e4') from algebraic move notation.
    Returns '' if no destination (e.g., pure O-O with no square).
    """
    # Search from end for pattern [a-h][1-8]
    for i in range(len(move)-1, 0, -1):
        if move[i] in '12345678' and move[i-1] in 'abcdefgh':
            return move[i-1:i+1]
    return ''

def _is_capture(move: str) -> bool:
    # Algebraic capture normally includes 'x', but sometimes destination contains opponent piece.
    return 'x' in move

def _promotion_piece(move: str) -> str:
    # Return promotion piece letter e.g. 'Q' or '' if no promotion
    m = re.search(r'=(Q|R|B|N)', move)
    return m.group(1) if m else ''

def policy(pieces: Dict[str, str], to_play: str, legal_moves: List[str]) -> str:
    """
    Select a move from legal_moves using heuristics:
    - Immediate mate (#) highest priority
    - Material captures valued by captured piece
    - Promotions strongly prioritized (queen best)
    - Checks given a small bonus
    - Castling small king-safety bonus
    - Center control small bonus
    Deterministic tiebreaking.
    """
    if not legal_moves:
        # Should not happen per problem statement, but return empty string defensively
        return ''

    color = 'w' if to_play == 'white' else 'b'
    opp_color = 'b' if color == 'w' else 'w'

    best_move = legal_moves[0]
    best_key = (-1e18, -1e18, -1e18, -1e18, 1e9)  # tuple for comparison

    for idx, move in enumerate(legal_moves):
        # Immediate mate
        if '#' in move:
            # Choose mate immediately; produce deterministic among mates by tie-break keys
            key = (1e9, 1e9, 1e9, 1e9, -idx)
            if key > best_key:
                best_key = key
                best_move = move
            continue

        score = 0.0
        captured_value = 0
        promo_rank = 0
        check_flag = 1 if '+' in move else 0

        # Promotion bonus
        promo = _promotion_piece(move)
        if promo:
            # Big bonus for promotions; reflect piece value
            captured_value += PIECE_VALUES.get(promo, 0)
            # additional promotion priority
            if promo == 'Q':
                promo_rank = 9000
            elif promo == 'R':
                promo_rank = 5000
            elif promo == 'B':
                promo_rank = 3300
            elif promo == 'N':
                promo_rank = 3000
            score += promo_rank

        # Extract destination square
        dest = _extract_dest_square(move)

        # Capture detection: prefer explicit 'x' and also check board occupancy
        is_cap = _is_capture(move)
        if dest:
            occ = pieces.get(dest)
            if occ:
                # If there's an opponent piece on the destination, it's a capture by movement even if 'x' absent
                if occ[0] == opp_color:
                    is_cap = True
                    # Value of captured piece
                    captured_value += PIECE_VALUES.get(occ[1], 0)
            else:
                # Handle some en-passant cases: when move includes 'x' but dest empty (hard to detect captured pawn square)
                if 'x' in move:
                    # If it's a pawn capture (starts with a-h), assume captured pawn value
                    if re.match(r'^[a-h]', move):
                        captured_value += PIECE_VALUES['P']

        # If capture detected, award material score
        if is_cap:
            # Captured_value is in piece-value units; scale to priority
            score += captured_value

        # Check bonus
        if check_flag:
            score += 50

        # Castling bonus for king safety
        if move.startswith('O-O'):
            score += 40

        # Center control: if destination is a central square
        if dest in CENTER_SQUARES:
            score += 20

        # Slight preference for moving knights/bishops out (development)
        # Infer moved piece: uppercase leading char indicates piece, else pawn
        moved_piece = ''
        if move and move[0] in 'KQRBN':
            moved_piece = move[0]
        else:
            moved_piece = 'P'
        if moved_piece in ('N', 'B'):
            score += 5

        # Compose deterministic key: higher is better.
        # key components: (score, captured_value, promo_rank, check_flag, -index)
        key = (score, captured_value, promo_rank, check_flag, -idx)

        if key > best_key:
            best_key = key
            best_move = move

    # Ensure returned move is legal
    if best_move not in legal_moves:
        return legal_moves[0]
    return best_move
