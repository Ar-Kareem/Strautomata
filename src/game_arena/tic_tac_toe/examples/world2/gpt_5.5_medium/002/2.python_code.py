
import time

WIN = 1_000_000
INF = 10_000_000

_LINES = (
    (0, 1, 2, 3),
    (4, 5, 6, 7),
    (8, 9, 10, 11),
    (12, 13, 14, 15),
    (0, 4, 8, 12),
    (1, 5, 9, 13),
    (2, 6, 10, 14),
    (3, 7, 11, 15),
    (0, 5, 10, 15),
    (3, 6, 9, 12),
)

_CELL_LINES = tuple(
    tuple(line for line in _LINES if i in line) for i in range(16)
)

_POS = (
    6, 3, 3, 6,
    3, 8, 8, 3,
    3, 8, 8, 3,
    6, 3, 3, 6,
)

_ATTACK_W = (0, 4, 30, 650, 100000)
_BLOCK_W = (0, 3, 25, 600, 90000)
_EVAL_W = (0, 6, 70, 1400, 0)

_TT = {}
_DEADLINE = 0.0
_NODES = 0


class _Timeout(Exception):
    pass


def _has_win(flat, p):
    for line in _LINES:
        if (
            flat[line[0]] == p and
            flat[line[1]] == p and
            flat[line[2]] == p and
            flat[line[3]] == p
        ):
            return True
    return False


def _terminal_score(flat, empties):
    if _has_win(flat, 1):
        return WIN + empties
    if _has_win(flat, -1):
        return -WIN - empties
    if empties == 0:
        return 0
    return None


def _immediate_wins(flat, p):
    wins = set()
    for line in _LINES:
        count = 0
        zero = -1
        blocked = False
        for i in line:
            v = flat[i]
            if v == p:
                count += 1
            elif v == 0:
                zero = i
            else:
                blocked = True
                break
        if not blocked and count == 3 and zero != -1:
            wins.add(zero)
    return wins


def _ordered_moves(flat, p, moves):
    scored = []
    opp = -p

    for idx in moves:
        score = _POS[idx]

        for line in _CELL_LINES[idx]:
            cp = 0
            co = 0
            for j in line:
                v = flat[j]
                if v == p:
                    cp += 1
                elif v == opp:
                    co += 1

            if co == 0:
                score += _ATTACK_W[cp + 1]
            if cp == 0:
                score += _BLOCK_W[co]

        scored.append((score, idx))

    scored.sort(reverse=True)
    return [idx for _, idx in scored]


def _evaluate(flat, to_move):
    term = _terminal_score(flat, flat.count(0))
    if term is not None:
        return term

    score = 0

    for i, v in enumerate(flat):
        if v == 1:
            score += _POS[i]
        elif v == -1:
            score -= _POS[i]

    for line in _LINES:
        c1 = 0
        c2 = 0
        for i in line:
            if flat[i] == 1:
                c1 += 1
            elif flat[i] == -1:
                c2 += 1

        if c2 == 0:
            score += _EVAL_W[c1]
        elif c1 == 0:
            score -= _EVAL_W[c2]

    my_threats = len(_immediate_wins(flat, 1))
    op_threats = len(_immediate_wins(flat, -1))

    score += 1800 * my_threats
    score -= 1900 * op_threats

    if to_move == 1 and my_threats:
        score += 4500
    if to_move == -1 and op_threats:
        score -= 4500

    return score


def _check_time():
    global _NODES
    _NODES += 1
    if (_NODES & 1023) == 0 and time.perf_counter() > _DEADLINE:
        raise _Timeout()


