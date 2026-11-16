
import time

def policy(pieces, to_play):
    start = time.time()
    TIME_LIMIT = 0.85

    board = [None]*64
    for sq, p in pieces.items():
        idx = (int(sq[1])-1)*8 + (ord(sq[0])-ord('a'))
        board[idx] = p

    us = 'w' if to_play == 'white' else 'b'

    KN = [(1,2),(2,1),(-1,2),(-2,1),(1,-2),(2,-1),(-1,-2),(-2,-1)]
    DIAG = [(1,1),(1,-1),(-1,1),(-1,-1)]
    ORTH = [(1,0),(-1,0),(0,1),(0,-1)]

    values = {'P':100,'N':320,'B':330,'R':500,'Q':900,'K':20000}

    pst_p = [0,0,0,0,0,0,0,0,
             5,10,10,-20,-20,10,10,5,
             5,-5,-10,0,0,-10,-5,5,
             0,0,0,20,20,0,0,0,
             5,5,10,25,25,10,5,5,
             10,10,20,30,30,20,10,10,
             50,50,50,50,50,50,50,50,
             0,0,0,0,0,0,0,0]
    pst_n = [-50,-40,-30,-30,-30,-30,-40,-50,
             -40,-20,0,5,5,0,-20,-40,
             -30,5,10,15,15,10,5,-30,
             -30,0,15,20,20,15,0,-30,
             -30,5,15,20,20,15,5,-30,
             -30,0,10,15,15,10,0,-30,
             -40,-20,0,0,0,0,-20,-40,
             -50,-40,-30,-30,-30,-30,-40,-50]
    pst_b = [-20,-10,-10,-10,-10,-10,-10,-20,
             -10,5,0,0,0,0,5,-10,
             -10,10,10,10,10,10,10,-10,
             -10,0,10,10,10,10,0,-10,
             -10,5,5,10,10,5,5,-10,
             -10,0,5,10,10,5,0,-10,
             -10,0,0,0,0,0,0,-10,
             -20,-10,-10,-10,-10,-10,-10,-20]
    pst_r = [0,0,0,5,5,0,0,0,
             -5,0,0,0,0,0,0,-5,
             -5,0,0,0,0,0,0,-5,
             -5,0,0,0,0,0,0,-5,
             -5,0,0,0,0,0,0,-5,
             -5,0,0,0,0,0,0,-5,
             5,10,10,10,10,10,10,5,
             0,0,0,0,0,0,0,0]
    pst_q = [0]*64
    pst_k = [20,30,10,0,0,10,30,20,
             20,20,0,0,0,0,20,20,
             -10,-20,-20,-20,-20,-20,-20,-10,
             -20,-30,-30,-40,-40,-30,-30,-20,
             -30,-40,-40,-50,-50,-40,-40,-30,
             -30,-40,-40,-50,-50,-40,-40,-30,
             -30,-40,-40,-50,-50,-40,-40,-30,
             -30,-40,-40,-50,-50,-40,-40,-30]
    psts = {'P':pst_p,'N':pst_n,'B':pst_b,'R':pst_r,'Q':pst_q,'K':pst_k}

    def is_attacked(b, sq, by_color):
        r, f = sq>>3, sq&7
        pawn_dr = -1 if by_color == 'w' else 1
        for df in (-1,1):
            nr, nf = r+pawn_dr, f+df
            if 0<=nr<8 and 0<=nf<8 and b[nr*8+nf] == by_color+'P':
                return True
        for dr,df in KN:
            nr,nf=r+dr,f+df
            if 0<=nr<8 and 0<=nf<8 and b[nr*8+nf] == by_color+'N':
                return True
        for dr in (-1,0,1):
            for df in (-1,0,1):
                if dr==0 and df==0: continue
                nr,nf=r+dr,f+df
                if 0<=nr<8 and 0<=nf<8 and b[nr*8+nf] == by_color+'K':
                    return True
        for dr,df in DIAG:
            nr,nf=r+dr,f+df
            while 0<=nr<8 and 0<=nf<8:
                t = b[nr*8+nf]
                if t is not None:
                    if t[0]==by_color and t[1] in 'BQ': return True
                    break
                nr+=dr; nf+=df
        for dr,df in ORTH:
            nr,nf=r+dr,f+df
            while 0<=nr<8 and 0<=nf<8:
                t = b[nr*8+nf]
                if t is not None:
                    if t[0]==by_color and t[1] in 'RQ': return True
                    break
                nr+=dr; nf+=df
        return False

    def find_king(b, color):
        tgt = color+'K'
        for i in range(64):
            if b[i] == tgt: return i
        return -1

    def gen_moves(b, color):
        moves = []
        them = 'b' if color=='w' else 'w'
        for i in range(64):
            p = b[i]
            if p is None or p[0] != color: continue
            pt = p[1]
            r, f = i>>3, i&7
            if pt == 'P':
                d = 1 if color=='w' else -1
                sr = 1 if color=='w' else 6
                pr_rank = 7 if color=='w' else 0
                nr = r+d
                if 0<=nr<8 and b[nr*8+f] is None:
                    if nr == pr_rank:
                        for prm in 'qrbn':
                            moves.append((i, nr*8+f, prm))
                    else:
                        moves.append((i, nr*8+f, None))
                        if r == sr and b[(r+2*d)*8+f] is None:
                            moves.append((i, (r+2*d)*8+f, None))
                for df in (-1,1):
                    nf = f+df
                    if 0<=nf<8 and 0<=nr<8:
                        t = b[nr*8+nf]
                        if t is not None and t[0] != color:
                            if nr == pr_rank:
                                for prm in 'qrbn':
                                    moves.append((i, nr*8+nf, prm))
                            else:
                                moves.append((i, nr*8+nf, None))
            elif pt == 'N':
                for dr,df in KN:
                    nr,nf=r+dr,f+df
                    if 0<=nr<8 and 0<=nf<8:
                        t = b[nr*8+nf]
                        if t is None or t[0] != color:
                            moves.append((i, nr*8+nf, None))
            elif pt in 'BRQ':
                dirs = []
                if pt in 'BQ': dirs += DIAG
                if pt in 'RQ': dirs += ORTH
                for dr,df in dirs:
                    nr,nf=r+dr,f+df
                    while 0<=nr<8 and 0<=nf<8:
                        t = b[nr*8+nf]
                        if t is None:
                            moves.append((i, nr*8+nf, None))
                        else:
                            if t[0] != color:
                                moves.append((i, nr*8+nf, None))
                            break
                        nr+=dr; nf+=df
            elif pt == 'K':
                for dr in (-1,0,1):
                    for df in (-1,0,1):
                        if dr==0 and df==0: continue
                        nr,nf=r+dr,f+df
                        if 0<=nr<8 and 0<=nf<8:
                            t = b[nr*8+nf]
                            if t is None or t[0] != color:
                                moves.append((i, nr*8+nf, None))
                hr = 0 if color=='w' else 7
                if r == hr and f == 4:
                    if b[hr*8+7] == color+'R' and b[hr*8+5] is None and b[hr*8+6] is None:
                        if (not is_attacked(b, hr*8+4, them) and
                            not is_attacked(b, hr*8+5, them) and
                            not is_attacked(b, hr*8+6, them)):
                            moves.append((i, hr*8+6, None))
                    if (b[hr*8+0] == color+'R' and b[hr*8+1] is None and
                        b[hr*8+2] is None and b[hr*8+3] is None):
                        if (not is_attacked(b, hr*8+4, them) and
                            not is_attacked(b, hr*8+3, them) and
                            not is_attacked(b, hr*8+2, them)):
                            moves.append((i, hr*8+2, None))
        return moves

    def make_move(b, m):
        fr, to, promo = m
        captured = b[to]
        moved = b[fr]
        b[to] = moved
        b[fr] = None
        if promo:
            b[to] = moved[0] + promo.upper()
        rook_move = None
        if moved[1] == 'K' and abs((to&7) - (fr&7)) == 2:
            rr = fr>>3
            if (to&7) == 6:
                rook_move = (rr*8+7, rr*8+5)
                b[rr*8+5] = b[rr*8+7]
                b[rr*8+7] = None
            else:
                rook_move = (rr*8+0, rr*8+3)
                b[rr*8+3] = b[rr*8+0]
                b[rr*8+0] = None
        return (fr, to, captured, moved, rook_move)

    def unmake_move(b, info):
        fr, to, captured, moved, rook_move = info
        b[fr] = moved
        b[to] = captured
        if rook_move:
            rfr, rto = rook_move
            b[rfr] = b[rto]
            b[rto] = None

    def legal_moves(b, color):
        them = 'b' if color=='w' else 'w'
        result = []
        for m in gen_moves(b, color):
            info = make_move(b, m)
            k = find_king(b, color)
            if k >= 0 and not is_attacked(b, k, them):
                result.append(m)
            unmake_move(b, info)
        return result

    def evaluate(b):
        score = 0
        for i in range(64):
            p = b[i]
            if p is None: continue
            v = values[p[1]]
            pst = psts[p[1]]
            if p[0] == 'w':
                score += v + pst[i]
            else:
                mi = (7-(i>>3))*8 + (i&7)
                score -= v + pst[mi]
        return score if us == 'w' else -score

    def score_cap(b, m):
        t = b[m[1]]
        if t is not None:
            return 10*values[t[1]] - values[b[m[0]][1]]
        if m[2]:
            return 800
        return 0

    timed_out = [False]

    def negamax(b, depth, alpha, beta, color):
        if timed_out[0]:
            return 0
        if depth == 0:
            s = evaluate(b)
            return s if color == us else -s
        moves = legal_moves(b, color)
        if not moves:
            k = find_king(b, color)
            them2 = 'b' if color=='w' else 'w'
            if k >= 0 and is_attacked(b, k, them2):
                return -100000 - depth
            return 0
        moves.sort(key=lambda m: score_cap(b, m), reverse=True)
        best = -10**9
        opp = 'b' if color=='w' else 'w'
        for m in moves:
            if timed_out[0]: break
            if time.time() - start > TIME_LIMIT:
                timed_out[0] = True
                break
            info = make_move(b, m)
            val = -negamax(b, depth-1, -beta, -alpha, opp)
            unmake_move(b, info)
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        return best

    root_moves = legal_moves(board, us)
    if not root_moves:
        return "0000"
    root_moves.sort(key=lambda m: score_cap(board, m), reverse=True)
    
    def move_to_str(m):
        fr, to, promo = m
        s = chr(ord('a')+(fr&7)) + str((fr>>3)+1) + chr(ord('a')+(to&7)) + str((to>>3)+1)
        if promo: s += promo
        return s

    best_move = root_moves[0]
    opp = 'b' if us=='w' else 'w'

    for depth in (1, 2, 3, 4):
        if time.time() - start > TIME_LIMIT * 0.4 and depth >= 3:
            if depth == 4: break
        if time.time() - start > TIME_LIMIT * 0.6:
            break
        alpha = -10**9
        beta = 10**9
        current_best = None
        current_best_score = -10**9
        move_scores = []
        for m in root_moves:
            if time.time() - start > TIME_LIMIT:
                timed_out[0] = True
                break
            info = make_move(board, m)
            val = -negamax(board, depth-1, -beta, -alpha, opp)
            unmake_move(board, info)
            if timed_out[0]:
                break
            move_scores.append((m, val))
            if val > current_best_score:
                current_best_score = val
                current_best = m
            if val > alpha:
                alpha = val
        if not timed_out[0] and current_best is not None:
            best_move = current_best
            move_scores.sort(key=lambda x: x[1], reverse=True)
            root_moves = [ms[0] for ms in move_scores]
        else:
            break

    return move_to_str(best_move)
