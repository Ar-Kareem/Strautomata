
import time
import math
from collections import deque

N = 11
MID = 5
INF = 10**9
WIN_SCORE = 10_000_000

# Hex neighbors for the coordinate system described in the prompt.
DIRS = ((0, -1), (0, 1), (-1, 0), (-1, 1), (1, 0), (1, -1))


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    """
    Return a legal move for 11x11 Hex.
    board values: 0 empty, 1 us, 2 opponent.
    """
    board = _make_board(me, opp)
    fallback = _fallback_move(board, color)

    try:
        # Keep margin below the 1 second limit.
        deadline = time.perf_counter() + 0.88
        move = _choose_move(board, color, deadline)
        if _is_legal(board, move):
            return move
    except Exception:
        pass

    return fallback


def _make_board(me, opp):
    board = [[0 for _ in range(N)] for _ in range(N)]
    for r, c in me:
        if _inside(r, c):
            board[r][c] = 1
    for r, c in opp:
        if _inside(r, c):
            board[r][c] = 2
    return board


def _choose_move(board, color, deadline):
    empties = _legal_moves(board)
    if not empties:
        return (0, 0)

    fallback = _fallback_move(board, color)
    opp_color = _other(color)
    total_stones = N * N - len(empties)

    # Opening: center is extremely valuable in no-swap Hex.
    if total_stones < 3 and board[MID][MID] == 0:
        return (MID, MID)

    # 1. Win immediately if possible.
    my_wins = _winning_moves(board, 1, color)
    if my_wins:
        return _select_best_local(board, my_wins, 1, color)

    # 2. Block opponent's immediate win.
    opp_wins = _winning_moves(board, 2, opp_color)
    if opp_wins:
        return _best_block(board, opp_wins, color)

    # 3. Small exact search in very late endgames.
    if len(empties) <= 6:
        exact = _exact_search_move(board, color, deadline)
        if exact is not None and _is_legal(board, exact):
            return exact
        if time.perf_counter() > deadline:
            return fallback

    # Search width depends on game phase.
    if len(empties) > 80:
        root_limit, resp_limit = 10, 6
    elif len(empties) > 45:
        root_limit, resp_limit = 12, 7
    elif len(empties) > 20:
        root_limit, resp_limit = 14, 8
    else:
        root_limit, resp_limit = min(18, len(empties)), min(10, len(empties))

    root_moves = _candidate_moves(board, 1, color, root_limit, deadline)
    if not root_moves:
        return fallback

    # 4. If we can create two independent immediate winning moves, do it.
    for m in root_moves:
        if time.perf_counter() > deadline:
            break
        r, c = m
        board[r][c] = 1
        try:
            if _has_connection(board, 1, color):
                return m
            if len(_winning_moves(board, 1, color, cap=2)) >= 2:
                return m
        finally:
            board[r][c] = 0

    # 5. Shallow adversarial search: our move, then opponent's best reply.
    best_move = root_moves[0]
    best_value = -INF

    for idx, m in enumerate(root_moves):
        if time.perf_counter() > deadline:
            break

        r, c = m
        board[r][c] = 1
        try:
            if _has_connection(board, 1, color):
                return m

            opp_responses = _candidate_moves(board, 2, opp_color, resp_limit, deadline)
            if not opp_responses:
                value = _static_eval(board, color)
            else:
                worst_reply_value = INF
                checked = 0

                for om in opp_responses:
                    if time.perf_counter() > deadline:
                        break

                    rr, cc = om
                    board[rr][cc] = 2
                    try:
                        leaf_value = _static_eval(board, color)
                    finally:
                        board[rr][cc] = 0

                    checked += 1
                    if leaf_value < worst_reply_value:
                        worst_reply_value = leaf_value

                if checked == 0:
                    break

                value = worst_reply_value

            # Small stable tie-breaker preserving root heuristic order.
            value += (len(root_moves) - idx) * 0.01

            if value > best_value:
                best_value = value
                best_move = m
        finally:
            board[r][c] = 0

    return best_move if _is_legal(board, best_move) else fallback


def _other(color):
    return "w" if color == "b" else "b"


