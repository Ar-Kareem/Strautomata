
import time

DIR_CHARS = ("L", "R")
FULL_MASK = (1 << 36) - 1
WIN_SCORE = 1_000_000
BOUND = 10_000_000

# Index 0..35 for board cells.
CELL_BITS = tuple(1 << i for i in range(36))

# Heuristic values for 5-cell windows with k stones and no opponent stones.
# Index 5 is unused in scoring because a 5-in-a-row is treated as terminal.
LINE_SCORES = (0, 2, 10, 60, 300, 0)

_NODE_COUNTER = 0


class SearchTimeout(Exception):
    pass


def _idx(r, c):
    return r * 6 + c


def _build_win_masks():
    masks = []
    # Horizontal, vertical, diagonal down-right, diagonal down-left
    for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
        for r in range(6):
            for c in range(6):
                rr = r + 4 * dr
                cc = c + 4 * dc
                if 0 <= rr < 6 and 0 <= cc < 6:
                    m = 0
                    for k in range(5):
                        m |= CELL_BITS[_idx(r + k * dr, c + k * dc)]
                    masks.append(m)
    return tuple(masks)


WIN_MASKS = _build_win_masks()


def _build_cell_weights():
    weights = [0] * 36
    for m in WIN_MASKS:
        b = m
        while b:
            lsb = b & -b
            i = lsb.bit_length() - 1
            weights[i] += 1
            b ^= lsb
    return tuple(weights)


CELL_WEIGHTS = _build_cell_weights()

