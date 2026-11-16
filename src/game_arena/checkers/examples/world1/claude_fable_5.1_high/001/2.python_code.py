
import time

TIME_BUDGET = 0.55
WIN = 30000
INF = 10 ** 9
MAX_PLY = 64

DIRS = ((1, 1), (1, -1), (-1, 1), (-1, -1))
NB = [[-1] * 4 for _ in range(64)]
JP = [[-1] * 4 for _ in range(64)]
for _idx in range(64):
    _r, _c = divmod(_idx, 8)
    for _d, (_dr, _dc) in enumerate(DIRS):
        _r1, _c1 = _r + _dr, _c + _dc
        if 0 <= _r1 < 8 and 0 <= _c1 < 8:
            NB[_idx][_d] = _r1 * 8 + _c1
            _r2, _c2 = _r + 2 * _dr, _c + 2 * _dc
            if 0 <= _r2 < 8 and 0 <= _c2 < 8:
                JP[_idx][_d] = _r2 * 8 + _c2

MAN_DIRS = {1: (0, 1), -1: (2, 3)}
KING_DIRS = (0, 1, 2, 3)

ROWB = [0, 2, 4, 7, 10, 14, 18, 0]
COLB = [0, 1, 2, 3, 3, 2, 1, 0]
MAN_PST = [0] * 64
OPP_MAN_PST = [0] * 64
KING_PST = [0] * 64
for _idx in range(64):
    _r, _c = divmod(_idx, 8)
    MAN_PST[_idx] = ROWB[_r] + COLB[_c]
    OPP_MAN_PST[_idx] = ROWB[7 - _r] + COLB[_c]
    KING_PST[_idx] = 2 * (7 - int(abs(_r - 3.5) + abs(_c - 3.5)))


def _caps(board, idx, side, king, dirs, path, caps, out):
    found = False
    piece = board[idx]
    nb = NB[idx]
    jp = JP[idx]
    for d in dirs:
        m = nb[d]
        if m < 0:
            continue
        q = board[m]
        if q == 0 or q * side > 0:
            continue
        l = jp[d]
        if l < 0 or board[l] != 0:
            continue
        found = True
        board[idx] = 0
        board[m] = 0
        board[l] = piece
        path.append(l)
        caps.append(m)
        if (not king) and ((side == 1 and l >= 56) or (side == -1 and l < 8)):
            out.append((tuple(path), tuple(caps)))
        else:
            _caps(board, l, side, king, dirs, path, caps, out)
        path.pop()
        caps.pop()
        board[l] = 0
        board[m] = q
        board[idx] = piece
    if not found and len(path) > 1:
        out.append((tuple(path), tuple(caps)))


def gen_moves(board, side):
    caps = []
    for idx in range(64):
        p = board[idx]
        if p * side <= 0:
            continue
        king = (p == 2 or p == -2)
        dirs = KING_DIRS if king else MAN_DIRS[side]
        _caps(board, idx, side, king, dirs, [idx], [], caps)
    if caps:
        return caps
    moves = []
    for idx in range(64):
        p = board[idx]
        if p * side <= 0:
            continue
        king = (p == 2 or p == -2)
        dirs = KING_DIRS if king else MAN_DIRS[side]
        nb = NB[idx]
        for d in dirs:
            m = nb[d]
            if m >= 0 and board[m] == 0:
                moves.append(((idx, m), ()))
    return moves


def apply_move(board, move, side):
    nb = board[:]
    path, caps = move
    src = path[0]
    dest = path[-1]
    piece = nb[src]
    nb[src] = 0
    for c in caps:
        nb[c] = 0
    if piece == 1 and dest >= 56:
        piece = 2
    elif piece == -1 and dest < 8:
        piece = -2
    nb[dest] = piece
    return nb


def evaluate(board):
    mm = mk = om = ok = 0
    s = 0
    my_back = 0
    op_back = 0
    my_kings = []
    opp_pieces = []
    for idx in range(64):
        p = board[idx]
        if p == 0:
            continue
        if p == 1:
            mm += 1
            s += MAN_PST[idx]
            if idx < 8:
                my_back += 1
        elif p == -1:
            om += 1
            s -= OPP_MAN_PST[idx]
            if idx >= 56:
                op_back += 1
            opp_pieces.append(idx)
        elif p == 2:
            mk += 1
            s += KING_PST[idx]
            my_kings.append(idx)
        else:
            ok += 1
            s -= KING_PST[idx]
            opp_pieces.append(idx)
    mat = 100 * (mm - om) + 155 * (mk - ok)
    s += mat
    total = mm + om + mk + ok
    if mat != 0:
        s += int(mat * 8 / (total + 4))
    if om > 0:
        s += 5 * my_back
    if mm > 0:
        s -= 5 * op_back
    # hunting term: pull my kings toward few remaining enemy pieces when ahead
    if mat > 0 and my_kings and 0 < len(opp_pieces) <= 4:
        dist = 0
        for k in my_kings:
            kr, kc = divmod(k, 8)
            best = 99
            for o in opp_pieces:
                orr, oc = divmod(o, 8)
                dd = abs(kr - orr) + abs(kc - oc)
                if dd < best:
                    best = dd
            dist += best
        s -= 2 * dist
    return s


