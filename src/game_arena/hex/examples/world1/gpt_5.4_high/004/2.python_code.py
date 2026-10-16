
from __future__ import annotations

from collections import deque

N = 11
EMPTY = 0
BLACK = 1
WHITE = 2

BIG = 10**9
UNREACHABLE = 999
WIN_SCORE = 10**7

ALL_CELLS = [(r, c) for r in range(N) for c in range(N)]
TOP = [(0, c) for c in range(N)]
BOTTOM = [(N - 1, c) for c in range(N)]
LEFT = [(r, 0) for r in range(N)]
RIGHT = [(r, N - 1) for r in range(N)]


def _inside(r: int, c: int) -> bool:
    return 0 <= r < N and 0 <= c < N


# Hex neighbors for the board orientation described in the prompt:
# (r, c-1), (r, c+1), (r-1, c), (r-1, c+1), (r+1, c), (r+1, c-1)
NEIGHBORS = [[[] for _ in range(N)] for _ in range(N)]
for r in range(N):
    for c in range(N):
        for dr, dc in ((0, -1), (0, 1), (-1, 0), (-1, 1), (1, 0), (1, -1)):
            nr, nc = r + dr, c + dc
            if _inside(nr, nc):
                NEIGHBORS[r][c].append((nr, nc))

# Bridge relations:
# Two stones at these offsets form a classic Hex bridge with two support cells.
BRIDGE_PATTERNS = [
    ((1, 1), ((0, 1), (1, 0))),
    ((2, -1), ((1, 0), (1, -1))),
    ((1, -2), ((1, -1), (0, -1))),
    ((-1, -1), ((0, -1), (-1, 0))),
    ((-2, 1), ((-1, 0), (-1, 1))),
    ((-1, 2), ((-1, 1), (0, 1))),
]

# For each cell, store all bridge endpoint pairs for which this cell is a support.
# This lets the move heuristic reward bridge repair / bridge breaking.
SUPPORT_PATTERNS = [[[] for _ in range(N)] for _ in range(N)]
for r, c in ALL_CELLS:
    a = (r, c)
    for (dr, dc), (s1, s2) in BRIDGE_PATTERNS:
        br, bc = r + dr, c + dc
        s1r, s1c = r + s1[0], c + s1[1]
        s2r, s2c = r + s2[0], c + s2[1]
        if _inside(br, bc) and _inside(s1r, s1c) and _inside(s2r, s2c):
            b = (br, bc)
            if a < b:
                SUPPORT_PATTERNS[s1r][s1c].append((a, b, (s2r, s2c)))
                SUPPORT_PATTERNS[s2r][s2c].append((a, b, (s1r, s1c)))

# Hex distance to center for light positional tie-breaking.
CENTER_DIST = [[0] * N for _ in range(N)]
for r in range(N):
    for c in range(N):
        dr = r - 5
        dc = c - 5
        CENTER_DIST[r][c] = max(abs(dr), abs(dc), abs(dr + dc))


def _other(code: int) -> int:
    return WHITE if code == BLACK else BLACK


def _side_bits_for_cell(r: int, c: int, code: int) -> int:
    bits = 0
    if code == BLACK:
        if r == 0:
            bits |= 1
        if r == N - 1:
            bits |= 2
    else:
        if c == 0:
            bits |= 1
        if c == N - 1:
            bits |= 2
    return bits


def _hex_distance(a: tuple[int, int], b: tuple[int, int]) -> int:
    dr = a[0] - b[0]
    dc = a[1] - b[1]
    return max(abs(dr), abs(dc), abs(dr + dc))


def _path_cost(board: list[list[int]], code: int) -> int:
    """0-1 BFS shortest connection cost for one color."""
    opp = _other(code)
    dist = [[BIG] * N for _ in range(N)]
    dq = deque()

    starts = TOP if code == BLACK else LEFT

    for r, c in starts:
        cell = board[r][c]
        if cell == opp:
            continue
        w = 0 if cell == code else 1
        if w < dist[r][c]:
            dist[r][c] = w
            if w == 0:
                dq.appendleft((r, c))
            else:
                dq.append((r, c))

    target_black = code == BLACK

    while dq:
        r, c = dq.popleft()
        d = dist[r][c]

        if target_black:
            if r == N - 1:
                return d
        else:
            if c == N - 1:
                return d

        for nr, nc in NEIGHBORS[r][c]:
            cell = board[nr][nc]
            if cell == opp:
                continue
            w = 0 if cell == code else 1
            nd = d + w
            if nd < dist[nr][nc]:
                dist[nr][nc] = nd
                if w == 0:
                    dq.appendleft((nr, nc))
                else:
                    dq.append((nr, nc))

    return UNREACHABLE


