
import time
from functools import lru_cache

# ---------- Precomputation ----------

BOARD_N = 8
SQ_N = 64
WIN_SCORE = 1_000_000
INF = 10_000_000

# Directions: N, S, W, E, NW, SE, NE, SW
DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1),
        (-1, -1), (1, 1), (-1, 1), (1, -1)]

ROW_KIND, COL_KIND, D1_KIND, D2_KIND = 0, 1, 2, 3
DIR_KIND = [
    COL_KIND, COL_KIND, ROW_KIND, ROW_KIND,
    D1_KIND, D1_KIND, D2_KIND, D2_KIND
]

ROW_MASK = [0] * 8
COL_MASK = [0] * 8
D1_MASK = [0] * 15   # r - c + 7
D2_MASK = [0] * 15   # r + c

for r in range(8):
    for c in range(8):
        bit = 1 << (r * 8 + c)
        ROW_MASK[r] |= bit
        COL_MASK[c] |= bit
        D1_MASK[r - c + 7] |= bit
        D2_MASK[r + c] |= bit

NEIGH_MASK = [0] * 64
CENTER_DIST = [0] * 64
EDGE_PENALTY = [0] * 64

for r in range(8):
    for c in range(8):
        idx = r * 8 + c
        m = 0
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                rr, cc = r + dr, c + dc
                if 0 <= rr < 8 and 0 <= cc < 8:
                    m |= 1 << (rr * 8 + cc)
        NEIGH_MASK[idx] = m

        # doubled Manhattan distance from board center
        CENTER_DIST[idx] = abs(2 * r - 7) + abs(2 * c - 7)

        edge = 1 if (r == 0 or r == 7 or c == 0 or c == 7) else 0
        corner = 1 if ((r == 0 or r == 7) and (c == 0 or c == 7)) else 0
        EDGE_PENALTY[idx] = edge + corner

# DEST[from][dir][distance] -> destination square, or -1
# PATH[from][dir][distance] -> squares strictly between from and destination
DEST = [[[-1] * 9 for _ in range(8)] for _ in range(64)]
PATH_MASK = [[[0] * 9 for _ in range(8)] for _ in range(64)]

for idx in range(64):
    r, c = divmod(idx, 8)
    for d, (dr, dc) in enumerate(DIRS):
        for n in range(1, 9):
            path = 0
            valid = True
            for step in range(1, n + 1):
                rr, cc = r + dr * step, c + dc * step
                if not (0 <= rr < 8 and 0 <= cc < 8):
                    valid = False
                    break
                if step < n:
                    path |= 1 << (rr * 8 + cc)
            if valid:
                DEST[idx][d][n] = rr * 8 + cc
                PATH_MASK[idx][d][n] = path


class _SearchTimeout(Exception):
    pass


# ---------- Bitboard utilities ----------

def _bits_from_board(board):
    my = 0
    opp = 0
    for r in range(8):
        row = board[r]
        for c in range(8):
            v = row[c]
            bit = 1 << (r * 8 + c)
            if v == 1:
                my |= bit
            elif v == -1:
                opp |= bit
    return my, opp


def _move_to_str(move):
    fr = move >> 6
    to = move & 63
    return f"{fr // 8},{fr % 8}:{to // 8},{to % 8}"


def _apply_move(my, opp, side, move):
    fr = move >> 6
    to = move & 63
    fm = 1 << fr
    tm = 1 << to

    if side == 1:
        # Move my piece; possibly capture opponent on destination.
        return ((my & ~fm) | tm, opp & ~tm)
    else:
        # Move opponent piece; possibly capture my piece on destination.
        return (my & ~tm, (opp & ~fm) | tm)


def _generate_moves(my, opp, side):
    own = my if side == 1 else opp
    enemy = opp if side == 1 else my
    occ = my | opp

    moves = []
    pieces = own

    while pieces:
        lsb = pieces & -pieces
        idx = lsb.bit_length() - 1
        pieces ^= lsb

        r = idx >> 3
        c = idx & 7

        counts = (
            (occ & ROW_MASK[r]).bit_count(),
            (occ & COL_MASK[c]).bit_count(),
            (occ & D1_MASK[r - c + 7]).bit_count(),
            (occ & D2_MASK[r + c]).bit_count(),
        )

        for d in range(8):
            n = counts[DIR_KIND[d]]
            to = DEST[idx][d][n]
            if to < 0:
                continue

            tm = 1 << to

            # Cannot land on own piece.
            if own & tm:
                continue

            # Cannot jump over enemy pieces; destination enemy is capturable.
            if PATH_MASK[idx][d][n] & enemy:
                continue

            moves.append((idx << 6) | to)

    return moves


