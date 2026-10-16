
import time

KING_DIRS = ((1, -1), (1, 1), (-1, -1), (-1, 1))
INF = 10 ** 9
TIME_BUDGET = 0.70

MYDIR = 1
deadline = 0.0
nodes = 0
TT = {}
LAST = None
MEN_ME = [0] * 64
MEN_OPP = [0] * 64
KPST = [0] * 64
_pst_dir = None


class Timeout(Exception):
    pass


def build_pst(mydir):
    global MEN_ME, MEN_OPP, KPST, _pst_dir
    if _pst_dir == mydir:
        return
    _pst_dir = mydir
    MEN_ME = [0] * 64
    MEN_OPP = [0] * 64
    KPST = [0] * 64
    for sq in range(64):
        r, c = sq >> 3, sq & 7
        center = 0
        if 2 <= r <= 5 and 2 <= c <= 5:
            center = 3
        if 3 <= r <= 4 and 3 <= c <= 4:
            center = 5
        edge_pen = 0
        if c == 0 or c == 7:
            edge_pen = 2
        # my men
        adv = r if mydir == 1 else 7 - r
        home = 0 if mydir == 1 else 7
        val = 3 * adv + center - edge_pen
        if r == home:
            val += 7
        MEN_ME[sq] = val
        # opponent men
        adv_o = 7 - r if mydir == 1 else r
        home_o = 7 if mydir == 1 else 0
        val_o = 3 * adv_o + center - edge_pen
        if r == home_o:
            val_o += 7
        MEN_OPP[sq] = val_o
        # kings
        dist_edge = min(r, 7 - r, c, 7 - c)
        KPST[sq] = 2 * dist_edge + center


def _caps(board, sq, r, c, v, side, is_king, dirs, prom_row, path, caps, out):
    found = False
    for dr, dc in dirs:
        lr, lc = r + 2 * dr, c + 2 * dc
        if 0 <= lr < 8 and 0 <= lc < 8:
            msq = (r + dr) * 8 + (c + dc)
            m = board[msq]
            lsq = lr * 8 + lc
            if m != 0 and ((m > 0) != (side > 0)) and board[lsq] == 0:
                found = True
                board[sq] = 0
                board[msq] = 0
                board[lsq] = v
                path.append(lsq)
                caps.append(msq)
                if (not is_king) and lr == prom_row:
                    out.append((tuple(path), tuple(caps)))
                else:
                    _caps(board, lsq, lr, lc, v, side, is_king, dirs, prom_row, path, caps, out)
                path.pop()
                caps.pop()
                board[lsq] = 0
                board[msq] = m
                board[sq] = v
    if not found and len(path) > 1:
        out.append((tuple(path), tuple(caps)))


def gen_moves(board, side, mydir):
    fwd = mydir if side == 1 else -mydir
    prom_row = 7 if fwd == 1 else 0
    man_dirs = ((fwd, -1), (fwd, 1))
    pieces = []
    if side == 1:
        for sq in range(64):
            if board[sq] > 0:
                pieces.append(sq)
    else:
        for sq in range(64):
            if board[sq] < 0:
                pieces.append(sq)
    captures = []
    for sq in pieces:
        v = board[sq]
        is_king = (v == 2 or v == -2)
        dirs = KING_DIRS if is_king else man_dirs
        _caps(board, sq, sq >> 3, sq & 7, v, side, is_king, dirs, prom_row, [sq], [], captures)
    if captures:
        return captures, True
    quiet = []
    for sq in pieces:
        v = board[sq]
        is_king = (v == 2 or v == -2)
        dirs = KING_DIRS if is_king else man_dirs
        r, c = sq >> 3, sq & 7
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8 and board[nr * 8 + nc] == 0:
                quiet.append(((sq, nr * 8 + nc), ()))
    return quiet, False


def apply_move(board, move, side, mydir):
    path, caps = move
    nb = board[:]
    v = nb[path[0]]
    nb[path[0]] = 0
    for c in caps:
        nb[c] = 0
    dest = path[-1]
    if v == 1 or v == -1:
        fwd = mydir if side == 1 else -mydir
        prom_row = 7 if fwd == 1 else 0
        if (dest >> 3) == prom_row:
            v = 2 * side
    nb[dest] = v
    return nb


def evaluate(board, side):
    my_mat = 0
    opp_mat = 0
    pos = 0
    my_kings = []
    opp_kings = []
    my_pieces = []
    opp_pieces = []
    for sq in range(64):
        v = board[sq]
        if v == 0:
            continue
        if v == 1:
            my_mat += 100
            pos += MEN_ME[sq]
            my_pieces.append(sq)
        elif v == 2:
            my_mat += 170
            pos += KPST[sq]
            my_kings.append(sq)
            my_pieces.append(sq)
        elif v == -1:
            opp_mat += 100
            pos -= MEN_OPP[sq]
            opp_pieces.append(sq)
        else:
            opp_mat += 170
            pos -= KPST[sq]
            opp_kings.append(sq)
            opp_pieces.append(sq)
    diff = my_mat - opp_mat
    score = diff + pos
    total = len(my_pieces) + len(opp_pieces)
    if diff != 0 and total > 0:
        score += diff * 5 // total
    if total <= 10:
        if diff > 0 and my_kings:
            d = 0
            for k in my_kings:
                kr, kc = k >> 3, k & 7
                for p in opp_pieces:
                    pr, pc = p >> 3, p & 7
                    d += max(abs(kr - pr), abs(kc - pc))
            score -= 2 * d
        elif diff < 0 and opp_kings:
            d = 0
            for k in opp_kings:
                kr, kc = k >> 3, k & 7
                for p in my_pieces:
                    pr, pc = p >> 3, p & 7
                    d += max(abs(kr - pr), abs(kc - pc))
            score += 2 * d
    return score if side == 1 else -score


