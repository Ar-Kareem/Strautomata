
import time
from typing import List, Tuple

ROWS = 5
COLS = 6
DIRS = [(-1, 0, 'U'), (0, 1, 'R'), (1, 0, 'D'), (0, -1, 'L')]
INF = 10**9

def _bits_from_grid(grid: List[List[int]]) -> int:
    b = 0
    for r in range(ROWS):
        row = grid[r]
        for c in range(COLS):
            if row[c]:
                b |= 1 << (r * COLS + c)
    return b

def _rc_to_bit(r: int, c: int) -> int:
    return 1 << (r * COLS + c)

def _popcount(x: int) -> int:
    return x.bit_count()

def _iter_bits(x: int):
    while x:
        lsb = x & -x
        idx = lsb.bit_length() - 1
        yield idx
        x ^= lsb

def _generate_moves(you_bits: int, opp_bits: int) -> List[Tuple[int, int, str]]:
    moves = []
    y = you_bits
    while y:
        lsb = y & -y
        idx = lsb.bit_length() - 1
        y ^= lsb
        r, c = divmod(idx, COLS)
        if r > 0 and (opp_bits & _rc_to_bit(r - 1, c)):
            moves.append((r, c, 'U'))
        if c + 1 < COLS and (opp_bits & _rc_to_bit(r, c + 1)):
            moves.append((r, c, 'R'))
        if r + 1 < ROWS and (opp_bits & _rc_to_bit(r + 1, c)):
            moves.append((r, c, 'D'))
        if c > 0 and (opp_bits & _rc_to_bit(r, c - 1)):
            moves.append((r, c, 'L'))
    return moves

def _apply_move(you_bits: int, opp_bits: int, move: Tuple[int, int, str]) -> Tuple[int, int]:
    r, c, d = move
    src = _rc_to_bit(r, c)
    if d == 'U':
        nr, nc = r - 1, c
    elif d == 'R':
        nr, nc = r, c + 1
    elif d == 'D':
        nr, nc = r + 1, c
    else:
        nr, nc = r, c - 1
    dst = _rc_to_bit(nr, nc)
    new_you = (you_bits ^ src) | dst
    new_opp = opp_bits ^ dst
    return new_you, new_opp

def _adjacent_enemy_count(r: int, c: int, opp_bits: int) -> int:
    cnt = 0
    if r > 0 and (opp_bits & _rc_to_bit(r - 1, c)):
        cnt += 1
    if c + 1 < COLS and (opp_bits & _rc_to_bit(r, c + 1)):
        cnt += 1
    if r + 1 < ROWS and (opp_bits & _rc_to_bit(r + 1, c)):
        cnt += 1
    if c > 0 and (opp_bits & _rc_to_bit(r, c - 1)):
        cnt += 1
    return cnt

def _evaluate(you_bits: int, opp_bits: int) -> int:
    my_moves = _generate_moves(you_bits, opp_bits)
    if not my_moves:
        return -100000
    opp_moves = _generate_moves(opp_bits, you_bits)
    if not opp_moves:
        return 100000

    score = 0
    score += 120 * (len(my_moves) - len(opp_moves))
    score += 8 * (_popcount(you_bits) - _popcount(opp_bits))

    my_threat = 0
    for idx in _iter_bits(you_bits):
        r, c = divmod(idx, COLS)
        my_threat += _adjacent_enemy_count(r, c, opp_bits)

    opp_threat = 0
    for idx in _iter_bits(opp_bits):
        r, c = divmod(idx, COLS)
        opp_threat += _adjacent_enemy_count(r, c, you_bits)

    score += 10 * (my_threat - opp_threat)

    center_bonus = 0
    for idx in _iter_bits(you_bits):
        r, c = divmod(idx, COLS)
        center_bonus -= abs(r - 2)
        center_bonus -= abs(c - 2.5)
    for idx in _iter_bits(opp_bits):
        r, c = divmod(idx, COLS)
        center_bonus += abs(r - 2)
        center_bonus += abs(c - 2.5)
    score += int(center_bonus * 2)

    return score

def _move_order_key(you_bits: int, opp_bits: int, move: Tuple[int, int, str]):
    new_you, new_opp = _apply_move(you_bits, opp_bits, move)
    opp_moves = _generate_moves(new_opp, new_you)
    if not opp_moves:
        return (10**9, 0, 0)

    my_next = _generate_moves(new_you, new_opp)
    r, c, d = move
    if d == 'U':
        nr, nc = r - 1, c
    elif d == 'R':
        nr, nc = r, c + 1
    elif d == 'D':
        nr, nc = r + 1, c
    else:
        nr, nc = r, c - 1
    center = -(abs(nr - 2) + abs(nc - 2.5))
    return (-len(opp_moves), len(my_next), center)

def _alphabeta(you_bits: int, opp_bits: int, depth: int, alpha: int, beta: int,
               start: float, limit: float, tt: dict) -> int:
    if time.perf_counter() - start > limit:
        raise TimeoutError

    key = (you_bits, opp_bits, depth)
    if key in tt:
        return tt[key]

    moves = _generate_moves(you_bits, opp_bits)
    if not moves:
        return -100000 - depth
    if depth == 0:
        val = _evaluate(you_bits, opp_bits)
        tt[key] = val
        return val

    moves.sort(key=lambda m: _move_order_key(you_bits, opp_bits, m), reverse=True)

    best = -INF
    for mv in moves:
        new_you, new_opp = _apply_move(you_bits, opp_bits, mv)
        val = -_alphabeta(new_opp, new_you, depth - 1, -beta, -alpha, start, limit, tt)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    tt[key] = best
    return best

def policy(you: list[int], opponent: list[int]) -> str:
    you_bits = _bits_from_grid(you)
    opp_bits = _bits_from_grid(opponent)

    legal = _generate_moves(you_bits, opp_bits)
    if not legal:
        # No legal move should normally not be queried in a valid game state,
        # but return a syntactically valid fallback.
        return "0,0,U"

    start = time.perf_counter()
    limit = 0.92

    legal.sort(key=lambda m: _move_order_key(you_bits, opp_bits, m), reverse=True)
    best_move = legal[0]

    # Immediate tactical checks
    for mv in legal:
        new_you, new_opp = _apply_move(you_bits, opp_bits, mv)
        if not _generate_moves(new_opp, new_you):
            return f"{mv[0]},{mv[1]},{mv[2]}"

    tt = {}
    try:
        depth = 1
        while depth <= 12:
            if time.perf_counter() - start > limit:
                break

            current_best = None
            current_best_val = -INF

            ordered = legal if depth == 1 else sorted(
                legal,
                key=lambda m: _move_order_key(you_bits, opp_bits, m),
                reverse=True
            )

            alpha = -INF
            beta = INF

            for mv in ordered:
                if time.perf_counter() - start > limit:
                    raise TimeoutError
                new_you, new_opp = _apply_move(you_bits, opp_bits, mv)
                val = -_alphabeta(new_opp, new_you, depth - 1, -beta, -alpha, start, limit, tt)
                if val > current_best_val:
                    current_best_val = val
                    current_best = mv
                if val > alpha:
                    alpha = val

            if current_best is not None:
                best_move = current_best
                legal.sort(
                    key=lambda m: 1 if m == best_move else 0,
                    reverse=True
                )
            depth += 1

    except TimeoutError:
        pass
    except Exception:
        # Safety: always return a legal move.
        pass

    return f"{best_move[0]},{best_move[1]},{best_move[2]}"
