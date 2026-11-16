
import numpy as np
import random
from collections import defaultdict

# ---- constants ----------------------------------------------------
# evaluation weights
WEIGHT_CORNERS = 30
WEIGHT_STABILITY = 2
WEIGHT_MOBILITY = 15
WEIGHT_DISCDIFF = 10
WEIGHT_POTENTIAL = 5

# alpha-beta depth (ply = two moves, we search 6 ply total)
MAX_DEPTH = 6

# transposition table size (holds board hash → (best_score, best_move))
TT_SIZE = 1024

# ---- helper functions --------------------------------------------

def move_to_idx(move: str):
    """'a4' → (row, col) where row 0 = rank 8, row 7 = rank 1."""
    col = ord(move[0]) - ord('a')
    row = int(move[1:]) - 1
    return row, col

def idx_to_move(row: int, col: int) -> str:
    return chr(col + ord('a')) + str(row + 1)

def any_dir(r, c):
    """Eight directions as (dr, dc)."""
    return [( -1, -1), ( -1, 0), ( -1, 1),
            ( 0, -1),           ( 0, 1),
            ( 1, -1), ( 1, 0), ( 1, 1)]

def get_moves(you: np.ndarray, opp: np.ndarray, player: int):
    """Return list of legal moves (as strings) for `player`."""
    moves = []
    for r in range(8):
        for c in range(8):
            if you[r, c] or opp[r, c]:
                continue
            # simulate placing player disc at (r,c)
            tmp_you = you.copy()
            tmp_you[r, c] = player
            # check 8 directions
            flips = 0
            for dr, dc in any_dir(r, c):
                cr, cc = r + dr, c + dc
                while 0 <= cr < 8 and 0 <= cc < 8 and opp[cr, cc] == player:
                    flips += 1
                    cr += dr
                    cc += dc
                if flips == 0:
                    break
            if flips > 0:
                moves.append(idx_to_move(r, c))
    return moves

def count_moves(you: np.ndarray, opp: np.ndarray):
    """Return (your_moves, opp_moves) tuple."""
    your = [mv for mv in get_moves(you, opp, 1) if mv]
    opp = [mv for mv in get_moves(you, opp, -1) if mv]
    return len(your), len(opp)

def corners(you: np.ndarray):
    """Corners are a1 (0,0), a8 (7,0), h1 (0,7), h8 (7,7)."""
    idx = [0, 7]
    score = 0
    for r in idx:
        for c in idx:
            score += you[r, c] * WEIGHT_CORNERS
    return score

def pair_stability(you: np.ndarray):
    """Stable disc pairs: count of opponent discs that will stay yours if opponent puts there."""
    # we count from each of our discs all reachable opponent discs in each direction
    stable = 0
    for dr, dc in any_dir():
        for r in range(8):
            for c in range(8):
                if you[r, c] == 1:          # our disc
                    # travel outward
                    cr, cc = r + dr, c + dc
                    while 0 <= cr < 8 and 0 <= cc < 8:
                        if you[cr, cc] == 0 and opp[cr, cc] == 1:
                            stable += 1
                        elif you[cr, cc] == 1:
                            break
                        else:  # opp disc that stops our travel
                            break
                        cr += dr
                        cc += dc
    return stable * WEIGHT_STABILITY

def mobility(you: np.ndarray, opp: np.ndarray):
    my, oppo = count_moves(you, opp)
    return (my - oppo) * WEIGHT_MOBILITY

def disc_diff(you: np.ndarray, opp: np.ndarray):
    return (you.sum() - opp.sum()) * WEIGHT_DISCDIFF

def potential(you: np.ndarray, opp: np.ndarray):
    """Number of opponent empty squares that would become yours on one capture."""
    # for each opponent disc, look outward in each direction; count empty cells reachable after a line of opponents
    pot = 0
    for dr, dc in any_dir():
        for r in range(8):
            for c in range(8):
                if opp[r, c] == 1:
                    cr, cc = r + dr, c + dc
                    while 0 <= cr < 8 and 0 <= cc < 8:
                        if you[cr, cc] == 1:  # found our disc -> a potential flip
                            pot += 1
                        elif opp[cr, cc] == 1:
                            pass   # continue line
                        else:   # empty cell stops line (cannot flip)
                            break
                        cr += dr
                        cc += dc
    return pot * WEIGHT_POTENTIAL

