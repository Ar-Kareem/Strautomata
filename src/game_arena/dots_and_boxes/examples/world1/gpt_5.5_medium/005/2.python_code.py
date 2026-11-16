
import time
import numpy as np

# ----- Board constants for a 4x4 box board -----
N = 4
NUM_H = 5 * 4          # horizontal edges: rows 0..4, cols 0..3
NUM_V = 4 * 5          # vertical edges: rows 0..3, cols 0..4
NUM_EDGES = NUM_H + NUM_V
NUM_BOXES = 16

FULL_EDGE_MASK = (1 << NUM_EDGES) - 1
FULL_BOX_MASK = (1 << NUM_BOXES) - 1

EDGE_STR = []
EDGE_BOXES = [[] for _ in range(NUM_EDGES)]
BOX_MASKS = [0 for _ in range(NUM_BOXES)]


def _h_idx(r, c):
    return r * 4 + c


def _v_idx(r, c):
    return NUM_H + r * 5 + c


# Edge strings
for r in range(5):
    for c in range(4):
        EDGE_STR.append(f"{r},{c},H")

for r in range(4):
    for c in range(5):
        EDGE_STR.append(f"{r},{c},V")

# Box masks
for r in range(4):
    for c in range(4):
        b = r * 4 + c
        edges = [
            _h_idx(r, c),
            _h_idx(r + 1, c),
            _v_idx(r, c),
            _v_idx(r, c + 1),
        ]
        mask = 0
        for e in edges:
            mask |= 1 << e
        BOX_MASKS[b] = mask

# Edge-to-adjacent-boxes
for r in range(5):
    for c in range(4):
        e = _h_idx(r, c)
        if r > 0:
            EDGE_BOXES[e].append((r - 1) * 4 + c)
        if r < 4:
            EDGE_BOXES[e].append(r * 4 + c)

for r in range(4):
    for c in range(5):
        e = _v_idx(r, c)
        if c > 0:
            EDGE_BOXES[e].append(r * 4 + (c - 1))
        if c < 4:
            EDGE_BOXES[e].append(r * 4 + c)


def _legal_moves(occ):
    return [m for m in range(NUM_EDGES) if ((occ >> m) & 1) == 0]


def _box_sides(occ, b):
    return (occ & BOX_MASKS[b]).bit_count()


def _cap_count_move(occ, capmask, m):
    cnt = 0
    for b in EDGE_BOXES[m]:
        if ((capmask >> b) & 1) == 0 and _box_sides(occ, b) == 3:
            cnt += 1
    return cnt


def _apply_move(occ, capmask, m):
    new_occ = occ | (1 << m)
    new_capmask = capmask
    captured = 0

    for b in EDGE_BOXES[m]:
        if ((capmask >> b) & 1) == 0:
            if (new_occ & BOX_MASKS[b]) == BOX_MASKS[b]:
                new_capmask |= 1 << b
                captured += 1

    return new_occ, new_capmask, captured


def _creates_three_box(occ, capmask, m):
    for b in EDGE_BOXES[m]:
        if ((capmask >> b) & 1) == 0 and _box_sides(occ, b) == 2:
            return True
    return False


def _is_safe_move(occ, capmask, m):
    return _cap_count_move(occ, capmask, m) == 0 and not _creates_three_box(occ, capmask, m)


def _heuristic_future(occ, capmask, player):
    """
    Returns an estimated future score difference from the original player's view.
    player is 1 if it is our turn, -1 if it is opponent's turn.
    """
    threes = 0
    twos = 0

    for b in range(NUM_BOXES):
        if ((capmask >> b) & 1) == 0:
            s = _box_sides(occ, b)
            if s == 3:
                threes += 1
            elif s == 2:
                twos += 1

    safe = 0
    for m in range(NUM_EDGES):
        if ((occ >> m) & 1) == 0:
            if _is_safe_move(occ, capmask, m):
                safe += 1

    # Immediate 3-sided boxes are valuable to the side to move.
    # Safe mobility is mildly useful. Many 2-sided boxes are slightly volatile.
    return player * (0.85 * threes + 0.04 * safe - 0.06 * twos)


