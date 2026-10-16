
from time import perf_counter

FULL_MASK = (1 << 36) - 1
WIN_SCORE = 10_000_000
INF = 10 ** 18
DIR_CHARS = ("L", "R")

# Heuristic score for uncontested 5-cell segments.
SEG5_SCORES = (0, 4, 18, 90, 1200, 0)

# Positional weights: favor center and quadrant centers.
WEIGHTS_GRID = (
    (1, 2, 2, 2, 2, 1),
    (2, 4, 3, 3, 4, 2),
    (2, 3, 5, 5, 3, 2),
    (2, 3, 5, 5, 3, 2),
    (2, 4, 3, 3, 4, 2),
    (1, 2, 2, 2, 2, 1),
)

# Build weight masks.
_wm = [0] * 6
for r in range(6):
    for c in range(6):
        _wm[WEIGHTS_GRID[r][c]] |= 1 << (r * 6 + c)
W1, W2, W3, W4, W5 = _wm[1], _wm[2], _wm[3], _wm[4], _wm[5]

# All 5-cell winning masks.
_win_masks = []

# Horizontal
for r in range(6):
    for c0 in range(2):
        m = 0
        for k in range(5):
            m |= 1 << (r * 6 + c0 + k)
        _win_masks.append(m)

# Vertical
for c in range(6):
    for r0 in range(2):
        m = 0
        for k in range(5):
            m |= 1 << ((r0 + k) * 6 + c)
        _win_masks.append(m)

# Diagonal down-right
for r0 in range(2):
    for c0 in range(2):
        m = 0
        for k in range(5):
            m |= 1 << ((r0 + k) * 6 + (c0 + k))
        _win_masks.append(m)

# Diagonal down-left
for r0 in range(2):
    for c0 in range(4, 6):
        m = 0
        for k in range(5):
            m |= 1 << ((r0 + k) * 6 + (c0 - k))
        _win_masks.append(m)

WIN_MASKS = tuple(_win_masks)

# Quadrant indices in row-major order.
QUAD_INDS = (
    (0, 1, 2, 6, 7, 8, 12, 13, 14),      # quad 0
    (3, 4, 5, 9, 10, 11, 15, 16, 17),    # quad 1
    (18, 19, 20, 24, 25, 26, 30, 31, 32),# quad 2
    (21, 22, 23, 27, 28, 29, 33, 34, 35) # quad 3
)

QUAD_MASKS = tuple(sum(1 << i for i in inds) for inds in QUAD_INDS)
OUTSIDE_MASKS = tuple(FULL_MASK ^ m for m in QUAD_MASKS)

