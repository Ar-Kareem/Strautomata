
import random
from typing import List, Tuple, Set

# ------------------------------------------------------------
# Helper utilities
# ------------------------------------------------------------
DIRS = [(-1, -1), (-1, 1), (1, -1), (1, 1)]  # NW, NE, SW, SE


def inside(r: int, c: int) -> bool:
    return 0 <= r < 8 and 0 <= c < 8


def dark_square(r: int, c: int) -> bool:
    # (0,0) is a playable dark square in the description
    return (r + c) % 2 == 0


def opponent(color: str) -> str:
    return 'w' if color == 'b' else 'b'


def promotion_row(color: str) -> int:
    return 0 if color == 'b' else 7


def forward_dirs(color: str) -> List[Tuple[int, int]]:
    """Directions a normal man may move in."""
    return [(-1, -1), (-1, 1)] if color == 'b' else [(1, -1), (1, 1)]


def all_dirs(color: str, king: bool) -> List[Tuple[int, int]]:
    """Directions a piece may move/capture in."""
    return DIRS if king else forward_dirs(color)


# ------------------------------------------------------------
# Capture generation (multi‑jump)
# ------------------------------------------------------------
def generate_captures(
    start: Tuple[int, int],
    king: bool,
    occupied: Set[Tuple[int, int]],
    opp: Set[Tuple[int, int]],
    color: str,
    visited: Set[Tuple[int, int]],
) -> List[List[Tuple[int, int]]]:
    """Return all capture sequences starting from *start*.
    Each sequence is a list of squares visited, including the start.
    """
    results = []
    r0, c0 = start
    dirs = all_dirs(color, king)

    any_jump = False
    for dr, dc in dirs:
        r_mid, c_mid = r0 + dr, c0 + dc
        r_lnd, c_lnd = r0 + 2 * dr, c0 + 2 * dc
        if not (inside(r_mid, c_mid) and inside(r_lnd, c_lnd)):
            continue
        mid_sq = (r_mid, c_mid)
        lnd_sq = (r_lnd, c_lnd)
        if mid_sq not in opp:
            continue
        if lnd_sq in occupied or not dark_square(*lnd_sq):
            continue

        any_jump = True
        # simulate the jump
        new_occupied = occupied.copy()
        new_occupied.remove(start)
        new_occupied.add(lnd_sq)
        new_opp = opp.copy()
        new_opp.remove(mid_sq)

        # If we land on promotion row, the piece becomes a king for the rest of the chain
        new_king = king or (lnd_sq[0] == promotion_row(color))

        sub_sequences = generate_captures(
            lnd_sq, new_king, new_occupied, new_opp, color, visited | {mid_sq}
        )
        if sub_sequences:
            for seq in sub_sequences:
                results.append([start] + seq)
        else:
            results.append([start, lnd_sq])

    if not any_jump:
        # no further jumps – this path ends here (already included by caller)
        pass
    return results


def all_capture_moves(
    my_men: List[Tuple[int, int]],
    my_kings: List[Tuple[int, int]],
    opp_men: List[Tuple[int, int]],
    opp_kings: List[Tuple[int, int]],
    color: str,
) -> List[Tuple[Tuple[int, int], Tuple[int, int], int]]:
    """
    Returns a list of possible capture moves.
    Each entry is (from_sq, to_sq, capture_count).
    """
    occupied = set(my_men + my_kings + opp_men + opp_kings)
    opp = set(opp_men + opp_kings)
    moves = []

    for piece in my_men:
        seqs = generate_captures(
            piece, king=False, occupied=occupied, opp=opp, color=color, visited=set()
        )
        for seq in seqs:
            if len(seq) >= 2:
                moves.append((seq[0], seq[-1], len(seq) - 1))

    for piece in my_kings:
        seqs = generate_captures(
            piece, king=True, occupied=occupied, opp=opp, color=color, visited=set()
        )
        for seq in seqs:
            if len(seq) >= 2:
                moves.append((seq[0], seq[-1], len(seq) - 1))

    return moves


