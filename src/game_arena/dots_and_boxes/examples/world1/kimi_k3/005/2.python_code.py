
import time
import numpy as np

_INF = 10 ** 9
_TT = {}
_deadline = 0.0
_nodes = 0


class _TO(Exception):
    pass


def _cands(r, c, d):
    # Boxes (i,j) in 0..3 x 0..3 adjacent to edge (r,c,d). d: 0=H, 1=V.
    if d == 0:  # horizontal edge h[r,c], legal for r 0..4, c 0..3
        out = []
        if r <= 3:
            out.append((r, c))      # this edge is the top of box (r,c)
        if r >= 1:
            out.append((r - 1, c))  # this edge is the bottom of box (r-1,c)
        return out
    else:        # vertical edge v[r,c], legal for r 0..3, c 0..4
        out = []
        if c <= 3:
            out.append((r, c))      # left of box (r,c)
        if c >= 1:
            out.append((r, c - 1))  # right of box (r,c-1)
        return out


def _apply(h, v, cap, r, c, d, player):
    h2 = h.copy(); v2 = v.copy(); cap2 = cap.copy()
    if d == 0:
        h2[r, c] = player
    else:
        v2[r, c] = player
    got = 0
    for (i, j) in _cands(r, c, d):
        if 0 <= i <= 3 and 0 <= j <= 3 and cap2[i, j] == 0:
            if h2[i, j] != 0 and h2[i + 1, j] != 0 and v2[i, j] != 0 and v2[i, j + 1] != 0:
                cap2[i, j] = player
                got += 1
    return h2, v2, cap2, got


def _gen_moves(h, v):
    mv = []
    for r, c in np.argwhere(h[:, :4] == 0):     # H: r 0..4, c 0..3
        mv.append((int(r), int(c), 0))
    for r, c in np.argwhere(v[:4, :] == 0):     # V: r 0..3, c 0..4
        mv.append((int(r), int(c), 1))
    return mv


def _cascade_gain(h, v, cap, player):
    # Boxes `player` would capture by repeatedly taking the forced (3-sided) box.
    h = h.copy(); v = v.copy(); cap = cap.copy()
    sub = cap[0:4, 0:4]
    gain = 0
    for _ in range(20):
        sides = ((h[0:4, 0:4] != 0).astype(np.int16) + (h[1:5, 0:4] != 0).astype(np.int16)
                 + (v[0:4, 0:4] != 0).astype(np.int16) + (v[0:4, 1:5] != 0).astype(np.int16))
        mask = (sides == 3) & (sub == 0)
        if not mask.any():
            break
        ij = np.argwhere(mask)[0]
        i = int(ij[0]); j = int(ij[1])
        if h[i, j] == 0:
            h[i, j] = player
        elif h[i + 1, j] == 0:
            h[i + 1, j] = player
        elif v[i, j] == 0:
            v[i, j] = player
        else:
            v[i, j + 1] = player
        comp = (h[0:4, 0:4] != 0) & (h[1:5, 0:4] != 0) & (v[0:4, 0:4] != 0) & (v[0:4, 1:5] != 0)
        newly = comp & (sub == 0)
        n = int(newly.sum())
        if n <= 0:
            break
        sub[newly] = player
        gain += n
    return gain


def _leaf(h, v, cap, player):
    base = int((cap[0:4, 0:4] == 1).sum() - (cap[0:4, 0:4] == -1).sum())
    g = _cascade_gain(h, v, cap, player)
    return base + g if player == 1 else base - g


def _score_moves(h, v, cap, player, moves):
    out = []
    for (r, c, d) in moves:
        got = 0; t = 0; n1 = 0
        for (i, j) in _cands(r, c, d):
            if cap[i, j] != 0:
                continue
            s = (h[i, j] != 0) + (h[i + 1, j] != 0) + (v[i, j] != 0) + (v[i, j + 1] != 0)
            if s == 3:
                got += 1
            elif s == 2:
                t += 1
            elif s == 1:
                n1 += 1
        if got > 0:
            h2, v2, c2, _ = _apply(h, v, cap, r, c, d, player)
            fol = _cascade_gain(h2, v2, c2, player)       # we keep the turn after capturing
            sc = 1000000 + got * 1000 + fol
        elif t > 0:                                       # gives a box a 3rd side -> chain for opponent
            h2, v2, c2, _ = _apply(h, v, cap, r, c, d, player)
            dmg = _cascade_gain(h2, v2, c2, -player)
            sc = -1000000 * dmg - t
        else:                                             # safe: prefer fresh (0-side) boxes, avoid making 2-sided boxes
            sc = -n1
        out.append((sc, (r, c, d)))
    out.sort(key=lambda x: x[0], reverse=True)
    return out


