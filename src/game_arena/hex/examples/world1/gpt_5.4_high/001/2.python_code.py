
from collections import deque

BOARD = 11
N = BOARD * BOARD
WIN = 10**9
PATH_FACTOR = 200

ROWS = [i // BOARD for i in range(N)]
COLS = [i % BOARD for i in range(N)]

NEI = [[] for _ in range(N)]
for r in range(BOARD):
    for c in range(BOARD):
        i = r * BOARD + c
        if c > 0:
            NEI[i].append(i - 1)          # (r, c-1)
        if c + 1 < BOARD:
            NEI[i].append(i + 1)          # (r, c+1)
        if r > 0:
            NEI[i].append(i - BOARD)      # (r-1, c)
        if r > 0 and c + 1 < BOARD:
            NEI[i].append(i - BOARD + 1)  # (r-1, c+1)
        if r + 1 < BOARD:
            NEI[i].append(i + BOARD)      # (r+1, c)
        if r + 1 < BOARD and c > 0:
            NEI[i].append(i + BOARD - 1)  # (r+1, c-1)

START_B = list(range(BOARD))                    # top edge
START_W = [r * BOARD for r in range(BOARD)]    # left edge

GOAL_B = [ROWS[i] == BOARD - 1 for i in range(N)]  # bottom edge
GOAL_W = [COLS[i] == BOARD - 1 for i in range(N)]  # right edge

EDGE_B = [ROWS[i] == 0 or ROWS[i] == BOARD - 1 for i in range(N)]
EDGE_W = [COLS[i] == 0 or COLS[i] == BOARD - 1 for i in range(N)]

CENTER = (BOARD // 2) * BOARD + (BOARD // 2)

# Small positional bias: central cells are good, and for black central columns
# matter a bit more; for white central rows matter a bit more.
POS_B = [0] * N
POS_W = [0] * N
for i in range(N):
    r, c = ROWS[i], COLS[i]
    centerish = 6 - max(abs(r - 5), abs(c - 5))
    POS_B[i] = centerish + (5 - abs(c - 5))
    POS_W[i] = centerish + (5 - abs(r - 5))


def shortest_cost(board, mark, starts, goals):
    """0-1 BFS shortest connection cost for one player."""
    opp = 3 - mark
    INF = 255
    dist = [INF] * N
    dq = deque()

    for s in starts:
        cell = board[s]
        if cell == opp:
            continue
        c = 0 if cell == mark else 1
        if c < dist[s]:
            dist[s] = c
            if c == 0:
                dq.appendleft(s)
            else:
                dq.append(s)

    while dq:
        u = dq.popleft()
        d = dist[u]
        if goals[u]:
            return d
        for v in NEI[u]:
            cell = board[v]
            if cell == opp:
                continue
            nd = d if cell == mark else d + 1
            if nd < dist[v]:
                dist[v] = nd
                if cell == mark:
                    dq.appendleft(v)
                else:
                    dq.append(v)
    return INF


def has_won(board, mark, starts, goals):
    """Exact connectivity check on existing stones only."""
    seen = bytearray(N)
    stack = []
    for s in starts:
        if board[s] == mark:
            seen[s] = 1
            stack.append(s)

    while stack:
        u = stack.pop()
        if goals[u]:
            return True
        for v in NEI[u]:
            if not seen[v] and board[v] == mark:
                seen[v] = 1
                stack.append(v)
    return False


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    opp_color = 'w' if color == 'b' else 'b'

    starts_me = START_B if color == 'b' else START_W
    goals_me = GOAL_B if color == 'b' else GOAL_W
    starts_opp = START_W if color == 'b' else START_B
    goals_opp = GOAL_W if color == 'b' else GOAL_B

    pos_me = POS_B if color == 'b' else POS_W
    pos_opp = POS_W if color == 'b' else POS_B
    edge_me = EDGE_B if color == 'b' else EDGE_W
    edge_opp = EDGE_W if color == 'b' else EDGE_B

    board = [0] * N
    for r, c in me:
        if 0 <= r < BOARD and 0 <= c < BOARD:
            board[r * BOARD + c] = 1
    for r, c in opp:
        if 0 <= r < BOARD and 0 <= c < BOARD:
            idx = r * BOARD + c
            if board[idx] == 0:
                board[idx] = 2

    empties = [i for i in range(N) if board[i] == 0]
    if not empties:
        return (0, 0)  # no legal move exists; should not normally happen

    total_stones = N - len(empties)

    # Sensible opening.
    if total_stones == 0:
        return (5, 5)
    if board[CENTER] == 0 and total_stones <= 1:
        return (5, 5)

    def move_bonus(idx, mark, pos_arr, edge_arr):
        own_adj = 0
        opp_adj = 0
        enemy = 3 - mark
        for v in NEI[idx]:
            if board[v] == mark:
                own_adj += 1
            elif board[v] == enemy:
                opp_adj += 1
        return 3 * own_adj + 2 * opp_adj + pos_arr[idx] + (1 if edge_arr[idx] else 0)

    def shape_diff():
        score = 0
        for u, cell in enumerate(board):
            if cell == 1:
                score += pos_me[u]
                if edge_me[u]:
                    score += 1
                for v in NEI[u]:
                    if v > u and board[v] == 1:
                        score += 3
            elif cell == 2:
                score -= pos_opp[u]
                if edge_opp[u]:
                    score -= 1
                for v in NEI[u]:
                    if v > u and board[v] == 2:
                        score -= 3
        return score

    def evaluate():
        d_me = shortest_cost(board, 1, starts_me, goals_me)
        if d_me == 0:
            return WIN
        d_opp = shortest_cost(board, 2, starts_opp, goals_opp)
        if d_opp == 0:
            return -WIN
        return PATH_FACTOR * (d_opp - d_me) + shape_diff()

    # Exact endgame search.
    if len(empties) <= 8:
        memo = {}

        def solve(moves, to_move, alpha, beta):
            key = (to_move, bytes(board))
            if key in memo:
                return memo[key]

            if has_won(board, 1, starts_me, goals_me):
                val = WIN + len(moves)
                memo[key] = val
                return val
            if has_won(board, 2, starts_opp, goals_opp):
                val = -WIN - len(moves)
                memo[key] = val
                return val
            if not moves:
                val = evaluate()
                memo[key] = val
                return val

            if to_move == 1:
                value = -10**18
                ordered = sorted(
                    moves,
                    key=lambda i: move_bonus(i, 1, pos_me, edge_me),
                    reverse=True,
                )
                for idx in ordered:
                    board[idx] = 1
                    nxt = tuple(m for m in moves if m != idx)
                    sc = solve(nxt, 2, alpha, beta)
                    board[idx] = 0
                    if sc > value:
                        value = sc
                    if value > alpha:
                        alpha = value
                    if alpha >= beta:
                        break
            else:
                value = 10**18
                ordered = sorted(
                    moves,
                    key=lambda i: move_bonus(i, 2, pos_opp, edge_opp),
                    reverse=True,
                )
                for idx in ordered:
                    board[idx] = 2
                    nxt = tuple(m for m in moves if m != idx)
                    sc = solve(nxt, 1, alpha, beta)
                    board[idx] = 0
                    if sc < value:
                        value = sc
                    if value < beta:
                        beta = value
                    if alpha >= beta:
                        break

            memo[key] = value
            return value

        moves = tuple(empties)
        ordered = sorted(moves, key=lambda i: move_bonus(i, 1, pos_me, edge_me), reverse=True)
        best_idx = ordered[0]
        alpha = -10**18
        beta = 10**18
        for idx in ordered:
            board[idx] = 1
            if has_won(board, 1, starts_me, goals_me):
                board[idx] = 0
                return (ROWS[idx], COLS[idx])
            nxt = tuple(m for m in moves if m != idx)
            sc = solve(nxt, 2, alpha, beta)
            board[idx] = 0
            if sc > alpha:
                alpha = sc
                best_idx = idx
        return (ROWS[best_idx], COLS[best_idx])

    # Fast tactical info from current board.
    current_opp_cost = shortest_cost(board, 2, starts_opp, goals_opp)

    # 1-ply scoring for all moves. Also catches immediate wins.
    candidate_scores = {}
    scored = []
    for idx in empties:
        board[idx] = 1
        d_me = shortest_cost(board, 1, starts_me, goals_me)
        if d_me == 0:
            board[idx] = 0
            return (ROWS[idx], COLS[idx])
        d_opp = shortest_cost(board, 2, starts_opp, goals_opp)
        sc = PATH_FACTOR * (d_opp - d_me) + move_bonus(idx, 1, pos_me, edge_me)
        candidate_scores[idx] = sc
        scored.append((sc, idx))
        board[idx] = 0

    # If opponent has a one-move win, block it.
    if current_opp_cost == 1:
        threats = []
        for idx in empties:
            board[idx] = 2
            if shortest_cost(board, 2, starts_opp, goals_opp) == 0:
                threats.append(idx)
            board[idx] = 0
        if threats:
            best_block = max(threats, key=lambda i: (candidate_scores.get(i, -10**9), pos_me[i]))
            return (ROWS[best_block], COLS[best_block])

    scored.sort(reverse=True)

    if len(empties) > 90:
        top_k = 10
    elif len(empties) > 60:
        top_k = 12
    elif len(empties) > 30:
        top_k = 16
    else:
        top_k = min(24, len(scored))

    candidates = scored[:top_k]
    best_idx = candidates[0][1]
    best_val = -10**18
    best_base = candidates[0][0]

    # Shallow minimax: our candidate vs all opponent replies.
    for base_sc, idx in candidates:
        board[idx] = 1

        reply_moves = sorted(
            (move_bonus(r, 2, pos_opp, edge_opp), r)
            for r in empties
            if r != idx
        )

        worst = 10**18
        for _, r in reversed(reply_moves):
            board[r] = 2
            val = evaluate()
            board[r] = 0
            if val < worst:
                worst = val
            if worst <= best_val:
                break

        if worst == 10**18:
            worst = evaluate()

        board[idx] = 0

        if worst > best_val or (worst == best_val and base_sc > best_base):
            best_val = worst
            best_base = base_sc
            best_idx = idx

    # Guaranteed legal fallback.
    if board[best_idx] == 0:
        return (ROWS[best_idx], COLS[best_idx])

    for i in range(N):
        if board[i] == 0:
            return (ROWS[i], COLS[i])

    return (0, 0)
