
import math
import time
from functools import lru_cache

FILES = "abcdefgh"
RANKS = "12345678"
PIECE_VAL = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}
INF = 10**9

# Piece-square tables from White perspective, indexed rank1..rank8, file a..h
PST = {
    'P': [
        0, 0, 0, 0, 0, 0, 0, 0,
        50, 50, 50, 50, 50, 50, 50, 50,
        10, 10, 20, 30, 30, 20, 10, 10,
        5, 5, 10, 25, 25, 10, 5, 5,
        0, 0, 0, 20, 20, 0, 0, 0,
        5, -5, -10, 0, 0, -10, -5, 5,
        5, 10, 10, -20, -20, 10, 10, 5,
        0, 0, 0, 0, 0, 0, 0, 0
    ],
    'N': [
        -50, -40, -30, -30, -30, -30, -40, -50,
        -40, -20, 0, 5, 5, 0, -20, -40,
        -30, 5, 10, 15, 15, 10, 5, -30,
        -30, 0, 15, 20, 20, 15, 0, -30,
        -30, 5, 15, 20, 20, 15, 5, -30,
        -30, 0, 10, 15, 15, 10, 0, -30,
        -40, -20, 0, 0, 0, 0, -20, -40,
        -50, -40, -30, -30, -30, -30, -40, -50
    ],
    'B': [
        -20, -10, -10, -10, -10, -10, -10, -20,
        -10, 5, 0, 0, 0, 0, 5, -10,
        -10, 10, 10, 10, 10, 10, 10, -10,
        -10, 0, 10, 10, 10, 10, 0, -10,
        -10, 5, 5, 10, 10, 5, 5, -10,
        -10, 0, 5, 10, 10, 5, 0, -10,
        -10, 0, 0, 0, 0, 0, 0, -10,
        -20, -10, -10, -10, -10, -10, -10, -20
    ],
    'R': [
        0, 0, 5, 10, 10, 5, 0, 0,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        5, 10, 10, 10, 10, 10, 10, 5,
        0, 0, 0, 5, 5, 0, 0, 0
    ],
    'Q': [
        -20, -10, -10, -5, -5, -10, -10, -20,
        -10, 0, 5, 0, 0, 0, 0, -10,
        -10, 5, 5, 5, 5, 5, 0, -10,
        0, 0, 5, 5, 5, 5, 0, -5,
        -5, 0, 5, 5, 5, 5, 0, -5,
        -10, 0, 5, 5, 5, 5, 0, -10,
        -10, 0, 0, 0, 0, 0, 0, -10,
        -20, -10, -10, -5, -5, -10, -10, -20
    ],
    'K': [
        20, 30, 10, 0, 0, 10, 30, 20,
        20, 20, 0, 0, 0, 0, 20, 20,
        -10, -20, -20, -20, -20, -20, -20, -10,
        -20, -30, -30, -40, -40, -30, -30, -20,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30
    ],
    'Ke': [
        -50, -30, -30, -30, -30, -30, -30, -50,
        -30, -30, 0, 0, 0, 0, -30, -30,
        -30, -10, 20, 30, 30, 20, -10, -30,
        -30, -10, 30, 40, 40, 30, -10, -30,
        -30, -10, 30, 40, 40, 30, -10, -30,
        -30, -10, 20, 30, 30, 20, -10, -30,
        -30, -20, -10, 0, 0, -10, -20, -30,
        -50, -40, -30, -20, -20, -30, -40, -50
    ]
}

KNIGHT_DIRS = [(1,2),(2,1),(-1,2),(-2,1),(1,-2),(2,-1),(-1,-2),(-2,-1)]
KING_DIRS = [(1,1),(1,0),(1,-1),(0,1),(0,-1),(-1,1),(-1,0),(-1,-1)]
BISHOP_DIRS = [(1,1),(1,-1),(-1,1),(-1,-1)]
ROOK_DIRS = [(1,0),(-1,0),(0,1),(0,-1)]
QUEEN_DIRS = BISHOP_DIRS + ROOK_DIRS

def sq_to_xy(s):
    return ord(s[0]) - 97, ord(s[1]) - 49

def xy_to_sq(x, y):
    return chr(97+x) + chr(49+y)

def inb(x, y):
    return 0 <= x < 8 and 0 <= y < 8

def color_char(to_play):
    return 'w' if to_play == 'white' else 'b'

