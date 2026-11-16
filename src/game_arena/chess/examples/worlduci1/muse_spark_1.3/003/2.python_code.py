
import time
import random

VALS = [0, 100, 320, 330, 500, 900, 0]
INF = 1000000
MATE = 100000

P_PST = [0,0,0,0,0,0,0,0,50,50,50,50,50,50,50,50,10,10,20,30,30,20,10,10,5,5,10,25,25,10,5,5,0,0,0,20,20,0,0,0,5,-5,-10,0,0,-10,-5,5,5,10,10,-20,-20,10,10,5,0,0,0,0,0,0,0,0]
N_PST = [-50,-40,-30,-30,-30,-30,-40,-50,-40,-20,0,0,0,0,-20,-40,-30,0,10,15,15,10,0,-30,-30,5,15,20,20,15,5,-30,-30,0,15,20,20,15,0,-30,-30,5,10,15,15,10,5,-30,-40,-20,0,5,5,0,-20,-40,-50,-40,-30,-30,-30,-30,-40,-50]
B_PST = [-20,-10,-10,-10,-10,-10,-10,-20,-10,0,0,0,0,0,0,-10,-10,0,5,10,10,5,0,-10,-10,5,5,10,10,5,5,-10,-10,0,10,10,10,10,0,-10,-10,10,10,10,10,10,10,-10,-10,5,0,0,0,0,5,-10,-20,-10,-10,-10,-10,-10,-10,-20]
R_PST = [0,0,0,0,0,0,0,0,5,10,10,10,10,10,10,5,-5,0,0,0,0,0,0,-5,-5,0,0,0,0,0,0,-5,-5,0,0,0,0,0,0,-5,-5,0,0,0,0,0,0,-5,-5,0,0,0,0,0,0,-5,0,0,0,5,5,0,0,0]
Q_PST = [-20,-10,-10,-5,-5,-10,-10,-20,-10,0,0,0,0,0,0,-10,-10,0,5,5,5,5,0,-10,-5,0,5,5,5,5,0,-5,0,0,5,5,5,5,0,-5,-10,5,5,5,5,5,0,-10,-10,0,5,0,0,0,0,-10,-20,-10,-10,-5,-5,-10,-10,-20]
K_PST = [-30,-40,-40,-50,-50,-40,-40,-30,-30,-40,-40,-50,-50,-40,-40,-30,-30,-40,-40,-50,-50,-40,-40,-30,-30,-40,-40,-50,-50,-40,-40,-30,-20,-30,-30,-40,-40,-30,-30,-20,-10,-20,-20,-20,-20,-20,-20,-10,20,20,0,0,0,0,20,20,20,30,10,0,0,10,30,20]
KE_PST = [-50,-40,-30,-20,-20,-30,-40,-50,-30,-20,-10,0,0,-10,-20,-30,-30,-10,20,30,30,20,-10,-30,-30,-10,30,40,40,30,-10,-30,-30,-10,30,40,40,30,-10,-30,-30,-10,20,30,30,20,-10,-30,-30,-30,0,0,0,0,-30,-30,-50,-30,-30,-30,-30,-30,-30,-50]
PSTS = [None, P_PST, N_PST, B_PST, R_PST, Q_PST, K_PST]

_deadline = 0.0
_nodes = 0

class _Timeout(Exception):
    pass

def _check_time():
    global _nodes
    _nodes += 1
    if (_nodes & 1023) == 0:
        if time.perf_counter() > _deadline:
            raise _Timeout()

def _idx(f, r):
    return r * 8 + f

