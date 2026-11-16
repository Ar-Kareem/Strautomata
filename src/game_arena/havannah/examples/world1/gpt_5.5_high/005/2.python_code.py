
from collections import deque
import math

_CACHE = {}


class _Info:
    __slots__ = (
        "h", "w", "M", "cells", "index", "neighbors",
        "edge_bits", "corner_bits", "boundary",
        "center_dist", "edge_dists", "corner_dists"
    )


def _popcount(x):
    return x.bit_count()


def _mask_key(valid_mask):
    h = len(valid_mask)
    w = len(valid_mask[0]) if h else 0
    bits = []
    for r in range(h):
        row = valid_mask[r]
        for c in range(w):
            bits.append(bool(row[c]))
    return (h, w, tuple(bits))


def _bfs_dist(neighbors, sources):
    m = len(neighbors)
    dist = [99] * m
    q = deque()
    for s in sources:
        if 0 <= s < m and dist[s] != 0:
            dist[s] = 0
            q.append(s)
    while q:
        v = q.popleft()
        nd = dist[v] + 1
        for nb in neighbors[v]:
            if dist[nb] > nd:
                dist[nb] = nd
                q.append(nb)
    return dist


def _get_info(valid_mask):
    key = _mask_key(valid_mask)
    got = _CACHE.get(key)
    if got is not None:
        return got

    h, w = key[0], key[1]
    info = _Info()
    info.h = h
    info.w = w

    cells = []
    index = {}
    for r in range(h):
        for c in range(w):
            if bool(valid_mask[r][c]):
                index[(r, c)] = len(cells)
                cells.append((r, c))

    info.cells = cells
    info.index = index
    info.M = len(cells)

    if not cells:
        info.neighbors = []
        info.edge_bits = []
        info.corner_bits = []
        info.boundary = []
        info.center_dist = []
        info.edge_dists = [[] for _ in range(6)]
        info.corner_dists = [[] for _ in range(6)]
        _CACHE[key] = info
        return info

    # Offset-column hex neighbors. For odd columns this exactly matches:
    # (4,1) touches (3,0),(4,0),(3,1),(5,1),(3,2),(4,2).
    odd_dirs = [(-1, 0), (1, 0), (-1, -1), (0, -1), (-1, 1), (0, 1)]
    even_dirs = [(-1, 0), (1, 0), (0, -1), (1, -1), (0, 1), (1, 1)]

    neighbors = [[] for _ in cells]
    for i, (r, c) in enumerate(cells):
        dirs = odd_dirs if (c & 1) else even_dirs
        ns = []
        for dr, dc in dirs:
            j = index.get((r + dr, c + dc))
            if j is not None:
                ns.append(j)
        neighbors[i] = ns

    info.neighbors = neighbors

    rows = [p[0] for p in cells]
    cols = [p[1] for p in cells]
    min_r, max_r = min(rows), max(rows)
    min_c, max_c = min(cols), max(cols)

    row_min = {}
    row_max = {}
    col_min = {}
    col_max = {}
    for r, c in cells:
        row_min[r] = min(row_min.get(r, c), c)
        row_max[r] = max(row_max.get(r, c), c)
        col_min[c] = min(col_min.get(c, r), r)
        col_max[c] = max(col_max.get(c, r), r)

    # Six geometric corners in clockwise order.
    corners = [
        (min_r, row_min[min_r]),
        (min_r, row_max[min_r]),
        (col_min[max_c], max_c),
        (max_r, row_max[max_r]),
        (max_r, row_min[max_r]),
        (col_max[min_c], min_c),
    ]

    corner_bits = [0] * len(cells)
    for bit, coord in enumerate(corners):
        j = index.get(coord)
        if j is not None:
            corner_bits[j] |= (1 << bit)

    edge_bits = [0] * len(cells)

    c0, c1, c2, c3, c4, c5 = corners
    e1_lo, e1_hi = sorted((c1[1], c2[1]))
    e4_lo, e4_hi = sorted((c5[1], c4[1]))

    for i, (r, c) in enumerate(cells):
        # Corners are not considered parts of edges for fork purposes.
        if corner_bits[i]:
            continue

        eb = 0
        if r == min_r:
            eb |= 1 << 0
        if e1_lo <= c <= e1_hi and r == col_min[c]:
            eb |= 1 << 1
        if c == max_c:
            eb |= 1 << 2
        if r == max_r:
            eb |= 1 << 3
        if e4_lo <= c <= e4_hi and r == col_max[c]:
            eb |= 1 << 4
        if c == min_c:
            eb |= 1 << 5
        edge_bits[i] = eb

    info.edge_bits = edge_bits
    info.corner_bits = corner_bits
    info.boundary = [len(neighbors[i]) < 6 for i in range(len(cells))]

    avg_r = sum(rows) / float(len(rows))
    avg_c = sum(cols) / float(len(cols))
    center_idx = min(
        range(len(cells)),
        key=lambda i: (cells[i][0] - avg_r) ** 2 + (cells[i][1] - avg_c) ** 2,
    )
    info.center_dist = _bfs_dist(neighbors, [center_idx])

    info.edge_dists = []
    for e in range(6):
        src = [i for i, b in enumerate(edge_bits) if b & (1 << e)]
        info.edge_dists.append(_bfs_dist(neighbors, src))

    info.corner_dists = []
    for cbit in range(6):
        src = [i for i, b in enumerate(corner_bits) if b & (1 << cbit)]
        info.corner_dists.append(_bfs_dist(neighbors, src))

    if len(_CACHE) > 8:
        _CACHE.clear()
    _CACHE[key] = info
    return info


