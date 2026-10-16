
import numpy as np
import random

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Directions a queen (and thus an amazon or arrow) can move.
DIRECTIONS = [
    (-1, 0), (1, 0),   # vertical
    (0, -1), (0, 1),   # horizontal
    (-1, -1), (-1, 1), # diagonals
    (1, -1), (1, 1)
]

# ----------------------------------------------------------------------
# Helpers for move generation and board manipulation
# ----------------------------------------------------------------------
def legal_moves(board, player):
    """
    Returns a list of all legal moves for `player` on `board`.

    Each move is a tuple ((from_r, from_c), (to_r, to_c), (arrow_r, arrow_c)).
    """
    rows, cols = board.shape
    moves = []

    # locate all amazons belonging to `player`
    for (r, c) in np.argwhere(board == player):
        # ---- queen moves for the "to" square ----
        for dr, dc in DIRECTIONS:
            nr, nc = r + dr, c + dc
            while 0 <= nr < rows and 0 <= nc < cols and board[nr, nc] == 0:
                # (nr,nc) is a valid destination.
                # Build the board as it looks after the amazon moves there.
                board_mod = board.copy()
                board_mod[r, c] = 0               # old square becomes empty
                board_mod[nr, nc] = player         # new square gets the amazon

                # ---- arrow shots from the destination ----
                for ar_dr, ar_dc in DIRECTIONS:
                    ar_r, ar_c = nr + ar_dr, nc + ar_dc
                    while 0 <= ar_r < rows and 0 <= ar_c < cols and board_mod[ar_r, ar_c] == 0:
                        # valid arrow landing square
                        moves.append(((r, c), (nr, nc), (ar_r, ar_c)))
                        ar_r += ar_dr
                        ar_c += ar_dc

                # continue moving the amazon further in the same direction
                nr += dr
                nc += dc

    return moves


def apply_move(board, move, player):
    """
    Returns a new board after playing `move`. `move` has the same format as
    returned by `legal_moves`.
    """
    (fr, fc), (tr, tc), (ar, ac) = move
    new_board = board.copy()
    new_board[fr, fc] = 0
    new_board[tr, tc] = player
    new_board[ar, ac] = -1               # arrow / blocked square
    return new_board


# ----------------------------------------------------------------------
# Evaluation heuristic (territory based)
# ----------------------------------------------------------------------
def reachable_squares(board, player):
    """
    Returns a boolean mask (shape board.shape) where an entry is True iff the
    corresponding empty square can be reached by a queen move from any amazon
    of `player`. Blocked squares (non‑zero) stop the ray.
    """
    rows, cols = board.shape
    reachable = np.zeros_like(board, dtype=bool)
    for (r, c) in np.argwhere(board == player):
        for dr, dc in DIRECTIONS:
            nr, nc = r + dr, c + dc
            while 0 <= nr < rows and 0 <= nc < cols:
                if board[nr, nc] != 0:
                    break
                reachable[nr, nc] = True
                nr += dr
                nc += dc
    return reachable


def evaluate(board, player):
    """
    Score the board from the perspective of `player`.
    Larger scores are better for `player`.
    """
    opponent = 3 - player
    reach_self = reachable_squares(board, player)
    reach_opp  = reachable_squares(board, opponent)

    # squares only reachable by one side (exclusive territory)
    exclusive_self = reach_self & ~reach_opp
    exclusive_opp  = reach_opp & ~reach_self

    # main component – exclusive territory
    score = exclusive_self.sum() - exclusive_opp.sum()

    # small tie‑breaker – overall mobility
    score += (reach_self.sum() - reach_opp.sum()) * 0.1
    return score


# ----------------------------------------------------------------------
# The policy required by the competition
# ----------------------------------------------------------------------
def policy(board):
    """
    Return a legal move string for the current player (1) on the given
    6×6 numpy board.
    """
    player = 1
    moves = legal_moves(board, player)

    # The environment promises that we always have at least one legal move,
    # but we keep a defensive fallback anyway.
    if not moves:
        raise RuntimeError("policy called with no legal moves available")

    best_score = None
    best_moves = []

    for mv in moves:
        next_board = apply_move(board, mv, player)
        sc = evaluate(next_board, player)

        if best_score is None or sc > best_score:
            best_score = sc
            best_moves = [mv]
        elif sc == best_score:
            best_moves.append(mv)

    # break ties randomly so the behaviour is less predictable
    chosen = random.choice(best_moves)

    (fr, fc), (tr, tc), (ar, ac) = chosen
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"