# Prefer cells that belong to more 5-windows, then more central cells.
CELL_ORDER = tuple(
    sorted(
        range(36),
        key=lambda i: (
            -CELL_WEIGHTS[i],
            abs(2 * (i // 6) - 5) + abs(2 * (i % 6) - 5),
            i,
        ),
    )
)


def _build_rotations():
    rot_masks = [[0, 0] for _ in range(4)]   # [quad][dir]
    rot_steps = [[None, None] for _ in range(4)]  # bit remaps

    for q in range(4):
        br = (q // 2) * 3
        bc = (q % 2) * 3

        for d in (0, 1):  # 0=L, 1=R
            steps = []
            mask = 0
            for i in range(3):
                for j in range(3):
                    src = _idx(br + i, bc + j)
                    if d == 1:  # R
                        ni, nj = j, 2 - i
                    else:       # L
                        ni, nj = 2 - j, i
                    dst = _idx(br + ni, bc + nj)
                    steps.append((CELL_BITS[src], CELL_BITS[dst]))
                    mask |= CELL_BITS[src]
            rot_masks[q][d] = mask
            rot_steps[q][d] = tuple(steps)

    return tuple(tuple(x) for x in rot_masks), tuple(tuple(x) for x in rot_steps)


ROT_MASKS, ROT_STEPS = _build_rotations()

# Rotation ordering: rotate the placement's own quadrant first, then others.
_rot_orders = []
for cell in range(36):
    r, c = divmod(cell, 6)
    own_q = (r // 3) * 2 + (c // 3)
    order = [(own_q, 0), (own_q, 1)]
    for q in range(4):
        if q != own_q:
            order.append((q, 0))
            order.append((q, 1))
    _rot_orders.append(tuple(order))
ROT_ORDER_PER_CELL = tuple(_rot_orders)


def apply_move(my_bits, opp_bits, cell, quad, d):
    # Place marble first.
    my_bits |= CELL_BITS[cell]

    mask = ROT_MASKS[quad][d]
    steps = ROT_STEPS[quad][d]

    new_my = my_bits & ~mask
    new_opp = opp_bits & ~mask

    for src_bit, dst_bit in steps:
        if my_bits & src_bit:
            new_my |= dst_bit
        if opp_bits & src_bit:
            new_opp |= dst_bit

    return new_my, new_opp


def analyze(my_bits, opp_bits):
    """
    Returns:
      my_win, opp_win, heuristic_score_from_my_perspective
    """
    score = 0
    my_win = False
    opp_win = False
    my4 = 0
    opp4 = 0
    my3 = 0
    opp3 = 0

    for mask in WIN_MASKS:
        a = (my_bits & mask).bit_count()
        b = (opp_bits & mask).bit_count()

        if a == 5:
            my_win = True
        if b == 5:
            opp_win = True

        if a and b:
            continue

        if a:
            score += LINE_SCORES[a]
            if a == 4:
                my4 += 1
            elif a == 3:
                my3 += 1
        elif b:
            score -= LINE_SCORES[b]
            if b == 4:
                opp4 += 1
            elif b == 3:
                opp3 += 1

    # Extra weight for multiple simultaneous threats.
    if my4 > 1:
        score += 400 * (my4 - 1) * (my4 - 1)
    if opp4 > 1:
        score -= 400 * (opp4 - 1) * (opp4 - 1)

    if my3 > 1:
        score += 30 * (my3 - 1)
    if opp3 > 1:
        score -= 30 * (opp3 - 1)

    return my_win, opp_win, score


def iter_moves(empty_mask):
    for cell in CELL_ORDER:
        if empty_mask & CELL_BITS[cell]:
            for quad, d in ROT_ORDER_PER_CELL[cell]:
                yield (cell, quad, d)


def negamax(my_bits, opp_bits, depth, alpha, beta, ply, deadline):
    global _NODE_COUNTER
    _NODE_COUNTER += 1
    if (_NODE_COUNTER & 255) == 0 and time.perf_counter() > deadline:
        raise SearchTimeout

    my_win, opp_win, static_score = analyze(my_bits, opp_bits)
    occupied = my_bits | opp_bits

    if my_win or opp_win or occupied == FULL_MASK:
        if my_win and opp_win:
            return 0
        if my_win:
            return WIN_SCORE - ply
        if opp_win:
            return -WIN_SCORE + ply
        return 0

    if depth == 0:
        return static_score

    best = -BOUND
    empty_mask = FULL_MASK ^ occupied

    for cell in CELL_ORDER:
        if not (empty_mask & CELL_BITS[cell]):
            continue
        for quad, d in ROT_ORDER_PER_CELL[cell]:
            nmy, nopp = apply_move(my_bits, opp_bits, cell, quad, d)
            score = -negamax(nopp, nmy, depth - 1, -beta, -alpha, ply + 1, deadline)

            if score > best:
                best = score
            if best > alpha:
                alpha = best
            if alpha >= beta:
                return best

    return best


def root_search(my_bits, opp_bits, depth, move_order, deadline, root_children):
    alpha = -BOUND
    beta = BOUND
    best_move = move_order[0]
    best_score = -BOUND
    scores = {}
    evaluated = 0

    for mv in move_order:
        if time.perf_counter() > deadline:
            if evaluated == 0:
                raise SearchTimeout
            break

        nmy, nopp = root_children[mv]

        try:
            score = -negamax(nopp, nmy, depth - 1, -beta, -alpha, 1, deadline)
        except SearchTimeout:
            if evaluated == 0:
                raise
            break

        scores[mv] = score
        evaluated += 1

        if score > best_score:
            best_score = score
            best_move = mv
        if score > alpha:
            alpha = score

    if evaluated == 0:
        raise SearchTimeout

    ordered = sorted(move_order, key=lambda m: scores.get(m, -BOUND - 1), reverse=True)
    return best_move, best_score, ordered


def move_to_str(move):
    cell, quad, d = move
    row = cell // 6 + 1
    col = cell % 6 + 1
    return f"{row},{col},{quad},{DIR_CHARS[d]}"


def policy(you, opponent) -> str:
    my_bits = 0
    opp_bits = 0

    # Parse input arrays / array-like objects.
    for r in range(6):
        yr = you[r]
        orow = opponent[r]
        for c in range(6):
            if int(yr[c]) == 1:
                my_bits |= CELL_BITS[_idx(r, c)]
            elif int(orow[c]) == 1:
                opp_bits |= CELL_BITS[_idx(r, c)]

    occupied = my_bits | opp_bits
    empty_mask = FULL_MASK ^ occupied

    moves = list(iter_moves(empty_mask))
    if not moves:
        # Should never happen per prompt, but still return a syntactically valid move.
        return "1,1,0,L"

    fallback = moves[0]
    best_move = fallback

    # Pre-scan all root moves:
    # - immediate winning move
    # - initial heuristic ordering
    # - cached child states for root search
    root_children = {}
    initial_scores = {}
    draw_move = None

    for mv in moves:
        cell, quad, d = mv
        nmy, nopp = apply_move(my_bits, opp_bits, cell, quad, d)
        root_children[mv] = (nmy, nopp)

        my_win, opp_win, static_score = analyze(nmy, nopp)

        if my_win and not opp_win:
            return move_to_str(mv)

        if my_win and opp_win:
            if draw_move is None:
                draw_move = mv
            initial_scores[mv] = 0
        elif opp_win:
            initial_scores[mv] = -WIN_SCORE + 1
        else:
            initial_scores[mv] = static_score

    ordered = sorted(moves, key=lambda m: initial_scores[m], reverse=True)
    best_move = ordered[0]
    if draw_move is not None and initial_scores[best_move] < 0:
        best_move = draw_move

    empties = 36 - occupied.bit_count()
    if empties <= 5:
        target_depth = 4
    elif empties <= 12:
        target_depth = 3
    else:
        target_depth = 2

    deadline = time.perf_counter() + 0.92

    global _NODE_COUNTER
    _NODE_COUNTER = 0

    try:
        for depth in range(2, target_depth + 1):
            mv, score, ordered = root_search(
                my_bits, opp_bits, depth, ordered, deadline, root_children
            )
            best_move = mv
            if abs(score) >= WIN_SCORE - 10:
                break
    except SearchTimeout:
        pass
    except Exception:
        # Safety-first: always return a legal move.
        pass

    return move_to_str(best_move)