def _component_stats(stones, start, info):
    seen = {start}
    stack = [start]
    size = 0
    eb = 0
    cb = 0

    while stack:
        v = stack.pop()
        if v not in stones:
            continue
        size += 1
        eb |= info.edge_bits[v]
        cb |= info.corner_bits[v]
        for nb in info.neighbors[v]:
            if nb in stones and nb not in seen:
                seen.add(nb)
                stack.append(nb)

    return size, eb, cb


def _surrounds_single_cell(stones, move, info):
    # Covers the uncommon but legal case where the enclosed cell is also
    # occupied by the ring-forming player.
    for center in info.neighbors[move]:
        ring = info.neighbors[center]
        if len(ring) != 6:
            continue
        ok = True
        for nb in ring:
            if nb not in stones:
                ok = False
                break
        if ok:
            return True
    return False


def _has_ring(stones, move, info):
    if len(stones) < 6:
        return False

    same_adj = 0
    for nb in info.neighbors[move]:
        if nb in stones:
            same_adj += 1
    if same_adj < 2:
        return False

    if _surrounds_single_cell(stones, move, info):
        return True

    # Treat this player's stones as walls. If any non-wall playable cell is
    # unreachable from the outside boundary, it is enclosed by a ring.
    visited = bytearray(info.M)
    q = deque()

    for i in range(info.M):
        if info.boundary[i] and i not in stones:
            visited[i] = 1
            q.append(i)

    while q:
        v = q.popleft()
        for nb in info.neighbors[v]:
            if not visited[nb] and nb not in stones:
                visited[nb] = 1
                q.append(nb)

    for i in range(info.M):
        if i not in stones and not visited[i]:
            return True
    return False


def _win_from_move(stones, move, info):
    _, eb, cb = _component_stats(stones, move, info)

    # Bridge: connected component touches at least two corners.
    if _popcount(cb) >= 2:
        return True

    # Fork: connected component touches at least three non-corner edges.
    if _popcount(eb) >= 3:
        return True

    # Ring.
    return _has_ring(stones, move, info)