def _distance_map(board: list[list[int]], code: int, from_start: bool) -> list[list[int]]:
    """Full 0-1 BFS distance map from one goal side."""
    opp = _other(code)
    dist = [[BIG] * N for _ in range(N)]
    dq = deque()

    if code == BLACK:
        starts = TOP if from_start else BOTTOM
    else:
        starts = LEFT if from_start else RIGHT

    for r, c in starts:
        cell = board[r][c]
        if cell == opp:
            continue
        w = 0 if cell == code else 1
        if w < dist[r][c]:
            dist[r][c] = w
            if w == 0:
                dq.appendleft((r, c))
            else:
                dq.append((r, c))

    while dq:
        r, c = dq.popleft()
        d = dist[r][c]
        for nr, nc in NEIGHBORS[r][c]:
            cell = board[nr][nc]
            if cell == opp:
                continue
            w = 0 if cell == code else 1
            nd = d + w
            if nd < dist[nr][nc]:
                dist[nr][nc] = nd
                if w == 0:
                    dq.appendleft((nr, nc))
                else:
                    dq.append((nr, nc))

    return dist


def _best_from_map(dist: list[list[int]], code: int) -> int:
    if code == BLACK:
        best = min(dist[N - 1][c] for c in range(N))
    else:
        best = min(dist[r][N - 1] for r in range(N))
    return best if best < BIG // 2 else UNREACHABLE


def _critical_sets(
    board: list[list[int]], code: int
) -> tuple[int, set[tuple[int, int]], set[tuple[int, int]]]:
    """
    Cells on some minimum-cost path (critical), and near-critical cells (+1).
    Only empty cells are returned.
    """
    ds = _distance_map(board, code, True)
    dt = _distance_map(board, code, False)
    base = _best_from_map(ds, code)

    critical: set[tuple[int, int]] = set()
    near: set[tuple[int, int]] = set()

    if base >= UNREACHABLE:
        return base, critical, near

    for r, c in ALL_CELLS:
        if board[r][c] != EMPTY:
            continue
        a = ds[r][c]
        b = dt[r][c]
        if a >= BIG // 2 or b >= BIG // 2:
            continue
        total = a + b - 1  # empty cell counted twice
        if total == base:
            critical.add((r, c))
        elif total == base + 1:
            near.add((r, c))

    return base, critical, near


def _component_info(
    board: list[list[int]], code: int
) -> tuple[list[list[int]], list[int]]:
    """
    Returns:
      labels[r][c] = component id for stones of this color, else -1
      side_flags[comp] = bitmask of touched goal sides
    """
    labels = [[-1] * N for _ in range(N)]
    side_flags: list[int] = []
    comp = 0

    for r, c in ALL_CELLS:
        if board[r][c] != code or labels[r][c] != -1:
            continue

        dq = deque([(r, c)])
        labels[r][c] = comp
        flags = 0

        while dq:
            x, y = dq.popleft()
            flags |= _side_bits_for_cell(x, y, code)
            for nx, ny in NEIGHBORS[x][y]:
                if board[nx][ny] == code and labels[nx][ny] == -1:
                    labels[nx][ny] = comp
                    dq.append((nx, ny))

        side_flags.append(flags)
        comp += 1

    return labels, side_flags


def _shape_score(board: list[list[int]], code: int) -> int:
    """Secondary tie-break evaluation for connectedness, bridges, and span."""
    opp = _other(code)
    adj = 0
    bridge = 0
    min_axis = N
    max_axis = -1

    for r, c in ALL_CELLS:
        if board[r][c] != code:
            continue

        axis = r if code == BLACK else c
        if axis < min_axis:
            min_axis = axis
        if axis > max_axis:
            max_axis = axis

        for nr, nc in NEIGHBORS[r][c]:
            if (nr > r or (nr == r and nc > c)) and board[nr][nc] == code:
                adj += 1

        for (dr, dc), (s1, s2) in BRIDGE_PATTERNS:
            br, bc = r + dr, c + dc
            if not _inside(br, bc) or board[br][bc] != code:
                continue
            if (br < r) or (br == r and bc <= c):
                continue

            s1r, s1c = r + s1[0], c + s1[1]
            s2r, s2c = r + s2[0], c + s2[1]
            if not (_inside(s1r, s1c) and _inside(s2r, s2c)):
                continue

            a = board[s1r][s1c]
            b = board[s2r][s2c]
            if a != opp and b != opp:
                bridge += 2
            elif a != opp or b != opp:
                bridge += 1

    span = 0 if max_axis < 0 else (max_axis - min_axis)
    return 2 * adj + 3 * bridge + 2 * span


