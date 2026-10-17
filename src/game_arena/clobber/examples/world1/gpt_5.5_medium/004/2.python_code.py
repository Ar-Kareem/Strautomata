
import time

ROWS = 5
COLS = 6
N = ROWS * COLS

MATE = 1000000
INF = 1000000000

_DIRS = [(-1, 0, "U"), (0, 1, "R"), (1, 0, "D"), (0, -1, "L")]

NEI = [[] for _ in range(N)]
ADJ = [0 for _ in range(N)]

for r in range(ROWS):
    for c in range(COLS):
        i = r * COLS + c
        for dr, dc, ch in _DIRS:
            rr, cc = r + dr, c + dc
            if 0 <= rr < ROWS and 0 <= cc < COLS:
                j = rr * COLS + cc
                NEI[i].append((j, ch))
                ADJ[i] |= 1 << j


def _bits(board):
    bits = 0
    try:
        if len(board) == ROWS:
            for r in range(ROWS):
                row = board[r]
                base = r * COLS
                for c in range(COLS):
                    if row[c]:
                        bits |= 1 << (base + c)
        else:
            for i in range(min(N, len(board))):
                if board[i]:
                    bits |= 1 << i
    except Exception:
        try:
            flat = board.flat
            for i in range(N):
                if flat[i]:
                    bits |= 1 << i
        except Exception:
            pass
    return bits


def _generate_moves(my, opp):
    moves = []
    b = my
    while b:
        lsb = b & -b
        src = lsb.bit_length() - 1
        targets = ADJ[src] & opp
        if targets:
            for dst, ch in NEI[src]:
                if targets & (1 << dst):
                    moves.append((src, dst, ch))
        b -= lsb
    return moves


def _edge_count(my, opp):
    total = 0
    b = my
    while b:
        lsb = b & -b
        src = lsb.bit_length() - 1
        total += (ADJ[src] & opp).bit_count()
        b -= lsb
    return total


def _active_count(my, opp):
    total = 0
    b = my
    while b:
        lsb = b & -b
        src = lsb.bit_length() - 1
        if ADJ[src] & opp:
            total += 1
        b -= lsb
    return total


def _apply(my, opp, move):
    src, dst, _ = move
    sm = 1 << src
    dm = 1 << dst

    next_my = opp & ~dm
    next_opp = (my & ~sm) | dm
    return next_my, next_opp


def _move_string(move):
    src, dst, ch = move
    return f"{src // COLS},{src % COLS},{ch}"


def _static_move_score(my, opp, move):
    src, dst, _ = move
    child_my, child_opp = _apply(my, opp, move)
    replies = _edge_count(child_my, child_opp)

    if replies == 0:
        return 100000

    captured_degree = (ADJ[dst] & my).bit_count()
    moved_degree_after = (ADJ[dst] & child_my).bit_count()

    return -100 * replies + 8 * captured_degree - 3 * moved_degree_after


def _order_moves(my, opp, moves, tt_best=None, history=None):
    if history is None:
        history = {}

    def key(m):
        src, dst, _ = m
        score = _static_move_score(my, opp, m)
        if tt_best is not None and tt_best == (src, dst):
            score += 1000000
        score += history.get((src, dst), 0)
        return score

    return sorted(moves, key=key, reverse=True)


