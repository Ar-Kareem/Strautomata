
import time
import random

MATE = 100000
VALS = [0, 100, 320, 330, 500, 900, 0]

P_PST = [0,0,0,0,0,0,0,0,50,50,50,50,50,50,50,50,10,10,20,30,30,20,10,10,5,5,10,25,25,10,5,5,0,0,0,20,20,0,0,0,5,-5,-10,0,0,-10,-5,5,5,10,10,-20,-20,10,10,5,0,0,0,0,0,0,0,0]
N_PST = [-50,-40,-30,-30,-30,-30,-40,-50,-40,-20,0,0,0,0,-20,-40,-30,0,10,15,15,10,0,-30,-30,5,15,20,20,15,5,-30,-30,0,15,20,20,15,0,-30,-30,5,10,15,15,10,5,-30,-40,-20,0,5,5,0,-20,-40,-50,-40,-30,-30,-30,-30,-40,-50]
B_PST = [-20,-10,-10,-10,-10,-10,-10,-20,-10,0,0,0,0,0,0,-10,-10,0,5,10,10,5,0,-10,-10,5,5,10,10,5,5,-10,-10,0,10,10,10,10,0,-10,-10,10,10,10,10,10,10,-10,-10,5,0,0,0,0,5,-10,-20,-10,-10,-10,-10,-10,-10,-20]
R_PST = [0,0,0,0,0,0,0,0,5,10,10,10,10,10,10,5,-5,0,0,0,0,0,0,-5,-5,0,0,0,0,0,0,-5,-5,0,0,0,0,0,0,-5,-5,0,0,0,0,0,0,-5,-5,0,0,0,0,0,0,-5,0,0,0,5,5,0,0,0]
Q_PST = [-20,-10,-10,-5,-5,-10,-10,-20,-10,0,0,0,0,0,0,-10,-10,0,5,5,5,5,0,-10,-5,0,5,5,5,5,0,-5,0,0,5,5,5,5,0,-5,-10,5,5,5,5,5,0,-10,-10,0,5,0,0,0,0,-10,-20,-10,-10,-5,-5,-10,-10,-20]
K_MID = [-30,-40,-40,-50,-50,-40,-40,-30,-30,-40,-40,-50,-50,-40,-40,-30,-30,-40,-40,-50,-50,-40,-40,-30,-30,-40,-40,-50,-50,-40,-40,-30,-20,-30,-30,-40,-40,-30,-30,-20,-10,-20,-20,-20,-20,-20,-20,-10,20,20,0,0,0,0,20,20,20,30,10,0,0,10,30,20]
K_END = [-50,-40,-30,-20,-20,-30,-40,-50,-30,-20,-10,0,0,-10,-20,-30,-30,-10,20,30,30,20,-10,-30,-30,-10,30,40,40,30,-10,-30,-30,-10,30,40,40,30,-10,-30,-30,-10,20,30,30,20,-10,-30,-30,-30,0,0,0,0,-30,-30,-50,-30,-30,-30,-30,-30,-30,-50]

KNIGHT_OFF = [(2,1),(1,2),(-1,2),(-2,1),(-2,-1),(-1,-2),(1,-2),(2,-1)]
KING_OFF = [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]
BISHOP_DIR = [(1,1),(1,-1),(-1,1),(-1,-1)]
ROOK_DIR = [(1,0),(-1,0),(0,1),(0,-1)]

class _TO(Exception):
    pass

_nodes = 0
_deadline = 0.0

def _idx_to_uci_fr_to(fr, to, promo):
    f1 = fr % 8; r1 = fr // 8
    f2 = to % 8; r2 = to // 8
    s = chr(97+f1) + str(r1+1) + chr(97+f2) + str(r2+1)
    if promo:
        if promo == 5: s += 'q'
        elif promo == 4: s += 'r'
        elif promo == 3: s += 'b'
        elif promo == 2: s += 'n'
        else: s += 'q'
    return s

