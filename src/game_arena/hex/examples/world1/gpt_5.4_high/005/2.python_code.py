
from collections import deque
from typing import List, Tuple

N = 11
NN = N * N

EMPTY = 0
BLACK = 1
WHITE = 2

INF = 10**9
WIN_SCORE = 10**8
EXACT_WIN = 10**6

NEI_DELTAS = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]

# Bridge endpoint offsets and the two support cells from the anchor endpoint.
BRIDGE_DELTAS = [
    ((1, 1), ((0, 1), (1, 0))),
    ((2, -1), ((1, 0), (1, -1))),
    ((1, -2), ((0, -1), (1, -1))),
    ((-1, -1), ((-1, 0), (0, -1))),
    ((-2, 1), ((-1, 0), (-1, 1))),
    ((-1, 2), ((-1, 1), (0, 1))),
]

RC = [(i // N, i % N) for i in range(NN)]

TOP = [i for i in range(N)]
BOTTOM = [i for i in range(NN - N, NN)]
LEFT = [r * N for r in range(N)]
RIGHT = [r * N + (N - 1) for r in range(N)]


def idx(r: int, c: int) -> int:
    return r * N + c


def inb(r: int, c: int) -> bool:
    return 0 <= r < N and 0 <= c < N


# Precompute neighbors.
NEI = [[] for _ in range(NN)]
for i in range(NN):
    r, c = RC[i]
    for dr, dc in NEI_DELTAS:
        nr, nc = r + dr, c + dc
        if inb(nr, nc):
            NEI[i].append(idx(nr, nc))

# Precompute bridge relations.
BRIDGE_PAIRS = []  # (a, b, s1, s2), unique with a < b
BRIDGE_AT_ENDPOINT = [[] for _ in range(NN)]  # i -> [(other, s1, s2), ...]
BRIDGE_AT_SUPPORT = [[] for _ in range(NN)]   # i -> [(a, b, other_support), ...]

for a in range(NN):
    ar, ac = RC[a]
    for (dr, dc), ((s1r, s1c), (s2r, s2c)) in BRIDGE_DELTAS:
        br, bc = ar + dr, ac + dc
        x1r, x1c = ar + s1r, ac + s1c
        x2r, x2c = ar + s2r, ac + s2c
        if inb(br, bc) and inb(x1r, x1c) and inb(x2r, x2c):
            b = idx(br, bc)
            s1 = idx(x1r, x1c)
            s2 = idx(x2r, x2c)
            if a < b:
                BRIDGE_PAIRS.append((a, b, s1, s2))
                BRIDGE_AT_ENDPOINT[a].append((b, s1, s2))
                BRIDGE_AT_ENDPOINT[b].append((a, s1, s2))
                BRIDGE_AT_SUPPORT[s1].append((a, b, s2))
                BRIDGE_AT_SUPPORT[s2].append((a, b, s1))

PREFERRED_ORDER = sorted(
    range(NN),
    key=lambda i: (
        abs(RC[i][0] - 5) + abs(RC[i][1] - 5),
        abs(RC[i][1] - 5),
        abs(RC[i][0] - 5),
    ),
)


def other_color(color: str) -> str:
    return 'w' if color == 'b' else 'b'


def stone_value(color: str) -> int:
    return BLACK if color == 'b' else WHITE


def build_board(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> List[int]:
    board = [EMPTY] * NN
    myv = stone_value(color)
    oppv = stone_value(other_color(color))
    for r, c in me:
        if inb(r, c):
            board[idx(r, c)] = myv
    for r, c in opp:
        if inb(r, c):
            j = idx(r, c)
            if board[j] == EMPTY:
                board[j] = oppv
    return board


def legal_moves(board: List[int]) -> List[int]:
    return [i for i, v in enumerate(board) if v == EMPTY]


def check_win(board: List[int], color: str) -> bool:
    own = stone_value(color)
    seen = [False] * NN
    dq = deque()

    if color == 'b':
        for i in TOP:
            if board[i] == own:
                seen[i] = True
                dq.append(i)
        while dq:
            x = dq.popleft()
            if x >= NN - N:
                return True
            for y in NEI[x]:
                if not seen[y] and board[y] == own:
                    seen[y] = True
                    dq.append(y)
    else:
        for i in LEFT:
            if board[i] == own:
                seen[i] = True
                dq.append(i)
        while dq:
            x = dq.popleft()
            if x % N == N - 1:
                return True
            for y in NEI[x]:
                if not seen[y] and board[y] == own:
                    seen[y] = True
                    dq.append(y)

    return False


def shortest_path_cost(board: List[int], color: str, reverse: bool = False) -> int:
    own = stone_value(color)
    enemy = stone_value(other_color(color))
    dist = [INF] * NN
    dq = deque()

    if color == 'b':
        starts = BOTTOM if reverse else TOP
        targets = TOP if reverse else BOTTOM
    else:
        starts = RIGHT if reverse else LEFT
        targets = LEFT if reverse else RIGHT

    for i in starts:
        v = board[i]
        if v == enemy:
            continue
        w = 0 if v == own else 1
        if w < dist[i]:
            dist[i] = w
            if w == 0:
                dq.appendleft(i)
            else:
                dq.append(i)

    while dq:
        x = dq.popleft()
        dx = dist[x]
        for y in NEI[x]:
            v = board[y]
            if v == enemy:
                continue
            w = 0 if v == own else 1
            nd = dx + w
            if nd < dist[y]:
                dist[y] = nd
                if w == 0:
                    dq.appendleft(y)
                else:
                    dq.append(y)

    best = INF
    for i in targets:
        if dist[i] < best:
            best = dist[i]
    return best


def border_dist(board: List[int], color: str, reverse: bool = False) -> List[int]:
    own = stone_value(color)
    enemy = stone_value(other_color(color))
    dist = [INF] * NN
    dq = deque()

    if color == 'b':
        starts = BOTTOM if reverse else TOP
    else:
        starts = RIGHT if reverse else LEFT

    for i in starts:
        v = board[i]
        if v == enemy:
            continue
        w = 0 if v == own else 1
        if w < dist[i]:
            dist[i] = w
            if w == 0:
                dq.appendleft(i)
            else:
                dq.append(i)

    while dq:
        x = dq.popleft()
        dx = dist[x]
        for y in NEI[x]:
            v = board[y]
            if v == enemy:
                continue
            w = 0 if v == own else 1
            nd = dx + w
            if nd < dist[y]:
                dist[y] = nd
                if w == 0:
                    dq.appendleft(y)
                else:
                    dq.append(y)

    return dist


def path_metrics(board: List[int], color: str) -> Tuple[int, int, int, int]:
    own = stone_value(color)
    enemy = stone_value(other_color(color))
    d1 = border_dist(board, color, False)
    d2 = border_dist(board, color, True)

    through = [INF] * NN
    best = INF

    for i, v in enumerate(board):
        if v == enemy:
            continue
        a = d1[i]
        b = d2[i]
        if a >= INF or b >= INF:
            continue
        w = 0 if v == own else 1
        t = a + b - w
        through[i] = t
        if t < best:
            best = t

    if best >= INF:
        return INF, 0, 0, 0

    width = 0
    near = 0
    pot = 0
    for i, v in enumerate(board):
        t = through[i]
        if t >= INF:
            continue
        add = 2 if v == own else 1
        if t == best:
            width += add
        elif t == best + 1:
            near += add
        if t <= 4:
            pot += (5 - t) * add

    return best, width, near, pot


def adjacency_count(board: List[int], color: str) -> int:
    own = stone_value(color)
    cnt = 0
    for i, v in enumerate(board):
        if v != own:
            continue
        for j in NEI[i]:
            if j > i and board[j] == own:
                cnt += 1
    return cnt


def bridge_potential_count(board: List[int], color: str) -> int:
    own = stone_value(color)
    enemy = stone_value(other_color(color))
    score = 0
    for a, b, s1, s2 in BRIDGE_PAIRS:
        if board[a] == own and board[b] == own:
            v1 = board[s1]
            v2 = board[s2]
            if v1 != enemy and v2 != enemy:
                if v1 == EMPTY and v2 == EMPTY:
                    score += 3
                elif (v1 == EMPTY and v2 == own) or (v2 == EMPTY and v1 == own):
                    score += 4
                elif v1 == own and v2 == own:
                    score += 2
            elif (v1 == enemy and v2 == EMPTY) or (v2 == enemy and v1 == EMPTY):
                score += 1
    return score


def anchor_count(board: List[int], color: str) -> int:
    own = stone_value(color)
    if color == 'b':
        t = sum(1 for i in TOP if board[i] == own)
        b = sum(1 for i in BOTTOM if board[i] == own)
    else:
        t = sum(1 for i in LEFT if board[i] == own)
        b = sum(1 for i in RIGHT if board[i] == own)
    return min(t, 2) + min(b, 2)


def local_move_bonus(board: List[int], mv: int, color: str) -> int:
    own = stone_value(color)
    enemy = stone_value(other_color(color))
    r, c = RC[mv]

    own_n = 0
    enemy_n = 0
    for j in NEI[mv]:
        if board[j] == own:
            own_n += 1
        elif board[j] == enemy:
            enemy_n += 1

    bonus = 6 * own_n + 3 * enemy_n
    bonus -= abs(r - 5) + abs(c - 5)

    if color == 'b':
        bonus -= abs(c - 5)
        if r == 0 or r == N - 1:
            bonus += 2
    else:
        bonus -= abs(r - 5)
        if c == 0 or c == N - 1:
            bonus += 2

    # Move as endpoint in own bridge patterns.
    for other, s1, s2 in BRIDGE_AT_ENDPOINT[mv]:
        vo = board[other]
        if vo == own:
            v1 = board[s1]
            v2 = board[s2]
            if v1 != enemy and v2 != enemy:
                if v1 == EMPTY and v2 == EMPTY:
                    bonus += 6
                elif (v1 == EMPTY and v2 == own) or (v2 == EMPTY and v1 == own):
                    bonus += 7
                elif v1 == own and v2 == own:
                    bonus += 3
            elif (v1 == enemy and v2 == EMPTY) or (v2 == enemy and v1 == EMPTY):
                bonus += 2

    # Move as support cell of own/opponent bridge.
    for a, b, other_s in BRIDGE_AT_SUPPORT[mv]:
        va = board[a]
        vb = board[b]
        vo = board[other_s]
        if va == own and vb == own:
            if vo == enemy:
                bonus += 14
            elif vo == EMPTY:
                bonus += 7
            else:
                bonus += 2
        elif va == enemy and vb == enemy:
            if vo == EMPTY:
                bonus += 12
            elif vo == own:
                bonus += 3

    return bonus


def simple_move_score(board: List[int], mv: int, color: str) -> int:
    own = stone_value(color)
    board[mv] = own
    if check_win(board, color):
        s = WIN_SCORE // 2 + local_move_bonus(board, mv, color)
    else:
        myd = shortest_path_cost(board, color)
        oppd = shortest_path_cost(board, other_color(color))
        s = 140 * (oppd - myd) + local_move_bonus(board, mv, color)
    board[mv] = EMPTY
    return s


def static_eval(board: List[int], root_color: str) -> int:
    opp_color = other_color(root_color)

    my_best, my_width, my_near, my_pot = path_metrics(board, root_color)
    op_best, op_width, op_near, op_pot = path_metrics(board, opp_color)

    my_adj = adjacency_count(board, root_color)
    op_adj = adjacency_count(board, opp_color)

    my_bridge = bridge_potential_count(board, root_color)
    op_bridge = bridge_potential_count(board, opp_color)

    my_anchor = anchor_count(board, root_color)
    op_anchor = anchor_count(board, opp_color)

    score = 220 * (op_best - my_best)
    score += 6 * (my_width - op_width)
    score += 2 * (my_near - op_near)
    score += 1 * (my_pot - op_pot)
    score += 4 * (my_adj - op_adj)
    score += 5 * (my_bridge - op_bridge)
    score += 6 * (my_anchor - op_anchor)
    return score


def any_immediate_win(board: List[int], color: str) -> bool:
    if shortest_path_cost(board, color) > 1:
        return False
    own = stone_value(color)
    for mv, v in enumerate(board):
        if v != EMPTY:
            continue
        board[mv] = own
        won = check_win(board, color)
        board[mv] = EMPTY
        if won:
            return True
    return False


def find_immediate_wins(board: List[int], color: str) -> List[int]:
    if shortest_path_cost(board, color) > 1:
        return []
    own = stone_value(color)
    wins = []
    for mv, v in enumerate(board):
        if v != EMPTY:
            continue
        board[mv] = own
        won = check_win(board, color)
        board[mv] = EMPTY
        if won:
            wins.append(mv)
    return wins


def choose_best_among(board: List[int], moves: List[int], color: str) -> int:
    own = stone_value(color)
    best_mv = moves[0]
    best_score = -10**18
    for mv in moves:
        board[mv] = own
        s = local_move_bonus(board, mv, color)
        myd = shortest_path_cost(board, color)
        oppd = shortest_path_cost(board, other_color(color))
        s += 30 * (oppd - myd)
        board[mv] = EMPTY
        if s > best_score:
            best_score = s
            best_mv = mv
    return best_mv


def ordered_small_moves(board: List[int], empties: List[int], color: str) -> List[int]:
    own = stone_value(color)
    scored = []
    for mv in empties:
        board[mv] = own
        s = local_move_bonus(board, mv, color)
        board[mv] = EMPTY
        scored.append((s, mv))
    scored.sort(reverse=True)
    return [mv for _, mv in scored]


def exact_value(board: List[int], to_move: str, root_color: str, empties: List[int],
                alpha: int, beta: int, memo: dict) -> int:
    prev = other_color(to_move)
    if check_win(board, prev):
        return EXACT_WIN if prev == root_color else -EXACT_WIN

    if not empties:
        return static_eval(board, root_color)

    key = (bytes(board), to_move)
    if key in memo:
        return memo[key]

    stone = stone_value(to_move)
    ordered = ordered_small_moves(board, empties, to_move)

    if to_move == root_color:
        best = -10**9
        for mv in ordered:
            board[mv] = stone
            rem = [x for x in empties if x != mv]
            val = exact_value(board, other_color(to_move), root_color, rem, alpha, beta, memo)
            board[mv] = EMPTY
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
    else:
        best = 10**9
        for mv in ordered:
            board[mv] = stone
            rem = [x for x in empties if x != mv]
            val = exact_value(board, other_color(to_move), root_color, rem, alpha, beta, memo)
            board[mv] = EMPTY
            if val < best:
                best = val
            if best < beta:
                beta = best
            if alpha >= beta:
                break

    memo[key] = best
    return best


def exact_policy(board: List[int], color: str, empties: List[int]) -> int:
    memo = {}
    stone = stone_value(color)
    ordered = sorted(empties, key=lambda mv: simple_move_score(board, mv, color), reverse=True)

    best_mv = ordered[0]
    best_val = -10**9

    for mv in ordered:
        board[mv] = stone
        if check_win(board, color):
            board[mv] = EMPTY
            return mv
        rem = [x for x in empties if x != mv]
        val = exact_value(board, other_color(color), color, rem, -EXACT_WIN, EXACT_WIN, memo)
        board[mv] = EMPTY
        if val > best_val:
            best_val = val
            best_mv = mv
        if best_val == EXACT_WIN:
            break

    return best_mv


def order_opponent_replies(board: List[int], opp_color: str, root_color: str, empties: List[int]) -> List[int]:
    oppv = stone_value(opp_color)
    od1 = border_dist(board, opp_color, False)
    od2 = border_dist(board, opp_color, True)
    rd1 = border_dist(board, root_color, False)
    rd2 = border_dist(board, root_color, True)

    scored = []
    for mv in empties:
        if od1[mv] >= INF or od2[mv] >= INF:
            t_opp = 99
        else:
            t_opp = od1[mv] + od2[mv] - 1

        if rd1[mv] >= INF or rd2[mv] >= INF:
            t_root = 99
        else:
            t_root = rd1[mv] + rd2[mv] - 1

        board[mv] = oppv
        lb = local_move_bonus(board, mv, opp_color)
        board[mv] = EMPTY

        s = -110 * t_opp - 55 * t_root + lb
        scored.append((s, mv))

    scored.sort(reverse=True)

    m = len(empties)
    if m <= 18:
        k = m
    elif m <= 40:
        k = 16
    elif m <= 70:
        k = 12
    else:
        k = 10

    return [mv for _, mv in scored[:k]]


def opening_move(board: List[int], color: str) -> int | None:
    total = sum(1 for v in board if v != EMPTY)
    if total == 0 and board[idx(5, 5)] == EMPTY:
        return idx(5, 5)

    if total == 1 and color == 'w':
        prefs = [
            idx(5, 4), idx(4, 6), idx(6, 4),
            idx(4, 5), idx(5, 6), idx(6, 5),
            idx(5, 5),
        ]
        for mv in prefs:
            if board[mv] == EMPTY:
                return mv

    if total <= 2 and board[idx(5, 5)] == EMPTY:
        return idx(5, 5)

    return None


def fallback_move(me: List[Tuple[int, int]], opp: List[Tuple[int, int]]) -> Tuple[int, int]:
    occ = set(me) | set(opp)
    for i in PREFERRED_ORDER:
        rc = RC[i]
        if rc not in occ:
            return rc
    return (0, 0)


def _policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Tuple[int, int]:
    board = build_board(me, opp, color)
    empties = legal_moves(board)

    if not empties:
        return (0, 0)

    if len(empties) == 1:
        return RC[empties[0]]

    # If the arena somehow provides an already-terminal position, still return legal.
    if check_win(board, color) or check_win(board, other_color(color)):
        return RC[empties[0]]

    om = opening_move(board, color)
    if om is not None:
        return RC[om]

    # Exact search in very small endgames.
    if len(empties) <= 8:
        mv = exact_policy(board, color, empties)
        return RC[mv]

    opp_color = other_color(color)
    myv = stone_value(color)
    oppv = stone_value(opp_color)

    # Immediate win.
    my_wins = find_immediate_wins(board, color)
    if my_wins:
        mv = choose_best_among(board, my_wins, color)
        return RC[mv]

    # Immediate block.
    opp_wins = find_immediate_wins(board, opp_color)
    if opp_wins:
        if len(opp_wins) == 1:
            return RC[opp_wins[0]]
        root_candidates = opp_wins[:]  # if multiple, game may already be lost; choose best block
    else:
        root_candidates = empties

    # Root ordering.
    root_scored = [(simple_move_score(board, mv, color), mv) for mv in root_candidates]
    root_scored.sort(reverse=True)

    m = len(root_candidates)
    if m <= 30:
        root_k = m
    elif m <= 60:
        root_k = 50
    elif m <= 90:
        root_k = 40
    else:
        root_k = 32

    search_moves = root_scored[:root_k]
    best_mv = search_moves[0][1]
    best_val = -10**18
    best_ord = -10**18

    for ord_score, mv in search_moves:
        board[mv] = myv

        if check_win(board, color):
            board[mv] = EMPTY
            return RC[mv]

        # If opponent has any immediate winning reply, this move is tactically bad.
        opp_sp = shortest_path_cost(board, opp_color)
        if opp_sp <= 1 and any_immediate_win(board, opp_color):
            val = -WIN_SCORE + ord_score
            board[mv] = EMPTY
        else:
            rem = [i for i, v in enumerate(board) if v == EMPTY]
            if not rem:
                val = static_eval(board, color)
                board[mv] = EMPTY
            else:
                replies = order_opponent_replies(board, opp_color, color, rem)
                worst = 10**18
                for omv in replies:
                    board[omv] = oppv
                    leaf = static_eval(board, color)
                    board[omv] = EMPTY
                    if leaf < worst:
                        worst = leaf
                    if worst <= best_val:
                        break
                val = worst
                board[mv] = EMPTY

        if val > best_val or (val == best_val and ord_score > best_ord):
            best_val = val
            best_ord = ord_score
            best_mv = mv

    return RC[best_mv]


def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Tuple[int, int]:
    try:
        mv = _policy(me, opp, color)
        r, c = mv
        occ = set(me) | set(opp)
        if 0 <= r < N and 0 <= c < N and (r, c) not in occ:
            return mv
        return fallback_move(me, opp)
    except Exception:
        return fallback_move(me, opp)
