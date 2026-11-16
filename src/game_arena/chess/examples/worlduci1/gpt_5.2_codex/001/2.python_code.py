
import math

FILES = "abcdefgh"
RANKS = "12345678"

PIECE_VALUES = {
    'P': 100,
    'N': 320,
    'B': 330,
    'R': 500,
    'Q': 900,
    'K': 20000
}

MATE_SCORE = 100000

def square_to_xy(sq):
    return FILES.index(sq[0]), RANKS.index(sq[1])

def xy_to_square(x, y):
    return FILES[x] + RANKS[y]

def in_bounds(x, y):
    return 0 <= x < 8 and 0 <= y < 8

def color_code(to_play):
    return 'w' if to_play == 'white' else 'b'

def opponent(color):
    return 'b' if color == 'w' else 'w'

def find_king(pieces, color):
    target = color + 'K'
    for sq, pc in pieces.items():
        if pc == target:
            return sq
    return None

def is_attacked(pieces, sq, by_color):
    x, y = square_to_xy(sq)
    enemy = by_color

    # Pawn attacks
    pawn_dir = 1 if enemy == 'w' else -1
    for dx in (-1, 1):
        nx, ny = x + dx, y + pawn_dir
        if in_bounds(nx, ny):
            nsq = xy_to_square(nx, ny)
            if pieces.get(nsq) == enemy + 'P':
                return True

    # Knight attacks
    for dx, dy in [(1,2),(2,1),(2,-1),(1,-2),(-1,-2),(-2,-1),(-2,1),(-1,2)]:
        nx, ny = x + dx, y + dy
        if in_bounds(nx, ny):
            nsq = xy_to_square(nx, ny)
            if pieces.get(nsq) == enemy + 'N':
                return True

    # King attacks
    for dx in (-1,0,1):
        for dy in (-1,0,1):
            if dx == 0 and dy == 0:
                continue
            nx, ny = x + dx, y + dy
            if in_bounds(nx, ny):
                nsq = xy_to_square(nx, ny)
                if pieces.get(nsq) == enemy + 'K':
                    return True

    # Sliding attacks
    # Rook/Queen (orthogonal)
    for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
        nx, ny = x + dx, y + dy
        while in_bounds(nx, ny):
            nsq = xy_to_square(nx, ny)
            if nsq in pieces:
                p = pieces[nsq]
                if p[0] == enemy and (p[1] == 'R' or p[1] == 'Q'):
                    return True
                break
            nx += dx
            ny += dy

    # Bishop/Queen (diagonal)
    for dx, dy in [(1,1),(1,-1),(-1,1),(-1,-1)]:
        nx, ny = x + dx, y + dy
        while in_bounds(nx, ny):
            nsq = xy_to_square(nx, ny)
            if nsq in pieces:
                p = pieces[nsq]
                if p[0] == enemy and (p[1] == 'B' or p[1] == 'Q'):
                    return True
                break
            nx += dx
            ny += dy

    return False

def make_move(pieces, move):
    newp = dict(pieces)
    frm = move[:2]
    to = move[2:4]
    promo = move[4] if len(move) > 4 else None

    piece = newp.pop(frm)
    # capture
    if to in newp:
        newp.pop(to)

    fx, fy = square_to_xy(frm)
    tx, ty = square_to_xy(to)

    # Castling
    if piece[1] == 'K' and abs(tx - fx) == 2:
        if to == 'g1':
            rook_from, rook_to = 'h1', 'f1'
        elif to == 'c1':
            rook_from, rook_to = 'a1', 'd1'
        elif to == 'g8':
            rook_from, rook_to = 'h8', 'f8'
        elif to == 'c8':
            rook_from, rook_to = 'a8', 'd8'
        else:
            rook_from = rook_to = None
        if rook_from and rook_from in newp:
            newp[rook_to] = newp.pop(rook_from)

    # Promotion
    if promo:
        piece = piece[0] + promo.upper()

    newp[to] = piece
    return newp