# Local 3x3 rotation maps: 0 = L, 1 = R
ROT_LOCAL = (
    tuple((2 - (i % 3)) * 3 + (i // 3) for i in range(9)),      # L
    tuple((i % 3) * 3 + (2 - (i // 3)) for i in range(9)),      # R
)

# Precompute rotated quadrant bitmasks and rotated placement destinations.
_rotated_quad = [[[0] * 512 for _ in range(2)] for _ in range(4)]
_place_after = [[[0] * 36 for _ in range(2)] for _ in range(4)]

for q, inds in enumerate(QUAD_INDS):
    local_of = {g: i for i, g in enumerate(inds)}

    for d in range(2):
        # For every 9-bit quadrant pattern, precompute the rotated global mask.
        for pat in range(512):
            rot_pat = 0
            for i in range(9):
                if (pat >> i) & 1:
                    rot_pat |= 1 << ROT_LOCAL[d][i]
            gmask = 0
            for j, g in enumerate(inds):
                if (rot_pat >> j) & 1:
                    gmask |= 1 << g
            _rotated_quad[q][d][pat] = gmask

        # Where a newly placed marble ends up after the chosen rotation.
        for idx in range(36):
            if idx in local_of:
                dest = inds[ROT_LOCAL[d][local_of[idx]]]
            else:
                dest = idx
            _place_after[q][d][idx] = 1 << dest

ROTATED_QUAD_MASK = tuple(tuple(tuple(x) for x in qq) for qq in _rotated_quad)
PLACE_AFTER = tuple(tuple(tuple(x) for x in qq) for qq in _place_after)

# Prebuilt move strings.
MOVE_STRS = tuple(
    tuple(
        tuple(f"{idx // 6 + 1},{idx % 6 + 1},{q},{DIR_CHARS[d]}" for d in range(2))
        for q in range(4)
    )
    for idx in range(36)
)

DEADLINE = 0.0
NODE_COUNTER = 0


class SearchTimeout(Exception):
    pass


def check_time():
    global NODE_COUNTER
    NODE_COUNTER += 1
    if (NODE_COUNTER & 255) == 0 and perf_counter() > DEADLINE:
        raise SearchTimeout


def bits_from_arrays(you, opponent):
    my = 0
    opp = 0
    bit = 1
    for r in range(6):
        yr = you[r]
        orow = opponent[r]
        for c in range(6):
            if yr[c]:
                my |= bit
            elif orow[c]:
                opp |= bit
            bit <<= 1
    return my, opp


def rotate_bits(bits, q, d):
    inds = QUAD_INDS[q]
    pat = 0
    for j, idx in enumerate(inds):
        pat |= ((bits >> idx) & 1) << j
    return (bits & OUTSIDE_MASKS[q]) | ROTATED_QUAD_MASK[q][d][pat]


def piece_square(bits):
    return (
        (bits & W1).bit_count()
        + 2 * (bits & W2).bit_count()
        + 3 * (bits & W3).bit_count()
        + 4 * (bits & W4).bit_count()
        + 5 * (bits & W5).bit_count()
    )


def score_position(my, opp):
    # Returns (score_from_my_perspective, is_terminal)
    score = piece_square(my) - piece_square(opp)
    my_win = False
    opp_win = False

    for mask in WIN_MASKS:
        am = my & mask
        bm = opp & mask

        if am:
            if bm:
                continue
            a = am.bit_count()
            if a == 5:
                my_win = True
            score += SEG5_SCORES[a]
        elif bm:
            b = bm.bit_count()
            if b == 5:
                opp_win = True
            score -= SEG5_SCORES[b]

    if my_win and opp_win:
        return 0, True
    if my_win:
        return WIN_SCORE, True
    if opp_win:
        return -WIN_SCORE, True
    if (my | opp) == FULL_MASK:
        return 0, True
    return score, False


def generate_ordered_moves(my, opp, limit=None):
    check_time()
    occupied = my | opp
    empty = FULL_MASK ^ occupied
    entries = []
    generated = 0

    for q in range(4):
        for d in range(2):
            rmy = rotate_bits(my, q, d)
            ropp = rotate_bits(opp, q, d)
            place_after = PLACE_AFTER[q][d]

            eb = empty
            while eb:
                lsb = eb & -eb
                idx = lsb.bit_length() - 1
                eb ^= lsb

                nmy = rmy | place_after[idx]
                s, _ = score_position(nmy, ropp)
                entries.append((s, idx, q, d, nmy, ropp))

                generated += 1
                if (generated & 127) == 0:
                    check_time()

    entries.sort(key=lambda x: x[0], reverse=True)
    if limit is not None and len(entries) > limit:
        return entries[:limit]
    return entries


def internal_limit(depth, empties):
    if depth >= 3:
        return 16 if empties > 6 else 24
    if depth == 2:
        return 20 if empties > 8 else None
    return None


def root_limit(depth, empties, n_moves):
    if depth <= 2:
        return n_moves
    if depth == 3:
        return min(n_moves, 64 if empties <= 10 else 48)
    return min(n_moves, 24)


def search(my, opp, depth, alpha, beta):
    check_time()

    score, terminal = score_position(my, opp)
    if terminal or depth == 0:
        return score

    occupied = my | opp
    empty = FULL_MASK ^ occupied

    # Exact 1-ply scan for speed.
    if depth == 1:
        best = -INF
        generated = 0

        for q in range(4):
            for d in range(2):
                rmy = rotate_bits(my, q, d)
                ropp = rotate_bits(opp, q, d)
                place_after = PLACE_AFTER[q][d]

                eb = empty
                while eb:
                    lsb = eb & -eb
                    idx = lsb.bit_length() - 1
                    eb ^= lsb

                    nmy = rmy | place_after[idx]
                    child_score, _ = score_position(ropp, nmy)
                    val = -child_score

                    if val > best:
                        best = val
                    if best > alpha:
                        alpha = best
                    if alpha >= beta:
                        return best

                    generated += 1
                    if (generated & 127) == 0:
                        check_time()

        return 0 if best == -INF else best

    empties = 36 - occupied.bit_count()
    limit = internal_limit(depth, empties)
    moves = generate_ordered_moves(my, opp, limit)

    best = -INF
    for _, _, _, _, nmy, nopp in moves:
        val = -search(nopp, nmy, depth - 1, -beta, -alpha)

        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta or best >= WIN_SCORE:
            break

    return 0 if best == -INF else best


def policy(you, opponent) -> str:
    global DEADLINE, NODE_COUNTER
    DEADLINE = perf_counter() + 0.92
    NODE_COUNTER = 0

    my, opp = bits_from_arrays(you, opponent)
    occupied = my | opp
    empty = FULL_MASK ^ occupied

    # Guaranteed legal fallback.
    lsb = empty & -empty
    fallback_idx = lsb.bit_length() - 1
    best_move = MOVE_STRS[fallback_idx][0][0]

    try:
        ordered_root = generate_ordered_moves(my, opp, None)
        if not ordered_root:
            return best_move

        best_move = MOVE_STRS[ordered_root[0][1]][ordered_root[0][2]][ordered_root[0][3]]

        # Immediate decisive win.
        if ordered_root[0][0] >= WIN_SCORE:
            return best_move

        empties = 36 - occupied.bit_count()
        target_depth = 2
        if empties <= 14:
            target_depth = 3
        if empties <= 8:
            target_depth = 4

        current_root = ordered_root
        completed_best = best_move

        # Depth 1 is already represented by ordered_root's quick scores.
        for depth in range(2, target_depth + 1):
            limit = root_limit(depth, empties, len(current_root))
            slice_root = current_root[:limit]

            rescored = []
            alpha = -INF
            cutoff = limit

            for i, entry in enumerate(slice_root):
                _, idx, q, d, nmy, nopp = entry
                val = -search(nopp, nmy, depth - 1, -INF, -alpha)
                rescored.append((val, idx, q, d, nmy, nopp))

                if val > alpha:
                    alpha = val
                if alpha >= WIN_SCORE:
                    cutoff = i + 1
                    break

            rescored.sort(key=lambda x: x[0], reverse=True)

            if cutoff < limit:
                current_root = rescored + current_root[cutoff:]
            else:
                current_root = rescored + current_root[limit:]

            completed_best = MOVE_STRS[current_root[0][1]][current_root[0][2]][current_root[0][3]]

            if current_root[0][0] >= WIN_SCORE:
                break

        return completed_best

    except SearchTimeout:
        return best_move