def _evaluate(my, opp):
    moves = _generate_moves(my, opp)
    if not moves:
        return -MATE

    best_reply = 999
    reply_sum = 0
    winning_moves = 0

    for m in moves:
        cm, co = _apply(my, opp, m)
        e = _edge_count(cm, co)
        reply_sum += e
        if e < best_reply:
            best_reply = e
        if e == 0:
            winning_moves += 1

    opp_moves = _generate_moves(opp, my)
    opp_best_reply = 999
    opp_reply_sum = 0
    opp_winning_moves = 0

    for m in opp_moves:
        cm, co = _apply(opp, my, m)
        e = _edge_count(cm, co)
        opp_reply_sum += e
        if e < opp_best_reply:
            opp_best_reply = e
        if e == 0:
            opp_winning_moves += 1

    my_active = _active_count(my, opp)
    opp_active = _active_count(opp, my)

    my_avg = reply_sum / max(1, len(moves))
    opp_avg = opp_reply_sum / max(1, len(opp_moves))

    score = 0
    score += 500 * (winning_moves - opp_winning_moves)
    score += 35 * (opp_best_reply - best_reply)
    score += 8 * int(opp_avg - my_avg)
    score += 5 * (opp_active - my_active)

    return int(score)


def policy(you: list[int], opponent: list[int]) -> str:
    try:
        my = _bits(you)
        opp = _bits(opponent)

        root_moves = _generate_moves(my, opp)

        if not root_moves:
            return "0,0,U"

        history = {}
        root_moves = _order_moves(my, opp, root_moves, None, history)
        best_move = root_moves[0]

        for m in root_moves:
            cm, co = _apply(my, opp, m)
            if _edge_count(cm, co) == 0:
                return _move_string(m)

        deadline = time.perf_counter() + 0.92
        tt = {}
        nodes = 0

        def negamax(a_my, a_opp, depth, alpha, beta, ply):
            nonlocal nodes

            nodes += 1
            if (nodes & 1023) == 0 and time.perf_counter() > deadline:
                raise TimeoutError

            key = (a_my, a_opp)
            alpha_orig = alpha

            entry = tt.get(key)
            tt_best = None
            if entry is not None:
                e_depth, e_val, e_flag, e_best = entry
                tt_best = e_best
                if e_depth >= depth:
                    if e_flag == 0:
                        return e_val
                    elif e_flag == 1:
                        if e_val > alpha:
                            alpha = e_val
                    else:
                        if e_val < beta:
                            beta = e_val
                    if alpha >= beta:
                        return e_val

            moves = _generate_moves(a_my, a_opp)
            if not moves:
                return -MATE + ply

            if depth <= 0:
                return _evaluate(a_my, a_opp)

            moves = _order_moves(a_my, a_opp, moves, tt_best, history)

            best_val = -INF
            best_pair = None

            for m in moves:
                cm, co = _apply(a_my, a_opp, m)
                val = -negamax(cm, co, depth - 1, -beta, -alpha, ply + 1)

                if val > best_val:
                    best_val = val
                    best_pair = (m[0], m[1])

                if val > alpha:
                    alpha = val

                if alpha >= beta:
                    history[(m[0], m[1])] = history.get((m[0], m[1]), 0) + depth * depth
                    break

            if best_val <= alpha_orig:
                flag = 2
            elif best_val >= beta:
                flag = 1
            else:
                flag = 0

            tt[key] = (depth, best_val, flag, best_pair)
            return best_val

        max_depth = 30

        for depth in range(1, max_depth + 1):
            if time.perf_counter() > deadline:
                break

            try:
                ordered = _order_moves(my, opp, root_moves, (best_move[0], best_move[1]), history)

                alpha = -INF
                beta = INF
                depth_best = best_move
                depth_score = -INF

                for m in ordered:
                    if time.perf_counter() > deadline:
                        raise TimeoutError

                    cm, co = _apply(my, opp, m)
                    score = -negamax(cm, co, depth - 1, -beta, -alpha, 1)

                    if score > depth_score:
                        depth_score = score
                        depth_best = m

                    if score > alpha:
                        alpha = score

                best_move = depth_best

                if depth_score >= MATE - 1000:
                    break

            except TimeoutError:
                break

        return _move_string(best_move)

    except Exception:
        try:
            my = _bits(you)
            opp = _bits(opponent)
            moves = _generate_moves(my, opp)
            if moves:
                return _move_string(moves[0])
        except Exception:
            pass

        return "0,0,U"
