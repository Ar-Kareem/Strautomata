
import sys
from copy import deepcopy

piece_values = {'Q': 9, 'R': 5, 'B': 3, 'N': 3, 'P': 1, 'K': 0}

pawn_table = [
    [0,  0,  0,  0,  0,  0,  0,  0],
    [50, 50, 50, 50, 50, 50, 50, 50],
    [10, 10, 20, 30, 30, 20, 10, 10],
    [5,  5, 10, 25, 25, 10,  5,  5],
    [0,  0,  0, 20, 20,  0,  0,  0],
    [5, -5,-10,  0,  0,-10, -5,  5],
    [5, 10, 10,-20,-20, 10, 10,  5],
    [0,  0,  0,  0,  0,  0,  0,  0]
]

knight_table = [
    [-50,-40,-30,-30,-30,-30,-40,-50],
    [-40,-20,  0,  0,  0,  0,-20,-40],
    [-30,  0, 10, 15, 15, 10,  0,-30],
    [-30,  5, 15, 20, 20, 15,  5,-30],
    [-30,  0, 15, 20, 20, 15,  0,-30],
    [-30,  5, 10, 15, 15, 10,  5,-30],
    [-40,-20,  0,  5,  5,  0,-20,-40],
    [-50,-40,-30,-30,-30,-30,-40,-50]
]

bishop_table = [
    [-20,-10,-10,-10,-10,-10,-10,-20],
    [-10,  0,  0,  0,  0,  0,  0,-10],
    [-10,  0,  5, 10, 10,  5,  0,-10],
    [-10,  5,  5, 10, 10,  5,  5,-10],
    [-10,  0, 10, 10, 10, 10,  0,-10],
    [-10, 10, 10, 10, 10, 10, 10,-10],
    [-10,  5,  0,  0,  0,  0,  5,-10],
    [-20,-10,-10,-10,-10,-10,-10,-20]
]

rook_table = [
    [0,  0,  0,  0,  0,  0,  0,  0],
    [5, 10, 10, 10, 10, 10, 10,  5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [0,  0,  0,  5,  5,  0,  0,  0]
]

queen_table = [
    [-20,-10,-10, -5, -5,-10,-10,-20],
    [-10,  0,  0,  0,  0,  0,  0,-10],
    [-10,  0,  5,  5,  5,  5,  0,-10],
    [-5,  0,  5,  5,  5,  5,  0, -5],
    [0,  0,  5,  5,  5,  5,  0, -5],
    [-10,  5,  5,  5,  5,  5,  0,-10],
    [-10,  0,  5,  0,  0,  0,  0,-10],
    [-20,-10,-10, -5, -5,-10,-10,-20]
]

king_table = [
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-20,-30,-30,-40,-40,-30,-30,-20],
    [-10,-20,-20,-20,-20,-20,-20,-10],
    [ 20, 20,  0,  0,  0,  0, 20, 20],
    [ 20, 30, 10,  0,  0, 10, 30, 20]
]

tables = {
    'P': pawn_table,
    'N': knight_table,
    'B': bishop_table,
    'R': rook_table,
    'Q': queen_table,
    'K': king_table
}

def get_pst_value(piece_type, square, is_white):
    file = ord(square[0]) - ord('a')
    rank = int(square[1]) - 1
    if not is_white:
        rank = 7 - rank
    table = tables.get(piece_type, [[0]*8 for _ in range(8)])
    return table[rank][file]

def square_to_coords(square):
    file = ord(square[0]) - ord('a')
    rank = int(square[1]) - 1
    return (file, rank)

def coords_to_square(file, rank):
    return chr(file + ord('a')) + str(rank + 1)

