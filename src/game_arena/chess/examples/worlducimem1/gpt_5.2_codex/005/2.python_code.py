
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

def square_to_coords(sq):
    return FILES.index(sq[0]), RANKS.index(sq[1])

def coords_to_square(x, y):
    return FILES[x] + RANKS[y]

def opponent(color):
    return 'black' if color == 'white' else 'white'

def piece_color(piece):
    return 'white' if piece[0] == 'w' else 'black'

def piece_type(piece):
    return piece[1]

def in_bounds(x, y):
    return 0 <= x < 8 and 0 <= y < 8

def get_king_square(board, color):
    for sq, pc in board.items():
        if pc == ('wK' if color == 'white' else 'bK'):
            return sq
    return None

def generate_attacks(board, color):
    attacks = set()
    for sq, pc in board.items():
        if piece_color(pc) != color:
            continue
        x, y = square_to_coords(sq)
        pt = piece_type(pc)
        if pt == 'P':
            dy = 1 if color == 'white' else -1
            for dx in (-1, 1):
                nx, ny = x+dx, y+dy
                if in_bounds(nx, ny):
                    attacks.add(coords_to_square(nx, ny))
        elif pt == 'N':
            for dx, dy in [(1,2),(2,1),(2,-1),(1,-2),(-1,-2),(-2,-1),(-2,1),(-1,2)]:
                nx, ny = x+dx, y+dy
                if in_bounds(nx, ny):
                    attacks.add(coords_to_square(nx, ny))
        elif pt in ('B','R','Q'):
            directions = []
            if pt in ('B','Q'):
                directions += [(1,1),(1,-1),(-1,1),(-1,-1)]
            if pt in ('R','Q'):
                directions += [(1,0),(-1,0),(0,1),(0,-1)]
            for dx, dy in directions:
                nx, ny = x+dx, y+dy
                while in_bounds(nx, ny):
                    nsq = coords_to_square(nx, ny)
                    attacks.add(nsq)
                    if nsq in board:
                        break
                    nx += dx
                    ny += dy
        elif pt == 'K':
            for dx in (-1,0,1):
                for dy in (-1,0,1):
                    if dx == 0 and dy == 0: continue
                    nx, ny = x+dx, y+dy
                    if in_bounds(nx, ny):
                        attacks.add(coords_to_square(nx, ny))
    return attacks

def is_in_check(board, color):
    ksq = get_king_square(board, color)
    if not ksq:
        return True
    opp = opponent(color)
    attacks = generate_attacks(board, opp)
    return ksq in attacks

def apply_move(board, move):
    new_board = dict(board)
    frm, to = move[:2], move[2:4]
    promo = move[4] if len(move) > 4 else None
    piece = new_board.pop(frm)
    if to in new_board:
        new_board.pop(to)
    if promo:
        color = 'w' if piece[0] == 'w' else 'b'
        new_board[to] = color + promo.upper()
    else:
        new_board[to] = piece
    return new_board

