
import random
import math

# Piece values for evaluation
PIECE_VALUES = {
    'P': 100,
    'N': 320,
    'B': 330,
    'R': 500,
    'Q': 900,
    'K': 0
}

FILES = 'abcdefgh'
RANKS = '12345678'

def square_to_xy(sq):
    return FILES.index(sq[0]), RANKS.index(sq[1])

def xy_to_square(x, y):
    return FILES[x] + RANKS[y]

def opponent(color):
    return 'black' if color == 'white' else 'white'

def color_of(piece):
    return 'white' if piece[0] == 'w' else 'black'

def generate_pseudo_moves(pieces, color):
    moves = []
    for sq, piece in pieces.items():
        if color_of(piece) != color:
            continue
        p = piece[1]
        x, y = square_to_xy(sq)
        if p == 'P':
            direction = 1 if color == 'white' else -1
            start_rank = 1 if color == 'white' else 6
            promote_rank = 7 if color == 'white' else 0

            # forward move
            nx, ny = x, y + direction
            if 0 <= ny <= 7 and xy_to_square(nx, ny) not in pieces:
                if ny == promote_rank:
                    for prom in "qrbn":
                        moves.append(sq + xy_to_square(nx, ny) + prom)
                else:
                    moves.append(sq + xy_to_square(nx, ny))
                # double move
                if y == start_rank:
                    nny = y + 2 * direction
                    if xy_to_square(x, nny) not in pieces:
                        moves.append(sq + xy_to_square(x, nny))

            # captures
            for dx in [-1, 1]:
                nx, ny = x + dx, y + direction
                if 0 <= nx <= 7 and 0 <= ny <= 7:
                    nsq = xy_to_square(nx, ny)
                    if nsq in pieces and color_of(pieces[nsq]) != color:
                        if ny == promote_rank:
                            for prom in "qrbn":
                                moves.append(sq + nsq + prom)
                        else:
                            moves.append(sq + nsq)

        elif p == 'N':
            for dx, dy in [(1,2),(2,1),(-1,2),(-2,1),(1,-2),(2,-1),(-1,-2),(-2,-1)]:
                nx, ny = x+dx, y+dy
                if 0 <= nx <= 7 and 0 <= ny <= 7:
                    nsq = xy_to_square(nx, ny)
                    if nsq not in pieces or color_of(pieces[nsq]) != color:
                        moves.append(sq + nsq)

        elif p in ['B','R','Q']:
            directions = []
            if p in ['B','Q']:
                directions += [(1,1),(1,-1),(-1,1),(-1,-1)]
            if p in ['R','Q']:
                directions += [(1,0),(-1,0),(0,1),(0,-1)]
            for dx, dy in directions:
                nx, ny = x+dx, y+dy
                while 0 <= nx <= 7 and 0 <= ny <= 7:
                    nsq = xy_to_square(nx, ny)
                    if nsq not in pieces:
                        moves.append(sq + nsq)
                    else:
                        if color_of(pieces[nsq]) != color:
                            moves.append(sq + nsq)
                        break
                    nx += dx
                    ny += dy

        elif p == 'K':
            for dx in [-1,0,1]:
                for dy in [-1,0,1]:
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = x+dx, y+dy
                    if 0 <= nx <= 7 and 0 <= ny <= 7:
                        nsq = xy_to_square(nx, ny)
                        if nsq not in pieces or color_of(pieces[nsq]) != color:
                            moves.append(sq + nsq)
    return moves