def _estimated_value_after(occ, capmask, player, m):
    new_occ, new_capmask, c = _apply_move(occ, capmask, m)
    gain = player * c
    next_player = player if c > 0 else -player
    return gain + _heuristic_future(new_occ, new_capmask, next_player)


def _order_moves(occ, capmask, player):
    moves = _legal_moves(occ)
    moves.sort(
        key=lambda m: _estimated_value_after(occ, capmask, player, m),
        reverse=(player == 1),
    )
    return moves


def _sacrifice_cost(occ, capmask, m):
    """
    Estimate how many boxes the opponent can greedily take after we play m.
    Used only as a fallback when all moves are unsafe.
    """
    new_occ, new_capmask, c = _apply_move(occ, capmask, m)
    if c > 0:
        return -c

    cost = 0
    occ2 = new_occ
    cap2 = new_capmask

    while True:
        caps = []
        for x in range(NUM_EDGES):
            if ((occ2 >> x) & 1) == 0:
                cc = _cap_count_move(occ2, cap2, x)
                if cc > 0:
                    caps.append((cc, x))

        if not caps:
            break

        caps.sort(reverse=True)
        _, x = caps[0]
        occ2, cap2, got = _apply_move(occ2, cap2, x)
        cost += got

        if cost >= NUM_BOXES:
            break

    return cost


def _static_best_move(occ, capmask):
    legal = _legal_moves(occ)
    if not legal:
        return None

    # 1. Take captures.
    caps = [m for m in legal if _cap_count_move(occ, capmask, m) > 0]
    if caps:
        def cap_key(m):
            new_occ, new_cap, c = _apply_move(occ, capmask, m)
            follow = 0
            for x in range(NUM_EDGES):
                if ((new_occ >> x) & 1) == 0:
                    follow += _cap_count_move(new_occ, new_cap, x)
            return (c, follow, _estimated_value_after(occ, capmask, 1, m))

        return max(caps, key=cap_key)

    # 2. Prefer safe moves.
    safe = [m for m in legal if _is_safe_move(occ, capmask, m)]
    if safe:
        return max(safe, key=lambda m: _estimated_value_after(occ, capmask, 1, m))

    # 3. If forced to open something, open the smallest estimated chain.
    return min(
        legal,
        key=lambda m: (_sacrifice_cost(occ, capmask, m), -_estimated_value_after(occ, capmask, 1, m)),
    )


