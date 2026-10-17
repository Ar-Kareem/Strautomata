
import random
from typing import List, Tuple, Set

# Type aliases for clarity
Square = Tuple[int, int]
Move = Tuple[Square, Square]

# Directions for moves: (drow, dcol)
# For black men (moving downwards) forward is -1 row, for white men forward is +1 row.
BLACK_FORWARD = [(-1, -1), (-1, 1)]
WHITE_FORWARD = [(1, -1), (1, 1)]
KING_DIRECTIONS = [(-1, -1), (-1, 1), (1, -1), (1, 1)]

def inside(r: int, c: int) -> bool:
    return 0 <= r < 8 and 0 <= c < 8

def is_dark(r: int, c: int) -> bool:
    # (0,0) is a dark square according to the spec
    return (r + c) % 2 == 1

def occupied(square: Square,
             my_men: Set[Square], my_kings: Set[Square],
             opp_men: Set[Square], opp_kings: Set[Square]) -> bool:
    return (square in my_men or square in my_kings or
            square in opp_men or square in opp_kings)

def opponent_pieces(opp_men: Set[Square], opp_kings: Set[Square]) -> Set[Square]:
    return opp_men | opp_kings

def my_pieces(my_men: Set[Square], my_kings: Set[Square]) -> Set[Square]:
    return my_men | my_kings

def generate_captures(piece: Square,
                      is_king: bool,
                      my_men: Set[Square], my_kings: Set[Square],
                      opp_men: Set[Square], opp_kings: Set[Square],
                      color: str,
                      visited_opps: Set[Square]) -> List[List[Square]]:
    """
    Return a list of capture paths. Each path is a list of squares, starting with the
    original piece square, then the landing squares after each jump.
    """
    dirs = KING_DIRECTIONS if is_king else (BLACK_FORWARD if color == 'b' else WHITE_FORWARD)
    captures = []

    for dr, dc in dirs:
        over_r, over_c = piece[0] + dr, piece[1] + dc
        landing_r, landing_c = piece[0] + 2 * dr, piece[1] + 2 * dc
        over = (over_r, over_c)
        landing = (landing_r, landing_c)

        if (inside(*over) and inside(*landing) and
                is_dark(*over) and is_dark(*landing) and
                not occupied(landing, my_men, my_kings, opp_men, opp_kings) and
                over in opponent_pieces(opp_men, opp_kings) and
                over not in visited_opps):
            # Perform the capture virtually
            new_my_men = set(my_men)
            new_my_kings = set(my_kings)
            new_opp_men = set(opp_men)
            new_opp_kings = set(opp_kings)

            # Remove captured opponent piece
            if over in new_opp_men:
                new_opp_men.remove(over)
            else:
                new_opp_kings.remove(over)

            # Move our piece
            new_piece = landing

            # Continue searching for further jumps
            further = generate_captures(
                new_piece, is_king,
                new_my_men, new_my_kings,
                new_opp_men, new_opp_kings,
                color,
                visited_opps | {over})

            if further:
                for path in further:
                    captures.append([piece] + path)
            else:
                captures.append([piece, landing])

    return captures

def all_capture_moves(my_men: Set[Square], my_kings: Set[Square],
                     opp_men: Set[Square], opp_kings: Set[Square],
                     color: str) -> List[Move]:
    """Return a list of all legal capture moves (as single‑step moves, even for multi‑jumps)."""
    best_paths = []  # each element: (path list, move tuple)
    max_len = 0

    # men
    for man in my_men:
        paths = generate_captures(man, False, my_men, my_kings,
                                 opp_men, opp_kings, color, set())
        for p in paths:
            if len(p) < 2:
                continue
            captures = len(p) - 1
            if captures > max_len:
                max_len = captures
                best_paths = [(p, (p[0], p[-1]))]
            elif captures == max_len:
                best_paths.append((p, (p[0], p[-1])))

    # kings
    for king in my_kings:
        paths = generate_captures(king, True, my_men, my_kings,
                                 opp_men, opp_kings, color, set())
        for p in paths:
            if len(p) < 2:
                continue
            captures = len(p) - 1
            if captures > max_len:
                max_len = captures
                best_paths = [(p, (p[0], p[-1]))]
            elif captures == max_len:
                best_paths.append((p, (p[0], p[-1])))

    # Return only the single‑step move (from, to) of each best path
    return [mv for _path, mv in best_paths] if best_paths else []

