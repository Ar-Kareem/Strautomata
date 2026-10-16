
import time
import math

ROWS = 5
COLS = 6
N = ROWS * COLS
DIRS = [(-1, 0, 'U'), (0, 1, 'R'), (1, 0, 'D'), (0, -1, 'L')]

# Bit masks for every square.
BIT = [1 << i for i in range(N)]

# Precompute directional neighbors: (from_index, to_index, dir_char)
NEI = [[] for _ in range(N)]
for r in range(ROWS):
    for c in range(COLS):
        i = r * COLS + c
        for dr, dc, ch in DIRS:
            rr, cc = r + dr, c + dc
            if 0 <= rr < ROWS and 0 <= cc < COLS:
                j = rr * COLS + cc
                NEI[i].append((j, ch))

CENTER_WEIGHT = [
    1, 2, 2, 2, 2, 1,
    2, 3, 4, 4, 3, 2,
    2, 4, 5, 5, 4, 2,
    2, 3, 4, 4, 3, 2,
    1, 2, 2, 2, 2, 1,
]

def _to_bits(arr):
    """Convert flat/list/numpy-like 5x6 array to bitboard."""
    b = 0
    # Works for nested lists and numpy arrays.
    try:
        for r in range(ROWS):
            row = arr[r]
            for c in range(COLS):
                if row[c]:
                    b |= BIT[r * COLS + c]
    except Exception:
        # Flat fallback.
        for i, v in enumerate(arr):
            if i >= N:
                break
            if v:
                b |= BIT[i]
    return b

def _moves(me, opp):
    """Return legal moves as tuples (from, to, dir)."""
    res = []
    x = me
    while x:
        lsb = x & -x
        i = lsb.bit_length() - 1
        for j, ch in NEI[i]:
            if opp & BIT[j]:
                res.append((i, j, ch))
        x ^= lsb
    return res

def _move_count(me, opp):
    cnt = 0
    x = me
    while x:
        lsb = x & -x
        i = lsb.bit_length() - 1
        for j, _ in NEI[i]:
            if opp & BIT[j]:
                cnt += 1
        x ^= lsb
    return cnt

def _apply(me, opp, mv):
    """Apply current player's move. Return new (current_player_bits, opponent_bits) after side swap."""
    i, j, _ = mv
    bi, bj = BIT[i], BIT[j]
    new_me = (me ^ bi) | bj      # my piece moves i -> j
    new_opp = opp ^ bj           # captured opponent piece removed
    return new_opp, new_me       # swap sides for negamax

def _static_eval(me, opp):
    """Heuristic from side-to-move perspective."""
    my_moves = _move_count(me, opp)
    if my_moves == 0:
        return -100000

    opp_moves = _move_count(opp, me)
    if opp_moves == 0:
        return 100000

    my_pieces = me.bit_count()
    opp_pieces = opp.bit_count()

    # Mobility is usually the strongest short-horizon signal in Clobber.
    score = 90 * (my_moves - opp_moves)

    # Having too many pieces can be bad in some Clobber positions, but in short tactical fights
    # piece advantage and capture availability are usually useful.
    score += 18 * (my_pieces - opp_pieces)

    # Slight center preference: central pieces tend to keep options.
    cm = 0
    co = 0
    x = me
    while x:
        lsb = x & -x
        cm += CENTER_WEIGHT[lsb.bit_length() - 1]
        x ^= lsb
    x = opp
    while x:
        lsb = x & -x
        co += CENTER_WEIGHT[lsb.bit_length() - 1]
        x ^= lsb
    score += 2 * (cm - co)

    # Prefer reducing opponent's next captures while keeping ours.
    return score

def _ordered_moves(me, opp):
    ms = _moves(me, opp)
    if len(ms) <= 1:
        return ms

    scored = []
    for mv in ms:
        nm_opp, nm_me = _apply(me, opp, mv)  # after swap: side to move is old opponent
        opp_reply_moves = _move_count(nm_opp, nm_me)
        my_future_moves = _move_count(nm_me, nm_opp)

        # Good moves leave opponent few replies and us future possibilities.
        # Also give a small bonus for moving toward center.
        _, to, _ = mv
        s = -120 * opp_reply_moves + 35 * my_future_moves + CENTER_WEIGHT[to]
        if opp_reply_moves == 0:
            s += 1000000
        scored.append((s, mv))
    scored.sort(reverse=True, key=lambda x: x[0])
    return [m for _, m in scored]

def _negamax(me, opp, depth, alpha, beta, deadline, table):
    if time.perf_counter() >= deadline:
        raise TimeoutError

    key = (me, opp, depth)
    val = table.get(key)
    if val is not None:
        return val

    ms = _ordered_moves(me, opp)
    if not ms:
        return -1000000 - depth

    # If any move leaves opponent no legal move, it wins immediately.
    for mv in ms:
        nme, nopp = _apply(me, opp, mv)
        if _move_count(nme, nopp) == 0:
            return 1000000 + depth

    if depth <= 0:
        return _static_eval(me, opp)

    best = -10**9
    for mv in ms:
        nme, nopp = _apply(me, opp, mv)
        v = -_negamax(nme, nopp, depth - 1, -beta, -alpha, deadline, table)
        if v > best:
            best = v
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    table[key] = best
    return best

def _format_move(mv):
    i, j, ch = mv
    r = i // COLS
    c = i % COLS
    return f"{r},{c},{ch}"

def policy(you: list[int], opponent: list[int]) -> str:
    start_time = time.perf_counter()
    # Keep margin under 1 second.
    deadline = start_time + 0.92

    me = _to_bits(you)
    opp = _to_bits(opponent)

    legal = _ordered_moves(me, opp)
    if not legal:
        # Should not happen in normal arena calls, but return a syntactically valid string.
        # It cannot be legal if no legal move exists.
        return "0,0,R"

    best_move = legal[0]

    # Immediate winning move.
    for mv in legal:
        nme, nopp = _apply(me, opp, mv)
        if _move_count(nme, nopp) == 0:
            return _format_move(mv)

    # Iterative deepening. Branching on 5x6 Clobber is modest; depths 5-9 are often reachable.
    table = {}
    max_depth = 30
    depth = 1

    try:
        while depth <= max_depth and time.perf_counter() < deadline:
            cur_best = best_move
            cur_score = -10**9
            alpha = -10**9
            beta = 10**9

            for mv in legal:
                if time.perf_counter() >= deadline:
                    raise TimeoutError
                nme, nopp = _apply(me, opp, mv)
                score = -_negamax(nme, nopp, depth - 1, -beta, -alpha, deadline, table)
                if score > cur_score:
                    cur_score = score
                    cur_best = mv
                if score > alpha:
                    alpha = score

            best_move = cur_best

            # Proven win/loss enough; no need to continue.
            if cur_score > 900000:
                break
            depth += 1
    except TimeoutError:
        pass
    except Exception:
        # Defensive fallback: never fail to return a legal move if one exists.
        best_move = legal[0]

    return _format_move(best_move)
