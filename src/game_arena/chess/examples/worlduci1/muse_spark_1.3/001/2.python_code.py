
import time
import random

INF = 10**9
MATE = 100000

VAL = [0, 100, 320, 330, 500, 900, 0]

PST_P = [
 0,0,0,0,0,0,0,0,
 50,50,50,50,50,50,50,50,
 10,10,20,30,30,20,10,10,
 5,5,10,25,25,10,5,5,
 0,0,0,20,20,0,0,0,
 5,-5,-10,0,0,-10,-5,5,
 5,10,10,-20,-20,10,10,5,
 0,0,0,0,0,0,0,0]
PST_N = [
 -50,-40,-30,-30,-30,-30,-40,-50,
 -40,-20,0,0,0,0,-20,-40,
 -30,0,10,15,15,10,0,-30,
 -30,5,15,20,20,15,5,-30,
 -30,0,15,20,20,15,0,-30,
 -30,5,10,15,15,10,5,-30,
 -40,-20,0,5,5,0,-20,-40,
 -50,-40,-30,-30,-30,-30,-40,-50]
PST_B = [
 -20,-10,-10,-10,-10,-10,-10,-20,
 -10,0,0,0,0,0,0,-10,
 -10,0,5,10,10,5,0,-10,
 -10,5,5,10,10,5,5,-10,
 -10,0,10,10,10,10,0,-10,
 -10,10,10,10,10,10,10,-10,
 -10,5,0,0,0,0,5,-10,
 -20,-10,-10,-10,-10,-10,-10,-20]
PST_R = [
 0,0,0,0,0,0,0,0,
 5,10,10,10,10,10,10,5,
 -5,0,0,0,0,0,0,-5,
 -5,0,0,0,0,0,0,-5,
 -5,0,0,0,0,0,0,-5,
 -5,0,0,0,0,0,0,-5,
 -5,0,0,0,0,0,0,-5,
 0,0,0,5,5,0,0,0]
PST_Q = [
 -20,-10,-10,-5,-5,-10,-10,-20,
 -10,0,0,0,0,0,0,-10,
 -10,0,5,5,5,5,0,-10,
 -5,0,5,5,5,5,0,-5,
 0,0,5,5,5,5,0,-5,
 -10,5,5,5,5,5,0,-10,
 -10,0,5,0,0,0,0,-10,
 -20,-10,-10,-5,-5,-10,-10,-20]
PST_KM = [
 -30,-40,-40,-50,-50,-40,-40,-30,
 -30,-40,-40,-50,-50,-40,-40,-30,
 -30,-40,-40,-50,-50,-40,-40,-30,
 -30,-40,-40,-50,-50,-40,-40,-30,
 -20,-30,-30,-40,-40,-30,-30,-20,
 -10,-20,-20,-20,-20,-20,-20,-10,
 20,20,0,0,0,0,20,20,
 20,30,10,0,0,10,30,20]
PST_KE = [
 -50,-40,-30,-20,-20,-30,-40,-50,
 -30,-20,-10,0,0,-10,-20,-30,
 -30,-10,20,30,30,20,-10,-30,
 -30,-10,30,40,40,30,-10,-30,
 -30,-10,30,40,40,30,-10,-30,
 -30,-10,20,30,30,20,-10,-30,
 -30,-30,0,0,0,0,-30,-30,
 -50,-30,-30,-30,-30,-30,-30,-50]

PST_MAP = [None, PST_P, PST_N, PST_B, PST_R, PST_Q, PST_KM]

KNIGHT_D = [(1,2),(2,1),(2,-1),(1,-2),(-1,-2),(-2,-1),(-2,1),(-1,2)]
KING_D = [(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1),(0,-1),(1,-1)]
ROOK_D = [(1,0),(-1,0),(0,1),(0,-1)]
BISHOP_D = [(1,1),(1,-1),(-1,1),(-1,-1)]