def _parse_uci(u):
    try:
        u = u.strip().lower()
        if len(u) < 4:
            return None
        f1 = ord(u[0])-97; r1 = int(u[1])-1
        f2 = ord(u[2])-97; r2 = int(u[3])-1
        if not (0 <= f1 < 8 and 0 <= r1 < 8 and 0 <= f2 < 8 and 0 <= r2 < 8):
            return None
        fr = r1*8+f1; to = r2*8+f2
        promo = 0
        if len(u) > 4:
            c = u[4]
            if c == 'q': promo = 5
            elif c == 'r': promo = 4
            elif c == 'b': promo = 3
            elif c == 'n': promo = 2
            else: promo = 0
        return (fr, to, promo)
    except:
        return None

def _find_king(board, color):
    k = 6*color
    for i, p in enumerate(board):
        if p == k:
            return i
    return -1

def _is_attacked(board, sq, attacker):
    f = sq % 8; r = sq // 8
    if attacker == 1:
        pr = r - 1
        if pr >= 0:
            if f-1 >= 0 and board[pr*8+f-1] == 1:
                return True
            if f+1 < 8 and board[pr*8+f+1] == 1:
                return True
    else:
        pr = r + 1
        if pr < 8:
            if f-1 >= 0 and board[pr*8+f-1] == -1:
                return True
            if f+1 < 8 and board[pr*8+f+1] == -1:
                return True
    nk = 2*attacker
    for dr, df in KNIGHT_OFF:
        nr = r+dr; nf = f+df
        if 0 <= nr < 8 and 0 <= nf < 8:
            if board[nr*8+nf] == nk:
                return True
    kk = 6*attacker
    for dr, df in KING_OFF:
        nr = r+dr; nf = f+df
        if 0 <= nr < 8 and 0 <= nf < 8:
            if board[nr*8+nf] == kk:
                return True
    for dr, df in BISHOP_DIR:
        nr = r+dr; nf = f+df
        while 0 <= nr < 8 and 0 <= nf < 8:
            p = board[nr*8+nf]
            if p != 0:
                if p*attacker > 0:
                    t = abs(p)
                    if t == 3 or t == 5:
                        return True
                break
            nr += dr; nf += df
    for dr, df in ROOK_DIR:
        nr = r+dr; nf = f+df
        while 0 <= nr < 8 and 0 <= nf < 8:
            p = board[nr*8+nf]
            if p != 0:
                if p*attacker > 0:
                    t = abs(p)
                    if t == 4 or t == 5:
                        return True
                break
            nr += dr; nf += df
    return False

def _in_check(board, color):
    k = _find_king(board, color)
    if k < 0:
        return False
    return _is_attacked(board, k, -color)

def _gen_pseudo(board, color):
    moves = []
    for fr in range(64):
        pc = board[fr]
        if pc == 0 or (pc*color) <= 0:
            continue
        t = abs(pc)
        f = fr % 8; r = fr // 8
        if t == 1:
            d = 1 if color == 1 else -1
            nr = r + d
            if 0 <= nr < 8:
                fwd = nr*8+f
                if board[fwd] == 0:
                    pro = (nr == 7 and color == 1) or (nr == 0 and color == -1)
                    if pro:
                        for pr in (5,4,3,2):
                            moves.append((fr,fwd,pr))
                    else:
                        moves.append((fr,fwd,0))
                        sr = 1 if color == 1 else 6
                        if r == sr:
                            fwd2 = (r+2*d)*8+f
                            if board[fwd2] == 0:
                                moves.append((fr,fwd2,0))
                for df in (-1,1):
                    nf = f+df
                    if 0 <= nf < 8:
                        to = nr*8+nf
                        tgt = board[to]
                        if tgt != 0 and tgt*color < 0 and abs(tgt) != 6:
                            pro = (nr == 7 and color == 1) or (nr == 0 and color == -1)
                            if pro:
                                for pr in (5,4,3,2):
                                    moves.append((fr,to,pr))
                            else:
                                moves.append((fr,to,0))
        elif t == 2:
            for dr, df in KNIGHT_OFF:
                nr = r+dr; nf = f+df
                if 0 <= nr < 8 and 0 <= nf < 8:
                    to = nr*8+nf
                    tgt = board[to]
                    if tgt == 0 or (tgt*color < 0 and abs(tgt) != 6):
                        moves.append((fr,to,0))
        elif t == 3 or t == 4 or t == 5:
            dirs = []
            if t == 3: dirs = BISHOP_DIR
            elif t == 4: dirs = ROOK_DIR
            else: dirs = BISHOP_DIR + ROOK_DIR
            for dr, df in dirs:
                nr = r+dr; nf = f+df
                while 0 <= nr < 8 and 0 <= nf < 8:
                    to = nr*8+nf
                    tgt = board[to]
                    if tgt == 0:
                        moves.append((fr,to,0))
                    else:
                        if tgt*color < 0 and abs(tgt) != 6:
                            moves.append((fr,to,0))
                        break
                    nr += dr; nf += df
        elif t == 6:
            for dr, df in KING_OFF:
                nr = r+dr; nf = f+df
                if 0 <= nr < 8 and 0 <= nf < 8:
                    to = nr*8+nf
                    tgt = board[to]
                    if tgt == 0 or (tgt*color < 0 and abs(tgt) != 6):
                        moves.append((fr,to,0))
    return moves