def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    deadline = time.perf_counter() + 0.88

    occ = 0
    capmask = 0

    # Read valid horizontal edges.
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] != 0:
                occ |= 1 << _h_idx(r, c)

    # Read valid vertical edges.
    for r in range(4):
        for c in range(5):
            if vertical[r, c] != 0:
                occ |= 1 << _v_idx(r, c)

    # Read captured boxes.
    for r in range(4):
        for c in range(4):
            if capture[r, c] != 0:
                capmask |= 1 << (r * 4 + c)

    legal = _legal_moves(occ)

    # Emergency fallback for terminal or malformed calls.
    if not legal:
        for r in range(5):
            for c in range(5):
                if horizontal[r, c] == 0:
                    return f"{r},{c},H"
        for r in range(5):
            for c in range(5):
                if vertical[r, c] == 0:
                    return f"{r},{c},V"
        return "0,0,H"

    fallback = _static_best_move(occ, capmask)
    if fallback is None:
        fallback = legal[0]

    best_move = fallback
    nodes = [0]

    class SearchTimeout(Exception):
        pass

    def check_time():
        nodes[0] += 1
        if (nodes[0] & 1023) == 0:
            if time.perf_counter() > deadline:
                raise SearchTimeout()

    def depth_search(o, cm, player, depth, alpha, beta):
        check_time()

        if o == FULL_EDGE_MASK or cm == FULL_BOX_MASK:
            return 0.0

        if depth <= 0:
            return _heuristic_future(o, cm, player)

        moves = _order_moves(o, cm, player)

        if player == 1:
            best = -1000.0
            for m in moves:
                no, ncm, c = _apply_move(o, cm, m)
                gain = c
                np_next = player if c > 0 else -player
                nd = depth if c > 0 else depth - 1
                val = gain + depth_search(no, ncm, np_next, nd, alpha, beta)
                if val > best:
                    best = val
                if best > alpha:
                    alpha = best
                if alpha >= beta:
                    break
            return best
        else:
            best = 1000.0
            for m in moves:
                no, ncm, c = _apply_move(o, cm, m)
                gain = -c
                np_next = player if c > 0 else -player
                nd = depth if c > 0 else depth - 1
                val = gain + depth_search(no, ncm, np_next, nd, alpha, beta)
                if val < best:
                    best = val
                if best < beta:
                    beta = best
                if alpha >= beta:
                    break
            return best

    def choose_depth(depth):
        moves = _order_moves(occ, capmask, 1)
        bm = moves[0]
        bv = -1000.0
        alpha = -1000.0
        beta = 1000.0

        for m in moves:
            if time.perf_counter() > deadline:
                raise SearchTimeout()

            no, ncm, c = _apply_move(occ, capmask, m)
            np_next = 1 if c > 0 else -1
            nd = depth if c > 0 else depth - 1
            val = c + depth_search(no, ncm, np_next, nd, alpha, beta)

            if val > bv:
                bv = val
                bm = m

            if bv > alpha:
                alpha = bv

        return bm

    def choose_exact():
        cache = {}

        def exact(o, cm, player, alpha, beta):
            check_time()

            if o == FULL_EDGE_MASK or cm == FULL_BOX_MASK:
                return 0

            key = (o, cm, player)
            if key in cache:
                return cache[key]

            moves = _order_moves(o, cm, player)

            if player == 1:
                best = -1000
                a = alpha
                for m in moves:
                    no, ncm, c = _apply_move(o, cm, m)
                    np_next = player if c > 0 else -player
                    val = c + exact(no, ncm, np_next, a, beta)
                    if val > best:
                        best = val
                    if best > a:
                        a = best
                    if a >= beta:
                        return best
                cache[key] = best
                return best
            else:
                best = 1000
                bnd = beta
                for m in moves:
                    no, ncm, c = _apply_move(o, cm, m)
                    np_next = player if c > 0 else -player
                    val = -c + exact(no, ncm, np_next, alpha, bnd)
                    if val < best:
                        best = val
                    if best < bnd:
                        bnd = best
                    if alpha >= bnd:
                        return best
                cache[key] = best
                return best

        moves = _order_moves(occ, capmask, 1)
        bm = moves[0]
        bv = -1000
        alpha = -1000
        beta = 1000

        for m in moves:
            if time.perf_counter() > deadline:
                raise SearchTimeout()

            no, ncm, c = _apply_move(occ, capmask, m)
            np_next = 1 if c > 0 else -1
            val = c + exact(no, ncm, np_next, alpha, beta)

            if val > bv:
                bv = val
                bm = m

            if bv > alpha:
                alpha = bv

        return bm

    try:
        remaining = len(legal)

        # Try exact solving in late endgames.
        if remaining <= 20:
            best_move = choose_exact()
        else:
            # Iterative deepening. Keep the last fully completed result.
            for d in range(2, 7):
                best_move = choose_depth(d)
                if time.perf_counter() > deadline:
                    break

    except SearchTimeout:
        pass
    except Exception:
        # Never risk returning an illegal move because of an internal error.
        best_move = fallback

    # Final legality guard.
    if ((occ >> best_move) & 1) == 0:
        return EDGE_STR[best_move]

    if ((occ >> fallback) & 1) == 0:
        return EDGE_STR[fallback]

    for m in range(NUM_EDGES):
        if ((occ >> m) & 1) == 0:
            return EDGE_STR[m]

    # Should be unreachable except on terminal/malformed states.
    return "0,0,H"
