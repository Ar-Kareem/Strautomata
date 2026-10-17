
import time

# --- precompute winning lines ---
_DIRS = []
for _dx in (-1, 0, 1):
    for _dy in (-1, 0, 1):
        for _dz in (-1, 0, 1):
            if _dx == 0 and _dy == 0 and _dz == 0:
                continue
            # canonical direction to avoid duplicates
            if _dx > 0:
                pass
            elif _dx == 0 and _dy > 0:
                pass
            elif _dx == 0 and _dy == 0 and _dz > 0:
                pass
            else:
                continue
            _DIRS.append((_dx, _dy, _dz))

WIN_MASKS = []
for _x in range(3):
    for _y in range(3):
        for _z in range(3):
            for _dx, _dy, _dz in _DIRS:
                _px, _py, _pz = _x - _dx, _y - _dy, _z - _dz
                if 0 <= _px < 3 and 0 <= _py < 3 and 0 <= _pz < 3:
                    continue  # not start of line
                _ex, _ey, _ez = _x + 2 * _dx, _y + 2 * _dy, _z + 2 * _dz
                if not (0 <= _ex < 3 and 0 <= _ey < 3 and 0 <= _ez < 3):
                    continue
                _m = 0
                for _t in range(3):
                    _cx, _cy, _cz = _x + _t * _dx, _y + _t * _dy, _z + _t * _dz
                    _idx = _cx * 9 + _cy * 3 + _cz
                    _m |= (1 << _idx)
                WIN_MASKS.append(_m)

LINES_BY_CELL = [[] for _ in range(27)]
for _m in WIN_MASKS:
    for _i in range(27):
        if (_m >> _i) & 1:
            LINES_BY_CELL[_i].append(_m)

CELL_W = [len(LINES_BY_CELL[i]) for i in range(27)]

INF = 100000

try:
    _bc = int.bit_count  # type: ignore
    def _pop(x: int) -> int:
        return x.bit_count()
except Exception:
    def _pop(x: int) -> int:
        return bin(x).count("1")

