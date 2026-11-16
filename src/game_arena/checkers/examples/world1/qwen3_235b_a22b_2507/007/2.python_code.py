
import random
from typing import Tuple, List, Optional, Generator

# Type alias for square
Square = Tuple[int, int]

# Directions as (dr, dc)
DIRECTIONS = [(-1, -1), (-1, 1), (1, -1), (1, 1)]  # NE, NW, SE, SW for black and white

# Precompute valid dark squares
DARK_SQUARES = {(r, c) for r in range(8) for c in range(8) if (r + c) % 2 == 1}

def is_valid(square: Square) -> bool:
    """Check if square is within bounds and dark."""
    r, c = square
    return (0 <= r < 8) and (0 <= c < 8) and ((r + c) % 2 == 1)

def is_back_rank(square: Square, color: str) -> bool:
    """Check if the piece is on the opponent's back rank (promotion row)."""
    r, c = square
    return (color == 'b' and r == 7) or (color == 'w' and r == 0)

def is_edge(square: Square) -> bool:
    """Check if square is on edge of board."""
    r, c = square
    return r in (0, 7) or c in (0, 7)

def get_directions(color: str) -> List[Square]:
    """Get movement directions for color. Black goes up (r-), white goes down (r+)"""
    if color == 'b':
        return [(-1, -1), (-1, 1)]  # Up-left, up-right
    else:
        return [(1, -1), (1, 1)]    # Down-left, down-right

def get_opponent_directions(color: str) -> List[Square]:
    """Get directions the opponent can move (to check threats)."""
    return get_directions('w' if color == 'b' else 'b')

def man_moves(square: Square, color: str, occupancies: set) -> Generator[Square, None, None]:
    """Generate all valid man moves (non-captures) from square."""
    directions = get_directions(color)
    r, c = square
    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        if is_valid((nr, nc)) and (nr, nc) not in occupancies:
            yield (nr, nc)

def man_captures(square: Square, color: str, my_pieces: set, opp_pieces: set) -> Generator[Tuple[Square, Square], None, None]:
    """Generate all valid man captures from square. Returns ((via), (to))"""
    directions = get_directions(color)
    r, c = square
    for dr, dc in directions:
        # One step to opponent
        mr, mc = r + dr, c + dc
        # Second step to empty
        tr, tc = mr + dr, mc + dc
        if is_valid((mr, mc)) and is_valid((tr, tc)) and \
           (mr, mc) in opp_pieces and (tr, tc) not in my_pieces and (tr, tc) not in opp_pieces:
            yield ((mr, mc), (tr, tc))

def king_moves(square: Square, my_pieces: set, opp_pieces: set) -> Generator[Square, None, None]:
    """Generate all valid king moves (non-captures) from square."""
    r, c = square
    for dr, dc in DIRECTIONS:
        nr, nc = r + dr, c + dc
        while is_valid((nr, nc)) and (nr, nc) not in my_pieces and (nr, nc) not in opp_pieces:
            yield (nr, nc)
            nr, nc = nr + dr, nc + dc

def king_captures(square: Square, my_pieces: set, opp_pieces: set) -> Generator[Tuple[Square, Square], None, None]:
    """Generate all valid king captures from square. Returns ((via), (to))"""
    r, c = square
    for dr, dc in DIRECTIONS:
        # First, scan in direction
        nr, nc = r + dr, c + dc
        # Find first opponent piece
        while is_valid((nr, nc)) and (nr, nc) not in my_pieces and (nr, nc) not in opp_pieces:
            nr, nc = nr + dr, nc + dc
        if is_valid((nr, nc)) and (nr, nc) in opp_pieces:
            # Then check one step beyond
            tr, tc = nr + dr, nc + dc
            while is_valid((tr, tc)) and (tr, tc) not in my_pieces and (tr, tc) not in opp_pieces:
                # Found a capture landing
                yield ((nr, nc), (tr, tc))
                tr, tc = tr + dr, tc + dc

def can_capture_man(square: Square, color: str, my_pieces: set, opp_pieces: set) -> bool:
    """Check if a man can capture."""
    return next(man_captures(square, color, my_pieces, opp_pieces), None) is not None

def can_capture_king(square: Square, my_pieces: set, opp_pieces: set) -> bool:
    """Check if a king can capture."""
    return next(king_captures(square, my_pieces, opp_pieces), None) is not None