def _inside(r, c):
    return 0 <= r < N and 0 <= c < N


def _neighbors(r, c):
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < N and 0 <= nc < N:
            yield nr, nc


def _is_legal(board, move):
    if not isinstance(move, tuple) or len(move) != 2:
        return False
    r, c = move
    return _inside(r, c) and board[r][c] == 0


def _legal_moves(board):
    return [(r, c) for r in range(N) for c in range(N) if board[r][c] == 0]


def _hex_dist_delta(dr, dc):
    # Axial-like distance for this skewed coordinate system.
    return (abs(dr) + abs(dc) + abs(dr + dc)) // 2


ALL_CELLS = [(r, c) for r in range(N) for c in range(N)]
CENTER_ORDER_B = sorted(
    ALL_CELLS,
    key=lambda x: (
        _hex_dist_delta(x[0] - MID, x[1] - MID),
        abs(x[1] - MID),
        abs(x[0] - MID),
    ),
)
CENTER_ORDER_W = sorted(
    ALL_CELLS,
    key=lambda x: (
        _hex_dist_delta(x[0] - MID, x[1] - MID),
        abs(x[0] - MID),
        abs(x[1] - MID),
    ),
)


def _center_order_for(color):
    return CENTER_ORDER_B if color == "b" else CENTER_ORDER_W


def _fallback_move(board, color):
    for r, c in _center_order_for(color):
        if board[r][c] == 0:
            return (r, c)
    return (0, 0)


def _touches_side(r, c, color):
    if color == "b":
        return r == 0, r == N - 1
    return c == 0, c == N - 1


def _has_connection(board, player, color):
    seen = [[False for _ in range(N)] for _ in range(N)]
    q = deque()

    if color == "b":
        for c in range(N):
            if board[0][c] == player:
                seen[0][c] = True
                q.append((0, c))

        while q:
            r, c = q.popleft()
            if r == N - 1:
                return True
            for nr, nc in _neighbors(r, c):
                if not seen[nr][nc] and board[nr][nc] == player:
                    seen[nr][nc] = True
                    q.append((nr, nc))
    else:
        for r in range(N):
            if board[r][0] == player:
                seen[r][0] = True
                q.append((r, 0))

        while q:
            r, c = q.popleft()
            if c == N - 1:
                return True
            for nr, nc in _neighbors(r, c):
                if not seen[nr][nc] and board[nr][nc] == player:
                    seen[nr][nc] = True
                    q.append((nr, nc))

    return False


def _shortest_distance(board, player, color):
    """
    0/1 Dijkstra distance from one target side to the other.
    Own stones cost 0, empty cells cost 1, enemy stones are blocked.
    """
    enemy = 3 - player
    dist = [[INF for _ in range(N)] for _ in range(N)]
    dq = deque()

    if color == "b":
        for c in range(N):
            v = board[0][c]
            if v == enemy:
                continue
            cost = 0 if v == player else 1
            if cost < dist[0][c]:
                dist[0][c] = cost
                if cost == 0:
                    dq.appendleft((0, c))
                else:
                    dq.append((0, c))

        while dq:
            r, c = dq.popleft()
            d = dist[r][c]
            if r == N - 1:
                return d
            for nr, nc in _neighbors(r, c):
                v = board[nr][nc]
                if v == enemy:
                    continue
                step = 0 if v == player else 1
                nd = d + step
                if nd < dist[nr][nc]:
                    dist[nr][nc] = nd
                    if step == 0:
                        dq.appendleft((nr, nc))
                    else:
                        dq.append((nr, nc))
    else:
        for r in range(N):
            v = board[r][0]
            if v == enemy:
                continue
            cost = 0 if v == player else 1
            if cost < dist[r][0]:
                dist[r][0] = cost
                if cost == 0:
                    dq.appendleft((r, 0))
                else:
                    dq.append((r, 0))

        while dq:
            r, c = dq.popleft()
            d = dist[r][c]
            if c == N - 1:
                return d
            for nr, nc in _neighbors(r, c):
                v = board[nr][nc]
                if v == enemy:
                    continue
                step = 0 if v == player else 1
                nd = d + step
                if nd < dist[nr][nc]:
                    dist[nr][nc] = nd
                    if step == 0:
                        dq.appendleft((nr, nc))
                    else:
                        dq.append((nr, nc))

    return INF