def opp(c):
    return 'b' if c == 'w' else 'w'

def side_name(c):
    return 'white' if c == 'w' else 'black'

def board_key(board, side):
    return tuple(sorted(board.items())), side

def pst_value(pt, c, x, y, endgame=False):
    key = 'Ke' if pt == 'K' and endgame else pt
    yy = y if c == 'w' else 7-y
    return PST[key][yy*8+x]

def find_king(board, c):
    target = c + 'K'
    for s, p in board.items():
        if p == target:
            return s
    return None

def attacked_by(board, sq, byc):
    x, y = sq_to_xy(sq)

    # Pawns
    py = y - 1 if byc == 'w' else y + 1
    for dx in (-1, 1):
        px = x + dx
        if inb(px, py) and board.get(xy_to_sq(px, py)) == byc + 'P':
            return True

    # Knights
    for dx, dy in KNIGHT_DIRS:
        nx, ny = x + dx, y + dy
        if inb(nx, ny) and board.get(xy_to_sq(nx, ny)) == byc + 'N':
            return True

    # King
    for dx, dy in KING_DIRS:
        nx, ny = x + dx, y + dy
        if inb(nx, ny) and board.get(xy_to_sq(nx, ny)) == byc + 'K':
            return True

    # Bishops / Queens
    for dx, dy in BISHOP_DIRS:
        nx, ny = x + dx, y + dy
        while inb(nx, ny):
            p = board.get(xy_to_sq(nx, ny))
            if p:
                if p[0] == byc and p[1] in ('B', 'Q'):
                    return True
                break
            nx += dx; ny += dy

    # Rooks / Queens
    for dx, dy in ROOK_DIRS:
        nx, ny = x + dx, y + dy
        while inb(nx, ny):
            p = board.get(xy_to_sq(nx, ny))
            if p:
                if p[0] == byc and p[1] in ('R', 'Q'):
                    return True
                break
            nx += dx; ny += dy

    return False

def in_check(board, c):
    k = find_king(board, c)
    if k is None:
        return True
    return attacked_by(board, k, opp(c))

def make_move(board, mv):
    nb = dict(board)
    fr, to = mv[:2], mv[2:4]
    promo = mv[4].upper() if len(mv) > 4 else None
    piece = nb.pop(fr)
    # Castling rook move if represented by king two-square move
    if piece[1] == 'K' and abs(ord(to[0]) - ord(fr[0])) == 2:
        if to[0] == 'g':
            rf, rt = 'h' + fr[1], 'f' + fr[1]
        else:
            rf, rt = 'a' + fr[1], 'd' + fr[1]
        if rf in nb:
            nb[rt] = nb.pop(rf)
    if promo and piece[1] == 'P':
        piece = piece[0] + promo
    nb[to] = piece
    return nb

