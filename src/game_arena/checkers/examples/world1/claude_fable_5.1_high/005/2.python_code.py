
import time

_TIME_BUDGET = 0.6
_pending = None
_KING_DIRS = ((1, -1), (1, 1), (-1, -1), (-1, 1))


class _Timeout(Exception):
    pass


def _caps(board, orig, sq, r, c, dirs, side, promo, is_man, taken, path, out):
    found = False
    for dr, dc in dirs:
        lr = r + 2 * dr
        lc = c + 2 * dc
        if 0 <= lr < 8 and 0 <= lc < 8:
            m = (r + dr) * 8 + (c + dc)
            q = board[m]
            if q != 0 and ((q < 0) if side > 0 else (q > 0)) and m not in taken:
                l = lr * 8 + lc
                if board[l] == 0:
                    found = True
                    nt = taken + (m,)
                    npth = path + (l,)
                    if is_man and lr == promo:
                        out.append((orig, l, nt, npth))
                    else:
                        _caps(board, orig, l, lr, lc, dirs, side, promo, is_man, nt, npth, out)
    if not found and taken:
        out.append((orig, sq, taken, path))


def _gen_moves(board, side, d, promo):
    caps = []
    quiet = []
    for sq in range(64):
        p = board[sq]
        if p == 0:
            continue
        if side > 0:
            if p < 0:
                continue
        else:
            if p > 0:
                continue
        r = sq >> 3
        c = sq & 7
        is_man = (p == 1 or p == -1)
        dirs = ((d, -1), (d, 1)) if is_man else _KING_DIRS
        board[sq] = 0
        _caps(board, sq, sq, r, c, dirs, side, promo, is_man, (), (), caps)
        board[sq] = p
        if not caps:
            for dr, dc in dirs:
                nr = r + dr
                nc = c + dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    t = nr * 8 + nc
                    if board[t] == 0:
                        quiet.append((sq, t, (), (t,)))
    return caps if caps else quiet


def _apply(board, mv, side, promo):
    b = board[:]
    frm, to, caps, _ = mv
    p = b[frm]
    b[frm] = 0
    for m in caps:
        b[m] = 0
    if (p == 1 or p == -1) and (to >> 3) == promo:
        p = 2 if side > 0 else -2
    b[to] = p
    return b


class _Engine:
    def __init__(self, d_me, deadline):
        self.d_me = d_me
        self.deadline = deadline
        self.nodes = 0
        self.tt = {}
        self.man_me = [0] * 64
        self.man_opp = [0] * 64
        self.king_tab = [0] * 64
        for sq in range(64):
            r = sq >> 3
            c = sq & 7
            prog_me = r if d_me == 1 else 7 - r
            prog_opp = 7 - prog_me
            center = 4.0 - max(abs(r - 3.5), abs(c - 3.5))
            v = 100 + 4 * prog_me
            if prog_me == 0:
                v += 7
            if 2 <= r <= 5 and 2 <= c <= 5:
                v += 3
            self.man_me[sq] = v
            v = 100 + 4 * prog_opp
            if prog_opp == 0:
                v += 7
            if 2 <= r <= 5 and 2 <= c <= 5:
                v += 3
            self.man_opp[sq] = v
            self.king_tab[sq] = 160 + int(2 * center)

    def evaluate(self, board):
        s = 0
        my = 0
        op = 0
        mm = self.man_me
        mo = self.man_opp
        kt = self.king_tab
        for sq in range(64):
            p = board[sq]
            if p == 0:
                continue
            if p == 1:
                s += mm[sq]
                my += 1
            elif p == 2:
                s += kt[sq]
                my += 1
            elif p == -1:
                s -= mo[sq]
                op += 1
            else:
                s -= kt[sq]
                op += 1
        if my != op:
            total = my + op
            s += (my - op) * (24 - total) * 2
        return s

    def search(self, board, side, depth, alpha, beta, ply):
        self.nodes += 1
        if (self.nodes & 255) == 0 and time.time() > self.deadline:
            raise _Timeout
        d = self.d_me if side == 1 else -self.d_me
        promo = 7 if d == 1 else 0
        moves = _gen_moves(board, side, d, promo)
        if not moves:
            return -30000 + ply
        is_cap = bool(moves[0][2])
        if depth <= 0 and (not is_cap or ply >= 40):
            return side * self.evaluate(board)
        use_tt = depth >= 1
        key = None
        tt_move = None
        if use_tt:
            key = (tuple(board), side)
            e = self.tt.get(key)
            if e is not None:
                e_depth, e_val, e_flag, e_move = e
                if e_depth >= depth:
                    if e_flag == 0:
                        return e_val
                    if e_flag == 1:
                        if e_val > alpha:
                            alpha = e_val
                    elif e_val < beta:
                        beta = e_val
                    if alpha >= beta:
                        return e_val
                tt_move = e_move
        if len(moves) > 1:
            if is_cap:
                moves.sort(key=lambda m: -len(m[2]))
            elif d == 1:
                moves.sort(key=lambda m: -(m[1] >> 3))
            else:
                moves.sort(key=lambda m: (m[1] >> 3))
            if tt_move is not None and tt_move in moves:
                moves.remove(tt_move)
                moves.insert(0, tt_move)
        best = -100000
        best_move = None
        a0 = alpha
        nd = depth - 1
        for mv in moves:
            nb = _apply(board, mv, side, promo)
            v = -self.search(nb, -side, nd, -beta, -alpha, ply + 1)
            if v > best:
                best = v
                best_move = mv
                if v > alpha:
                    alpha = v
                    if alpha >= beta:
                        break
        if use_tt:
            if best <= a0:
                flag = 2
            elif best >= beta:
                flag = 1
            else:
                flag = 0
            self.tt[key] = (depth, best, flag, best_move)
        return best


