
import time

def policy(pieces, to_play):
    color = 'w' if to_play == 'white' else 'b'
    
    def opp_of(c):
        return 'b' if c == 'w' else 'w'
    
    def sq_to_xy(sq):
        return ord(sq[0]) - 97, int(sq[1]) - 1
    
    def xy_to_sq(x, y):
        return chr(97 + x) + str(y + 1)
    
    def ib(x, y):
        return 0 <= x < 8 and 0 <= y < 8
    
    PV = {'P':100, 'N':320, 'B':330, 'R':500, 'Q':900, 'K':20000}
    
    PST_P = [0,0,0,0,0,0,0,0, 5,10,10,-20,-20,10,10,5, 5,-5,-10,0,0,-10,-5,5,
             0,0,0,20,20,0,0,0, 5,5,10,25,25,10,5,5, 10,10,20,30,30,20,10,10,
             50,50,50,50,50,50,50,50, 0,0,0,0,0,0,0,0]
    PST_N = [-50,-40,-30,-30,-30,-30,-40,-50, -40,-20,0,5,5,0,-20,-40,
             -30,5,10,15,15,10,5,-30, -30,0,15,20,20,15,0,-30,
             -30,5,15,20,20,15,5,-30, -30,0,10,15,15,10,0,-30,
             -40,-20,0,0,0,0,-20,-40, -50,-40,-30,-30,-30,-30,-40,-50]
    PST_B = [-20,-10,-10,-10,-10,-10,-10,-20, -10,5,0,0,0,0,5,-10,
             -10,10,10,10,10,10,10,-10, -10,0,10,10,10,10,0,-10,
             -10,5,5,10,10,5,5,-10, -10,0,5,10,10,5,0,-10,
             -10,0,0,0,0,0,0,-10, -20,-10,-10,-10,-10,-10,-10,-20]
    PST_R = [0,0,5,10,10,5,0,0]*8
    PST_K = [20,30,10,0,0,10,30,20, 20,20,0,0,0,0,20,20, -10,-20,-20,-20,-20,-20,-20,-10,
             -20,-30,-30,-40,-40,-30,-30,-20, -30,-40,-40,-50,-50,-40,-40,-30,
             -30,-40,-40,-50,-50,-40,-40,-30, -30,-40,-40,-50,-50,-40,-40,-30,
             -30,-40,-40,-50,-50,-40,-40,-30]
    
    def gen_pseudo(board, c):
        moves = []
        o = opp_of(c)
        for sq, p in list(board.items()):
            if p[0] != c: continue
            x, y = sq_to_xy(sq)
            pt = p[1]
            if pt == 'P':
                d = 1 if c == 'w' else -1
                sr = 1 if c == 'w' else 6
                pr = 7 if c == 'w' else 0
                ny = y + d
                if ib(x, ny):
                    t = xy_to_sq(x, ny)
                    if t not in board:
                        if ny == pr:
                            for pp in 'qrbn': moves.append((sq, t, pp))
                        else:
                            moves.append((sq, t, ''))
                            if y == sr:
                                t2 = xy_to_sq(x, y+2*d)
                                if t2 not in board:
                                    moves.append((sq, t2, ''))
                    for dx in (-1, 1):
                        nx = x + dx
                        if ib(nx, ny):
                            t = xy_to_sq(nx, ny)
                            if t in board and board[t][0] == o:
                                if ny == pr:
                                    for pp in 'qrbn': moves.append((sq, t, pp))
                                else:
                                    moves.append((sq, t, ''))
            elif pt == 'N':
                for dx, dy in [(1,2),(2,1),(2,-1),(1,-2),(-1,-2),(-2,-1),(-2,1),(-1,2)]:
                    nx, ny = x+dx, y+dy
                    if ib(nx, ny):
                        t = xy_to_sq(nx, ny)
                        if t not in board or board[t][0] != c:
                            moves.append((sq, t, ''))
            elif pt in 'BRQ':
                dirs = []
                if pt in 'BQ': dirs += [(1,1),(1,-1),(-1,1),(-1,-1)]
                if pt in 'RQ': dirs += [(1,0),(-1,0),(0,1),(0,-1)]
                for dx, dy in dirs:
                    nx, ny = x+dx, y+dy
                    while ib(nx, ny):
                        t = xy_to_sq(nx, ny)
                        if t not in board:
                            moves.append((sq, t, ''))
                        else:
                            if board[t][0] != c:
                                moves.append((sq, t, ''))
                            break
                        nx += dx; ny += dy
            elif pt == 'K':
                for dx in (-1,0,1):
                    for dy in (-1,0,1):
                        if dx==0 and dy==0: continue
                        nx, ny = x+dx, y+dy
                        if ib(nx, ny):
                            t = xy_to_sq(nx, ny)
                            if t not in board or board[t][0] != c:
                                moves.append((sq, t, ''))
                rank = '1' if c == 'w' else '8'
                if sq == 'e'+rank:
                    if board.get('h'+rank) == c+'R':
                        if 'f'+rank not in board and 'g'+rank not in board:
                            moves.append((sq, 'g'+rank, ''))
                    if board.get('a'+rank) == c+'R':
                        if 'b'+rank not in board and 'c'+rank not in board and 'd'+rank not in board:
                            moves.append((sq, 'c'+rank, ''))
        return moves
    
    def is_attacked(board, sq, by):
        x, y = sq_to_xy(sq)
        pd = -1 if by == 'w' else 1
        for dx in (-1, 1):
            nx, ny = x+dx, y+pd
            if ib(nx, ny) and board.get(xy_to_sq(nx,ny)) == by+'P':
                return True
        for dx, dy in [(1,2),(2,1),(2,-1),(1,-2),(-1,-2),(-2,-1),(-2,1),(-1,2)]:
            nx, ny = x+dx, y+dy
            if ib(nx, ny) and board.get(xy_to_sq(nx,ny)) == by+'N':
                return True
        for dx in (-1,0,1):
            for dy in (-1,0,1):
                if dx==0 and dy==0: continue
                nx, ny = x+dx, y+dy
                if ib(nx, ny) and board.get(xy_to_sq(nx,ny)) == by+'K':
                    return True
        for dx, dy in [(1,1),(1,-1),(-1,1),(-1,-1)]:
            nx, ny = x+dx, y+dy
            while ib(nx, ny):
                p = board.get(xy_to_sq(nx,ny))
                if p:
                    if p == by+'B' or p == by+'Q': return True
                    break
                nx += dx; ny += dy
        for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
            nx, ny = x+dx, y+dy
            while ib(nx, ny):
                p = board.get(xy_to_sq(nx,ny))
                if p:
                    if p == by+'R' or p == by+'Q': return True
                    break
                nx += dx; ny += dy
        return False
    
    def make_move(board, mv):
        frm, to, promo = mv
        nb = dict(board)
        piece = nb.pop(frm)
        if promo:
            piece = piece[0] + promo.upper()
        nb[to] = piece
        if piece[1] == 'K' and abs(ord(to[0])-ord(frm[0])) == 2:
            r = frm[1]
            if to[0] == 'g':
                rk = nb.pop('h'+r); nb['f'+r] = rk
            else:
                rk = nb.pop('a'+r); nb['d'+r] = rk
        return nb
    
    def find_king(board, c):
        for sq, p in board.items():
            if p == c+'K': return sq
        return None
    
    def legal_moves(board, c):
        o = opp_of(c)
        res = []
        for mv in gen_pseudo(board, c):
            frm, to, _ = mv
            piece = board[frm]
            if piece[1] == 'K' and abs(ord(to[0])-ord(frm[0])) == 2:
                if is_attacked(board, frm, o): continue
                mid = ('f' if to[0]=='g' else 'd') + frm[1]
                if is_attacked(board, mid, o): continue
            nb = make_move(board, mv)
            ks = find_king(nb, c)
            if ks and not is_attacked(nb, ks, o):
                res.append(mv)
        return res
    
    def eval_board(board):
        s = 0
        for sq, p in board.items():
            x, y = sq_to_xy(sq)
            idx = y*8+x if p[0]=='w' else (7-y)*8+x
            v = PV[p[1]]
            if p[1]=='P': v += PST_P[idx]
            elif p[1]=='N': v += PST_N[idx]
            elif p[1]=='B': v += PST_B[idx]
            elif p[1]=='R': v += PST_R[idx]
            elif p[1]=='K': v += PST_K[idx]
            s += v if p[0]=='w' else -v
        return s
    
    start = time.time()
    TL = 0.7
    
    def negamax(board, depth, alpha, beta, c, ply):
        if time.time() - start > TL:
            raise TimeoutError
        moves = legal_moves(board, c)
        if not moves:
            ks = find_king(board, c)
            if ks and is_attacked(board, ks, opp_of(c)):
                return -100000 + ply
            return 0
        if depth == 0:
            e = eval_board(board)
            return e if c == 'w' else -e
        def ms(mv):
            to = mv[1]
            sc = 0
            if to in board:
                sc = PV[board[to][1]]*10 - PV[board[mv[0]][1]]
            if mv[2]: sc += 800
            return sc
        moves.sort(key=ms, reverse=True)
        best = -1000000
        for mv in moves:
            nb = make_move(board, mv)
            v = -negamax(nb, depth-1, -beta, -alpha, opp_of(c), ply+1)
            if v > best:
                best = v
            if best > alpha: alpha = best
            if alpha >= beta: break
        return best
    
    root_moves = legal_moves(pieces, color)
    if not root_moves:
        return "0000"
    
    def ms_root(mv):
        to = mv[1]
        sc = 0
        if to in pieces:
            sc = PV[pieces[to][1]]*10 - PV[pieces[mv[0]][1]]
        if mv[2]: sc += 800
        return sc
    root_moves.sort(key=ms_root, reverse=True)
    
    best_mv = root_moves[0]
    
    try:
        for depth in range(1, 5):
            if time.time() - start > TL * 0.4:
                break
            cur_best = None
            cur_val = -1000000
            alpha = -1000000
            beta = 1000000
            ordered = [best_mv] + [m for m in root_moves if m != best_mv]
            for mv in ordered:
                nb = make_move(pieces, mv)
                try:
                    v = -negamax(nb, depth-1, -beta, -alpha, opp_of(color), 1)
                except TimeoutError:
                    raise
                if v > cur_val:
                    cur_val = v
                    cur_best = mv
                if cur_val > alpha: alpha = cur_val
            if cur_best is not None:
                best_mv = cur_best
    except TimeoutError:
        pass
    
    frm, to, promo = best_mv
    return frm + to + promo