def _search(flat, p, depth, alpha, beta, empties):
    _check_time()

    term = _terminal_score(flat, empties)
    if term is not None:
        return term

    if depth <= 0:
        return _evaluate(flat, p)

    key = (tuple(flat), p, depth)
    cached = _TT.get(key)
    if cached is not None:
        return cached

    moves = [i for i, v in enumerate(flat) if v == 0]
    moves = _ordered_moves(flat, p, moves)

    cut = False

    if p == 1:
        best = -INF
        for m in moves:
            flat[m] = 1
            val = _search(flat, -1, depth - 1, alpha, beta, empties - 1)
            flat[m] = 0

            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                cut = True
                break
    else:
        best = INF
        for m in moves:
            flat[m] = -1
            val = _search(flat, 1, depth - 1, alpha, beta, empties - 1)
            flat[m] = 0

            if val < best:
                best = val
            if best < beta:
                beta = best
            if alpha >= beta:
                cut = True
                break

    if not cut:
        _TT[key] = best

    return best


def _root_search(flat, depth, fallback):
    legal = [i for i, v in enumerate(flat) if v == 0]
    moves = _ordered_moves(flat, 1, legal)

    if fallback in moves:
        moves.remove(fallback)
        moves.insert(0, fallback)

    best_move = moves[0]
    best_val = -INF
    alpha = -INF
    beta = INF
    empties = len(legal)

    for m in moves:
        if time.perf_counter() > _DEADLINE:
            raise _Timeout()

        flat[m] = 1
        val = _search(flat, -1, depth - 1, alpha, beta, empties - 1)
        flat[m] = 0

        if val > best_val:
            best_val = val
            best_move = m

        if best_val > alpha:
            alpha = best_val

    return best_val, best_move


def _best_from(flat, cells, p=1):
    cells = [c for c in cells if flat[c] == 0]
    if not cells:
        return None
    return _ordered_moves(flat, p, cells)[0]


def _find_fork(flat, p, legal):
    best = None
    best_score = -INF

    for m in legal:
        flat[m] = p
        threat_count = len(_immediate_wins(flat, p))
        flat[m] = 0

        if threat_count >= 2:
            s = threat_count * 1000 + _POS[m]
            if s > best_score:
                best_score = s
                best = m

    return best


def policy(board: list[list[int]]) -> tuple[int, int]:
    global _DEADLINE, _NODES, _TT

    start = time.perf_counter()
    _DEADLINE = start + 0.88
    _NODES = 0

    if len(_TT) > 500000:
        _TT.clear()

    flat = []
    for r in range(4):
        for c in range(4):
            flat.append(int(board[r][c]))

    legal = [i for i, v in enumerate(flat) if v == 0]

    if not legal:
        return (0, 0)

    # Strong opening choice.
    if len(legal) == 16:
        return (1, 1)

    # Win immediately if possible.
    my_wins = _immediate_wins(flat, 1)
    if my_wins:
        m = _best_from(flat, my_wins, 1)
        return divmod(m, 4)

    # Block opponent's immediate win.
    op_wins = _immediate_wins(flat, -1)
    if op_wins:
        m = _best_from(flat, op_wins, 1)
        return divmod(m, 4)

    # Create an unavoidable double threat.
    fork = _find_fork(flat, 1, legal)
    if fork is not None:
        return divmod(fork, 4)

    ordered = _ordered_moves(flat, 1, legal)
    best_move = ordered[0]

    # If the opponent has exactly one fork square, prefer covering it as fallback.
    op_forks = []
    for m in legal:
        flat[m] = -1
        if len(_immediate_wins(flat, -1)) >= 2:
            op_forks.append(m)
        flat[m] = 0

    if len(op_forks) == 1:
        best_move = op_forks[0]

    empties = len(legal)

    try:
        for depth in range(1, empties + 1):
            val, move = _root_search(flat, depth, best_move)
            best_move = move

            if val >= WIN:
                break

            if time.perf_counter() > _DEADLINE:
                break

    except _Timeout:
        pass
    except Exception:
        pass

    r, c = divmod(best_move, 4)
    if 0 <= r < 4 and 0 <= c < 4 and board[r][c] == 0:
        return (r, c)

    # Absolute safety fallback.
    for i in legal:
        r, c = divmod(i, 4)
        if board[r][c] == 0:
            return (r, c)

    return (0, 0)
