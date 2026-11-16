
import time
import random
from typing import List, Tuple

ROWS = 5
COLS = 6
N = ROWS * COLS

# Direction deltas and chars
DIRS = {
    'U': (-1, 0),
    'D': (1, 0),
    'L': (0, -1),
    'R': (0, 1),
}

INF = 10**9

# Precompute row/col for indices
IDX_TO_RC = [(i // COLS, i % COLS) for i in range(N)]
RC_TO_IDX = {(r, c): r * COLS + c for r in range(ROWS) for c in range(COLS)}

def board_lists_to_bitboards(you: List[int], opp: List[int]) -> Tuple[int, int]:
    you_bits = 0
    opp_bits = 0
    for r in range(ROWS):
        for c in range(COLS):
            idx = r * COLS + c
            if you[r][c]:
                you_bits |= 1 << idx
            if opp[r][c]:
                opp_bits |= 1 << idx
    return you_bits, opp_bits

def popcount(x: int) -> int:
    return x.bit_count()

def gen_moves(player_bits: int, opp_bits: int) -> List[Tuple[int, int, str]]:
    """Generate moves for player: list of (from_idx, to_idx, dir_char)."""
    moves = []
    bits = player_bits
    while bits:
        lsb = bits & -bits
        from_idx = lsb.bit_length() - 1
        bits -= lsb
        r, c = IDX_TO_RC[from_idx]
        # check four directions
        for dch, (dr, dc) in DIRS.items():
            nr = r + dr
            nc = c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS:
                to_idx = nr * COLS + nc
                if (opp_bits >> to_idx) & 1:
                    moves.append((from_idx, to_idx, dch))
    return moves

def apply_move(player_bits: int, opp_bits: int, move: Tuple[int, int, str]) -> Tuple[int, int]:
    from_idx, to_idx, _ = move
    # remove from source, capture opponent at dest, place at dest
    player_bits = player_bits & ~(1 << from_idx)
    player_bits = player_bits | (1 << to_idx)
    opp_bits = opp_bits & ~(1 << to_idx)
    return player_bits, opp_bits

# Transposition table
TT = {}

def evaluate(player_bits: int, opp_bits: int) -> int:
    """Heuristic evaluation from current player's perspective (higher is better)."""
    # If player has no moves -> losing position
    my_moves = gen_moves(player_bits, opp_bits)
    if not my_moves:
        return -1000000
    opp_moves = gen_moves(opp_bits, player_bits)
    mobility_score = (len(my_moves) - len(opp_moves)) * 20
    material_score = (popcount(player_bits) - popcount(opp_bits)) * 100
    # safety: count pieces that are not adjacent to any opponent (safer)
    safe = 0
    bits = player_bits
    while bits:
        lsb = bits & -bits
        idx = lsb.bit_length() - 1
        bits -= lsb
        r, c = IDX_TO_RC[idx]
        threatened = False
        for dr, dc in DIRS.values():
            nr = r + dr
            nc = c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS:
                if (opp_bits >> (nr * COLS + nc)) & 1:
                    threatened = True
                    break
        if not threatened:
            safe += 1
    safety_score = safe * 30
    return mobility_score + material_score + safety_score

def negamax(player_bits: int, opp_bits: int, depth: int, alpha: int, beta: int, start_time: float, time_limit: float) -> int:
    # Time check
    if time.time() - start_time > time_limit:
        # Cut off search due to time; return static eval
        return evaluate(player_bits, opp_bits)
    key = (player_bits, opp_bits, depth)
    if key in TT:
        return TT[key]
    moves = gen_moves(player_bits, opp_bits)
    if not moves:
        val = -1000000
        TT[key] = val
        return val
    if depth == 0:
        val = evaluate(player_bits, opp_bits)
        TT[key] = val
        return val
    # Move ordering: prefer moves that reduce opponent moves after move
    def move_order_key(mv):
        nbp, nbo = apply_move(player_bits, opp_bits, mv)
        # opponent will move next, so count their moves (lower is better -> higher priority)
        return -len(gen_moves(nbo, nbp))
    moves.sort(key=move_order_key)
    best = -INF
    for mv in moves:
        nbp, nbo = apply_move(player_bits, opp_bits, mv)
        # Recurse with sides swapped; negamax returns value from opponent's perspective -> negate
        val = -negamax(nbo, nbp, depth - 1, -beta, -alpha, start_time, time_limit)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
        # Time check inside loop
        if time.time() - start_time > time_limit:
            break
    TT[key] = best
    return best

def best_move_search(player_bits: int, opp_bits: int, max_time: float = 0.90) -> Tuple[int, int, str]:
    """Iterative deepening search to find best move. Returns a move tuple."""
    start_time = time.time()
    time_limit = max_time
    moves = gen_moves(player_bits, opp_bits)
    if not moves:
        # No legal moves: (shouldn't happen in valid calls). Return a dummy legal string by trying to find any capture.
        return None
    best_mv = moves[0]
    # Try depths increasing
    max_depth = 6  # safe cap; iterative deepening will stop on time
    for depth in range(1, max_depth + 1):
        if time.time() - start_time > time_limit:
            break
        current_best = None
        current_best_val = -INF
        # Order moves with heuristic before deeper search
        moves_ordered = sorted(moves, key=lambda mv: -((popcount(player_bits) - popcount(opp_bits)) * 100))  # cheap fallback
        # But actually prefer by earlier ordering
        moves_ordered = moves
        for mv in moves_ordered:
            if time.time() - start_time > time_limit:
                break
            nbp, nbo = apply_move(player_bits, opp_bits, mv)
            val = -negamax(nbo, nbp, depth - 1, -INF, INF, start_time, time_limit)
            if val > current_best_val:
                current_best_val = val
                current_best = mv
        if current_best is not None:
            best_mv = current_best
    return best_mv

def move_to_string(move: Tuple[int, int, str]) -> str:
    from_idx, to_idx, dch = move
    r, c = IDX_TO_RC[from_idx]
    return f"{r},{c},{dch}"

def policy(you: List[List[int]], opponent: List[List[int]]) -> str:
    """
    Main API. you and opponent are 5x6 lists (rows x cols) with 0/1.
    Returns a move string 'row,col,dir'.
    """
    # Convert to bitboards
    player_bits, opp_bits = board_lists_to_bitboards(you, opponent)
    # Find best move with search
    mv = best_move_search(player_bits, opp_bits, max_time=0.90)
    if mv is None:
        # No moves found: as a fallback (shouldn't normally happen), try to find any legal capture brute-force
        moves = gen_moves(player_bits, opp_bits)
        if not moves:
            # As absolute last resort (invalid but must return something), return an arbitrary move string within bounds.
            # However, typical arena states will always have a legal move when called.
            return "0,0,U"
        mv = moves[0]
    return move_to_string(mv)

# If run as script, nothing to do. The policy function is the API entry point.