def generate_simple_moves(my_men: Set[Square], my_kings: Set[Square],
                          opp_men: Set[Square], opp_kings: Set[Square],
                          color: str) -> List[Move]:
    """Generate all non‑capture moves."""
    moves = []
    dirs_men = BLACK_FORWARD if color == 'b' else WHITE_FORWARD

    # men
    for man in my_men:
        for dr, dc in dirs_men:
            r, c = man[0] + dr, man[1] + dc
            if inside(r, c) and is_dark(r, c):
                dest = (r, c)
                if not occupied(dest, my_men, my_kings, opp_men, opp_kings):
                    moves.append((man, dest))

    # kings
    for king in my_kings:
        for dr, dc in KING_DIRECTIONS:
            r, c = king[0] + dr, king[1] + dc
            if inside(r, c) and is_dark(r, c):
                dest = (r, c)
                if not occupied(dest, my_men, my_kings, opp_men, opp_kings):
                    moves.append((king, dest))

    return moves

def opponent_can_capture(target: Square,
                         my_men: Set[Square], my_kings: Set[Square],
                         opp_men: Set[Square], opp_kings: Set[Square],
                         opp_color: str) -> bool:
    """
    Return True if the opponent, given the current board,
    can capture a piece that would end on `target`.
    Used for a quick safety heuristic.
    """
    # Build a board where a hypothetical piece sits on `target`.
    # For safety we only need to know if opponent has any capture that lands on that square.
    # Iterate opponent pieces and see if they can jump onto target.
    dirs = KING_DIRECTIONS if opp_color == 'w' else KING_DIRECTIONS  # opponent king moves both ways
    opp_forward = WHITE_FORWARD if opp_color == 'w' else BLACK_FORWARD

    # Opponent men
    for opp in opp_men:
        dirs_piece = opp_forward
        for dr, dc in dirs_piece:
            over = (target[0] - dr, target[1] - dc)  # square opponent would jump from
            from_sq = (target[0] - 2*dr, target[1] - 2*dc)  # square opponent would start on
            if (inside(*from_sq) and inside(*over) and is_dark(*from_sq) and is_dark(*over)):
                if (from_sq in opp_men or from_sq in opp_kings) and \
                   (over in my_men or over in my_kings) and \
                   not occupied(target, my_men, my_kings, opp_men, opp_kings):
                    return True

    # Opponent kings
    for opp in opp_kings:
        for dr, dc in KING_DIRECTIONS:
            over = (target[0] - dr, target[1] - dc)
            from_sq = (target[0] - 2*dr, target[1] - 2*dc)
            if (inside(*from_sq) and inside(*over) and is_dark(*from_sq) and is_dark(*over)):
                if (from_sq in opp_men or from_sq in opp_kings) and \
                   (over in my_men or over in my_kings) and \
                   not occupied(target, my_men, my_kings, opp_men, opp_kings):
                    return True
    return False

def safe_moves(moves: List[Move],
               my_men: Set[Square], my_kings: Set[Square],
               opp_men: Set[Square], opp_kings: Set[Square],
               opp_color: str) -> List[Move]:
    """Filter moves to those whose destination square cannot be captured immediately."""
    safe = []
    for mv in moves:
        dest = mv[1]
        if not opponent_can_capture(dest,
                                    my_men, my_kings,
                                    opp_men, opp_kings,
                                    opp_color):
            safe.append(mv)
    return safe

def score_move(move: Move, color: str) -> int:
    """Simple heuristic: promote‑ward progress for men."""
    frm, to = move
    if color == 'b':
        # men move down (row decreases) – want smaller row values
        return -to[0]
    else:
        return to[0]

def policy(my_men: List[Square],
           my_kings: List[Square],
           opp_men: List[Square],
           opp_kings: List[Square],
           color: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """
    Returns a legal move for the current player.
    Captures are mandatory; if several capture sequences have the same length,
    the first in deterministic order is chosen.
    If no capture is possible, a simple safety heuristic decides the move.
    """
    # Convert lists to sets for O(1) membership tests
    my_men_set = set(my_men)
    my_kings_set = set(my_kings)
    opp_men_set = set(opp_men)
    opp_kings_set = set(opp_kings)

    # 1. Look for captures
    captures = all_capture_moves(my_men_set, my_kings_set,
                                 opp_men_set, opp_kings_set,
                                 color)
    if captures:
        # Deterministic selection – sort and pick first
        captures.sort()
        return captures[0]

    # 2. Generate simple moves
    simple_moves = generate_simple_moves(my_men_set, my_kings_set,
                                          opp_men_set, opp_kings_set,
                                          color)
    if not simple_moves:
        raise RuntimeError("No legal moves available – the policy cannot act.")

    # 3. Prefer safe moves
    opp_color = 'w' if color == 'b' else 'b'
    safe = safe_moves(simple_moves, my_men_set, my_kings_set,
                      opp_men_set, opp_kings_set, opp_color)
    candidates = safe if safe else simple_moves

    # 4. Rank by forward progress (men towards promotion) and deterministic order
    candidates.sort(key=lambda m: (score_move(m, color), m))
    return candidates[0]
