
import math
import random

# Piece values
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

def square_to_coords(sq):
    return FILES.index(sq[0]), RANKS.index(sq[1])

def coords_to_square(x, y):
    return FILES[x] + RANKS[y]

def opponent(color):
    return 'b' if color == 'w' else 'w'

def find_king(pieces, color):
    for sq, pc in pieces.items():
        if pc == color + 'K':
            return sq
    return None

def is_on_board(x, y):
    return 0 <= x < 8 and 0 <= y < 8

def is_attacked(pieces, square, by_color):
    x, y = square_to_coords(square)
    # Pawn attacks
    if by_color == 'w':
        pawn_dirs = [(-1, 1), (1, 1)]
    else:
        pawn_dirs = [(-1, -1), (1, -1)]
    for dx, dy in pawn_dirs:
        nx, ny = x + dx, y + dy
        if is_on_board(nx, ny):
            sq = coords_to_square(nx, ny)
            if pieces.get(sq) == by_color + 'P':
                return True

    # Knight attacks
    for dx, dy in [(1,2),(2,1),(2,-1),(1,-2),(-1,-2),(-2,-1),(-2,1),(-1,2)]:
        nx, ny = x + dx, y + dy
        if is_on_board(nx, ny):
            sq = coords_to_square(nx, ny)
            if pieces.get(sq) == by_color + 'N':
                return True

    # King adjacent
    for dx in [-1,0,1]:
        for dy in [-1,0,1]:
            if dx == 0 and dy == 0:
                continue
            nx, ny = x + dx, y + dy
            if is_on_board(nx, ny):
                sq = coords_to_square(nx, ny)
                if pieces.get(sq) == by_color + 'K':
                    return True

    # Sliding pieces
    directions = [
        (1,0),(-1,0),(0,1),(0,-1),  # rook/queen
        (1,1),(1,-1),(-1,1),(-1,-1) # bishop/queen
    ]
    for dx, dy in directions:
        nx, ny = x + dx, y + dy
        while is_on_board(nx, ny):
            sq = coords_to_square(nx, ny)
            if sq in pieces:
                pc = pieces[sq]
                if pc[0] == by_color:
                    pt = pc[1]
                    if (dx == 0 or dy == 0) and (pt == 'R' or pt == 'Q'):
                        return True
                    if (dx != 0 and dy != 0) and (pt == 'B' or pt == 'Q'):
                        return True
                break
            nx += dx
            ny += dy
    return False

def generate_pseudo_moves(pieces, color):
    moves = []
    for sq, pc in pieces.items():
        if pc[0] != color:
            continue
        x, y = square_to_coords(sq)
        pt = pc[1]
        if pt == 'P':
            direction = 1 if color == 'w' else -1
            start_rank = 1 if color == 'w' else 6
            promotion_rank = 7 if color == 'w' else 0
            # forward one
            nx, ny = x, y + direction
            if is_on_board(nx, ny):
                dest = coords_to_square(nx, ny)
                if dest not in pieces:
                    if ny == promotion_rank:
                        for promo in ['q','r','b','n']:
                            moves.append(sq + dest + promo)
                    else:
                        moves.append(sq + dest)
                    # forward two
                    if y == start_rank:
                        ny2 = y + 2*direction
                        dest2 = coords_to_square(nx, ny2)
                        if dest2 not in pieces:
                            moves.append(sq + dest2)
            # captures
            for dx in [-1, 1]:
                nx, ny = x + dx, y + direction
                if is_on_board(nx, ny):
                    dest = coords_to_square(nx, ny)
                    if dest in pieces and pieces[dest][0] == opponent(color):
                        if ny == promotion_rank:
                            for promo in ['q','r','b','n']:
                                moves.append(sq + dest + promo)
                        else:
                            moves.append(sq + dest)
        elif pt == 'N':
            for dx, dy in [(1,2),(2,1),(2,-1),(1,-2),(-1,-2),(-2,-1),(-2,1),(-1,2)]:
                nx, ny = x + dx, y + dy
                if is_on_board(nx, ny):
                    dest = coords_to_square(nx, ny)
                    if dest not in pieces or pieces[dest][0] != color:
                        moves.append(sq + dest)
        elif pt == 'K':
            for dx in [-1,0,1]:
                for dy in [-1,0,1]:
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = x + dx, y + dy
                    if is_on_board(nx, ny):
                        dest = coords_to_square(nx, ny)
                        if dest not in pieces or pieces[dest][0] != color:
                            moves.append(sq + dest)
            # Castling (assume allowed if in initial squares and path clear)
            if color == 'w' and sq == 'e1':
                if pieces.get('h1') == 'wR' and all(s not in pieces for s in ['f1','g1']):
                    moves.append('e1g1')
                if pieces.get('a1') == 'wR' and all(s not in pieces for s in ['b1','c1','d1']):
                    moves.append('e1c1')
            if color == 'b' and sq == 'e8':
                if pieces.get('h8') == 'bR' and all(s not in pieces for s in ['f8','g8']):
                    moves.append('e8g8')
                if pieces.get('a8') == 'bR' and all(s not in pieces for s in ['b8','c8','d8']):
                    moves.append('e8c8')
        elif pt in ('B','R','Q'):
            dirs = []
            if pt in ('B','Q'):
                dirs += [(1,1),(1,-1),(-1,1),(-1,-1)]
            if pt in ('R','Q'):
                dirs += [(1,0),(-1,0),(0,1),(0,-1)]
            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                while is_on_board(nx, ny):
                    dest = coords_to_square(nx, ny)
                    if dest in pieces:
                        if pieces[dest][0] != color:
                            moves.append(sq + dest)
                        break
                    moves.append(sq + dest)
                    nx += dx
                    ny += dy
    return moves