def _search(h, v, cap, player, depth, alpha, beta):
    global _nodes
    _nodes += 1
    if (_nodes & 511) == 0 and time.perf_counter() > _deadline:
        raise _TO
    key = (h.tobytes(), v.tobytes(), cap.tobytes(), player)
    oa, ob = alpha, beta
    ent = _TT.get(key)
    if ent is not None:
        ed, ev, ef = ent
        if ed >= depth:
            if ef == 0:
                return ev
            if ef == 1 and ev > alpha:
                alpha = ev
            elif ef == 2 and ev < beta:
                beta = ev
            if alpha >= beta:
                return ev
    if depth <= 0:
        return _leaf(h, v, cap, player)
    moves = _gen_moves(h, v)
    if not moves:
        return int((cap[0:4, 0:4] == 1).sum() - (cap[0:4, 0:4] == -1).sum())
    scored = _score_moves(h, v, cap, player, moves)
    if player == 1:
        best = -_INF
        for _, (r, c, d) in scored:
            h2, v2, c2, g = _apply(h, v, cap, r, c, d, player)
            np_ = player if g > 0 else -player          # extra turn on a capture
            val = _search(h2, v2, c2, np_, depth - 1, alpha, beta)
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
    else:
        best = _INF
        for _, (r, c, d) in scored:
            h2, v2, c2, g = _apply(h, v, cap, r, c, d, player)
            np_ = player if g > 0 else -player
            val = _search(h2, v2, c2, np_, depth - 1, alpha, beta)
            if val < best:
                best = val
            if best < beta:
                beta = best
            if alpha >= beta:
                break
    if best <= oa:
        ef = 2
    elif best >= ob:
        ef = 1
    else:
        ef = 0
    _TT[key] = (depth, best, ef)
    return best


def _first_legal(h, v):
    z = np.argwhere(h[:, :4] == 0)
    if len(z):
        return int(z[0][0]), int(z[0][1]), 0
    z = np.argwhere(v[:4, :] == 0)
    if len(z):
        return int(z[0][0]), int(z[0][1]), 1
    return 0, 0, 0


def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    global _TT, _deadline, _nodes
    H = np.asarray(horizontal, dtype=np.int16)
    V = np.asarray(vertical, dtype=np.int16)
    C = np.asarray(capture, dtype=np.int16)

    moves = _gen_moves(H, V)
    if not moves:
        return "0,0,H"

    # Guaranteed-legal, already-strong fallback (captures > safe > shortest chain).
    best = _score_moves(H, V, C, 1, moves)[0][1]

    _TT = {}
    _nodes = 0
    start = time.perf_counter()
    _deadline = start + 0.85
    last = best
    depth = 1
    try:
        while depth <= 64 and time.perf_counter() < _deadline:
            scored = _score_moves(H, V, C, 1, _gen_moves(H, V))
            for idx, (_, mv) in enumerate(scored):      # try previous best first
                if mv == last:
                    scored.insert(0, scored.pop(idx))
                    break
            alpha = -_INF
            best_val = -_INF
            best_mv = scored[0][1]
            for _, (r, c, d) in scored:
                h2, v2, c2, g = _apply(H, V, C, r, c, d, 1)
                np_ = 1 if g > 0 else -1                # extra turn on a capture
                val = _search(h2, v2, c2, np_, depth - 1, alpha, _INF)
                if val > best_val:
                    best_val = val
                    best_mv = (r, c, d)
                if val > alpha:
                    alpha = val
            last = best_mv
            best = best_mv
            depth += 1
    except _TO:
        pass

    r, c, d = best
    # Final legality guard.
    if d == 0:
        if not (0 <= r <= 4 and 0 <= c <= 3) or H[r, c] != 0:
            r, c, d = _first_legal(H, V)
    else:
        if not (0 <= r <= 3 and 0 <= c <= 4) or V[r, c] != 0:
            r, c, d = _first_legal(H, V)
    return "%d,%d,%s" % (r, c, 'H' if d == 0 else 'V')
