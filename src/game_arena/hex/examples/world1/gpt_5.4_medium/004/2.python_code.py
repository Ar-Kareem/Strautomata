
from __future__ import annotations

from collections import deque

BOARD = 11
N = BOARD * BOARD
INF = 10**9


def _idx(r: int, c: int) -> int:
    return r * BOARD + c


def _rc(i: int) -> tuple[int, int]:
    return divmod(i, BOARD)


NEI = [[] for _ in range(N)]
for r in range(BOARD):
    for c in range(BOARD):
        i = _idx(r, c)
        for nr, nc in (
            (r, c - 1),
            (r, c + 1),
            (r - 1, c),
            (r - 1, c + 1),
            (r + 1, c),
            (r + 1, c - 1),
        ):
            if 0 <= nr < BOARD and 0 <= nc < BOARD:
                NEI[i].append(_idx(nr, nc))

TOP = [_idx(0, c) for c in range(BOARD)]
BOTTOM = [_idx(BOARD - 1, c) for c in range(BOARD)]
LEFT = [_idx(r, 0) for r in range(BOARD)]
RIGHT = [_idx(r, BOARD - 1) for r in range(BOARD)]

START_EDGE = {"b": TOP, "w": LEFT}
GOAL_EDGE = {"b": BOTTOM, "w": RIGHT}