def _ring_potential(stones, move, info):
    total = 0
    for center in info.neighbors[move]:
        ring = info.neighbors[center]
        if len(ring) != 6:
            continue
        cnt = 0
        for nb in ring:
            if nb == move or nb in stones:
                cnt += 1

        if cnt >= 6:
            total += 5000
        elif cnt == 5:
            total += 1100
        elif cnt == 4:
            total += 260
        elif cnt == 3:
            total += 60
    return total


def _basic_score(move, me_set, opp_set, info, stage, opp_win_set):
    neigh = info.neighbors[move]
    own_adj = sum(1 for nb in neigh if nb in me_set)
    opp_adj = sum(1 for nb in neigh if nb in opp_set)
    empty_adj = len(neigh) - own_adj - opp_adj

    score = 0.0
    dist = info.center_dist[move]

    # Central control is strongest early; later, structure matters more.
    if stage < 10:
        score += 180.0 - 15.0 * dist
    else:
        score += 95.0 - 5.5 * dist

    if own_adj == 0:
        score -= 90.0 if stage > 4 else 5.0
    else:
        score += 55.0 * own_adj + 20.0 * own_adj * own_adj
        if own_adj >= 2:
            score += 80.0

    score += 28.0 * opp_adj + 10.0 * opp_adj * opp_adj
    score += 3.0 * empty_adj

    my_stones = set(me_set)
    my_stones.add(move)
    size, eb, cb = _component_stats(my_stones, move, info)
    ec = _popcount(eb)
    cc = _popcount(cb)

    score += 10.0 * size + 2.0 * min(size, 20)
    score += 190.0 * ec * ec + 240.0 * cc
    if ec == 2:
        score += 750.0
    if cc == 1:
        score += 260.0
    if cc >= 1 and ec >= 1:
        score += 100.0

    if info.edge_bits[move]:
        score += 70.0
    if info.corner_bits[move]:
        score += 110.0

    # Do not rush to the rim in the first few moves unless tactically needed.
    if stage < 8:
        if info.corner_bits[move]:
            score -= 220.0
        elif info.edge_bits[move]:
            score -= 80.0

    # Extension toward new fork edges.
    if ec:
        vals = []
        for e in range(6):
            if not (eb & (1 << e)):
                vals.append(info.edge_dists[e][move])
        if vals:
            d = min(vals)
            if d < 99:
                score += (150.0 * ec) / (d + 1.0)
                if ec == 2:
                    score += 900.0 / (d + 1.0)

    # Extension toward another bridge corner.
    if cc:
        vals = []
        for c in range(6):
            if not (cb & (1 << c)):
                vals.append(info.corner_dists[c][move])
        if vals:
            d = min(vals)
            if d < 99:
                score += 500.0 / (d + 1.0)

    # Defensive denial: how good would this point be for the opponent?
    opp_stones = set(opp_set)
    opp_stones.add(move)
    osize, oeb, ocb = _component_stats(opp_stones, move, info)
    oec = _popcount(oeb)
    occ = _popcount(ocb)

    score += 6.0 * osize + 35.0 * opp_adj
    score += 130.0 * oec * oec + 180.0 * occ
    if oec == 2:
        score += 650.0
    if occ == 1:
        score += 220.0

    if oec:
        vals = []
        for e in range(6):
            if not (oeb & (1 << e)):
                vals.append(info.edge_dists[e][move])
        if vals:
            d = min(vals)
            if d < 99:
                score += (80.0 * oec) / (d + 1.0)

    if occ:
        vals = []
        for c in range(6):
            if not (ocb & (1 << c)):
                vals.append(info.corner_dists[c][move])
        if vals:
            d = min(vals)
            if d < 99:
                score += 260.0 / (d + 1.0)

    score += 1.05 * _ring_potential(me_set, move, info)
    score += 0.85 * _ring_potential(opp_set, move, info)

    if move in opp_win_set:
        score += 80000.0

    # Tiny deterministic tie breaker.
    r, c = info.cells[move]
    score += ((r * 37 + c * 17) % 13) * 0.001
    return score