def _make(board, mv):
    fr, to, promo = mv
    pc = board[fr]
    cap = board[to]
    f1 = fr % 8; r1 = fr // 8
    f2 = to % 8; r2 = to // 8
    rf = -1; rt = -1; rpc = 0
    ep_sq = -1; ep_pc = 0
    # castling rook move (for legal_moves that contain it)
    if abs(pc) == 6 and abs(f2-f1) == 2:
        if f2 > f1:
            rf = r1*8+7; rt = r1*8+5
        else:
            rf = r1*8+0; rt = r1*8+3
        rpc = board[rf]
        board[rt] = rpc
        board[rf] = 0
    # en passant capture
    if abs(pc) == 1 and f1 != f2 and cap == 0:
        ep_sq = r1*8+f2
        ep_pc = board[ep_sq]
        # only remove if enemy pawn there
        if ep_pc != 0 and ep_pc*pc < 0 and abs(ep_pc) == 1:
            board[ep_sq] = 0
        else:
            ep_sq = -1; ep_pc = 0
    board[fr] = 0
    if promo:
        col = 1 if pc > 0 else -1
        board[to] = promo*col
    else:
        board[to] = pc
    return (fr, to, pc, cap, rf, rt, rpc, ep_sq, ep_pc, promo)

def _unmake(board, undo):
    fr, to, pc, cap, rf, rt, rpc, ep_sq, ep_pc, promo = undo
    board[fr] = pc
    board[to] = cap
    if rf >= 0:
        board[rf] = rpc
        board[rt] = 0
    if ep_sq >= 0:
        board[ep_sq] = ep_pc

def _gen_legal(board, color):
    pseudos = _gen_pseudo(board, color)
    legal = []
    for mv in pseudos:
        u = _make(board, mv)
        k = _find_king(board, color)
        ok = True
        if k >= 0:
            if _is_attacked(board, k, -color):
                ok = False
        # illegal king capture check already excluded; also ensure not leaving king adjacent etc covered
        _unmake(board, u)
        if ok:
            legal.append(mv)
    return legal

def _evaluate(board):
    # decide endgame
    has_q = False
    total = 0
    for p in board:
        if p != 0:
            t = abs(p)
            if t == 5:
                has_q = True
            if t in (2,3,4,5):
                total += VALS[t]
    end = (not has_q) or (total < 2600)
    score = 0
    wb = 0; bb = 0
    for sq in range(64):
        p = board[sq]
        if p == 0:
            continue
        t = abs(p)
        w = p > 0
        f = sq % 8; r = sq // 8
        if w:
            idx = (7-r)*8+f
        else:
            idx = r*8+f
        v = VALS[t]
        if t == 1: v += P_PST[idx]
        elif t == 2: v += N_PST[idx]
        elif t == 3: v += B_PST[idx]; 
        elif t == 4: v += R_PST[idx]
        elif t == 5: v += Q_PST[idx]
        elif t == 6:
            v += K_END[idx] if end else K_MID[idx]
        if t == 3:
            if w: wb += 1
            else: bb += 1
        if w: score += v
        else: score -= v
    if wb >= 2: score += 30
    if bb >= 2: score -= 30
    return score

