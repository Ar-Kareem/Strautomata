
import time
import numpy as np

# Standard 4x4 boxes = 5x5 dots. Edge arrays are padded to 5x5 by the arena;
# the valid edges are H[r,c] for r=0..4,c=0..3 and V[r,c] for r=0..3,c=0..4.
BOX_R = 4
BOX_C = 4
N_EDGES = 40
FULL_MASK = (1 << N_EDGES) - 1
INF = 10 ** 9
CAP_W = 12

# Exact-search control. The fallback move is computed before exact search starts,
# so a timeout still returns a legal, reasonable move.
TIME_LIMIT = 0.82
EXACT_ATTEMPT_LIMIT = 22
_SEARCH = [0, 0.0]  # nodes, deadline


class _Timeout(Exception):
    pass


def _build_tables():
    box_masks = []
    edge_boxes = [[] for _ in range(N_EDGES)]
    edge_req = [[] for _ in range(N_EDGES)]

    def h_id(r, c):
        return r * 4 + c

    def v_id(r, c):
        return 20 + r * 5 + c

    def b_id(r, c):
        return r * 4 + c

    for r in range(BOX_R):
        for c in range(BOX_C):
            ids = (h_id(r, c), h_id(r + 1, c), v_id(r, c), v_id(r, c + 1))
            m = 0
            for e in ids:
                m |= 1 << e
            box_masks.append(m)

    for r in range(5):
        for c in range(4):
            e = h_id(r, c)
            bit = 1 << e
            if r > 0:
                b = b_id(r - 1, c)
                edge_boxes[e].append(b)
                edge_req[e].append((box_masks[b] ^ bit, box_masks[b]))
            if r < BOX_R:
                b = b_id(r, c)
                edge_boxes[e].append(b)
                edge_req[e].append((box_masks[b] ^ bit, box_masks[b]))

    for r in range(4):
        for c in range(5):
            e = v_id(r, c)
            bit = 1 << e
            if c > 0:
                b = b_id(r, c - 1)
                edge_boxes[e].append(b)
                edge_req[e].append((box_masks[b] ^ bit, box_masks[b]))
            if c < BOX_C:
                b = b_id(r, c)
                edge_boxes[e].append(b)
                edge_req[e].append((box_masks[b] ^ bit, box_masks[b]))

    edge_priority = [0 if len(edge_boxes[e]) == 1 else 1 for e in range(N_EDGES)]
    return box_masks, edge_boxes, edge_req, edge_priority


BOX_MASKS, EDGE_BOXES, EDGE_REQ, EDGE_PRIORITY = _build_tables()
_EXACT_TT = {}
_FLAG_EXACT = 0
_FLAG_LOWER = 1
_FLAG_UPPER = 2


def _mask_from_arrays(horizontal, vertical):
    mask = 0
    for r in range(5):
        base = r * 4
        for c in range(4):
            if horizontal[r, c] != 0:
                mask |= 1 << (base + c)
    for r in range(4):
        base = 20 + r * 5
        for c in range(5):
            if vertical[r, c] != 0:
                mask |= 1 << (base + c)
    return mask


def _edge_gain(mask, e):
    g = 0
    for need, full in EDGE_REQ[e]:
        if (mask & full) == need:
            g += 1
    return g


def _count3(mask):
    n = 0
    for bm in BOX_MASKS:
        if (mask & bm).bit_count() == 3:
            n += 1
    return n


def _static_pos_value(mask):
    """Fast one-ply value for the player to move, used only outside exact endgame."""
    avail = FULL_MASK & ~mask
    if avail == 0:
        return 0

    c3 = 0
    c2 = 0
    for bm in BOX_MASKS:
        pc = (mask & bm).bit_count()
        if pc == 3:
            c3 += 1
        elif pc == 2:
            c2 += 1

    if c3:
        max_gain = 0
        a = avail
        while a:
            lb = a & -a
            a -= lb
            e = lb.bit_length() - 1
            g = _edge_gain(mask, e)
            if g > max_gain:
                max_gain = g
        return CAP_W * max_gain + 4 * (c3 - max_gain) + (1 if c2 else 0)

    # No immediate capture: if a safe move exists value is about 0; otherwise the
    # side to move must open something, so estimate the smallest offered threat.
    best_damage = None
    a = avail
    while a:
        lb = a & -a
        a -= lb
        m2 = mask | lb
        oc3 = 0
        oc2 = 0
        for bm in BOX_MASKS:
            pc = (m2 & bm).bit_count()
            if pc == 3:
                oc3 += 1
            elif pc == 2:
                oc2 += 1
        damage = (oc3, oc2)
        if best_damage is None or damage < best_damage:
            best_damage = damage

    if best_damage[0] == 0:
        return 0
    return -(CAP_W * best_damage[0] + 3 * best_damage[1])