TOUCH_START_B = [i // BOARD == 0 for i in range(N)]
TOUCH_GOAL_B = [i // BOARD == BOARD - 1 for i in range(N)]
TOUCH_START_W = [i % BOARD == 0 for i in range(N)]
TOUCH_GOAL_W = [i % BOARD == BOARD - 1 for i in range(N)]

# Bridge / virtual-connection helpers.
# BRIDGES[i] contains (j, c1, c2) where i and j are "bridge endpoints"
# and c1, c2 are the two common neighboring connector cells.
BRIDGES = [[] for _ in range(N)]
# CONNECTOR_PATTERNS[x] contains (u, v, other_connector) where x is one of the
# two connector cells for bridge endpoints u, v.
CONNECTOR_PATTERNS = [[] for _ in range(N)]

for i in range(N):
    nei_i = set(NEI[i])
    for j in range(i + 1, N):
        if j in nei_i:
            continue
        common = [x for x in NEI[i] if x in NEI[j]]
        if len(common) == 2:
            a, b = common
            BRIDGES[i].append((j, a, b))
            BRIDGES[j].append((i, a, b))
            CONNECTOR_PATTERNS[a].append((i, j, b))
            CONNECTOR_PATTERNS[b].append((i, j, a))


def _other(color: str) -> str:
    return "w" if color == "b" else "b"


def _touch_start(i: int, color: str) -> bool:
    return TOUCH_START_B[i] if color == "b" else TOUCH_START_W[i]


def _touch_goal(i: int, color: str) -> bool:
    return TOUCH_GOAL_B[i] if color == "b" else TOUCH_GOAL_W[i]


def _cap_cost(x: int) -> int:
    return 25 if x >= INF else x


def _wins_from_move(move: int, stones: set[int], color: str) -> bool:
    # Check whether adding stone "move" to "stones" wins immediately.
    stack = [move]
    seen = {move}
    touch_s = _touch_start(move, color)
    touch_g = _touch_goal(move, color)

    while stack and not (touch_s and touch_g):
        u = stack.pop()
        for v in NEI[u]:
            if v != move and v not in stones:
                continue
            if v in seen:
                continue
            seen.add(v)
            stack.append(v)
            if _touch_start(v, color):
                touch_s = True
            if _touch_goal(v, color):
                touch_g = True

    return touch_s and touch_g


def _find_immediate_wins(
    stones: set[int],
    empties: list[int],
    color: str,
    limit: int | None = None,
) -> list[int]:
    wins = []
    for e in empties:
        if _wins_from_move(e, stones, color):
            wins.append(e)
            if limit is not None and len(wins) >= limit:
                break
    return wins


def _side_dist(player: set[int], opponent: set[int], starts: list[int]) -> list[int]:
    dist = [INF] * N
    dq = deque()

    for s in starts:
        if s in opponent:
            continue
        w = 0 if s in player else 1
        if w < dist[s]:
            dist[s] = w
            if w == 0:
                dq.appendleft(s)
            else:
                dq.append(s)

    while dq:
        u = dq.popleft()
        du = dist[u]
        for v in NEI[u]:
            if v in opponent:
                continue
            w = 0 if v in player else 1
            nd = du + w
            if nd < dist[v]:
                dist[v] = nd
                if w == 0:
                    dq.appendleft(v)
                else:
                    dq.append(v)

    return dist


def _compute_metrics(player: set[int], opponent: set[int], color: str):
    d_start = _side_dist(player, opponent, START_EDGE[color])
    d_goal = _side_dist(player, opponent, GOAL_EDGE[color])
    base = min(d_start[g] for g in GOAL_EDGE[color])
    return d_start, d_goal, base


def _shortest_path_cost(player: set[int], opponent: set[int], color: str) -> int:
    d = _side_dist(player, opponent, START_EDGE[color])
    return min(d[g] for g in GOAL_EDGE[color])


def _component_ids(stones: set[int]) -> dict[int, int]:
    comp = {}
    cid = 0
    for s in stones:
        if s in comp:
            continue
        comp[s] = cid
        stack = [s]
        while stack:
            u = stack.pop()
            for v in NEI[u]:
                if v in stones and v not in comp:
                    comp[v] = cid
                    stack.append(v)
        cid += 1
    return comp


def _center_tiebreak(i: int, color: str) -> tuple[int, int, int]:
    r, c = _rc(i)
    center_dist = abs(r - 5) + abs(c - 5)
    axis_dist = abs(c - 5) if color == "b" else abs(r - 5)
    return (-center_dist, -axis_dist, -i)


def _opening_move(occupied: set[int], color: str) -> int | None:
    total = len(occupied)
    if total == 0 and color == "b":
        return _idx(5, 5)

    if total <= 2:
        prefs = []
        if color == "b":
            prefs = [
                (5, 5),
                (4, 5),
                (6, 5),
                (5, 4),
                (5, 6),
                (4, 6),
                (6, 4),
                (4, 4),
                (6, 6),
                (3, 5),
                (7, 5),
            ]
        else:
            prefs = [
                (5, 5),
                (5, 4),
                (5, 6),
                (4, 5),
                (6, 5),
                (4, 6),
                (6, 4),
                (4, 4),
                (6, 6),
                (5, 3),
                (5, 7),
            ]
        for r, c in prefs:
            i = _idx(r, c)
            if i not in occupied:
                return i
    return None


def _static_score(
    i: int,
    me: set[int],
    opp: set[int],
    color: str,
    me_comp: dict[int, int],
    opp_comp: dict[int, int],
    ds_me_s: list[int],
    ds_me_g: list[int],
    base_me: int,
    ds_opp_s: list[int],
    ds_opp_g: list[int],
    base_opp: int,
    turn: int,
) -> float:
    r, c = _rc(i)
    base_me_c = _cap_cost(base_me)
    base_opp_c = _cap_cost(base_opp)

    self_through = ds_me_s[i] + ds_me_g[i] - 1 if ds_me_s[i] < INF and ds_me_g[i] < INF else INF
    opp_through = ds_opp_s[i] + ds_opp_g[i] - 1 if ds_opp_s[i] < INF and ds_opp_g[i] < INF else INF

    friends = [n for n in NEI[i] if n in me]
    enemies = [n for n in NEI[i] if n in opp]
    friend_comps = {me_comp[n] for n in friends}
    enemy_comps = {opp_comp[n] for n in enemies}

    score = 0.0

    # Path criticality: moves that lie on strong connection routes for either side.
    if self_through < INF:
        d = max(0, _cap_cost(self_through) - base_me_c)
        score += 11.0 / (1 + d)
        if _cap_cost(self_through) == base_me_c:
            score += 4.0

    if opp_through < INF:
        d = max(0, _cap_cost(opp_through) - base_opp_c)
        score += 13.0 / (1 + d)
        if _cap_cost(opp_through) == base_opp_c:
            score += 5.0

    # Local connectivity.
    score += 2.5 * len(friends)
    score += 1.4 * len(enemies)

    # Joining multiple groups is very valuable in Hex.
    if len(friend_comps) >= 2:
        score += 7.0 + 4.0 * (len(friend_comps) - 2)
    elif len(friend_comps) == 1 and len(friends) >= 2:
        score += 1.5

    # Cutting between multiple opponent groups is also useful.
    if len(enemy_comps) >= 2:
        score += 3.5 + 2.5 * (len(enemy_comps) - 2)

    # Bridge / virtual connection patterns.
    bridge_score = 0.0

    # As an endpoint of a friendly bridge.
    for j, a, b in BRIDGES[i]:
        if j in me and a not in opp and b not in opp:
            bridge_score += 2.4
            if a in me or b in me:
                bridge_score += 1.2

    # As one connector of a friendly bridge, or to break an opponent bridge.
    for u, v, other_conn in CONNECTOR_PATTERNS[i]:
        if u in me and v in me and other_conn not in opp:
            bridge_score += 3.0
            if other_conn in me:
                bridge_score += 1.0
        elif u in opp and v in opp and other_conn not in me:
            bridge_score += 2.5

    score += bridge_score

    # Side-touching cells matter a bit for actual completion.
    if color == "b":
        if TOUCH_START_B[i] or TOUCH_GOAL_B[i]:
            score += 1.5
    else:
        if TOUCH_START_W[i] or TOUCH_GOAL_W[i]:
            score += 1.5

    # Opening / center preference.
    opening_factor = max(0.0, (18 - turn) / 18.0)
    score += opening_factor * (5.0 - 0.55 * (abs(r - 5) + abs(c - 5)))

    # Mild axis preference.
    score -= 0.12 * (abs(c - 5) if color == "b" else abs(r - 5))

    return score


def _detailed_score(
    i: int,
    coarse: float,
    me: set[int],
    opp: set[int],
    empties: list[int],
    color: str,
    base_me: int,
    base_opp: int,
) -> float:
    opp_color = _other(color)

    if _wins_from_move(i, me, color):
        return 1e12

    me2 = set(me)
    me2.add(i)

    # Reject moves that allow an immediate reply win.
    empties2 = [e for e in empties if e != i]
    opp_reply_wins = _find_immediate_wins(opp, empties2, opp_color, limit=1)

    new_me = _shortest_path_cost(me2, opp, color)
    new_opp = _shortest_path_cost(opp, me2, opp_color)

    base_me_c = _cap_cost(base_me)
    base_opp_c = _cap_cost(base_opp)
    new_me_c = _cap_cost(new_me)
    new_opp_c = _cap_cost(new_opp)

    score = 0.0
    score += 140.0 * (base_me_c - new_me_c)
    score += 110.0 * (new_opp_c - base_opp_c)
    score -= 9.0 * new_me_c
    score += 2.0 * coarse

    if opp_reply_wins:
        score -= 200000.0
    else:
        score += 5.0

    return score


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    me_set = {_idx(r, c) for r, c in me}
    opp_set = {_idx(r, c) for r, c in opp}
    occupied = me_set | opp_set

    empties = [i for i in range(N) if i not in occupied]
    if not empties:
        return (0, 0)

    # Opening book.
    op = _opening_move(occupied, color)
    if op is not None and op in empties:
        return _rc(op)

    opp_color = _other(color)

    # 1) Immediate win.
    my_wins = _find_immediate_wins(me_set, empties, color, limit=None)
    if my_wins:
        best = max(my_wins, key=lambda i: _center_tiebreak(i, color))
        return _rc(best)

    # 2) Immediate block if opponent threatens to win now.
    opp_wins = _find_immediate_wins(opp_set, empties, opp_color, limit=None)
    if opp_wins:
        best_move = None
        best_score = -10**18
        for i in opp_wins:
            # Try the block and pick the least bad / most useful one.
            coarse = 0.0
            s = _detailed_score(i, coarse, me_set, opp_set, empties, color, 12, 12)
            tb = _center_tiebreak(i, color)
            if best_move is None or s > best_score or (s == best_score and tb > _center_tiebreak(best_move, color)):
                best_move = i
                best_score = s
        return _rc(best_move if best_move is not None else opp_wins[0])

    # Strategic evaluation.
    ds_me_s, ds_me_g, base_me = _compute_metrics(me_set, opp_set, color)
    ds_opp_s, ds_opp_g, base_opp = _compute_metrics(opp_set, me_set, opp_color)

    me_comp = _component_ids(me_set)
    opp_comp = _component_ids(opp_set)

    turn = len(me) + len(opp)

    scored = []
    for i in empties:
        s = _static_score(
            i,
            me_set,
            opp_set,
            color,
            me_comp,
            opp_comp,
            ds_me_s,
            ds_me_g,
            base_me,
            ds_opp_s,
            ds_opp_g,
            base_opp,
            turn,
        )
        scored.append((s, i))

    scored.sort(key=lambda x: (x[0],) + _center_tiebreak(x[1], color), reverse=True)

    # Only deeply inspect the most promising moves.
    k = 12 if len(empties) > 50 else 10
    candidates = scored[:k] if len(scored) > k else scored

    best_move = None
    best_score = -10**18

    for coarse, i in candidates:
        s = _detailed_score(i, coarse, me_set, opp_set, empties, color, base_me, base_opp)
        tb = _center_tiebreak(i, color)
        if best_move is None or s > best_score or (s == best_score and tb > _center_tiebreak(best_move, color)):
            best_move = i
            best_score = s

    if best_move is not None:
        return _rc(best_move)

    # Final legal fallback.
    fallback = max(empties, key=lambda i: _center_tiebreak(i, color))
    return _rc(fallback)
