
import re
from typing import Dict, Tuple, List

# Policy function required by the arena
def policy(pieces: dict, to_play: str, legal_moves: list, memory: dict) -> Tuple[str, dict]:
    """
    Select a move from legal_moves using a heuristic that favors mate, promotions,
    high-value captures, checks, castling, and central control.
    Returns (move, memory).
    """
    if not legal_moves:
        # As a fail-safe, though the problem states legal_moves will be provided
        return ("", memory or {})

    # Piece values for heuristic (for captured piece evaluation)
    values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 1000}

    # central squares preference
    central_squares = {'e4', 'd4', 'e5', 'd5', 'c4', 'f4', 'c5', 'f5', 'd5', 'e5'}

    # opponent color code in pieces dict
    opp_color = 'b' if to_play == 'white' else 'w'

    def find_last_square(move: str) -> str:
        # Find last occurrence of a square like 'e4' in the SAN move
        matches = re.findall(r'[a-h][1-8]', move)
        return matches[-1] if matches else None

    def moving_piece_type(move: str) -> str:
        # Determine moving piece type from SAN: K,Q,R,B,N => else pawn 'P'
        if move.startswith('O-O'):
            return 'K'
        c = move[0]
        if c in 'KQRBN':
            return c
        return 'P'

    def score_move(move: str) -> float:
        s = 0.0

        # Big priorities
        if '#' in move:
            s += 100000.0  # immediate mate
        if '=' in move:
            # Promotion: prefer to queen more strongly
            m = re.search(r'=(\w)', move)
            if m:
                promo = m.group(1).upper()
                if promo == 'Q':
                    s += 9000.0
                elif promo == 'R':
                    s += 2000.0
                elif promo in ('B', 'N'):
                    s += 1500.0
            else:
                s += 5000.0

        # Capture scoring
        is_capture = 'x' in move
        dest = find_last_square(move)
        if is_capture:
            # If destination square has a piece, use its type to score capture
            if dest and dest in pieces:
                piece_code = pieces[dest]  # e.g. 'bQ'
                # Only credit if it's opponent piece (should be)
                if piece_code and len(piece_code) == 2 and piece_code[0] == opp_color:
                    cap_type = piece_code[1].upper()
                    cap_value = values.get(cap_type, 1)
                    # Basic capture score: captured piece value squared-ish to favor high-value captures
                    s += 100.0 * cap_value
                    # Additional bonus for capturing queen/rook
                    if cap_type == 'Q':
                        s += 300.0
                    elif cap_type == 'R':
                        s += 120.0
                else:
                    # Unclear capture (e.g., en passant), assume pawn capture
                    s += 100.0 * values['P']
            else:
                # Destination empty in pieces (likely en passant), assume pawn capture
                s += 100.0 * values['P']

        # Check & check-giving
        if '+' in move:
            s += 50.0

        # Castling gives safety boost
        if move.startswith('O-O'):
            s += 40.0

        # Encourage central control and forward pawn moves:
        if dest:
            if dest in central_squares:
                s += 20.0
            # Bonus for advancing pawns toward opponent side
            mtype = moving_piece_type(move)
            if mtype == 'P':
                # Determine rank: file is dest[0], rank is int(dest[1])
                try:
                    rank = int(dest[1])
                    if to_play == 'white':
                        s += (rank - 2) * 2.0  # farther up board gives more score
                    else:
                        s += (7 - rank) * 2.0
                except:
                    pass

        # Minor heuristic to prefer piece moves (develop) over aimless pawn shuffles
        mtype = moving_piece_type(move)
        if mtype in ('N', 'B'):
            s += 5.0
        elif mtype == 'R':
            s += 3.0
        elif mtype == 'Q':
            s += 1.0

        # Slight tie-breaker using lexical order to keep deterministic
        # (will be applied externally by sorting)
        return s

    # Compute scores for all legal moves
    scored_moves: List[tuple] = []
    for mv in legal_moves:
        try:
            sc = score_move(mv)
        except Exception:
            sc = 0.0
        scored_moves.append((sc, mv))

    # Choose the highest scoring move. For deterministic tie-break, sort by (-score, move)
    scored_moves.sort(key=lambda x: (-x[0], x[1]))
    best_move = scored_moves[0][1]

    # Return the chosen move and memory (unchanged)
    return (best_move, memory or {})
