
from collections import deque
import math

# Hex-neighbour directions for the coordinate system described in the prompt.
_DIRS = ((-1, 0), (1, 0), (0, -1), (-1, -1), (0, 1), (-1, 1))


def _is_valid(mask, r, c):
    try:
        return bool(mask[r][c])
    except Exception:
        return False


def _shape(mask):
    return len(mask), len(mask[0])


def _valid_cells(mask):
    n, m = _shape(mask)
    out = []
    for r in range(n):
        for c in range(m):
            if _is_valid(mask, r, c):
                out.append((r, c))
    return out


def _neighbors(cell, mask):
    r, c = cell
    n, m = _shape(mask)
    for dr, dc in _DIRS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < n and 0 <= nc < m and _is_valid(mask, nr, nc):
            yield (nr, nc)


def _board_info(mask):
    """
    Derive corners and six edge classes directly from the playable mask.
    This avoids assuming a specific hex radius.
    """
    cells = _valid_cells(mask)
    cellset = set(cells)

    deg = {}
    boundary = set()
    for x in cells:
        d = sum(1 for _ in _neighbors(x, mask))
        deg[x] = d
        if d < 6:
            boundary.add(x)

    # On a normal Havannah board, corners are the boundary cells with smallest degree.
    if boundary:
        mindeg = min(deg[x] for x in boundary)
        corners = {x for x in boundary if deg[x] == mindeg}
    else:
        corners = set()

    # If something odd happens, fall back to six geometrically extreme points.
    if len(corners) != 6 and cells:
        keys = [
            lambda x: x[0],
            lambda x: -x[0],
            lambda x: x[1],
            lambda x: -x[1],
            lambda x: x[0] + x[1],
            lambda x: -(x[0] + x[1]),
        ]
        corners = set()
        for key in keys:
            best = min(cells, key=key)
            corners.add(best)

    # Edge cells are boundary cells excluding corners.  Split them into connected
    # boundary chains; each chain is one of the six Havannah edges.
    edge_id = {}
    edge_cells = boundary - corners
    eid = 0
    seen = set()
    for start in list(edge_cells):
        if start in seen:
            continue
        q = deque([start])
        seen.add(start)
        while q:
            x = q.popleft()
            edge_id[x] = eid
            for y in _neighbors(x, mask):
                if y in edge_cells and y not in seen:
                    seen.add(y)
                    q.append(y)
        eid += 1

    # In rare masks, edge chains may not split cleanly.  The policy still works;
    # fork detection is just slightly approximate.
    corner_bit = {}
    for i, x in enumerate(sorted(corners)):
        corner_bit[x] = 1 << i

    edge_bit = {}
    for x, i in edge_id.items():
        edge_bit[x] = 1 << i

    # Center used by heuristic.
    if cells:
        cr = sum(r for r, c in cells) / float(len(cells))
        cc = sum(c for r, c in cells) / float(len(cells))
    else:
        cr = cc = 0.0

    return cells, cellset, corner_bit, edge_bit, (cr, cc)