def generate_moves(mymen: List[Square], mykings: List[Square], oppmen: List[Square], oppkings: List[Square], color: str) -> List[Tuple[Square, Square]]:
    """Generate all legal moves. Returns list of (from, to) moves."""
    my_pieces = set(mymen + mykings)
    opp_pieces = set(oppmen + oppkings)
    all_pieces = my_pieces | opp_pieces

    moves = []

    # First, check if ANY capture is possible
    has_capture = False
    for sq in mymen:
        if can_capture_man(sq, color, my_pieces, opp_pieces):
            has_capture = True
            break
    if not has_capture:
        for sq in mykings:
            if can_capture_king(sq, my_pieces, opp_pieces):
                has_capture = True
                break

    # Generate captures only if capture is mandatory
    if has_capture:
        # Men captures
        for sq in mymen:
            for via, to in man_captures(sq, color, my_pieces, opp_pieces):
                moves.append((sq, to))
        # Kings captures
        for sq in mykings:
            for via, to in king_captures(sq, my_pieces, opp_pieces):
                moves.append((sq, to))
    else:
        # Non-captures
        for sq in mymen:
            for to in man_moves(sq, color, all_pieces):
                moves.append((sq, to))
        for sq in mykings:
            for to in king_moves(sq, my_pieces, opp_pieces):
                moves.append((sq, to))

    return moves

def will_promote(from_sq: Square, to_sq: Square, color: str) -> bool:
    """Check if move promotes a man to king."""
    fr, _ = from_sq
    tr, _ = to_sq
    if color == 'b':
        return fr < 7 and tr == 7
    else:
        return fr > 0 and tr == 0

def evaluate(mymen: List[Square], mykings: List[Square], oppmen: List[Square], oppkings: List[Square], color: str) -> float:
    """Evaluate the board state from player's perspective."""
    opp_color = 'w' if color == 'b' else 'b'

    score = 0.0

    # Piece values
    score += 100 * len(mymen)
    score += 150 * len(mykings)
    score -= 100 * len(oppmen)
    score -= 150 * len(oppkings)

    # Positional bonuses for men: closer to promotion is better
    for r, c in mymen:
        if color == 'b':
            dist = 7 - r
            score += (7 - dist) * 5  # More points the closer to row 7
            if is_back_rank((r, c), color):
                score += 20
        else:
            dist = r
            score += (7 - dist) * 5
            if is_back_rank((r, c), color):
                score += 20

    # Opponent men: penalize if close to promotion
    for r, c in oppmen:
        if color == 'b':
            dist = r  # Distance to row 0 for white
            score -= (7 - dist) * 5
        else:
            dist = 7 - r  # Distance to row 7 for black
            score -= (7 - dist) * 5

    # Kings: prefer central control, avoid danger
    for r, c in mykings:
        if color == 'b':
            if r > 4:
                score += 5  # Safe for black king if in top half
        else:
            if r < 4:
                score += 5  # Safe for white king in bottom half
        # Edge bonus for king safety
        if is_edge((r, c)):
            score += 5

    # Mobility bonus: count future moves
    # We don't want to call generate_moves here for performance, so light approximation
    my_mob = 0
    opp_mob = 0
    my_pieces = set(mymen + mykings)
    opp_pieces = set(oppmen + oppkings)
    all_pieces = my_pieces | opp_pieces

    # Simple lookahead: count immediate non-capture options
    for sq in mymen:
        my_mob += len(list(man_moves(sq, color, all_pieces)))
    for sq in mykings:
        my_mob += len(list(king_moves(sq, my_pieces, opp_pieces)))
    for sq in oppmen:
        opp_mob += len(list(man_moves(sq, opp_color, all_pieces)))
    for sq in oppkings:
        opp_mob += len(list(king_moves(sq, opp_pieces, my_pieces)))

    score += (my_mob - opp_mob) * 2

    # King formation incentive
    if len(mykings) == 0 and len(mymen) > 0:
        # If about to promote, add incentive
        for sq in mymen:
            if will_promote(sq, (sq[0] + (1 if color == 'w' else -1), sq[1] + 1), color) or \
               will_promote(sq, (sq[0] + (1 if color == 'w' else -1), sq[1] - 1), color):
                score += 8

    return score

