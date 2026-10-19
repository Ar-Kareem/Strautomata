
import math
from collections import deque

N = 15

# Hex neighbours for the coordinate system described in the prompt.
DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1)]


def _truth(v):
    try:
        return bool(v)
    except Exception:
        return False


def _valid_cells(valid_mask):
    cells = []
    n = len(valid_mask)
    for r in range(n):
        for c in range(len(valid_mask[r])):
            if _truth(valid_mask[r][c]):
                cells.append((r, c))
    return cells


def _make_geom(valid_mask):
    cells = _valid_cells(valid_mask)
    cellset = set(cells)

    # Corners: playable cells with minimal degree on the hex-board boundary.
    deg = {}
    for p in cells:
        r, c = p
        d = 0
        for dr, dc in DIRS:
            if (r + dr, c + dc) in cellset:
                d += 1
        deg[p] = d
    corners = [p for p in cells if deg[p] <= 3]

    # Normal Havannah hex should have six corners. If mask is non-standard,
    # take extremal boundary cells as a robust fallback.
    if len(corners) != 6:
        extremals = []
        keys = [
            lambda x: x[0], lambda x: -x[0],
            lambda x: x[1], lambda x: -x[1],
            lambda x: x[0] - x[1], lambda x: x[1] - x[0],
        ]
        for key in keys:
            best = min(cells, key=key)
            if best not in extremals:
                extremals.append(best)
        corners = extremals[:6]

    corner_set = set(corners)

    # Boundary cells, excluding corners, split into six connected edge groups.
    boundary = {p for p in cells if deg[p] < 6 and p not in corner_set}
    edges = []
    unseen = set(boundary)
    while unseen:
        start = unseen.pop()
        comp = {start}
        q = deque([start])
        while q:
            r, c = q.popleft()
            for dr, dc in DIRS:
                nb = (r + dr, c + dc)
                if nb in unseen:
                    unseen.remove(nb)
                    comp.add(nb)
                    q.append(nb)
        edges.append(comp)

    # In odd masks, boundary may be split imperfectly; still works as a heuristic.
    edge_id = {}
    for i, e in enumerate(edges):
        for p in e:
            edge_id[p] = i

    center = (sum(r for r, c in cells) / max(1, len(cells)),
              sum(c for r, c in cells) / max(1, len(cells)))

    return cells, cellset, corner_set, edge_id, center


def _neighbors(p, cellset):
    r, c = p
    for dr, dc in DIRS:
        nb = (r + dr, c + dc)
        if nb in cellset:
            yield nb


def _has_ring_after(stones, move, cellset):
    """Ring test via cycle creation: if two neighbouring friendly stones of move
    are already connected without using move, adding move forms a cycle."""
    s = set(stones)
    neigh = [nb for nb in _neighbors(move, cellset) if nb in s]
    if len(neigh) < 2:
        return False

    blocked = move
    for i in range(len(neigh)):
        a = neigh[i]
        for j in range(i + 1, len(neigh)):
            b = neigh[j]
            q = deque([a])
            seen = {a, blocked}
            while q:
                x = q.popleft()
                if x == b:
                    return True
                for nb in _neighbors(x, cellset):
                    if nb not in seen and nb in s:
                        seen.add(nb)
                        q.append(nb)
    return False


def _win_after(stones, move, cellset, corners, edge_id):
    s = set(stones)
    s.add(move)
    seen = set()

    for start in list(s):
        if start in seen:
            continue
        comp = []
        q = deque([start])
        seen.add(start)
        corner_count = 0
        edge_bits = set()
        while q:
            p = q.popleft()
            comp.append(p)
            if p in corners:
                corner_count += 1
            if p in edge_id:
                edge_bits.add(edge_id[p])
            for nb in _neighbors(p, cellset):
                if nb in s and nb not in seen:
                    seen.add(nb)
                    q.append(nb)

        if move in comp:
            if corner_count >= 2:
                return True
            if len(edge_bits) >= 3:
                return True
            break

    return _has_ring_after(stones, move, cellset)


def _component_info(stones, cellset, corners, edge_id):
    s = set(stones)
    comp_id = {}
    infos = []
    seen = set()
    for start in s:
        if start in seen:
            continue
        idx = len(infos)
        q = deque([start])
        seen.add(start)
        stones_comp = []
        corner_count = 0
        edges = set()
        while q:
            p = q.popleft()
            comp_id[p] = idx
            stones_comp.append(p)
            if p in corners:
                corner_count += 1
            if p in edge_id:
                edges.add(edge_id[p])
            for nb in _neighbors(p, cellset):
                if nb in s and nb not in seen:
                    seen.add(nb)
                    q.append(nb)
        infos.append((len(stones_comp), corner_count, edges))
    return comp_id, infos