def generate_moves(pieces, color):
    moves = []
    current_color = color[0].lower()
    for square, piece in pieces.items():
        if piece[0] != current_color:
            continue
        piece_type = piece[1]
        if piece_type == 'P':
            moves += generate_pawn_moves(square, pieces, color)
        elif piece_type == 'N':
            moves += generate_knight_moves(square, pieces, color)
        elif piece_type == 'B':
            moves += generate_bishop_moves(square, pieces, color)
        elif piece_type == 'R':
            moves += generate_rook_moves(square, pieces, color)
        elif piece_type == 'Q':
            moves += generate_queen_moves(square, pieces, color)
        elif piece_type == 'K':
            moves += generate_king_moves(square, pieces, color)
    return moves

def generate_pawn_moves(square, pieces, color):
    moves = []
    is_white = color == 'white'
    direction = 1 if is_white else -1
    start_rank = int(square[1])
    next_rank = start_rank + direction
    if next_rank < 1 or next_rank > 8:
        return []
    current_file = square[0]
    next_square = current_file + str(next_rank)
    if next_square not in pieces:
        moves.append(square + next_square)
        if (start_rank == 2 and is_white) or (start_rank == 7 and not is_white):
            double_rank = next_rank + direction
            double_square = current_file + str(double_rank)
            if double_square not in pieces:
                moves.append(square + double_square)
    
    capture_files = []
    if current_file != 'a':
        capture_files.append(chr(ord(current_file) - 1))
    if current_file != 'h':
        capture_files.append(chr(ord(current_file) + 1))
    
    for cf in capture_files:
        target_square = cf + str(next_rank)
        if target_square in pieces and pieces[target_square][0] != color[0].lower():
            moves.append(square + target_square)
        if (target_square not in pieces and
            (is_white and next_rank == 6) or (not is_white and next_rank == 3)):
            pass
    
    promotion_rank = '8' if is_white else '1'
    if next_rank == int(promotion_rank):
        for move in moves.copy():
            if move[3:] == promotion_rank:
                for promote in ['q', 'r', 'b', 'n']:
                    moves.append(move + promote)
                moves.remove(move)
    return moves

def generate_knight_moves(square, pieces, color):
    moves = []
    file, rank = square_to_coords(square)
    offsets = [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
               (1, -2), (1, 2), (2, -1), (2, 1)]
    for df, dr in offsets:
        new_file = file + df
        new_rank = rank + dr
        if 0 <= new_file < 8 and 0 <= new_rank < 8:
            new_square = coords_to_square(new_file, new_rank)
            if new_square not in pieces or pieces[new_square][0] != color[0].lower():
                moves.append(square + new_square)
    return moves

def generate_line_moves(square, pieces, color, directions):
    moves = []
    current_file, current_rank = square_to_coords(square)
    current_color = color[0].lower()
    for df, dr in directions:
        new_file, new_rank = current_file + df, current_rank + dr
        while 0 <= new_file < 8 and 0 <= new_rank < 8:
            new_square = coords_to_square(new_file, new_rank)
            if new_square in pieces:
                if pieces[new_square][0] != current_color:
                    moves.append(square + new_square)
                break
            else:
                moves.append(square + new_square)
            new_file += df
            new_rank += dr
    return moves

def generate_bishop_moves(square, pieces, color):
    directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    return generate_line_moves(square, pieces, color, directions)

def generate_rook_moves(square, pieces, color):
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    return generate_line_moves(square, pieces, color, directions)

def generate_queen_moves(square, pieces, color):
    return generate_bishop_moves(square, pieces, color) + generate_rook_moves(square, pieces, color)

def generate_king_moves(square, pieces, color):
    moves = []
    file, rank = square_to_coords(square)
    current_color = color[0].lower()
    offsets = [(-1, -1), (-1, 0), (-1, 1),
               (0, -1),          (0, 1),
               (1, -1),  (1, 0), (1, 1)]
    for df, dr in offsets:
        new_file = file + df
        new_rank = rank + dr
        if 0 <= new_file < 8 and 0 <= new_rank < 8:
            new_square = coords_to_square(new_file, new_rank)
            if new_square not in pieces or pieces[new_square][0] != current_color:
                moves.append(square + new_square)
    return moves

