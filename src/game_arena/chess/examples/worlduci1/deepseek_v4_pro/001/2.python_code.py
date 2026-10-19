
import time

class TimeoutError(Exception):
    pass

# Piece values
PIECE_VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 0}

# Piece-square tables (from white's perspective, a1=0, h1=7, a8=56, h8=63)
PAWN_PST = [
    0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
    5,  5, 10, 25, 25, 10,  5,  5,
    0,  0,  0, 20, 20,  0,  0,  0,
    5, -5,-10,  0,  0,-10, -5,  5,
    5, 10, 10,-20,-20, 10, 10,  5,
    0,  0,  0,  0,  0,  0,  0,  0
]

KNIGHT_PST = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50
]

BISHOP_PST = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20
]

ROOK_PST = [
    0,  0,  0,  0,  0,  0,  0,  0,
    5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    0,  0,  0,  5,  5,  0,  0,  0
]

QUEEN_PST = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
    -5,  0,  5,  5,  5,  5,  0, -5,
    0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20
]

KING_MIDDLE_PST = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
    20, 20,  0,  0,  0,  0, 20, 20,
    20, 30, 10,  0,  0, 10, 30, 20
]

PST = {
    'P': PAWN_PST,
    'N': KNIGHT_PST,
    'B': BISHOP_PST,
    'R': ROOK_PST,
    'Q': QUEEN_PST,
    'K': KING_MIDDLE_PST
}

DIRECTIONS = {
    'K': [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)],
    'N': [(-2,-1), (-2,1), (-1,-2), (-1,2), (1,-2), (1,2), (2,-1), (2,1)],
    'B': [(-1,-1), (-1,1), (1,-1), (1,1)],
    'R': [(-1,0), (1,0), (0,-1), (0,1)],
    'Q': [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
}

def sq_to_rc(sq):
    return int(sq[1]) - 1, ord(sq[0]) - ord('a')

def rc_to_sq(row, col):
    return chr(col + ord('a')) + str(row + 1)

def get_pst_value(piece_type, idx, color):
    if color == 'b':
        idx = 63 - idx
    return PST[piece_type][idx]

def build_board(pieces):
    board = [['.' for _ in range(8)] for _ in range(8)]
    king_pos = {'w': None, 'b': None}
    for sq, piece in pieces.items():
        row, col = sq_to_rc(sq)
        board[row][col] = piece
        if piece[1] == 'K':
            king_pos[piece[0]] = (row, col)
    return board, king_pos

def is_attacked_by(board, square, attacker_color):
    r, c = square
    for i in range(8):
        for j in range(8):
            p = board[i][j]
            if p == '.' or p[0] != attacker_color:
                continue
            p_type = p[1]
            if p_type == 'P':
                if attacker_color == 'w':
                    if i + 1 == r and (j - 1 == c or j + 1 == c):
                        return True
                else:
                    if i - 1 == r and (j - 1 == c or j + 1 == c):
                        return True
            elif p_type == 'N':
                if (abs(r - i) == 2 and abs(c - j) == 1) or (abs(r - i) == 1 and abs(c - j) == 2):
                    return True
            elif p_type == 'B':
                if abs(r - i) == abs(c - j) and r != i:
                    step_r = 1 if r > i else -1
                    step_c = 1 if c > j else -1
                    rr, cc = i + step_r, j + step_c
                    blocked = False
                    while rr != r or cc != c:
                        if board[rr][cc] != '.':
                            blocked = True
                            break
                        rr += step_r
                        cc += step_c
                    if not blocked:
                        return True
            elif p_type == 'R':
                if r == i or c == j:
                    if r == i:
                        step = 1 if c > j else -1
                        for cc in range(j + step, c, step):
                            if board[i][cc] != '.':
                                break
                        else:
                            return True
                    else:
                        step = 1 if r > i else -1
                        for rr in range(i + step, r, step):
                            if board[rr][j] != '.':
                                break
                        else:
                            return True
            elif p_type == 'Q':
                if r == i or c == j or abs(r - i) == abs(c - j):
                    if r == i or c == j:
                        if r == i:
                            step = 1 if c > j else -1
                            for cc in range(j + step, c, step):
                                if board[i][cc] != '.':
                                    break
                            else:
                                return True
                        else:
                            step = 1 if r > i else -1
                            for rr in range(i + step, r, step):
                                if board[rr][j] != '.':
                                    break
                            else:
                                return True
                    else:
                        step_r = 1 if r > i else -1
                        step_c = 1 if c > j else -1
                        rr, cc = i + step_r, j + step_c
                        while rr != r or cc != c:
                            if board[rr][cc] != '.':
                                break
                            rr += step_r
                            cc += step_c
                        else:
                            return True
            elif p_type == 'K':
                if abs(r - i) <= 1 and abs(c - j) <= 1:
                    return True
    return False

