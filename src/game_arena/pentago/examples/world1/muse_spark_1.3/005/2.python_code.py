
import time

FULL = (1 << 36) - 1
BIT = [1 << i for i in range(36)]

# win masks : 32 windows of length 5
WIN_MASKS = []
for r in range(6):
    for c in (0, 1):
        m = 0
        for k in range(5):
            m |= 1 << (r * 6 + c + k)
        WIN_MASKS.append(m)
for c in range(6):
    for r in (0, 1):
        m = 0
        for k in range(5):
            m |= 1 << ((r + k) * 6 + c)
        WIN_MASKS.append(m)
for r in (0, 1):
    for c in (0, 1):
        m = 0
        for k in range(5):
            m |= 1 << ((r + k) * 6 + c + k)
        WIN_MASKS.append(m)
for r in (0, 1):
    for c in (4, 5):
        m = 0
        for k in range(5):
            m |= 1 << ((r + k) * 6 + c - k)
        WIN_MASKS.append(m)
WIN_MASKS = tuple(WIN_MASKS)

QUAD_BASE = [(0, 0), (0, 3), (3, 0), (3, 3)]
QUAD_CELLS = []
QUAD_MASK = []
for (br, bc) in QUAD_BASE:
    cells = []
    m = 0
    for i in range(3):
        for j in range(3):
            p = (br + i) * 6 + (bc + j)
            cells.append(p)
            m |= 1 << p
    QUAD_CELLS.append(cells)
    QUAD_MASK.append(m)

# ROT_MAP[q][0]=L, [q][1]=R  list of (src,dst)
ROT_MAP = []
for q, (br, bc) in enumerate(QUAD_BASE):
    mpL = []
    mpR = []
    for i in range(3):
        for j in range(3):
            src = (br + i) * 6 + (bc + j)
            dstR = (br + j) * 6 + (bc + 2 - i)
            dstL = (br + 2 - j) * 6 + (bc + i)
            mpR.append((src, dstR))
            mpL.append((src, dstL))
    ROT_MAP.append((mpL, mpR))

CENTER_MASK = (1 << (2 * 6 + 2)) | (1 << (2 * 6 + 3)) | (1 << (3 * 6 + 2)) | (1 << (3 * 6 + 3))

WY = (0, 1, 12, 120, 8000)
WO = (0, 1, 15, 180, 15000)
INF = 10000000

try:
    _bc = int.bit_count
    def popcnt(x):
        return x.bit_count()
except Exception:
    def popcnt(x):
        return bin(x).count("1")

def has_win(b):
    for m in WIN_MASKS:
        if (b & m) == m:
            return True
    return False

def rotate_bits(bits, q, d):
    # d 0=L 1=R
    mp = ROT_MAP[q][d]
    qm = QUAD_MASK[q]
    res = bits & (~qm)
    # unrolled loop of 9
    for src, dst in mp:
        if (bits >> src) & 1:
            res |= 1 << dst
    return res

def evaluate(y, o):
    yw = False
    ow = False
    # quick win check fused
    for m in WIN_MASKS:
        if not yw and (y & m) == m:
            yw = True
        if not ow and (o & m) == m:
            ow = True
        if yw and ow:
            return 0
    if yw:
        return INF
    if ow:
        return -INF
    s = 0
    for m in WIN_MASKS:
        ym = y & m
        if ym:
            if o & m:
                continue
            c = popcnt(ym)
            s += WY[c] if c < 5 else 0
        else:
            om = o & m
            if om:
                c = popcnt(om)
                s -= WO[c] if c < 5 else 0
    s += popcnt(y & CENTER_MASK) * 4 - popcnt(o & CENTER_MASK) * 4
    return s


class _Timeout(Exception):
    pass