def _winning_moves(board, player, color, cap=None):
    """
    Empty cells that complete player's connection immediately.
    """
    if _shortest_distance(board, player, color) != 1:
        return []

    moves = []
    for r in range(N):
        for c in range(N):
            if board[r][c] != 0:
                continue

            board[r][c] = player
            try:
                if _has_connection(board, player, color):
                    moves.append((r, c))
                    if cap is not None and len(moves) >= cap:
                        return moves
            finally:
                board[r][c] = 0

    return moves


def _select_best_local(board, moves, player, color):
    best = moves[0]
    best_score = -INF
    for m in moves:
        s = _local_move_score(board, m, player, color)
        if s > best_score:
            best_score = s
            best = m
    return best


def _best_block(board, opp_wins, color):
    opp_color = _other(color)
    best = opp_wins[0]
    best_score = -INF

    for m in opp_wins:
        r, c = m
        if board[r][c] != 0:
            continue

        board[r][c] = 1
        try:
            if _has_connection(board, 1, color):
                return m

            remaining = len(_winning_moves(board, 2, opp_color, cap=2))
            score = -500_000 * remaining + _static_eval(board, color)
            score += _local_move_score(board, m, 1, color)

            if score > best_score:
                best_score = score
                best = m
        finally:
            board[r][c] = 0

    return best


def _component_labels(board, player, color):
    labels = [[-1 for _ in range(N)] for _ in range(N)]
    infos = []

    for r in range(N):
        for c in range(N):
            if board[r][c] != player or labels[r][c] != -1:
                continue

            idx = len(infos)
            q = [(r, c)]
            labels[r][c] = idx
            qi = 0
            size = 0
            side1 = False
            side2 = False

            while qi < len(q):
                x, y = q[qi]
                qi += 1
                size += 1

                a, b = _touches_side(x, y, color)
                side1 = side1 or a
                side2 = side2 or b

                for nx, ny in _neighbors(x, y):
                    if board[nx][ny] == player and labels[nx][ny] == -1:
                        labels[nx][ny] = idx
                        q.append((nx, ny))

            infos.append((size, side1, side2))

    return labels, infos


def _make_bridge_data():
    data = []
    origin_neighbors = set(DIRS)
    for dr in range(-2, 3):
        for dc in range(-2, 3):
            if dr == 0 and dc == 0:
                continue
            if _hex_dist_delta(dr, dc) != 2:
                continue

            other_neighbors = {(dr + x, dc + y) for x, y in DIRS}
            commons = tuple(origin_neighbors & other_neighbors)
            if len(commons) == 2:
                data.append((dr, dc, commons))
    return tuple(data)


BRIDGE_DATA = _make_bridge_data()


def _bridge_score(board, r, c, player):
    enemy = 3 - player
    score = 0.0

    for dr, dc, commons in BRIDGE_DATA:
        rr, cc = r + dr, c + dc
        if not _inside(rr, cc):
            continue

        v = board[rr][cc]
        if v == 0:
            continue

        if v == player:
            blocked = False
            empty_count = 0
            for cr, cco in commons:
                sr, sc = r + cr, c + cco
                if not _inside(sr, sc):
                    blocked = True
                    break
                sv = board[sr][sc]
                if sv == enemy:
                    blocked = True
                    break
                if sv == 0:
                    empty_count += 1
            if not blocked:
                score += 16.0 if empty_count == 2 else 7.0

        elif v == enemy:
            # Occupying a good enemy bridge endpoint is useful defense.
            blocked = False
            empty_count = 0
            for cr, cco in commons:
                sr, sc = r + cr, c + cco
                if not _inside(sr, sc):
                    blocked = True
                    break
                sv = board[sr][sc]
                if sv == player:
                    blocked = True
                    break
                if sv == 0:
                    empty_count += 1
            if not blocked:
                score += 11.0 if empty_count == 2 else 4.0

    return score