def make_move(pieces, move):
    new_pieces = pieces.copy()
    start = move[0:2]
    end = move[2:4]
    promo = move[4] if len(move) > 4 else None
    piece = new_pieces.pop(start)
    # Castling rook move
    if piece[1] == 'K' and abs(FILES.index(start[0]) - FILES.index(end[0])) == 2:
        if end == 'g1':
            new_pieces.pop('h1', None)
            new_pieces['f1'] = 'wR'
        elif end == 'c1':
            new_pieces.pop('a1', None)
            new_pieces['d1'] = 'wR'
        elif end == 'g8':
            new_pieces.pop('h8', None)
            new_pieces['f8'] = 'bR'
        elif end == 'c8':
            new_pieces.pop('a8', None)
            new_pieces['d8'] = 'bR'
    # capture
    if end in new_pieces:
        new_pieces.pop(end)
    # promotion
    if promo:
        new_pieces[end] = piece[0] + promo.upper()
    else:
        new_pieces[end] = piece
    return new_pieces

def legal_moves(pieces, color):
    moves = []
    for mv in generate_pseudo_moves(pieces, color):
        new_p = make_move(pieces, mv)
        king_sq = find_king(new_p, color)
        if king_sq and not is_attacked(new_p, king_sq, opponent(color)):
            # For castling, ensure no square crossed is attacked
            if mv in ('e1g1','e1c1','e8g8','e8c8'):
                if color == 'w':
                    if mv == 'e1g1':
                        if is_attacked(pieces, 'e1', 'b') or is_attacked(pieces, 'f1', 'b') or is_attacked(pieces, 'g1', 'b'):
                            continue
                    else:
                        if is_attacked(pieces, 'e1', 'b') or is_attacked(pieces, 'd1', 'b') or is_attacked(pieces, 'c1', 'b'):
                            continue
                else:
                    if mv == 'e8g8':
                        if is_attacked(pieces, 'e8', 'w') or is_attacked(pieces, 'f8', 'w') or is_attacked(pieces, 'g8', 'w'):
                            continue
                    else:
                        if is_attacked(pieces, 'e8', 'w') or is_attacked(pieces, 'd8', 'w') or is_attacked(pieces, 'c8', 'w'):
                            continue
            moves.append(mv)
    return moves

def evaluate(pieces):
    score = 0
    for sq, pc in pieces.items():
        val = PIECE_VALUES[pc[1]]
        if pc[0] == 'w':
            score += val
        else:
            score -= val
    return score

MATE = 100000

def negamax(pieces, color, depth, alpha, beta):
    moves = legal_moves(pieces, color)
    if depth == 0 or not moves:
        if not moves:
            king_sq = find_king(pieces, color)
            if king_sq and is_attacked(pieces, king_sq, opponent(color)):
                return -MATE + (2 - depth)
            else:
                return 0
        base = evaluate(pieces)
        return base if color == 'w' else -base

    best = -math.inf
    # order captures first
    def move_score(mv):
        end = mv[2:4]
        return 1 if end in pieces else 0
    moves.sort(key=move_score, reverse=True)

    for mv in moves:
        new_p = make_move(pieces, mv)
        score = -negamax(new_p, opponent(color), depth - 1, -beta, -alpha)
        if score > best:
            best = score
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best

def policy(pieces: dict[str, str], to_play: str) -> str:
    color = 'w' if to_play == 'white' else 'b'
    moves = legal_moves(pieces, color)
    if not moves:
        return ""
    best_move = moves[0]
    best_score = -math.inf
    for mv in moves:
        new_p = make_move(pieces, mv)
        score = -negamax(new_p, opponent(color), 2, -math.inf, math.inf)
        if score > best_score:
            best_score = score
            best_move = mv
    return best_move