def _count_winning_replies(stones, just_played, legal, info, limit=3):
    count = 0
    for x in legal:
        if x == just_played or x in stones:
            continue
        stones.add(x)
        if _win_from_move(stones, x, info):
            count += 1
            stones.remove(x)
            if count >= limit:
                break
        else:
            stones.remove(x)
    return count


def _fallback(valid_mask, me, opp):
    occupied = set()
    for seq in (me, opp):
        for p in seq:
            try:
                occupied.add((int(p[0]), int(p[1])))
            except Exception:
                pass

    try:
        h = len(valid_mask)
        w = len(valid_mask[0]) if h else 0
    except Exception:
        return (0, 0)

    cr = (h - 1) / 2.0
    cc = (w - 1) / 2.0
    best = None
    best_d = 10 ** 9

    for r in range(h):
        for c in range(w):
            try:
                ok = bool(valid_mask[r][c])
            except Exception:
                ok = False
            if ok and (r, c) not in occupied:
                d = (r - cr) ** 2 + (c - cc) ** 2
                if d < best_d:
                    best_d = d
                    best = (r, c)

    return best if best is not None else (0, 0)


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    try:
        info = _get_info(valid_mask)
        if info.M == 0:
            return (0, 0)

        me_set = set()
        opp_set = set()

        for p in me:
            idx = info.index.get((int(p[0]), int(p[1])))
            if idx is not None:
                me_set.add(idx)

        for p in opp:
            idx = info.index.get((int(p[0]), int(p[1])))
            if idx is not None:
                opp_set.add(idx)

        occupied = me_set | opp_set
        legal = [i for i in range(info.M) if i not in occupied]

        if not legal:
            return info.cells[0]

        # Opening: take the most central available point.
        if len(me_set) == 0:
            best = min(legal, key=lambda i: info.center_dist[i])
            return info.cells[best]

        central_order = sorted(legal, key=lambda i: info.center_dist[i])

        # 1. Win immediately if possible.
        for m in central_order:
            me_set.add(m)
            won = _win_from_move(me_set, m, info)
            me_set.remove(m)
            if won:
                return info.cells[m]

        # 2. Block the opponent's immediate win if there is exactly one.
        opp_wins = []
        for m in legal:
            opp_set.add(m)
            won = _win_from_move(opp_set, m, info)
            opp_set.remove(m)
            if won:
                opp_wins.append(m)

        if len(opp_wins) == 1:
            return info.cells[opp_wins[0]]

        opp_win_set = set(opp_wins)
        stage = len(me_set) + len(opp_set)

        base = {}
        multi_opp_threat = len(opp_wins) > 1
        for m in legal:
            s = _basic_score(m, me_set, opp_set, info, stage, opp_win_set)
            if multi_opp_threat:
                # If several opponent wins exist, at least occupy one of them.
                if m in opp_win_set:
                    s += 60000.0
                else:
                    s -= 60000.0
            base[m] = s

        ordered = sorted(legal, key=lambda i: base[i], reverse=True)

        # 3. Refine strongest candidates by next-turn threats.
        top_n = 24 if len(ordered) > 60 else min(32, len(ordered))
        best = ordered[0]
        best_score = -1e100

        for rank, m in enumerate(ordered[:top_n]):
            s = base[m] - 0.01 * rank

            if multi_opp_threat:
                remaining = len(opp_wins) - (1 if m in opp_win_set else 0)
                s -= 120000.0 * remaining

            me_set.add(m)
            threats = _count_winning_replies(me_set, m, legal, info, limit=3)
            me_set.remove(m)

            if threats == 1:
                s += 1800.0
            elif threats >= 2:
                s += 9000.0 + 2500.0 * threats

            if s > best_score:
                best_score = s
                best = m

        return info.cells[best]

    except Exception:
        return _fallback(valid_mask, me, opp)