def _local_move_score(
    board,
    move,
    player,
    color,
    labels_p=None,
    infos_p=None,
    labels_e=None,
    infos_e=None,
):
    r, c = move
    enemy = 3 - player
    enemy_color = _other(color)

    if labels_p is None or infos_p is None:
        labels_p, infos_p = _component_labels(board, player, color)
    if labels_e is None or infos_e is None:
        labels_e, infos_e = _component_labels(board, enemy, enemy_color)

    score = 0.0

    # Center and main-axis preference.
    hd = _hex_dist_delta(r - MID, c - MID)
    score += 4.0 * (N - 1 - hd)

    if color == "b":
        score += 5.0 * (MID - abs(c - MID))
        if r == 0 or r == N - 1:
            score += 3.0
        if c == 0 or c == N - 1:
            score -= 4.0
    else:
        score += 5.0 * (MID - abs(r - MID))
        if c == 0 or c == N - 1:
            score += 3.0
        if r == 0 or r == N - 1:
            score -= 4.0

    own_components = set()
    enemy_components = set()
    adj_own = 0
    adj_enemy = 0

    for nr, nc in _neighbors(r, c):
        v = board[nr][nc]
        if v == player:
            adj_own += 1
            lab = labels_p[nr][nc]
            if lab >= 0:
                own_components.add(lab)
        elif v == enemy:
            adj_enemy += 1
            lab = labels_e[nr][nc]
            if lab >= 0:
                enemy_components.add(lab)

    # Connecting multiple friendly groups is often decisive.
    score += 14.0 * adj_own
    score += 24.0 * max(0, len(own_components) - 1)
    for lab in own_components:
        score += 2.0 * min(12, infos_p[lab][0])

    # Blocking and leaning against opponent groups.
    score += 8.0 * adj_enemy
    score += 16.0 * max(0, len(enemy_components) - 1)

    # Own side contact.
    s1, s2 = _touches_side(r, c, color)
    for lab in own_components:
        _, a, b = infos_p[lab]
        s1 = s1 or a
        s2 = s2 or b
    if s1:
        score += 10.0
    if s2:
        score += 10.0
    if s1 and s2:
        score += 1000.0

    # Opponent side contact: good defensive squares.
    es1, es2 = _touches_side(r, c, enemy_color)
    for lab in enemy_components:
        _, a, b = infos_e[lab]
        es1 = es1 or a
        es2 = es2 or b
    if es1 and es2:
        score += 70.0
    elif es1 or es2:
        score += 6.0

    score += _bridge_score(board, r, c, player)
    return score


def _move_score(board, move, player, color, labels_p=None, infos_p=None, labels_e=None, infos_e=None):
    r, c = move
    enemy = 3 - player
    enemy_color = _other(color)

    local = _local_move_score(
        board, move, player, color, labels_p, infos_p, labels_e, infos_e
    )

    board[r][c] = player
    try:
        pd = _shortest_distance(board, player, color)
        ed = _shortest_distance(board, enemy, enemy_color)
    finally:
        board[r][c] = 0

    if pd == 0:
        return WIN_SCORE + local
    if ed == 0:
        return -WIN_SCORE + local

    pdc = min(pd, 30)
    edc = min(ed, 30)

    score = local
    score += 3500.0 * (edc - pdc)
    score += 9000.0 / (pdc + 1.0)
    score -= 8500.0 / (edc + 1.0)

    # Creating a single threat is good but usually blockable.
    if pd == 1:
        score += 2600.0
    if ed == 1:
        score -= 2200.0

    return score


def _rank_moves(board, player, color, deadline=None):
    enemy = 3 - player
    enemy_color = _other(color)

    labels_p, infos_p = _component_labels(board, player, color)
    labels_e, infos_e = _component_labels(board, enemy, enemy_color)

    scored = []
    for r in range(N):
        for c in range(N):
            if board[r][c] != 0:
                continue

            if deadline is not None and time.perf_counter() > deadline:
                scored.sort(key=lambda x: x[0], reverse=True)
                return scored

            s = _move_score(
                board,
                (r, c),
                player,
                color,
                labels_p,
                infos_p,
                labels_e,
                infos_e,
            )
            scored.append((s, (r, c)))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored


