
import time

ROWS = 5
COLS = 6
N = ROWS * COLS

DIRS = [
    (-1, 0, "U"),
    (0, 1, "R"),
    (1, 0, "D"),
    (0, -1, "L"),
]

WIN = 1000000
TIME_LIMIT = 0.90

# Precompute neighbor information.
NEIGHBORS = [[] for _ in range(N)]
ADJ_MASK = [0 for _ in range(N)]

for r in range(ROWS):
    for c in range(COLS):
        i = r * COLS + c
        for dr, dc, d in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS:
                j = nr * COLS + nc
                NEIGHBORS[i].append((j, d))
                ADJ_MASK[i] |= 1 << j


def _to_bits(board):
    """Convert a 5x6 list/numpy-like array to a bitboard."""
    bits = 0
    for r in range(ROWS):
        row = board[r]
        for c in range(COLS):
            if row[c]:
                bits |= 1 << (r * COLS + c)
    return bits


def _bit_count(x):
    return x.bit_count()


def _legal_moves(my, opp):
    """Return moves as tuples: (from_index, to_index, dir)."""
    moves = []
    pieces = my
    while pieces:
        lsb = pieces & -pieces
        i = lsb.bit_length() - 1
        targets = ADJ_MASK[i] & opp
        while targets:
            t = targets & -targets
            j = t.bit_length() - 1
            # Find direction.
            for nj, d in NEIGHBORS[i]:
                if nj == j:
                    moves.append((i, j, d))
                    break
            targets ^= t
        pieces ^= lsb
    return moves


def _mobility(my, opp):
    """Count legal moves for side my against side opp."""
    count = 0
    pieces = my
    while pieces:
        lsb = pieces & -pieces
        i = lsb.bit_length() - 1
        count += _bit_count(ADJ_MASK[i] & opp)
        pieces ^= lsb
    return count


def _apply(my, opp, move):
    """Apply move and return position from next player's perspective."""
    i, j, _ = move
    ib = 1 << i
    jb = 1 << j

    new_my = (my & ~ib) | jb
    new_opp = opp & ~jb

    # Swap perspective: opponent becomes player to move.
    return new_opp, new_my


def _evaluate(my, opp):
    """Static evaluation from current player's perspective."""
    my_mob = _mobility(my, opp)
    if my_mob == 0:
        return -WIN

    opp_mob = _mobility(opp, my)
    if opp_mob == 0:
        return WIN

    my_pieces = _bit_count(my)
    opp_pieces = _bit_count(opp)

    # Mobility is the dominant factor in Clobber.
    score = 120 * (my_mob - opp_mob)

    # Having some material can help preserve future options.
    score += 6 * (my_pieces - opp_pieces)

    # Reward pieces that are adjacent to enemies; they create tactical options.
    active_my = 0
    active_opp = 0

    p = my
    while p:
        b = p & -p
        i = b.bit_length() - 1
        if ADJ_MASK[i] & opp:
            active_my += 1
        p ^= b

    p = opp
    while p:
        b = p & -p
        i = b.bit_length() - 1
        if ADJ_MASK[i] & my:
            active_opp += 1
        p ^= b

    score += 20 * (active_my - active_opp)

    return score


def _ordered_moves(my, opp):
    moves = _legal_moves(my, opp)

    def key(m):
        next_my, next_opp = _apply(my, opp, m)
        # next_my is opponent-to-move pieces after perspective swap.
        opp_next_mob = _mobility(next_my, next_opp)
        my_reply_mob = _mobility(next_opp, next_my)

        # Prefer moves that leave the opponent with fewer moves.
        return my_reply_mob - 3 * opp_next_mob

    moves.sort(key=key, reverse=True)
    return moves


def policy(you: list[int], opponent: list[int]) -> str:
    start = time.perf_counter()

    my = _to_bits(you)
    opp = _to_bits(opponent)

    root_moves = _legal_moves(my, opp)

    # If no legal move exists, the game is already lost. Return a harmless
    # default string; normally the arena should not request a move here.
    if not root_moves:
        return "0,0,U"

    # Always keep a legal fallback.
    best_move = root_moves[0]

    transposition = {}

    def timed_out():
        return time.perf_counter() - start > TIME_LIMIT

    def negamax(my_bits, opp_bits, depth, alpha, beta, ply):
        if timed_out():
            raise TimeoutError

        key = (my_bits, opp_bits, depth)
        if key in transposition:
            return transposition[key]

        moves = _ordered_moves(my_bits, opp_bits)

        if not moves:
            return -WIN + ply

        if depth == 0:
            return _evaluate(my_bits, opp_bits)

        best = -WIN * 2

        for mv in moves:
            n_my, n_opp = _apply(my_bits, opp_bits, mv)
            val = -negamax(n_my, n_opp, depth - 1, -beta, -alpha, ply + 1)

            if val > best:
                best = val

            if best > alpha:
                alpha = best

            if alpha >= beta:
                break

        transposition[key] = best
        return best

    try:
        # Iterative deepening. The board is small, but branching can be high,
        # so we deepen until the time budget is nearly exhausted.
        depth = 1
        while depth <= 30:
            if timed_out():
                break

            current_best = best_move
            current_score = -WIN * 2

            ordered = _ordered_moves(my, opp)

            for mv in ordered:
                if timed_out():
                    raise TimeoutError

                n_my, n_opp = _apply(my, opp, mv)
                score = -negamax(n_my, n_opp, depth - 1, -WIN * 2, WIN * 2, 1)

                if score > current_score:
                    current_score = score
                    current_best = mv

            best_move = current_best

            # If we found a forced immediate/near-immediate win, stop.
            if current_score >= WIN - 100:
                break

            depth += 1

    except TimeoutError:
        pass

    r = best_move[0] // COLS
    c = best_move[0] % COLS
    d = best_move[2]

    return f"{r},{c},{d}"
