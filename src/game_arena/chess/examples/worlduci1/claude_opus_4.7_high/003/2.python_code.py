
import time

# Precompute attack tables at module level
_KNIGHT_OFFS = []
for _i in range(64):
    _x, _y = _i % 8, _i // 8
    _lst = []
    for _dx, _dy in [(1,2),(2,1),(-1,2),(-2,1),(1,-2),(2,-1),(-1,-2),(-2,-1)]:
        _nx, _ny = _x + _dx, _y + _dy
        if 0 <= _nx < 8 and 0 <= _ny < 8:
            _lst.append(_ny * 8 + _nx)
    _KNIGHT_OFFS.append(_lst)

_KING_OFFS = []
for _i in range(64):
    _x, _y = _i % 8, _i // 8
    _lst = []
    for _dx in (-1, 0, 1):
        for _dy in (-1, 0, 1):
            if _dx == 0 and _dy == 0: continue
            _nx, _ny = _x + _dx, _y + _dy
            if 0 <= _nx < 8 and 0 <= _ny < 8:
                _lst.append(_ny * 8 + _nx)
    _KING_OFFS.append(_lst)

_BISHOP_DIRS = [(1,1),(1,-1),(-1,1),(-1,-1)]
_ROOK_DIRS = [(1,0),(-1,0),(0,1),(0,-1)]
_QUEEN_DIRS = _BISHOP_DIRS + _ROOK_DIRS

_RAYS = {}
for _sq in range(64):
    _x, _y = _sq % 8, _sq // 8
    for _dx, _dy in _QUEEN_DIRS:
        _ray = []
        _nx, _ny = _x + _dx, _y + _dy
        while 0 <= _nx < 8 and 0 <= _ny < 8:
            _ray.append(_ny * 8 + _nx)
            _nx += _dx; _ny += _dy
        _RAYS[(_sq, _dx, _dy)] = _ray

_VALS = {'P':100,'N':320,'B':330,'R':500,'Q':900,'K':20000}

_PST_P = [0,0,0,0,0,0,0,0, 5,10,10,-20,-20,10,10,5, 5,-5,-10,0,0,-10,-5,5,
          0,0,0,20,20,0,0,0, 5,5,10,25,25,10,5,5, 10,10,20,30,30,20,10,10,
          50,50,50,50,50,50,50,50, 0,0,0,0,0,0,0,0]
_PST_N = [-50,-40,-30,-30,-30,-30,-40,-50, -40,-20,0,5,5,0,-20,-40,
          -30,5,10,15,15,10,5,-30, -30,0,15,20,20,15,0,-30,
          -30,5,15,20,20,15,5,-30, -30,0,10,15,15,10,0,-30,
          -40,-20,0,0,0,0,-20,-40, -50,-40,-30,-30,-30,-30,-40,-50]
_PST_B = [-20,-10,-10,-10,-10,-10,-10,-20, -10,5,0,0,0,0,5,-10,
          -10,10,10,10,10,10,10,-10, -10,0,10,10,10,10,0,-10,
          -10,5,5,10,10,5,5,-10, -10,0,5,10,10,5,0,-10,
          -10,0,0,0,0,0,0,-10, -20,-10,-10,-10,-10,-10,-10,-20]
_PST_R = [0,0,0,5,5,0,0,0, -5,0,0,0,0,0,0,-5, -5,0,0,0,0,0,0,-5,
          -5,0,0,0,0,0,0,-5, -5,0,0,0,0,0,0,-5, -5,0,0,0,0,0,0,-5,
          5,10,10,10,10,10,10,5, 0,0,0,0,0,0,0,0]
_PST_Q = [-20,-10,-10,-5,-5,-10,-10,-20, -10,0,0,0,0,0,0,-10,
          -10,0,5,5,5,5,0,-10, -5,0,5,5,5,5,0,-5,
          0,0,5,5,5,5,0,-5, -10,5,5,5,5,5,0,-10,
          -10,0,5,0,0,0,0,-10, -20,-10,-10,-5,-5,-10,-10,-20]
_PST_K = [20,30,10,0,0,10,30,20, 20,20,0,0,0,0,20,20,
          -10,-20,-20,-20,-20,-20,-20,-10, -20,-30,-30,-40,-40,-30,-30,-20,
          -30,-40,-40,-50,-50,-40,-40,-30, -30,-40,-40,-50,-50,-40,-40,-30,
          -30,-40,-40,-50,-50,-40,-40,-30, -30,-40,-40,-50,-50,-40,-40,-30]