def pseudo_moves(board, c, captures_only=False):
    moves = []
    for s, p in list(board.items()):
        if p[0] != c:
            continue
        pt = p[1]
        x, y = sq_to_xy(s)

        if pt == 'P':
            d = 1 if c == 'w' else -1
            start = 1 if c == 'w' else 6
            promo_rank = 7 if c == 'w' else 0

            # Captures
            for dx in (-1, 1):
                nx, ny = x + dx, y + d
                if inb(nx, ny):
                    t = xy_to_sq(nx, ny)
                    if t in board and board[t][0] != c:
                        if ny == promo_rank:
                            for pr in "qrbn":
                                moves.append(s + t + pr)
                        else:
                            moves.append(s + t)

            if not captures_only:
                # Forward moves
                nx, ny = x, y + d
                if inb(nx, ny):
                    t = xy_to_sq(nx, ny)
                    if t not in board:
                        if ny == promo_rank:
                            for pr in "qrbn":
                                moves.append(s + t + pr)
                        else:
                            moves.append(s + t)
                            if y == start:
                                t2 = xy_to_sq(x, y + 2*d)
                                if t2 not in board:
                                    moves.append(s + t2)

        elif pt == 'N':
            for dx, dy in KNIGHT_DIRS:
                nx, ny = x + dx, y + dy
                if inb(nx, ny):
                    t = xy_to_sq(nx, ny)
                    if t not in board:
                        if not captures_only:
                            moves.append(s + t)
                    elif board[t][0] != c:
                        moves.append(s + t)

        elif pt in ('B', 'R', 'Q'):
            dirs = BISHOP_DIRS if pt == 'B' else ROOK_DIRS if pt == 'R' else QUEEN_DIRS
            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                while inb(nx, ny):
                    t = xy_to_sq(nx, ny)
                    if t in board:
                        if board[t][0] != c:
                            moves.append(s + t)
                        break
                    else:
                        if not captures_only:
                            moves.append(s + t)
                    nx += dx; ny += dy

        elif pt == 'K':
            for dx, dy in KING_DIRS:
                nx, ny = x + dx, y + dy
                if inb(nx, ny):
                    t = xy_to_sq(nx, ny)
                    if t not in board:
                        if not captures_only:
                            moves.append(s + t)
                    elif board[t][0] != c:
                        moves.append(s + t)
            # Conservative castling generation: only if pieces currently on original squares.
            if not captures_only and not in_check(board, c):
                rank = '1' if c == 'w' else '8'
                if s == 'e' + rank:
                    enemy = opp(c)
                    if board.get('h'+rank) == c+'R' and ('f'+rank not in board) and ('g'+rank not in board):
                        if not attacked_by(board, 'f'+rank, enemy) and not attacked_by(board, 'g'+rank, enemy):
                            moves.append(s + 'g' + rank)
                    if board.get('a'+rank) == c+'R' and ('b'+rank not in board) and ('c'+rank not in board) and ('d'+rank not in board):
                        if not attacked_by(board, 'd'+rank, enemy) and not attacked_by(board, 'c'+rank, enemy):
                            moves.append(s + 'c' + rank)
    return moves

def legal_moves(board, c, captures_only=False):
    res = []
    for mv in pseudo_moves(board, c, captures_only):
        nb = make_move(board, mv)
        if not in_check(nb, c):
            res.append(mv)
    return res

def material_phase(board):
    total = 0
    for p in board.values():
        if p[1] != 'K':
            total += PIECE_VAL[p[1]]
    return total

def evaluate(board, rootc):
    # Positive is good for rootc
    phase = material_phase(board)
    endgame = phase < 2400
    score = 0
    bishops = {'w': 0, 'b': 0}
    pawns_by_file = {'w': [0]*8, 'b': [0]*8}

    for s, p in board.items():
        c, pt = p[0], p[1]
        x, y = sq_to_xy(s)
        sign = 1 if c == rootc else -1
        val = PIECE_VAL[pt] + pst_value(pt, c, x, y, endgame)
        if pt == 'B':
            bishops[c] += 1
        if pt == 'P':
            pawns_by_file[c][x] += 1
            # advancement and center pawns
            adv = y if c == 'w' else 7-y
            val += adv * 8
            if x in (3,4):
                val += 8
        score += sign * val

    for c in ('w', 'b'):
        sign = 1 if c == rootc else -1
        if bishops[c] >= 2:
            score += sign * 35
        for f in range(8):
            if pawns_by_file[c][f] > 1:
                score -= sign * 12 * (pawns_by_file[c][f]-1)
            if pawns_by_file[c][f] and all(pawns_by_file[c][af] == 0 for af in (f-1, f+1) if 0 <= af < 8):
                score -= sign * 10

    # Mobility (cheap)
    try:
        score += 2 * (len(pseudo_moves(board, rootc)) - len(pseudo_moves(board, opp(rootc))))
    except Exception:
        pass

    # King danger
    for c in ('w', 'b'):
        k = find_king(board, c)
        if k:
            x, y = sq_to_xy(k)
            danger = 0
            enemy = opp(c)
            for dx, dy in KING_DIRS:
                nx, ny = x+dx, y+dy
                if inb(nx, ny) and attacked_by(board, xy_to_sq(nx, ny), enemy):
                    danger += 1
            score += (-1 if c == rootc else 1) * danger * 12

    return score

def move_score(board, mv, c):
    fr, to = mv[:2], mv[2:4]
    piece = board.get(fr, 'wP')[1]
    cap = board.get(to)
    sc = 0
    if len(mv) > 4:
        sc += PIECE_VAL[mv[4].upper()] + 800
    if cap:
        sc += 10 * PIECE_VAL[cap[1]] - PIECE_VAL[piece]
    nb = make_move(board, mv)
    if in_check(nb, opp(c)):
        sc += 80
    # Prefer centralization
    x, y = sq_to_xy(to)
    sc += 4 - abs(3.5-x) - abs(3.5-y)
    return sc