def generate_pseudo_moves(pieces, color):
    moves = []
    for sq, pc in pieces.items():
        if pc[0] != color:
            continue
        x, y = square_to_xy(sq)
        ptype = pc[1]

        if ptype == 'P':
            diry = 1 if color == 'w' else -1
            start_rank = 1 if color == 'w' else 6
            prom_rank = 7 if color == 'w' else 0

            # forward
            ny = y + diry
            if in_bounds(x, ny):
                nsq = xy_to_square(x, ny)
                if nsq not in pieces:
                    if ny == prom_rank:
                        for prom in "qrbn":
                            moves.append(sq + nsq + prom)
                    else:
                        moves.append(sq + nsq)
                    # double move
                    if y == start_rank:
                        ny2 = y + 2*diry
                        nsq2 = xy_to_square(x, ny2)
                        if nsq2 not in pieces:
                            moves.append(sq + nsq2)
            # captures
            for dx in (-1, 1):
                nx = x + dx
                ny = y + diry
                if in_bounds(nx, ny):
                    nsq = xy_to_square(nx, ny)
                    if nsq in pieces and pieces[nsq][0] != color:
                        if ny == prom_rank:
                            for prom in "qrbn":
                                moves.append(sq + nsq + prom)
                        else:
                            moves.append(sq + nsq)

        elif ptype == 'N':
            for dx, dy in [(1,2),(2,1),(2,-1),(1,-2),(-1,-2),(-2,-1),(-2,1),(-1,2)]:
                nx, ny = x + dx, y + dy
                if in_bounds(nx, ny):
                    nsq = xy_to_square(nx, ny)
                    if nsq not in pieces or pieces[nsq][0] != color:
                        moves.append(sq + nsq)

        elif ptype in ('B', 'R', 'Q'):
            dirs = []
            if ptype in ('B', 'Q'):
                dirs += [(1,1),(1,-1),(-1,1),(-1,-1)]
            if ptype in ('R', 'Q'):
                dirs += [(1,0),(-1,0),(0,1),(0,-1)]
            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                while in_bounds(nx, ny):
                    nsq = xy_to_square(nx, ny)
                    if nsq in pieces:
                        if pieces[nsq][0] != color:
                            moves.append(sq + nsq)
                        break
                    moves.append(sq + nsq)
                    nx += dx
                    ny += dy

        elif ptype == 'K':
            for dx in (-1,0,1):
                for dy in (-1,0,1):
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = x + dx, y + dy
                    if in_bounds(nx, ny):
                        nsq = xy_to_square(nx, ny)
                        if nsq not in pieces or pieces[nsq][0] != color:
                            moves.append(sq + nsq)

            # Castling
            if color == 'w' and sq == 'e1':
                # King side
                if 'h1' in pieces and pieces['h1'] == 'wR':
                    if 'f1' not in pieces and 'g1' not in pieces:
                        moves.append('e1g1')
                # Queen side
                if 'a1' in pieces and pieces['a1'] == 'wR':
                    if 'b1' not in pieces and 'c1' not in pieces and 'd1' not in pieces:
                        moves.append('e1c1')
            if color == 'b' and sq == 'e8':
                # King side
                if 'h8' in pieces and pieces['h8'] == 'bR':
                    if 'f8' not in pieces and 'g8' not in pieces:
                        moves.append('e8g8')
                # Queen side
                if 'a8' in pieces and pieces['a8'] == 'bR':
                    if 'b8' not in pieces and 'c8' not in pieces and 'd8' not in pieces:
                        moves.append('e8c8')

    return moves

def generate_legal_moves(pieces, color):
    moves = []
    for mv in generate_pseudo_moves(pieces, color):
        newp = make_move(pieces, mv)
        ksq = find_king(newp, color)
        if ksq and not is_attacked(newp, ksq, opponent(color)):
            # additional castling legality: cannot castle through check
            if mv in ('e1g1','e1c1','e8g8','e8c8'):
                if color == 'w':
                    if mv == 'e1g1':
                        squares = ['e1','f1','g1']
                    else:
                        squares = ['e1','d1','c1']
                else:
                    if mv == 'e8g8':
                        squares = ['e8','f8','g8']
                    else:
                        squares = ['e8','d8','c8']
                if any(is_attacked(pieces, sq, opponent(color)) for sq in squares):
                    continue
            moves.append(mv)
    return moves

def evaluate(pieces):
    score = 0
    for pc in pieces.values():
        val = PIECE_VALUES[pc[1]]
        score += val if pc[0] == 'w' else -val
    return score

def negamax(pieces, color, depth, alpha, beta):
    legal = generate_legal_moves(pieces, color)
    if depth == 0 or not legal:
        ksq = find_king(pieces, color)
        if not legal:
            if ksq and is_attacked(pieces, ksq, opponent(color)):
                return -MATE_SCORE + (3 - depth)
            else:
                return 0
        score = evaluate(pieces)
        return score if color == 'w' else -score

    best = -math.inf
    for mv in legal:
        newp = make_move(pieces, mv)
        val = -negamax(newp, opponent(color), depth - 1, -beta, -alpha)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best

def policy(pieces, to_play):
    color = color_code(to_play)
    legal = generate_legal_moves(pieces, color)
    if not legal:
        return legal[0] if legal else "a1a1"  # fallback (should not occur)
    best_move = legal[0]
    best_val = -math.inf
    for mv in legal:
        newp = make_move(pieces, mv)
        val = -negamax(newp, opponent(color), 2, -math.inf, math.inf)
        if val > best_val:
            best_val = val
            best_move = mv
    return best_move
