
import time
import itertools

# ------------------------------------------------------------
# Piece–square tables from Sunfish / simplified PST
# ------------------------------------------------------------
pst = {
    'P': (
         0,   0,   0,   0,   0,   0,   0,   0,
         78,  83,  86,  73, 102,  82,  85,  90,
         7,   29,  21,  44,  31,  31,  34,   7,
        -17,  16,  -2,  15,  14,   0,  15, -13,
        -26,   3,  10,   9,   6,   1,   0, -23,
        -22,   9,   5, -11, -10,  -2,   3, -19,
        -31,   8,  -7, -37, -36, -14,   3, -31,
         0,   0,   0,   0,   0,   0,   0,   0
    ),
    'N': (
        -66, -53, -75, -75, -10, -55, -58, -70,
        -3,  -6, 100, -36,   4,  62,  -4, -14,
        10,  67,   1,  74,  73,  27,  62,  -2,
        24,  24,  45,  37,  33,  41,  25,  17,
        -1,   5,  31,  21,  22,  35,   2,   0,
        -18, 10,  13,  22,  18,  15,  11, -14,
        -23, -15,  2,   0,   2,   0, -23, -20,
        -74, -23, -26, -24, -19, -35, -22, -69
    ),
    'B': (
        -59, -78, -82, -76, -23, -107, -37, -50,
        -11, 20,  35, -42, -39,  31,   2, -22,
        -9,  39, -32,  41,  52, -10,  28, -14,
        25,  17,  20,  34,  26,  25,  15,  10,
        13,  10,  17,  23,  17,  16,   0,   7,
        14,  25,  24,  15,   8,  25,  20,  15,
        19,  20,  11,   6,   7,   6,  20,  16,
        -7,   2, -15, -12, -14, -15, -10, -10
    ),
    'R': (
        35,  29,  33,   4,  37,  33,  56,  50,
        55,  29,  56,  67,  55,  62,  34,  60,
        19,  35,  28,  33,  45,  27,  25,  15,
        0,   5,  16,  13,  18,  -4,  -9,  -6,
        -28, -35, -16, -21, -13, -29, -46, -30,
        -42, -28, -42, -25, -25, -35, -26, -46,
        -53, -38, -31, -26, -29, -43, -44, -53,
        -30, -24, -18,   5,  -2, -18, -31, -32
    ),
    'Q': (
        6,   1,  -8, -104, 69,  24,  88,  26,
        14,  32,  60, -10,  20,  76,  57,  24,
        -2,  43,  32,  60,  72,  63,  43,   2,
        1,  -16,  22,  17,  25,  20, -13,  -6,
        -14, -15,  -2,  -5,  -1, -10, -20, -22,
        -30,  -6, -13, -11, -16, -11, -16, -27,
        -36, -18,   0, -19, -15, -15, -21, -38,
        -39, -30, -31, -13, -31, -36, -34, -42
    ),
    'K': (
        4,  54,  47, -99, -99,  60,  83, -62,
        -32, 10,  55,  56,  56,  55,  10,   3,
        -62, 12, -57,  44, -67,  28,  37, -31,
        -55, 50,  11,  -4, -19,  13,   0, -49,
        -55, -43, -52, -28, -51, -47,  -8, -50,
        -47, -42, -43, -79, -64, -32, -29, -32,
        -4,   3, -14, -50, -57, -18,  13,   4,
        17,  30,  -3, -14,   6,  -1,  40,  18
    )
}

PIECE_VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}

COLOR_MAP = {'w': 1, 'b': -1}
RANK_MAP = {str(r): r for r in range(1, 9)}
FILE_MAP = {f: i for i, f in enumerate('abcdefgh')}
FILE_MAP_REV = {i: f for f, i in FILE_MAP.items()}

# ------------------------------------------------------------
# Board helper
# ------------------------------------------------------------
def parse_board(pieces, to_play):
    """Return board as flat list length 64 (None = empty,
    else (color_sign, piece_type)), plus side_sign."""
    board = [None] * 64
    for sq, pc in pieces.items():
        c = COLOR_MAP[pc[0]]
        pt = pc[1].upper()
        idx = (RANK_MAP[sq[1]] - 1) * 8 + FILE_MAP[sq[0]]
        board[idx] = (c, pt)
    side_sign = COLOR_MAP['w'] if to_play == 'white' else COLOR_MAP['b']
    return board, side_sign