class _DSU:
    def __init__(self):
        self.p = {}
        self.sz = {}

    def add(self, x):
        self.p[x] = x
        self.sz[x] = 1

    def find(self, x):
        p = self.p
        while p[x] != x:
            p[x] = p[p[x]]
            x = p[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return ra
        if self.sz[ra] < self.sz[rb]:
            ra, rb = rb, ra
        self.p[rb] = ra
        self.sz[ra] += self.sz[rb]
        return ra


def _components(stones, mask, corner_bit, edge_bit):
    stones = set(stones)
    dsu = _DSU()
    for x in stones:
        dsu.add(x)

    for x in stones:
        for y in _neighbors(x, mask):
            if y in stones:
                dsu.union(x, y)

    cmask = {}
    emask = {}
    size = {}
    for x in stones:
        r = dsu.find(x)
        cmask[r] = cmask.get(r, 0) | corner_bit.get(x, 0)
        emask[r] = emask.get(r, 0) | edge_bit.get(x, 0)
        size[r] = size.get(r, 0) + 1

    return dsu, cmask, emask, size, stones


def _popcount(x):
    try:
        return x.bit_count()
    except AttributeError:
        return bin(x).count("1")


def _move_result(move, stones, comp, mask, corner_bit, edge_bit):
    """
    Return:
      win: whether move immediately completes bridge/fork/ring-like cycle
      cnum: number of connected corners after move
      enum: number of connected edges after move
      cycle: whether the move creates a graph cycle
      group_size: size of resulting connected group
      adj: adjacent friendly stones
    """
    dsu, cmask, emask, size, stone_set = comp
    c = corner_bit.get(move, 0)
    e = edge_bit.get(move, 0)
    roots = []
    adj = 0

    for nb in _neighbors(move, mask):
        if nb in stone_set:
            adj += 1
            rt = dsu.find(nb)
            if rt not in roots:
                roots.append(rt)

    group_size = 1
    for rt in roots:
        c |= cmask.get(rt, 0)
        e |= emask.get(rt, 0)
        group_size += size.get(rt, 1)

    # A newly placed stone creates a cycle if it connects two neighbours that
    # were already in the same connected component without the new stone.
    seen_roots = set()
    cycle = False
    for nb in _neighbors(move, mask):
        if nb in stone_set:
            rt = dsu.find(nb)
            if rt in seen_roots:
                cycle = True
                break
            seen_roots.add(rt)

    cnum = _popcount(c)
    enum = _popcount(e)

    # Bridge: two corners. Fork: three edges. Ring: approximated by cycle.
    win = (cnum >= 2) or (enum >= 3) or cycle
    return win, cnum, enum, cycle, group_size, adj


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    cells, cellset, corner_bit, edge_bit, center = _board_info(valid_mask)

    occupied = set(me) | set(opp)
    legal = [x for x in cells if x not in occupied]

    # Absolute safety fallback.
    if not legal:
        return cells[0] if cells else (0, 0)

    me_comp = _components(me, valid_mask, corner_bit, edge_bit)
    opp_comp = _components(opp, valid_mask, corner_bit, edge_bit)

    # 1. Take an immediate win.
    for mv in legal:
        win, _, _, _, _, _ = _move_result(mv, me, me_comp, valid_mask, corner_bit, edge_bit)
        if win:
            return (int(mv[0]), int(mv[1]))

    # 2. Block opponent immediate wins.
    opp_wins = []
    for mv in legal:
        win, _, _, _, _, _ = _move_result(mv, opp, opp_comp, valid_mask, corner_bit, edge_bit)
        if win:
            opp_wins.append(mv)

    if len(opp_wins) == 1:
        mv = opp_wins[0]
        return (int(mv[0]), int(mv[1]))

    # 3. Heuristic scoring.
    cr, cc = center
    best = None
    best_score = -10**18

    # Candidate reduction: after the first move, prefer cells close to stones.
    # Still keep all legal cells as fallback.
    near = set()
    if occupied:
        for s in occupied:
            for nb in _neighbors(s, valid_mask):
                if nb not in occupied:
                    near.add(nb)
    candidates = list(near) if near else legal

    for mv in candidates:
        own_win, own_c, own_e, own_cycle, own_size, own_adj = _move_result(
            mv, me, me_comp, valid_mask, corner_bit, edge_bit
        )
        opp_win, opp_c, opp_e, opp_cycle, opp_size, opp_adj = _move_result(
            mv, opp, opp_comp, valid_mask, corner_bit, edge_bit
        )

        # Distance-to-center preference.
        dist = abs(mv[0] - cr) + abs(mv[1] - cc)

        score = 0.0

        # If several opponent wins exist, blocking one is still valuable.
        if mv in opp_wins:
            score += 500000.0

        # Build our threats.
        score += 140.0 * own_adj
        score += 14.0 * own_size
        score += 950.0 * own_c
        score += 700.0 * own_e
        if own_cycle:
            score += 1200.0

        # Block opponent development.
        score += 120.0 * opp_adj
        score += 10.0 * opp_size
        score += 850.0 * opp_c
        score += 650.0 * opp_e
        if opp_cycle:
            score += 900.0

        # Prefer moves that touch both colours: active fighting points.
        if own_adj and opp_adj:
            score += 180.0

        # Empty isolated points are usually poor except opening.
        if own_adj + opp_adj == 0:
            score -= 80.0

        # Mild centrality.
        score -= 5.0 * dist

        # Corners are tactically important but often too committal;
        # still value them when useful.
        if mv in corner_bit:
            score += 120.0
        if mv in edge_bit:
            score += 45.0

        # Small deterministic tie-breaker, avoids random import and keeps stable.
        score += ((mv[0] * 31 + mv[1] * 17) % 13) * 0.001

        if score > best_score:
            best_score = score
            best = mv

    if best is None:
        best = legal[0]

    return (int(best[0]), int(best[1]))
