
import random
import numpy as np

PIECE_VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}
PAWN_TABLE = np.array([
    [0,  0,  0,  0,  0,  0,  0,  0],
    [50, 50, 50, 50, 50, 50, 50, 50],
    [10, 10, 20, 30, 30, 20, 10, 10],
    [5,  5, 10, 25, 25, 10,  5,  5],
    [0,  0,  0, 20, 20,  0,  0,  0],
    [5, -5,-10,  0,  0,-10, -5,  5],
    [5, 10, 10,-20,-20, 10, 10,  5],
    [0,  0,  0,  0,  0,  0,  0,  0]
])
KNIGHT_TABLE = np.array([
    [-50,-40,-30,-30,-30,-30,-40,-50],
    [-40,-20,  0,  0,  0,  0,-20,-40],
    [-30,  0, 10, 15, 15, 10,  0,-30],
    [-30,  5, 15, 20, 20, 15,  5,-30],
    [-30,  0, 15, 20, 20, 15,  0,-30],
    [-30,  5, 10, 15, 15, 10,  5,-30],
    [-40,-20,  0,  5,  5,  0,-20,-40],
    [-50,-40,-30,-30,-30,-30,-40,-50]
])
BISHOP_TABLE = np.array([
    [-20,-10,-10,-10,-10,-10,-10,-20],
    [-10,  0,  0,  0,  0,  0,  0,-10],
    [-10,  0,  5, 10, 10,  5,  0,-10],
    [-10,  5,  5, 10, 10,  5,  5,-10],
    [-10,  0, 10, 10, 10, 10,  0,-10],
    [-10, 10, 10, 10, 10, 10, 10,-10],
    [-10,  5,  0,  0,  0,  0,  5,-10],
    [-20,-10,-10,-10,-10,-10,-10,-20]
])
ROOK_TABLE = np.array([
    [0,  0,  0,  0,  0,  0,  0,  0],
    [5, 10, 10, 10, 10, 10, 10,  5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [0,  0,  0,  5,  5,  0,  0,  0]
])
QUEEN_TABLE = np.array([
    [-20,-10,-10, -5, -5,-10,-10,-20],
    [-10,  0,  0,  0,  0,  0,  0,-10],
    [-10,  0,  5,  5,  5,  5,  0,-10],
    [-5,  0,  5,  5,  5,  5,  0, -5],
    [0,  0,  5,  5,  5,  5,  0, -5],
    [-10,  5,  5,  5,  5,  5,  0,-10],
    [-10,  0,  5,  0,  0,  0,  0,-10],
    [-20,-10,-10, -5, -5,-10,-10,-20]
])
KING_TABLE = np.array([
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-20,-30,-30,-40,-40,-30,-30,-20],
    [-10,-20,-20,-20,-20,-20,-20,-10],
    [20, 20,  0,  0,  0,  0, 20, 20],
    [20, 30, 10,  0,  0, 10, 30, 20]
])
KING_ENDGAME_TABLE = np.array([
    [-50,-40,-30,-20,-20,-30,-40,-50],
    [-30,-20,-10,  0,  0,-10,-20,-30],
    [-30,-10, 20, 30, 30, 20,-10,-30],
    [-30,-10, 30, 40, 40, 30,-10,-30],
    [-30,-10, 30, 40, 40, 30,-10,-30],
    [-30,-10, 20, 30, 30, 20,-10,-30],
    [-30,-30,  0,  0,  0,  0,-30,-30],
    [-50,-30,-30,-30,-30,-30,-30,-50]
])

def parse_move(move):
    if move[0] in 'NBRQK':
        piece_type = move[0]
        move = move[1:]
    else:
        piece_type = 'P'
    if 'x' in move:
        move = move.replace('x', '')
    if '+' in move or '#' in move:
        move = move[:-1]
    if '=' in move:
        move = move[:2]
    if len(move) == 3:
        move = move[1:]
    start_file, start_rank, end_file, end_rank = None, None, None, None
    if len(move) == 4:
        start_file, start_rank, end_file, end_rank = move[0], move[1], move[2], move[3]
    elif len(move) == 3:
        end_file, end_rank = move[0], move[1]
    elif len(move) == 2:
        end_file, end_rank = move[0], move[1]
    return {'piece_type': piece_type, 'start_file': start_file, 'start_rank': start_rank, 'end_file': end_file, 'end_rank': end_rank}

def square_to_coords(square):
    file = ord(square[0]) - ord('a')
    rank = int(square[1]) - 1
    return rank, file

