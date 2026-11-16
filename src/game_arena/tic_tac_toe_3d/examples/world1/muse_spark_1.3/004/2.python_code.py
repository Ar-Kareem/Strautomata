
import time

FULL = (1 << 27) - 1
INF = 10 ** 9
WIN_VAL = 1000000

try:
    (1).bit_count()
    def _popcnt(x):
        return x.bit_count()
except AttributeError:
    def _popcnt(x):
        return bin(x).count("1")

def _gen_lines():
    dirs = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dx == 0 and dy == 0 and dz == 0:
                    continue
                # canonical: first non-zero positive to avoid opposite duplicate
                if dx != 0:
                    if dx < 0:
                        continue
                elif dy != 0:
                    if dy < 0:
                        continue
                else:
                    if dz < 0:
                        continue
                dirs.append((dx, dy, dz))
    lines = []
    for dx, dy, dz in dirs:
        for x0 in range(3):
            for y0 in range(3):
                for z0 in range(3):
                    x2 = x0 + 2 * dx
                    y2 = y0 + 2 * dy
                    z2 = z0 + 2 * dz
                    if 0 <= x2 < 3 and 0 <= y2 < 3 and 0 <= z2 < 3:
                        cells = []
                        for t in range(3):
                            x = x0 + t * dx
                            y = y0 + t * dy
                            z = z0 + t * dz
                            idx = x * 9 + y * 3 + z
                            cells.append(idx)
                        lines.append(tuple(cells))
    # deduplicate (should already be unique)
    uniq = []
    seen = set()
    for c in lines:
        s = frozenset(c)
        if s not in seen:
            seen.add(s)
            uniq.append(c)
    return uniq

_LINES = _gen_lines()
WIN_MASKS = []
for cells in _LINES:
    m = 0
    for c in cells:
        m |= 1 << c
    WIN_MASKS.append(m)

LINES_THROUGH = [[] for _ in range(27)]
CELL_WEIGHT = [0] * 27
for li, cells in enumerate(_LINES):
    for c in cells:
        LINES_THROUGH[c].append(li)
        CELL_WEIGHT[c] += 1

SORTED_CELLS = sorted(range(27), key=lambda c: CELL_WEIGHT[c], reverse=True)

def _evaluate(my_mask, opp_mask):
    s = 0
    for w in WIN_MASKS:
        m = w & my_mask
        if m:
            if w & opp_mask:
                continue
            c = _popcnt(m)
            if c == 1:
                s += 1
            elif c == 2:
                s += 100
            else:
                s += 100000
        else:
            o = w & opp_mask
            if o:
                c = _popcnt(o)
                if c == 1:
                    s -= 1
                elif c == 2:
                    s -= 100
                else:
                    s -= 100000
    return s

def _find_win_idx(my_mask, opp_mask):
    for w in WIN_MASKS:
        if w & opp_mask:
            continue
        m = w & my_mask
        if m and _popcnt(m) == 2:
            empty = w ^ m
            # empty is single bit
            idx = empty.bit_length() - 1
            return idx
    return None

class _Timeout(Exception):
    pass

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    try:
        t0 = time.perf_counter()
        deadline = t0 + 0.90

        # collect empties and masks
        my_mask = 0
        opp_mask = 0
        empties = []
        # also keep flat for fallback
        for i in range(3):
            Bi = board[i]
            for j in range(3):
                Bj = Bi[j]
                for k in range(3):
                    v = Bj[k]
                    idx = i * 9 + j * 3 + k
                    if v == 1:
                        my_mask |= 1 << idx
                    elif v == -1:
                        opp_mask |= 1 << idx
                    else:
                        empties.append(idx)
        if not empties:
            return (0, 0, 0)

        if len(empties) == 27:
            return (1, 1, 1)

        # immediate win
        widx = _find_win_idx(my_mask, opp_mask)
        if widx is not None:
            return (widx // 9, (widx % 9) // 3, widx % 3)
        # immediate block
        bidx = _find_win_idx(opp_mask, my_mask)
        if bidx is not None:
            return (bidx // 9, (bidx % 9) // 3, bidx % 3)

        empty_mask = FULL & ~(my_mask | opp_mask)
        # root moves in static best order
        root_moves = [c for c in SORTED_CELLS if (empty_mask >> c) & 1]
        if not root_moves:
            e = empties[0]
            return (e // 9, (e % 9) // 3, e % 3)
        best_move = root_moves[0]

        n_empty = len(root_moves)
        if n_empty > 20:
            max_depth = 3
        elif n_empty > 14:
            max_depth = 4
        elif n_empty > 10:
            max_depth = 5
        elif n_empty > 7:
            max_depth = 7
        else:
            max_depth = n_empty

        # local bindings for speed
        _WIN_MASKS = WIN_MASKS
        _LINES_TH = LINES_THROUGH
        _SORTED = SORTED_CELLS
        _EVAL = _evaluate
        nodes = [0]

        def negamax(my_m, opp_m, depth, alpha, beta, ply, last_mv):
            nodes[0] += 1
            if (nodes[0] & 1023) == 0:
                if time.perf_counter() > deadline:
                    raise _Timeout()
            if last_mv != -1:
                # did opp (who just moved) win through last_mv ?
                for li in _LINES_TH[last_mv]:
                    w = _WIN_MASKS[li]
                    if (w & opp_m) == w:
                        return -WIN_VAL + ply
            if depth == 0:
                return _EVAL(my_m, opp_m)
            em = FULL & ~(my_m | opp_m)
            if em == 0:
                return 0
            best = -INF
            # iterate in static order
            for mv in _SORTED:
                if ((em >> mv) & 1) == 0:
                    continue
                bit = 1 << mv
                # swap: opponent becomes new my
                sc = -negamax(opp_m, my_m | bit, depth - 1, -beta, -alpha, ply + 1, mv)
                if sc > best:
                    best = sc
                    if best > alpha:
                        alpha = best
                    if alpha >= beta:
                        break
            return best

        # iterative deepening
        # scores for ordering
        try:
            # order dict for next iteration
            for depth in range(2, max_depth + 1):
                if time.perf_counter() > deadline - 0.05:
                    break
                alpha = -INF
                beta = INF
                cur_best = best_move
                cur_best_score = -INF
                scored = []
                for mv in root_moves:
                    if time.perf_counter() > deadline - 0.02:
                        raise _Timeout()
                    bit = 1 << mv
                    # root move: we play mv, then opponent to move
                    # call negamax with swapped perspective
                    sc = -negamax(opp_mask, my_mask | bit, depth - 1, -beta, -alpha, 1, mv)
                    scored.append((sc, mv))
                    if sc > cur_best_score:
                        cur_best_score = sc
                        cur_best = mv
                    if sc > alpha:
                        alpha = sc
                    # early win break
                    if cur_best_score >= WIN_VAL - 30:
                        break
                # sort for next depth: best first
                scored.sort(key=lambda x: x[0], reverse=True)
                root_moves = [mv for _, mv in scored]
                best_move = cur_best
                # if forced win found, stop
                if cur_best_score >= WIN_VAL - 30:
                    break
                # if forced loss avoided? continue deeper
        except _Timeout:
            pass

        return (best_move // 9, (best_move % 9) // 3, best_move % 3)
    except Exception:
        try:
            for i in range(3):
                for j in range(3):
                    for k in range(3):
                        if board[i][j][k] == 0:
                            return (i, j, k)
        except Exception:
            pass
        return (0, 0, 0)