def _touch_features(move, stones, comp_id, infos, cellset, corners, edge_id):
    ids = set()
    adj = 0
    for nb in _neighbors(move, cellset):
        if nb in stones:
            adj += 1
            ids.add(comp_id.get(nb, -1))
    ids.discard(-1)

    size = 1
    corn = 1 if move in corners else 0
    eds = set()
    if move in edge_id:
        eds.add(edge_id[move])
    for i in ids:
        sz, co, es = infos[i]
        size += sz
        corn += co
        eds |= set(es)
    return adj, len(ids), size, corn, len(eds)


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    try:
        cells, cellset, corners, edge_id, center = _make_geom(valid_mask)
        occupied = set(me) | set(opp)
        legal = [p for p in cells if p not in occupied]
        if not legal:
            return cells[0] if cells else (0, 0)

        me_set = set(me)
        opp_set = set(opp)

        # 1. Win immediately if possible.
        for mv in legal:
            if _win_after(me, mv, cellset, corners, edge_id):
                return mv

        # 2. Block opponent's immediate win.
        opp_wins = []
        for mv in legal:
            if _win_after(opp, mv, cellset, corners, edge_id):
                opp_wins.append(mv)
        if opp_wins:
            # If several blocks, choose the one also best for us.
            legal_to_score = opp_wins
        else:
            legal_to_score = legal

        my_comp, my_infos = _component_info(me, cellset, corners, edge_id)
        op_comp, op_infos = _component_info(opp, cellset, corners, edge_id)

        cr, cc = center
        maxdist = max(1.0, max(abs(r - cr) + abs(c - cc) for r, c in cells))

        best = None
        best_score = -10**18

        for mv in legal_to_score:
            madj, mmerge, msize, mcorn, medges = _touch_features(
                mv, me_set, my_comp, my_infos, cellset, corners, edge_id
            )
            oadj, omerge, osize, ocorn, oedges = _touch_features(
                mv, opp_set, op_comp, op_infos, cellset, corners, edge_id
            )

            r, c = mv
            central = 1.0 - (abs(r - cr) + abs(c - cc)) / maxdist

            # Friendly strategic value: connect components and approach
            # bridge/fork/ring threats.
            score = 0.0
            score += 7.0 * madj
            score += 13.0 * max(0, mmerge - 1)
            score += 0.55 * min(msize, 30)
            score += 24.0 * mcorn
            score += 18.0 * medges
            if mcorn >= 2:
                score += 90.0
            if medges >= 3:
                score += 90.0
            if madj >= 2 and mmerge >= 1:
                score += 18.0

            # Defensive value: occupy opponent's strong connection points.
            score += 5.5 * oadj
            score += 10.0 * max(0, omerge - 1)
            score += 14.0 * ocorn
            score += 11.0 * oedges
            if ocorn >= 2:
                score += 55.0
            if oedges >= 3:
                score += 55.0

            # Local shape: prefer cells with many nearby friendly liberties,
            # but avoid completely isolated edge moves early.
            empty_neigh = 0
            friend2 = 0
            opp2 = 0
            for nb in _neighbors(mv, cellset):
                if nb not in occupied:
                    empty_neigh += 1
                    for nb2 in _neighbors(nb, cellset):
                        if nb2 in me_set:
                            friend2 += 0.15
                        elif nb2 in opp_set:
                            opp2 += 0.08

            score += 2.0 * empty_neigh + friend2 + opp2
            score += 9.0 * central

            # Opening: central moves are usually flexible in Havannah.
            if len(occupied) < 8:
                score += 18.0 * central
                if mv in corners or mv in edge_id:
                    score -= 8.0

            # Slight deterministic tie-breaker.
            score += ((r * 31 + c * 17) % 101) * 1e-4

            if score > best_score:
                best_score = score
                best = mv

        if best is not None:
            return best

        return legal[0]

    except Exception:
        # Absolute safety fallback: scan for any legal unoccupied coordinate.
        occupied = set(me) | set(opp)
        try:
            for r in range(len(valid_mask)):
                for c in range(len(valid_mask[r])):
                    if _truth(valid_mask[r][c]) and (r, c) not in occupied:
                        return (r, c)
        except Exception:
            pass
        return (0, 0)
