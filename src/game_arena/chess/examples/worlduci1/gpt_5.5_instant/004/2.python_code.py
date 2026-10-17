
import time
import math

FILES = "abcdefgh"
RANKS = "12345678"
PIECE_VAL = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}
MATE = 1000000

KNIGHT_DIRS = [(1,2),(2,1),(-1,2),(-2,1),(1,-2),(2,-1),(-1,-2),(-2,-1)]
KING_DIRS = [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]
BISHOP_DIRS = [(1,1),(1,-1),(-1,1),(-1,-1)]
ROOK_DIRS = [(1,0),(-1,0),(0,1),(0,-1)]
QUEEN_DIRS = BISHOP_DIRS + ROOK_DIRS

# Simple piece-square tables from White perspective.
PST = {
    'P': [
        0,0,0,0,0,0,0,0,
        50,50,50,50,50,50,50,50,
        10,10,20,30,30,20,10,10,
        5,5,10,25,25,10,5,5,
        0,0,0,20,20,0,0,0,
        5,-5,-10,0,0,-10,-5,5,
        5,10,10,-20,-20,10,10,5,
        0,0,0,0,0,0,0,0
    ],
    'N': [
        -50,-40,-30,-30,-30,-30,-40,-50,
        -40,-20,0,5,5,0,-20,-40,
        -30,5,10,15,15,10,5,-30,
        -30,0,15,20,20,15,0,-30,
        -30,5,15,20,20,15,5,-30,
        -30,0,10,15,15,10,0,-30,
        -40,-20,0,0,0,0,-20,-40,
        -50,-40,-30,-30,-30,-30,-40,-50
    ],
    'B': [
        -20,-10,-10,-10,-10,-10,-10,-20,
        -10,5,0,0,0,0,5,-10,
        -10,10,10,10,10,10,10,-10,
        -10,0,10,10,10,10,0,-10,
        -10,5,5,10,10,5,5,-10,
        -10,0,5,10,10,5,0,-10,
        -10,0,0,0,0,0,0,-10,
        -20,-10,-10,-10,-10,-10,-10,-20
    ],
    'R': [
        0,0,0,5,5,0,0,0,
        -5,0,0,0,0,0,0,-5,
        -5,0,0,0,0,0,0,-5,
        -5,0,0,0,0,0,0,-5,
        -5,0,0,0,0,0,0,-5,
        -5,0,0,0,0,0,0,-5,
        5,10,10,10,10,10,10,5,
        0,0,0,0,0,0,0,0
    ],
    'Q': [
        -20,-10,-10,-5,-5,-10,-10,-20,
        -10,0,5,0,0,0,0,-10,
        -10,5,5,5,5,5,0,-10,
        0,0,5,5,5,5,0,-5,
        -5,0,5,5,5,5,0,-5,
        -10,0,5,5,5,5,0,-10,
        -10,0,0,0,0,0,0,-10,
        -20,-10,-10,-5,-5,-10,-10,-20
    ],
    'K': [
        20,30,10,0,0,10,30,20,
        20,20,0,0,0,0,20,20,
        -10,-20,-20,-20,-20,-20,-20,-10,
        -20,-30,-30,-40,-40,-30,-30,-20,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30
    ]
}

def sq_to_xy(s):
    return ord(s[0]) - 97, ord(s[1]) - 49

def xy_to_sq(x, y):
    return chr(97 + x) + chr(49 + y)

def inside(x, y):
    return 0 <= x < 8 and 0 <= y < 8

def color_char(to_play):
    return 'w' if to_play == 'white' else 'b'

def other(c):
    return 'b' if c == 'w' else 'w'

def promo_rank(c):
    return 7 if c == 'w' else 0

def pawn_dir(c):
    return 1 if c == 'w' else -1

def pst_value(pt, c, x, y):
    idx = y * 8 + x if c == 'w' else (7 - y) * 8 + x
    return PST.get(pt, [0]*64)[idx]

def find_king(board, c):
    target = c + 'K'
    for s, p in board.items():
        if p == target:
            return s
    return None

def is_attacked(board, sq, by_color):
    x, y = sq_to_xy(sq)

    # pawns
    pd = pawn_dir(by_color)
    for dx in (-1, 1):
        ax, ay = x - dx, y - pd
        if inside(ax, ay) and board.get(xy_to_sq(ax, ay)) == by_color + 'P':
            return True

    # knights
    for dx, dy in KNIGHT_DIRS:
        ax, ay = x + dx, y + dy
        if inside(ax, ay) and board.get(xy_to_sq(ax, ay)) == by_color + 'N':
            return True

    # king
    for dx, dy in KING_DIRS:
        ax, ay = x + dx, y + dy
        if inside(ax, ay) and board.get(xy_to_sq(ax, ay)) == by_color + 'K':
            return True

    # bishops / queens
    for dx, dy in BISHOP_DIRS:
        ax, ay = x + dx, y + dy
        while inside(ax, ay):
            p = board.get(xy_to_sq(ax, ay))
            if p:
                if p[0] == by_color and p[1] in ('B', 'Q'):
                    return True
                break
            ax += dx; ay += dy

    # rooks / queens
    for dx, dy in ROOK_DIRS:
        ax, ay = x + dx, y + dy
        while inside(ax, ay):
            p = board.get(xy_to_sq(ax, ay))
            if p:
                if p[0] == by_color and p[1] in ('R', 'Q'):
                    return True
                break
            ax += dx; ay += dy

    return False

