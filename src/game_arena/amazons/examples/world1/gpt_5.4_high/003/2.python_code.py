import time
from collections import deque
import numpy as np

SIZE = 6
DIRS = [(-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)]

INF = 10**9
MATE = 100000

CENTER = []
for r in range(SIZE):
    for c in range(SIZE):
        CENTER.append(5.0 - (abs(r - 2.5) + abs(c - 2.5)))


class _Timeout(Exception):
    pass


def _fmt_move(move):
    f, t, a = move
    fr, fc = divmod(f, SIZE)
    tr, tc = divmod(t, SIZE)
    ar, ac = divmod(a, SIZE)
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"


def _make_move(board, move, player):
    f, t, a = move
    board[f] = 0
    board[t] = player
    board[a] = -1


def _unmake_move(board, move, player):
    f, t, a = move
    board[a] = 0
    board[t] = 0
    board[f] = player


def _ray_mobility_from(board, start):
    r, c = divmod(start, SIZE)
    total = 0
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        while 0 <= nr < SIZE and 0 <= nc < SIZE:
            j = nr * SIZE + nc
            if board[j] != 0:
                break
            total += 1
            nr += dr
            nc += dc
    return total


def _queen_mobility(board, player):
    total = 0
    for i, v in enumerate(board):
        if v != player:
            continue
        r, c = divmod(i, SIZE)
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while 0 <= nr < SIZE and 0 <= nc < SIZE:
                j = nr * SIZE + nc
                if board[j] != 0:
                    break
                total += 1
                nr += dr
                nc += dc
    return total


def _has_any_destination(board, player):
    for i, v in enumerate(board):
        if v != player:
            continue
        r, c = divmod(i, SIZE)
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < SIZE and 0 <= nc < SIZE:
                if board[nr * SIZE + nc] == 0:
                    return True
    return False


def _pressure_score(arrow_idx, opp_rcs):
    ar, ac = divmod(arrow_idx, SIZE)
    score = 0.0
    for rr, cc in opp_rcs:
        dr = abs(ar - rr)
        dc = abs(ac - cc)
        m = max(dr, dc)
        if m == 1:
            score += 3.0
        elif m == 2 and (dr == 0 or dc == 0 or dr == dc):
            score += 1.0
    return score


def _first_legal_move(board, player):
    positions = [i for i, v in enumerate(board) if v == player]
    for f in positions:
        fr, fc = divmod(f, SIZE)
        board[f] = 0
        for dr, dc in DIRS:
            nr, nc = fr + dr, fc + dc
            while 0 <= nr < SIZE and 0 <= nc < SIZE:
                t = nr * SIZE + nc
                if board[t] != 0:
                    break
                board[t] = player
                tr, tc = nr, nc
                for adr, adc in DIRS:
                    ar, ac = tr + adr, tc + adc
                    while 0 <= ar < SIZE and 0 <= ac < SIZE:
                        a = ar * SIZE + ac
                        if board[a] != 0:
                            break
                        board[t] = 0
                        board[f] = player
                        return (f, t, a)
                        ar += adr
                        ac += adc
                board[t] = 0
                nr += dr
                nc += dc
        board[f] = player
    return None


def _generate_moves(board, player, limit=None, tt_move=None):
    opp = 3 - player
    my_positions = [i for i, v in enumerate(board) if v == player]
    opp_rcs = [divmod(i, SIZE) for i, v in enumerate(board) if v == opp]

    scored = []

    for f in my_positions:
        fr, fc = divmod(f, SIZE)
        board[f] = 0

        for dr, dc in DIRS:
            nr, nc = fr + dr, fc + dc
            while 0 <= nr < SIZE and 0 <= nc < SIZE:
                t = nr * SIZE + nc
                if board[t] != 0:
                    break

                board[t] = player
                to_center = CENTER[t]

                for adr, adc in DIRS:
                    ar, ac = nr + adr, nc + adc
                    while 0 <= ar < SIZE and 0 <= ac < SIZE:
                        a = ar * SIZE + ac
                        if board[a] != 0:
                            break

                        board[a] = -1
                        local = _ray_mobility_from(board, t)
                        pressure = _pressure_score(a, opp_rcs)
                        score = 2.2 * local + 1.0 * to_center + 0.8 * CENTER[a] + pressure
                        if a == f:
                            score += 0.3
                        move = (f, t, a)
                        if tt_move is not None and move == tt_move:
                            score += 10000.0
                        scored.append((score, move))
                        board[a] = 0

                        ar += adr
                        ac += adc

                board[t] = 0
                nr += dr
                nc += dc

        board[f] = player

    scored.sort(key=lambda x: x[0], reverse=True)
    if limit is not None and len(scored) > limit:
        scored = scored[:limit]
    return [m for _, m in scored]


def _queen_distances(board, player):
    dist = [99] * (SIZE * SIZE)
    q = deque()

    for i, v in enumerate(board):
        if v == player:
            dist[i] = 0
            q.append(i)

    while q:
        i = q.popleft()
        d = dist[i] + 1
        r, c = divmod(i, SIZE)

        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while 0 <= nr < SIZE and 0 <= nc < SIZE:
                j = nr * SIZE + nc
                if board[j] != 0:
                    break
                if dist[j] == 99:
                    dist[j] = d
                    q.append(j)
                nr += dr
                nc += dc

    return dist


def _territory_score(board, player):
    opp = 3 - player
    d_me = _queen_distances(board, player)
    d_opp = _queen_distances(board, opp)

    score = 0.0
    for i, v in enumerate(board):
        if v != 0:
            continue
        a = d_me[i]
        b = d_opp[i]
        if a < b:
            score += 1.0
            if b < 99:
                score += 0.15 * (b - a)
            else:
                score += 0.5
        elif b < a:
            score -= 1.0
            if a < 99:
                score -= 0.15 * (a - b)
            else:
                score -= 0.5
    return score