def search(board, side, depth, alpha, beta, ply):
    global nodes
    nodes += 1
    if (nodes & 1023) == 0 and time.time() > deadline:
        raise Timeout()
    moves, is_cap = gen_moves(board, side, MYDIR)
    if not moves:
        return -30000 + ply
    if depth <= 0 and (not is_cap or ply >= 40):
        return evaluate(board, side)
    key = (tuple(board), side)
    entry = TT.get(key)
    tt_move = None
    if entry is not None:
        if entry[0] >= depth:
            flag, val = entry[1], entry[2]
            if flag == 0:
                return val
            if flag == 1 and val >= beta:
                return val
            if flag == 2 and val <= alpha:
                return val
        tt_move = entry[3]
    if is_cap:
        if len(moves) > 1:
            moves.sort(key=lambda m: -len(m[1]))
        nd = depth if len(moves) == 1 else depth - 1
    else:
        nd = depth - 1
    if tt_move is not None and len(moves) > 1:
        for i, m in enumerate(moves):
            if m == tt_move:
                if i:
                    moves[0], moves[i] = moves[i], moves[0]
                break
    orig_alpha = alpha
    best = -INF
    best_move = moves[0]
    for m in moves:
        nb = apply_move(board, m, side, MYDIR)
        v = -search(nb, -side, nd, -beta, -alpha, ply + 1)
        if v > best:
            best = v
            best_move = m
        if v > alpha:
            alpha = v
        if alpha >= beta:
            break
    if best <= orig_alpha:
        flag = 2
    elif best >= beta:
        flag = 1
    else:
        flag = 0
    TT[key] = (depth, flag, best, best_move)
    return best


def _to_rc(sq):
    return (sq >> 3, sq & 7)


def policy(my_men, my_kings, opp_men, opp_kings, color):
    global MYDIR, deadline, nodes, TT, LAST
    start = time.time()
    deadline = start + TIME_BUDGET
    MYDIR = -1 if color == 'b' else 1
    build_pst(MYDIR)
    board = [0] * 64
    for (r, c) in my_men:
        board[r * 8 + c] = 1
    for (r, c) in my_kings:
        board[r * 8 + c] = 2
    for (r, c) in opp_men:
        board[r * 8 + c] = -1
    for (r, c) in opp_kings:
        board[r * 8 + c] = -2

    moves, is_cap = gen_moves(board, 1, MYDIR)
    if not moves:
        LAST = None
        # No legal move exists; return something well-formed.
        if my_men:
            r, c = my_men[0]
            return ((r, c), (r + MYDIR, c + 1))
        if my_kings:
            r, c = my_kings[0]
            return ((r, c), (r + 1, c + 1))
        return ((0, 0), (1, 1))

    # Multi-jump continuation detection
    if is_cap and LAST is not None:
        exp_boards, dest = LAST
        if tuple(board) in exp_boards:
            cont = [m for m in moves if m[0][0] == dest]
            if cont:
                moves = cont

    TT = {}
    nodes = 0
    best_move = moves[0]
    if len(moves) > 1:
        if is_cap:
            moves.sort(key=lambda m: -len(m[1]))
        ordered = moves
        for depth in range(1, 60):
            try:
                alpha = -INF
                cur_best = None
                scores = []
                for m in ordered:
                    nb = apply_move(board, m, 1, MYDIR)
                    v = -search(nb, -1, depth - 1, -INF, -alpha, 1)
                    scores.append((v, m))
                    if v > alpha:
                        alpha = v
                        cur_best = m
                if cur_best is not None:
                    best_move = cur_best
                scores.sort(key=lambda x: -x[0])
                ordered = [m for _, m in scores]
                if alpha > 20000 or alpha < -20000:
                    break
                if time.time() - start > TIME_BUDGET * 0.5:
                    break
            except Timeout:
                break

    path, caps = best_move
    frm, to = path[0], path[1]

    # Record expected state for multi-jump continuation
    if caps:
        v = board[frm]
        b1 = board[:]
        b1[frm] = 0
        b1[caps[0]] = 0
        vv = v
        if v == 1:
            prom_row = 7 if MYDIR == 1 else 0
            if (to >> 3) == prom_row:
                vv = 2
        b1[to] = vv
        b2 = b1[:]
        b2[caps[0]] = board[caps[0]]
        LAST = ({tuple(b1), tuple(b2)}, to)
    else:
        LAST = None

    return (_to_rc(frm), _to_rc(to))