def _order_score(board, mv):
    fr, to, promo = mv
    mover = board[fr]
    vic = board[to]
    s = 0
    if vic != 0:
        s += 10*VALS[abs(vic)] - VALS[abs(mover)]
    if promo:
        s += 9000 + VALS[promo]
        if vic != 0:
            s += 10*VALS[abs(vic)]
    else:
        # centralize slightly
        f = to % 8; r = to // 8
        s += (3 - abs(3.5-0.5-f)) + (3 - abs(3.5-0.5-r))
        # pawn push bonus
        if abs(mover) == 1:
            s += 5
    return s

def _quiesce(board, alpha, beta, color, ply):
    global _nodes, _deadline
    _nodes += 1
    if (_nodes & 1023) == 0 and time.time() > _deadline:
        raise _TO()
    in_c = _in_check(board, color)
    if in_c:
        legal = _gen_legal(board, color)
        if not legal:
            return -MATE + ply
        legal.sort(key=lambda m: _order_score(board, m), reverse=True)
        best = -MATE
        for mv in legal:
            u = _make(board, mv)
            sc = -_quiesce(board, -beta, -alpha, -color, ply+1)
            _unmake(board, u)
            if sc > best:
                best = sc
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        return alpha
    stand = color * _evaluate(board)
    if stand >= beta:
        return beta
    if stand > alpha:
        alpha = stand
    # captures + promos
    legal = _gen_legal(board, color)
    caps = []
    for mv in legal:
        fr, to, pr = mv
        if board[to] != 0 or pr != 0:
            caps.append(mv)
    caps.sort(key=lambda m: _order_score(board, m), reverse=True)
    for mv in caps:
        u = _make(board, mv)
        sc = -_quiesce(board, -beta, -alpha, -color, ply+1)
        _unmake(board, u)
        if sc > alpha:
            alpha = sc
        if alpha >= beta:
            break
    return alpha

def _negamax(board, depth, alpha, beta, color, ply):
    global _nodes, _deadline
    _nodes += 1
    if (_nodes & 1023) == 0 and time.time() > _deadline:
        raise _TO()
    if depth <= 0:
        return _quiesce(board, alpha, beta, color, ply)
    in_c = _in_check(board, color)
    legal = _gen_legal(board, color)
    if not legal:
        if in_c:
            return -MATE + ply
        return 0
    legal.sort(key=lambda m: _order_score(board, m), reverse=True)
    best = -MATE*2
    for mv in legal:
        u = _make(board, mv)
        # simple check extension
        ext = 0
        if _in_check(board, -color):
            # don't explode: only extend if depth small? allow 1
            pass
        sc = -_negamax(board, depth-1+ext, -beta, -alpha, -color, ply+1)
        _unmake(board, u)
        if sc > best:
            best = sc
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return alpha

