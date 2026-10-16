
import time

# Piece values in centipawns
PIECE_VALUES = {
    'P': 100,
    'N': 320,
    'B': 330,
    'R': 500,
    'Q': 900,
    'K': 20000
}

# Piece-square tables for White (from rank 1 to rank 8)
PAWN_TABLE = [
     0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
     5,  5, 10, 25, 25, 10,  5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5, -5,-10,  0,  0,-10, -5,  5,
     5, 10, 10,-20,-20, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0
]

KNIGHT_TABLE = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50,
]

BISHOP_TABLE = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20,
]

ROOK_TABLE = [
      0,  0,  0,  0,  0,  0,  0,  0,
      5, 10, 10, 10, 10, 10, 10,  5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
      0,  0,  0,  5,  5,  0,  0,  0
]

QUEEN_TABLE = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
     -5,  0,  5,  5,  5,  5,  0, -5,
      0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20
]

KING_TABLE = [
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
    'P': PAWN_TABLE,
    'N': KNIGHT_TABLE,
    'B': BISHOP_TABLE,
    'R': ROOK_TABLE,
    'Q': QUEEN_TABLE,
    'K': KING_TABLE,
}

KNIGHT_DIRS = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
BISHOP_DIRS = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
ROOK_DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]
KING_DIRS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

def sq_to_cr(sq: str):
    return ord(sq[0]) - 97, int(sq[1]) - 1

def cr_to_sq(c: int, r: int):
    return chr(97 + c) + str(r + 1)

def apply_move(board: dict, move: str) -> dict:
    nb = dict(board)
    src = move[:2]
    dst = move[2:4]
    promo = move[4:].upper() if len(move) > 4 else None

    piece = nb.pop(src, None)
    if not piece:
        return nb
    
    color = piece[0]
    ptype = promo if promo else piece[1]

    # Handle castling king move
    if piece[1] == 'K' and abs(ord(dst[0]) - ord(src[0])) == 2:
        r = src[1]
        if dst[0] == 'g':
            rook = nb.pop('h' + r, None)
            if rook:
                nb['f' + r] = rook
        elif dst[0] == 'c':
            rook = nb.pop('a' + r, None)
            if rook:
                nb['d' + r] = rook

    nb[dst] = color + ptype
    return nb

def square_attacked(board: dict, target_sq: str, by_color: str) -> bool:
    tc, tr = sq_to_cr(target_sq)

    # Pawns
    p_step = -1 if by_color == 'w' else 1
    for dc in (-1, 1):
        fc, fr = tc + dc, tr + p_step
        if 0 <= fc < 8 and 0 <= fr < 8:
            p = board.get(cr_to_sq(fc, fr))
            if p == by_color + 'P':
                return True

    # Knights
    for dc, dr in KNIGHT_DIRS:
        fc, fr = tc + dc, tr + dr
        if 0 <= fc < 8 and 0 <= fr < 8:
            if board.get(cr_to_sq(fc, fr)) == by_color + 'N':
                return True

    # King
    for dc, dr in KING_DIRS:
        fc, fr = tc + dc, tr + dr
        if 0 <= fc < 8 and 0 <= fr < 8:
            if board.get(cr_to_sq(fc, fr)) == by_color + 'K':
                return True

    # Straight (R, Q)
    for dc, dr in ROOK_DIRS:
        fc, fr = tc + dc, tr + dr
        while 0 <= fc < 8 and 0 <= fr < 8:
            p = board.get(cr_to_sq(fc, fr))
            if p:
                if p[0] == by_color and p[1] in ('R', 'Q'):
                    return True
                break
            fc += dc
            fr += dr

    # Diagonal (B, Q)
    for dc, dr in BISHOP_DIRS:
        fc, fr = tc + dc, tr + dr
        while 0 <= fc < 8 and 0 <= fr < 8:
            p = board.get(cr_to_sq(fc, fr))
            if p:
                if p[0] == by_color and p[1] in ('B', 'Q'):
                    return True
                break
            fc += dc
            fr += dr

    return False

