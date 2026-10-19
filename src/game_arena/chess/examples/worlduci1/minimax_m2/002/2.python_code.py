
import copy

def square_to_index(square):
    file = square[0]
    rank = int(square[1])
    return (ord(file) - ord('a')) * 8 + (rank - 1)

def rotate_square(square):
    file = square[0]
    rank = square[1]
    new_file = chr(ord('a') + (ord('h') - ord(file)))
    new_rank = str(9 - int(rank))
    return new_file + new_rank

# Material values
material = {
    'P': 100,
    'N': 320,
    'B': 330,
    'R': 500,
    'Q': 900,
    'K': 20000
}

# Piece-square tables
pawn_table = [
    0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
    5,  5, 10, 25, 25, 10,  5,  5,
    0,  0,  0, 20, 20,  0,  0,  0,
    5, -5,-10,  0,  0,-10, -5,  5,
    5, 10, 10,-20,-20, 10, 10,  5,
    0,  0,  0,  0,  0,  0,  0,  0
]

knight_table = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50
]

bishop_table = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -20,-10,-10,-10,-10,-10,-10,-20
]

rook_table = [
     0,  0,  0,  5,  5,  0,  0,  0,
     5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     0,  0,  0,  5,  5,  0,  0,  0
]

queen_table = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -10,  5,  5,  5,  5,  5,  0,-10,
     -5,  0,  5,  5,  5,  5,  0, -5,
      0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20
]

king_table = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
     20, 20,  0,  0,  0,  0, 20, 20,
     20, 30, 10,  0,  0, 10, 30, 20
]

piece_square_table = {
    'P': pawn_table,
    'N': knight_table,
    'B': bishop_table,
    'R': rook_table,
    'Q': queen_table,
    'K': king_table
}

def evaluate(pieces, player):
    evaluation = 0
    for square, piece in pieces.items():
        color = piece[0]
        piece_type = piece[1]
        if color == 'b':
            rotated_square = rotate_square(square)
            table_index = square_to_index(rotated_square)
        else:
            table_index = square_to_index(square)
        table_value = piece_square_table[piece_type][table_index]
        if color == 'w':
            evaluation += material[piece_type] + table_value
        else:
            evaluation -= material[piece_type] + table_value
    if player == 'black':
        evaluation = -evaluation
    return evaluation

def piece_attacks_square(pieces, piece_square, piece, target_square):
    color = piece[0]
    piece_type = piece[1]
    file1 = piece_square[0]
    rank1 = int(piece_square[1])
    file2 = target_square[0]
    rank2 = int(target_square[1])
    df = ord(file2) - ord(file1)
    dr = rank2 - rank1

    if piece_type == 'P':
        if color == 'w' and dr == 1 and abs(df) == 1:
            return True
        elif color == 'b' and dr == -1 and abs(df) == 1:
            return True
        return False
    elif piece_type == 'N':
        if (abs(df)==1 and abs(dr)==2) or (abs(df)==2 and abs(dr)==1):
            return True
        return False
    elif piece_type == 'B':
        if abs(df) == abs(dr) and df != 0:
            step_file = 1 if df > 0 else -1
            step_rank = 1 if dr > 0 else -1
            current_file = chr(ord(file1) + step_file)
            current_rank = rank1 + step_rank
            while current_file != file2 and current_rank != rank2:
                current_square = current_file + str(current_rank)
                if current_square in pieces:
                    return False
                current_file = chr(ord(current_file) + step_file)
                current_rank += step_rank
            return True
        return False
    elif piece_type == 'R':
        if df == 0 or dr == 0:
            if df == 0:
                step_file = 0
                step_rank = 1 if dr > 0 else -1
            else:
                step_file = 1 if df > 0 else -1
                step_rank = 0
            current_file = chr(ord(file1) + step_file)
            current_rank = rank1 + step_rank
            while current_file != file2 or current_rank != rank2:
                current_square = current_file + str(current_rank)
                if current_square in pieces:
                    return False
                current_file = chr(ord(current_file) + step_file)
                current_rank += step_rank
            return True
        return False
    elif piece_type == 'Q':
        if (abs(df)==abs(dr) and df!=0) or (df==0 or dr==0):
            if df == 0:
                step_file = 0
                step_rank = 1 if dr > 0 else -1
            elif dr == 0:
                step_file = 1 if df > 0 else -1
                step_rank = 0
            else:
                step_file = 1 if df > 0 else -1
                step_rank = 1 if dr > 0 else -1
            current_file = chr(ord(file1) + step_file)
            current_rank = rank1 + step_rank
            while current_file != file2 or current_rank != rank2:
                current_square = current_file + str(current_rank)
                if current_square in pieces:
                    return False
                current_file = chr(ord(current_file) + step_file)
                current_rank += step_rank
            return True
        return False
    elif piece_type == 'K':
        if abs(df) <= 1 and abs(dr) <= 1 and (df != 0 or dr != 0):
            return True
        return False
    return False

def is_square_attacked(pieces, square, attacker_color):
    for s, p in pieces.items():
        if p[0] == attacker_color:
            if piece_attacks_square(pieces, s, p, square):
                return True
    return False

def is_in_check(pieces, color):
    for square, piece in pieces.items():
        if piece == color + 'K':
            king_square = square
            break
    else:
        return False
    opponent_color = 'w' if color == 'b' else 'b'
    return is_square_attacked(pieces, king_square, opponent_color)