def search(board, c, rootc, depth, alpha, beta, end_time):
    if time.time() > end_time:
        raise TimeoutError

    moves = legal_moves(board, c)
    if not moves:
        if in_check(board, c):
            return -1000000 - depth if c == rootc else 1000000 + depth
        return 0

    if depth <= 0:
        return quiesce(board, c, rootc, alpha, beta, end_time)

    moves.sort(key=lambda m: move_score(board, m, c), reverse=True)

    if c == rootc:
        best = -INF
        for mv in moves:
            val = search(make_move(board, mv), opp(c), rootc, depth-1, alpha, beta, end_time)
            if val > best:
                best = val
            alpha = max(alpha, best)
            if alpha >= beta:
                break
        return best
    else:
        best = INF
        for mv in moves:
            val = search(make_move(board, mv), opp(c), rootc, depth-1, alpha, beta, end_time)
            if val < best:
                best = val
            beta = min(beta, best)
            if alpha >= beta:
                break
        return best

def quiesce(board, c, rootc, alpha, beta, end_time):
    if time.time() > end_time:
        raise TimeoutError

    stand = evaluate(board, rootc)
    if c == rootc:
        if stand >= beta:
            return beta
        alpha = max(alpha, stand)
        moves = legal_moves(board, c, captures_only=True)
        moves.sort(key=lambda m: move_score(board, m, c), reverse=True)
        for mv in moves[:12]:
            val = quiesce(make_move(board, mv), opp(c), rootc, alpha, beta, end_time)
            alpha = max(alpha, val)
            if alpha >= beta:
                break
        return alpha
    else:
        if stand <= alpha:
            return alpha
        beta = min(beta, stand)
        moves = legal_moves(board, c, captures_only=True)
        moves.sort(key=lambda m: move_score(board, m, c), reverse=True)
        for mv in moves[:12]:
            val = quiesce(make_move(board, mv), opp(c), rootc, alpha, beta, end_time)
            beta = min(beta, val)
            if alpha >= beta:
                break
        return beta

def tactical_fallback(board, c, moves):
    # Immediate mate, then highest tactical/eval move.
    best = moves[0]
    bestv = -INF
    for mv in moves:
        nb = make_move(board, mv)
        om = legal_moves(nb, opp(c))
        if not om and in_check(nb, opp(c)):
            return mv
        val = evaluate(nb, c) + move_score(board, mv, c)
        # Avoid moves allowing immediate recapture/checkmate where possible
        if not legal_moves(nb, opp(c)) and not in_check(nb, opp(c)):
            val -= 20
        if val > bestv:
            bestv = val
            best = mv
    return best

def policy(pieces: dict[str, str], to_play: str) -> str:
    try:
        board = dict(pieces)
        c = color_char(to_play)
        moves = legal_moves(board, c)
        if not moves:
            # Should not happen in arena unless game already over; return a syntactically plausible move.
            return "a1a1"

        # If arena has hidden legal_moves with stricter castling rights, generated castle may be illegal.
        # Since no move list is passed, prefer non-castles unless search clearly selects one.
        fallback = tactical_fallback(board, c, moves)

        end_time = time.time() + 0.88
        best = fallback

        # Depth depending on branching.
        max_depth = 4
        if len(moves) > 35:
            max_depth = 3
        if material_phase(board) < 1800 and len(moves) < 25:
            max_depth = 5

        ordered = sorted(moves, key=lambda m: move_score(board, m, c), reverse=True)

        for depth in range(1, max_depth + 1):
            try:
                alpha, beta = -INF, INF
                local_best = best
                local_score = -INF
                for mv in ordered:
                    if time.time() > end_time:
                        raise TimeoutError
                    val = search(make_move(board, mv), opp(c), c, depth-1, alpha, beta, end_time)
                    if val > local_score:
                        local_score = val
                        local_best = mv
                    alpha = max(alpha, local_score)
                best = local_best
                ordered.sort(key=lambda m: (m == best, move_score(board, m, c)), reverse=True)
            except TimeoutError:
                break

        return best if best in moves else fallback
    except Exception:
        try:
            board = dict(pieces)
            c = color_char(to_play)
            lm = legal_moves(board, c)
            if lm:
                return lm[0]
        except Exception:
            pass
        return "a1a1"
