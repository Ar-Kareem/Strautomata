
import time

ROWS = 5
COLS = 6
N = ROWS * COLS
DIRS = [(-1, 0, 'U'), (0, 1, 'R'), (1, 0, 'D'), (0, -1, 'L')]

# Precomputed board geometry
NEIGH = [[] for _ in range(N)]                 # list of (to_idx, dir_char)
ADJ_MASK = [0] * N                             # adjacent cells bitmask
VULN_MASK = [0] * N                            # cells that could capture a piece on this square
DIR_TO_DELTA = {'U': (-1, 0), 'R': (0, 1), 'D': (1, 0), 'L': (0, -1)}

for r in range(ROWS):
    for c in range(COLS):
        i = r * COLS + c
        for dr, dc, ch in DIRS:
            rr, cc = r + dr, c + dc
            if 0 <= rr < ROWS and 0 <= cc < COLS:
                j = rr * COLS + cc
                NEIGH[i].append((j, ch))
                ADJ_MASK[i] |= 1 << j

# In Clobber, vulnerability of square i is just adjacency:
# if opponent has a piece adjacent to i, that piece can capture onto i.
for i in range(N):
    VULN_MASK[i] = ADJ_MASK[i]

# Mild preference for central squares
CENTER_WEIGHT = [0] * N
for r in range(ROWS):
    for c in range(COLS):
        i = r * COLS + c
        CENTER_WEIGHT[i] = 6 - abs(r - 2) - abs(c - 2.5)

INF = 10**9

def popcount(x: int) -> int:
    return x.bit_count()

def bits(x: int):
    while x:
        lsb = x & -x
        yield lsb.bit_length() - 1
        x ^= lsb

def board_to_bitboard(arr) -> int:
    b = 0
    # Accept nested lists or numpy arrays
    for r in range(ROWS):
        row = arr[r]
        for c in range(COLS):
            if row[c]:
                b |= 1 << (r * COLS + c)
    return b

def generate_moves(me: int, opp: int):
    moves = []
    pieces = me
    while pieces:
        lsb = pieces & -pieces
        i = lsb.bit_length() - 1
        pieces ^= lsb
        for j, ch in NEIGH[i]:
            if (opp >> j) & 1:
                moves.append((i, j, ch))
    return moves

def mobility(me: int, opp: int) -> int:
    total = 0
    pieces = me
    while pieces:
        lsb = pieces & -pieces
        i = lsb.bit_length() - 1
        pieces ^= lsb
        total += popcount(ADJ_MASK[i] & opp)
    return total

def apply_move(me: int, opp: int, move):
    i, j, _ = move
    me2 = (me ^ (1 << i)) | (1 << j)
    opp2 = opp ^ (1 << j)
    return me2, opp2

def move_score(me: int, opp: int, move) -> int:
    # Static tactical ordering heuristic
    i, j, _ = move
    me2, opp2 = apply_move(me, opp, move)

    # Opponent to move next: want to reduce their mobility
    opp_mob = mobility(opp2, me2)
    my_mob_next = mobility(me2, opp2)

    # Is the moved piece on a vulnerable square?
    vulnerable = 1 if (VULN_MASK[j] & opp2) else 0

    # Was original piece vulnerable, and did we escape?
    old_vulnerable = 1 if (VULN_MASK[i] & opp) else 0

    return (
        -20 * opp_mob
        + 8 * my_mob_next
        - 12 * vulnerable
        + 6 * old_vulnerable
        + 2 * CENTER_WEIGHT[j]
        - CENTER_WEIGHT[i]
    )

def evaluate(me: int, opp: int) -> int:
    my_moves = mobility(me, opp)
    opp_moves = mobility(opp, me)
    my_pieces = popcount(me)
    opp_pieces = popcount(opp)

    # Vulnerability counts
    my_vuln = 0
    opp_vuln = 0
    for i in bits(me):
        if VULN_MASK[i] & opp:
            my_vuln += 1
    for i in bits(opp):
        if VULN_MASK[i] & me:
            opp_vuln += 1

    # Central presence
    center_me = sum(CENTER_WEIGHT[i] for i in bits(me))
    center_opp = sum(CENTER_WEIGHT[i] for i in bits(opp))

    # Mobility dominates in Clobber
    return (
        30 * (my_moves - opp_moves)
        + 6 * (my_pieces - opp_pieces)
        + 4 * (opp_vuln - my_vuln)
        + (center_me - center_opp)
    )

def policy(you: list[int], opponent: list[int]) -> str:
    me = board_to_bitboard(you)
    opp = board_to_bitboard(opponent)

    legal = generate_moves(me, opp)
    if not legal:
        # Should not happen in valid arena calls, but return a syntactically valid string.
        # This is only a safety fallback.
        return "0,0,R"

    # Immediate tactical ordering
    legal.sort(key=lambda mv: move_score(me, opp, mv), reverse=True)
    best_move = legal[0]

    start_time = time.time()
    time_limit = 0.92  # keep margin under 1 second

    tt = {}

    def negamax(cur_me: int, cur_opp: int, depth: int, alpha: int, beta: int, ply: int):
        # Time guard
        if time.time() - start_time > time_limit:
            raise TimeoutError

        key = (cur_me, cur_opp, depth)
        if key in tt:
            return tt[key]

        moves = generate_moves(cur_me, cur_opp)

        if not moves:
            # No legal moves: current player loses
            score = -100000 + ply
            tt[key] = score
            return score

        if depth == 0:
            score = evaluate(cur_me, cur_opp)
            tt[key] = score
            return score

        # Order moves
        moves.sort(key=lambda mv: move_score(cur_me, cur_opp, mv), reverse=True)

        best = -INF
        for mv in moves:
            me2, opp2 = apply_move(cur_me, cur_opp, mv)
            score = -negamax(opp2, me2, depth - 1, -beta, -alpha, ply + 1)
            if score > best:
                best = score
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break

        tt[key] = best
        return best

    # Iterative deepening
    depth = 1
    try:
        while True:
            if time.time() - start_time > time_limit:
                break

            current_best = best_move
            current_best_score = -INF

            ordered = generate_moves(me, opp)
            ordered.sort(key=lambda mv: move_score(me, opp, mv), reverse=True)

            alpha = -INF
            beta = INF

            for mv in ordered:
                if time.time() - start_time > time_limit:
                    raise TimeoutError
                me2, opp2 = apply_move(me, opp, mv)
                score = -negamax(opp2, me2, depth - 1, -beta, -alpha, 1)
                if score > current_best_score:
                    current_best_score = score
                    current_best = mv
                if score > alpha:
                    alpha = score

            best_move = current_best
            depth += 1

    except TimeoutError:
        pass

    i, _, ch = best_move
    r, c = divmod(i, COLS)
    return f"{r},{c},{ch}"
