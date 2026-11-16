
import time

TIME_BUDGET = 0.70

class _Timeout(Exception):
    pass

_nodes = 0

def _make_move(board, player, idx):
    b = board[:]
    pit = player * 7 + idx
    seeds = b[pit]
    b[pit] = 0
    skip = 13 if player == 0 else 6
    my_store = 6 if player == 0 else 13
    pos = pit
    if seeds >= 13:
        laps = seeds // 13
        seeds -= laps * 13
        for p in range(14):
            if p != skip:
                b[p] += laps
    while seeds > 0:
        pos += 1
        if pos == 14:
            pos = 0
        if pos == skip:
            continue
        b[pos] += 1
        seeds -= 1
    extra = False
    if pos == my_store:
        extra = True
    else:
        lo = player * 7
        if lo <= pos < lo + 6 and b[pos] == 1:
            opp = 12 - pos
            if b[opp] > 0:
                b[my_store] += b[opp] + 1
                b[opp] = 0
                b[pos] = 0
    s0 = b[0] + b[1] + b[2] + b[3] + b[4] + b[5]
    s1 = b[7] + b[8] + b[9] + b[10] + b[11] + b[12]
    if s0 == 0 or s1 == 0:
        b[6] += s0
        b[13] += s1
        for i in range(6):
            b[i] = 0
            b[7 + i] = 0
        return b, False, True
    return b, extra, False

def _evaluate(board, terminal):
    diff = board[6] - board[13]
    if terminal:
        if diff > 0:
            return 100000 + diff * 100
        elif diff < 0:
            return -100000 + diff * 100
        return 0
    if board[6] > 24:
        return 50000 + diff * 100
    if board[13] > 24:
        return -50000 + diff * 100
    score = diff * 100
    s0 = board[0] + board[1] + board[2] + board[3] + board[4] + board[5]
    s1 = board[7] + board[8] + board[9] + board[10] + board[11] + board[12]
    score += (s0 - s1) * 4
    # extra-move opportunities
    for i in range(6):
        v = board[i]
        if v > 0 and v % 13 == 6 - i:
            score += 12
        w = board[7 + i]
        if w > 0 and w % 13 == 6 - i:
            score -= 12
    return score

def _ordered_moves(board, player):
    lo = player * 7
    moves = []
    for i in range(6):
        s = board[lo + i]
        if s > 0:
            pri = 0
            if s % 13 == 6 - i:
                pri = 3
            else:
                # simple capture detection (no laps)
                if s < 13:
                    end = lo + i + s
                    # positions pass store and opponent side
                    if s <= 5 - i:
                        end_pit = lo + i + s
                        if board[end_pit] == 0 and board[12 - end_pit] > 0:
                            pri = 2
                    else:
                        # lands on own side after wrapping: 13 positions per lap
                        rel = (i + s) % 13  # 0..12 relative index counting own 6, store, opp 6
                        if rel < 6 and rel != i:
                            end_pit = lo + rel
                            if board[end_pit] == 0 and board[12 - end_pit] > 0:
                                pri = 2
            moves.append((pri, s, i))
    moves.sort(key=lambda m: (-m[0], -m[1]))
    return [m[2] for m in moves]

def _search(board, player, depth, alpha, beta, deadline):
    global _nodes
    _nodes += 1
    if (_nodes & 2047) == 0 and time.perf_counter() > deadline:
        raise _Timeout()
    if depth <= 0:
        return _evaluate(board, False)
    moves = _ordered_moves(board, player)
    if not moves:
        # should not occur (handled by sweep), but be safe
        return _evaluate(board, True)
    if player == 0:
        best = -10**9
        for m in moves:
            nb, extra, term = _make_move(board, player, m)
            if term:
                val = _evaluate(nb, True)
            elif extra:
                val = _search(nb, 0, depth - 1, alpha, beta, deadline)
            else:
                val = _search(nb, 1, depth - 1, alpha, beta, deadline)
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        return best
    else:
        best = 10**9
        for m in moves:
            nb, extra, term = _make_move(board, player, m)
            if term:
                val = _evaluate(nb, True)
            elif extra:
                val = _search(nb, 1, depth - 1, alpha, beta, deadline)
            else:
                val = _search(nb, 0, depth - 1, alpha, beta, deadline)
            if val < best:
                best = val
            if best < beta:
                beta = best
            if alpha >= beta:
                break
        return best

def policy(you, opponent):
    start = time.perf_counter()
    deadline = start + TIME_BUDGET
    board = list(you[:7]) + list(opponent[:7])
    legal = [i for i in range(6) if board[i] > 0]
    if not legal:
        return 0
    if len(legal) == 1:
        return legal[0]
    # Immediate extra move heuristic as fallback ordering
    root_moves = _ordered_moves(board, 0)
    best_move = root_moves[0]
    try:
        depth = 1
        while depth <= 40:
            alpha = -10**9
            beta = 10**9
            cur_best = None
            cur_val = -10**9
            for m in root_moves:
                nb, extra, term = _make_move(board, 0, m)
                if term:
                    val = _evaluate(nb, True)
                elif extra:
                    val = _search(nb, 0, depth - 1, alpha, beta, deadline)
                else:
                    val = _search(nb, 1, depth - 1, alpha, beta, deadline)
                if val > cur_val:
                    cur_val = val
                    cur_best = m
                if val > alpha:
                    alpha = val
            if cur_best is not None:
                best_move = cur_best
                # move best to front for next iteration
                root_moves.remove(cur_best)
                root_moves.insert(0, cur_best)
            if cur_val > 90000 or cur_val < -90000:
                break
            depth += 1
            if time.perf_counter() > deadline:
                break
    except _Timeout:
        pass
    except Exception:
        pass
    if board[best_move] <= 0:
        best_move = legal[0]
    return best_move
