
import time

PIECE_VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}
SQ = [[chr(97+x)+str(y+1) for y in range(8)] for x in range(8)]
KNIGHT_MOVES = [(1,2),(2,1),(-1,2),(-2,1),(1,-2),(2,-1),(-1,-2),(-2,-1)]
BISHOP_DIRS = [(1,1),(1,-1),(-1,1),(-1,-1)]
ROOK_DIRS = [(1,0),(-1,0),(0,1),(0,-1)]
QUEEN_DIRS = BISHOP_DIRS + ROOK_DIRS
KING_MOVES = [(dx,dy) for dx in (-1,0,1) for dy in (-1,0,1) if dx or dy]

def sq_to_xy(sq):
    return ord(sq[0]) - 97, int(sq[1]) - 1

def gen_pseudo_moves(pieces, color):
    moves = []
    enemy = 'b' if color == 'w' else 'w'
    for sq, piece in pieces.items():
        if piece[0] != color:
            continue
        x, y = sq_to_xy(sq)
        pt = piece[1]
        if pt == 'P':
            d = 1 if color == 'w' else -1
            start_rank = 1 if color == 'w' else 6
            promo_rank = 7 if color == 'w' else 0
            ny = y + d
            if 0 <= ny < 8:
                t = SQ[x][ny]
                if t not in pieces:
                    if ny == promo_rank:
                        for p in 'qrbn': moves.append(sq + t + p)
                    else:
                        moves.append(sq + t)
                        if y == start_rank:
                            t2 = SQ[x][y + 2*d]
                            if t2 not in pieces: moves.append(sq + t2)
                for dx in (-1, 1):
                    nx = x + dx
                    if 0 <= nx < 8:
                        t = SQ[nx][ny]
                        if t in pieces and pieces[t][0] == enemy:
                            if ny == promo_rank:
                                for p in 'qrbn': moves.append(sq + t + p)
                            else:
                                moves.append(sq + t)
        elif pt == 'N':
            for dx, dy in KNIGHT_MOVES:
                nx, ny = x+dx, y+dy
                if 0 <= nx < 8 and 0 <= ny < 8:
                    t = SQ[nx][ny]
                    if t not in pieces or pieces[t][0] != color:
                        moves.append(sq + t)
        elif pt == 'K':
            for dx, dy in KING_MOVES:
                nx, ny = x+dx, y+dy
                if 0 <= nx < 8 and 0 <= ny < 8:
                    t = SQ[nx][ny]
                    if t not in pieces or pieces[t][0] != color:
                        moves.append(sq + t)
            hr = '1' if color == 'w' else '8'
            if sq == 'e' + hr:
                if pieces.get('h'+hr) == color+'R' and ('f'+hr) not in pieces and ('g'+hr) not in pieces:
                    moves.append(sq + 'g' + hr)
                if pieces.get('a'+hr) == color+'R' and ('b'+hr) not in pieces and ('c'+hr) not in pieces and ('d'+hr) not in pieces:
                    moves.append(sq + 'c' + hr)
        else:
            dirs = BISHOP_DIRS if pt == 'B' else (ROOK_DIRS if pt == 'R' else QUEEN_DIRS)
            for dx, dy in dirs:
                nx, ny = x+dx, y+dy
                while 0 <= nx < 8 and 0 <= ny < 8:
                    t = SQ[nx][ny]
                    if t in pieces:
                        if pieces[t][0] != color: moves.append(sq + t)
                        break
                    moves.append(sq + t)
                    nx += dx; ny += dy
    return moves

def is_attacked(pieces, sq, by_color):
    x, y = sq_to_xy(sq)
    pdir = -1 if by_color == 'w' else 1
    for dx in (-1, 1):
        nx, ny = x+dx, y+pdir
        if 0 <= nx < 8 and 0 <= ny < 8:
            if pieces.get(SQ[nx][ny]) == by_color+'P': return True
    for dx, dy in KNIGHT_MOVES:
        nx, ny = x+dx, y+dy
        if 0 <= nx < 8 and 0 <= ny < 8:
            if pieces.get(SQ[nx][ny]) == by_color+'N': return True
    for dx, dy in BISHOP_DIRS:
        nx, ny = x+dx, y+dy
        while 0 <= nx < 8 and 0 <= ny < 8:
            s = SQ[nx][ny]
            if s in pieces:
                p = pieces[s]
                if p == by_color+'B' or p == by_color+'Q': return True
                break
            nx += dx; ny += dy
    for dx, dy in ROOK_DIRS:
        nx, ny = x+dx, y+dy
        while 0 <= nx < 8 and 0 <= ny < 8:
            s = SQ[nx][ny]
            if s in pieces:
                p = pieces[s]
                if p == by_color+'R' or p == by_color+'Q': return True
                break
            nx += dx; ny += dy
    for dx, dy in KING_MOVES:
        nx, ny = x+dx, y+dy
        if 0 <= nx < 8 and 0 <= ny < 8:
            if pieces.get(SQ[nx][ny]) == by_color+'K': return True
    return False

