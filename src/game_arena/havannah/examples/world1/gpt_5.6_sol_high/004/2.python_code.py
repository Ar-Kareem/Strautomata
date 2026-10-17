
import heapq
import math
from collections import deque


def policy(me: list[tuple[int, int]],
           opp: list[tuple[int, int]],
           valid_mask) -> tuple[int, int]:
    """
    Havannah policy for an offset-column hex board.

    For an odd column c, the four cross-column neighbors of (r, c)
    are (r-1, c-1), (r, c-1), (r-1, c+1), and (r, c+1).
    For an even column, they are shifted one row downward.
    """

    try:
        rows, cols = valid_mask.shape[:2]
    except AttributeError:
        rows = len(valid_mask)
        cols = len(valid_mask[0]) if rows else 0

    # ------------------------------------------------------------------
    # Board geometry
    # ------------------------------------------------------------------

    cells = []
    index = {}

    for r in range(rows):
        for c in range(cols):
            if bool(valid_mask[r][c]):
                index[(r, c)] = len(cells)
                cells.append((r, c))

    n = len(cells)

    me_idx = {index[p] for p in me if p in index}
    opp_idx = {index[p] for p in opp if p in index}
    occupied = me_idx | opp_idx
    legal = [i for i in range(n) if i not in occupied]

    # The game specification guarantees that a legal move exists.
    # This branch only protects against malformed external input.
    if not legal:
        for r in range(rows):
            for c in range(cols):
                if bool(valid_mask[r][c]) and (r, c) not in set(me) | set(opp):
                    return (r, c)
        return (0, 0)

    def raw_neighbors(r, c):
        if c & 1:
            return (
                (r - 1, c), (r + 1, c),
                (r - 1, c - 1), (r, c - 1),
                (r - 1, c + 1), (r, c + 1),
            )
        return (
            (r - 1, c), (r + 1, c),
            (r, c - 1), (r + 1, c - 1),
            (r, c + 1), (r + 1, c + 1),
        )

    neighbors = [[] for _ in range(n)]
    for i, (r, c) in enumerate(cells):
        for p in raw_neighbors(r, c):
            j = index.get(p)
            if j is not None:
                neighbors[i].append(j)

    # Integer axial-like coordinates. They form a Z^2 lattice and are
    # useful for convex hulls, polygon areas, and Pick's theorem.
    axial = []
    display_xy = []
    for r, c in cells:
        a = c
        b = r - ((c + 1) // 2)
        axial.append((a, b))
        display_xy.append((math.sqrt(3.0) * c, 2.0 * r - (c & 1)))

    # Cyclic ordering of neighbors around every cell.
    ordered_neighbors = []
    for i in range(n):
        x0, y0 = display_xy[i]
        ordered_neighbors.append(sorted(
            neighbors[i],
            key=lambda j: math.atan2(
                display_xy[j][1] - y0,
                display_xy[j][0] - x0
            )
        ))

    boundary = {i for i in range(n) if len(neighbors[i]) < 6}

    def cross(o, a, b):
        return ((a[0] - o[0]) * (b[1] - o[1])
                - (a[1] - o[1]) * (b[0] - o[0]))

    def convex_hull_indices():
        pts = sorted((axial[i][0], axial[i][1], i) for i in range(n))
        if len(pts) <= 1:
            return [p[2] for p in pts]

        lower = []
        for p in pts:
            while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
                lower.pop()
            lower.append(p)

        upper = []
        for p in reversed(pts):
            while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
                upper.pop()
            upper.append(p)

        return [p[2] for p in lower[:-1] + upper[:-1]]

    corners = convex_hull_indices()

    # A proper Havannah board has exactly six convex-hull vertices.
    # Degree-three boundary points are a useful fallback.
    if len(corners) != 6:
        degree_corners = [i for i in boundary if len(neighbors[i]) <= 3]
        if len(degree_corners) == 6:
            cx = sum(display_xy[i][0] for i in degree_corners) / 6.0
            cy = sum(display_xy[i][1] for i in degree_corners) / 6.0
            corners = sorted(
                degree_corners,
                key=lambda i: math.atan2(
                    display_xy[i][1] - cy,
                    display_xy[i][0] - cx
                )
            )
        else:
            # Farthest-point fallback for unusual masks.
            candidates = list(boundary) if boundary else list(range(n))
            chosen = [min(candidates)]
            while len(chosen) < min(6, len(candidates)):
                best = max(
                    (i for i in candidates if i not in chosen),
                    key=lambda i: min(
                        (display_xy[i][0] - display_xy[j][0]) ** 2
                        + (display_xy[i][1] - display_xy[j][1]) ** 2
                        for j in chosen
                    )
                )
                chosen.append(best)
            corners = chosen

    corner_id = {v: k for k, v in enumerate(corners)}
    corner_set = set(corners)

    # Removing the corners separates the board boundary into six edges.
    edge_components = []
    unseen_boundary = set(boundary) - corner_set

    while unseen_boundary:
        start = unseen_boundary.pop()
        comp = [start]
        q = [start]
        while q:
            u = q.pop()
            for v in neighbors[u]:
                if v in unseen_boundary:
                    unseen_boundary.remove(v)
                    q.append(v)
                    comp.append(v)
        edge_components.append(comp)

    if len(edge_components) == 6:
        cx = sum(display_xy[i][0] for i in range(n)) / max(1, n)
        cy = sum(display_xy[i][1] for i in range(n)) / max(1, n)
        edge_components.sort(
            key=lambda comp: math.atan2(
                sum(display_xy[i][1] for i in comp) / len(comp) - cy,
                sum(display_xy[i][0] for i in comp) / len(comp) - cx
            )
        )
    else:
        # Classify boundary points by nearest hull side.
        edge_components = [[] for _ in range(6)]
        if len(corners) >= 6:
            cx = sum(display_xy[i][0] for i in corners[:6]) / 6.0
            cy = sum(display_xy[i][1] for i in corners[:6]) / 6.0
            corners = sorted(
                corners[:6],
                key=lambda i: math.atan2(
                    display_xy[i][1] - cy,
                    display_xy[i][0] - cx
                )
            )
            corner_id = {v: k for k, v in enumerate(corners)}
            corner_set = set(corners)

            def segment_distance_sq(px, py, ax, ay, bx, by):
                vx, vy = bx - ax, by - ay
                wx, wy = px - ax, py - ay
                vv = vx * vx + vy * vy
                if vv == 0:
                    return wx * wx + wy * wy
                t = max(0.0, min(1.0, (wx * vx + wy * vy) / vv))
                dx = px - (ax + t * vx)
                dy = py - (ay + t * vy)
                return dx * dx + dy * dy

            for i in boundary - corner_set:
                px, py = display_xy[i]
                best_edge = 0
                best_dist = float("inf")
                for e in range(6):
                    a = corners[e]
                    b = corners[(e + 1) % 6]
                    ax, ay = display_xy[a]
                    bx, by = display_xy[b]
                    d = segment_distance_sq(px, py, ax, ay, bx, by)
                    if d < best_dist:
                        best_dist = d
                        best_edge = e
                edge_components[best_edge].append(i)

    cell_edge = [-1] * n
    for e, comp in enumerate(edge_components[:6]):
        for i in comp:
            if i not in corner_set:
                cell_edge[i] = e

    edge_sources = [list(comp) for comp in edge_components[:6]]
    while len(edge_sources) < 6:
        edge_sources.append([])

    # Distance from the outer boundary, used as a central-influence term.
    boundary_depth = [10 ** 6] * n
    dq = deque()
    for i in boundary:
        boundary_depth[i] = 0
        dq.append(i)

    while dq:
        u = dq.popleft()
        nd = boundary_depth[u] + 1
        for v in neighbors[u]:
            if boundary_depth[v] > nd:
                boundary_depth[v] = nd
                dq.append(v)

    # ------------------------------------------------------------------
    # Win detection
    # ------------------------------------------------------------------

    def has_ring(stones):
        """
        Detect a ring as a stone-graph cycle whose polygon contains at
        least one lattice cell center.

        Faces of the embedded planar graph are traversed by following the
        clockwise predecessor of the incoming edge. For simple cycles,
        Pick's theorem determines whether a lattice point lies strictly
        inside. Non-simple outer walks are checked with winding numbers.
        """
        if len(stones) < 6:
            return False

        stone_neighbors = {}
        directed_edge_count = 0
        for u in stones:
            ns = [v for v in ordered_neighbors[u] if v in stones]
            stone_neighbors[u] = ns
            directed_edge_count += len(ns)

        # A graph without a cycle cannot form a ring.
        if directed_edge_count // 2 < len(stones):
            return False

        visited = set()

        def polygon_area2(poly):
            area = 0
            m = len(poly)
            for k in range(m):
                x1, y1 = axial[poly[k]]
                x2, y2 = axial[poly[(k + 1) % m]]
                area += x1 * y2 - x2 * y1
            return area

        def simple_polygon_has_lattice_interior(poly):
            area2 = abs(polygon_area2(poly))
            if area2 == 0:
                return False

            boundary_points = 0
            m = len(poly)
            for k in range(m):
                x1, y1 = axial[poly[k]]
                x2, y2 = axial[poly[(k + 1) % m]]
                boundary_points += math.gcd(abs(x2 - x1), abs(y2 - y1))

            # Pick: 2I = |area2| - B + 2.
            return area2 - boundary_points + 2 >= 2

        def point_inside_walk(point, poly):
            px, py = axial[point]
            winding = 0
            m = len(poly)

            for k in range(m):
                x1, y1 = axial[poly[k]]
                x2, y2 = axial[poly[(k + 1) % m]]
                cr = (x2 - x1) * (py - y1) - (y2 - y1) * (px - x1)

                if cr == 0 and min(x1, x2) <= px <= max(x1, x2) \
                        and min(y1, y2) <= py <= max(y1, y2):
                    return False

                if y1 <= py < y2 and cr > 0:
                    winding += 1
                elif y2 <= py < y1 and cr < 0:
                    winding -= 1

            return winding != 0

        for a in stones:
            for b in stone_neighbors[a]:
                if (a, b) in visited:
                    continue

                start = (a, b)
                u, v = a, b
                poly = [a]
                valid_walk = True

                for _ in range(directed_edge_count + 2):
                    if (u, v) in visited and (u, v) != start:
                        valid_walk = False
                        break

                    visited.add((u, v))
                    poly.append(v)

                    ns = stone_neighbors.get(v, [])
                    if not ns:
                        valid_walk = False
                        break

                    try:
                        incoming_pos = ns.index(u)
                    except ValueError:
                        valid_walk = False
                        break

                    # Clockwise predecessor keeps one face consistently
                    # on the same side of the directed walk.
                    w = ns[(incoming_pos - 1) % len(ns)]
                    u, v = v, w

                    if (u, v) == start:
                        break
                else:
                    valid_walk = False

                if not valid_walk or len(poly) < 4:
                    continue

                if poly[-1] == poly[0]:
                    poly.pop()

                if len(poly) < 3 or polygon_area2(poly) == 0:
                    continue

                if len(set(poly)) == len(poly):
                    if simple_polygon_has_lattice_interior(poly):
                        return True
                else:
                    # Repeated vertices normally come from branches on an
                    # outer face. Winding remains valid for the closed walk.
                    poly_set = set(poly)
                    for p in range(n):
                        if p not in poly_set and point_inside_walk(p, poly):
                            return True

        return False

    def has_win(stones):
        if not stones:
            return False

        unseen = set(stones)

        while unseen:
            start = unseen.pop()
            stack = [start]
            touched_corners = set()
            touched_edges = set()

            while stack:
                u = stack.pop()

                cid = corner_id.get(u)
                if cid is not None:
                    touched_corners.add(cid)

                eid = cell_edge[u]
                if eid >= 0:
                    touched_edges.add(eid)

                for v in neighbors[u]:
                    if v in unseen:
                        unseen.remove(v)
                        stack.append(v)

            if len(touched_corners) >= 2:
                return True
            if len(touched_edges) >= 3:
                return True

        return has_ring(stones)

    def winning_moves(stones, available, limit=None):
        result = []
        for x in available:
            stones.add(x)
            won = has_win(stones)
            stones.remove(x)
            if won:
                result.append(x)
                if limit is not None and len(result) >= limit:
                    break
        return result

    # Empty-board opening: occupy a maximally central cell.
    if not me_idx and not opp_idx:
        best = max(
            legal,
            key=lambda i: (
                boundary_depth[i],
                -abs(cells[i][0] - (rows - 1) / 2.0)
                - abs(cells[i][1] - (cols - 1) / 2.0),
                -i
            )
        )
        return cells[best]

    # Exact immediate tactical checks.
    my_wins = winning_moves(me_idx, legal)
    if my_wins:
        best = max(
            my_wins,
            key=lambda i: (
                len([v for v in neighbors[i] if v in me_idx]),
                boundary_depth[i],
                -i
            )
        )
        return cells[best]

    opponent_wins = winning_moves(opp_idx, legal)
    if len(opponent_wins) == 1:
        return cells[opponent_wins[0]]

    # ------------------------------------------------------------------
    # Component analysis for strategic scoring
    # ------------------------------------------------------------------

    def analyze_components(stones):
        label = [-1] * n
        sizes = []
        comp_corners = []
        comp_edges = []

        cid = 0
        for start in stones:
            if label[start] != -1:
                continue

            label[start] = cid
            q = [start]
            size = 0
            cs = set()
            es = set()

            while q:
                u = q.pop()
                size += 1

                corner = corner_id.get(u)
                if corner is not None:
                    cs.add(corner)

                edge = cell_edge[u]
                if edge >= 0:
                    es.add(edge)

                for v in neighbors[u]:
                    if v in stones and label[v] == -1:
                        label[v] = cid
                        q.append(v)

            sizes.append(size)
            comp_corners.append(cs)
            comp_edges.append(es)
            cid += 1

        return label, sizes, comp_corners, comp_edges

    my_label, my_sizes, my_comp_corners, my_comp_edges = \
        analyze_components(me_idx)
    op_label, op_sizes, op_comp_corners, op_comp_edges = \
        analyze_components(opp_idx)

    # ------------------------------------------------------------------
    # Shortest-path fields toward each corner and edge
    # ------------------------------------------------------------------

    INF = 10 ** 6

    def distance_field(sources, friendly, enemy):
        dist = [INF] * n
        heap = []

        for s in sources:
            if s in enemy:
                continue
            cost = 0 if s in friendly else 1
            if cost < dist[s]:
                dist[s] = cost
                heapq.heappush(heap, (cost, s))

        while heap:
            d, u = heapq.heappop(heap)
            if d != dist[u]:
                continue

            for v in neighbors[u]:
                if v in enemy:
                    continue
                nd = d + (0 if v in friendly else 1)
                if nd < dist[v]:
                    dist[v] = nd
                    heapq.heappush(heap, (nd, v))

        return dist

    my_corner_dist = [
        distance_field([c], me_idx, opp_idx) for c in corners[:6]
    ]
    op_corner_dist = [
        distance_field([c], opp_idx, me_idx) for c in corners[:6]
    ]
    my_edge_dist = [
        distance_field(src, me_idx, opp_idx) for src in edge_sources
    ]
    op_edge_dist = [
        distance_field(src, opp_idx, me_idx) for src in edge_sources
    ]

    def path_potential(x, corner_fields, edge_fields):
        corner_values = [field[x] for field in corner_fields
                         if field[x] < INF]
        edge_values = [field[x] for field in edge_fields
                       if field[x] < INF]

        bridge = INF
        if len(corner_values) >= 2:
            corner_values.sort()
            bridge = corner_values[0] + corner_values[1] - 1

        fork = INF
        if len(edge_values) >= 3:
            edge_values.sort()
            fork = edge_values[0] + edge_values[1] + edge_values[2] - 2

        value = 0.0
        if bridge < INF:
            value += max(0.0, 28.0 - 2.2 * bridge)
        if fork < INF:
            value += max(0.0, 30.0 - 1.55 * fork)
        return value

    total_stones = len(me_idx) + len(opp_idx)

    def static_score(x):
        score = 0.0

        my_adjacent = [v for v in neighbors[x] if v in me_idx]
        op_adjacent = [v for v in neighbors[x] if v in opp_idx]

        my_comps = {my_label[v] for v in my_adjacent}
        op_comps = {op_label[v] for v in op_adjacent}

        score += 4.6 * len(my_adjacent)
        score += 3.4 * len(op_adjacent)
        score += 11.5 * max(0, len(my_comps) - 1)
        score += 7.5 * max(0, len(op_comps) - 1)

        # Slight preference for connecting substantial components.
        if my_comps:
            score += min(15.0, 0.75 * sum(my_sizes[c] for c in my_comps))
        if op_comps:
            score += min(10.0, 0.45 * sum(op_sizes[c] for c in op_comps))

        my_corners = set()
        my_edges = set()
        for cid in my_comps:
            my_corners.update(my_comp_corners[cid])
            my_edges.update(my_comp_edges[cid])

        if x in corner_id:
            my_corners.add(corner_id[x])
            score += 8.0
        if cell_edge[x] >= 0:
            my_edges.add(cell_edge[x])
            score += 2.5

        score += 12.0 * len(my_corners)
        score += 7.0 * len(my_edges)
        if len(my_corners) >= 2:
            score += 80.0
        if len(my_edges) >= 3:
            score += 80.0

        # Defensive estimate: how dangerous would the opponent be if the
        # same cell were left available to them?
        op_corners = set()
        op_edges = set()
        for cid in op_comps:
            op_corners.update(op_comp_corners[cid])
            op_edges.update(op_comp_edges[cid])

        if x in corner_id:
            op_corners.add(corner_id[x])
        if cell_edge[x] >= 0:
            op_edges.add(cell_edge[x])

        score += 8.5 * len(op_corners)
        score += 5.4 * len(op_edges)
        if len(op_corners) >= 2:
            score += 42.0
        if len(op_edges) >= 3:
            score += 42.0

        # Joining two separated neighbors from the same component is a
        # strong ring-building motif.
        component_counts = {}
        for v in my_adjacent:
            cid = my_label[v]
            component_counts[cid] = component_counts.get(cid, 0) + 1

        for count in component_counts.values():
            if count >= 2:
                score += 9.0 + 4.0 * (count - 2)

        # Reward non-contiguous friendly contacts around the cell.
        flags = [1 if v in me_idx else 0 for v in ordered_neighbors[x]]
        if flags:
            transitions = sum(
                1 for k in range(len(flags))
                if flags[k] != flags[(k + 1) % len(flags)]
            )
            if sum(flags) >= 2 and transitions >= 4:
                score += 8.0

        # Central influence matters most in the opening and middle game.
        center_weight = max(0.8, 3.0 - total_stones / 26.0)
        score += center_weight * boundary_depth[x]

        score += 0.55 * path_potential(
            x, my_corner_dist, my_edge_dist
        )
        score += 0.36 * path_potential(
            x, op_corner_dist, op_edge_dist
        )

        # Small deterministic tie-breaker to avoid repetitive symmetry.
        signature = (
            x * 92821
            + len(me_idx) * 68917
            + len(opp_idx) * 31337
            + sum((v + 1) * 17 for v in my_adjacent)
        ) % 1009
        score += signature / 100900.0

        return score

    # If the opponent has several immediate wins, the position may be
    # tactically lost, but choose the block that creates the best counterplay.
    if opponent_wins:
        best_move = opponent_wins[0]
        best_value = -float("inf")

        for x in opponent_wins:
            value = static_score(x)
            me_idx.add(x)
            remaining = [y for y in legal if y != x]
            threats = winning_moves(me_idx, remaining, limit=2)
            me_idx.remove(x)

            if len(threats) >= 2:
                value += 5000.0
            elif len(threats) == 1:
                value += 140.0

            if value > best_value:
                best_value = value
                best_move = x

        return cells[best_move]

    # ------------------------------------------------------------------
    # Candidate ranking and forcing-threat search
    # ------------------------------------------------------------------

    scored = [(static_score(x), x) for x in legal]
    scored.sort(reverse=True)

    # Include highly ranked moves plus ring-like connection candidates.
    candidate_set = {x for _, x in scored[:14]}

    ring_candidates = []
    for x in legal:
        adjacent_components = {}
        for v in neighbors[x]:
            if v in me_idx:
                cid = my_label[v]
                adjacent_components[cid] = adjacent_components.get(cid, 0) + 1
        if any(count >= 2 for count in adjacent_components.values()):
            ring_candidates.append(x)

    ring_candidates.sort(key=static_score, reverse=True)
    candidate_set.update(ring_candidates[:6])

    best_move = scored[0][1]
    best_value = scored[0][0]

    # A move producing two distinct immediate winning moves is normally
    # decisive. Single threats are also valuable because they force a reply.
    for x in candidate_set:
        base = static_score(x)
        me_idx.add(x)
        remaining = [y for y in legal if y != x]
        threats = winning_moves(me_idx, remaining, limit=3)
        me_idx.remove(x)

        if len(threats) >= 2:
            value = base + 6000.0 + 100.0 * len(threats)
        elif len(threats) == 1:
            forced = threats[0]
            value = base + 150.0
            value += 2.0 * len([v for v in neighbors[forced] if v in me_idx])
        else:
            value = base

        if value > best_value:
            best_value = value
            best_move = x

    # Absolute legality guard.
    if best_move in occupied or best_move not in legal:
        best_move = legal[0]

    return cells[best_move]