def make_move(pieces, move_str, to_play):
    new_pieces = pieces.copy()
    move_info = parse_move(move_str)
    end_square = move_info['end_file'] + move_info['end_rank']
    end_rank, end_file = square_to_coords(end_square)
    color = 'w' if to_play == 'white' else 'b'
    if move_info['piece_type'] == 'O':
        if move_str == 'O-O':
            if color == 'w':
                new_pieces['e1'] = ''
                new_pieces['f1'] = 'wR'
                new_pieces['g1'] = 'wK'
                new_pieces['h1'] = ''
            else:
                new_pieces['e8'] = ''
                new_pieces['f8'] = 'bR'
                new_pieces['g8'] = 'bK'
                new_pieces['h8'] = ''
        elif move_str == 'O-O-O':
            if color == 'w':
                new_pieces['e1'] = ''
                new_pieces['d1'] = 'wR'
                new_pieces['c1'] = 'wK'
                new_pieces['a1'] = ''
            else:
                new_pieces['e8'] = ''
                new_pieces['d8'] = 'bR'
                new_pieces['c8'] = 'bK'
                new_pieces['a8'] = ''
    else:
        for square, piece in pieces.items():
            if piece and piece[0] == color and piece[1] == move_info['piece_type']:
                rank, file = square_to_coords(square)
                if move_info['start_file'] and move_info['start_file'] != square[0]:
                    continue
                if move_info['start_rank'] and move_info['start_rank'] != square[1]:
                    continue
                new_pieces[square] = ''
                break
        if '=' in move_str:
            promo_piece = move_str[-1]
            new_pieces[end_square] = color + promo_piece
        else:
            new_pieces[end_square] = color + move_info['piece_type']
    return new_pieces

def evaluate_position(pieces, to_play):
    score = 0
    piece_counts = {'w': {}, 'b': {}}
    for square, piece in pieces.items():
        if piece:
            color, piece_type = piece[0], piece[1]
            piece_counts[color][piece_type] = piece_counts[color].get(piece_type, 0) + 1
            value = PIECE_VALUES[piece_type]
            rank, file = square_to_coords(square)
            if piece_type == 'P':
                table = PAWN_TABLE
            elif piece_type == 'N':
                table = KNIGHT_TABLE
            elif piece_type == 'B':
                table = BISHOP_TABLE
            elif piece_type == 'R':
                table = ROOK_TABLE
            elif piece_type == 'Q':
                table = QUEEN_TABLE
            elif piece_type == 'K':
                table = KING_TABLE
            else:
                table = np.zeros((8, 8))
            if color == 'w':
                score += value + table[rank, file]
            else:
                score -= value + table[7-rank, file]
    white_material = sum(PIECE_VALUES[p] * count for p, count in piece_counts['w'].items())
    black_material = sum(PIECE_VALUES[p] * count for p, count in piece_counts['b'].items())
    if white_material < 20000 or black_material < 20000:
        for square, piece in pieces.items():
            if piece and piece[1] == 'K':
                rank, file = square_to_coords(square)
                if piece[0] == 'w':
                    score += KING_ENDGAME_TABLE[rank, file] - KING_TABLE[rank, file]
                else:
                    score -= KING_ENDGAME_TABLE[7-rank, file] - KING_TABLE[7-rank, file]
    if to_play == 'white':
        return score
    else:
        return -score

def minimax(pieces, depth, alpha, beta, maximizing_player, to_play):
    if depth == 0:
        return evaluate_position(pieces, to_play), None
    legal_moves = []
    color = 'w' if to_play == 'white' else 'b'
    for move in generate_pseudo_legal_moves(pieces, to_play):
        if is_legal_move(pieces, move, to_play):
            legal_moves.append(move)
    if not legal_moves:
        return evaluate_position(pieces, to_play), None
    best_move = None
    if maximizing_player:
        max_eval = float('-inf')
        for move in legal_moves:
            new_pieces = make_move(pieces, move, to_play)
            new_to_play = 'black' if to_play == 'white' else 'white'
            eval_score, _ = minimax(new_pieces, depth - 1, alpha, beta, False, new_to_play)
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval, best_move
    else:
        min_eval = float('inf')
        for move in legal_moves:
            new_pieces = make_move(pieces, move, to_play)
            new_to_play = 'black' if to_play == 'white' else 'white'
            eval_score, _ = minimax(new_pieces, depth - 1, alpha, beta, True, new_to_play)
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval, best_move

def generate_pseudo_legal_moves(pieces, to_play):
    moves = []
    color = 'w' if to_play == 'white' else 'b'
    for square, piece in pieces.items():
        if piece and piece[0] == color:
            piece_type = piece[1]
            if piece_type == 'P':
                generate_pawn_moves(moves, square, pieces, color)
            elif piece_type == 'N':
                generate_knight_moves(moves, square, pieces, color)
            elif piece_type == 'B':
                generate_bishop_moves(moves, square, pieces, color)
            elif piece_type == 'R':
                generate_rook_moves(moves, square, pieces, color)
            elif piece_type == 'Q':
                generate_queen_moves(moves, square, pieces, color)
            elif piece_type == 'K':
                generate_king_moves(moves, square, pieces, color)
    return moves