def _static_eval(board: list[list[int]], my_code: int, opp_code: int) -> int:
    my_cost = _path_cost(board, my_code)
    if my_cost == 0:
        return WIN_SCORE

    opp_cost = _path_cost(board, opp_code)
    if opp_cost == 0:
        return -WIN_SCORE

    score = 120 * (opp_cost - my_cost)

    # Only spend extra work on shape details when the race is close.
    if abs(opp_cost - my_cost) <= 2:
        score += _shape_score(board, my_code)
        score -= _shape_score(board, opp_code)

    return score


def _local_move_bonus(
    board: list[list[int]],
    r: int,
    c: int,
    my_code: int,
    opp_code: int,
    my_labels: list[list[int]],
    my_side_flags: list[int],
    opp_labels: list[list[int]],
    my_critical: set[tuple[int, int]],
    my_near: set[tuple[int, int]],
    opp_critical: set[tuple[int, int]],
    opp_near: set[tuple[int, int]],
) -> int:
    """Fast move-ordering heuristic from the current board, before playing (r, c)."""
    adj_my = 0
    adj_opp = 0
    friendly_groups: set[int] = set()
    enemy_groups: set[int] = set()

    side_bits = _side_bits_for_cell(r, c, my_code)

    for nr, nc in NEIGHBORS[r][c]:
        v = board[nr][nc]
        if v == my_code:
            adj_my += 1
            lab = my_labels[nr][nc]
            if lab >= 0:
                friendly_groups.add(lab)
                side_bits |= my_side_flags[lab]
        elif v == opp_code:
            adj_opp += 1
            lab = opp_labels[nr][nc]
            if lab >= 0:
                enemy_groups.add(lab)

    bonus = 0

    # Merge own groups, especially groups touching opposite goal sides.
    bonus += 9 * len(friendly_groups)
    bonus += 3 * adj_my
    if side_bits == 3:
        bonus += 22

    # Slight reward for contesting enemy structure.
    bonus += 5 * len(enemy_groups)
    bonus += 2 * adj_opp

    # Current shortest-path criticality.
    if (r, c) in my_critical:
        bonus += 8
    elif (r, c) in my_near:
        bonus += 3

    if (r, c) in opp_critical:
        bonus += 10
    elif (r, c) in opp_near:
        bonus += 4

    # If this move forms a new bridge endpoint pair with existing stones.
    for (dr, dc), (s1, s2) in BRIDGE_PATTERNS:
        br, bc = r + dr, c + dc
        if not _inside(br, bc) or board[br][bc] != my_code:
            continue
        s1r, s1c = r + s1[0], c + s1[1]
        s2r, s2c = r + s2[0], c + s2[1]
        if not (_inside(s1r, s1c) and _inside(s2r, s2c)):
            continue
        a = board[s1r][s1c]
        b = board[s2r][s2c]
        if a != opp_code and b != opp_code:
            bonus += 6
        elif a != opp_code or b != opp_code:
            bonus += 2

    # If this move is a support cell for a bridge, reward repairing ours or breaking theirs.
    for (a, b, other_support) in SUPPORT_PATTERNS[r][c]:
        ar, ac = a
        br, bc = b
        orr, orc = other_support
        va = board[ar][ac]
        vb = board[br][bc]
        vo = board[orr][orc]

        if va == my_code and vb == my_code:
            if vo == opp_code:
                bonus += 8   # repair a half-broken own bridge
            elif vo == EMPTY:
                bonus += 3   # reinforce a living bridge
            else:
                bonus += 2   # complete around already-owned support
        elif va == opp_code and vb == opp_code:
            if vo == my_code:
                bonus += 7   # fully deny their bridge
            elif vo == EMPTY:
                bonus += 4   # force them to answer

    # Mild center / lane preference.
    if my_code == BLACK:
        bonus -= abs(c - 5)
        if r == 0 or r == N - 1:
            bonus += 2
    else:
        bonus -= abs(r - 5)
        if c == 0 or c == N - 1:
            bonus += 2

    bonus -= CENTER_DIST[r][c] // 2
    return bonus


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    my_code = BLACK if color == "b" else WHITE
    opp_code = _other(my_code)

    board = [[EMPTY] * N for _ in range(N)]
    for r, c in me:
        if _inside(r, c):
            board[r][c] = my_code
    for r, c in opp:
        if _inside(r, c):
            board[r][c] = opp_code

    empties = [(r, c) for r, c in ALL_CELLS if board[r][c] == EMPTY]

    # Legal fallback, just in case.
    if not empties:
        return (0, 0)
    if len(empties) == 1:
        return empties[0]

    # Opening: center is very strong.
    if len(me) + len(opp) <= 1 and board[5][5] == EMPTY:
        return (5, 5)

    # Current-board structure for move ordering.
    my_labels, my_side_flags = _component_info(board, my_code)
    opp_labels, _opp_side_flags = _component_info(board, opp_code)

    _my_base, my_critical, my_near = _critical_sets(board, my_code)
    _opp_base, opp_critical, opp_near = _critical_sets(board, opp_code)

    move_h: dict[tuple[int, int], int] = {}
    root_info: list[tuple[int, tuple[int, int]]] = []

    # 1) Immediate win check + root heuristics.
    for r, c in empties:
        local = _local_move_bonus(
            board, r, c,
            my_code, opp_code,
            my_labels, my_side_flags, opp_labels,
            my_critical, my_near, opp_critical, opp_near
        )

        board[r][c] = my_code
        my_cost = _path_cost(board, my_code)
        if my_cost == 0:
            board[r][c] = EMPTY
            return (r, c)

        opp_cost = _path_cost(board, opp_code)
        board[r][c] = EMPTY

        h = 120 * (opp_cost - my_cost) + local
        if my_cost == 1:
            h += 20
        if opp_cost == 1:
            h -= 20

        mv = (r, c)
        move_h[mv] = h
        root_info.append((h, mv))

    # 2) If opponent has an immediate win next move, we must address it.
    opp_wins_now: list[tuple[int, int]] = []
    for r, c in empties:
        board[r][c] = opp_code
        if _path_cost(board, opp_code) == 0:
            opp_wins_now.append((r, c))
        board[r][c] = EMPTY

    if len(opp_wins_now) == 1:
        return opp_wins_now[0]

    # Candidate set.
    root_info.sort(reverse=True)

    if opp_wins_now:
        # Already losing or in a very sharp position; at least try to block one of them.
        candidate_moves = sorted(opp_wins_now, key=lambda mv: move_h.get(mv, -BIG), reverse=True)
    else:
        m = len(empties)
        if m > 90:
            k = 18
        elif m > 70:
            k = 20
        elif m > 50:
            k = 24
        elif m > 35:
            k = 28
        else:
            k = m
        candidate_moves = [mv for _, mv in root_info[:k]]

    if not candidate_moves:
        return root_info[0][1] if root_info else empties[0]

    # Static reply priorities to help alpha-beta-style cutoff find strong replies early.
    reply_base_priority: dict[tuple[int, int], int] = {}
    for mv in empties:
        r, c = mv
        p = 0
        if mv in opp_critical:
            p += 10
        elif mv in opp_near:
            p += 4
        if mv in my_critical:
            p += 8
        elif mv in my_near:
            p += 3
        p -= CENTER_DIST[r][c] // 2
        reply_base_priority[mv] = p

    best_move = candidate_moves[0]
    best_value = -BIG

    # 3) Two-ply minimax:
    #    choose move maximizing the worst opponent reply.
    for mv in candidate_moves:
        r, c = mv
        board[r][c] = my_code

        remaining = [x for x in empties if x != mv]

        if not remaining:
            value = _static_eval(board, my_code, opp_code)
            board[r][c] = EMPTY
            if value > best_value or (value == best_value and move_h[mv] > move_h.get(best_move, -BIG)):
                best_value = value
                best_move = mv
            continue

        remaining.sort(
            key=lambda x: reply_base_priority[x] +
            (4 if _hex_distance(x, mv) == 1 else (2 if _hex_distance(x, mv) == 2 else 0)),
            reverse=True
        )

        worst_reply_value = BIG

        for rv in remaining:
            rr, rc = rv
            board[rr][rc] = opp_code
            score = _static_eval(board, my_code, opp_code)
            board[rr][rc] = EMPTY

            if score < worst_reply_value:
                worst_reply_value = score
                # Root-level alpha-beta style cutoff.
                if worst_reply_value <= best_value:
                    break

        board[r][c] = EMPTY

        if worst_reply_value > best_value or (
            worst_reply_value == best_value and move_h[mv] > move_h.get(best_move, -BIG)
        ):
            best_value = worst_reply_value
            best_move = mv

    # Final legal safety check.
    if best_move in empties:
        return best_move
    return empties[0]
