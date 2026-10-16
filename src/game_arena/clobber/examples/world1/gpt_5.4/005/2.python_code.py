
from typing import List, Tuple

ROWS = 5
COLS = 6
N = ROWS * COLS

# Directions: (dr, dc, char)
DIRS = [(-1, 0, 'U'), (0, 1, 'R'), (1, 0, 'D'), (0, -1, 'L')]

# Precompute neighbors and move masks
NEIGHBORS = [[] for _ in range(N)]  # (dst, dir_char)
ADJ_MASK = [0] * N

for r in range(ROWS):
    for c in range(COLS):
        i = r * COLS + c
        for dr, dc, ch in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS:
                j = nr * COLS + nc
                NEIGHBORS[i].append((j, ch))
                ADJ_MASK[i] |= (1 << j)

# Small transposition table
TT = {}

def list_to_bits(board: List[List[int]]) -> int:
    bits = 0
    k = 0
    for r in range(ROWS):
        row = board[r]
        for c in range(COLS):
            if row[c]:
                bits |= (1 << k)
            k += 1
    return bits

def bits_to_move_str(src: int, dst: int) -> str:
    r, c = divmod(src, COLS)
    if dst == src - COLS:
        d = 'U'
    elif dst == src + 1:
        d = 'R'
    elif dst == src + COLS:
        d = 'D'
    else:
        d = 'L'
    return f"{r},{c},{d}"

def legal_moves_bits(you_bits: int, opp_bits: int) -> List[Tuple[int, int]]:
    moves = []
    y = you_bits
    while y:
        lsb = y & -y
        src = lsb.bit_length() - 1
        targets = ADJ_MASK[src] & opp_bits
        t = targets
        while t:
            tlsb = t & -t
            dst = tlsb.bit_length() - 1
            moves.append((src, dst))
            t ^= tlsb
        y ^= lsb
    return moves

def apply_move(you_bits: int, opp_bits: int, move: Tuple[int, int]) -> Tuple[int, int]:
    src, dst = move
    you_bits ^= (1 << src)
    you_bits |= (1 << dst)
    opp_bits ^= (1 << dst)
    return opp_bits, you_bits  # swap perspective for next player

def mobility(you_bits: int, opp_bits: int) -> int:
    count = 0
    y = you_bits
    while y:
        lsb = y & -y
        src = lsb.bit_length() - 1
        count += (ADJ_MASK[src] & opp_bits).bit_count()
        y ^= lsb
    return count

def connected_pairs(bits: int) -> int:
    # Count orthogonally adjacent same-color pairs once
    total = 0
    b = bits
    while b:
        lsb = b & -b
        i = lsb.bit_length() - 1
        r, c = divmod(i, COLS)
        if c + 1 < COLS and (bits >> (i + 1)) & 1:
            total += 1
        if r + 1 < ROWS and (bits >> (i + COLS)) & 1:
            total += 1
        b ^= lsb
    return total

def evaluate(you_bits: int, opp_bits: int) -> int:
    my_moves = mobility(you_bits, opp_bits)
    op_moves = mobility(opp_bits, you_bits)

    if my_moves == 0:
        return -100000
    if op_moves == 0:
        return 100000

    my_count = you_bits.bit_count()
    op_count = opp_bits.bit_count()

    # Heuristic:
    # mobility dominates, then immediate threats/traps, then material/shape
    score = 0
    score += 120 * (my_moves - op_moves)
    score += 10 * (my_count - op_count)
    score -= 4 * connected_pairs(you_bits)   # clustered own pieces are often vulnerable/stuck
    score += 4 * connected_pairs(opp_bits)   # opponent clusters can be targets
    return score

