
import numpy as np
import random

# ----------------------------------------------------------------------------
#  Directions for queen‑like moves (N, NE, E, SE, S, SW, W, NW)
# ----------------------------------------------------------------------------
DIRS = [(-1, 0), (-1, 1), (0, 1), (1, 1),
        (1, 0), (1, -1), (0, -1), (-1, -1)]

BOARD_SIZE = 6

def _in_bounds(r, c):
    """True if (r,c) lies inside the 6×6 board."""
    return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE

# ----------------------------------------------------------------------------
#  Move generation
# ----------------------------------------------------------------------------
def _generate_moves(board, player):
    """
    Return a list of all legal moves for `player`.
    Each move is a tuple (from_r, from_c, to_r, to_c, arr_r, arr_c).
    """
    moves = []
    # locate all amazons belonging to the player
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r, c] != player:
                continue
            # try every direction for the amazon's move
            for dr, dc in DIRS:
                nr, nc = r + dr, c + dc
                while _in_bounds(nr, nc) and board[nr, nc] == 0:   # empty target
                    # ----- apply the move to a temporary board -----
                    tmp = board.copy()
                    tmp[r, c] = 0
                    tmp[nr, nc] = player

                    # ----- generate all arrow shots from the landing square -----
                    for adr, adc in DIRS:
                        ar, ac = nr + adr, nc + adc
                        while _in_bounds(ar, ac):
                            if tmp[ar, ac] != 0:        # blocked – cannot shoot further
                                break
                            # legal arrow landing square (empty)
                            moves.append((r, c, nr, nc, ar, ac))
                            ar += adr
                            ac += adc
                    # continue stepping in the same direction for the amazon move
                    nr += dr
                    nc += dc
    return moves

# ----------------------------------------------------------------------------
#  Board evaluation (mobility / territory heuristic)
# ----------------------------------------------------------------------------
def _reachable_squares(board, player):
    """Return a set of all empty squares reachable by queen moves from `player`'s amazons."""
    reachable = set()
    # positions of the player's amazons
    positions = [(r, c) for r in range(BOARD_SIZE)
                 for c in range(BOARD_SIZE) if board[r, c] == player]
    for r, c in positions:
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while _in_bounds(nr, nc) and board[nr, nc] == 0:
                reachable.add((nr, nc))
                nr += dr
                nc += dc
    return reachable

def _evaluate(board):
    """Higher values are better for player 1."""
    our = _reachable_squares(board, 1)
    opp = _reachable_squares(board, 2)

    our_excl = our - opp
    opp_excl = opp - our

    # raw mobility difference + bonus for exclusive territory
    return (len(our) - len(opp)) + 2 * (len(our_excl) - len(opp_excl))

# ----------------------------------------------------------------------------
#  Policy entry point
# ----------------------------------------------------------------------------
def policy(board):
    """
    `board` – 6×6 numpy array, values: 0 empty, 1 our amazon,
               2 opponent amazon, -1 arrow.
    Returns a move string "fr,fc:tr,tc:ar,ac" (0‑based coordinates).
    """
    # ---- 1. generate all legal moves for us (player = 1) ----
    moves = _generate_moves(board, player=1)

    # ---- 2. fallback – should never be needed, but guarantees a legal move ----
    if not moves:
        # Scan the board manually to find at least one legal move.
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board[r, c] != 1:
                    continue
                for dr, dc in DIRS:
                    nr, nc = r + dr, c + dc
                    while _in_bounds(nr, nc) and board[nr, nc] == 0:
                        # temporary board after the amazon moves
                        tmp = board.copy()
                        tmp[r, c] = 0
                        tmp[nr, nc] = 1
                        # try any arrow shot from the new location
                        for adr, adc in DIRS:
                            ar, ac = nr + adr, nc + adc
                            while _in_bounds(ar, ac):
                                if tmp[ar, ac] != 0:
                                    break
                                # a legal move was found – return it immediately
                                return f"{r},{c}:{nr},{nc}:{ar},{ac}"
                            # continue scanning arrow directions
                        nr += dr
                        nc += dc
        # if we reach this point there really is no legal move – the environment
        # promises not to call us, but we raise to avoid returning garbage.
        raise RuntimeError("policy: no legal move exists")

    # ---- 3. evaluate every candidate move and keep the best ones ----
    best_score = -np.inf
    best_moves = []

    for mv in moves:
        fr, fc, tr, tc, ar, ac = mv
        # construct the board that results after playing this move
        tmp = board.copy()
        tmp[fr, fc] = 0
        tmp[tr, tc] = 1
        tmp[ar, ac] = -1

        score = _evaluate(tmp)
        if score > best_score:
            best_score = score
            best_moves = [mv]
        elif score == best_score:
            best_moves.append(mv)

    # ---- 4. choose uniformly among the top‑scoring moves ----
    # (randomness makes the policy less predictable)
    chosen = random.choice(best_moves)
    fr, fc, tr, tc, ar, ac = chosen
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"