def policy(you, opponent) -> str:
    # fallback legal move finder
    def fallback():
        try:
            for r in range(6):
                for c in range(6):
                    try:
                        a = you[r][c]
                        b = opponent[r][c]
                    except Exception:
                        continue
                    if a == 0 and b == 0:
                        return f"{r+1},{c+1},0,R"
        except Exception:
            pass
        return "1,1,0,R"

    try:
        start = time.time()
        deadline = start + 0.90

        yb = 0
        ob = 0
        for r in range(6):
            for c in range(6):
                try:
                    a = you[r][c]
                except Exception:
                    a = 0
                try:
                    b = opponent[r][c]
                except Exception:
                    b = 0
                if a == 1:
                    yb |= 1 << (r * 6 + c)
                elif b == 1:
                    ob |= 1 << (r * 6 + c)
        occ = yb | ob
        empties = []
        for p in range(36):
            if (occ >> p) & 1 == 0:
                empties.append(p)
        if not empties:
            return fallback()
        yc = popcnt(yb)
        oc = popcnt(ob)
        total = yc + oc

        if total == 0:
            return "3,3,1,R"
        if total == 1:
            # take centre if free
            for (rr, cc) in ((2, 2), (2, 3), (3, 2), (3, 3)):
                p = rr * 6 + cc
                if ((occ >> p) & 1) == 0:
                    return f"{rr+1},{cc+1},0,R"

        # ---- immediate winning move ----
        can_win_us = (yc + 1) >= 5
        can_win_opp_next = (oc + 1) >= 5
        draw_move = None
        if can_win_us:
            for p in empties:
                r = p // 6
                c = p % 6
                yplaced = yb | (1 << p)
                for q in range(4):
                    for d, ch in ((0, 'L'), (1, 'R')):
                        y1 = rotate_bits(yplaced, q, d)
                        o1 = rotate_bits(ob, q, d)
                        yw = has_win(y1)
                        if yw:
                            ow = has_win(o1)
                            if not ow:
                                return f"{r+1},{c+1},{q},{ch}"
                            if draw_move is None:
                                draw_move = f"{r+1},{c+1},{q},{ch}"
        # if we have only drawing win and board almost full, take it
        # otherwise continue to search (draw better than loss, handled later)

        # ---- generate all root boards dedup ----
        # build list of (score, y1, o1, movestr)
        root_list = []
        seen = set()
        for p in empties:
            r = p // 6
            c = p % 6
            yplaced = yb | (1 << p)
            for q in range(4):
                for d, ch in ((0, 'L'), (1, 'R')):
                    y1 = rotate_bits(yplaced, q, d)
                    o1 = rotate_bits(ob, q, d)
                    key = (y1, o1)
                    if key in seen:
                        continue
                    seen.add(key)
                    # immediate suicide? mark very bad but keep for now
                    # quick win flags
                    yw = False
                    ow = False
                    # only check if possible
                    if (yc + 1) >= 5 or (oc) >= 5:
                        for m in WIN_MASKS:
                            if not yw and (y1 & m) == m:
                                yw = True
                            if not ow and (o1 & m) == m:
                                ow = True
                            if yw and ow:
                                break
                    if ow and not yw:
                        sc = -INF
                    elif yw and not ow:
                        sc = INF
                    elif yw and ow:
                        sc = 0
                    else:
                        sc = evaluate(y1, o1)
                    root_list.append([sc, y1, o1, f"{r+1},{c+1},{q},{ch}"])
                    if time.time() > deadline - 0.05:
                        break
                if time.time() > deadline - 0.05:
                    break
            if time.time() > deadline - 0.05:
                break

        if not root_list:
            return fallback()
        # sort desc
        root_list.sort(key=lambda x: x[0], reverse=True)
        # if best is immediate win, return it
        if root_list[0][0] >= INF:
            return root_list[0][3]
        # filter losing moves that allow opponent immediate win (if relevant)
        if can_win_opp_next and len(root_list) > 1:
            # only check top N to save time
            Ncheck = min(len(root_list), 40)
            filtered = []
            # quick helper to test if opponent has winning reply from (y1,o1)
            for idx in range(Ncheck):
                sc, y1, o1 = root_list[idx][0], root_list[idx][1], root_list[idx][2]
                if sc <= -INF // 2:
                    continue  # already losing immediately
                occ1 = y1 | o1
                opp_win_exists = False
                # enumerate opp placements
                # if time low, break
                if time.time() > deadline - 0.15:
                    filtered = root_list[:Ncheck]
                    break
                for p2 in range(36):
                    if (occ1 >> p2) & 1:
                        continue
                    oplaced = o1 | (1 << p2)
                    for q2 in range(4):
                        for d2 in (0, 1):
                            y2 = rotate_bits(y1, q2, d2)
                            o2 = rotate_bits(oplaced, q2, d2)
                            # opponent wins and we don't -> loss
                            ow2 = has_win(o2)
                            if ow2 and not has_win(y2):
                                opp_win_exists = True
                                break
                        if opp_win_exists:
                            break
                    if opp_win_exists:
                        break
                if not opp_win_exists:
                    filtered.append(root_list[idx])
            # also add unchecked tail
            if len(root_list) > Ncheck:
                filtered.extend(root_list[Ncheck:])
            if filtered:
                # keep filtered, but preserve order; if we removed too many, keep best of removed as last resort
                root_list = filtered
            else:
                # all checked moves lose -> try to force draw if draw_move exists
                if draw_move is not None:
                    return draw_move
                # keep original (all losing), will pick best static
                pass
            # re-sort filtered by static (already sorted)
            if time.time() > deadline - 0.05:
                return root_list[0][3]

        n_empty = len(empties)
        if n_empty >= 22:
            max_depth = 2
            RK = 18
            Kmid = 10
        elif n_empty >= 14:
            max_depth = 3
            RK = 16
            Kmid = 10
        elif n_empty >= 9:
            max_depth = 3
            RK = 22
            Kmid = 12
        else:
            max_depth = 4
            RK = 28
            Kmid = 12

        root_list = root_list[:RK] if len(root_list) > RK else root_list

        # if only one candidate or no time, return best static
        if len(root_list) == 1 or time.time() > deadline - 0.10:
            return root_list[0][3]

        nodes = [0]

        def check_to():
            nodes[0] += 1
            if (nodes[0] & 63) == 0 and time.time() > deadline:
                raise _Timeout()

        # move generation inside search
        def gen_children(y, o, is_max, K):
            check_to()
            occ2 = y | o
            # collect empties
            el = []
            for pp in range(36):
                if ((occ2 >> pp) & 1) == 0:
                    el.append(pp)
            if not el:
                return []
            seen2 = set()
            lst = []
            for pp in el:
                placed = (y | (1 << pp)) if is_max else (o | (1 << pp))
                # we need both boards after rotation; placement only on mover side
                for qq in range(4):
                    for dd in (0, 1):
                        if is_max:
                            ny = rotate_bits(placed, qq, dd)
                            no = rotate_bits(o, qq, dd)
                        else:
                            ny = rotate_bits(y, qq, dd)
                            no = rotate_bits(placed, qq, dd)
                        key = (ny, no)
                        if key in seen2:
                            continue
                        seen2.add(key)
                        sc = evaluate(ny, no)
                        lst.append((sc, ny, no))
            if not lst:
                return []
            lst.sort(key=lambda x: x[0], reverse=is_max)
            if len(lst) > K:
                lst = lst[:K]
            return lst

        def min_value(y, o, depth, alpha, beta):
            check_to()
            # terminal?
            yw = has_win(y)
            ow = has_win(o)
            if yw and ow:
                return 0
            if yw:
                return INF + depth
            if ow:
                return -INF - depth
            if (y | o) == FULL:
                return 0
            if depth <= 0:
                return evaluate(y, o)
            if depth == 1:
                # opponent moves, pick min eval
                occ2 = y | o
                best = 10**18
                seen2 = set()
                for pp in range(36):
                    if (occ2 >> pp) & 1:
                        continue
                    oplaced = o | (1 << pp)
                    for qq in range(4):
                        for dd in (0, 1):
                            ny = rotate_bits(y, qq, dd)
                            no = rotate_bits(oplaced, qq, dd)
                            key = (ny, no)
                            if key in seen2:
                                continue
                            seen2.add(key)
                            v = evaluate(ny, no)
                            if v < best:
                                best = v
                                if best <= alpha:
                                    return best
                                if best < beta:
                                    beta = best
                            check_to()
                return best if best != 10**18 else evaluate(y, o)
            else:
                children = gen_children(y, o, False, Kmid)
                if not children:
                    return evaluate(y, o)
                best = 10**18
                for _, ny, no in children:
                    v = max_value(ny, no, depth - 1, alpha, beta)
                    if v < best:
                        best = v
                        if best <= alpha:
                            return best
                        if best < beta:
                            beta = best
                return best

        def max_value(y, o, depth, alpha, beta):
            check_to()
            yw = has_win(y)
            ow = has_win(o)
            if yw and ow:
                return 0
            if yw:
                return INF + depth
            if ow:
                return -INF - depth
            if (y | o) == FULL:
                return 0
            if depth <= 0:
                return evaluate(y, o)
            if depth == 1:
                occ2 = y | o
                best = -10**18
                seen2 = set()
                for pp in range(36):
                    if (occ2 >> pp) & 1:
                        continue
                    yplaced = y | (1 << pp)
                    for qq in range(4):
                        for dd in (0, 1):
                            ny = rotate_bits(yplaced, qq, dd)
                            no = rotate_bits(o, qq, dd)
                            key = (ny, no)
                            if key in seen2:
                                continue
                            seen2.add(key)
                            v = evaluate(ny, no)
                            if v > best:
                                best = v
                                if best >= beta:
                                    return best
                                if best > alpha:
                                    alpha = best
                            check_to()
                return best if best != -10**18 else evaluate(y, o)
            else:
                children = gen_children(y, o, True, Kmid)
                if not children:
                    return evaluate(y, o)
                best = -10**18
                for _, ny, no in children:
                    v = min_value(ny, no, depth - 1, alpha, beta)
                    if v > best:
                        best = v
                        if best >= beta:
                            return best
                        if best > alpha:
                            alpha = best
                return best

        best_move = root_list[0][3]
        try:
            # iterative deepening: try max_depth, fallback to 2 if timeout
            depths = [2]
            if max_depth >= 3:
                depths.append(3)
            if max_depth >= 4:
                depths.append(4)
            cur_best = best_move
            for d in depths:
                if time.time() > deadline - 0.15:
                    break
                alpha = -10**18
                beta = 10**18
                local_best = cur_best
                local_best_val = -10**18
                # order root by previous iteration? keep static order for d==2, else reorder by previous scores
                for _, y1, o1, ms in list(root_list):
                    v = min_value(y1, o1, d - 1, alpha, beta)
                    if v > local_best_val:
                        local_best_val = v
                        local_best = ms
                    if v > alpha:
                        alpha = v
                    check_to()
                    if time.time() > deadline - 0.05:
                        raise _Timeout()
                cur_best = local_best
                best_move = cur_best
                # update root_list order by searched values? re-evaluate quickly: we already have values implicitly; do one pass reorder
                # early exit if winning
                if local_best_val >= INF // 2:
                    break
        except _Timeout:
            pass
        return best_move
    except Exception:
        return fallback()