# ------------------------------------------------------------
# Ordinary slide generation
# ------------------------------------------------------------
def slide_moves(
    my_men: List[Tuple[int, int]],
    my_kings: List[Tuple[int, int]],
    occupied: Set[Tuple[int, int]],
    color: str,
) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
    moves = []
    # men
    for r, c in my_men:
        for dr, dc in forward_dirs(color):
            nr, nc = r + dr, c + dc
            if inside(nr, nc) and dark_square(nr, nc) and (nr, nc) not in occupied:
                moves.append(((r, c), (nr, nc)))
    # kings
    for r, c in my_kings:
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if inside(nr, nc) and dark_square(nr, nc) and (nr, nc) not in occupied:
                moves.append(((r, c), (nr, nc)))
    return moves


def distance_to_promotion(r: int, color: str) -> int:
    return r if color == 'b' else 7 - r


def is_exposed(move: Tuple[Tuple[int, int], Tuple[int, int]],
               my_men: List[Tuple[int, int]],
               my_kings: List[Tuple[int, int]],
               opp_men: List[Tuple[int, int]],
               opp_kings: List[Tuple[int, int]],
               color: str) -> bool:
    """Return True if after performing *move* the landing piece could be captured
    by the opponent on their next turn."""
    # Simulate board after our move
    our_piece_from, our_piece_to = move
    new_my_men = [p for p in my_men if p != our_piece_from]
    new_my_kings = [p for p in my_kings if p != our_piece_from]

    # promotion?
    if our_piece_from in my_men and our_piece_to[0] == promotion_row(color):
        new_my_kings.append(our_piece_to)
    else:
        if our_piece_from in my_men:
            new_my_men.append(our_piece_to)
        else:
            new_my_kings.append(our_piece_to)

    occupied = set(new_my_men + new_my_kings + opp_men + opp_kings)

    # Opponent capture check: a single‑step capture is enough
    opp_color = opponent(color)
    opp_dirs = all_dirs(opp_color, king=False)  # we only need forward for men; kings handled later
    opp_all_dirs = DIRS

    # Check each opponent piece
    for opp_piece in opp_men + opp_kings:
        opp_is_king = opp_piece in opp_kings
        dirs = opp_all_dirs if opp_is_king else forward_dirs(opp_color)
        for dr, dc in dirs:
            r_mid, c_mid = opp_piece[0] + dr, opp_piece[1] + dc
            r_lnd, c_lnd = opp_piece[0] + 2 * dr, opp_piece[1] + 2 * dc
            if not (inside(r_mid, c_mid) and inside(r_lnd, c_lnd)):
                continue
            if (r_mid, c_mid) not in occupied:
                continue
            if (r_lnd, c_lnd) in occupied:
                continue
            # if the landed square is exactly where our piece moved to => we are capturable
            if (r_lnd, c_lnd) == our_piece_to:
                return True
    return False


# ------------------------------------------------------------
# Main policy function
# ------------------------------------------------------------
def policy(
    my_men: List[Tuple[int, int]],
    my_kings: List[Tuple[int, int]],
    opp_men: List[Tuple[int, int]],
    opp_kings: List[Tuple[int, int]],
    color: str,
) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """
    Returns a legal move for the current player.
    """
    # 1. Look for captures (mandatory)
    captures = all_capture_moves(my_men, my_kings, opp_men, opp_kings, color)
    if captures:
        # Choose the longest capture chain
        max_len = max(c[2] for c in captures)
        best = [c for c in captures if c[2] == max_len]

        # Prefer a capture that ends in the promotion row (if not already a king)
        promo_row = promotion_row(color)
        pref = [
            c for c in best
            if (c[0] not in my_kings) and (c[1][0] == promo_row)
        ]
        if pref:
            best = pref

        chosen = random.choice(best)
        return chosen[0], chosen[1]

    # 2. No capture – generate ordinary slides
    occupied = set(my_men + my_kings + opp_men + opp_kings)
    slides = slide_moves(my_men, my_kings, occupied, color)

    if not slides:
        # No legal move – return a dummy move (should never happen in a legal game)
        raise RuntimeError("No legal moves available")

    # Rank slides: first by distance to promotion (smaller is better)
    def slide_score(move):
        _, to_sq = move
        return distance_to_promotion(to_sq[0], color)

    slides.sort(key=slide_score)

    # Among the best distance moves, discard those that are immediately exposable
    best_dist = slide_score(slides[0])
    candidates = [m for m in slides if slide_score(m) == best_dist]

    safe = [m for m in candidates if not is_exposed(m, my_men, my_kings, opp_men, opp_kings, color)]
    if safe:
        return random.choice(safe)

    # fallback – pick any of the best‑distance moves
    return random.choice(candidates)
