
from __future__ import annotations

from functools import lru_cache
import time

_N = 4
_CELLS = _N * _N
_FULL_MASK = (1 << _CELLS) - 1

_WIN_SCORE = 1_000_000
_INF = 1_000_000_000
_EVAL_LIMIT = _WIN_SCORE // 2

_TIME_LIMIT = 0.82
_CHECK_MASK = 1023

_LINE_WEIGHTS = (0, 18, 180, 3500, 0)
_ADVANCE_WEIGHTS = (0, 25, 230, 4500, 100000)
_BLOCK_WEIGHTS = (0, 22, 210, 4200, 0)


def _make_win_masks() -> tuple[int, ...]:
    masks = []

    for r in range(_N):
        m = 0
        for c in range(_N):
            m |= 1 << (r * _N + c)
        masks.append(m)

    for c in range(_N):
        m = 0
        for r in range(_N):
            m |= 1 << (r * _N + c)
        masks.append(m)

    m = 0
    for i in range(_N):
        m |= 1 << (i * _N + i)
    masks.append(m)

    m = 0
    for i in range(_N):
        m |= 1 << (i * _N + (_N - 1 - i))
    masks.append(m)

    return tuple(masks)


_WIN_MASKS = _make_win_masks()
_CELL_LINES = tuple(
    tuple(w for w in _WIN_MASKS if w & (1 << i)) for i in range(_CELLS)
)

_cell_values = []
for i in range(_CELLS):
    r, c = divmod(i, _N)
    v = 30 * len(_CELL_LINES[i])
    if r in (1, 2) and c in (1, 2):
        v += 8
    _cell_values.append(v)
_CELL_VALUE = tuple(_cell_values)