def is_square_attacked(pieces, square, attacker_color):
    x, y = square_to_xy(square)
    # Pawns
    direction = 1 if attacker_color == 'white' else -1
    for dx in [-1, 1]:
        nx, ny = x+dx, y-direction
        if 0 <= nx <= 7 and 0 <= ny <= 7:
            nsq = xy_to_square(nx, ny)
            if nsq in pieces and pieces[nsq][1] == 'P' and color_of(pieces[nsq]) == attacker_color:
                return True
    # Knights
    for dx, dy in [(1,2),(2,1),(-1,2),(-2,1),(1,-2),(2,-1),(-1,-2),(-2,-1)]:
        nx, ny = x+dx, y+dy
        if 0 <= nx <= 7 and 0 <= ny <= 7:
            nsq = xy_to_square(nx, ny)
            if nsq in pieces and pieces[nsq][1] == 'N' and color_of(pieces[nsq]) == attacker_color:
                return True
    # Bishops/Queens
    for dx, dy in [(1,1),(1,-1),(-1,1),(-1,-1)]:
        nx, ny = x+dx, y+dy
        while 0 <= nx <= 7 and 0 <= ny <= 7:
            nsq = xy_to_square(nx, ny)
            if nsq in pieces:
                if color_of(pieces[nsq]) == attacker_color and pieces[nsq][1] in ['B','Q']:
                    return True
                break
            nx += dx
            ny += dy
    # Rooks/Queens
    for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
        nx, ny = x+dx, y+dy
        while 0 <= nx <= 7 and 0 <= ny <= 7:
            nsq = xy_to_square(nx, ny)
            if nsq in pieces:
                if color_of(pieces[nsq]) == attacker_color and pieces[nsq][1] in ['R','Q']:
                    return True
                break
            nx += dx
            ny += dy
    # King
    for dx in [-1,0,1]:
        for dy in [-1,0,1]:
            if dx == 0 and dy == 0:
                continue
            nx, ny = x+dx, y+dy
            if 0 <= nx <= 7 and 0 <= ny <= 7:
                nsq = xy_to_square(nx, ny)
                if nsq in pieces and pieces[nsq][1] == 'K' and color_of(pieces[nsq]) == attacker_color:
                    return True
    return False

def find_king(pieces, color):
    for sq, piece in pieces.items():
        if piece[1] == 'K' and color_of(piece) == color:
            return sq
    return None

def make_move(pieces, move):
    new_pieces = dict(pieces)
    from_sq = move[0:2]
    to_sq = move[2:4]
    prom = move[4] if len(move) == 5 else None
    piece = new_pieces.pop(from_sq)
    if to_sq in new_pieces:
        new_pieces.pop(to_sq)
    if prom:
        piece = piece[0] + prom.upper()
    new_pieces[to_sq] = piece
    return new_pieces

def legal_moves(pieces, color):
    moves = []
    for mv in generate_pseudo_moves(pieces, color):
        new_pieces = make_move(pieces, mv)
        king_sq = find_king(new_pieces, color)
        if king_sq and not is_square_attacked(new_pieces, king_sq, opponent(color)):
            moves.append(mv)
    return moves

def evaluate(pieces, color):
    score = 0
    for piece in pieces.values():
        val = PIECE_VALUES[piece[1]]
        if color_of(piece) == color:
            score += val
        else:
            score -= val
    return score

def minimax(pieces, color, depth, alpha, beta):
    moves = legal_moves(pieces, color)
    if depth == 0 or not moves:
        # checkmate or stalemate
        if not moves:
            king_sq = find_king(pieces, color)
            if king_sq and is_square_attacked(pieces, king_sq, opponent(color)):
                return -99999
            else:
                return 0
        return evaluate(pieces, color)
    max_eval = -math.inf
    for mv in moves:
        new_pieces = make_move(pieces, mv)
        eval = -minimax(new_pieces, opponent(color), depth-1, -beta, -alpha)
        max_eval = max(max_eval, eval)
        alpha = max(alpha, eval)
        if alpha >= beta:
            break
    return max_eval

def policy(pieces: dict[str, str], to_play: str, memory: dict):
    color = 'white' if to_play == 'white' else 'black'
    moves = legal_moves(pieces, color)
    if not moves:
        return ("a1a1", memory)  # fallback, shouldn't happen

    best_score = -math.inf
    best_move = moves[0]
    for mv in moves:
        new_pieces = make_move(pieces, mv)
        score = -minimax(new_pieces, opponent(color), 1, -math.inf, math.inf)
        if score > best_score:
            best_score = score
            best_move = mv

    return best_move, memory