def in_check(board, c):
    k = find_king(board, c)
    if not k:
        return True
    return is_attacked(board, k, other(c))

def apply_move(board, mv):
    nb = dict(board)
    frm, to = mv[:2], mv[2:4]
    p = nb.pop(frm)
    if len(mv) == 5:
        p = p[0] + mv[4].upper()
    nb[to] = p
    return nb

def gen_pseudo(board, c):
    moves = []
    for s, p in list(board.items()):
        if p[0] != c:
            continue
        pt = p[1]
        x, y = sq_to_xy(s)

        if pt == 'P':
            d = pawn_dir(c)
            ny = y + d
            if inside(x, ny):
                to = xy_to_sq(x, ny)
                if to not in board:
                    if ny == promo_rank(c):
                        for pr in "qrbn":
                            moves.append(s + to + pr)
                    else:
                        moves.append(s + to)
                        start = 1 if c == 'w' else 6
                        ny2 = y + 2*d
                        to2 = xy_to_sq(x, ny2)
                        if y == start and inside(x, ny2) and to2 not in board:
                            moves.append(s + to2)
                for dx in (-1, 1):
                    nx = x + dx
                    if inside(nx, ny):
                        cap = xy_to_sq(nx, ny)
                        if cap in board and board[cap][0] != c:
                            if ny == promo_rank(c):
                                for pr in "qrbn":
                                    moves.append(s + cap + pr)
                            else:
                                moves.append(s + cap)

        elif pt == 'N':
            for dx, dy in KNIGHT_DIRS:
                nx, ny = x + dx, y + dy
                if inside(nx, ny):
                    to = xy_to_sq(nx, ny)
                    if to not in board or board[to][0] != c:
                        moves.append(s + to)

        elif pt == 'K':
            for dx, dy in KING_DIRS:
                nx, ny = x + dx, y + dy
                if inside(nx, ny):
                    to = xy_to_sq(nx, ny)
                    if to not in board or board[to][0] != c:
                        moves.append(s + to)
            # Conservative castling support if the arena includes castling positions.
            if c == 'w' and s == 'e1':
                if 'h1' in board and board.get('h1') == 'wR' and 'f1' not in board and 'g1' not in board:
                    moves.append('e1g1')
                if 'a1' in board and board.get('a1') == 'wR' and 'd1' not in board and 'c1' not in board and 'b1' not in board:
                    moves.append('e1c1')
            if c == 'b' and s == 'e8':
                if 'h8' in board and board.get('h8') == 'bR' and 'f8' not in board and 'g8' not in board:
                    moves.append('e8g8')
                if 'a8' in board and board.get('a8') == 'bR' and 'd8' not in board and 'c8' not in board and 'b8' not in board:
                    moves.append('e8c8')

        else:
            dirs = BISHOP_DIRS if pt == 'B' else ROOK_DIRS if pt == 'R' else QUEEN_DIRS
            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                while inside(nx, ny):
                    to = xy_to_sq(nx, ny)
                    if to in board:
                        if board[to][0] != c:
                            moves.append(s + to)
                        break
                    moves.append(s + to)
                    nx += dx; ny += dy
    return moves

def gen_legal(board, c):
    out = []
    for mv in gen_pseudo(board, c):
        frm, to = mv[:2], mv[2:4]
        piece = board.get(frm)
        if not piece:
            continue
        # handle castling legality and rook movement in board application
        nb = dict(board)
        p = nb.pop(frm)
        if piece[1] == 'K' and abs(ord(to[0]) - ord(frm[0])) == 2:
            if in_check(board, c):
                continue
            if to[0] == 'g':
                rook_from, rook_to = ('h1','f1') if c == 'w' else ('h8','f8')
                pass_sq = ('f1' if c == 'w' else 'f8')
            else:
                rook_from, rook_to = ('a1','d1') if c == 'w' else ('a8','d8')
                pass_sq = ('d1' if c == 'w' else 'd8')
            if is_attacked(board, pass_sq, other(c)) or is_attacked(board, to, other(c)):
                continue
            if rook_from in nb:
                nb.pop(rook_from)
                nb[rook_to] = c + 'R'
            nb[to] = p
        else:
            if len(mv) == 5:
                p = c + mv[4].upper()
            nb[to] = p
        if not in_check(nb, c):
            out.append(mv)
    return out