_INDEX_TO_MOVE = tuple((i // _N, i % _N) for i in range(_CELLS))

_IS_WIN = [False] * (1 << _CELLS)
for _mask in range(1 << _CELLS):
    for _w in _WIN_MASKS:
        if (_mask & _w) == _w:
            _IS_WIN[_mask] = True
            break

_POS_SCORE = [0] * (1 << _CELLS)
for _mask in range(1, 1 << _CELLS):
    _lsb = _mask & -_mask
    _POS_SCORE[_mask] = _POS_SCORE[_mask ^ _lsb] + _CELL_VALUE[
        _lsb.bit_length() - 1
    ]

del _cell_values


@lru_cache(maxsize=131072)
def _winning_moves(p: int, o: int) -> int:
    """Empty cells where player p wins immediately."""
    empty = _FULL_MASK & ~(p | o)
    result = 0
    for w in _WIN_MASKS:
        if w & o:
            continue
        missing = w & empty
        if missing and (missing & (missing - 1)) == 0:
            result |= missing
    return result


@lru_cache(maxsize=65536)
def _fork_moves(p: int, o: int) -> int:
    """Moves that create at least two distinct immediate winning threats."""
    if p.bit_count() < 4:
        return 0

    legal = _FULL_MASK & ~(p | o)
    forks = 0

    while legal:
        b = legal & -legal
        legal ^= b
        p2 = p | b

        if _IS_WIN[p2]:
            continue

        if _winning_moves(p2, o).bit_count() >= 2 and _winning_moves(o, p2) == 0:
            forks |= b

    return forks


@lru_cache(maxsize=131072)
def _evaluate(p: int, o: int) -> int:
    """Static score from the current player's perspective."""
    score = _POS_SCORE[p] - _POS_SCORE[o]

    for w in _WIN_MASKS:
        pc = (p & w).bit_count()
        oc = (o & w).bit_count()

        if oc == 0:
            score += _LINE_WEIGHTS[pc]
        elif pc == 0:
            score -= _LINE_WEIGHTS[oc]

    score += 5000 * (
        _winning_moves(p, o).bit_count() - _winning_moves(o, p).bit_count()
    )
    score += 25000 * (_fork_moves(p, o).bit_count() - _fork_moves(o, p).bit_count())

    if score > _EVAL_LIMIT:
        return _EVAL_LIMIT
    if score < -_EVAL_LIMIT:
        return -_EVAL_LIMIT
    return score


def _move_order_score(p: int, o: int, b: int) -> int:
    p2 = p | b
    if _IS_WIN[p2]:
        return 100_000_000

    idx = b.bit_length() - 1
    score = _CELL_VALUE[idx]

    for w in _CELL_LINES[idx]:
        pc = (p & w).bit_count()
        oc = (o & w).bit_count()

        if oc == 0:
            score += _ADVANCE_WEIGHTS[pc + 1]
        if pc == 0:
            score += _BLOCK_WEIGHTS[oc]

    my_threats = _winning_moves(p2, o).bit_count()
    opp_threats = _winning_moves(o, p2).bit_count()

    if my_threats >= 2 and opp_threats == 0:
        score += 200_000 + 20_000 * my_threats
    elif my_threats:
        score += 12_000 * my_threats

    if opp_threats:
        score -= 150_000 * opp_threats

    if my_threats == 0:
        opp_forks = _fork_moves(o, p2).bit_count()
        if opp_forks:
            score -= 40_000 * opp_forks

    return score


def _ordered_moves(p: int, o: int, preferred: int = 0) -> list[int]:
    legal = _FULL_MASK & ~(p | o)
    scored = []

    while legal:
        b = legal & -legal
        legal ^= b
        s = _move_order_score(p, o, b)
        if b == preferred:
            s += 300_000_000
        scored.append((s, b))

    scored.sort(reverse=True)
    return [b for _, b in scored]


def _best_bit_from_mask(p: int, o: int, mask: int) -> int:
    mask &= _FULL_MASK & ~(p | o)
    if not mask:
        return 0

    best = 0
    best_score = -_INF

    while mask:
        b = mask & -mask
        mask ^= b
        s = _move_order_score(p, o, b)
        if s > best_score:
            best_score = s
            best = b

    return best


_TT = {}
_TT_LIMIT = 250_000
_EXACT = 0
_LOWER = 1
_UPPER = 2

_DEADLINE = 0.0
_NODES = 0


class _Timeout(Exception):
    pass


def _negamax(p: int, o: int, depth: int, alpha: int, beta: int) -> int:
    global _NODES

    _NODES += 1
    if (_NODES & _CHECK_MASK) == 0 and time.perf_counter() > _DEADLINE:
        raise _Timeout

    if _IS_WIN[o]:
        return -_WIN_SCORE - depth
    if _IS_WIN[p]:
        return _WIN_SCORE + depth
    if (p | o) == _FULL_MASK:
        return 0

    win_now = _winning_moves(p, o)
    if win_now:
        return _WIN_SCORE + depth - 1

    opp_win = _winning_moves(o, p)
    if opp_win:
        if opp_win & (opp_win - 1):
            return -_WIN_SCORE - depth + 2
    else:
        fork_now = _fork_moves(p, o)
        if fork_now:
            return _WIN_SCORE + depth - 3
        if depth <= 0:
            return _evaluate(p, o)

    use_tt = depth > 0
    tt_move = 0
    alpha_orig = alpha
    beta_orig = beta
    key = 0

    if use_tt:
        key = p | (o << 16) | (depth << 32)
        entry = _TT.get(key)
        if entry is not None:
            val, flag, move = entry
            if flag == _EXACT:
                return val
            if flag == _LOWER:
                if val > alpha:
                    alpha = val
            elif flag == _UPPER:
                if val < beta:
                    beta = val
            if alpha >= beta:
                return val
            tt_move = move

    if opp_win:
        moves = (opp_win,)
    else:
        moves = _ordered_moves(p, o, tt_move)

    best = -_INF
    best_move = 0

    for b in moves:
        val = -_negamax(o, p | b, depth - 1, -beta, -alpha)

        if val > best:
            best = val
            best_move = b
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break

    if best == -_INF:
        best = _evaluate(p, o)

    if use_tt:
        if best <= alpha_orig:
            flag = _UPPER
        elif best >= beta_orig:
            flag = _LOWER
        else:
            flag = _EXACT
        _TT[key] = (best, flag, best_move)

    return best


def _board_to_masks(board) -> tuple[int, int]:
    p = 0
    o = 0

    for r in range(_N):
        for c in range(_N):
            v = board[r][c]
            bit = 1 << (r * _N + c)
            if v == 1:
                p |= bit
            elif v == -1:
                o |= bit

    return p, o


def _bit_to_move(b: int) -> tuple[int, int]:
    if not b:
        return (0, 0)
    return _INDEX_TO_MOVE[b.bit_length() - 1]


def _policy_impl(board) -> tuple[int, int]:
    global _DEADLINE, _NODES

    us, them = _board_to_masks(board)
    legal = _FULL_MASK & ~(us | them)

    if not legal:
        return (0, 0)

    if (legal & (legal - 1)) == 0:
        return _bit_to_move(legal)

    if _IS_WIN[us] or _IS_WIN[them]:
        b = _best_bit_from_mask(us, them, legal) or (legal & -legal)
        return _bit_to_move(b)

    win = _winning_moves(us, them) & legal
    if win:
        b = _best_bit_from_mask(us, them, win) or (win & -win)
        return _bit_to_move(b)

    opp_win = _winning_moves(them, us) & legal
    if opp_win and (opp_win & (opp_win - 1)) == 0:
        return _bit_to_move(opp_win)

    if legal == _FULL_MASK:
        return (1, 1)

    if not opp_win:
        fork = _fork_moves(us, them) & legal
        if fork:
            b = _best_bit_from_mask(us, them, fork) or (fork & -fork)
            return _bit_to_move(b)

    if len(_TT) > _TT_LIMIT:
        _TT.clear()

    ordered = _ordered_moves(us, them, 0)
    best_move = ordered[0] if ordered else (legal & -legal)
    best_score = -_INF

    _DEADLINE = time.perf_counter() + _TIME_LIMIT
    _NODES = 0

    empties = legal.bit_count()

    for depth in range(1, empties + 1):
        try:
            moves = _ordered_moves(us, them, best_move)
            alpha = -_INF
            beta = _INF
            current_best = best_move
            current_score = -_INF

            for b in moves:
                if (_NODES & _CHECK_MASK) == 0 and time.perf_counter() > _DEADLINE:
                    raise _Timeout

                score = -_negamax(them, us | b, depth - 1, -beta, -alpha)

                if score > current_score:
                    current_score = score
                    current_best = b
                if score > alpha:
                    alpha = score

            best_move = current_best
            best_score = current_score

            if best_score > _WIN_SCORE // 2 or best_score < -_WIN_SCORE // 2:
                break

        except _Timeout:
            break

    if not (best_move & legal):
        best_move = legal & -legal

    return _bit_to_move(best_move)


def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Return a legal move as (row, col). 1 is this agent, -1 is the opponent,
    and 0 is empty.
    """
    try:
        r, c = _policy_impl(board)
        r = int(r)
        c = int(c)
        if 0 <= r < _N and 0 <= c < _N and board[r][c] == 0:
            return (r, c)
    except Exception:
        pass

    for r in range(_N):
        for c in range(_N):
            try:
                if board[r][c] == 0:
                    return (r, c)
            except Exception:
                continue

    return (0, 0)
