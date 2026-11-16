
import math
from collections import deque

N = 15

# Neighbor convention from prompt:
# (r,c) touches same col r±1, left col (r,c-1),(r-1,c-1), right col (r,c+1),(r-1,c+1)
DIRS = [(1, 0), (-1, 0), (0, -1), (-1, -1), (0, 1), (-1, 1)]


def _in_bounds(r, c, mask):
    return 0 <= r < len(mask) and 0 <= c < len(mask[0]) and bool(mask[r][c])


def _neighbors(cell, mask):
    r, c = cell
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if _in_bounds(nr, nc, mask):
            yield (nr, nc)


def _all_valid(mask):
    out = []
    R = len(mask)
    C = len(mask[0])
    for r in range(R):
        for c in range(C):
            if bool(mask[r][c]):
                out.append((r, c))
    return out


def _board_info(mask):
    cells = _all_valid(mask)
    deg = {}
    for x in cells:
        deg[x] = sum(1 for _ in _neighbors(x, mask))

    corners = set([x for x in cells if deg[x] == 3])

    # Determine the six edge sets by walking boundary arcs between corners.
    # For scoring and fork detection, edge identity only matters consistently.
    boundary = set([x for x in cells if deg[x] < 6])
    noncorner_boundary = boundary - corners

    # Split non-corner boundary into connected components after removing corners.
    edges = []
    seen = set()
    for x in noncorner_boundary:
        if x in seen:
            continue
        q = deque([x])
        seen.add(x)
        comp = set([x])
        while q:
            u = q.popleft()
            for v in _neighbors(u, mask):
                if v in noncorner_boundary and v not in seen:
                    seen.add(v)
                    comp.add(v)
                    q.append(v)
        edges.append(comp)

    # On a normal Havannah board, this gives six edge components.
    # If mask geometry is unusual, still use whatever components exist.
    edge_id = {}
    for i, e in enumerate(edges):
        for x in e:
            edge_id[x] = i

    # geometric center of playable cells
    cr = sum(r for r, c in cells) / max(1, len(cells))
    cc = sum(c for r, c in cells) / max(1, len(cells))

    return cells, corners, edges, edge_id, (cr, cc)


_CACHE = {}


def _get_info(mask):
    key = id(mask)
    info = _CACHE.get(key)
    if info is None:
        info = _board_info(mask)
        _CACHE[key] = info
    return info


def _components(stones, mask, corners, edge_id):
    stones = set(stones)
    seen = set()
    comps = []
    for s in stones:
        if s in seen:
            continue
        q = deque([s])
        seen.add(s)
        comp = []
        cs = set()
        es = set()
        while q:
            u = q.popleft()
            comp.append(u)
            if u in corners:
                cs.add(u)
            if u in edge_id:
                es.add(edge_id[u])
            for v in _neighbors(u, mask):
                if v in stones and v not in seen:
                    seen.add(v)
                    q.append(v)
        comps.append((comp, cs, es))
    return comps


def _has_bridge_or_fork(stones, mask, corners, edge_id):
    for comp, cs, es in _components(stones, mask, corners, edge_id):
        if len(cs) >= 2:
            return True
        if len(es) >= 3:
            return True
    return False


def _has_ring(stones, mask):
    # Ring exists iff there is an empty/opponent region not connected to board exterior,
    # when own stones are treated as walls. Add an outside node around the rectangular array.
    stones = set(stones)
    R = len(mask)
    C = len(mask[0])
    seen = set()
    q = deque()

    # Non-playable outside border acts as exterior; seed all non-stone boundary-adjacent cells.
    # Easier: flood all valid non-own cells touching boundary of playable mask.
    for r in range(R):
        for c in range(C):
            if not bool(mask[r][c]) or (r, c) in stones:
                continue
            # A valid cell is exterior-adjacent if it has fewer than 6 valid neighbors.
            if sum(1 for _ in _neighbors((r, c), mask)) < 6:
                seen.add((r, c))
                q.append((r, c))

    while q:
        u = q.popleft()
        for v in _neighbors(u, mask):
            if v not in stones and v not in seen:
                seen.add(v)
                q.append(v)

    for r in range(R):
        for c in range(C):
            if bool(mask[r][c]) and (r, c) not in stones and (r, c) not in seen:
                return True
    return False


def _is_win(stones, mask, corners, edge_id):
    return _has_bridge_or_fork(stones, mask, corners, edge_id) or _has_ring(stones, mask)


