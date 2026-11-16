
import math
import time

FILES = "abcdefgh"
RANKS = "12345678"
F2I = {c: i for i, c in enumerate(FILES)}
I2F = {i: c for i, c in enumerate(FILES)}

VAL = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}

KNIGHT_DIRS = [(1,2),(2,1),(-1,2),(-2,1),(1,-2),(2,-1),(-1,-2),(-2,-1)]
KING_DIRS = [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]
BISHOP_DIRS = [(1,1),(1,-1),(-1,1),(-1,-1)]
ROOK_DIRS = [(1,0),(-1,0),(0,1),(0,-1)]
QUEEN_DIRS = BISHOP_DIRS + ROOK_DIRS

PST = {
    'P': [
        0, 0, 0, 0, 0, 0, 0, 0,
        50,50,50,50,50,50,50,50,
        10,10,20,30,30,20,10,10,
        5, 5,10,25,25,10, 5, 5,
        0, 0, 0,20,20, 0, 0, 0,
        5,-5,-10,0, 0,-10,-5, 5,
        5,10,10,-20,-20,10,10,5,
        0, 0, 0, 0, 0, 0, 0, 0
    ],
    'N': [
        -50,-40,-30,-30,-30,-30,-40,-50,
        -40,-20, 0, 5, 5, 0,-20,-40,
        -30, 5,10,15,15,10, 5,-30,
        -30, 0,15,20,20,15, 0,-30,
        -30, 5,15,20,20,15, 5,-30,
        -30, 0,10,15,15,10, 0,-30,
        -40,-20, 0, 0, 0, 0,-20,-40,
        -50,-40,-30,-30,-30,-30,-40,-50
    ],
    'B': [
        -20,-10,-10,-10,-10,-10,-10,-20,
        -10, 5, 0, 0, 0, 0, 5,-10,
        -10,10,10,10,10,10,10,-10,
        -10, 0,10,10,10,10, 0,-10,
        -10, 5, 5,10,10, 5, 5,-10,
        -10, 0, 5,10,10, 5, 0,-10,
        -10, 0, 0, 0, 0, 0, 0,-10,
        -20,-10,-10,-10,-10,-10,-10,-20
    ],
    'R': [
        0, 0, 0, 5, 5, 0, 0, 0,
        -5,0,0,0,0,0,0,-5,
        -5,0,0,0,0,0,0,-5,
        -5,0,0,0,0,0,0,-5,
        -5,0,0,0,0,0,0,-5,
        -5,0,0,0,0,0,0,-5,
        5,10,10,10,10,10,10,5,
        0, 0, 0, 0, 0, 0, 0, 0
    ],
    'Q': [
        -20,-10,-10,-5,-5,-10,-10,-20,
        -10, 0, 5, 0, 0, 0, 0,-10,
        -10, 5, 5, 5, 5, 5, 0,-10,
        0, 0, 5, 5, 5, 5, 0,-5,
        -5, 0, 5, 5, 5, 5, 0,-5,
        -10, 0, 5, 5, 5, 5, 0,-10,
        -10, 0, 0, 0, 0, 0, 0,-10,
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
    return F2I[s[0]], int(s[1]) - 1

def xy_to_sq(x, y):
    return I2F[x] + str(y + 1)

def inside(x, y):
    return 0 <= x < 8 and 0 <= y < 8

def color_code(to_play):
    return 'w' if to_play == 'white' else 'b'

def opp(c):
    return 'b' if c == 'w' else 'w'

def board_key(board, side):
    return side + "|" + "|".join(k + board[k] for k in sorted(board))

def find_king(board, color):
    k = color + 'K'
    for sq, pc in board.items():
        if pc == k:
            return sq
    return None

def attacked(board, sq, by_color):
    x, y = sq_to_xy(sq)

    pdir = 1 if by_color == 'w' else -1
    for dx in (-1, 1):
        px, py = x - dx, y - pdir
        if inside(px, py) and board.get(xy_to_sq(px, py)) == by_color + 'P':
            return True

    for dx, dy in KNIGHT_DIRS:
        nx, ny = x + dx, y + dy
        if inside(nx, ny) and board.get(xy_to_sq(nx, ny)) == by_color + 'N':
            return True

    for dx, dy in BISHOP_DIRS:
        nx, ny = x + dx, y + dy
        while inside(nx, ny):
            pc = board.get(xy_to_sq(nx, ny))
            if pc:
                if pc[0] == by_color and pc[1] in ('B', 'Q'):
                    return True
                break
            nx += dx; ny += dy

    for dx, dy in ROOK_DIRS:
        nx, ny = x + dx, y + dy
        while inside(nx, ny):
            pc = board.get(xy_to_sq(nx, ny))
            if pc:
                if pc[0] == by_color and pc[1] in ('R', 'Q'):
                    return True
                break
            nx += dx; ny += dy

    for dx, dy in KING_DIRS:
        nx, ny = x + dx, y + dy
        if inside(nx, ny) and board.get(xy_to_sq(nx, ny)) == by_color + 'K':
            return True

    return False

def in_check(board, color):
    ksq = find_king(board, color)
    if not ksq:
        return True
    return attacked(board, ksq, opp(color))

def pseudo_moves(board, color):
    moves = []
    for sq, pc in list(board.items()):
        if pc[0] != color:
            continue
        p = pc[1]
        x, y = sq_to_xy(sq)

        if p == 'P':
            d = 1 if color == 'w' else -1
            start = 1 if color == 'w' else 6
            promo_rank = 7 if color == 'w' else 0

            ny = y + d
            if inside(x, ny):
                ns = xy_to_sq(x, ny)
                if ns not in board:
                    if ny == promo_rank:
                        for pr in "qrbn":
                            moves.append(sq + ns + pr)
                    else:
                        moves.append(sq + ns)
                        if y == start:
                            ny2 = y + 2*d
                            ns2 = xy_to_sq(x, ny2)
                            if inside(x, ny2) and ns2 not in board:
                                moves.append(sq + ns2)

            for dx in (-1, 1):
                nx, ny = x + dx, y + d
                if inside(nx, ny):
                    ns = xy_to_sq(nx, ny)
                    target = board.get(ns)
                    if target and target[0] != color:
                        if ny == promo_rank:
                            for pr in "qrbn":
                                moves.append(sq + ns + pr)
                        else:
                            moves.append(sq + ns)

        elif p == 'N':
            for dx, dy in KNIGHT_DIRS:
                nx, ny = x + dx, y + dy
                if inside(nx, ny):
                    ns = xy_to_sq(nx, ny)
                    t = board.get(ns)
                    if not t or t[0] != color:
                        moves.append(sq + ns)

        elif p in ('B', 'R', 'Q'):
            dirs = BISHOP_DIRS if p == 'B' else ROOK_DIRS if p == 'R' else QUEEN_DIRS
            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                while inside(nx, ny):
                    ns = xy_to_sq(nx, ny)
                    t = board.get(ns)
                    if not t:
                        moves.append(sq + ns)
                    else:
                        if t[0] != color:
                            moves.append(sq + ns)
                        break
                    nx += dx; ny += dy

        elif p == 'K':
            for dx, dy in KING_DIRS:
                nx, ny = x + dx, y + dy
                if inside(nx, ny):
                    ns = xy_to_sq(nx, ny)
                    t = board.get(ns)
                    if not t or t[0] != color:
                        moves.append(sq + ns)

            # Conservative castling support when position still contains unmoved king/rook
            if color == 'w' and sq == 'e1':
                if board.get('h1') == 'wR' and 'f1' not in board and 'g1' not in board:
                    if not attacked(board, 'e1', 'b') and not attacked(board, 'f1', 'b') and not attacked(board, 'g1', 'b'):
                        moves.append('e1g1')
                if board.get('a1') == 'wR' and 'd1' not in board and 'c1' not in board and 'b1' not in board:
                    if not attacked(board, 'e1', 'b') and not attacked(board, 'd1', 'b') and not attacked(board, 'c1', 'b'):
                        moves.append('e1c1')
            if color == 'b' and sq == 'e8':
                if board.get('h8') == 'bR' and 'f8' not in board and 'g8' not in board:
                    if not attacked(board, 'e8', 'w') and not attacked(board, 'f8', 'w') and not attacked(board, 'g8', 'w'):
                        moves.append('e8g8')
                if board.get('a8') == 'bR' and 'd8' not in board and 'c8' not in board and 'b8' not in board:
                    if not attacked(board, 'e8', 'w') and not attacked(board, 'd8', 'w') and not attacked(board, 'c8', 'w'):
                        moves.append('e8c8')
    return moves

def make_move(board, mv):
    b = dict(board)
    frm, to = mv[:2], mv[2:4]
    pc = b.pop(frm, None)
    if pc is None:
        return b

    # castling rook move
    if pc[1] == 'K' and abs(F2I[to[0]] - F2I[frm[0]]) == 2:
        if to == 'g1' and b.get('h1') == 'wR':
            b['f1'] = b.pop('h1')
        elif to == 'c1' and b.get('a1') == 'wR':
            b['d1'] = b.pop('a1')
        elif to == 'g8' and b.get('h8') == 'bR':
            b['f8'] = b.pop('h8')
        elif to == 'c8' and b.get('a8') == 'bR':
            b['d8'] = b.pop('a8')

    if len(mv) > 4 and pc[1] == 'P':
        pc = pc[0] + mv[4].upper()
    b[to] = pc
    return b

def legal_moves_for(board, color):
    res = []
    for mv in pseudo_moves(board, color):
        nb = make_move(board, mv)
        if not in_check(nb, color):
            res.append(mv)
    return res

def pst_value(piece, x, y, color):
    idx = y * 8 + x if color == 'w' else (7 - y) * 8 + x
    return PST[piece][idx]

def evaluate(board, root_color):
    score = 0
    wk = find_king(board, 'w')
    bk = find_king(board, 'b')

    for sq, pc in board.items():
        c, p = pc[0], pc[1]
        x, y = sq_to_xy(sq)
        v = VAL[p] + pst_value(p, x, y, c)
        if p == 'B':
            v += 5
        if c == root_color:
            score += v
        else:
            score -= v

    # bishop pair
    for c in ('w', 'b'):
        bishops = sum(1 for pc in board.values() if pc == c + 'B')
        if bishops >= 2:
            score += 35 if c == root_color else -35

    # king safety: penalty if king is attacked-adjacent exposed
    for c, ksq in [('w', wk), ('b', bk)]:
        if ksq:
            kx, ky = sq_to_xy(ksq)
            shield = 0
            forward = 1 if c == 'w' else -1
            for dx in (-1, 0, 1):
                nx, ny = kx + dx, ky + forward
                if inside(nx, ny) and board.get(xy_to_sq(nx, ny)) == c + 'P':
                    shield += 1
            adj_pen = (3 - shield) * 8
            score += -adj_pen if c == root_color else adj_pen

    return score

def move_score(board, mv, color):
    frm, to = mv[:2], mv[2:4]
    pc = board.get(frm, color + 'P')
    target = board.get(to)
    s = 0
    if target:
        s += 10 * VAL[target[1]] - VAL[pc[1]]
    if len(mv) > 4:
        s += {'q': 900, 'r': 450, 'b': 300, 'n': 290}.get(mv[4], 0)
    if pc[1] == 'P':
        s += 5
    # prefer centralization
    tx, ty = sq_to_xy(to)
    s += 4 - abs(tx - 3.5) + 4 - abs(ty - 3.5)
    return s

def search(board, color, root_color, depth, alpha, beta, end_time, tt):
    if time.time() > end_time:
        return evaluate(board, root_color)

    key = (board_key(board, color), depth)
    if key in tt:
        return tt[key]

    moves = legal_moves_for(board, color)
    if not moves:
        if in_check(board, color):
            return -999999 if color == root_color else 999999
        return 0

    if depth <= 0:
        # quiescence-lite: if in check or captures exist, search one ply of forcing moves
        base = evaluate(board, root_color)
        tactical = [m for m in moves if board.get(m[2:4]) or len(m) > 4]
        if not in_check(board, color) or not tactical:
            return base
        tactical.sort(key=lambda m: move_score(board, m, color), reverse=True)
        if color == root_color:
            val = -10**9
            for m in tactical[:10]:
                val = max(val, search(make_move(board, m), opp(color), root_color, -1, alpha, beta, end_time, tt))
                alpha = max(alpha, val)
                if alpha >= beta:
                    break
            return val
        else:
            val = 10**9
            for m in tactical[:10]:
                val = min(val, search(make_move(board, m), opp(color), root_color, -1, alpha, beta, end_time, tt))
                beta = min(beta, val)
                if alpha >= beta:
                    break
            return val

    moves.sort(key=lambda m: move_score(board, m, color), reverse=True)

    if color == root_color:
        best = -10**9
        for m in moves:
            nb = make_move(board, m)
            v = search(nb, opp(color), root_color, depth - 1, alpha, beta, end_time, tt)
            if v > best:
                best = v
            alpha = max(alpha, best)
            if alpha >= beta:
                break
    else:
        best = 10**9
        for m in moves:
            nb = make_move(board, m)
            v = search(nb, opp(color), root_color, depth - 1, alpha, beta, end_time, tt)
            if v < best:
                best = v
            beta = min(beta, best)
            if alpha >= beta:
                break

    tt[key] = best
    return best

def policy(pieces: dict[str, str], to_play: str) -> str:
    try:
        color = color_code(to_play)
        board = dict(pieces)
        legal = legal_moves_for(board, color)
        if not legal:
            # No legal chess move exists; return syntactically plausible fallback.
            return "a1a1"

        # Immediate mate / winning king capture safeguards
        for m in legal:
            nb = make_move(board, m)
            om = legal_moves_for(nb, opp(color))
            if not om and in_check(nb, opp(color)):
                return m

        # If any move captures a king due to nonstandard arena state, take it.
        for m in legal:
            t = board.get(m[2:4])
            if t and t[1] == 'K':
                return m

        end_time = time.time() + 0.82
        tt = {}
        best_move = legal[0]
        best_val = -10**9

        # Order root moves tactically
        legal.sort(key=lambda m: move_score(board, m, color), reverse=True)

        # Adaptive depth
        n = len(legal)
        depth = 3
        if n <= 12:
            depth = 4
        if n <= 6:
            depth = 5
        if len(board) <= 8:
            depth = max(depth, 5)

        for d in range(1, depth + 1):
            if time.time() > end_time:
                break
            current_best = best_move
            current_val = -10**9
            alpha, beta = -10**9, 10**9

            for m in legal:
                if time.time() > end_time:
                    break
                nb = make_move(board, m)
                v = search(nb, opp(color), color, d - 1, alpha, beta, end_time, tt)

                # bonuses for checking and castling/promotion
                if in_check(nb, opp(color)):
                    v += 25
                if len(m) > 4 and m[4] == 'q':
                    v += 40
                if m in ('e1g1','e1c1','e8g8','e8c8'):
                    v += 20

                if v > current_val:
                    current_val = v
                    current_best = m
                alpha = max(alpha, current_val)

            if time.time() <= end_time:
                best_move, best_val = current_best, current_val

        # Final legality guarantee
        if best_move in legal:
            return best_move
        return legal[0]
    except Exception:
        # Emergency legal-ish generation fallback
        try:
            color = color_code(to_play)
            lm = legal_moves_for(dict(pieces), color)
            return lm[0] if lm else "a1a1"
        except Exception:
            return "a1a1"
