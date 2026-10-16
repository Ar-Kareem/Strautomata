
import time

PIECE_VALS = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}

PAWN_TABLE = [
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10,-20,-20, 10, 10,  5,
     5, -5,-10,  0,  0,-10, -5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5,  5, 10, 25, 25, 10,  5,  5,
    10, 10, 20, 30, 30, 20, 10, 10,
    50, 50, 50, 50, 50, 50, 50, 50,
     0,  0,  0,  0,  0,  0,  0,  0
]

KNIGHT_TABLE = [
   -50,-40,-30,-30,-30,-30,-40,-50,
   -40,-20,  0,  5,  5,  0,-20,-40,
   -30,  5, 10, 15, 15, 10,  5,-30,
   -30,  0, 15, 20, 20, 15,  0,-30,
   -30,  5, 15, 20, 20, 15,  5,-30,
   -30,  0, 10, 15, 15, 10,  0,-30,
   -40,-20,  0,  0,  0,  0,-20,-40,
   -50,-40,-30,-30,-30,-30,-40,-50
]

BISHOP_TABLE = [
   -20,-10,-10,-10,-10,-10,-10,-20,
   -10,  5,  0,  0,  0,  0,  5,-10,
   -10, 10, 10, 10, 10, 10, 10,-10,
   -10,  0, 10, 10, 10, 10,  0,-10,
   -10,  5,  5, 10, 10,  5,  5,-10,
   -10,  0,  5, 10, 10,  5,  0,-10,
   -10,  0,  0,  0,  0,  0,  0,-10,
   -20,-10,-10,-10,-10,-10,-10,-20
]

ROOK_TABLE = [
     0,  0,  0,  5,  5,  0,  0,  0,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     5, 10, 10, 10, 10, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0
]

QUEEN_TABLE = [
   -20,-10,-10, -5, -5,-10,-10,-20,
   -10,  0,  5,  0,  0,  0,  0,-10,
   -10,  5,  5,  5,  5,  5,  0,-10,
     0,  0,  5,  5,  5,  5,  0, -5,
    -5,  0,  5,  5,  5,  5,  0, -5,
   -10,  0,  5,  5,  5,  5,  0,-10,
   -10,  0,  0,  0,  0,  0,  0,-10,
   -20,-10,-10, -5, -5,-10,-10,-20
]

KING_TABLE = [
    20, 30, 10,  0,  0, 10, 30, 20,
    20, 20,  0,  0,  0,  0, 20, 20,
   -10,-20,-20,-20,-20,-20,-20,-10,
   -20,-30,-30,-40,-40,-30,-30,-20,
   -30,-40,-40,-50,-50,-40,-40,-30,
   -30,-40,-40,-50,-50,-40,-40,-30,
   -30,-40,-40,-50,-50,-40,-40,-30,
   -30,-40,-40,-50,-50,-40,-40,-30
]

PST = {
    'P': PAWN_TABLE,
    'N': KNIGHT_TABLE,
    'B': BISHOP_TABLE,
    'R': ROOK_TABLE,
    'Q': QUEEN_TABLE,
    'K': KING_TABLE
}