def generate_legal_moves(board, color, memory):
    moves = []
    for sq, pc in board.items():
        if piece_color(pc) != color:
            continue
        x, y = square_to_coords(sq)
        pt = piece_type(pc)
        if pt == 'P':
            dy = 1 if color == 'white' else -1
            start_rank = 1 if color == 'white' else 6
            promo_rank = 7 if color == 'white' else 0
            # forward
            nx, ny = x, y+dy
            if in_bounds(nx, ny):
                nsq = coords_to_square(nx, ny)
                if nsq not in board:
                    if ny == promo_rank:
                        for p in "qrbn":
                            moves.append(sq + nsq + p)
                    else:
                        moves.append(sq + nsq)
                    # double
                    if y == start_rank:
                        ny2 = y + 2*dy
                        nsq2 = coords_to_square(nx, ny2)
                        if nsq2 not in board:
                            moves.append(sq + nsq2)
            # captures
            for dx in (-1, 1):
                nx, ny = x+dx, y+dy
                if in_bounds(nx, ny):
                    nsq = coords_to_square(nx, ny)
                    if nsq in board and piece_color(board[nsq]) != color:
                        if ny == promo_rank:
                            for p in "qrbn":
                                moves.append(sq + nsq + p)
                        else:
                            moves.append(sq + nsq)
        elif pt == 'N':
            for dx, dy in [(1,2),(2,1),(2,-1),(1,-2),(-1,-2),(-2,-1),(-2,1),(-1,2)]:
                nx, ny = x+dx, y+dy
                if in_bounds(nx, ny):
                    nsq = coords_to_square(nx, ny)
                    if nsq not in board or piece_color(board[nsq]) != color:
                        moves.append(sq + nsq)
        elif pt in ('B','R','Q'):
            directions = []
            if pt in ('B','Q'):
                directions += [(1,1),(1,-1),(-1,1),(-1,-1)]
            if pt in ('R','Q'):
                directions += [(1,0),(-1,0),(0,1),(0,-1)]
            for dx, dy in directions:
                nx, ny = x+dx, y+dy
                while in_bounds(nx, ny):
                    nsq = coords_to_square(nx, ny)
                    if nsq in board:
                        if piece_color(board[nsq]) != color:
                            moves.append(sq + nsq)
                        break
                    moves.append(sq + nsq)
                    nx += dx
                    ny += dy
        elif pt == 'K':
            for dx in (-1,0,1):
                for dy in (-1,0,1):
                    if dx == 0 and dy == 0: continue
                    nx, ny = x+dx, y+dy
                    if in_bounds(nx, ny):
                        nsq = coords_to_square(nx, ny)
                        if nsq not in board or piece_color(board[nsq]) != color:
                            moves.append(sq + nsq)
            # simple castling check
            if color == 'white' and sq == 'e1':
                # kingside
                if 'h1' in board and board['h1'] == 'wR':
                    if 'f1' not in board and 'g1' not in board:
                        if not is_in_check(board, color):
                            atk = generate_attacks(board, opponent(color))
                            if 'f1' not in atk and 'g1' not in atk:
                                moves.append('e1g1')
                if 'a1' in board and board['a1'] == 'wR':
                    if 'b1' not in board and 'c1' not in board and 'd1' not in board:
                        if not is_in_check(board, color):
                            atk = generate_attacks(board, opponent(color))
                            if 'd1' not in atk and 'c1' not in atk:
                                moves.append('e1c1')
            if color == 'black' and sq == 'e8':
                if 'h8' in board and board['h8'] == 'bR':
                    if 'f8' not in board and 'g8' not in board:
                        if not is_in_check(board, color):
                            atk = generate_attacks(board, opponent(color))
                            if 'f8' not in atk and 'g8' not in atk:
                                moves.append('e8g8')
                if 'a8' in board and board['a8'] == 'bR':
                    if 'b8' not in board and 'c8' not in board and 'd8' not in board:
                        if not is_in_check(board, color):
                            atk = generate_attacks(board, opponent(color))
                            if 'd8' not in atk and 'c8' not in atk:
                                moves.append('e8c8')
    # filter for legality (king safety)
    legal = []
    for mv in moves:
        nb = apply_move(board, mv)
        if not is_in_check(nb, color):
            legal.append(mv)
    return legal

def evaluate(board, color):
    score = 0
    for sq, pc in board.items():
        val = PIECE_VALUES[piece_type(pc)]
        if piece_color(pc) == color:
            score += val
        else:
            score -= val
    return score

def negamax(board, color, depth, alpha, beta):
    legal = generate_legal_moves(board, color, {})
    if depth == 0 or not legal:
        if not legal:
            if is_in_check(board, color):
                return -100000
            else:
                return 0
        return evaluate(board, color)
    best = -math.inf
    for mv in legal:
        nb = apply_move(board, mv)
        score = -negamax(nb, opponent(color), depth-1, -beta, -alpha)
        if score > best:
            best = score
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best

def policy(pieces: dict[str, str], to_play: str, memory: dict) -> tuple[str, dict]:
    color = to_play
    legal = generate_legal_moves(pieces, color, memory)
    if not legal:
        return ("a1a1", memory)  # fallback, should not happen
    # choose depth
    depth = 3 if len(legal) <= 10 else 2
    best_move = legal[0]
    best_score = -math.inf
    for mv in legal:
        nb = apply_move(pieces, mv)
        score = -negamax(nb, opponent(color), depth-1, -math.inf, math.inf)
        if score > best_score:
            best_score = score
            best_move = mv
    return best_move, memory