def _to_move(frm, to):
    return ((frm >> 3, frm & 7), (to >> 3, to & 7))


def policy(my_men, my_kings, opp_men, opp_kings, color):
    global _pending
    start = time.time()
    deadline = start + _TIME_BUDGET
    board = [0] * 64
    for (r, c) in my_men:
        board[r * 8 + c] = 1
    for (r, c) in my_kings:
        board[r * 8 + c] = 2
    for (r, c) in opp_men:
        board[r * 8 + c] = -1
    for (r, c) in opp_kings:
        board[r * 8 + c] = -2
    d_me = -1 if color == 'b' else 1
    promo = 7 if d_me == 1 else 0

    # Continue a planned multi-jump if the arena is step-based and state matches.
    try:
        if _pending is not None:
            exp, rest = _pending
            if rest and tuple(board) == exp:
                frm, to, cap = rest[0]
                nb = board[:]
                p = nb[frm]
                nb[frm] = 0
                nb[cap] = 0
                nb[to] = p
                rest = rest[1:]
                _pending = (tuple(nb), rest) if rest else None
                return _to_move(frm, to)
            _pending = None
    except Exception:
        _pending = None

    moves = _gen_moves(board, 1, d_me, promo)
    if not moves:
        pieces = list(my_men) + list(my_kings)
        if pieces:
            r, c = pieces[0]
            return ((r, c), (r + d_me, c + 1))
        return ((0, 0), (1, 1))

    best = moves[0]
    if len(moves) > 1:
        eng = _Engine(d_me, deadline)
        ordered = list(moves)
        final_scores = None
        try:
            for depth in range(1, 40):
                alpha = -1000000
                beta = 1000000
                cur_best = None
                cur_val = -10000000
                scores = []
                for mv in ordered:
                    nb = _apply(board, mv, 1, promo)
                    v = -eng.search(nb, -1, depth - 1, -beta, -alpha, 1)
                    scores.append((v, mv))
                    if v > cur_val:
                        cur_val = v
                        cur_best = mv
                        if v > alpha:
                            alpha = v
                    best = cur_best
                scores.sort(key=lambda x: -x[0])
                ordered = [m for _, m in scores]
                final_scores = scores
                if cur_val > 20000 or cur_val < -20000:
                    break
                if time.time() - start > _TIME_BUDGET * 0.45:
                    # unlikely to finish another full iteration
                    pass
        except _Timeout:
            pass
        except Exception:
            pass
        # Hedge: prefer a single-jump capture if it is practically as good.
        try:
            if final_scores and len(best[2]) > 1:
                top = final_scores[0][0]
                for v, mv in final_scores:
                    if len(mv[2]) == 1 and v >= top - 25:
                        best = mv
                        break
        except Exception:
            pass

    frm, to, caps, path = best
    first_to = path[0]
    try:
        if len(path) > 1:
            nb = board[:]
            p = nb[frm]
            nb[frm] = 0
            nb[caps[0]] = 0
            nb[first_to] = p
            rest = []
            cur = first_to
            for i in range(1, len(path)):
                rest.append((cur, path[i], caps[i]))
                cur = path[i]
            _pending = (tuple(nb), rest)
        else:
            _pending = None
    except Exception:
        _pending = None
    return _to_move(frm, first_to)