_PSTS = {'P':_PST_P,'N':_PST_N,'B':_PST_B,'R':_PST_R,'Q':_PST_Q,'K':_PST_K}


def policy(pieces, to_play):
    start_time = time.time()
    TIME_LIMIT = 0.7
    color = 'w' if to_play == 'white' else 'b'
    enemy = 'b' if color == 'w' else 'w'

    board = [''] * 64
    for sq, p in pieces.items():
        x = ord(sq[0]) - 97
        y = int(sq[1]) - 1
        board[y * 8 + x] = p

    def attacked(bd, sq, by_color):
        x, y = sq % 8, sq // 8
        pdir = 1 if by_color == 'w' else -1
        py = y - pdir
        if 0 <= py < 8:
            pc = by_color + 'P'
            if x > 0 and bd[py*8 + x - 1] == pc: return True
            if x < 7 and bd[py*8 + x + 1] == pc: return True
        nc = by_color + 'N'
        for s in _KNIGHT_OFFS[sq]:
            if bd[s] == nc: return True
        kc = by_color + 'K'
        for s in _KING_OFFS[sq]:
            if bd[s] == kc: return True
        for dx, dy in _BISHOP_DIRS:
            for s in _RAYS[(sq, dx, dy)]:
                p = bd[s]
                if p:
                    if p[0] == by_color and (p[1] == 'B' or p[1] == 'Q'):
                        return True
                    break
        for dx, dy in _ROOK_DIRS:
            for s in _RAYS[(sq, dx, dy)]:
                p = bd[s]
                if p:
                    if p[0] == by_color and (p[1] == 'R' or p[1] == 'Q'):
                        return True
                    break
        return False

    def find_king(bd, c):
        kp = c + 'K'
        for i in range(64):
            if bd[i] == kp: return i
        return -1

    def gen_moves(bd, c):
        moves = []
        ec = 'b' if c == 'w' else 'w'
        direction = 1 if c == 'w' else -1
        start_rank = 1 if c == 'w' else 6
        promo_rank = 7 if c == 'w' else 0
        home_rank = 0 if c == 'w' else 7

        for sq in range(64):
            p = bd[sq]
            if not p or p[0] != c: continue
            x, y = sq % 8, sq // 8
            pt = p[1]
            if pt == 'P':
                ny = y + direction
                if 0 <= ny < 8:
                    nsq = ny * 8 + x
                    if not bd[nsq]:
                        if ny == promo_rank:
                            for pr in ('q','r','b','n'):
                                moves.append((sq, nsq, pr))
                        else:
                            moves.append((sq, nsq, None))
                            if y == start_rank:
                                nsq2 = (y + 2*direction) * 8 + x
                                if not bd[nsq2]:
                                    moves.append((sq, nsq2, None))
                    for dx in (-1, 1):
                        nx = x + dx
                        if 0 <= nx < 8:
                            csq = ny * 8 + nx
                            t = bd[csq]
                            if t and t[0] == ec:
                                if ny == promo_rank:
                                    for pr in ('q','r','b','n'):
                                        moves.append((sq, csq, pr))
                                else:
                                    moves.append((sq, csq, None))
            elif pt == 'N':
                for nsq in _KNIGHT_OFFS[sq]:
                    t = bd[nsq]
                    if not t or t[0] == ec:
                        moves.append((sq, nsq, None))
            elif pt == 'K':
                for nsq in _KING_OFFS[sq]:
                    t = bd[nsq]
                    if not t or t[0] == ec:
                        moves.append((sq, nsq, None))
                if y == home_rank and x == 4:
                    hr_off = home_rank * 8
                    if bd[hr_off+7] == c+'R' and not bd[hr_off+5] and not bd[hr_off+6]:
                        if not attacked(bd, hr_off+4, ec) and not attacked(bd, hr_off+5, ec) and not attacked(bd, hr_off+6, ec):
                            moves.append((sq, hr_off+6, 'c'))
                    if bd[hr_off] == c+'R' and not bd[hr_off+1] and not bd[hr_off+2] and not bd[hr_off+3]:
                        if not attacked(bd, hr_off+4, ec) and not attacked(bd, hr_off+3, ec) and not attacked(bd, hr_off+2, ec):
                            moves.append((sq, hr_off+2, 'c'))
            elif pt == 'B':
                for dx, dy in _BISHOP_DIRS:
                    for nsq in _RAYS[(sq, dx, dy)]:
                        t = bd[nsq]
                        if not t:
                            moves.append((sq, nsq, None))
                        else:
                            if t[0] == ec:
                                moves.append((sq, nsq, None))
                            break
            elif pt == 'R':
                for dx, dy in _ROOK_DIRS:
                    for nsq in _RAYS[(sq, dx, dy)]:
                        t = bd[nsq]
                        if not t:
                            moves.append((sq, nsq, None))
                        else:
                            if t[0] == ec:
                                moves.append((sq, nsq, None))
                            break
            else:
                for dx, dy in _QUEEN_DIRS:
                    for nsq in _RAYS[(sq, dx, dy)]:
                        t = bd[nsq]
                        if not t:
                            moves.append((sq, nsq, None))
                        else:
                            if t[0] == ec:
                                moves.append((sq, nsq, None))
                            break
        return moves

    def make(bd, move):
        fr, to, promo = move
        captured = bd[to]
        piece = bd[fr]
        bd[fr] = ''
        rook_info = None
        if promo == 'c':
            bd[to] = piece
            hr = (fr // 8) * 8
            if to % 8 == 6:
                bd[hr+5] = bd[hr+7]; bd[hr+7] = ''
                rook_info = ('k', hr)
            else:
                bd[hr+3] = bd[hr]; bd[hr] = ''
                rook_info = ('q', hr)
        elif promo:
            bd[to] = piece[0] + promo.upper()
        else:
            bd[to] = piece
        return captured, rook_info, piece

    def unmake(bd, move, captured, rook_info, piece):
        fr, to, _ = move
        bd[fr] = piece
        bd[to] = captured
        if rook_info:
            side, hr = rook_info
            if side == 'k':
                bd[hr+7] = bd[hr+5]; bd[hr+5] = ''
            else:
                bd[hr] = bd[hr+3]; bd[hr+3] = ''

    def eval_board(bd):
        score = 0
        for i in range(64):
            p = bd[i]
            if not p: continue
            pt = p[1]
            v = _VALS[pt]
            if p[0] == 'w':
                score += v + _PSTS[pt][i]
            else:
                mi = (7 - i // 8) * 8 + (i % 8)
                score -= v + _PSTS[pt][mi]
        return score

    class TO(Exception): pass

    node_count = [0]

    def negamax(depth, alpha, beta, c):
        node_count[0] += 1
        if node_count[0] & 511 == 0:
            if time.time() - start_time > TIME_LIMIT:
                raise TO()

        ec = 'b' if c == 'w' else 'w'

        if depth <= 0:
            s = eval_board(board)
            return (s if c == 'w' else -s), None

        moves = gen_moves(board, c)

        def mkey(m):
            t = board[m[1]]
            if t:
                return -(_VALS[t[1]] * 10 - _VALS[board[m[0]][1]])
            return 0
        moves.sort(key=mkey)

        best = -10**9
        best_move = None
        legal_count = 0

        for m in moves:
            captured, rook_info, piece = make(board, m)
            king_sq = find_king(board, c)
            if king_sq < 0 or attacked(board, king_sq, ec):
                unmake(board, m, captured, rook_info, piece)
                continue
            legal_count += 1
            try:
                score, _ = negamax(depth - 1, -beta, -alpha, ec)
            except TO:
                unmake(board, m, captured, rook_info, piece)
                raise
            score = -score
            unmake(board, m, captured, rook_info, piece)

            if score > best:
                best = score
                best_move = m
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break

        if legal_count == 0:
            king_sq = find_king(board, c)
            if king_sq >= 0 and attacked(board, king_sq, ec):
                return -100000 - depth, None
            return 0, None

        return best, best_move

    best_move = None
    snapshot = list(board)
    for depth in range(1, 5):
        if time.time() - start_time > TIME_LIMIT * 0.5 and best_move is not None:
            break
        try:
            _, mv = negamax(depth, -10**9, 10**9, color)
            if mv is not None:
                best_move = mv
        except TO:
            for i in range(64):
                board[i] = snapshot[i]
            break

    if best_move is None:
        moves = gen_moves(board, color)
        for m in moves:
            captured, rook_info, piece = make(board, m)
            king_sq = find_king(board, color)
            ok = king_sq >= 0 and not attacked(board, king_sq, enemy)
            unmake(board, m, captured, rook_info, piece)
            if ok:
                best_move = m
                break

    if best_move is None:
        return 'a1a1'

    fr, to, promo = best_move
    fr_str = chr(97 + fr % 8) + str(fr // 8 + 1)
    to_str = chr(97 + to % 8) + str(to // 8 + 1)
    if promo and promo != 'c':
        return fr_str + to_str + promo
    return fr_str + to_str