def is_legal_move(pieces, move, to_play):
    return True

def generate_pawn_moves(moves, square, pieces, color):
    rank, file = square_to_coords(square)
    direction = 1 if color == 'w' else -1
    start_rank = 1 if color == 'w' else 6
    end_square = chr(ord('a') + file) + str(rank + 1 + direction)
    if end_square in pieces and not pieces[end_square]:
        moves.append(square + end_square)
        if rank == start_rank:
            end_square2 = chr(ord('a') + file) + str(rank + 2 + 2 * direction)
            if end_square2 in pieces and not pieces[end_square2]:
                moves.append(square + end_square2)
    for df in [-1, 1]:
        if 0 <= file + df < 8:
            capture_square = chr(ord('a') + file + df) + str(rank + 1 + direction)
            if capture_square in pieces and pieces[capture_square] and pieces[capture_square][0] != color:
                moves.append(square + capture_square)

def generate_knight_moves(moves, square, pieces, color):
    rank, file = square_to_coords(square)
    offsets = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
    for dr, df in offsets:
        nr, nf = rank + dr, file + df
        if 0 <= nr < 8 and 0 <= nf < 8:
            end_square = chr(ord('a') + nf) + str(nr + 1)
            if end_square in pieces and (not pieces[end_square] or pieces[end_square][0] != color):
                moves.append('N' + square + end_square)

def generate_bishop_moves(moves, square, pieces, color):
    rank, file = square_to_coords(square)
    offsets = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    for dr, df in offsets:
        for i in range(1, 8):
            nr, nf = rank + i * dr, file + i * df
            if 0 <= nr < 8 and 0 <= nf < 8:
                end_square = chr(ord('a') + nf) + str(nr + 1)
                if end_square in pieces:
                    if not pieces[end_square]:
                        moves.append('B' + square + end_square)
                    elif pieces[end_square][0] != color:
                        moves.append('B' + square + end_square)
                        break
                    else:
                        break
            else:
                break

def generate_rook_moves(moves, square, pieces, color):
    rank, file = square_to_coords(square)
    offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    for dr, df in offsets:
        for i in range(1, 8):
            nr, nf = rank + i * dr, file + i * df
            if 0 <= nr < 8 and 0 <= nf < 8:
                end_square = chr(ord('a') + nf) + str(nr + 1)
                if end_square in pieces:
                    if not pieces[end_square]:
                        moves.append('R' + square + end_square)
                    elif pieces[end_square][0] != color:
                        moves.append('R' + square + end_square)
                        break
                    else:
                        break
            else:
                break

def generate_queen_moves(moves, square, pieces, color):
    rank, file = square_to_coords(square)
    offsets = [(-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)]
    for dr, df in offsets:
        for i in range(1, 8):
            nr, nf = rank + i * dr, file + i * df
            if 0 <= nr < 8 and 0 <= nf < 8:
                end_square = chr(ord('a') + nf) + str(nr + 1)
                if end_square in pieces:
                    if not pieces[end_square]:
                        moves.append('Q' + square + end_square)
                    elif pieces[end_square][0] != color:
                        moves.append('Q' + square + end_square)
                        break
                    else:
                        break
            else:
                break

def generate_king_moves(moves, square, pieces, color):
    rank, file = square_to_coords(square)
    offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    for dr, df in offsets:
        nr, nf = rank + dr, file + df
        if 0 <= nr < 8 and 0 <= nf < 8:
            end_square = chr(ord('a') + nf) + str(nr + 1)
            if end_square in pieces and (not pieces[end_square] or pieces[end_square][0] != color):
                moves.append('K' + square + end_square)
    if square == ('e1' if color == 'w' else 'e8'):
        if pieces.get(chr(ord('a') + file - 4) + str(rank + 1), '') == color + 'R':
            moves.append('O-O-O')
        if pieces.get(chr(ord('a') + file + 3) + str(rank + 1), '') == color + 'R':
            moves.append('O-O')

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    if len(legal_moves) == 1:
        return legal_moves[0]
    _, best_move = minimax(pieces, 3, float('-inf'), float('inf'), True, to_play)
    if best_move and best_move in legal_moves:
        return best_move
    captures = [move for move in legal_moves if 'x' in move]
    checks = [move for move in legal_moves if '+' in move or '#' in move]
    pawns = [move for move in legal_moves if move[0].islower()]
    if checks:
        return random.choice(checks)
    if captures:
        return random.choice(captures)
    if pawns:
        return random.choice(pawns)
    return random.choice(legal_moves)