def _component_features_after(move, stones, mask, corners, edge_id):
    sset = set(stones)
    sset.add(move)
    # Find component containing move
    q = deque([move])
    seen = set([move])
    cs = set()
    es = set()
    size = 0
    while q:
        u = q.popleft()
        size += 1
        if u in corners:
            cs.add(u)
        if u in edge_id:
            es.add(edge_id[u])
        for v in _neighbors(u, mask):
            if v in sset and v not in seen:
                seen.add(v)
                q.append(v)
    return size, len(cs), len(es)


def _count_two_step_targets(move, stones, occupied, mask):
    # Count friendly stones at distance two through at least one empty midpoint.
    stones = set(stones)
    occupied = set(occupied)
    mids = []
    for n in _neighbors(move, mask):
        if n not in occupied:
            mids.append(n)
    cnt = 0
    seen = set()
    for m in mids:
        for x in _neighbors(m, mask):
            if x != move and x in stones and x not in seen:
                seen.add(x)
                cnt += 1
    return cnt


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    try:
        cells, corners, edges, edge_id, center = _get_info(valid_mask)
        occupied = set(me) | set(opp)
        legal = [x for x in cells if x not in occupied]
        if not legal:
            # Should never happen, but return a valid-looking coordinate if arena calls on full board.
            return cells[0] if cells else (0, 0)

        me_set = set(me)
        opp_set = set(opp)

        # 1. Immediate winning move.
        for mv in legal:
            new_me = me_set | {mv}
            if _is_win(new_me, valid_mask, corners, edge_id):
                return mv

        # 2. Block opponent immediate winning move.
        opponent_wins = []
        for mv in legal:
            new_opp = opp_set | {mv}
            if _is_win(new_opp, valid_mask, corners, edge_id):
                opponent_wins.append(mv)
        if opponent_wins:
            # If multiple blocks, choose the one also best for us.
            legal_to_score = opponent_wins
        else:
            legal_to_score = legal

        cr, cc = center
        best = legal_to_score[0]
        best_score = -10**18

        for mv in legal_to_score:
            r, c = mv
            score = 0.0

            # Friendly component value after move.
            my_size, my_corners, my_edges = _component_features_after(mv, me_set, valid_mask, corners, edge_id)
            score += 8.0 * my_size
            score += 55.0 * my_corners
            score += 45.0 * my_edges
            if my_corners >= 1 and my_edges >= 1:
                score += 15.0

            # Opponent component disruption / contest important cells.
            op_size, op_corners, op_edges = _component_features_after(mv, opp_set, valid_mask, corners, edge_id)
            score += 5.0 * op_size
            score += 35.0 * op_corners
            score += 28.0 * op_edges

            # Local adjacency.
            friendly_adj = 0
            opp_adj = 0
            empty_adj = 0
            for nb in _neighbors(mv, valid_mask):
                if nb in me_set:
                    friendly_adj += 1
                elif nb in opp_set:
                    opp_adj += 1
                else:
                    empty_adj += 1
            score += 12.0 * friendly_adj
            score += 7.0 * opp_adj
            score += 1.5 * empty_adj

            # Distance-two connection potential.
            score += 5.5 * _count_two_step_targets(mv, me_set, occupied, valid_mask)
            score += 3.0 * _count_two_step_targets(mv, opp_set, occupied, valid_mask)

            # Prefer central play early, but value boundary/corners for Havannah goals.
            dist = math.hypot(r - cr, c - cc)
            score += max(0.0, 20.0 - 2.0 * dist)

            if mv in corners:
                score += 18.0
            if mv in edge_id:
                score += 12.0

            # Avoid totally isolated non-strategic moves unless opening.
            if len(me) > 0 and friendly_adj == 0:
                score -= 8.0

            # Opening preference: play near center.
            if len(me) == 0:
                score += max(0.0, 100.0 - 8.0 * dist)

            # Tiny deterministic tie breaker toward center-ish lexicographic stability.
            score -= 0.001 * (r * 17 + c)

            if score > best_score:
                best_score = score
                best = mv

        # Final legality guard.
        if best in occupied or not _in_bounds(best[0], best[1], valid_mask):
            for mv in legal:
                return mv
        return best

    except Exception:
        # Absolute safety fallback: scan mask and avoid occupied.
        occ = set(me) | set(opp)
        try:
            for r in range(len(valid_mask)):
                for c in range(len(valid_mask[0])):
                    if bool(valid_mask[r][c]) and (r, c) not in occ:
                        return (r, c)
        except Exception:
            pass
        return (0, 0)