def _uci_of(fr, to, promo):
    s = chr(fr % 8 + 97) + str(fr // 8 + 1) + chr(to % 8 + 97) + str(to // 8 + 1)
    if promo:
        s += {5: 'q', 4: 'r', 3: 'b', 2: 'n'}[promo]
    return s

def _parse_uci(u):
    try:
        fr = (ord(u[0]) - 97) + (int(u[1]) - 1) * 8
        to = (ord(u[2]) - 97) + (int(u[3]) - 1) * 8
        promo = 0
        if len(u) > 4:
            c = u[4].lower()
            if c == 'q':
                promo = 5
            elif c == 'r':
                promo = 4
            elif c == 'b':
                promo = 3
            elif c == 'n':
                promo = 2
            else:
                promo = 5
        return fr, to, promo
    except Exception:
        return None

def _is_attacked(board, sq, by_white):
    f = sq & 7
    r = sq >> 3
    if by_white:
        if r > 0:
            if f > 0 and board[sq - 9] == 1:
                return True
            if f < 7 and board[sq - 7] == 1:
                return True
    else:
        if r < 7:
            if f > 0 and board[sq + 7] == -1:
                return True
            if f < 7 and board[sq + 9] == -1:
                return True
    # knights
    for df, dr in ((1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2)):
        nf = f + df
        nr = r + dr
        if 0 <= nf < 8 and 0 <= nr < 8:
            v = board[nr * 8 + nf]
            if v != 0 and (v > 0) == by_white and abs(v) == 2:
                return True
    # king
    for df in (-1, 0, 1):
        for dr in (-1, 0, 1):
            if df == 0 and dr == 0:
                continue
            nf = f + df
            nr = r + dr
            if 0 <= nf < 8 and 0 <= nr < 8:
                v = board[nr * 8 + nf]
                if v != 0 and (v > 0) == by_white and abs(v) == 6:
                    return True
    # orthogonal sliders
    for df, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nf = f + df
        nr = r + dr
        while 0 <= nf < 8 and 0 <= nr < 8:
            v = board[nr * 8 + nf]
            if v != 0:
                if (v > 0) == by_white:
                    a = abs(v)
                    if a == 4 or a == 5:
                        return True
                break
            nf += df
            nr += dr
    # diagonal sliders
    for df, dr in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        nf = f + df
        nr = r + dr
        while 0 <= nf < 8 and 0 <= nr < 8:
            v = board[nr * 8 + nf]
            if v != 0:
                if (v > 0) == by_white:
                    a = abs(v)
                    if a == 3 or a == 5:
                        return True
                break
            nf += df
            nr += dr
    return False

def _find_king(board, white):
    k = 6 if white else -6
    for i in range(64):
        if board[i] == k:
            return i
    return -1

def _in_check(board, white):
    ksq = _find_king(board, white)
    if ksq < 0:
        return False
    return _is_attacked(board, ksq, not white)

def _do_move(board, fr, to, promo):
    moving = board[fr]
    captured = board[to]
    extra = None
    # castling: king moves 2
    if abs(moving) == 6 and abs((to & 7) - (fr & 7)) == 2:
        if to > fr:
            rf = fr + 3
            rt = fr + 1
        else:
            rf = fr - 4
            rt = fr - 1
        rook = board[rf]
        board[rt] = rook
        board[rf] = 0
        board[to] = moving
        board[fr] = 0
        extra = ('c', rf, rt)
        return captured, moving, extra
    # en passant: pawn diagonal to empty
    if abs(moving) == 1 and (to & 7) != (fr & 7) and captured == 0:
        epsq = (fr >> 3) * 8 + (to & 7)
        epc = board[epsq]
        if epc != 0 and abs(epc) == 1 and (epc > 0) != (moving > 0):
            board[epsq] = 0
            board[to] = moving
            board[fr] = 0
            extra = ('e', epsq, epc)
            return captured, moving, extra
    if promo:
        board[to] = promo if moving > 0 else -promo
        board[fr] = 0
    else:
        board[to] = moving
        board[fr] = 0
    return captured, moving, extra

def _undo_move(board, fr, to, promo, captured, moving, extra):
    if extra is not None:
        if extra[0] == 'c':
            _, rf, rt = extra
            board[rf] = board[rt]
            board[rt] = 0
            board[fr] = moving
            board[to] = captured
            return
        elif extra[0] == 'e':
            _, epsq, epc = extra
            board[fr] = moving
            board[to] = 0
            board[epsq] = epc
            return
    board[fr] = moving
    board[to] = captured

def _gen_pseudo(board, white):
    moves = []
    for fr in range(64):
        p = board[fr]
        if p == 0 or (p > 0) != white:
            continue
        t = abs(p)
        f = fr & 7
        r = fr >> 3
        if t == 1:
            d = 1 if white else -1
            nr = r + d
            if 0 <= nr < 8:
                to = nr * 8 + f
                if board[to] == 0:
                    if nr == 7 or nr == 0:
                        for pr in (5, 4, 3, 2):
                            moves.append((fr, to, pr))
                    else:
                        moves.append((fr, to, 0))
                    sr = 1 if white else 6
                    if r == sr:
                        to2 = (r + 2 * d) * 8 + f
                        if board[to2] == 0:
                            moves.append((fr, to2, 0))
                for df in (-1, 1):
                    nf = f + df
                    if 0 <= nf < 8:
                        to = nr * 8 + nf
                        v = board[to]
                        if v != 0 and (v > 0) != white and abs(v) != 6:
                            if nr == 7 or nr == 0:
                                for pr in (5, 4, 3, 2):
                                    moves.append((fr, to, pr))
                            else:
                                moves.append((fr, to, 0))
        elif t == 2:
            for df, dr in ((1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2)):
                nf = f + df
                nr = r + dr
                if 0 <= nf < 8 and 0 <= nr < 8:
                    to = nr * 8 + nf
                    v = board[to]
                    if v == 0 or ((v > 0) != white and abs(v) != 6):
                        moves.append((fr, to, 0))
        elif t == 6:
            for df in (-1, 0, 1):
                for dr in (-1, 0, 1):
                    if df == 0 and dr == 0:
                        continue
                    nf = f + df
                    nr = r + dr
                    if 0 <= nf < 8 and 0 <= nr < 8:
                        to = nr * 8 + nf
                        v = board[to]
                        if v == 0 or ((v > 0) != white and abs(v) != 6):
                            moves.append((fr, to, 0))
        else:
            dirs = []
            if t == 3 or t == 5:
                dirs += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
            if t == 4 or t == 5:
                dirs += [(1, 0), (-1, 0), (0, 1), (0, -1)]
            for df, dr in dirs:
                nf = f + df
                nr = r + dr
                while 0 <= nf < 8 and 0 <= nr < 8:
                    to = nr * 8 + nf
                    v = board[to]
                    if v == 0:
                        moves.append((fr, to, 0))
                    else:
                        if (v > 0) != white and abs(v) != 6:
                            moves.append((fr, to, 0))
                        break
                    nf += df
                    nr += dr
    return moves

def _gen_legal(board, white):
    pseudos = _gen_pseudo(board, white)
    legal = []
    for fr, to, promo in pseudos:
        cap, mov, ext = _do_move(board, fr, to, promo)
        ksq = _find_king(board, white)
        ok = True
        if ksq >= 0:
            if _is_attacked(board, ksq, not white):
                ok = False
        _undo_move(board, fr, to, promo, cap, mov, ext)
        if ok:
            legal.append((fr, to, promo))
    return legal

def _evaluate(board):
    # decide endgame for king pst
    mat = 0
    for v in board:
        if v != 0 and abs(v) != 6:
            mat += VALS[abs(v)]
    endgame = mat <= 1300
    s = 0
    for i in range(64):
        v = board[i]
        if v == 0:
            continue
        a = abs(v)
        f = i & 7
        r = i >> 3
        if v > 0:
            ti = (7 - r) * 8 + f
            s += VALS[a]
            if a == 6:
                s += (KE_PST[ti] if endgame else K_PST[ti])
            else:
                s += PSTS[a][ti]
        else:
            ti = r * 8 + f
            s -= VALS[a]
            if a == 6:
                s -= (KE_PST[ti] if endgame else K_PST[ti])
            else:
                s -= PSTS[a][ti]
    return s

def _order_moves(board, moves):
    scored = []
    for fr, to, promo in moves:
        mv = board[fr]
        cap = board[to]
        sc = 0
        if cap != 0:
            sc = 10 * VALS[abs(cap)] - VALS[abs(mv)]
        if promo:
            sc += 900 if promo == 5 else 500
            if cap != 0:
                sc += 500
        # centralize slightly, promotion already
        sc += 0
        scored.append((sc, fr, to, promo))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [(fr, to, pr) for _, fr, to, pr in scored]

def _qsearch(board, alpha, beta, white, ply, qd):
    _check_time()
    in_chk = _in_check(board, white)
    if not in_chk:
        stand = _evaluate(board) if white else -_evaluate(board)
        if stand >= beta:
            return beta
        if stand > alpha:
            alpha = stand
        if qd <= 0:
            return alpha
    else:
        if qd <= -2:
            # avoid explosion, static
            pass
    legal = _gen_legal(board, white)
    if not legal:
        if in_chk:
            return -MATE + ply
        return 0
    if in_chk:
        ordered = _order_moves(board, legal)
    else:
        caps = []
        for fr, to, pr in legal:
            if board[to] != 0 or pr != 0:
                caps.append((fr, to, pr))
        if not caps:
            return alpha
        ordered = _order_moves(board, caps)
    for fr, to, pr in ordered:
        cap, mov, ext = _do_move(board, fr, to, pr)
        val = -_qsearch(board, -beta, -alpha, not white, ply + 1, qd - 1)
        _undo_move(board, fr, to, pr, cap, mov, ext)
        if val >= beta:
            return beta
        if val > alpha:
            alpha = val
    return alpha

def _negamax(board, depth, alpha, beta, white, ply):
    _check_time()
    if depth <= 0:
        return _qsearch(board, alpha, beta, white, ply, 3)
    legal = _gen_legal(board, white)
    if not legal:
        if _in_check(board, white):
            return -MATE + ply
        return 0
    ordered = _order_moves(board, legal)
    best = -INF
    for fr, to, pr in ordered:
        cap, mov, ext = _do_move(board, fr, to, pr)
        val = -_negamax(board, depth - 1, -beta, -alpha, not white, ply + 1)
        _undo_move(board, fr, to, pr, cap, mov, ext)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best

def policy(pieces, to_play, legal_moves=None):
    global _deadline, _nodes
    start = time.perf_counter()
    _deadline = start + 0.88
    _nodes = 0
    try:
        white = str(to_play).lower().startswith('w')
        board = [0] * 64
        tm = {'P': 1, 'N': 2, 'B': 3, 'R': 4, 'Q': 5, 'K': 6}
        for sq, code in pieces.items():
            try:
                f = ord(sq[0]) - 97
                r = int(sq[1]) - 1
                if not (0 <= f < 8 and 0 <= r < 8):
                    continue
                idx = r * 8 + f
                c = code[0]
                t = code[1]
                v = tm.get(t, 0)
                if v == 0:
                    continue
                board[idx] = v if c == 'w' else -v
            except Exception:
                continue
        # obtain root UCI list
        root_uci = None
        if legal_moves is not None:
            try:
                if len(legal_moves) > 0:
                    root_uci = list(legal_moves)
            except Exception:
                root_uci = None
        if root_uci is None or len(root_uci) == 0:
            leg = _gen_legal(board, white)
            if not leg:
                # no moves: return something (game over) - fallback
                return '0000'
            root_uci = [_uci_of(fr, to, pr) for fr, to, pr in leg]
        if len(root_uci) == 1:
            return root_uci[0]
        # parse root
        root_moves = []
        for u in root_uci:
            pu = _parse_uci(u)
            if pu is None:
                continue
            root_moves.append((pu[0], pu[1], pu[2], u))
        if not root_moves:
            leg = _gen_legal(board, white)
            if not leg:
                return root_uci[0]
            return _uci_of(leg[0][0], leg[0][1], leg[0][2])
        # quick ordering by MVV-LVA + eval
        def _root_score(fr, to, pr):
            cap = board[to]
            sc = 0
            if cap != 0:
                mv = board[fr]
                sc = 10 * VALS[abs(cap)] - (VALS[abs(mv)] if mv != 0 else 0)
            if pr:
                sc += 800
            return sc
        root_moves.sort(key=lambda x: _root_score(x[0], x[1], x[2]), reverse=True)
        # iterative deepening
        # adjust max depth by piece count
        cnt = sum(1 for v in board if v != 0)
        max_depth = 5 if cnt <= 10 else (4 if cnt <= 20 else 3)
        best_uci = root_moves[0][3]
        # try depth 1..max
        ordered = root_moves
        for depth in range(1, max_depth + 1):
            alpha = -INF
            beta = INF
            cur_best = None
            cur_best_val = -INF
            # search each root move
            for fr, to, pr, u in ordered:
                cap, mov, ext = _do_move(board, fr, to, pr)
                try:
                    val = -_negamax(board, depth - 1, -beta, -alpha, not white, 1)
                except _Timeout:
                    _undo_move(board, fr, to, pr, cap, mov, ext)
                    raise
                _undo_move(board, fr, to, pr, cap, mov, ext)
                if val > cur_best_val:
                    cur_best_val = val
                    cur_best = (fr, to, pr, u, val)
                if val > alpha:
                    alpha = val
            # completed depth
            if cur_best is not None:
                best_uci = cur_best[3]
                # reorder by value for next iteration
                # re-evaluate ordering: need scores for all; do simple: move best to front
                # To get full ordering, we would need values; approximate by keeping best first
                # Re-sort using quick 1-ply re-search? Keep simple: put best first
                new_order = [m for m in ordered if m[3] == best_uci] + [m for m in ordered if m[3] != best_uci]
                ordered = new_order
                if cur_best_val >= MATE - 1000:
                    break
            if time.perf_counter() > _deadline - 0.05:
                break
        return best_uci
    except _Timeout:
        # return best so far if available
        try:
            if 'best_uci' in locals() and best_uci is not None:
                return best_uci
        except Exception:
            pass
        try:
            if legal_moves is not None and len(legal_moves) > 0:
                return legal_moves[0]
        except Exception:
            pass
        try:
            leg = _gen_legal(board, white)  # type: ignore
            if leg:
                return _uci_of(leg[0][0], leg[0][1], leg[0][2])
        except Exception:
            pass
        return '0000'
    except Exception:
        try:
            if legal_moves is not None and len(legal_moves) > 0:
                return legal_moves[0]
        except Exception:
            pass
        try:
            # last resort generate
            white2 = str(to_play).lower().startswith('w')
            b2 = [0] * 64
            tm2 = {'P': 1, 'N': 2, 'B': 3, 'R': 4, 'Q': 5, 'K': 6}
            for sq, code in pieces.items():
                try:
                    f = ord(sq[0]) - 97
                    r = int(sq[1]) - 1
                    idx = r * 8 + f
                    b2[idx] = tm2[code[1]] if code[0] == 'w' else -tm2[code[1]]
                except Exception:
                    continue
            leg = _gen_legal(b2, white2)
            if leg:
                return _uci_of(leg[0][0], leg[0][1], leg[0][2])
        except Exception:
            pass
        return '0000'