_start = 0.0
_limit = 0.9
_nodes = 0

class TimeUp(Exception):
    pass

def check_time():
    global _nodes
    _nodes += 1
    if (_nodes & 511) == 0:
        if time.perf_counter() - _start > _limit:
            raise TimeUp()

def sq_to_idx(s):
    return (ord(s[0])-97) + (ord(s[1])-49)*8

def idx_to_sq(i):
    return chr((i%8)+97) + chr((i//8)+49)

def uci_to_move(u):
    fr = sq_to_idx(u[0:2])
    to = sq_to_idx(u[2:4])
    pr = 0
    if len(u) > 4:
        c = u[4].lower()
        if c == 'q': pr = 5
        elif c == 'r': pr = 4
        elif c == 'b': pr = 3
        elif c == 'n': pr = 2
        else: pr = 5
    return (fr, to, pr)

def move_to_uci(fr, to, pr):
    s = idx_to_sq(fr) + idx_to_sq(to)
    if pr:
        if pr == 5: s += 'q'
        elif pr == 4: s += 'r'
        elif pr == 3: s += 'b'
        elif pr == 2: s += 'n'
        else: s += 'q'
    return s

def board_from_pieces(pieces):
    b = [0]*64
    for sq, pc in pieces.items():
        try:
            if len(sq) != 2: continue
            f = ord(sq[0])-97
            r = ord(sq[1])-49
            if f < 0 or f > 7 or r < 0 or r > 7: continue
            idx = r*8+f
            if len(pc) != 2: continue
            col = pc[0]
            typ = pc[1]
            if typ not in ('P','N','B','R','Q','K'): continue
            t = {'P':1,'N':2,'B':3,'R':4,'Q':5,'K':6}[typ]
            if col == 'w': b[idx] = t
            elif col == 'b': b[idx] = 6+t
            else: continue
        except: continue
    return b

def find_king(board, color):
    k = 6 + color*6
    for i in range(64):
        if board[i] == k:
            return i
    return -1

def is_attacked(board, sq, att):
    r = sq // 8
    f = sq % 8
    # pawns
    if att == 0:
        rr = r - 1
        if rr >= 0:
            if f-1 >= 0 and board[rr*8+f-1] == 1: return True
            if f+1 <= 7 and board[rr*8+f+1] == 1: return True
    else:
        rr = r + 1
        if rr <= 7:
            if f-1 >= 0 and board[rr*8+f-1] == 7: return True
            if f+1 <= 7 and board[rr*8+f+1] == 7: return True
    # knights
    nk = 2 + att*6
    for df, dr in KNIGHT_D:
        ff = f+df; rrr = r+dr
        if 0 <= ff <= 7 and 0 <= rrr <= 7:
            if board[rrr*8+ff] == nk: return True
    # king
    kk = 6 + att*6
    for df, dr in KING_D:
        ff = f+df; rrr = r+dr
        if 0 <= ff <= 7 and 0 <= rrr <= 7:
            if board[rrr*8+ff] == kk: return True
    # sliders rook/queen orthogonal
    for df, dr in ROOK_D:
        ff = f+df; rrr = r+dr
        while 0 <= ff <= 7 and 0 <= rrr <= 7:
            p = board[rrr*8+ff]
            if p != 0:
                if (p-1)//6 == att:
                    t = (p-1)%6+1
                    if t == 4 or t == 5: return True
                break
            ff += df; rrr += dr
    for df, dr in BISHOP_D:
        ff = f+df; rrr = r+dr
        while 0 <= ff <= 7 and 0 <= rrr <= 7:
            p = board[rrr*8+ff]
            if p != 0:
                if (p-1)//6 == att:
                    t = (p-1)%6+1
                    if t == 3 or t == 5: return True
                break
            ff += df; rrr += dr
    return False

def in_check(board, color):
    k = find_king(board, color)
    if k < 0: return False
    return is_attacked(board, k, 1-color)

def do_make(board, fr, to, promo):
    moved = board[fr]
    cap = board[to]
    cap_ep_idx = -1
    cap_ep_piece = 0
    # en passant: pawn diagonal to empty
    mt = (moved-1)%6+1 if moved else 0
    if mt == 1 and fr%8 != to%8 and cap == 0:
        # diagonal pawn push to empty -> capture adjacent
        ep = (fr//8)*8 + (to%8)
        if board[ep] != 0 and (board[ep]-1)//6 != (moved-1)//6:
            et = (board[ep]-1)%6+1
            if et == 1:
                cap_ep_idx = ep
                cap_ep_piece = board[ep]
                board[ep] = 0
                cap = cap_ep_piece
    # castling rook move
    rook_fr = -1; rook_to = -1
    if mt == 6 and abs((to%8)-(fr%8)) == 2:
        rf = fr//8
        if to%8 == 6: # kingside
            rook_fr = rf*8+7; rook_to = rf*8+5
        elif to%8 == 2: # queenside
            rook_fr = rf*8+0; rook_to = rf*8+3
        else: rook_fr = -1
    undo_rook_piece = 0
    if rook_fr >= 0:
        undo_rook_piece = board[rook_fr]
        board[rook_to] = board[rook_fr]
        board[rook_fr] = 0
    board[fr] = 0
    if promo:
        col = (moved-1)//6
        board[to] = col*6 + promo
    else:
        board[to] = moved
    return (moved, cap, cap_ep_idx, cap_ep_piece, rook_fr, rook_to, undo_rook_piece)

def do_unmake(board, fr, to, promo, undo):
    moved, cap, cap_ep_idx, cap_ep_piece, rook_fr, rook_to, undo_rook_piece = undo
    board[fr] = moved
    # restore rook
    if rook_fr >= 0:
        board[rook_fr] = undo_rook_piece
        board[rook_to] = 0
    if cap_ep_idx >= 0:
        board[to] = 0
        board[cap_ep_idx] = cap_ep_piece
    else:
        board[to] = cap

def gen_pseudo(board, color, captures_only=False):
    moves = []
    for fr in range(64):
        p = board[fr]
        if p == 0: continue
        if (p-1)//6 != color: continue
        t = (p-1)%6+1
        r = fr//8; f = fr%8
        if t == 1:
            dr = 1 if color == 0 else -1
            start = 1 if color == 0 else 6
            last = 7 if color == 0 else 0
            r1 = r+dr
            if 0 <= r1 <= 7:
                to1 = r1*8+f
                if not captures_only:
                    if board[to1] == 0:
                        if r1 == last:
                            for pr in (5,4,3,2):
                                moves.append((fr,to1,pr))
                        else:
                            moves.append((fr,to1,0))
                            if r == start:
                                r2 = r+2*dr
                                to2 = r2*8+f
                                if board[to2] == 0:
                                    moves.append((fr,to2,0))
                # captures
                for df in (-1,1):
                    ff = f+df
                    if 0 <= ff <= 7:
                        toc = r1*8+ff
                        q = board[toc]
                        if q != 0 and (q-1)//6 != color and (q-1)%6+1 != 6:
                            if r1 == last:
                                for pr in (5,4,3,2):
                                    moves.append((fr,toc,pr))
                            else:
                                moves.append((fr,toc,0))
        elif t == 2:
            for df, dr_ in KNIGHT_D:
                ff = f+df; rr = r+dr_
                if 0 <= ff <= 7 and 0 <= rr <= 7:
                    toc = rr*8+ff
                    q = board[toc]
                    if q == 0:
                        if not captures_only: moves.append((fr,toc,0))
                    elif (q-1)//6 != color and (q-1)%6+1 != 6:
                        moves.append((fr,toc,0))
        elif t == 3 or t == 4 or t == 5:
            dirs = ROOK_D if t == 4 else (BISHOP_D if t == 3 else ROOK_D+BISHOP_D)
            for df, dr_ in dirs:
                ff = f+df; rr = r+dr_
                while 0 <= ff <= 7 and 0 <= rr <= 7:
                    toc = rr*8+ff
                    q = board[toc]
                    if q == 0:
                        if not captures_only: moves.append((fr,toc,0))
                    else:
                        if (q-1)//6 != color and (q-1)%6+1 != 6:
                            moves.append((fr,toc,0))
                        break
                    ff += df; rr += dr_
        elif t == 6:
            for df, dr_ in KING_D:
                ff = f+df; rr = r+dr_
                if 0 <= ff <= 7 and 0 <= rr <= 7:
                    toc = rr*8+ff
                    q = board[toc]
                    if q == 0:
                        if not captures_only: moves.append((fr,toc,0))
                    elif (q-1)//6 != color and (q-1)%6+1 != 6:
                        moves.append((fr,toc,0))
            if not captures_only:
                # castling optimistic
                if color == 0 and fr == 4:
                    # kingside
                    if board[7] == 4 and board[5] == 0 and board[6] == 0:
                        if not is_attacked(board,4,1) and not is_attacked(board,5,1) and not is_attacked(board,6,1):
                            moves.append((fr,6,0))
                    if board[0] == 4 and board[1] == 0 and board[2] == 0 and board[3] == 0:
                        if not is_attacked(board,4,1) and not is_attacked(board,3,1) and not is_attacked(board,2,1):
                            moves.append((fr,2,0))
                if color == 1 and fr == 60:
                    if board[63] == 10 and board[61] == 0 and board[62] == 0:
                        if not is_attacked(board,60,0) and not is_attacked(board,61,0) and not is_attacked(board,62,0):
                            moves.append((fr,62,0))
                    if board[56] == 10 and board[57] == 0 and board[58] == 0 and board[59] == 0:
                        if not is_attacked(board,60,0) and not is_attacked(board,59,0) and not is_attacked(board,58,0):
                            moves.append((fr,58,0))
    return moves

def gen_legal(board, color, captures_only=False):
    pseudo = gen_pseudo(board, color, captures_only)
    legal = []
    for (fr,to,pr) in pseudo:
        u = do_make(board, fr, to, pr)
        k = find_king(board, color)
        ok = True
        if k >= 0 and is_attacked(board, k, 1-color):
            ok = False
        do_unmake(board, fr, to, pr, u)
        if ok:
            legal.append((fr,to,pr))
    return legal

def evaluate(board):
    score = 0
    wB = 0; bB = 0
    wQ = 0; bQ = 0
    tot = 0
    for i in range(64):
        p = board[i]
        if p == 0: continue
        col = (p-1)//6
        t = (p-1)%6+1
        r = i//8; f = i%8
        if t == 3:
            if col == 0: wB += 1
            else: bB += 1
        if t == 5:
            if col == 0: wQ += 1
            else: bQ += 1
        if t != 1 and t != 6:
            tot += VAL[t]
    endgame = False
    if wQ + bQ == 0: endgame = True
    elif tot <= 2600: endgame = True
    for i in range(64):
        p = board[i]
        if p == 0: continue
        col = (p-1)//6
        t = (p-1)%6+1
        r = i//8; f = i%8
        if col == 0:
            ti = (7-r)*8+f
            tab = PST_KE if (t == 6 and endgame) else PST_MAP[t]
            score += VAL[t] + tab[ti]
        else:
            ti = r*8+f
            tab = PST_KE if (t == 6 and endgame) else PST_MAP[t]
            score -= VAL[t] + tab[ti]
    if wB >= 2: score += 30
    if bB >= 2: score -= 30
    return score

def move_order_score(board, fr, to, pr):
    cap = board[to]
    s = 0
    if cap != 0:
        vt = (cap-1)%6+1
        at = (board[fr]-1)%6+1
        s = 10000 + VAL[vt]*10 - VAL[at]
    # ep capture to empty diagonal pawn
    elif (board[fr]-1)%6+1 == 1 and fr%8 != to%8:
        s = 10000 + 100*10 - 100
    if pr:
        s += 9000 + VAL[pr]
    else:
        # centralize a bit
        tf = to%8; tr = to//8
        s += (3 - abs(3.5-0.5-tf) - abs(3.5-0.5-tr))*2 if False else 0
    return s

def quiesce(board, color, alpha, beta, ply):
    check_time()
    ic = in_check(board, color)
    if ic:
        legal = gen_legal(board, color, False)
        if not legal:
            return -MATE + ply
        # order
        legal.sort(key=lambda m: move_order_score(board, m[0], m[1], m[2]), reverse=True)
        for (fr,to,pr) in legal:
            u = do_make(board, fr, to, pr)
            sc = -quiesce(board, 1-color, -beta, -alpha, ply+1)
            do_unmake(board, fr, to, pr, u)
            if sc >= beta: return beta
            if sc > alpha: alpha = sc
        return alpha
    # stand pat
    ev = evaluate(board)
    sc_std = ev if color == 0 else -ev
    if sc_std >= beta: return beta
    if sc_std > alpha: alpha = sc_std
    if ply > 12: return alpha
    caps = gen_legal(board, color, True)
    if not caps: return alpha
    caps.sort(key=lambda m: move_order_score(board, m[0], m[1], m[2]), reverse=True)
    for (fr,to,pr) in caps:
        u = do_make(board, fr, to, pr)
        sc = -quiesce(board, 1-color, -beta, -alpha, ply+1)
        do_unmake(board, fr, to, pr, u)
        if sc >= beta: return beta
        if sc > alpha: alpha = sc
    return alpha

def negamax(board, color, depth, alpha, beta, ply):
    check_time()
    ic = in_check(board, color)
    if depth <= 0:
        return quiesce(board, color, alpha, beta, ply)
    # null move pruning
    if depth >= 3 and not ic and ply > 0:
        ev = evaluate(board)
        se = ev if color == 0 else -ev
        if se >= beta:
            try:
                ns = -negamax(board, 1-color, depth-3, -beta, -beta+1, ply+1)
                if ns >= beta:
                    return beta
            except TimeUp:
                raise
    legal = gen_legal(board, color, False)
    if not legal:
        if ic: return -MATE + ply
        else: return 0
    # order: try captures first; simple sort
    # score with static ordering
    scored = []
    for m in legal:
        scored.append((move_order_score(board, m[0], m[1], m[2]), m))
    scored.sort(key=lambda x: x[0], reverse=True)
    best = -INF
    for _, (fr,to,pr) in scored:
        u = do_make(board, fr, to, pr)
        ext = 1 if in_check(board, 1-color) or ic else 0
        # limit extension to avoid explosion: only when depth small? allow
        nd = depth - 1 + (ext if depth < 4 else 0)
        try:
            sc = -negamax(board, 1-color, nd, -beta, -alpha, ply+1)
        except TimeUp:
            do_unmake(board, fr, to, pr, u)
            raise
        do_unmake(board, fr, to, pr, u)
        if sc > best: best = sc
        if sc > alpha: alpha = sc
        if alpha >= beta: break
    return best

def policy(pieces, to_play, legal_moves=None, *args, **kwargs):
    global _start, _limit, _nodes
    try:
        # support alternative call conventions
        if legal_moves is not None and not isinstance(legal_moves, list):
            # maybe called with different signature, ignore
            legal_moves = None
        # also check kwargs
        if legal_moves is None and 'legal_moves' in kwargs:
            lm = kwargs['legal_moves']
            if isinstance(lm, list): legal_moves = lm
        # time setup
        _start = time.perf_counter()
        _limit = 0.90
        _nodes = 0
        col = 0 if (to_play == 'white' or to_play == 'w' or to_play == 0) else 1
        # handle to_play as color int already?
        board = board_from_pieces(pieces)
        # determine root UCI list
        root_uci = None
        if isinstance(legal_moves, list) and len(legal_moves) > 0:
            # filter strings
            root_uci = [m for m in legal_moves if isinstance(m, str) and len(m) >= 4]
            if not root_uci:
                root_uci = None
        if root_uci is None:
            # generate
            leg = gen_legal(board, col, False)
            if not leg:
                return "0000"
            if len(leg) == 1:
                return move_to_uci(*leg[0])
            root_uci = [move_to_uci(*m) for m in leg]
        if len(root_uci) == 1:
            return root_uci[0]
        # quick mate in 1 check
        # order root by static heuristic first
        root_moves = []
        for u in root_uci:
            try:
                fr, to, pr = uci_to_move(u)
                s = move_order_score(board, fr, to, pr)
                # small eval bonus after move? center/promotion
                root_moves.append((s, u, fr, to, pr))
            except:
                root_moves.append((0, u, None, None, None))
        root_moves.sort(key=lambda x: x[0], reverse=True)
        # iterative deepening
        best_uci = root_moves[0][1]
        # try depth 1..5
        max_depth = 5
        # adjust by branching: if many moves, limit depth
        if len(root_uci) > 35:
            max_depth = 4
        for depth in range(1, max_depth+1):
            try:
                alpha = -INF
                beta = INF
                cur_best = best_uci
                cur_best_score = -INF
                # search each root move
                scores = []
                for _, u, fr, to, pr in root_moves:
                    if fr is None:
                        fr2, to2, pr2 = uci_to_move(u)
                    else:
                        fr2, to2, pr2 = fr, to, pr
                    # make on board; handle illegal root moves gracefully (skip if king missing issue?)
                    # need to ensure fr2/to2 in range
                    if fr2 < 0 or fr2 > 63 or to2 < 0 or to2 > 63:
                        continue
                    undo = do_make(board, fr2, to2, pr2)
                    # if move leaves king in check, it's illegal -> give -INF (should not happen for provided list)
                    # but don't prune: still allow? check
                    k = find_king(board, col)
                    illegal = False
                    if k >= 0 and is_attacked(board, k, 1-col):
                        illegal = True
                    if illegal:
                        do_unmake(board, fr2, to2, pr2, undo)
                        scores.append((-INF-1000, u, fr, to, pr))
                        continue
                    # immediate mate detection: if opponent has no moves and in check -> mate
                    sc = -negamax(board, 1-col, depth-1, -beta, -alpha, 1)
                    do_unmake(board, fr2, to2, pr2, undo)
                    scores.append((sc, u, fr, to, pr))
                    if sc > cur_best_score:
                        cur_best_score = sc
                        cur_best = u
                    if sc > alpha:
                        alpha = sc
                    # early exit on mate found
                    if cur_best_score >= MATE - 50:
                        break
                # reorder for next iteration
                scores.sort(key=lambda x: x[0], reverse=True)
                # update root_moves order
                root_moves = [(s, u, fr, to, pr) for (s, u, fr, to, pr) in scores]
                best_uci = cur_best
                # if found forced mate, stop
                if cur_best_score >= MATE - 100:
                    break
                # if time low, stop
                if time.perf_counter() - _start > _limit - 0.08:
                    break
            except TimeUp:
                break
        return best_uci
    except Exception:
        try:
            if isinstance(legal_moves, list) and len(legal_moves) > 0:
                return legal_moves[0]
        except: pass
        try:
            # fallback generate one
            col2 = 0 if (to_play == 'white' or to_play == 'w') else 1
            b2 = board_from_pieces(pieces)
            lg = gen_legal(b2, col2, False)
            if lg:
                return move_to_uci(*lg[0])
        except: pass
        return "0000"