class Search:
    def __init__(self, deadline):
        self.deadline = deadline
        self.nodes = 0
        self.tt = {}
        self.hist = {}
        self.abort = False

    def negamax(self, board, side, depth, alpha, beta, ply):
        self.nodes += 1
        if (self.nodes & 255) == 0 and time.time() > self.deadline:
            self.abort = True
            return 0
        moves = gen_moves(board, side)
        if not moves:
            return -WIN + ply
        is_cap = bool(moves[0][1])
        if (depth <= 0 and not is_cap) or ply >= MAX_PLY:
            return side * evaluate(board)
        key = (tuple(board), side)
        tt_move = None
        entry = self.tt.get(key)
        if entry is not None:
            e_depth, e_flag, e_val, tt_move = entry
            if e_depth >= depth:
                if e_flag == 0:
                    return e_val
                if e_flag == 1 and e_val >= beta:
                    return e_val
                if e_flag == 2 and e_val <= alpha:
                    return e_val
        if len(moves) > 1:
            hist = self.hist
            moves.sort(key=lambda m: (m == tt_move, len(m[1]),
                                      hist.get((side, m[0][0], m[0][-1]), 0)),
                       reverse=True)
        best = -INF
        best_move = None
        a = alpha
        for m in moves:
            nb = apply_move(board, m, side)
            v = -self.negamax(nb, -side, depth - 1, -beta, -a, ply + 1)
            if self.abort:
                return 0
            if v > best:
                best = v
                best_move = m
                if v > a:
                    a = v
                    if a >= beta:
                        hk = (side, m[0][0], m[0][-1])
                        self.hist[hk] = self.hist.get(hk, 0) + depth * depth
                        break
        if best <= alpha:
            flag = 2
        elif best >= beta:
            flag = 1
        else:
            flag = 0
        self.tt[key] = (depth, flag, best, best_move)
        return best


def choose_move(board, moves, deadline):
    if len(moves) == 1:
        return moves[0]
    s = Search(deadline)
    best_move = moves[0]
    depth = 1
    while depth <= 50:
        a = -INF
        local_best = None
        local_val = -INF
        ordered = [best_move] + [m for m in moves if m != best_move]
        for m in ordered:
            nb = apply_move(board, m, 1)
            v = -s.negamax(nb, -1, depth - 1, -INF, -a, 1)
            if s.abort:
                break
            if v > local_val:
                local_val = v
                local_best = m
                if v > a:
                    a = v
        if s.abort:
            if local_best is not None:
                best_move = local_best
            break
        best_move = local_best
        if local_val >= WIN - 200 or local_val <= -WIN + 200:
            break
        if time.time() > deadline:
            break
        depth += 1
    return best_move


def policy(my_men, my_kings, opp_men, opp_kings, color):
    start = time.time()
    deadline = start + TIME_BUDGET
    flip = str(color).lower().startswith('b')

    def to_idx(sq):
        r, c = int(sq[0]), int(sq[1])
        if flip:
            r = 7 - r
        return r * 8 + c

    def to_sq(i):
        r, c = divmod(i, 8)
        if flip:
            r = 7 - r
        return (r, c)

    board = [0] * 64
    for sq in my_men:
        board[to_idx(sq)] = 1
    for sq in my_kings:
        board[to_idx(sq)] = 2
    for sq in opp_men:
        board[to_idx(sq)] = -1
    for sq in opp_kings:
        board[to_idx(sq)] = -2

    moves = gen_moves(board, 1)
    if not moves:
        pieces = list(my_men) + list(my_kings)
        if pieces:
            p = pieces[0]
            dr = -1 if flip else 1
            tr = min(7, max(0, int(p[0]) + dr))
            tc = min(7, max(0, int(p[1]) + 1))
            return ((int(p[0]), int(p[1])), (tr, tc))
        return ((0, 0), (1, 1))

    try:
        mv = choose_move(board, moves, deadline)
        if mv is None:
            mv = moves[0]
    except Exception:
        mv = moves[0]
    path = mv[0]
    return (to_sq(path[0]), to_sq(path[1]))