def _candidate_moves(board, player, color, limit, deadline=None):
    enemy = 3 - player
    enemy_color = _other(color)

    result = []
    seen = set()

    def add(m):
        if m not in seen and _is_legal(board, m):
            seen.add(m)
            result.append(m)

    # If current player can win, only winning moves matter.
    own_wins = _winning_moves(board, player, color, cap=max(1, limit))
    if own_wins:
        for m in own_wins:
            add(m)
        return result

    # If opponent can win, include blocking moves first.
    enemy_wins = _winning_moves(board, enemy, enemy_color, cap=max(4, limit))
    for m in enemy_wins:
        add(m)

    if len(result) >= limit:
        return result

    ranked = _rank_moves(board, player, color, deadline)
    for _, m in ranked:
        add(m)
        if len(result) >= limit:
            break

    if not result:
        for m in _center_order_for(color):
            add(m)
            if result:
                break

    return result


def _component_eval(board, player, color):
    _, infos = _component_labels(board, player, color)
    score = 0.0
    for size, s1, s2 in infos:
        score += 10.0 * math.sqrt(size)
        if s1:
            score += 8.0 + 1.5 * size
        if s2:
            score += 8.0 + 1.5 * size
    return score


def _static_eval(board, color):
    """
    Evaluation from our/root perspective.
    In the main search this is usually called after opponent's reply,
    so distance 1 for us means we win on the next move.
    """
    opp_color = _other(color)

    md = _shortest_distance(board, 1, color)
    od = _shortest_distance(board, 2, opp_color)

    if md == 0:
        return WIN_SCORE
    if od == 0:
        return -WIN_SCORE

    mdc = min(md, 30)
    odc = min(od, 30)

    value = 0.0
    value += 4500.0 * (odc - mdc)
    value += 13000.0 / (mdc + 1.0)
    value -= 12500.0 / (odc + 1.0)

    # If it is our turn next and we have a one-move win, this is nearly decisive.
    if md == 1:
        value += 200_000.0
    elif od == 1:
        # A single opponent threat can usually be blocked; two are often losing.
        opp_threats = len(_winning_moves(board, 2, opp_color, cap=2))
        if opp_threats >= 2:
            value -= 200_000.0
        else:
            value -= 6000.0

    value += _component_eval(board, 1, color)
    value -= _component_eval(board, 2, opp_color)

    return value


class _Timeout(Exception):
    pass


def _exact_search_move(board, color, deadline):
    """
    Tiny exact solver for <= 6 empty cells.
    Returns a winning move if one can be proven quickly.
    """
    empties = _legal_moves(board)
    if len(empties) > 6:
        return None

    memo = {}
    opp_color = _other(color)

    def board_key(player):
        flat = []
        for row in board:
            flat.extend(row)
        return (player, tuple(flat))

    def can_current_player_win(player, player_color):
        if time.perf_counter() > deadline:
            raise _Timeout()

        enemy = 3 - player
        enemy_color = _other(player_color)

        # If the previous move connected, current player already lost.
        if _has_connection(board, enemy, enemy_color):
            return False

        if _winning_moves(board, player, player_color, cap=1):
            return True

        legal = _legal_moves(board)
        if not legal:
            return False

        key = board_key(player)
        if key in memo:
            return memo[key]

        moves = _candidate_moves(board, player, player_color, len(legal), None)

        for m in moves:
            r, c = m
            board[r][c] = player
            try:
                opp_can_win = can_current_player_win(enemy, enemy_color)
            finally:
                board[r][c] = 0

            if not opp_can_win:
                memo[key] = True
                return True

        memo[key] = False
        return False

    try:
        root_moves = _candidate_moves(board, 1, color, len(empties), None)
        for m in root_moves:
            r, c = m
            board[r][c] = 1
            try:
                if _has_connection(board, 1, color):
                    return m
                if not can_current_player_win(2, opp_color):
                    return m
            finally:
                board[r][c] = 0
    except _Timeout:
        return None

    return None
