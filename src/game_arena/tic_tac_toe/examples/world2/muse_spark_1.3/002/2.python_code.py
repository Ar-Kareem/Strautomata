
import time

WIN_LINES = [
    (0, 1, 2, 3), (4, 5, 6, 7), (8, 9, 10, 11), (12, 13, 14, 15),
    (0, 4, 8, 12), (1, 5, 9, 13), (2, 6, 10, 14), (3, 7, 11, 15),
    (0, 5, 10, 15), (3, 6, 9, 12)
]

POS = [2, 1, 1, 2, 1, 5, 5, 1, 1, 5, 5, 1, 2, 1, 1, 2]

NEIGHBORS = []
for _i in range(16):
    _r = _i // 4
    _c = _i % 4
    _lst = []
    for _dr in (-1, 0, 1):
        for _dc in (-1, 0, 1):
            if _dr == 0 and _dc == 0:
                continue
            _nr = _r + _dr
            _nc = _c + _dc
            if 0 <= _nr < 4 and 0 <= _nc < 4:
                _lst.append(_nr * 4 + _nc)
    NEIGHBORS.append(_lst)


def _winner(flat):
    for a, b, c, d in WIN_LINES:
        v = flat[a]
        if v != 0 and v == flat[b] and v == flat[c] and v == flat[d]:
            return v
    return 0


def _eval(flat):
    s = 0
    for a, b, c, d in WIN_LINES:
        n1 = 0
        no = 0
        va = flat[a]
        if va == 1:
            n1 += 1
        elif va == -1:
            no += 1
        vb = flat[b]
        if vb == 1:
            n1 += 1
        elif vb == -1:
            no += 1
        vc = flat[c]
        if vc == 1:
            n1 += 1
        elif vc == -1:
            no += 1
        vd = flat[d]
        if vd == 1:
            n1 += 1
        elif vd == -1:
            no += 1
        if n1 and no:
            continue
        if n1 == 4:
            return 100000
        if no == 4:
            return -100000
        if n1 == 3:
            s += 1000
        elif n1 == 2:
            s += 100
        elif n1 == 1:
            s += 1
        elif no == 3:
            s -= 1000
        elif no == 2:
            s -= 100
        elif no == 1:
            s -= 1
    s += (flat[5] + flat[6] + flat[9] + flat[10]) * 2
    return s


def _ordered(flat, empties):
    scored = []
    for i in empties:
        sc = POS[i]
        cnt = 0
        for nb in NEIGHBORS[i]:
            if flat[nb] != 0:
                cnt += 1
        sc += cnt * 2
        scored.append((sc, i))
    scored.sort(reverse=True)
    return [x[1] for x in scored]


class _TO(Exception):
    pass


def policy(board: list[list[int]]) -> tuple[int, int]:
    try:
        start = time.perf_counter()
        deadline = start + 0.85

        flat = [0] * 16
        for r in range(4):
            row = board[r]
            for c in range(4):
                flat[r * 4 + c] = row[c]

        empties = [i for i, v in enumerate(flat) if v == 0]
        if not empties:
            return (0, 0)
        if len(empties) == 1:
            return (empties[0] // 4, empties[0] % 4)
        if len(empties) == 16:
            return (1, 1)

        # immediate win
        for i in empties:
            flat[i] = 1
            w = False
            for a, b, c, d in WIN_LINES:
                if i != a and i != b and i != c and i != d:
                    continue
                if flat[a] == 1 and flat[b] == 1 and flat[c] == 1 and flat[d] == 1:
                    w = True
                    break
            flat[i] = 0
            if w:
                return (i // 4, i % 4)

        # immediate block (single threat)
        opp = []
        for i in empties:
            flat[i] = -1
            w = False
            for a, b, c, d in WIN_LINES:
                if i != a and i != b and i != c and i != d:
                    continue
                if flat[a] == -1 and flat[b] == -1 and flat[c] == -1 and flat[d] == -1:
                    w = True
                    break
            flat[i] = 0
            if w:
                opp.append(i)
        if len(opp) == 1:
            return (opp[0] // 4, opp[0] % 4)

        ordered = _ordered(flat, empties)
        best_move = ordered[0]
        best_score = -10**9

        n = len(empties)
        if n <= 10:
            max_depth = n
        elif n <= 12:
            max_depth = 6
        elif n <= 13:
            max_depth = 5
        else:
            max_depth = 4

        nodes = 0

        def ab(depth, alpha, beta, maximizing):
            nonlocal nodes
            nodes += 1
            if (nodes & 511) == 0 and time.perf_counter() > deadline:
                raise _TO()
            w = _winner(flat)
            if w != 0:
                if w == 1:
                    return 100000 + depth
                else:
                    return -100000 - depth
            if depth == 0:
                return _eval(flat)
            # generate empties
            em = [i for i, v in enumerate(flat) if v == 0]
            if not em:
                return 0
            om = _ordered(flat, em)
            if maximizing:
                val = -10**9
                for m in om:
                    flat[m] = 1
                    try:
                        sc = ab(depth - 1, alpha, beta, False)
                    except _TO:
                        flat[m] = 0
                        raise
                    flat[m] = 0
                    if sc > val:
                        val = sc
                    if val > alpha:
                        alpha = val
                    if alpha >= beta:
                        break
                return val
            else:
                val = 10**9
                for m in om:
                    flat[m] = -1
                    try:
                        sc = ab(depth - 1, alpha, beta, True)
                    except _TO:
                        flat[m] = 0
                        raise
                    flat[m] = 0
                    if sc < val:
                        val = sc
                    if val < beta:
                        beta = val
                    if alpha >= beta:
                        break
                return val

        # iterative deepening at root
        for depth in range(1, max_depth + 1):
            if time.perf_counter() > deadline:
                break
            alpha = -10**9
            beta = 10**9
            cur_best = best_move
            cur_score = -10**9
            scored_moves = []
            try:
                for m in ordered:
                    if time.perf_counter() > deadline:
                        raise _TO()
                    flat[m] = 1
                    sc = ab(depth - 1, alpha, beta, False)
                    flat[m] = 0
                    scored_moves.append((sc, m))
                    if sc > cur_score:
                        cur_score = sc
                        cur_best = m
                    if sc > alpha:
                        alpha = sc
            except _TO:
                try:
                    flat[m] = 0
                except Exception:
                    pass
                break
            best_move = cur_best
            best_score = cur_score
            scored_moves.sort(reverse=True)
            ordered = [m for _, m in scored_moves]
            # keep unsearched moves if pruned (should not happen often at root without break)
            if len(ordered) < n:
                pass
            if best_score > 90000:
                break

        if flat[best_move] != 0:
            # safety: pick first legal
            for i in empties:
                if flat[i] == 0:
                    # flat may be dirty due to abort, check original board
                    r, c = i // 4, i % 4
                    if board[r][c] == 0:
                        best_move = i
                        break
        r, c = best_move // 4, best_move % 4
        if board[r][c] != 0:
            for rr in range(4):
                for cc in range(4):
                    if board[rr][cc] == 0:
                        return (rr, cc)
        return (r, c)
    except Exception:
        try:
            for rr in range(4):
                for cc in range(4):
                    if board[rr][cc] == 0:
                        return (rr, cc)
        except Exception:
            pass
        return (0, 0)