def evaluate(board, us):
    them = other(us)
    score = 0
    kings = {us: find_king(board, us), them: find_king(board, them)}
    for s, p in board.items():
        c, pt = p[0], p[1]
        x, y = sq_to_xy(s)
        val = PIECE_VAL[pt] + pst_value(pt, c, x, y)
        if pt == 'P':
            val += (y if c == 'w' else 7-y) * 6
        score += val if c == us else -val

    # Bishop pair
    for c in (us, them):
        bishops = sum(1 for p in board.values() if p == c + 'B')
        if bishops >= 2:
            score += 35 if c == us else -35

    # King safety: penalize being in check and attacked squares near king.
    for c in (us, them):
        k = kings[c]
        if k:
            kx, ky = sq_to_xy(k)
            danger = 0
            for dx, dy in KING_DIRS + [(0,0)]:
                nx, ny = kx + dx, ky + dy
                if inside(nx, ny) and is_attacked(board, xy_to_sq(nx, ny), other(c)):
                    danger += 1
            adj = -18 * danger
            if in_check(board, c):
                adj -= 80
            score += adj if c == us else -adj

    # Light mobility term
    try:
        score += 2 * (len(gen_pseudo(board, us)) - len(gen_pseudo(board, them)))
    except Exception:
        pass
    return score

def move_order_score(board, mv, c):
    frm, to = mv[:2], mv[2:4]
    moving = board.get(frm, c+'P')
    sc = 0
    if to in board:
        victim = board[to][1]
        sc += 10 * PIECE_VAL[victim] - PIECE_VAL.get(moving[1], 0)
    if len(mv) == 5:
        sc += PIECE_VAL[mv[4].upper()] - PIECE_VAL['P'] + (800 if mv[4] == 'q' else 0)
    # centralization
    tx, ty = sq_to_xy(to)
    sc += 6 - abs(tx - 3.5) - abs(ty - 3.5)
    return sc

def search(board, c, us, depth, alpha, beta, end_time):
    if time.time() > end_time:
        raise TimeoutError

    legal = gen_legal(board, c)
    if not legal:
        if in_check(board, c):
            return -MATE - depth if c == us else MATE + depth
        return 0

    if depth <= 0:
        return evaluate(board, us)

    legal.sort(key=lambda m: move_order_score(board, m, c), reverse=True)

    if c == us:
        best = -10**9
        for mv in legal:
            nb = make_move_full(board, mv)
            val = search(nb, other(c), us, depth-1, alpha, beta, end_time)
            if val > best:
                best = val
            alpha = max(alpha, best)
            if alpha >= beta:
                break
        return best
    else:
        best = 10**9
        for mv in legal:
            nb = make_move_full(board, mv)
            val = search(nb, other(c), us, depth-1, alpha, beta, end_time)
            if val < best:
                best = val
            beta = min(beta, best)
            if alpha >= beta:
                break
        return best

def make_move_full(board, mv):
    nb = dict(board)
    frm, to = mv[:2], mv[2:4]
    p = nb.pop(frm)
    if p[1] == 'K' and abs(ord(to[0]) - ord(frm[0])) == 2:
        if to[0] == 'g':
            rf, rt = ('h1','f1') if p[0] == 'w' else ('h8','f8')
        else:
            rf, rt = ('a1','d1') if p[0] == 'w' else ('a8','d8')
        if rf in nb:
            nb[rt] = nb.pop(rf)
    if len(mv) == 5:
        p = p[0] + mv[4].upper()
    nb[to] = p
    return nb

def policy(pieces: dict[str, str], to_play: str) -> str:
    c = color_char(to_play)
    board = dict(pieces)
    legal = gen_legal(board, c)

    # Absolute safety fallback: if generator somehow fails, return any pseudo move.
    if not legal:
        pseudo = gen_pseudo(board, c)
        return pseudo[0] if pseudo else "a1a1"

    if len(legal) == 1:
        return legal[0]

    # Immediate tactical pre-scan: mate in one / best capture-promotion.
    opp = other(c)
    best_fast = legal[0]
    best_fast_score = -10**9
    for mv in legal:
        nb = make_move_full(board, mv)
        opp_legal = gen_legal(nb, opp)
        if not opp_legal and in_check(nb, opp):
            return mv
        sc = move_order_score(board, mv, c)
        if in_check(nb, opp):
            sc += 120
        if sc > best_fast_score:
            best_fast_score = sc
            best_fast = mv

    end_time = time.time() + 0.85
    best_move = best_fast

    # Iterative deepening; depth 3 is usually reachable, depth 4 in small endgames.
    piece_count = len(board)
    max_depth = 4 if piece_count <= 10 else 3
    if piece_count <= 5:
        max_depth = 5

    try:
        for depth in range(1, max_depth + 1):
            current_best = best_move
            current_score = -10**9
            alpha, beta = -10**9, 10**9
            ordered = sorted(legal, key=lambda m: move_order_score(board, m, c), reverse=True)
            for mv in ordered:
                if time.time() > end_time:
                    raise TimeoutError
                nb = make_move_full(board, mv)
                val = search(nb, opp, c, depth-1, alpha, beta, end_time)
                if val > current_score:
                    current_score = val
                    current_best = mv
                alpha = max(alpha, current_score)
            best_move = current_best
    except Exception:
        pass

    return best_move