def sq_name(sq: int) -> str:
    return chr(97 + (sq % 8)) + str((sq // 8) + 1)

def name_sq(name: str) -> int:
    return (ord(name[0]) - 97) + (int(name[1]) - 1) * 8

def evaluate_board(board: list) -> int:
    score = 0
    for sq in range(64):
        p = board[sq]
        if not p:
            continue
        color, p_type = p[0], p[1]
        val = PIECE_VALS[p_type]
        idx = sq if color == 'w' else (sq ^ 56)
        pst_val = PST[p_type][idx]
        total = val + pst_val
        score += total if color == 'w' else -total
    return score

def is_in_check(board: list, color: str) -> bool:
    target_k = color + 'K'
    k_sq = -1
    for i in range(64):
        if board[i] == target_k:
            k_sq = i
            break
    if k_sq == -1:
        return True

    opp = 'b' if color == 'w' else 'w'
    kf, kr = k_sq % 8, k_sq // 8

    # Pawn attacks
    pawn_dir = 1 if color == 'w' else -1
    for df in (-1, 1):
        nf, nr = kf + df, kr + pawn_dir
        if 0 <= nf < 8 and 0 <= nr < 8:
            if board[nr * 8 + nf] == opp + 'P':
                return True

    # Knight attacks
    for df, dr in ((1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2)):
        nf, nr = kf + df, kr + dr
        if 0 <= nf < 8 and 0 <= nr < 8:
            if board[nr * 8 + nf] == opp + 'N':
                return True

    # King attacks (adjacent)
    for df in (-1, 0, 1):
        for dr in (-1, 0, 1):
            if df == 0 and dr == 0:
                continue
            nf, nr = kf + df, kr + dr
            if 0 <= nf < 8 and 0 <= nr < 8:
                if board[nr * 8 + nf] == opp + 'K':
                    return True

    # Straight line attacks (Rook / Queen)
    for df, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        step = 1
        while True:
            nf, nr = kf + df * step, kr + dr * step
            if not (0 <= nf < 8 and 0 <= nr < 8):
                break
            p = board[nr * 8 + nf]
            if p:
                if p[0] == opp and (p[1] == 'R' or p[1] == 'Q'):
                    return True
                break
            step += 1

    # Diagonal attacks (Bishop / Queen)
    for df, dr in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        step = 1
        while True:
            nf, nr = kf + df * step, kr + dr * step
            if not (0 <= nf < 8 and 0 <= nr < 8):
                break
            p = board[nr * 8 + nf]
            if p:
                if p[0] == opp and (p[1] == 'B' or p[1] == 'Q'):
                    return True
                break
            step += 1

    return False

def make_move(board: list, m: str):
    fsq = name_sq(m[:2])
    tsq = name_sq(m[2:4])
    moved = board[fsq]
    captured = board[tsq]
    ep_sq, ep_cap = None, None
    castle_info = None

    # En passant check
    if moved and moved[1] == 'P' and abs(fsq % 8 - tsq % 8) == 1 and board[tsq] is None:
        ep_sq = (fsq // 8) * 8 + (tsq % 8)
        ep_cap = board[ep_sq]
        board[ep_sq] = None

    # Castling
    if moved and moved[1] == 'K':
        if m == 'e1g1':
            castle_info = (5, 7, board[7])
            board[5] = board[7]
            board[7] = None
        elif m == 'e1c1':
            castle_info = (3, 0, board[0])
            board[3] = board[0]
            board[0] = None
        elif m == 'e8g8':
            castle_info = (61, 63, board[63])
            board[61] = board[63]
            board[63] = None
        elif m == 'e8c8':
            castle_info = (59, 56, board[56])
            board[59] = board[56]
            board[56] = None

    board[fsq] = None
    if len(m) > 4:
        board[tsq] = moved[0] + m[4].upper()
    else:
        board[tsq] = moved

    return (fsq, tsq, moved, captured, ep_sq, ep_cap, castle_info)

def unmake_move(board: list, undo):
    fsq, tsq, moved, captured, ep_sq, ep_cap, castle_info = undo
    board[fsq] = moved
    board[tsq] = captured
    if ep_sq is not None:
        board[ep_sq] = ep_cap
    if castle_info:
        r_dest, r_src, r_piece = castle_info
        board[r_src] = r_piece
        board[r_dest] = None

def get_legal_moves(board: list, color: str) -> list:
    moves = []
    opp = 'b' if color == 'w' else 'w'
    pawn_dir = 1 if color == 'w' else -1
    start_rank = 1 if color == 'w' else 6
    promo_rank = 7 if color == 'w' else 0

    for sq in range(64):
        p = board[sq]
        if not p or p[0] != color:
            continue
        pt = p[1]
        f, r = sq % 8, sq // 8

        if pt == 'P':
            # Single push
            nr = r + pawn_dir
            if 0 <= nr < 8:
                dest = nr * 8 + f
                if board[dest] is None:
                    if nr == promo_rank:
                        for pr in ('q', 'r', 'b', 'n'):
                            moves.append(sq_name(sq) + sq_name(dest) + pr)
                    else:
                        moves.append(sq_name(sq) + sq_name(dest))
                        # Double push
                        if r == start_rank:
                            dest2 = (r + 2 * pawn_dir) * 8 + f
                            if board[dest2] is None:
                                moves.append(sq_name(sq) + sq_name(dest2))

            # Captures
            for df in (-1, 1):
                nf = f + df
                if 0 <= nf < 8 and 0 <= nr < 8:
                    dest = nr * 8 + nf
                    if board[dest] and board[dest][0] == opp:
                        if nr == promo_rank:
                            for pr in ('q', 'r', 'b', 'n'):
                                moves.append(sq_name(sq) + sq_name(dest) + pr)
                        else:
                            moves.append(sq_name(sq) + sq_name(dest))

        elif pt == 'N':
            for df, dr in ((1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2)):
                nf, nr = f + df, r + dr
                if 0 <= nf < 8 and 0 <= nr < 8:
                    dest = nr * 8 + nf
                    if board[dest] is None or board[dest][0] == opp:
                        moves.append(sq_name(sq) + sq_name(dest))

        elif pt in ('B', 'R', 'Q'):
            dirs = []
            if pt in ('B', 'Q'):
                dirs.extend(((1, 1), (1, -1), (-1, 1), (-1, -1)))
            if pt in ('R', 'Q'):
                dirs.extend(((1, 0), (-1, 0), (0, 1), (0, -1)))
            for df, dr in dirs:
                step = 1
                while True:
                    nf, nr = f + df * step, r + dr * step
                    if not (0 <= nf < 8 and 0 <= nr < 8):
                        break
                    dest = nr * 8 + nf
                    target = board[dest]
                    if target is None:
                        moves.append(sq_name(sq) + sq_name(dest))
                    else:
                        if target[0] == opp:
                            moves.append(sq_name(sq) + sq_name(dest))
                        break
                    step += 1

        elif pt == 'K':
            for df in (-1, 0, 1):
                for dr in (-1, 0, 1):
                    if df == 0 and dr == 0:
                        continue
                    nf, nr = f + df, r + dr
                    if 0 <= nf < 8 and 0 <= nr < 8:
                        dest = nr * 8 + nf
                        if board[dest] is None or board[dest][0] == opp:
                            moves.append(sq_name(sq) + sq_name(dest))

    # Filter out illegal moves that leave king in check
    legal = []
    for m in moves:
        undo = make_move(board, m)
        if not is_in_check(board, color):
            legal.append(m)
        unmake_move(board, undo)
    return legal

def score_move_ordering(board: list, m: str) -> int:
    score = 0
    fsq = name_sq(m[:2])
    tsq = name_sq(m[2:4])
    attacker = board[fsq]
    victim = board[tsq]

    if victim:
        # MVV-LVA
        score += 10000 + PIECE_VALS.get(victim[1], 0) * 10 - PIECE_VALS.get(attacker[1], 0)
    if len(m) > 4:
        promo = m[4].upper()
        score += 20000 + PIECE_VALS.get(promo, 0)
    return score

def alpha_beta(board: list, depth: int, alpha: int, beta: int, maximizing: bool, end_time: float):
    if time.perf_counter() > end_time:
        raise TimeoutError()

    color = 'w' if maximizing else 'b'
    moves = get_legal_moves(board, color)

    if not moves:
        if is_in_check(board, color):
            return -999999 if maximizing else 999999
        return 0

    if depth == 0:
        return evaluate_board(board)

    moves.sort(key=lambda m: score_move_ordering(board, m), reverse=True)

    if maximizing:
        max_eval = -10000000
        for m in moves:
            undo = make_move(board, m)
            ev = alpha_beta(board, depth - 1, alpha, beta, False, end_time)
            unmake_move(board, undo)
            max_eval = max(max_eval, ev)
            alpha = max(alpha, ev)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = 10000000
        for m in moves:
            undo = make_move(board, m)
            ev = alpha_beta(board, depth - 1, alpha, beta, True, end_time)
            unmake_move(board, undo)
            min_eval = min(min_eval, ev)
            beta = min(beta, ev)
            if beta <= alpha:
                break
        return min_eval

def policy(pieces: dict[str, str], to_play: str, legal_moves: list = None, *args, **kwargs) -> str:
    start_time = time.perf_counter()
    end_time = start_time + 0.65

    if legal_moves is None and 'legal_moves' in kwargs:
        legal_moves = kwargs['legal_moves']

    board = [None] * 64
    for sq, p in pieces.items():
        board[name_sq(sq)] = p

    my_color = 'w' if to_play.lower().startswith('w') else 'b'
    is_white = (my_color == 'w')

    if legal_moves is None:
        available_moves = get_legal_moves(board, my_color)
    else:
        available_moves = list(legal_moves)

    if not available_moves:
        return ""
    if len(available_moves) == 1:
        return available_moves[0]

    # Pre-sort moves
    available_moves.sort(key=lambda m: score_move_ordering(board, m), reverse=True)
    best_move = available_moves[0]

    # Iterative deepening search (Depth 1, 2, 3)
    for depth in range(1, 4):
        current_best = best_move
        alpha = -10000000
        beta = 10000000

        try:
            if is_white:
                best_val = -10000000
                for m in available_moves:
                    undo = make_move(board, m)
                    val = alpha_beta(board, depth - 1, alpha, beta, False, end_time)
                    unmake_move(board, undo)
                    if val > best_val:
                        best_val = val
                        current_best = m
                    alpha = max(alpha, val)
            else:
                best_val = 10000000
                for m in available_moves:
                    undo = make_move(board, m)
                    val = alpha_beta(board, depth - 1, alpha, beta, True, end_time)
                    unmake_move(board, undo)
                    if val < best_val:
                        best_val = val
                        current_best = m
                    beta = min(beta, val)

            best_move = current_best
            if abs(best_val) > 900000:
                break
        except TimeoutError:
            break

    if legal_moves and best_move not in legal_moves:
        return legal_moves[0]
    return best_move