@lru_cache(maxsize=65536)
def _is_connected(bits):
    if bits == 0:
        return False
    if bits & (bits - 1) == 0:
        return True

    start = bits & -bits
    seen = start
    frontier = start

    while frontier and seen != bits:
        nb = 0
        f = frontier
        while f:
            lsb = f & -f
            nb |= NEIGH_MASK[lsb.bit_length() - 1]
            f ^= lsb
        nb &= bits & ~seen
        seen |= nb
        frontier = nb

    return seen == bits


@lru_cache(maxsize=65536)
def _formation_score(bits):
    n = bits.bit_count()

    if n == 0:
        return -50_000
    if n == 1:
        return 50_000

    coords = []
    rows = []
    cols = []

    sum_r = 0
    sum_c = 0
    min_r = 8
    max_r = -1
    min_c = 8
    max_c = -1

    adjacency_double = 0
    center_sum = 0
    edge_sum = 0

    p = bits
    while p:
        lsb = p & -p
        idx = lsb.bit_length() - 1
        p ^= lsb

        r, c = divmod(idx, 8)
        coords.append(idx)
        rows.append(r)
        cols.append(c)

        sum_r += r
        sum_c += c
        if r < min_r:
            min_r = r
        if r > max_r:
            max_r = r
        if c < min_c:
            min_c = c
        if c > max_c:
            max_c = c

        adjacency_double += (NEIGH_MASK[idx] & bits).bit_count()
        center_sum += CENTER_DIST[idx]
        edge_sum += EDGE_PENALTY[idx]

    adjacency = adjacency_double // 2
    bbox_area = (max_r - min_r + 1) * (max_c - min_c + 1)

    # Sum nearest-neighbor Chebyshev distances: lower means less isolated.
    nearest_sum = 0
    for i in range(n):
        best = 8
        ri, ci = rows[i], cols[i]
        for j in range(n):
            if i == j:
                continue
            d = max(abs(ri - rows[j]), abs(ci - cols[j]))
            if d < best:
                best = d
                if best == 1:
                    break
        nearest_sum += best

    # Spread around centroid, scaled without floats.
    spread_scaled = 0
    for i in range(n):
        spread_scaled += max(abs(n * rows[i] - sum_r),
                             abs(n * cols[i] - sum_c))

    # Component count and largest component.
    rem = bits
    comps = 0
    largest = 0

    while rem:
        start = rem & -rem
        seen = start
        frontier = start

        while frontier:
            nb = 0
            f = frontier
            while f:
                lsb = f & -f
                nb |= NEIGH_MASK[lsb.bit_length() - 1]
                f ^= lsb
            nb &= bits & ~seen
            seen |= nb
            frontier = nb

        comps += 1
        size = seen.bit_count()
        if size > largest:
            largest = size
        rem &= ~seen

    score = 0

    if comps == 1:
        score += 40_000

    # Main LOA objective: few components and a large main component.
    score -= 1800 * (comps - 1)
    score += (1400 * largest) // n

    # Encourage compact, mutually supporting groups.
    score += 110 * adjacency
    score -= 55 * nearest_sum
    score -= 30 * bbox_area
    score -= (8 * spread_scaled) // n

    # Prefer central, non-edge formations.
    score -= 12 * center_sum
    score -= 18 * edge_sum

    # Tiny stabilizer; material is not dominant in LOA.
    score += 3 * n

    return score


def _evaluate(my, opp, side):
    if side == 1:
        me, enemy = my, opp
    else:
        me, enemy = opp, my
    return _formation_score(me) - _formation_score(enemy) + 5


def _ordered_moves(my, opp, side, moves, ttmove=-1, tactical=False):
    if len(moves) <= 1:
        return moves

    own = my if side == 1 else opp
    enemy = opp if side == 1 else my

    scored = []

    for m in moves:
        fr = m >> 6
        to = m & 63
        fm = 1 << fr
        tm = 1 << to

        capture = 1 if (enemy & tm) else 0
        own_after = (own & ~fm) | tm

        old_neighbors = (NEIGH_MASK[fr] & own).bit_count()
        new_neighbors = (NEIGH_MASK[to] & own_after).bit_count()

        s = 0
        s += 90 * new_neighbors
        s += 25 * (new_neighbors - old_neighbors)
        s += 6 * (CENTER_DIST[fr] - CENTER_DIST[to])
        s -= 18 * EDGE_PENALTY[to]
        s -= 8 * ((NEIGH_MASK[to] & enemy).bit_count())

        if capture:
            s += 80

        if tactical:
            own_conn = _is_connected(own_after)
            if own_conn:
                s += 1_000_000

            # Capturing can accidentally make the opponent connected.
            if capture:
                enemy_after = enemy & ~tm
                if (not own_conn) and _is_connected(enemy_after):
                    s -= 900_000

        if m == ttmove:
            s += 2_000_000

        scored.append((s, m))

    scored.sort(reverse=True)
    return [m for _, m in scored]