def is_in_check(board, king_color):
    for i in range(8):
        for j in range(8):
            if board[i][j] == king_color + 'K':
                return is_attacked_by(board, (i, j), 'w' if king_color == 'b' else 'b')
    return False

def generate_legal_moves(board, king_pos, side_to_move):
    moves = []
    for i in range(8):
        for j in range(8):
            piece = board[i][j]
            if piece == '.' or piece[0] != side_to_move:
                continue
            p_type = piece[1]
            color = piece[0]
            sq = rc_to_sq(i, j)

            if p_type == 'P':
                direction = 1 if color == 'w' else -1
                start_rank = 1 if color == 'w' else 6
                prom_rank = 7 if color == 'w' else 0
                r1 = i + direction
                if 0 <= r1 < 8:
                    if board[r1][j] == '.':
                        if r1 == prom_rank:
                            for prom in ['q', 'r', 'b', 'n']:
                                moves.append(sq + rc_to_sq(r1, j) + prom)
                        else:
                            moves.append(sq + rc_to_sq(r1, j))
                        if i == start_rank:
                            r2 = i + 2 * direction
                            if board[r2][j] == '.':
                                moves.append(sq + rc_to_sq(r2, j))
                for dj in [-1, 1]:
                    nj = j + dj
                    if 0 <= nj < 8:
                        target = board[r1][nj]
                        if target != '.' and target[0] != color:
                            if r1 == prom_rank:
                                for prom in ['q', 'r', 'b', 'n']:
                                    moves.append(sq + rc_to_sq(r1, nj) + prom)
                            else:
                                moves.append(sq + rc_to_sq(r1, nj))
            elif p_type in ('N', 'B', 'R', 'Q', 'K'):
                if p_type == 'K':
                    for dr, dc in DIRECTIONS['K']:
                        r1, c1 = i + dr, j + dc
                        if 0 <= r1 < 8 and 0 <= c1 < 8:
                            target = board[r1][c1]
                            if target == '.' or target[0] != color:
                                moves.append(sq + rc_to_sq(r1, c1))
                    # castling
                    if color == 'w' and i == 0 and j == 4:
                        if board[0][7] == 'wR' and board[0][5] == '.' and board[0][6] == '.':
                            if not is_attacked_by(board, (0,4), 'b') and not is_attacked_by(board, (0,5), 'b') and not is_attacked_by(board, (0,6), 'b'):
                                moves.append('e1g1')
                        if board[0][0] == 'wR' and board[0][3] == '.' and board[0][2] == '.' and board[0][1] == '.':
                            if not is_attacked_by(board, (0,4), 'b') and not is_attacked_by(board, (0,3), 'b') and not is_attacked_by(board, (0,2), 'b'):
                                moves.append('e1c1')
                    elif color == 'b' and i == 7 and j == 4:
                        if board[7][7] == 'bR' and board[7][5] == '.' and board[7][6] == '.':
                            if not is_attacked_by(board, (7,4), 'w') and not is_attacked_by(board, (7,5), 'w') and not is_attacked_by(board, (7,6), 'w'):
                                moves.append('e8g8')
                        if board[7][0] == 'bR' and board[7][3] == '.' and board[7][2] == '.' and board[7][1] == '.':
                            if not is_attacked_by(board, (7,4), 'w') and not is_attacked_by(board, (7,3), 'w') and not is_attacked_by(board, (7,2), 'w'):
                                moves.append('e8c8')
                else:
                    for dr, dc in DIRECTIONS[p_type]:
                        r, c = i + dr, j + dc
                        while 0 <= r < 8 and 0 <= c < 8:
                            target = board[r][c]
                            if target == '.':
                                moves.append(sq + rc_to_sq(r, c))
                            elif target[0] != color:
                                moves.append(sq + rc_to_sq(r, c))
                                break
                            else:
                                break
                            if p_type in ('N', 'K'):
                                break
                            r += dr
                            c += dc

    legal_moves = []
    for move in moves:
        if len(move) == 4:
            from_sq, to_sq, prom = move[:2], move[2:4], None
        elif len(move) == 5:
            from_sq, to_sq, prom = move[:2], move[2:4], move[4]
        else:
            continue
        new_board = [row[:] for row in board]
        r1, c1 = sq_to_rc(from_sq)
        r2, c2 = sq_to_rc(to_sq)
        piece_moved = new_board[r1][c1]
        new_board[r1][c1] = '.'
        if prom:
            new_board[r2][c2] = piece_moved[0] + prom.upper()
        else:
            new_board[r2][c2] = piece_moved
        if piece_moved[1] == 'K' and abs(c2 - c1) == 2:
            if c2 == 6:
                rook_from, rook_to = (r1, 7), (r1, 5)
            else:
                rook_from, rook_to = (r1, 0), (r1, 3)
            new_board[rook_from[0]][rook_from[1]] = '.'
            new_board[rook_to[0]][rook_to[1]] = piece_moved[0] + 'R'
        if not is_in_check(new_board, piece_moved[0]):
            legal_moves.append(move)
    return legal_moves