def idx_to_sq(idx):
    return FILE_MAP_REV[idx % 8] + str(idx // 8 + 1)

def sq_to_idx(sq):
    return FILE_MAP[sq[0]] + (RANK_MAP[sq[1]] - 1) * 8

def move_to_idcs(move):
    fr = sq_to_idx(move[:2])
    to = sq_to_idx(move[2:4])
    prom = move[4] if len(move) > 4 else None
    return fr, to, prom

def generate_moves(board, side_sign):
    """Generate all pseudo–legal moves as tuples (fr, to, prom).
    Handles captures, slides, pawn moves, castling, promotions."""
    moves = []
    enemy = -side_sign
    for fr in range(64):
        pc = board[fr]
        if pc is None or pc[0] != side_sign:
            continue
        pt = pc[1]
        fr_f = fr % 8
        fr_r = fr // 8
        if pt == 'P':
            dir_ = side_sign  # white 1 => rank grows, black -1 => rank shrinks
            # single push
            to = fr + dir_ * 8
            if 0 <= to < 64 and board[to] is None:
                if to // 8 in [0, 7]:
                    for prom in 'QRBN':
                        moves.append((fr, to, prom.lower() if side_sign == 1 else prom.upper()))
                else:
                    moves.append((fr, to, None))
                # double push from start rank
                if (side_sign == 1 and fr_r == 1) or (side_sign == -1 and fr_r == 6):
                    to2 = fr + dir_ * 16
                    if 0 <= to2 < 64 and board[to2] is None:
                        moves.append((fr, to2, None))
            # captures left/right
            for df in [-1, 1]:
                nf = fr_f + df
                if 0 <= nf < 8:
                    to = fr + dir_ * 8 + df
                    if 0 <= to < 64:
                        target = board[to]
                        if target is not None and target[0] == enemy:
                            if to // 8 in [0, 7]:
                                for prom in 'QRBN':
                                    moves.append((fr, to, prom.lower() if side_sign == 1 else prom.upper()))
                            else:
                                moves.append((fr, to, None))
            # en passant (simplified: assume last move not tracked, so skip for evaluation;
            #  we will generate an approximate set for move generation usage. Avoid for now.)
        elif pt == 'N':
            for df, dr in [(2,1),(2,-1),(-2,1),(-2,-1),(1,2),(1,-2),(-1,2),(-1,-2)]:
                nf, nr = fr_f+df, fr_r+dr
                if 0 <= nf < 8 and 0 <= nr < 8:
                    to = nr*8 + nf
                    target = board[to]
                    if target is None or target[0] == enemy:
                        moves.append((fr, to, None))
        elif pt in 'BQR':
            dirs = []
            if pt in 'BQ':
                dirs += [(1,1),(1,-1),(-1,1),(-1,-1)]
            if pt in 'RQ':
                dirs += [(1,0),(-1,0),(0,1),(0,-1)]
            for df, dr in dirs:
                for step in range(1, 8):
                    nf, nr = fr_f+df*step, fr_r+dr*step
                    if 0 <= nf < 8 and 0 <= nr < 8:
                        to = nr*8 + nf
                        target = board[to]
                        if target is None:
                            moves.append((fr, to, None))
                        elif target[0] == enemy:
                            moves.append((fr, to, None))
                            break
                        else:
                            break
                    else:
                        break
        elif pt == 'K':
            for df, dr in itertools.product([-1,0,1], repeat=2):
                if df == 0 and dr == 0:
                    continue
                nf, nr = fr_f+df, fr_r+dr
                if 0 <= nf < 8 and 0 <= nr < 8:
                    to = nr*8 + nf
                    target = board[to]
                    if target is None or target[0] == enemy:
                        moves.append((fr, to, None))
            # Castling (white: e1, black: e8)
            if pt == 'K':
                if side_sign == 1 and fr == 4:  # e1
                    if board[7] is not None and board[7][1] == 'R' and board[7][0] == 1:
                        if all(board[i] is None for i in [5,6]):
                            moves.append((4,6,None))
                    if board[0] is not None and board[0][1] == 'R' and board[0][0] == 1:
                        if all(board[i] is None for i in [1,2,3]):
                            moves.append((4,2,None))
                if side_sign == -1 and fr == 60:  # e8
                    if board[63] is not None and board[63][1] == 'R' and board[63][0] == -1:
                        if all(board[i] is None for i in [61,62]):
                            moves.append((60,62,None))
                    if board[56] is not None and board[56][1] == 'R' and board[56][0] == -1:
                        if all(board[i] is None for i in [57,58,59]):
                            moves.append((60,58,None))
    return moves

def apply_move(board, fr, to, prom):
    """Applies move on copied board; returns new board and captured piece."""
    new_board = board[:]
    pc = new_board[fr]
    captured = new_board[to]
    new_board[to] = (pc[0], prom.upper()) if prom else pc
    new_board[fr] = None
    # castling rook adjustment
    if pc[1] == 'K':
        if abs(fr - to) == 2:
            if to == 6:  # white O-O
                new_board[5] = new_board[7]
                new_board[7] = None
            elif to == 2:  # white O-O-O
                new_board[3] = new_board[0]
                new_board[0] = None
            elif to == 62:  # black O-O
                new_board[61] = new_board[63]
                new_board[63] = None
            elif to == 58:  # black O-O-O
                new_board[59] = new_board[56]
                new_board[56] = None
    # en passant removal would go here if implemented
    return new_board, captured

def evaluate(board, side_sign):
    """Static evaluation in centipawns from side_sign perspective."""
    score = 0
    for idx, pc in enumerate(board):
        if pc is None:
            continue
        col, pt = pc
        val = PIECE_VALUES[pt]
        row = idx // 8
        col_f = idx % 8
        if col == 1:  # white
            table = pst[pt]
            pst_val = table[63 - idx] if table else 0
        else:
            table = pst[pt]
            # mirror black
            pst_val = table[idx] if table else 0
        score += col * (val + pst_val)
    return score * side_sign

# ------------------------------------------------------------
# Move ordering helpers
# ------------------------------------------------------------
def order_moves(board, side_sign, moves):
    """Order moves for alpha–beta: captures first by MVV-LVA, then promotions, then others."""
    scored = []
    for fr, to, prom in moves:
        captured = board[to]
        # capture bonus
        if captured is not None:
            order_score = PIECE_VALUES[captured[1]] - PIECE_VALUES[board[fr][1]] // 100
        elif prom:
            order_score = PIECE_VALUES.get(prom.upper(), 0) + 200
        else:
            order_score = 0
        scored.append((fr, to, prom, order_score))
    scored.sort(key=lambda x: x[3], reverse=True)
    return [(x[0], x[1], x[2]) for x in scored]

# ------------------------------------------------------------
# Quiescence and negamax
# ------------------------------------------------------------
def quiesce(board, side_sign, alpha, beta, depth_left):
    """Quiescence search: only captures/promotions."""
    stand_pat = evaluate(board, side_sign)
    if stand_pat >= beta:
        return beta
    if stand_pat > alpha:
        alpha = stand_pat
    if depth_left <= 0:
        return alpha
    moves = generate_moves(board, side_sign)
    moves = [m for m in moves if board[m[1]] is not None or m[2]]  # captures or promotion
    moves = order_moves(board, side_sign, moves)
    for fr, to, prom in moves:
        new_board, _ = apply_move(board, fr, to, prom)
        val = -quiesce(new_board, -side_sign, -beta, -alpha, depth_left-1)
        if val >= beta:
            return beta
        if val > alpha:
            alpha = val
    return alpha

def negamax(board, side_sign, depth, alpha, beta):
    """Negamax with alpha–beta."""
    if depth == 0:
        return quiesce(board, side_sign, alpha, beta, 3)
    moves = generate_moves(board, side_sign)
    if not moves:
        # checkmate or stalemate
        # if king in check => mated
        king_idx = None
        for i, pc in enumerate(board):
            if pc is not None and pc[0] == side_sign and pc[1] == 'K':
                king_idx = i
                break
        # approximate: if any enemy can capture king => mate
        enemy_moves = generate_moves(board, -side_sign)
        in_check = any(to == king_idx for (_, to, _) in enemy_moves)
        return -20000 + (depth * 10) if in_check else 0
    moves = order_moves(board, side_sign, moves)
    for fr, to, prom in moves:
        new_board, _ = apply_move(board, fr, to, prom)
        val = -negamax(new_board, -side_sign, depth-1, -beta, -alpha)
        if val >= beta:
            return beta
        if val > alpha:
            alpha = val
    return alpha

# ------------------------------------------------------------
# Policy
# ------------------------------------------------------------
def policy(pieces: dict, to_play: str) -> str:
    start_time = time.time()
    board, side_sign = parse_board(pieces, to_play)
    legal_moves = generate_moves(board, side_sign)
    # Convert to UCI strings
    legal_moves_uci = []
    for fr, to, prom in legal_moves:
        uci = idx_to_sq(fr) + idx_to_sq(to)
        if prom:
            uci += prom.lower()
        legal_moves_uci.append(uci)
    # quick static 1–ply fallback
    best_move = legal_moves_uci[0]
    best_score = -99999
    moves_tuples = [(move_to_idcs(u), u) for u in legal_moves_uci]
    # Iterative deepening
    for depth in (1, 2, 3, 4, 5):
        if time.time() - start_time > 0.9:
            break
        alpha, beta = -99999, 99999
        current_best = None
        current_best_score = -99999
        ordered = order_moves(board, side_sign, [m for (m, _) in moves_tuples])
        for (fr, to, prom), u in zip(ordered, [None]*len(ordered)):
            # map back to string
            uci = idx_to_sq(fr)+idx_to_sq(to)
            if prom:
                uci += prom.lower()
            new_board, _ = apply_move(board, fr, to, prom)
            val = -negamax(new_board, -side_sign, depth-1, -beta, -alpha)
            if val > current_best_score:
                current_best_score = val
                current_best = uci
            if val > alpha:
                alpha = val
        if current_best is not None:
            best_move = current_best
            best_score = current_best_score
    return best_move