# ---------- Required API ----------

def policy(board) -> str:
    my, opp = _bits_from_board(board)

    root_moves = _generate_moves(my, opp, 1)

    # In a valid LOA position this should not happen. If it does, no legal
    # move exists to return, so use a syntactically valid emergency string.
    if not root_moves:
        return "0,0:0,0"

    root_moves = _ordered_moves(my, opp, 1, root_moves, tactical=True)
    best_move = root_moves[0]

    # If a move wins immediately, play it.
    for m in root_moves:
        nmy, nopp = _apply_move(my, opp, 1, m)
        if _is_connected(nmy):
            return _move_to_str(m)

    if len(root_moves) == 1:
        return _move_to_str(best_move)

    start = time.perf_counter()
    deadline = start + 0.88

    total_pieces = (my | opp).bit_count()
    if total_pieces <= 8:
        max_depth = 6
    elif total_pieces <= 12:
        max_depth = 5
    else:
        max_depth = 4

    tt = {}
    nodes = 0

    def negamax(cmy, copp, side, depth, alpha, beta, ply):
        nonlocal nodes

        nodes += 1
        if (nodes & 1023) == 0 and time.perf_counter() > deadline:
            raise _SearchTimeout()

        # Previous mover is -side. If previous mover connected, side to move lost.
        prev_bits = copp if side == 1 else cmy
        cur_bits = cmy if side == 1 else copp

        if _is_connected(prev_bits):
            return -WIN_SCORE + ply
        if _is_connected(cur_bits):
            return WIN_SCORE - ply

        if depth <= 0:
            return _evaluate(cmy, copp, side)

        key = (cmy, copp, side)
        alpha_orig = alpha
        beta_orig = beta
        ttmove = -1

        entry = tt.get(key)
        if entry is not None:
            e_depth, e_val, e_flag, e_move = entry
            ttmove = e_move
            if e_depth >= depth:
                if e_flag == 0:
                    return e_val
                elif e_flag == 1:
                    if e_val > alpha:
                        alpha = e_val
                else:
                    if e_val < beta:
                        beta = e_val
                if alpha >= beta:
                    return e_val

        moves = _generate_moves(cmy, copp, side)
        if not moves:
            return _evaluate(cmy, copp, side)

        moves = _ordered_moves(
            cmy, copp, side, moves,
            ttmove=ttmove,
            tactical=(depth >= 2)
        )

        best_val = -INF
        best_local = moves[0]

        for m in moves:
            nmy, nopp = _apply_move(cmy, copp, side, m)
            val = -negamax(nmy, nopp, -side, depth - 1,
                           -beta, -alpha, ply + 1)

            if val > best_val:
                best_val = val
                best_local = m

            if val > alpha:
                alpha = val
                if alpha >= beta:
                    break

        if best_val <= alpha_orig:
            flag = -1     # upper bound
        elif best_val >= beta_orig:
            flag = 1      # lower bound
        else:
            flag = 0      # exact

        tt[key] = (depth, best_val, flag, best_local)
        return best_val

    try:
        # Iterative deepening: always keep the best fully completed result.
        for depth in range(1, max_depth + 1):
            if time.perf_counter() > deadline:
                break

            iteration_best = best_move
            iteration_score = -INF
            alpha = -INF
            beta = INF

            # Principal variation first.
            if best_move in root_moves:
                ordered_root = [best_move] + [m for m in root_moves if m != best_move]
            else:
                ordered_root = root_moves

            for m in ordered_root:
                if time.perf_counter() > deadline:
                    raise _SearchTimeout()

                nmy, nopp = _apply_move(my, opp, 1, m)
                val = -negamax(nmy, nopp, -1, depth - 1,
                               -beta, -alpha, 1)

                if val > iteration_score:
                    iteration_score = val
                    iteration_best = m

                if val > alpha:
                    alpha = val

            best_move = iteration_best

            if iteration_score >= WIN_SCORE - 1000:
                break

    except _SearchTimeout:
        pass
    except Exception:
        # Safety: best_move is always from generated legal root moves.
        pass

    return _move_to_str(best_move)