def is_in_check(pieces, color):
    current_color = color[0].lower()
    king_square = None
    for square, piece in pieces.items():
        if piece == current_color + 'K':
            king_square = square
            break
    if not king_square:
        return False
    opponent_color = 'w' if current_color == 'b' else 'b'
    kf, kr = square_to_coords(king_square)
    for square, piece in pieces.items():
        if piece[0] != opponent_color:
            continue
        pt = piece[1]
        if pt == 'P':
            direction = -1 if opponent_color == 'w' else 1
            for df in (-1, 1):
                new_rank = kr + direction
                new_file = kf + df
                if 0 <= new_file < 8 and 0 <= new_rank < 8:
                    if square_to_coords(square) == (new_file, new_rank):
                        return True
        elif pt == 'N':
            offsets = [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
                       (1, -2), (1, 2), (2, -1), (2, 1)]
            for df, dr in offsets:
                if square_to_coords(square) == (kf + df, kr + dr):
                    return True
        elif pt in ['B', 'Q']:
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
            for df, dr in directions:
                f, r = square_to_coords(square)
                if (kf - f) == 0 or (kr - r) == 0 or abs(kf - f) != abs(kr - r):
                    continue
                steps = max(abs(kf - f), abs(kr - r))
                blocked = False
                for step in range(1, steps):
                    check_f = f + step * df // steps * steps
                    check_r = r + step * dr // steps * steps
                    check_sq = coords_to_square(check_f, check_r)
                    if check_sq in pieces and check_sq != square:
                        blocked = True
                        break
                if not blocked:
                    return True
        elif pt in ['R', 'Q']:
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            for df, dr in directions:
                f, r = square_to_coords(square)
                if (kf - f) != 0 and (kr - r) != 0:
                    continue
                steps = max(abs(kf - f), abs(kr - r))
                blocked = False
                for step in range(1, steps):
                    check_f = f + (kf - f) * step // steps
                    check_r = r + (kr - r) * step // steps
                    check_sq = coords_to_square(check_f, check_r)
                    if check_sq in pieces and check_sq != square:
                        blocked = True
                        break
                if not blocked:
                    return True
        elif pt == 'K':
            if abs(kf - square_to_coords(square)[0]) <= 1 and abs(kr - square_to_coords(square)[1]) <= 1:
                return True
    return False

def get_legal_moves(pieces, color):
    pseudo_legal = generate_moves(pieces, color)
    legal_moves = []
    for move in pseudo_legal:
        new_pieces = deepcopy(pieces)
        start = move[:2]
        end = move[2:4]
        piece = new_pieces[start]
        del new_pieces[start]
        if len(move) == 5:
            new_pieces[end] = piece[0] + move[4].upper()
        else:
            new_pieces[end] = piece
        if not is_in_check(new_pieces, color):
            legal_moves.append(move)
    return legal_moves

def evaluate_move(move, pieces, color):
    current_color = color[0].lower()
    start = move[:2]
    end = move[2:4]
    piece_type = pieces[start][1]
    
    capture_value = 0
    if end in pieces and pieces[end][0] != current_color:
        captured_piece = pieces[end][1]
        capture_value = piece_values.get(captured_piece, 0)
    
    promotion_value = 0
    if len(move) == 5:
        promoted_to = move[4].upper()
        if promoted_to in piece_values:
            promotion_value = piece_values[promoted_to] - piece_values['P']
    
    is_white = color == 'white'
    start_value = get_pst_value(piece_type, start, is_white)
    end_value = get_pst_value(piece_type, end, is_white)
    positional_value = end_value - start_value
    
    total = capture_value * 10 + positional_value + promotion_value * 10
    return total

def policy(pieces: dict[str, str], to_play: str) -> str:
    legal_moves = get_legal_moves(pieces, to_play)
    if not legal_moves:
        return ''
    
    best_move = None
    best_score = -sys.maxsize
    for move in legal_moves:
        score = evaluate_move(move, pieces, to_play)
        if score > best_score:
            best_score = score
            best_move = move
    return best_move if best_move else legal_moves[0]