def generate_piece_moves(pieces, square, piece):
    color = piece[0]
    piece_type = piece[1]
    moves = []
    file = square[0]
    rank = int(square[1])

    if piece_type == 'P':
        direction = 1 if color == 'w' else -1
        new_square = file + str(rank + direction)
        if new_square not in pieces:
            moves.append(new_square)
            if (color == 'w' and rank == 2) or (color == 'b' and rank == 7):
                new_square2 = file + str(rank + 2 * direction)
                if new_square2 not in pieces:
                    moves.append(new_square2)
        for new_file in [chr(ord(file)-1), chr(ord(file)+1)]:
            new_square = new_file + str(rank + direction)
            if new_square in pieces and pieces[new_square][0] != color:
                moves.append(new_square)
    elif piece_type == 'N':
        knight_moves = [(1,2), (1,-2), (-1,2), (-1,-2), (2,1), (2,-1), (-2,1), (-2,-1)]
        for df, dr in knight_moves:
            new_file = chr(ord(file)+df)
            new_rank = rank + dr
            if 'a' <= new_file <= 'h' and 1 <= new_rank <= 8:
                new_square = new_file + str(new_rank)
                if new_square not in pieces or pieces[new_square][0] != color:
                    moves.append(new_square)
    elif piece_type in ['B', 'R', 'Q']:
        directions = []
        if piece_type in ['B', 'Q']:
            directions += [(1,1), (1,-1), (-1,1), (-1,-1)]
        if piece_type in ['R', 'Q']:
            directions += [(1,0), (-1,0), (0,1), (0,-1)]
        for df, dr in directions:
            new_file = file
            new_rank = rank
            while True:
                new_file = chr(ord(new_file)+df)
                new_rank += dr
                if not ('a' <= new_file <= 'h' and 1 <= new_rank <= 8):
                    break
                new_square = new_file + str(new_rank)
                if new_square in pieces:
                    if pieces[new_square][0] != color:
                        moves.append(new_square)
                    break
                else:
                    moves.append(new_square)
    elif piece_type == 'K':
        for df in [-1, 0, 1]:
            for dr in [-1, 0, 1]:
                if df == 0 and dr == 0:
                    continue
                new_file = chr(ord(file)+df)
                new_rank = rank + dr
                if 'a' <= new_file <= 'h' and 1 <= new_rank <= 8:
                    new_square = new_file + str(new_rank)
                    if new_square not in pieces or pieces[new_square][0] != color:
                        moves.append(new_square)
        if color == 'w':
            if square == 'e1':
                if 'g1' not in pieces and 'f1' not in pieces and 'h1' in pieces and pieces['h1'] == 'wR':
                    if not (is_square_attacked(pieces, 'e1', 'black') or is_square_attacked(pieces, 'f1', 'black') or is_square_attacked(pieces, 'g1', 'black')):
                        moves.append('g1')
                if 'c1' not in pieces and 'd1' not in pieces and 'b1' not in pieces and 'a1' in pieces and pieces['a1'] == 'wR':
                    if not (is_square_attacked(pieces, 'e1', 'black') or is_square_attacked(pieces, 'd1', 'black') or is_square_attacked(pieces, 'c1', 'black')):
                        moves.append('c1')
        else:
            if square == 'e8':
                if 'g8' not in pieces and 'f8' not in pieces and 'h8' in pieces and pieces['h8'] == 'bR':
                    if not (is_square_attacked(pieces, 'e8', 'white') or is_square_attacked(pieces, 'f8', 'white') or is_square_attacked(pieces, 'g8', 'white')):
                        moves.append('g8')
                if 'c8' not in pieces and 'd8' not in pieces and 'b8' not in pieces and 'a8' in pieces and pieces['a8'] == 'bR':
                    if not (is_square_attacked(pieces, 'e8', 'white') or is_square_attacked(pieces, 'd8', 'white') or is_square_attacked(pieces, 'c8', 'white')):
                        moves.append('c8')
    return [square+move for move in moves]

def simulate_move(pieces, move, color):
    new_pieces = copy.deepcopy(pieces)
    from_square = move[:2]
    to_square = move[2:]
    piece = new_pieces[from_square]
    del new_pieces[from_square]
    if to_square in new_pieces and new_pieces[to_square][0] != color:
        del new_pieces[to_square]
    if piece[1] == 'P' and (to_square[1]=='8' or to_square[1]=='1'):
        piece = color + 'Q'
    new_pieces[to_square] = piece
    if piece[1]=='K' and from_square in ['e1', 'e8']:
        if to_square == 'g1':
            new_pieces['f1'] = new_pieces['h1']
            del new_pieces['h1']
        elif to_square == 'c1':
            new_pieces['d1'] = new_pieces['a1']
            del new_pieces['a1']
        elif to_square == 'g8':
            new_pieces['f8'] = new_pieces['h8']
            del new_pieces['h8']
        elif to_square == 'c8':
            new_pieces['d8'] = new_pieces['a8']
            del new_pieces['a8']
    return new_pieces

def generate_legal_moves(pieces, color):
    legal_moves = []
    for square, piece in pieces.items():
        if piece[0] == color:
            moves = generate_piece_moves(pieces, square, piece)
            for move in moves:
                new_pieces = simulate_move(pieces, move, color)
                if not is_in_check(new_pieces, color):
                    legal_moves.append(move)
    return legal_moves

def policy(pieces, to_play):
    legal_moves = generate_legal_moves(pieces, to_play)
    for move in legal_moves:
        new_pieces = simulate_move(pieces, move, to_play)
        opponent = 'black' if to_play == 'white' else 'white'
        opponent_moves = generate_legal_moves(new_pieces, opponent)
        if len(opponent_moves) == 0 and is_in_check(new_pieces, opponent):
            return move
    best_move = None
    best_evaluation = -float('inf')
    for move in legal_moves:
        new_pieces = simulate_move(pieces, move, to_play)
        evaluation = evaluate(new_pieces, to_play)
        if evaluation > best_evaluation:
            best_evaluation = evaluation
            best_move = move
    return best_move