def evaluate(you: np.ndarray, opp: np.ndarray):
    """Simple weighted evaluation."""
    return (corners(you) + pair_stability(you) +
            mobility(you, opp) + disc_diff(you, opp) +
            potential(you, opp))

def board_hash(you: np.ndarray, opp: np.ndarray, turn: int):
    """Compact hashable representation for the transposition table."""
    # you & opp are 0/1; we also include whose turn it is (1 = us, -1 = opp)
    # 8*8*2 bits = 128 bits; pack into tuple for dict key
    return (int(you.tobytes(), 16) << 56) | (int(opp.tobytes(), 16) << 12) | (turn & 0b11)

# ---- symmetry handling -------------------------------------------

# Othello board has 4 symmetrical transformations that are legal moves:
#   - horizontal flip   (swap a<->h, b<->g, ... with row unchanged)
#   - vertical flip     (swap row 0<->7, 1<->6, ... with col unchanged)
#   - diagonal flip     (swap (r,c) ↔ (7-c,7-r))
#   - anti‑diagonal flip
# We canonicalize a board by applying a permutation that makes its
# lexicographically smallest representation first. This dramatically
# reduces the number of distinct positions the search examines.
# Below are the permutation indices for the 4 symmetries; they are applied
# to the board arrays (you and opp) to generate canonical forms.

SYM_TRANSFORM = {
    0b0000: lambda r, c: (r, c),                 # identity
    0b0001: lambda r, c: (c, r),                 # horizontal
    0b0010: lambda r, c: (7 - r, c),             # vertical
    0b0011: lambda r, c: (7 - c, 7 - r),         # diagonal
    0b0100: lambda r, c: (c, 7 - r),             # anti‑diagonal
    0b0101: lambda r, c: (7 - c, r),             # combine horizontal+vertical
    0b0110: lambda r, c: (7 - r, 7 - c),         # vertical+diagonal
    0b0111: lambda r, c: (7 - c, 7 - r),         # all three (same as diagonal)
    0b1000: lambda r, c: (7 - r, c),             # vertical (already)
    0b1001: lambda r, c: (7 - c, 7 - r),         # vertical+diagonal
    0b1010: lambda r, c: (c, 7 - c),             # horizontal+anti‑diagonal
    0b1011: lambda r, c: (7 - c, c),             # all four
    0b1100: lambda r, c: (7 - r, 7 - c),         # vertical+diagonal
    0b1101: lambda r, c: (c, 7 - c),             # horizontal+diagonal
    0b1110: lambda r, c: (7 - r, 7 - r),         # vertical+anti‑diagonal
    0b1111: lambda r, c: (r, c),                 # identity again (full flip)
}

def canonical_form(you: np.ndarray, opp: np.ndarray):
    """Return a tuple of you & opp after applying the best symmetry."""
    best = you.copy()
    best_opp = opp.copy()
    for sym in range(16):
        cand_you = np.empty((8,8), dtype=np.int8)
        cand_opp = np.empty((8,8), dtype=np.int8)
        for r in range(8):
            for c in range(8):
                tr, tc = SYM_TRANSFORM[sym](r, c)
                cand_you[r, c] = best[tr, tc]
                cand_opp[r, c] = best_opp[tr, tc]
        # compute the hash string (lexicographically minimal when represented as hex)
        you_str = ''.join(f'{v:02x}' for v in cand_you.tobytes())
        opp_str = ''.join(f'{v:02x}' for v in cand_opp.tobytes())
        key = f'{you_str}{opp_str}'
        if key < key_min:
            best = cand_you
            best_opp = cand_opp
            key_min = key
    return best, best_opp

# ---- simulation utilities -------------------------------------------