def make_move(pieces, move):
    np = dict(pieces)
    src = move[:2]; dst = move[2:4]
    piece = np[src]
    del np[src]
    np[dst] = piece
    if piece[1] == 'K' and abs(ord(src[0]) - ord(dst[0])) == 2:
        rank = src[1]
        if dst[0] == 'g':
            np['f'+rank] = np.pop('h'+rank)
        else:
            np['d'+rank] = np.pop('a'+rank)
    if len(move) == 5:
        np[dst] = piece[0] + move[4].upper()
    return np

def find_king(pieces, color):
    k = color + 'K'
    for sq, p in pieces.items():
        if p == k: return sq
    return None

def legal_moves(pieces, color):
    pseudo = gen_pseudo_moves(pieces, color)
    legal = []
    enemy = 'b' if color == 'w' else 'w'
    king_sq = find_king(pieces, color)
    in_check_now = king_sq is not None and is_attacked(pieces, king_sq, enemy)
    for m in pseudo:
        src = m[:2]; dst = m[2:4]
        piece = pieces[src]
        if piece[1] == 'K' and abs(ord(src[0]) - ord(dst[0])) == 2:
            if in_check_now: continue
            pass_sq = chr((ord(src[0]) + ord(dst[0]))//2) + src[1]
            if is_attacked(pieces, pass_sq, enemy): continue
        np = make_move(pieces, m)
        ks = dst if piece[1] == 'K' else king_sq
        if ks is None or not is_attacked(np, ks, enemy):
            legal.append(m)
    return legal

def evaluate(pieces):
    score = 0
    for sq, piece in pieces.items():
        v = PIECE_VALUES[piece[1]]
        x, y = sq_to_xy(sq)
        cx = 3.5 - abs(3.5 - x); cy = 3.5 - abs(3.5 - y)
        pos = int((cx + cy)) if piece[1] in 'NBP' else 0
        if piece[0] == 'w': score += v + pos
        else: score -= v + pos
    return score

def order_moves(pieces, moves):
    scored = []
    for m in moves:
        dst = m[2:4]
        s = 0
        if dst in pieces:
            s = PIECE_VALUES.get(pieces[dst][1], 0) * 10 - PIECE_VALUES.get(pieces[m[:2]][1], 0)
        if len(m) == 5: s += 8000
        scored.append((s, m))
    scored.sort(reverse=True, key=lambda x: x[0])
    return [m for _, m in scored]

def search(pieces, color, depth, alpha, beta):
    if depth == 0:
        return evaluate(pieces), None
    moves = legal_moves(pieces, color)
    enemy = 'b' if color == 'w' else 'w'
    if not moves:
        king_sq = find_king(pieces, color)
        if king_sq and is_attacked(pieces, king_sq, enemy):
            return (-100000 - depth if color == 'w' else 100000 + depth), None
        return 0, None
    moves = order_moves(pieces, moves)
    best_move = moves[0]
    if color == 'w':
        best = -9999999
        for m in moves:
            np = make_move(pieces, m)
            score, _ = search(np, 'b', depth-1, alpha, beta)
            if score > best:
                best = score; best_move = m
            if best > alpha: alpha = best
            if beta <= alpha: break
        return best, best_move
    else:
        best = 9999999
        for m in moves:
            np = make_move(pieces, m)
            score, _ = search(np, 'w', depth-1, alpha, beta)
            if score < best:
                best = score; best_move = m
            if best < beta: beta = best
            if beta <= alpha: break
        return best, best_move

def policy(pieces, to_play):
    color = 'w' if to_play == 'white' else 'b'
    moves = legal_moves(pieces, color)
    if not moves:
        return "0000"
    start = time.time()
    _, best = search(pieces, color, 3, -9999999, 9999999)
    if best is None:
        best = moves[0]
    if time.time() - start < 0.2 and len(pieces) <= 12:
        try:
            _, b4 = search(pieces, color, 4, -9999999, 9999999)
            if b4: best = b4
        except Exception:
            pass
    return best