def policy(pieces, to_play="white", legal_moves=None, *args, **kwargs):
    global _nodes, _deadline
    try:
        if legal_moves is None:
            if 'legal_moves' in kwargs and kwargs['legal_moves'] is not None:
                legal_moves = kwargs['legal_moves']
            elif 'moves' in kwargs and kwargs['moves'] is not None:
                legal_moves = kwargs['moves']
            elif len(args) > 0 and isinstance(args[0], (list, tuple)):
                legal_moves = args[0]
        if isinstance(to_play, (list, tuple)):
            legal_moves = to_play
            to_play = "white"
        cs = str(to_play).lower() if to_play is not None else "white"
        if cs.startswith('w'):
            color = 1
        elif cs.startswith('b'):
            color = -1
        else:
            color = 1
        board = [0]*64
        try:
            for sqs, pcs in pieces.items():
                try:
                    s = str(sqs).strip().lower()
                    if len(s) < 2:
                        continue
                    f = ord(s[0])-97
                    r = int(s[1])-1
                    if not (0 <= f < 8 and 0 <= r < 8):
                        continue
                    idx = r*8+f
                    ps = str(pcs)
                    if len(ps) < 2:
                        continue
                    c0 = ps[0].lower()
                    t0 = ps[1].upper()
                    col = 1 if c0 == 'w' else -1 if c0 == 'b' else 0
                    if col == 0:
                        continue
                    mp = {'P':1,'N':2,'B':3,'R':4,'Q':5,'K':6}
                    tt = mp.get(t0, 0)
                    if tt == 0:
                        continue
                    board[idx] = tt*col
                except:
                    continue
        except:
            pass
        # root moves
        root = []
        uci_map = {}
        if legal_moves is not None:
            try:
                lm = list(legal_moves)
            except:
                lm = []
            for u in lm:
                try:
                    us = str(u).strip().lower()
                    if not us:
                        continue
                    parsed = _parse_uci(us)
                    if parsed is None:
                        continue
                    root.append(parsed)
                    uci_map[parsed] = str(u).strip()
                except:
                    continue
            if not root:
                # fallback to generated
                legal_moves = None
        if legal_moves is None:
            root = _gen_legal(board, color)
            if not root:
                return ""
            uci_map = {}
            for mv in root:
                uci_map[mv] = _idx_to_uci_fr_to(mv[0], mv[1], mv[2])
        if len(root) == 1:
            mv = root[0]
            return uci_map.get(mv, _idx_to_uci_fr_to(mv[0], mv[1], mv[2]))
        # order root for search
        root_sorted = sorted(root, key=lambda m: _order_score(board, m), reverse=True)
        # quick mate in 1 check
        for mv in root_sorted:
            u = _make(board, mv)
            opp = _gen_legal(board, -color)
            is_mate = False
            if not opp and _in_check(board, -color):
                _unmake(board, u)
                return uci_map.get(mv, _idx_to_uci_fr_to(mv[0], mv[1], mv[2]))
            _unmake(board, u)
        start = time.time()
        _deadline = start + 0.85
        _nodes = 0
        best_mv = root_sorted[0]
        # static fallback best by eval after move
        try:
            best_sc_f = -10**18
            for mv in root_sorted:
                u = _make(board, mv)
                sc = color * _evaluate(board)
                # bonus for capture ordering already
                _unmake(board, u)
                if sc > best_sc_f:
                    best_sc_f = sc
                    best_mv = mv
        except:
            pass
        max_depth = 4 if len(root_sorted) < 25 else 3
        # iterative deepening
        try:
            for depth in range(1, max_depth+1):
                alpha = -MATE*2
                beta = MATE*2
                cur_best = best_mv
                cur_best_sc = -MATE*2
                # move ordering from previous iteration: put best first
                ordered = [best_mv] + [m for m in root_sorted if m != best_mv]
                for mv in ordered:
                    u = _make(board, mv)
                    sc = -_negamax(board, depth-1, -beta, -alpha, -color, 1)
                    _unmake(board, u)
                    if sc > cur_best_sc:
                        cur_best_sc = sc
                        cur_best = mv
                    if sc > alpha:
                        alpha = sc
                    if time.time() > _deadline:
                        raise _TO()
                best_mv = cur_best
                root_sorted = sorted(root_sorted, key=lambda m: (m == best_mv, _order_score(board, m)), reverse=True)
                if cur_best_sc > MATE-1000:
                    break
                if time.time() > _deadline:
                    break
        except _TO:
            pass
        except Exception:
            pass
        return uci_map.get(best_mv, _idx_to_uci_fr_to(best_mv[0], best_mv[1], best_mv[2]))
    except Exception:
        try:
            if legal_moves is not None and len(list(legal_moves)) > 0:
                return str(list(legal_moves)[0])
        except:
            pass
        try:
            # emergency: generate something
            b2 = [0]*64
            for sqs, pcs in pieces.items():
                try:
                    f = ord(str(sqs)[0].lower())-97; r = int(str(sqs)[1])-1
                    idx = r*8+f
                    col = 1 if str(pcs)[0].lower()=='w' else -1
                    mp = {'P':1,'N':2,'B':3,'R':4,'Q':5,'K':6}
                    tt = mp.get(str(pcs)[1].upper(),0)
                    if tt: b2[idx]=tt*col
                except:
                    continue
            cs2 = str(to_play).lower() if isinstance(to_play,str) else "white"
            col2 = 1 if cs2.startswith('w') else -1
            mvs = _gen_legal(b2, col2)
            if mvs:
                m = mvs[0]
                return _idx_to_uci_fr_to(m[0],m[1],m[2])
        except:
            pass
        return "a2a3"