def generate_pseudo_moves(board: dict, color: str) -> list:
    moves = []
    opp = 'b' if color == 'w' else 'w'
    p_dir = 1 if color == 'w' else -1
    start_rank = 1 if color == 'w' else 6
    promo_rank = 7 if color == 'w' else 0

    for sq, piece in list(board.items()):
        if piece[0] != color:
            continue
        pt = piece[1]
        c, r = sq_to_cr(sq)

        if pt == 'P':
            # Forward one step
            nr = r + p_dir
            if 0 <= nr < 8:
                fwd_sq = cr_to_sq(c, nr)
                if fwd_sq not in board:
                    if nr == promo_rank:
                        for prom in ('q', 'r', 'b', 'n'):
                            moves.append(sq + fwd_sq + prom)
                    else:
                        moves.append(sq + fwd_sq)
                        # Forward two steps
                        if r == start_rank:
                            fwd2_sq = cr_to_sq(c, r + 2 * p_dir)
                            if fwd2_sq not in board:
                                moves.append(sq + fwd2_sq)

            # Diagonal captures
            for dc in (-1, 1):
                nc = c + dc
                if 0 <= nc < 8 and 0 <= nr < 8:
                    cap_sq = cr_to_sq(nc, nr)
                    target = board.get(cap_sq)
                    if target and target[0] == opp:
                        if nr == promo_rank:
                            for prom in ('q', 'r', 'b', 'n'):
                                moves.append(sq + cap_sq + prom)
                        else:
                            moves.append(sq + cap_sq)

        elif pt == 'N':
            for dc, dr in KNIGHT_DIRS:
                nc, nr = c + dc, r + dr
                if 0 <= nc < 8 and 0 <= nr < 8:
                    dest = cr_to_sq(nc, nr)
                    t = board.get(dest)
                    if not t or t[0] != color:
                        moves.append(sq + dest)

        elif pt == 'K':
            for dc, dr in KING_DIRS:
                nc, nr = c + dc, r + dr
                if 0 <= nc < 8 and 0 <= nr < 8:
                    dest = cr_to_sq(nc, nr)
                    t = board.get(dest)
                    if not t or t[0] != color:
                        moves.append(sq + dest)

        elif pt in ('B', 'R', 'Q'):
            dirs = []
            if pt in ('B', 'Q'):
                dirs.extend(BISHOP_DIRS)
            if pt in ('R', 'Q'):
                dirs.extend(ROOK_DIRS)

            for dc, dr in dirs:
                nc, nr = c + dc, r + dr
                while 0 <= nc < 8 and 0 <= nr < 8:
                    dest = cr_to_sq(nc, nr)
                    t = board.get(dest)
                    if not t:
                        moves.append(sq + dest)
                    else:
                        if t[0] != color:
                            moves.append(sq + dest)
                        break
                    nc += dc
                    nr += dr

    return moves

def generate_legal_moves(board: dict, color: str) -> list:
    pseudo = generate_pseudo_moves(board, color)
    legal = []
    opp = 'b' if color == 'w' else 'w'

    for mv in pseudo:
        nb = apply_move(board, mv)
        # Find king of our color
        k_sq = None
        for s, p in nb.items():
            if p == color + 'K':
                k_sq = s
                break
        if k_sq and not square_attacked(nb, k_sq, opp):
            legal.append(mv)
    return legal

def evaluate(board: dict) -> int:
    score = 0
    for sq, piece in board.items():
        color, pt = piece[0], piece[1]
        c, r = sq_to_cr(sq)
        idx = (7 - r) * 8 + c if color == 'w' else r * 8 + c
        val = PIECE_VALUES.get(pt, 0) + PST.get(pt, [0] * 64)[idx]
        if color == 'w':
            score += val
        else:
            score -= val
    return score

def score_move(board: dict, move: str) -> int:
    # MVV-LVA move ordering
    dst = move[2:4]
    victim = board.get(dst)
    score = 0
    if victim:
        attacker = board.get(move[:2])
        score = 1000 + PIECE_VALUES.get(victim[1], 0) * 10 - (PIECE_VALUES.get(attacker[1], 0) if attacker else 0)
    if len(move) > 4:
        promo = move[4].upper()
        score += PIECE_VALUES.get(promo, 0)
    return score

def alpha_beta(board: dict, depth: int, alpha: int, beta: int, maximizing: bool, end_time: float) -> int:
    if time.time() > end_time:
        return evaluate(board)
    
    color = 'w' if maximizing else 'b'
    legal = generate_legal_moves(board, color)
    
    if not legal:
        k_sq = None
        for s, p in board.items():
            if p == color + 'K':
                k_sq = s
                break
        opp = 'b' if color == 'w' else 'w'
        if k_sq and square_attacked(board, k_sq, opp):
            return -50000 - depth if maximizing else 50000 + depth
        return 0  # Stalemate

    if depth == 0:
        return evaluate(board)

    legal.sort(key=lambda m: score_move(board, m), reverse=True)

    if maximizing:
        val = -1000000
        for m in legal:
            nb = apply_move(board, m)
            val = max(val, alpha_beta(nb, depth - 1, alpha, beta, False, end_time))
            alpha = max(alpha, val)
            if beta <= alpha:
                break
        return val
    else:
        val = 1000000
        for m in legal:
            nb = apply_move(board, m)
            val = min(val, alpha_beta(nb, depth - 1, alpha, beta, True, end_time))
            beta = min(beta, val)
            if beta <= alpha:
                break
        return val

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str] = None, *args, **kwargs) -> str:
    color = 'w' if to_play.lower().startswith('w') else 'b'
    
    if not legal_moves:
        legal_moves = generate_legal_moves(pieces, color)

    if not legal_moves:
        # Fallback if no legal moves exist
        return "0000"

    if len(legal_moves) == 1:
        return legal_moves[0]

    end_time = time.time() + 0.85

    # Check for immediate checkmate or queen capture
    legal_moves.sort(key=lambda m: score_move(pieces, m), reverse=True)

    best_move = legal_moves[0]
    depth = 2

    is_max = (color == 'w')
    best_score = -10000000 if is_max else 10000000

    for m in legal_moves:
        nb = apply_move(pieces, m)
        score = alpha_beta(nb, depth - 1, -10000000, 10000000, not is_max, end_time)
        if is_max and score > best_score:
            best_score = score
            best_move = m
        elif not is_max and score < best_score:
            best_score = score
            best_move = m
        if time.time() > end_time:
            break

    return best_move
