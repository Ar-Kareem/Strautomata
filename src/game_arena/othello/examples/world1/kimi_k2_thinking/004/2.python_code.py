
import numpy as np

# ----------------------------------------------------------------------
#  Constants
# ----------------------------------------------------------------------
# 8 directions as (dr, dc)
DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1),
              (0, -1),           (0, 1),
              (1, -1),  (1, 0),  (1, 1)]

# Classic Othello static board weights (higher = better for the occupant)
WEIGHTS = np.array([
    [100, -20, 10, 5, 5, 10, -20, 100],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [10, -2, 0, 0, 0, 0, -2, 10],
    [5, -2, 0, 0, 0, 0, -2, 5],
    [5, -2, 0, 0, 0, 0, -2, 5],
    [10, -2, 0, 0, 0, 0, -2, 10],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [100, -20, 10, 5, 5, 10, -20, 100]
], dtype=np.int32)

# Flatten for fast index look‑up
W = WEIGHTS.flatten()

# ----------------------------------------------------------------------
#  Helpers
# ----------------------------------------------------------------------
def board_to_bitboards(you: np.ndarray, opp: np.ndarray):
    """Convert 8×8 arrays to 64‑bit bitboards."""
    you_bb = 0
    opp_bb = 0
    for r in range(8):
        for c in range(8):
            idx = r * 8 + c
            if you[r, c]:
                you_bb |= 1 << idx
            if opp[r, c]:
                opp_bb |= 1 << idx
    return you_bb, opp_bb

def idx_to_algebraic(idx: int) -> str:
    col = idx % 8
    row = idx // 8
    return chr(ord('a') + col) + str(row + 1)

def algebraic_to_idx(s: str) -> int:
    col = ord(s[0]) - ord('a')
    row = int(s[1]) - 1
    return row * 8 + col

# ----------------------------------------------------------------------
#  Move generation
# ----------------------------------------------------------------------
def is_legal_move(pos: int, my_bb: int, opp_bb: int) -> bool:
    """True if placing a disc at pos flips at least one opponent disc."""
    r = pos // 8
    c = pos % 8
    for dr, dc in DIRECTIONS:
        nr = r + dr
        nc = c + dc
        if not (0 <= nr < 8 and 0 <= nc < 8):
            continue
        nidx = nr * 8 + nc
        if ((opp_bb >> nidx) & 1) == 0:
            continue                     # neighbour not an opponent disc
        # we have at least one opponent neighbour – keep scanning
        tr = nr + dr
        tc = nc + dc
        while 0 <= tr < 8 and 0 <= tc < 8:
            idx = tr * 8 + tc
            if ((my_bb >> idx) & 1):
                return True              # a bracket exists
            if ((opp_bb >> idx) & 1) == 0:
                break                    # empty square – no bracket
            tr += dr
            tc += dc
    return False

def legal_moves(my_bb: int, opp_bb: int):
    """All legal move indices for the player."""
    empties = (~(my_bb | opp_bb)) & 0xFFFFFFFFFFFFFFFF
    moves = []
    while empties:
        low = empties & -empties
        pos = low.bit_length() - 1
        if is_legal_move(pos, my_bb, opp_bb):
            moves.append(pos)
        empties &= empties - 1
    return moves

def legal_move_count(my_bb: int, opp_bb: int) -> int:
    """Number of legal moves (faster when we only need the count)."""
    empties = (~(my_bb | opp_bb)) & 0xFFFFFFFFFFFFFFFF
    cnt = 0
    while empties:
        low = empties & -empties
        pos = low.bit_length() - 1
        if is_legal_move(pos, my_bb, opp_bb):
            cnt += 1
        empties &= empties - 1
    return cnt

# ----------------------------------------------------------------------
#  Board update (placing a disc and flipping)
# ----------------------------------------------------------------------
def apply_move(pos: int, my_bb: int, opp_bb: int):
    """
    Return (new_my_bb, new_opp_bb) after the player places a disc at pos.
    All bracketed opponent discs are flipped.
    """
    # board after the new disc is placed (no flips yet)
    new_my = my_bb | (1 << pos)
    combined_flips = 0

    r = pos // 8
    c = pos % 8

    for dr, dc in DIRECTIONS:
        nr = r + dr
        nc = c + dc
        if not (0 <= nr < 8 and 0 <= nc < 8):
            continue
        nidx = nr * 8 + nc
        if ((opp_bb >> nidx) & 1) == 0:
            continue                     # no opponent adjacent in this direction

        # start the set of discs that would be flipped in this direction
        flip_mask = (1 << nidx)
        tr = nr + dr
        tc = nc + dc

        while 0 <= tr < 8 and 0 <= tc < 8:
            idx = tr * 8 + tc
            if ((new_my >> idx) & 1):    # our colour – bracket complete
                combined_flips |= flip_mask
                break
            if ((opp_bb >> idx) & 1) == 0:  # empty – bracket fails
                break
            # opponent disc – continue the line
            flip_mask |= (1 << idx)
            tr += dr
            tc += dc

    # apply all flips
    final_my = new_my | combined_flips
    final_opp = opp_bb & ~combined_flips
    return final_my, final_opp

# ----------------------------------------------------------------------
#  Position evaluation (static features)
# ----------------------------------------------------------------------
def evaluate(my_bb: int, opp_bb: int) -> float:
    """Higher values mean the position is better for the player."""
    # 1) static board weights
    static = 0
    bb = my_bb
    while bb:
        low = bb & -bb
        idx = low.bit_length() - 1
        static += W[idx]
        bb ^= low
    bb = opp_bb
    while bb:
        low = bb & -bb
        idx = low.bit_length() - 1
        static -= W[idx]
        bb ^= low

    # 2) mobility difference
    my_moves = legal_move_count(my_bb, opp_bb)
    opp_moves = legal_move_count(opp_bb, my_bb)
    mobility = (my_moves - opp_moves) * 10.0

    # 3) disc count difference (more important when the board is almost full)
    total = (my_bb.bit_count() + opp_bb.bit_count())
    fill = total / 64.0
    disc = (my_bb.bit_count() - opp_bb.bit_count()) * (5.0 * fill)

    return static + mobility + disc

# ----------------------------------------------------------------------
#  Move selection (2‑ply minimax)
# ----------------------------------------------------------------------
def best_move(my_bb: int, opp_bb: int, moves):
    """Return the move index that maximises the worst‑case evaluation."""
    best_val = -float('inf')
    best = moves[0]

    for mv in moves:
        # our move
        after_my, after_opp = apply_move(mv, my_bb, opp_bb)

        # opponent replies
        opp_replies = legal_moves(after_opp, after_my)
        if not opp_replies:
            # opponent must pass – evaluate the board after our move
            val = evaluate(after_my, after_opp)
        else:
            # opponent will pick the reply that is worst for us
            worst = float('inf')
            for ormv in opp_replies:
                after_opp2, after_my2 = apply_move(ormv, after_opp, after_my)
                val = evaluate(after_my2, after_opp2)
                if val < worst:
                    worst = val
            val = worst

        if val > best_val:
            best_val = val
            best = mv

    return best

# ----------------------------------------------------------------------
#  Public API – the only function that will be called by the arena
# ----------------------------------------------------------------------
def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """
    Return a legal move for the player (you) in algebraic notation
    (e.g. \"d3\") or \"pass\" if no move exists.
    """
    you_bb, opp_bb = board_to_bitboards(you, opponent)
    moves = legal_moves(you_bb, opp_bb)
    if not moves:
        return "pass"
    chosen = best_move(you_bb, opp_bb, moves)
    return idx_to_algebraic(chosen)
