
import copy

def square_to_coords(s):
    return (ord(s[0]) - ord('a'), int(s[1]) - 1)

def coords_to_square(f, r):
    return chr(ord('a') + f) + str(r + 1)

def knight_attack(knight_square, target_square):
    sf, sr = square_to_coords(knight_square)
    tf, tr = square_to_coords(target_square)
    return ((abs(tf - sf), abs(tr - sr)) == (1, 2)) or ((abs(tf - sf), abs(tr - sr)) == (2, 1))

def bishop_attack(bishop_square, target_square, board):
    f1, r1 = square_to_coords(bishop_square)
    f2, r2 = square_to_coords(target_square)
    if abs(f1 - f2) != abs(r1 - r2):
        return False
    dir_f = 1 if f2 > f1 else -1
    dir_r = 1 if r2 > r1 else -1
    f, r = f1 + dir_f, r1 + dir_r
    while 0 <= f < 8 and 0 <= r < 8:
        new_sq = coords_to_square(f, r)
        if new_sq == target_square:
            return True
        if new_sq in board and board[new_sq][0] == bishop_square[0]:
            break
        f += dir_f
        r += dir_r
    return False

def can_attack(square, piece_type, target_square, board):
    if piece_type == 'N':
        return knight_attack(square, target_square)
    elif piece_type == 'B':
        return bishop_attack(square, target_square, board)
    elif piece_type == 'R':
        sf, sr = square_to_coords(square)
        tf, tr = square_to_coords(target_square)
        if sf != tf and sr != tr:
            return False
        if sf == tf:
            dr = 1 if tr > sr else -1
            r = sr + dr
            while r <= tr if sf == tf else sr:
                new_sq = coords_to_square(sf, r)
                if new_sq in board and board[new_sq][0] == square[0]:
                    return False
                r += dr
            return True
        else:
            dc = 1 if tf > sf else -1
            f = sf + dc
            while f <= tf if sr == tr else sf:
                new_sq = coords_to_square(f, sr)
                if new_sq in board and board[new_sq][0] == square[0]:
                    return False
                f += dc
            return True
    elif piece_type == 'Q':
        return bishop_attack(square, target_square, board) or rook_attack(square, target_square, board)
    elif piece_type == 'P':
        pf, pr = square_to_coords(square)
        tf, tr = square_to_coords(target_square)
        dir = 1 if current_color == 'w' else -1
        if pr + dir == tr and abs(tf - pf) == 1 and board.get(target_square, '')[0] == opponent:
            return True
    return False

def is_king_in_check(board, current_color):
    opponent = 'b' if current_color == 'w' else 'w'
    king_pos = None
    for sq, p in board.items():
        if p == current_color + 'K':
            king_pos = sq
            break
    if not king_pos:
        return False
    for s, p in board.items():
        if p[0] == opponent and p[1] != 'K':
            if can_attack(s, p[1], king_pos, board):
                return True
    return False

def policy(pieces: dict, to_play: str) -> str:
    current_color = to_play[0]
    opponent = 'b' if to_play == 'w' else 'w'
    legal_moves = []
    captured_scores = {}

    for square, piece in pieces.items():
        if piece[0] != current_color:
            continue
        ptype = piece[1]
        moves = []
        if ptype == 'K':
            f, r = square_to_coords(square)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    nf = f + dx
                    nr = r + dy
                    if 0 <= nf < 8 and 0 <= nr < 8:
                        new_sq = coords_to_square(nf, nr)
                        if not (new_sq in pieces and pieces[new_sq][0] == current_color):
                            moves.append(new_sq)
        elif ptype == 'N':
            f, r = square_to_coords(square)
            offsets = [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
                       (1, -2), (1, 2), (2, -1), (2, 1)]
            for dx, dy in offsets:
                nf = f + dx
                nr = r + dy
                if 0 <= nf < 8 and 0 <= nr < 8:
                    new_sq = coords_to_square(nf, nr)
                    if not (new_sq in pieces and pieces[new_sq][0] == current_color):
                        moves.append(new_sq)
        elif ptype == 'B':
            f, r = square_to_coords(square)
            diffs = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
            for dx, dy in diffs:
                nf, nr = f, r
                while True:
                    nf += dx
                    nr += dy
                    if not (0 <= nf < 8 and 0 <= nr < 8):
                        break
                    new_sq = coords_to_square(nf, nr)
                    if new_sq in pieces and pieces[new_sq][0] == current_color:
                        break
                    moves.append(new_sq)
        elif ptype == 'R':
            f, r = square_to_coords(square)
            dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
            for dx, dy in dirs:
                nf, nr = f, r
                while True:
                    nf += dx
                    nr += dy
                    if not (0 <= nf < 8 and 0 <= nr < 8):
                        break
                    new_sq = coords_to_square(nf, nr)
                    if new_sq in pieces and pieces[new_sq][0] == current_color:
                        break
                    moves.append(new_sq)
        elif ptype == 'Q':
            f, r = square_to_coords(square)
            dirs = [(1, 0), (-1, 0), (0, 1), (0, -1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
            for dx, dy in dirs:
                nf, nr = f, r
                while True:
                    nf += dx
                    nr += dy
                    if not (0 <= nf < 8 and 0 <= nr < 8):
                        break
                    new_sq = coords_to_square(nf, nr)
                    if new_sq in pieces and pieces[new_sq][0] == current_color:
                        break
                    moves.append(new_sq)
        elif ptype == 'P':
            f, r = square_to_coords(square)
            dir = 1 if current_color == 'w' else -1
            new_sq = coords_to_square(f, r + dir)
            if new_sq not in pieces:
                moves.append(new_sq)
            if (current_color == 'w' and r == 1) or (current_color == 'b' and r == 6):
                new_sq = coords_to_square(f, r + 2 * dir)
                if new_sq not in pieces:
                    moves.append(new_sq)
            for dx in (-1, 1):
                new_sq = coords_to_square(f + dx, r + dir)
                if new_sq in pieces and pieces[new_sq][0] == opponent:
                    moves.append(new_sq)
        legal = []
        for new_sq in moves:
            temp = copy.deepcopy(pieces)
            if to_play == 'w':
                temp[square] = ptype
            temp[square] = ptype
            temp.pop(square)
            temp[new_sq] = ptype
            if not is_king_in_check(temp, current_color):
                legal.append(new_sq)
        for new_sq in legal:
            legal_moves.append((square, new_sq))
    
    evaluated = []
    for move in legal_moves:
        cap_piece = None
        if move[1] not in pieces or (pieces[move[1]][0] != current_color):
            cap_piece = pieces.get(move[1], '')
            cap_val = PIECE_VALUES.get(cap_piece[1], 0) if cap_piece else 0
            move_score = cap_val
            if cap_piece and cap_piece[1] == 'K' and cap_piece[0] == opponent:
                move_score += 1000
            evaluated.append((new_sq, move_score))
    
    if not evaluated:
        return legal_moves[0] if legal_moves else ''
    
    best_score = -1
    best_move = ''
    for move in evaluated:
        _, score = move
        if score > best_score or (score == best_score and best_move == ''):
            best_score = score
            best_move = move[0]
    return best_move