def _component_score(board, player):
    opp = 3 - player
    seen = [False] * (SIZE * SIZE)
    score = 0.0

    for i in range(SIZE * SIZE):
        if seen[i] or board[i] == -1:
            continue

        stack = [i]
        seen[i] = True
        empties = 0
        my_cnt = 0
        opp_cnt = 0

        while stack:
            j = stack.pop()
            v = board[j]
            if v == 0:
                empties += 1
            elif v == player:
                my_cnt += 1
            elif v == opp:
                opp_cnt += 1

            r, c = divmod(j, SIZE)
            for dr, dc in DIRS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < SIZE and 0 <= nc < SIZE:
                    k = nr * SIZE + nc
                    if not seen[k] and board[k] != -1:
                        seen[k] = True
                        stack.append(k)

        if my_cnt and not opp_cnt:
            score += empties + 1.5 * my_cnt
        elif opp_cnt and not my_cnt:
            score -= empties + 1.5 * opp_cnt

    return score


def _positional_score(board, player):
    opp = 3 - player
    score = 0.0
    for i, v in enumerate(board):
        if v == player:
            score += CENTER[i]
        elif v == opp:
            score -= CENTER[i]
    return score


def _evaluate(board, player, eval_cache):
    key = (player, tuple(board))
    if key in eval_cache:
        return eval_cache[key]

    opp = 3 - player
    my_mob = _queen_mobility(board, player)
    if my_mob == 0:
        return -MATE // 2

    opp_mob = _queen_mobility(board, opp)
    if opp_mob == 0:
        return MATE // 2

    empties = board.count(0)
    terr = _territory_score(board, player)
    comp = _component_score(board, player)
    pos = _positional_score(board, player)

    if empties > 18:
        score = 2.6 * (my_mob - opp_mob) + 6.5 * terr + 1.8 * comp + 0.35 * pos
    elif empties > 10:
        score = 2.2 * (my_mob - opp_mob) + 8.0 * terr + 2.5 * comp + 0.25 * pos
    else:
        score = 1.4 * (my_mob - opp_mob) + 10.5 * terr + 3.8 * comp + 0.15 * pos

    eval_cache[key] = score
    return score


def _node_move_limit(depth, empties):
    if depth >= 4:
        return 8 if empties > 8 else 10
    if depth == 3:
        return 10 if empties > 10 else 14
    if depth == 2:
        return 18 if empties > 12 else 24
    return None


def _root_width(depth, n_moves, empties):
    if depth == 1:
        return n_moves
    if depth == 2:
        return n_moves if n_moves <= 32 else 28
    if depth == 3:
        return n_moves if n_moves <= 18 else 14
    return n_moves if n_moves <= 10 else 8


def _negamax(board, player, depth, alpha, beta, ply, deadline, eval_cache, order_cache):
    if time.perf_counter() >= deadline:
        raise _Timeout

    if not _has_any_destination(board, player):
        return -MATE + ply

    if depth == 0:
        return _evaluate(board, player, eval_cache)

    key = (player, tuple(board))
    tt_move = order_cache.get(key)
    limit = _node_move_limit(depth, board.count(0))
    moves = _generate_moves(board, player, limit=limit, tt_move=tt_move)

    if not moves:
        return -MATE + ply

    opp = 3 - player
    best = -INF
    best_move = moves[0]

    for move in moves:
        _make_move(board, move, player)
        val = -_negamax(board, opp, depth - 1, -beta, -alpha, ply + 1, deadline, eval_cache, order_cache)
        _unmake_move(board, move, player)

        if val > best:
            best = val
            best_move = move

        if val > alpha:
            alpha = val
        if alpha >= beta:
            break

        if time.perf_counter() >= deadline:
            raise _Timeout

    order_cache[key] = best_move
    return best


def policy(board) -> str:
    flat = [int(x) for x in np.asarray(board).reshape(-1)]
    deadline = time.perf_counter() + 0.92

    moves = _generate_moves(flat, 1, limit=None, tt_move=None)
    if not moves:
        fallback = _first_legal_move(flat, 1)
        if fallback is not None:
            return _fmt_move(fallback)
        for i, v in enumerate(flat):
            if v == 1:
                r, c = divmod(i, SIZE)
                return f"{r},{c}:{r},{c}:{r},{c}"
        return "0,0:0,0:0,0"

    if len(moves) == 1:
        return _fmt_move(moves[0])

    ordered = moves[:]
    best_move = ordered[0]

    empties = flat.count(0)
    n_moves = len(ordered)

    max_depth = 2
    if n_moves <= 14 or empties <= 12:
        max_depth = 3
    if n_moves <= 8 and empties <= 8:
        max_depth = 4

    eval_cache = {}
    order_cache = {}

    for depth in range(1, max_depth + 1):
        try:
            width = _root_width(depth, len(ordered), empties)
            alpha = -INF
            beta = INF
            scored = []

            for move in ordered[:width]:
                if time.perf_counter() >= deadline:
                    raise _Timeout

                _make_move(flat, move, 1)
                val = -_negamax(flat, 2, depth - 1, -beta, -alpha, 1, deadline, eval_cache, order_cache)
                _unmake_move(flat, move, 1)

                scored.append((val, move))
                if val > alpha:
                    alpha = val

            if scored:
                scored.sort(key=lambda x: x[0], reverse=True)
                best_move = scored[0][1]
                searched = {m for _, m in scored}
                ordered = [m for _, m in scored] + [m for m in ordered if m not in searched]

        except _Timeout:
            break

    return _fmt_move(best_move)
