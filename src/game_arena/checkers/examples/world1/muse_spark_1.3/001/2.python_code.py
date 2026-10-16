
import time

_DIRS_ALL = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
_MAN_VAL = 100
_KING_VAL = 140

def _rc(p):
    return (p // 8, p % 8)

def _p(r, c):
    return r * 8 + c

def _inside(r, c):
    return 0 <= r < 8 and 0 <= c < 8

def _promo_row(color):
    return 7 if color == 'w' else 0

def _opp(color):
    return 'b' if color == 'w' else 'w'

def _gen_quiets(my_men, my_kings, occ, color):
    moves = []
    if color == 'w':
        mdirs = [(1, 1), (1, -1)]
    else:
        mdirs = [(-1, 1), (-1, -1)]
    pr = _promo_row(color)
    for pos in my_men:
        r = pos // 8
        c = pos % 8
        for dr, dc in mdirs:
            nr, nc = r + dr, c + dc
            if not _inside(nr, nc):
                continue
            np = nr * 8 + nc
            if np in occ:
                continue
            prom = (nr == pr)
            moves.append((pos, np, prom))
    for pos in my_kings:
        r = pos // 8
        c = pos % 8
        for dr, dc in _DIRS_ALL:
            nr, nc = r + dr, c + dc
            if not _inside(nr, nc):
                continue
            np = nr * 8 + nc
            if np in occ:
                continue
            moves.append((pos, np, False))
    return moves

def _caps_for_piece(start, is_king, my_set, opp_set, occ, color):
    pr = _promo_row(color)
    seqs = []
    # stack of (cur, captured_set_tuple_list, path_list, captured_set_for_lookup)
    # use recursion via stack
    # dfs
    def dfs(cur, captured_list, captured_set, path, visited):
        r = cur // 8
        c = cur % 8
        found = False
        for dr, dc in _DIRS_ALL:
            mr, mc = r + dr, c + dc
            lr, lc = r + 2 * dr, c + 2 * dc
            if not _inside(lr, lc):
                continue
            if not _inside(mr, mc):
                continue
            mid = mr * 8 + mc
            land = lr * 8 + lc
            if mid not in opp_set:
                continue
            if mid in captured_set:
                continue
            # landing must be empty (accounting for vacated start and captured)
            if land in visited:
                continue
            if land != start and land in occ and land not in captured_set:
                continue
            # legal capture step
            # promotion stops
            if not is_king and lr == pr:
                # terminal, do not extend
                seqs.append((path + [land], captured_list + [mid]))
                found = True
                continue
            found = True
            captured_set.add(mid)
            visited.add(land)
            dfs(land, captured_list + [mid], captured_set, path + [land], visited)
            captured_set.remove(mid)
            visited.remove(land)
        if not found and len(path) > 1:
            seqs.append((path, captured_list))
    dfs(start, [], set(), [start], set([start]))
    return seqs

def _gen_all_captures(my_men, my_kings, opp_men, opp_kings, color):
    my_set = my_men | my_kings
    opp_set = opp_men | opp_kings
    occ = my_set | opp_set
    all_seqs = []
    for pos in my_men:
        s = _caps_for_piece(pos, False, my_set, opp_set, occ, color)
        for path, caps in s:
            all_seqs.append((path, caps, False))
    for pos in my_kings:
        s = _caps_for_piece(pos, True, my_set, opp_set, occ, color)
        for path, caps in s:
            all_seqs.append((path, caps, True))
    return all_seqs

def _piece_score(men, kings, col):
    s = 0
    if col == 'w':
        for p in men:
            r = p // 8
            c = p % 8
            s += _MAN_VAL + r * 5
            if 2 <= r <= 5 and 2 <= c <= 5:
                s += 5
            elif 1 <= r <= 6 and 2 <= c <= 5:
                s += 2
            if c == 0 or c == 7:
                s += 2
            if r == 0 or r == 1:
                s += 4
        for p in kings:
            r = p // 8
            c = p % 8
            s += _KING_VAL
            d = abs(r - 3.5) + abs(c - 3.5)
            s += int((7.0 - d) * 2)
    else:
        for p in men:
            r = p // 8
            c = p % 8
            s += _MAN_VAL + (7 - r) * 5
            if 2 <= r <= 5 and 2 <= c <= 5:
                s += 5
            elif 1 <= r <= 6 and 2 <= c <= 5:
                s += 2
            if c == 0 or c == 7:
                s += 2
            if r == 6 or r == 7:
                s += 4
        for p in kings:
            r = p // 8
            c = p % 8
            s += _KING_VAL
            d = abs(r - 3.5) + abs(c - 3.5)
            s += int((7.0 - d) * 2)
    return s

def _evaluate(s_men, s_kings, o_men, o_kings, s_col):
    o_col = _opp(s_col)
    return _piece_score(s_men, s_kings, s_col) - _piece_score(o_men, o_kings, o_col)

class _Timeout(Exception):
    pass

def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    t0 = time.perf_counter()
    deadline = t0 + 0.88
    # convert to sets of ints
    try:
        s_men = set(p[0] * 8 + p[1] for p in my_men)
        s_kings = set(p[0] * 8 + p[1] for p in my_kings)
        o_men = set(p[0] * 8 + p[1] for p in opp_men)
        o_kings = set(p[0] * 8 + p[1] for p in opp_kings)
    except Exception:
        # bad input, return dummy
        try:
            f = tuple(my_men[0]) if my_men else tuple(my_kings[0])
            return ((int(f[0]), int(f[1])), (int(f[0]), int(f[1])))
        except Exception:
            return ((2, 1), (3, 0))

    # helpers to return move
    def seq_to_move(path):
        a = path[0]
        b = path[1]
        return ((a // 8, a % 8), (b // 8, b % 8))

    def quiet_to_move(q):
        return ((q[0] // 8, q[0] % 8), (q[1] // 8, q[1] % 8))

    # generate root legal (maximal captures for international safety)
    try:
        all_caps = _gen_all_captures(s_men, s_kings, o_men, o_kings, color)
    except Exception:
        all_caps = []

    is_capture_root = len(all_caps) > 0
    root_caps = []
    root_quiets = []
    if is_capture_root:
        ml = max(len(c[1]) for c in all_caps)
        root_caps = [c for c in all_caps if len(c[1]) == ml]
        # order: more kings captured, promotion
        def cap_key(item):
            path, caps, is_k = item
            # count king victims
            kv = 0
            for cp in caps:
                if cp in o_kings:
                    kv += 1
            end = path[-1]
            er = end // 8
            prom = 1 if (not is_k and er == _promo_row(color)) else 0
            return (-len(caps), -kv, -prom)
        root_caps.sort(key=cap_key)
        if len(root_caps) == 1:
            return seq_to_move(root_caps[0][0])
    else:
        occ = s_men | s_kings | o_men | o_kings
        try:
            root_quiets = _gen_quiets(s_men, s_kings, occ, color)
        except Exception:
            root_quiets = []
        if len(root_quiets) == 0:
            # no moves: must still return something legal-ish
            # try any capture (even non-maximal) or dummy
            if all_caps:
                return seq_to_move(all_caps[0][0])
            # dummy: move first piece anywhere if possible
            try:
                if s_men:
                    f = next(iter(s_men))
                else:
                    f = next(iter(s_kings))
                fr, fc = f // 8, f % 8
                for dr, dc in _DIRS_ALL:
                    nr, nc = fr + dr, fc + dc
                    if _inside(nr, nc) and (nr * 8 + nc) not in occ:
                        return ((fr, fc), (nr, nc))
                return ((fr, fc), (fr, fc))
            except Exception:
                return ((2, 1), (3, 0))
        if len(root_quiets) == 1:
            return quiet_to_move(root_quiets[0])
        # order quiets: promotion first, advancement, center
        pr = _promo_row(color)
        def q_key(q):
            f, t, prom = q
            fr = f // 8; fc = f % 8
            tr = t // 8; tc = t % 8
            adv = tr if color == 'w' else (7 - tr)
            cent = 1 if 2 <= tc <= 5 and 2 <= tr <= 5 else 0
            return (-int(prom), -adv, -cent)
        root_quiets.sort(key=q_key)

    # if no time, greedy return
    # build apply helpers
    def apply_capture(s_m, s_k, o_m, o_k, path, caps, is_k, col):
        ns_m = set(s_m); ns_k = set(s_k)
        no_m = set(o_m); no_k = set(o_k)
        st = path[0]; en = path[-1]
        if is_k:
            ns_k.remove(st); ns_k.add(en)
        else:
            ns_m.remove(st)
            if (en // 8) == _promo_row(col):
                ns_k.add(en)
            else:
                ns_m.add(en)
        for cp in caps:
            if cp in no_m:
                no_m.remove(cp)
            elif cp in no_k:
                no_k.remove(cp)
        return ns_m, ns_k, no_m, no_k

    def apply_quiet(s_m, s_k, o_m, o_k, f, t, col):
        ns_m = set(s_m); ns_k = set(s_k)
        # f is own piece
        if f in ns_m:
            ns_m.remove(f)
            if (t // 8) == _promo_row(col):
                ns_k.add(t)
            else:
                ns_m.add(t)
        else:
            ns_k.remove(f); ns_k.add(t)
        return ns_m, ns_k, o_m, o_k

    nodes = [0]

    def check_time():
        nodes[0] += 1
        if nodes[0] % 512 == 0 and time.perf_counter() > deadline:
            raise _Timeout()

    # negamax
    def negamax(s_m, s_k, o_m, o_k, col, depth, alpha, beta, ply):
        check_time()
        caps = _gen_all_captures(s_m, s_k, o_m, o_k, col)
        if caps:
            # order
            # sort by length desc, king captures, promotion
            # quick ordering without heavy sort for deep nodes: use len
            caps.sort(key=lambda x: -len(x[1]))
            if depth <= -6:
                return _evaluate(s_m, s_k, o_m, o_k, col)
            best = -1000000
            for path, clist, isk in caps:
                ns_m, ns_k, no_m, no_k = apply_capture(s_m, s_k, o_m, o_k, path, clist, isk, col)
                oc = _opp(col)
                v = -negamax(no_m, no_k, ns_m, ns_k, oc, depth - 1, -beta, -alpha, ply + 1)
                if v > best:
                    best = v
                if best > alpha:
                    alpha = best
                if alpha >= beta:
                    break
            return best
        else:
            occ2 = s_m | s_k | o_m | o_k
            qs = _gen_quiets(s_m, s_k, occ2, col)
            if not qs:
                return -9000 + ply  # loss
            if depth <= 0:
                return _evaluate(s_m, s_k, o_m, o_k, col)
            # order quiets: promotions first
            pr2 = _promo_row(col)
            # simple ordering by advancement
            if col == 'w':
                qs.sort(key=lambda q: (-int(q[2]), -(q[1] // 8)))
            else:
                qs.sort(key=lambda q: (-int(q[2]), -((7 - (q[1] // 8)))))
            best = -1000000
            for f, t, prom in qs:
                ns_m, ns_k, no_m, no_k = apply_quiet(s_m, s_k, o_m, o_k, f, t, col)
                oc = _opp(col)
                v = -negamax(no_m, no_k, ns_m, ns_k, oc, depth - 1, -beta, -alpha, ply + 1)
                if v > best:
                    best = v
                if best > alpha:
                    alpha = best
                if alpha >= beta:
                    break
            return best

    # iterative deepening at root
    try:
        if is_capture_root:
            # score each root cap
            # initial greedy best
            best_item = root_caps[0]
            best_is_cap = True
            # order already
            # try depths
            for depth in (1, 2, 3, 4, 5, 6, 7):
                if time.perf_counter() > deadline - 0.05:
                    break
                scores = []
                alpha = -1000000
                beta = 1000000
                # search each
                cur_best = None
                cur_best_val = -1000000
                for item in root_caps:
                    path, clist, isk = item
                    ns_m, ns_k, no_m, no_k = apply_capture(s_men, s_kings, o_men, o_kings, path, clist, isk, color)
                    oc = _opp(color)
                    # depth-1 for opponent
                    v = -negamax(no_m, no_k, ns_m, ns_k, oc, depth - 1, -beta, -alpha, 1)
                    scores.append((v, item))
                    if v > cur_best_val:
                        cur_best_val = v
                        cur_best = item
                    if v > alpha:
                        alpha = v
                # reorder for next iteration
                scores.sort(key=lambda x: -x[0])
                root_caps = [it for _, it in scores]
                best_item = cur_best
                # if winning line found and time low, break
                if depth >= 6 and time.perf_counter() > deadline - 0.15:
                    break
            return seq_to_move(best_item[0])
        else:
            best_q = root_quiets[0]
            for depth in (1, 2, 3, 4, 5, 6, 7):
                if time.perf_counter() > deadline - 0.05:
                    break
                scores = []
                alpha = -1000000
                beta = 1000000
                cur_best = None
                cur_best_val = -1000000
                for q in root_quiets:
                    f, t, prom = q
                    ns_m, ns_k, no_m, no_k = apply_quiet(s_men, s_kings, o_men, o_kings, f, t, color)
                    oc = _opp(color)
                    v = -negamax(no_m, no_k, ns_m, ns_k, oc, depth - 1, -beta, -alpha, 1)
                    scores.append((v, q))
                    if v > cur_best_val:
                        cur_best_val = v
                        cur_best = q
                    if v > alpha:
                        alpha = v
                scores.sort(key=lambda x: -x[0])
                root_quiets = [it for _, it in scores]
                best_q = cur_best
                if depth >= 6 and time.perf_counter() > deadline - 0.15:
                    break
            return quiet_to_move(best_q)
    except _Timeout:
        pass
    except Exception:
        pass

    # fallback on timeout / error: return current best greedy
    try:
        if is_capture_root and root_caps:
            return seq_to_move(root_caps[0][0])
        if (not is_capture_root) and root_quiets:
            return quiet_to_move(root_quiets[0])
        # last resort: any legal
        if all_caps:
            ml2 = max(len(c[1]) for c in all_caps)
            for c in all_caps:
                if len(c[1]) == ml2:
                    return seq_to_move(c[0])
            return seq_to_move(all_caps[0][0])
        occ3 = s_men | s_kings | o_men | o_kings
        qs2 = _gen_quiets(s_men, s_kings, occ3, color)
        if qs2:
            return quiet_to_move(qs2[0])
    except Exception:
        pass
    # ultimate dummy (should not happen)
    try:
        if s_men:
            f = next(iter(s_men)); fr, fc = f // 8, f % 8
        else:
            f = next(iter(s_kings)); fr, fc = f // 8, f % 8
        occ4 = s_men | s_kings | o_men | o_kings
        for dr, dc in _DIRS_ALL:
            nr, nc = fr + dr, fc + dc
            if _inside(nr, nc) and (nr * 8 + nc) not in occ4:
                return ((fr, fc), (nr, nc))
        return ((fr, fc), (fr, fc))
    except Exception:
        return ((2, 1), (3, 0))