def _ordered_root_moves(mask):
    avail = FULL_MASK & ~mask
    moves = []
    a = avail
    while a:
        lb = a & -a
        a -= lb
        e = lb.bit_length() - 1
        g = _edge_gain(mask, e)
        m2 = mask | lb
        if g:
            value = CAP_W * g + _static_pos_value(m2)
            safe_key = 0
        else:
            value = -_static_pos_value(m2)
            max_sc = 0
            side_sum = 0
            for b in EDGE_BOXES[e]:
                pc = (m2 & BOX_MASKS[b]).bit_count()
                if pc > max_sc:
                    max_sc = pc
                side_sum += pc
            safe_key = -(10 * max_sc + side_sum)
        moves.append(((value, safe_key, -EDGE_PRIORITY[e], -e), e, g, m2))
    moves.sort(key=lambda x: x[0], reverse=True)
    return moves


def _solve_exact(mask, alpha=-INF, beta=INF):
    ent = _EXACT_TT.get(mask)
    if ent is not None:
        val, flag = ent
        if flag == _FLAG_EXACT:
            return val
        if flag == _FLAG_LOWER:
            if val > alpha:
                alpha = val
        else:
            if val < beta:
                beta = val
        if alpha >= beta:
            return val

    if (mask & FULL_MASK) == FULL_MASK:
        return 0

    _SEARCH[0] += 1
    if (_SEARCH[0] & 1023) == 0 and time.monotonic() > _SEARCH[1]:
        raise _Timeout()

    alpha0, beta0 = alpha, beta
    best = -INF

    avail = FULL_MASK & ~mask
    moves = []
    a = avail
    while a:
        lb = a & -a
        a -= lb
        e = lb.bit_length() - 1
        g = _edge_gain(mask, e)
        # Captures first (larger first), then boundary/safer-looking edges.
        key = (0 if g else 1, -g, EDGE_PRIORITY[e], e)
        moves.append((key, e, g, lb))
    moves.sort(key=lambda x: x[0])

    for _, e, g, lb in moves:
        m2 = mask | lb
        if g:
            # Same player moves again; shift the window by the immediate gain.
            score = g + _solve_exact(m2, alpha - g, beta - g)
        else:
            score = -_solve_exact(m2, -beta, -alpha)

        if score > best:
            best = score
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    if best <= alpha0:
        flag = _FLAG_UPPER
    elif best >= beta0:
        flag = _FLAG_LOWER
    else:
        flag = _FLAG_EXACT
    _EXACT_TT[mask] = (best, flag)
    return best


def _edge_name(e):
    if e < 20:
        return f"{e // 4},{e % 4},H"
    j = e - 20
    return f"{j // 5},{j % 5},V"


def _any_zero_edge(horizontal, vertical):
    for r in range(horizontal.shape[0]):
        for c in range(horizontal.shape[1]):
            if horizontal[r, c] == 0:
                return f"{r},{c},H"
    for r in range(vertical.shape[0]):
        for c in range(vertical.shape[1]):
            if vertical[r, c] == 0:
                return f"{r},{c},V"
    return "0,0,H"


def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    mask = _mask_from_arrays(horizontal, vertical)
    moves = _ordered_root_moves(mask)
    if not moves:
        return _any_zero_edge(horizontal, vertical)

    fallback_edge = moves[0][1]
    empty_edges = N_EDGES - (mask & FULL_MASK).bit_count()
    chosen = fallback_edge

    if empty_edges <= EXACT_ATTEMPT_LIMIT:
        _SEARCH[0] = 0
        _SEARCH[1] = time.monotonic() + TIME_LIMIT
        try:
            best_val = -INF
            best_edge = fallback_edge
            for _, e, g, m2 in moves:
                if g:
                    val = g + _solve_exact(m2)
                else:
                    val = -_solve_exact(m2)
                if val > best_val:
                    best_val = val
                    best_edge = e
            chosen = best_edge
        except _Timeout:
            chosen = fallback_edge

    return _edge_name(chosen)