def ordered_moves(you_bits: int, opp_bits: int) -> List[Tuple[int, int]]:
    moves = legal_moves_bits(you_bits, opp_bits)
    if len(moves) <= 1:
        return moves

    scored = []
    for mv in moves:
        n_you, n_opp = apply_move(you_bits, opp_bits, mv)
        # next player is opponent; from our perspective negate their mobility edge
        # but keep ordering inexpensive
        opp_reply = mobility(n_you, n_opp)
        our_next = mobility(n_opp, n_you)
        src, dst = mv

        # Prefer moves that reduce opponent replies and preserve our future moves.
        # Slight bonus if destination has many adjacent opponents in current board.
        local_pressure = (ADJ_MASK[dst] & opp_bits).bit_count()
        local_risk = (ADJ_MASK[dst] & you_bits).bit_count()
        score = -40 * opp_reply + 20 * our_next + 8 * local_pressure - 5 * local_risk

        # Huge priority to immediate win
        if opp_reply == 0:
            score += 1000000
        scored.append((score, mv))

    scored.sort(reverse=True)
    return [mv for _, mv in scored]

def negamax(you_bits: int, opp_bits: int, depth: int, alpha: int, beta: int) -> int:
    key = (you_bits, opp_bits, depth)
    if key in TT:
        return TT[key]

    moves = ordered_moves(you_bits, opp_bits)
    if not moves:
        return -100000 + (10 - depth)

    # Exact solve for tiny positions
    total_pieces = you_bits.bit_count() + opp_bits.bit_count()
    if depth == 0:
        val = evaluate(you_bits, opp_bits)
        TT[key] = val
        return val

    best = -10**9
    for mv in moves:
        n_you, n_opp = apply_move(you_bits, opp_bits, mv)
        val = -negamax(n_you, n_opp, depth - 1, -beta, -alpha)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    TT[key] = best
    return best

def choose_depth(num_moves: int, total_pieces: int) -> int:
    # Conservative depth schedule to stay within time.
    if total_pieces <= 8:
        return 12
    if total_pieces <= 12:
        return 10
    if total_pieces <= 16:
        return 8
    if num_moves <= 4:
        return 8
    if num_moves <= 8:
        return 6
    return 5

def policy(you: List[List[int]], opponent: List[List[int]]) -> str:
    you_bits = list_to_bits(you)
    opp_bits = list_to_bits(opponent)

    moves = legal_moves_bits(you_bits, opp_bits)

    # Guaranteed legal fallback assumption from problem statement:
    # there should be at least one legal move when policy is called.
    # Still, defensively return something syntactically valid if not.
    if not moves:
        for r in range(ROWS):
            for c in range(COLS):
                if you[r][c]:
                    # Try to fabricate nearest in-bounds direction; arena should never reach here.
                    if r > 0:
                        return f"{r},{c},U"
                    if c + 1 < COLS:
                        return f"{r},{c},R"
                    if r + 1 < ROWS:
                        return f"{r},{c},D"
                    return f"{r},{c},L"
        return "0,0,R"

    # Immediate winning move?
    for mv in moves:
        n_you, n_opp = apply_move(you_bits, opp_bits, mv)
        if not legal_moves_bits(n_you, n_opp):
            return bits_to_move_str(*mv)

    ordered = ordered_moves(you_bits, opp_bits)
    fallback = bits_to_move_str(*ordered[0])

    total_pieces = you_bits.bit_count() + opp_bits.bit_count()
    depth = choose_depth(len(ordered), total_pieces)

    best_move = ordered[0]
    best_val = -10**9
    alpha = -10**9
    beta = 10**9

    # Clear TT occasionally by size
    if len(TT) > 200000:
        TT.clear()

    for mv in ordered:
        n_you, n_opp = apply_move(you_bits, opp_bits, mv)
        val = -negamax(n_you, n_opp, depth - 1, -beta, -alpha)
        if val > best_val:
            best_val = val
            best_move = mv
        if val > alpha:
            alpha = val

    move_str = bits_to_move_str(*best_move)

    # Final legality check; otherwise use fallback
    src, dst = best_move
    sr, sc = divmod(src, COLS)
    dr, dc = divmod(dst, COLS)
    if (
        0 <= sr < ROWS and 0 <= sc < COLS and
        0 <= dr < ROWS and 0 <= dc < COLS and
        you[sr][sc] == 1 and opponent[dr][dc] == 1 and
        abs(sr - dr) + abs(sc - dc) == 1
    ):
        return move_str
    return fallback
