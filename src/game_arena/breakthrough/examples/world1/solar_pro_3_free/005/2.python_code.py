
from typing import List, Tuple, Set, Optional
import random

WIN_SCORE = 10_000

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def opposite_color(c: str) -> str:
    """Return the opposite player colour."""
    return 'w' if c == 'b' else 'b'


def distance_to_home(row: int, color: str) -> int:
    """How many forward squares a piece needs to reach the opponent’s home row."""
    return row if color == 'b' else 7 - row


def forward_empty_squares(piece: Tuple[int, int],
                         own_set: Set[Tuple[int, int]],
                         opp_set: Set[Tuple[int, int]],
                         dr: int) -> List[Tuple[int, int]]:
    """All squares reachable by a forward step that are empty."""
    r, c = piece
    results: List[Tuple[int, int]] = []
    # straight forward
    nr, nc = r + dr, c
    if 0 <= nr <= 7 and 0 <= nc <= 7:
        if (nr, nc) not in own_set and (nr, nc) not in opp_set:
            results.append((nr, nc))
    # diagonal forward left / right
    for dc in (-1, 1):
        nr, nc = r + dr, c + dc
        if 0 <= nr <= 7 and 0 <= nc <= 7:
            if (nr, nc) not in own_set and (nr, nc) not in opp_set:
                results.append((nr, nc))
    return results


def own_trapped(pieces: List[Tuple[int, int]],
                own_set: Set[Tuple[int, int]],
                opp_set: Set[Tuple[int, int]],
                dr: int) -> int:
    """Count own pieces with zero forward‑empty squares."""
    cnt = 0
    for p in pieces:
        if len(forward_empty_squares(p, own_set, opp_set, dr)) == 0:
            cnt += 1
    return cnt


def opp_trapped(pieces: List[Tuple[int, int]],
                own_set: Set[Tuple[int, int]],
                opp_set: Set[Tuple[int, int]],
                dr: int) -> int:
    """Count opponent pieces with zero forward‑empty squares."""
    cnt = 0
    for p in pieces:
        if len(forward_empty_squares(p, own_set, opp_set, dr)) == 0:
            cnt += 1
    return cnt


def generate_moves(me: List[Tuple[int, int]],
                  opp: List[Tuple[int, int]],
                  dr: int) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
    """Return all legal forward or diagonal‑forward moves (including captures)."""
    own_set = set(me)
    opp_set = set(opp)
    moves: List[Tuple[Tuple[int, int], Tuple[int, int]]] = []

    for r, c in me:
        for to_row, to_col in [(r + dr, c), (r + dr, c - 1), (r + dr, c + 1)]:
            if 0 <= to_row <= 7 and 0 <= to_col <= 7:
                if (to_row, to_col) in opp_set:          # capture
                    moves.append(((r, c), (to_row, to_col)))
                else:                                   # empty square
                    moves.append(((r, c), (to_row, to_col)))
    return moves


# ----------------------------------------------------------------------
# Static evaluation
# ----------------------------------------------------------------------
def evaluate(me: List[Tuple[int, int]],
            opp: List[Tuple[int, int]],
            color: str) -> int:
    """Return a numeric score: higher is better for the player to move."""
    # immediate win / opponent empty
    target = 0 if color == 'b' else 7
    for r, _ in me:
        if r == target:
            return WIN_SCORE
    if not opp:
        return WIN_SCORE

    own_set = set(me)
    opp_set = set(opp)
    dr = -1 if color == 'b' else 1

    # basic distance scores
    self_dist = sum(distance_to_home(r, color) for r, _ in me)
    opp_dist = sum(distance_to_home(r, color) for r, _ in opp)

    # capture bonuses / penalties
    own_captures = sum(1
                       for r, c in me
                       for dc in (-1, 1)
                       if 0 <= r + dr <= 7 and 0 <= c + dc <= 7
                          and (r + dr, c + dc) in opp_set)
    self_dist += own_captures                      # more capture chances → better

    opp_captures = sum(1
                       for r, c in opp
                       for dc in (-1, 1)
                       if 0 <= r + dr <= 7 and 0 <= c + dc <= 7
                          and (r + dr, c + dc) in own_set)
    opp_dist -= opp_captures                       # opponent capture ability → worse

    # piece trapping penalty (large)
    own_trapped = own_trapped(me, own_set, opp_set, dr)
    opp_trapped = opp_trapped(opp, own_set, opp_set, dr)
    self_dist -= own_trapped * 5                     # heavy penalty for own trapped
    opp_dist -= opp_trapped * 5                     # reward opponent trapped

    # forward mobility – a small reward for having many empty forward squares
    self_mob = sum(len(forward_empty_squares(p, own_set, opp_set, dr))
                   for p in me)
    self_dist += self_mob * 0.1                     # bonus for mobility

    opp_mob = sum(len(forward_empty_squares(p, own_set, opp_set, dr))
                 for p in opp)
    opp_dist -= opp_mob * 0.1                       # penalty for opponent mobility

    return self_dist - opp_dist


# ----------------------------------------------------------------------
# Minimax with alpha‑beta pruning
# ----------------------------------------------------------------------
MAX_DEPTH = 5

def minimax(me: List[Tuple[int, int]],
            opp: List[Tuple[int, int]],
            color: str,
            depth: int,
            alpha: int,
            beta: int) -> Tuple[int, Optional[Tuple[Tuple[int, int], Tuple[int, int]]]]:
    """Depth‑limited minimax returning (score, best_move)."""
    target = 0 if color == 'b' else 7

    # Immediate win or opponent eliminated
    if any(r == target for r, _ in me) or not opp:
        return WIN_SCORE, None

    # Leaf node – use static evaluation
    if depth >= MAX_DEPTH:
        return evaluate(me, opp, color), None

    dr = -1 if color == 'b' else 1
    moves = generate_moves(me, opp, dr)

    best_move: Optional[Tuple[Tuple[int, int], Tuple[int, int]]] = None
    if color == 'b':
        best_score = -float('inf')
    else:
        best_score = float('inf')

    for move in moves:
        from_pos, to_pos = move
        # apply the move
        new_me = [p for p in me if p != from_pos] + [to_pos]
        new_opp = list(opp)
        if to_pos in new_opp:
            new_opp.remove(to_pos)

        # opponent’s turn
        child_score, _ = minimax(new_me, new_opp, opposite_color(color),
                                depth + 1, alpha, beta)

        # update best
        if color == 'b':
            if child_score > best_score:
                best_score = child_score
                best_move = move
        else:
            if child_score < best_score:
                best_score = child_score
                best_move = move

        # alpha‑beta prune
        if color == 'b':
            alpha = max(alpha, best_score)
        else:
            beta = min(beta, best_score)
        if alpha >= beta:
            break

    # If no move found (should not happen), fall back to a random legal move
    if best_move is None and moves:
        best_move = random.choice(moves)

    return best_score, best_move


# ----------------------------------------------------------------------
# Public API required by the arena
# ----------------------------------------------------------------------
def policy(me: List[Tuple[int, int]],
          opp: List[Tuple[int, int]],
          color: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """
    Choose the best legal move for the current player.
    Returns ((from_row, from_col), (to_row, to_col)).
    """
    dr = -1 if color == 'b' else 1
    score, move = minimax(me, opp, color, depth=0, alpha=-WIN_SCORE,
                          beta= WIN_SCORE)

    # The minimax already guarantees a legal move; the fallback ensures one anyway.
    return move
