
import sys
sys.setrecursionlimit(10000)

# ------------------------------------------------------------
# Board geometry
ROWS, COLS = 5, 3
NUM_SQUARES = ROWS * COLS

# mapping (row,col) -> index and back
idx_to_rc = [(r, c) for r in range(1, ROWS + 1) for c in range(1, COLS + 1)]
rc_to_idx = {(r, c): idx for idx, (r, c) in enumerate(idx_to_rc)}

# knight moves (L shape)
KNIGHT_OFFSETS = [(2, 1), (2, -1), (-2, 1), (-2, -1),
                  (1, 2), (1, -2), (-1, 2), (-1, -2)]

# pre‑compute reachable squares for every square
POSSIBLE_MOVES = []
for r in range(1, ROWS + 1):
    for c in range(1, COLS + 1):
        idx = rc_to_idx[(r, c)]
        moves = []
        for dr, dc in KNIGHT_OFFSETS:
            nr, nc = r + dr, c + dc
            if 1 <= nr <= ROWS and 1 <= nc <= COLS:
                moves.append(rc_to_idx[(nr, nc)])
        POSSIBLE_MOVES.append(moves)

# ------------------------------------------------------------
# DP with memoisation
from functools import lru_cache

@lru_cache(maxsize=None)
def dp(knight_idx: int, mask: int, k: int):
    """
    Returns (best_captures, best_move) where best_move is a destination index
    or -1 for a 'tick' (pass).  k is the number of moves still available.
    """
    if k == 0:
        return (0, -1)

    best_val = 0
    best_move = -1  # -1 means tick

    # option 1: tick (pass)
    val_tick, _ = dp(knight_idx, mask, k - 1)
    if val_tick > best_val:
        best_val = val_tick
        best_move = -1

    # option 2: all knight jumps
    for dest in POSSIBLE_MOVES[knight_idx]:
        capture = (mask >> dest) & 1
        new_mask = mask & ~(1 << dest) if capture else mask
        val, _ = dp(dest, new_mask, k - 1)
        val += capture
        if val > best_val:
            best_val = val
            best_move = dest

    return (best_val, best_move)

# ------------------------------------------------------------
def parse_state(state, role):
    """Extract knight index, pawn mask and current step for the given role."""
    knight_idx = None
    pawn_mask = 0
    step = 0
    for fact in state:
        if not isinstance(fact, list) or len(fact) < 2:
            continue
        if fact[0] == "cell" and fact[1] == role:
            r = int(fact[2])
            c = int(fact[3])
            piece = fact[4]
            idx = (r - 1) * COLS + (c - 1)
            if piece == "knight":
                knight_idx = idx
            elif piece == "pawn":
                pawn_mask |= (1 << idx)
        elif fact[0] == "step":
            step = int(fact[1])
    return knight_idx, pawn_mask, step

def policy(state, role):
    # -----------------------------------------------------------------
    # 1. Parse the current situation for the requested role
    knight_idx, pawn_mask, step = parse_state(state, role)
    if knight_idx is None:
        # Should never happen; fallback to tick
        return "tick"

    # -----------------------------------------------------------------
    # 2. Determine how many moves remain for this player
    #    step counts total moves performed so far (including the move that
    #    led to this state).  Left moves on odd steps, right on even steps.
    if role == "left":
        used = (step + 1) // 2
    else:
        used = step // 2
    remaining = max(0, 16 - used)

    # If no moves left, we can only pass
    if remaining == 0:
        return "tick"

    # -----------------------------------------------------------------
    # 3. Query the DP for the optimal move
    _, best_move = dp(knight_idx, pawn_mask, remaining)

    # -----------------------------------------------------------------
    # 4. Produce the action string
    if best_move == -1:
        return "tick"
    else:
        r, c = idx_to_rc[knight_idx]
        nr, nc = idx_to_rc[best_move]
        return f"move({role},{r},{c},{nr},{nc})"