def make_move(you: np.ndarray, opp: np.ndarray, move: str, player: int):
    """Place a disc at `move`, flip captured discs, return new board and list of captured cells."""
    r, c = move_to_idx(move)
    new_you = you.copy()
    new_opp = opp.copy()
    new_you[r, c] = player
    # captured cells list
    caps = set()
    flips = 0
    for dr, dc in any_dir(r, c):
        cr, cc = r + dr, c + dc
        while 0 <= cr < 8 and 0 <= cc < 8 and opp[cr, cc] == player:
            # opponent disc found → flip
            caps.add((cr, cc))
            flips += 1
            cr += dr
            cc += dc
            # when we meet a disc of the opposite player, stop
            if new_you[cr, cc] == player:
                break
    # remove flipped opponent discs and insert ours
    new_opp -= np.array([idx in caps for idx in np.ndindex(8, 8)], dtype=np.int8)
    new_you[caps] = player
    return new_you, new_opp, list(caps)

def undo_move(you: np.ndarray, opp: np.ndarray, move: str, player: int, caps):
    """Reverse the effect of a move."""
    r, c = move_to_idx(move)
    you[r, c] = 0
    opp[r, c] = 0
    # undo captured discs
    opp[caps] = player
    you[caps] = 0

# ---- Alpha‑Beta search ----------------------------------------------

class TranspositionCache:
    """Simple LRU cache for the best known move at a given depth."""
    def __init__(self):
        self.table = {}
        self.maxsize = TT_SIZE

    def get(self, key):
        return self.table.get(key)

    def set(self, key, value):
        self.table[key] = value
        if len(self.table) > self.maxsize:
            # evict the oldest entry (first inserted)
            self.table.popitem(last=False)

cache = TranspositionCache()

def alphabeta(you: np.ndarray, opp: np.ndarray, player: int, depth: int,
             alpha: float, beta: float, turn: int):
    """Return (best_score, best_move) for the given board."""
    # turn = 1 if we are maximizing, -1 if opponent minimizing
    if depth == 0 or not get_moves(you, opp, player):
        return evaluate(you, opp), None

    # cache lookup – ignore move, only use board hash and depth/turn
    board_hash = (int(you.tobytes(), 16) << 56) | (int(opp.tobytes(), 16) << 12) | (turn & 0b11)
    cache_key = (board_hash, depth, turn)
    cached = cache.get(cache_key)
    if cached is not None:
        # cached result: best_score and best_move
        if turn == 1:   # we are at maximizing
            score, mv = cached
            if alpha <= score <= beta:
                return score, mv
        else:           # minimizing opponent
            score, mv = cached
            if alpha <= score <= beta:
                return score, mv

    moves = get_moves(you, opp, player)
    best_move = random.choice(moves)          # tie‑breaker (random)
    best_score = -float('inf') if turn == 1 else float('inf')

    for move in moves:
        new_you, new_opp, caps = make_move(you, opp, move, player)
        # Symmetry reduction
        sym_you, sym_opp = canonical_form(new_you, new_opp)
        # Recompute the flip count for the symmetrical board to avoid duplicate work
        # (we can count flips using the original move; it's cheap)
        flip_cnt = len(caps) if caps else 0
        # Compute the immediate contribution of this move
        # We keep the original move string (final output) but search on the canonical board
        # To ensure we return a legal move, we restore afterwards with the original caps.
        # Alpha‑Beta recursion
        if turn == 1:
            score, mv = alphabeta(sym_you, sym_opp, -player, depth - 1,
                                 alpha, beta, -turn)
            total = flip_cnt + score
            if total > best_score:
                best_score = total
                best_move = move
                if best_score >= beta:
                    break
                alpha = max(alpha, best_score)
        else:
            score, mv = alphabeta(sym_you, sym_opp, -player, depth - 1,
                                 alpha, beta, -turn)
            total = flip_cnt + score
            if total < best_score:
                best_score = total
                best_move = move
                if best_score <= alpha:
                    break
                beta = min(beta, best_score)

    # store the result in the cache
    cache.set(cache_key, (best_score, best_move))
    return best_score, best_move

# ---- public API -----------------------------------------------------

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """
    Returns the next move string ("a1" … "h8") or "pass" if there is no legal move.
    """
    # First check for a pass
    if not get_moves(you, opponent, 1):
        return "pass"

    # Othello start: we are player 1
    move, _ = alphabeta(you, opponent, 1, MAX_DEPTH, -float('inf'), float('inf'), 1)
    # In case the search found a None (should never happen when moves exist)
    if move is None:
        return random.choice(get_moves(you, opponent, 1))
    return move