def apply_move(mymen: List[Square], mykings: List[Square], oppmen: List[Square], oppkings: List[Square],
                from_sq: Square, to_sq: Square, color: str) -> Tuple[List[Square], List[Square], List[Square], List[Square]]:
    """Apply a move and return new state. Does NOT validate move."""
    mymen = mymen.copy()
    mykings = mykings.copy()
    oppmen = oppmen.copy()
    oppkings = oppkings.copy()

    # Determine if captured
    capture = False
    cap_sq = None
    fr, fc = from_sq
    tr, tc = to_sq

    # Detect capture: distance > 1
    if abs(tr - fr) > 1:
        capture = True
        mid_r = (fr + tr) // 2
        mid_c = (fc + tc) // 2
        cap_sq = (mid_r, mid_c)

        # Remove opponent piece
        if cap_sq in oppmen:
            oppmen.remove(cap_sq)
        elif cap_sq in oppkings:
            oppkings.remove(cap_sq)

    # Move piece
    if from_sq in mymen:
        mymen.remove(from_sq)
        if will_promote(from_sq, to_sq, color):
            mykings.append(to_sq)
        else:
            mymen.append(to_sq)
    elif from_sq in mykings:
        mykings.remove(from_sq)
        mykings.append(to_sq)
    else:
        raise ValueError(f"Invalid from_sq {from_sq}")

    return mymen, mykings, oppmen, oppkings

def minimax(mymen: List[Square], mykings: List[Square], oppmen: List[Square], oppkings: List[Square],
            color: str, depth: int, alpha: float, beta: float, maximizing: bool) -> float:
    """Minimax with alpha-beta pruning. Returns evaluation."""
    if depth == 0:
        return evaluate(mymen, mykings, oppmen, oppkings, 'b' if maximizing else 'w')

    moves = generate_moves(mymen, mykings, oppmen, oppkings, color if maximizing else ('w' if color == 'b' else 'b'))

    if not moves:
        return -10000 if maximizing else 10000  # Losing state

    # Move ordering: captures first, promotion next, rest
    def move_score(move):
        from_sq, to_sq = move
        score = 0
        # Capture is high priority
        fr, fc = from_sq
        tr, tc = to_sq
        if abs(tr - fr) > 1:
            score += 100
        if will_promote(from_sq, to_sq, color if maximizing else ('w' if color == 'b' else 'b')):
            score += 50
        return score

    moves.sort(key=move_score, reverse=True)

    if maximizing:
        value = float('-inf')
        for move in moves:
            new_mymen, new_mykings, new_oppmen, new_oppkings = apply_move(
                mymen, mykings, oppmen, oppkings, move[0], move[1], color)
            v = minimax(new_oppmen, new_oppkings, new_mymen, new_mykings,
                        ('w' if color == 'b' else 'b'), depth - 1, alpha, beta, False)
            value = max(value, v)
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value
    else:
        value = float('inf')
        for move in moves:
            new_mymen, new_mykings, new_oppmen, new_oppkings = apply_move(
                oppmen, oppkings, mymen, mykings, move[0], move[1], 'w' if color == 'b' else 'b')
            v = minimax(new_mymen, new_mykings, new_oppmen, new_oppkings,
                        color, depth - 1, alpha, beta, True)
            value = min(value, v)
            beta = min(beta, value)
            if beta <= alpha:
                break
        return value

def policy(mymen: List[Square], mykings: List[Square], oppmen: List[Square], oppkings: List[Square], color: str) -> Tuple[Square, Square]:
    """
    Main policy function that returns the best move.
    """
    moves = generate_moves(mymen, mykings, oppmen, oppkings, color)
    if not moves:
        # Should not happen, but fallback
        # Try to return any piece moving forward
        my_pieces = mymen + mykings
        for sq in my_pieces:
            r, c = sq
            drs = get_directions(color)
            for dr, dc in drs:
                nr, nc = r + dr, c + dc
                if is_valid((nr, nc)) and (nr, nc) not in (set(mymen + mykings + oppmen + oppkings)):
                    return (sq, (nr, nc))
        # Last resort: return first piece to same place (invalid but safe)
        if my_pieces:
            return (my_pieces[0], my_pieces[0])
        return ((0, 0), (0, 0))

    # If only one move, return it
    if len(moves) == 1:
        return moves[0]

    # Determine search depth based on move count (to stay under time)
    branching = len(moves)
    depth = 6
    if branching > 10:
        depth = 4
    elif branching > 5:
        depth = 5

    best_move = moves[0]
    best_value = float('-inf')

    # Move ordering for root
    def root_move_score(move):
        score = 0
        fr, fc = move[0]
        tr, tc = move[1]
        # Capture high priority
        if abs(tr - fr) > 1:
            score += 100
        # Promotion
        if will_promote(move[0], move[1], color):
            score += 50
        return score

    moves.sort(key=root_move_score, reverse=True)

    # Start minimax search
    for move in moves:
        new_mymen, new_mykings, new_oppmen, new_oppkings = apply_move(mymen, mykings, oppmen, oppkings, move[0], move[1], color)
        value = minimax(new_oppmen, new_oppkings, new_mymen, new_mykings, 'w' if color == 'b' else 'b', depth - 1, float('-inf'), float('inf'), False)
        if value > best_value:
            best_value = value
            best_move = move

    return best_move