def _idx_to_coord(idx: int):
    return (idx // 9, (idx % 9) // 3, idx % 3)

class _Timeout(Exception):
    pass

def _evaluate(my: int, opp: int) -> int:
    my1 = 0
    my2 = 0
    opp1 = 0
    opp2 = 0
    for m in WIN_MASKS:
        a = my & m
        if a:
            if opp & m:
                continue
            c = _pop(a)
            if c == 1:
                my1 += 1
            elif c == 2:
                my2 += 1
            else:
                # 3 in a row (should have been caught as win)
                return INF
        else:
            b = opp & m
            if b == 0:
                continue
            c = _pop(b)
            if c == 1:
                opp1 += 1
            elif c == 2:
                opp2 += 1
            else:
                return -INF
    s = my1 * 1 + my2 * 100 - opp1 * 1 - opp2 * 120
    if my2 >= 2:
        s += 500 + (my2 - 2) * 200
    if opp2 >= 2:
        s -= 600 + (opp2 - 2) * 200
    return s

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    start = time.time()
    deadline = start + 0.85
    # parse board
    my = 0
    opp = 0
    empties: list[int] = []
    try:
        for i in range(3):
            bi = board[i]
            for j in range(3):
                bj = bi[j]
                for k in range(3):
                    v = bj[k]
                    idx = i * 9 + j * 3 + k
                    if v == 1:
                        my |= (1 << idx)
                    elif v == -1:
                        opp |= (1 << idx)
                    else:
                        empties.append(idx)
    except Exception:
        return (1, 1, 1)

    if not empties:
        return (0, 0, 0)

    def first_empty_fallback():
        c = _idx_to_coord(empties[0])
        return (int(c[0]), int(c[1]), int(c[2]))

    try:
        # 1. immediate win
        for idx in empties:
            nm = my | (1 << idx)
            for m in LINES_BY_CELL[idx]:
                if (nm & m) == m:
                    c = _idx_to_coord(idx)
                    return (int(c[0]), int(c[1]), int(c[2]))
        # 2. opponent immediate threats
        threats: list[int] = []
        for idx in empties:
            no = opp | (1 << idx)
            for m in LINES_BY_CELL[idx]:
                if (no & m) == m:
                    threats.append(idx)
                    break
        if len(threats) == 1:
            c = _idx_to_coord(threats[0])
            return (int(c[0]), int(c[1]), int(c[2]))

        center_idx = 13  # (1,1,1)
        center_bit = 1 << center_idx
        occupied = my | opp

        # 3. center book (only if no threats)
        if (occupied & center_bit) == 0 and len(threats) == 0:
            return (1, 1, 1)

        # 4. second player first move book: 1 piece on board, center taken
        total_cnt = _pop(occupied)
        if total_cnt == 1:
            # play a corner
            for cidx in (0, 2, 6, 8, 18, 20, 24, 26):
                if (occupied & (1 << cidx)) == 0:
                    c = _idx_to_coord(cidx)
                    return (int(c[0]), int(c[1]), int(c[2]))
        if total_cnt == 0:
            return (1, 1, 1)

        # if multiple threats, need search; if search fails fallback to block one
        n = len(empties)

        # move ordering helper (closure for speed)
        def order_moves(cur_my: int, cur_opp: int, empt: list[int]):
            scored = []
            for idx in empt:
                s = CELL_W[idx]
                for m in LINES_BY_CELL[idx]:
                    a_my = cur_my & m
                    a_opp = cur_opp & m
                    if a_opp:
                        if a_my:
                            continue
                        # pure opponent line
                        # count opp stones in line
                        oc = _pop(a_opp)
                        if oc == 2:
                            s += 10000
                        elif oc == 1:
                            s += 50
                        # oc==0 impossible here (a_opp!=0)
                    else:
                        mc = _pop(a_my) if a_my else 0
                        if mc == 2:
                            s += 9000
                        elif mc == 1:
                            s += 100
                        else:
                            s += 1
                scored.append((s, idx))
            scored.sort(key=lambda x: x[0], reverse=True)
            return [idx for _, idx in scored]

        # decide max depth
        if n <= 8:
            max_depth = n
        elif n <= 12:
            max_depth = 6
        elif n <= 18:
            max_depth = 5
        else:
            max_depth = 4
        if max_depth > n:
            max_depth = n
        if max_depth < 2:
            max_depth = min(2, n)

        nodes = [0]

        # recursive negamax with alpha-beta, in-place empt list handling via new lists
        def negamax(cur_my: int, cur_opp: int, empt_list: list[int], depth: int, alpha: int, beta: int, lim: int, orig: int) -> int:
            nodes[0] += 1
            if (nodes[0] & 1023) == 0 and time.time() > deadline:
                raise _Timeout()
            if not empt_list:
                return 0
            if depth == 0:
                return _evaluate(cur_my, cur_opp)
            ordered = order_moves(cur_my, cur_opp, empt_list)
            # breadth limit on deep plies
            if depth <= lim - 2 and len(ordered) > 10:
                ordered = ordered[:10]
                if depth <= lim - 3 and len(ordered) > 8:
                    ordered = ordered[:8]
            best = -INF
            for idx in ordered:
                bit = 1 << idx
                new_my = cur_my | bit
                # win check
                w = False
                for m in LINES_BY_CELL[idx]:
                    if (new_my & m) == m:
                        w = True
                        break
                if w:
                    # prefer faster win
                    ply = orig - depth
                    return INF - ply
                # build new empt list
                # manual loop to avoid comprehension overhead? keep simple
                new_empt = [e for e in empt_list if e != idx]
                score = -negamax(cur_opp, new_my, new_empt, depth - 1, -beta, -alpha, lim, orig)
                if score > best:
                    best = score
                if best > alpha:
                    alpha = best
                if alpha >= beta:
                    break
            return best

        # initial ordering for best fallback
        root_ordered_init = order_moves(my, opp, empties)
        best_move_idx = root_ordered_init[0]

        # iterative deepening
        for lim in range(2, max_depth + 1):
            if time.time() > deadline - 0.05:
                break
            try:
                root_ordered = order_moves(my, opp, empties)
                alpha = -INF
                best_score = -INF
                local_best = root_ordered[0]
                for idx in root_ordered:
                    if time.time() > deadline - 0.02:
                        raise _Timeout()
                    bit = 1 << idx
                    new_my = my | bit
                    # win already checked, but double-check
                    w = False
                    for m in LINES_BY_CELL[idx]:
                        if (new_my & m) == m:
                            w = True
                            break
                    if w:
                        c = _idx_to_coord(idx)
                        return (int(c[0]), int(c[1]), int(c[2]))
                    new_empt = [e for e in empties if e != idx]
                    score = -negamax(opp, new_my, new_empt, lim - 1, -INF, -alpha, lim, lim)
                    if score > best_score:
                        best_score = score
                        local_best = idx
                    if score > alpha:
                        alpha = score
                    # beta cutoff at root = INF so no break
                best_move_idx = local_best
                if best_score >= INF - 50:
                    break
            except _Timeout:
                break

        c = _idx_to_coord(best_move_idx)
        # safety: ensure legal
        if ((my | opp) & (1 << best_move_idx)) != 0:
            return first_empty_fallback()
        return (int(c[0]), int(c[1]), int(c[2]))
    except _Timeout:
        try:
            c = _idx_to_coord(best_move_idx)  # type: ignore
            return (int(c[0]), int(c[1]), int(c[2]))
        except Exception:
            return first_empty_fallback()
    except Exception:
        try:
            return first_empty_fallback()
        except Exception:
            return (1, 1, 1)