def evaluate_board(board):
    score = 0
    for i in range(8):
        for j in range(8):
            p = board[i][j]
            if p == '.':
                continue
            color = p[0]
            p_type = p[1]
            val = PIECE_VALUES[p_type] + get_pst_value(p_type, i*8 + j, color)
            if color == 'w':
                score += val
            else:
                score -= val
    return score

def evaluate_from_side(board, side):
    score = evaluate_board(board)
    return score if side == 'w' else -score

def apply_move(board, king_pos, move):
    new_board = [row[:] for row in board]
    new_king_pos = king_pos.copy()
    from_sq, to_sq = move[:2], move[2:4]
    prom = move[4] if len(move) == 5 else None
    r1, c1 = sq_to_rc(from_sq)
    r2, c2 = sq_to_rc(to_sq)
    piece = new_board[r1][c1]
    color = piece[0]
    p_type = piece[1]
    new_board[r1][c1] = '.'
    if prom:
        new_board[r2][c2] = color + prom.upper()
    else:
        new_board[r2][c2] = piece
    if p_type == 'K':
        new_king_pos[color] = (r2, c2)
        if abs(c2 - c1) == 2:
            if c2 == 6:
                rook_from, rook_to = (r1, 7), (r1, 5)
            else:
                rook_from, rook_to = (r1, 0), (r1, 3)
            new_board[rook_from[0]][rook_from[1]] = '.'
            new_board[rook_to[0]][rook_to[1]] = color + 'R'
    return new_board, new_king_pos

def order_moves(moves, board, side):
    def move_score(move):
        from_sq, to_sq = move[:2], move[2:4]
        prom = move[4] if len(move) == 5 else None
        r1, c1 = sq_to_rc(from_sq)
        r2, c2 = sq_to_rc(to_sq)
        piece = board[r1][c1]
        target = board[r2][c2]
        if target != '.':
            return 10 * PIECE_VALUES[target[1]] - PIECE_VALUES[piece[1]]
        if prom:
            return 900 + PIECE_VALUES[prom.upper()]
        return get_pst_value(piece[1], r2*8 + c2, piece[0]) - get_pst_value(piece[1], r1*8 + c1, piece[0])
    return sorted(moves, key=move_score, reverse=True)

def negamax(board, king_pos, depth, alpha, beta, side, start_time, time_limit):
    if time.time() - start_time > time_limit:
        raise TimeoutError
    if depth == 0:
        return evaluate_from_side(board, side), None
    moves = generate_legal_moves(board, king_pos, side)
    if not moves:
        if is_in_check(board, side):
            return -100000 + depth, None
        else:
            return 0, None
    best_move = None
    moves = order_moves(moves, board, side)
    for move in moves:
        new_board, new_king = apply_move(board, king_pos, move)
        next_side = 'b' if side == 'w' else 'w'
        val, _ = negamax(new_board, new_king, depth - 1, -beta, -alpha, next_side, start_time, time_limit)
        val = -val
        if val > alpha:
            alpha = val
            best_move = move
        if alpha >= beta:
            break
    return alpha, best_move

def policy(pieces: dict[str, str], to_play: str) -> str:
    board, king_pos = build_board(pieces)
    side = 'w' if to_play == 'white' else 'b'
    legal_moves = generate_legal_moves(board, king_pos, side)
    if not legal_moves:
        return '0000'
    start_time = time.time()
    best_move = legal_moves[0]
    try:
        for depth in range(1, 5):
            if time.time() - start_time > 0.8:
                break
            _, move = negamax(board, king_pos, depth, -float('inf'), float('inf'), side, start_time, 0.9)
            if move is not None:
                best_move = move
    except TimeoutError:
        pass
    return best_move
