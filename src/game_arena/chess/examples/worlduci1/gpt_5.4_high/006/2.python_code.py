
import time

PAWN = 1
KNIGHT = 2
BISHOP = 3
ROOK = 4
QUEEN = 5
KING = 6

VALUE = [0, 100, 320, 330, 500, 900, 0]
PHASE_VAL = [0, 0, 1, 1, 2, 4, 0]

PIECE_FROM_CHAR = {
    "P": PAWN,
    "N": KNIGHT,
    "B": BISHOP,
    "R": ROOK,
    "Q": QUEEN,
    "K": KING,
}

PROMO_TO_CHAR = {
    QUEEN: "q",
    ROOK: "r",
    BISHOP: "b",
    KNIGHT: "n",
}

INF = 10_000_000
MATE = 1_000_000

_deadline = 0.0
_nodes = 0


def _flat(rows):
    return tuple(x for row in rows for x in row)


PAWN_PST = _flat([
    [0, 0, 0, 0, 0, 0, 0, 0],
    [5, 10, 10, -20, -20, 10, 10, 5],
    [5, -5, -10, 0, 0, -10, -5, 5],
    [0, 0, 0, 20, 20, 0, 0, 0],
    [5, 5, 10, 25, 25, 10, 5, 5],
    [10, 10, 20, 30, 30, 20, 10, 10],
    [50, 50, 50, 50, 50, 50, 50, 50],
    [0, 0, 0, 0, 0, 0, 0, 0],
])

KNIGHT_PST = _flat([
    [-50, -40, -30, -30, -30, -30, -40, -50],
    [-40, -20, 0, 5, 5, 0, -20, -40],
    [-30, 5, 10, 15, 15, 10, 5, -30],
    [-30, 0, 15, 20, 20, 15, 0, -30],
    [-30, 5, 15, 20, 20, 15, 5, -30],
    [-30, 0, 10, 15, 15, 10, 0, -30],
    [-40, -20, 0, 0, 0, 0, -20, -40],
    [-50, -40, -30, -30, -30, -30, -40, -50],
])

BISHOP_PST = _flat([
    [-20, -10, -10, -10, -10, -10, -10, -20],
    [-10, 0, 0, 0, 0, 0, 0, -10],
    [-10, 0, 5, 10, 10, 5, 0, -10],
    [-10, 5, 5, 10, 10, 5, 5, -10],
    [-10, 0, 10, 10, 10, 10, 0, -10],
    [-10, 10, 10, 10, 10, 10, 10, -10],
    [-10, 5, 0, 0, 0, 0, 5, -10],
    [-20, -10, -10, -10, -10, -10, -10, -20],
])

ROOK_PST = _flat([
    [0, 0, 0, 0, 0, 0, 0, 0],
    [5, 10, 10, 10, 10, 10, 10, 5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [0, 0, 0, 5, 5, 0, 0, 0],
])

QUEEN_PST = _flat([
    [-20, -10, -10, -5, -5, -10, -10, -20],
    [-10, 0, 5, 0, 0, 0, 0, -10],
    [-10, 5, 5, 5, 5, 5, 0, -10],
    [0, 0, 5, 5, 5, 5, 0, -5],
    [-5, 0, 5, 5, 5, 5, 0, -5],
    [-10, 0, 5, 5, 5, 5, 0, -10],
    [-10, 0, 0, 0, 0, 0, 0, -10],
    [-20, -10, -10, -5, -5, -10, -10, -20],
])

KING_MG = _flat([
    [20, 30, 10, 0, 0, 10, 30, 20],
    [20, 20, 0, 0, 0, 0, 20, 20],
    [-10, -20, -20, -20, -20, -20, -20, -10],
    [-20, -30, -30, -40, -40, -30, -30, -20],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
])

KING_EG = _flat([
    [-50, -30, -30, -30, -30, -30, -30, -50],
    [-30, -30, 0, 0, 0, 0, -30, -30],
    [-30, -10, 20, 30, 30, 20, -10, -30],
    [-30, -10, 30, 40, 40, 30, -10, -30],
    [-30, -10, 30, 40, 40, 30, -10, -30],
    [-30, -10, 20, 30, 30, 20, -10, -30],
    [-30, -20, -10, 0, 0, -10, -20, -30],
    [-50, -40, -30, -20, -20, -30, -40, -50],
])

PST = [None, PAWN_PST, KNIGHT_PST, BISHOP_PST, ROOK_PST, QUEEN_PST, None]

SQUARE_NAMES = [chr(97 + f) + str(r + 1) for r in range(8) for f in range(8)]


def _precompute_targets():
    knight = [[] for _ in range(64)]
    king = [[] for _ in range(64)]
    rook_rays = [[] for _ in range(64)]
    bishop_rays = [[] for _ in range(64)]

    knight_steps = [(1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2)]
    king_steps = [(1, 1), (1, 0), (1, -1), (0, 1), (0, -1), (-1, 1), (-1, 0), (-1, -1)]
    rook_dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    bishop_dirs = [(1, 1), (1, -1), (-1, 1), (-1, -1)]

    for sq in range(64):
        f = sq & 7
        r = sq >> 3

        for df, dr in knight_steps:
            nf = f + df
            nr = r + dr
            if 0 <= nf < 8 and 0 <= nr < 8:
                knight[sq].append(nr * 8 + nf)

        for df, dr in king_steps:
            nf = f + df
            nr = r + dr
            if 0 <= nf < 8 and 0 <= nr < 8:
                king[sq].append(nr * 8 + nf)

        for df, dr in rook_dirs:
            ray = []
            nf = f + df
            nr = r + dr
            while 0 <= nf < 8 and 0 <= nr < 8:
                ray.append(nr * 8 + nf)
                nf += df
                nr += dr
            rook_rays[sq].append(tuple(ray))

        for df, dr in bishop_dirs:
            ray = []
            nf = f + df
            nr = r + dr
            while 0 <= nf < 8 and 0 <= nr < 8:
                ray.append(nr * 8 + nf)
                nf += df
                nr += dr
            bishop_rays[sq].append(tuple(ray))

    return (
        tuple(tuple(x) for x in knight),
        tuple(tuple(x) for x in king),
        tuple(tuple(tuple(ray) for ray in rays) for rays in rook_rays),
        tuple(tuple(tuple(ray) for ray in rays) for rays in bishop_rays),
    )


KNIGHT_TARGETS, KING_TARGETS, ROOK_RAYS, BISHOP_RAYS = _precompute_targets()


def square_to_idx(sq):
    return (ord(sq[1]) - 49) * 8 + (ord(sq[0]) - 97)


def idx_to_square(idx):
    return SQUARE_NAMES[idx]


def move_to_uci(move):
    fr, to, promo = move
    u = SQUARE_NAMES[fr] + SQUARE_NAMES[to]
    if promo:
        u += PROMO_TO_CHAR[promo]
    return u


def board_from_pieces(pieces):
    board = [0] * 64
    for sq, pc in pieces.items():
        side = 1 if pc[0] == "w" else -1
        board[square_to_idx(sq)] = side * PIECE_FROM_CHAR[pc[1]]
    return board


def maybe_timeout():
    global _nodes
    _nodes += 1
    if (_nodes & 255) == 0 and time.perf_counter() > _deadline:
        raise TimeoutError


def find_king(board, side):
    target = side * KING
    for i, p in enumerate(board):
        if p == target:
            return i
    return -1


def is_attacked(board, sq, by_side):
    if sq < 0:
        return False

    f = sq & 7

    # Pawn attacks
    if by_side == 1:
        if f < 7:
            j = sq - 7
            if j >= 0 and board[j] == PAWN:
                return True
        if f > 0:
            j = sq - 9
            if j >= 0 and board[j] == PAWN:
                return True
    else:
        if f < 7:
            j = sq + 9
            if j < 64 and board[j] == -PAWN:
                return True
        if f > 0:
            j = sq + 7
            if j < 64 and board[j] == -PAWN:
                return True

    # Knight attacks
    target_knight = by_side * KNIGHT
    for j in KNIGHT_TARGETS[sq]:
        if board[j] == target_knight:
            return True

    # King attacks
    target_king = by_side * KING
    for j in KING_TARGETS[sq]:
        if board[j] == target_king:
            return True

    # Bishop / Queen attacks
    b = by_side * BISHOP
    q = by_side * QUEEN
    for rays in BISHOP_RAYS[sq]:
        for j in rays:
            p = board[j]
            if p == 0:
                continue
            if p == b or p == q:
                return True
            break

    # Rook / Queen attacks
    r = by_side * ROOK
    for rays in ROOK_RAYS[sq]:
        for j in rays:
            p = board[j]
            if p == 0:
                continue
            if p == r or p == q:
                return True
            break

    return False


def make_move(board, move):
    fr, to, promo = move
    p = board[fr]
    side = 1 if p > 0 else -1
    nb = board.copy()
    nb[fr] = 0
    nb[to] = side * promo if promo else p

    # Conservative support for castling-shaped king moves.
    if abs(p) == KING and abs(to - fr) == 2:
        if to > fr:
            rook_from = fr + 3
            rook_to = fr + 1
        else:
            rook_from = fr - 4
            rook_to = fr - 1
        nb[rook_to] = nb[rook_from]
        nb[rook_from] = 0

    return nb


def generate_pseudo_moves(board, side, tactical_only=False):
    moves = []
    promo_pieces = (QUEEN, ROOK, BISHOP, KNIGHT)

    for sq, p in enumerate(board):
        if p * side <= 0:
            continue

        t = abs(p)
        f = sq & 7
        r = sq >> 3

        if t == PAWN:
            nr = r + side
            if 0 <= nr < 8:
                to = sq + 8 * side

                # Quiet push
                if board[to] == 0:
                    if nr == 7 or nr == 0:
                        for pr in promo_pieces:
                            moves.append((sq, to, pr))
                    elif not tactical_only:
                        moves.append((sq, to, 0))
                        # Double push
                        if (side == 1 and r == 1) or (side == -1 and r == 6):
                            to2 = sq + 16 * side
                            if board[to2] == 0:
                                moves.append((sq, to2, 0))

                # Captures
                for df in (-1, 1):
                    nf = f + df
                    if 0 <= nf < 8:
                        cap = nr * 8 + nf
                        target = board[cap]
                        if target * side < 0 and abs(target) != KING:
                            if nr == 7 or nr == 0:
                                for pr in promo_pieces:
                                    moves.append((sq, cap, pr))
                            else:
                                moves.append((sq, cap, 0))

        elif t == KNIGHT:
            for to in KNIGHT_TARGETS[sq]:
                target = board[to]
                if target == 0:
                    if not tactical_only:
                        moves.append((sq, to, 0))
                elif target * side < 0 and abs(target) != KING:
                    moves.append((sq, to, 0))

        elif t == BISHOP:
            rays_set = BISHOP_RAYS[sq]
            for ray in rays_set:
                for to in ray:
                    target = board[to]
                    if target == 0:
                        if not tactical_only:
                            moves.append((sq, to, 0))
                        continue
                    if target * side < 0 and abs(target) != KING:
                        moves.append((sq, to, 0))
                    break

        elif t == ROOK:
            rays_set = ROOK_RAYS[sq]
            for ray in rays_set:
                for to in ray:
                    target = board[to]
                    if target == 0:
                        if not tactical_only:
                            moves.append((sq, to, 0))
                        continue
                    if target * side < 0 and abs(target) != KING:
                        moves.append((sq, to, 0))
                    break

        elif t == QUEEN:
            for ray in ROOK_RAYS[sq]:
                for to in ray:
                    target = board[to]
                    if target == 0:
                        if not tactical_only:
                            moves.append((sq, to, 0))
                        continue
                    if target * side < 0 and abs(target) != KING:
                        moves.append((sq, to, 0))
                    break
            for ray in BISHOP_RAYS[sq]:
                for to in ray:
                    target = board[to]
                    if target == 0:
                        if not tactical_only:
                            moves.append((sq, to, 0))
                        continue
                    if target * side < 0 and abs(target) != KING:
                        moves.append((sq, to, 0))
                    break

        elif t == KING:
            for to in KING_TARGETS[sq]:
                target = board[to]
                if target == 0:
                    if not tactical_only:
                        moves.append((sq, to, 0))
                elif target * side < 0 and abs(target) != KING:
                    moves.append((sq, to, 0))

    return moves


def generate_legal_moves(board, side, tactical_only=False):
    king_sq = find_king(board, side)
    pseudo = generate_pseudo_moves(board, side, tactical_only)
    if king_sq == -1:
        return pseudo

    legal = []
    for mv in pseudo:
        fr, to, _ = mv
        nb = make_move(board, mv)
        ks = to if abs(board[fr]) == KING else king_sq
        if not is_attacked(nb, ks, -side):
            legal.append(mv)
    return legal


def generate_castling_fallback(board, side):
    # Only used as an emergency last resort because full castling rights are not provided.
    moves = []
    if side == 1:
        ksq = 4
        if board[ksq] != KING:
            return moves
        if is_attacked(board, ksq, -1):
            return moves
        # O-O
        if board[7] == ROOK and board[5] == 0 and board[6] == 0:
            if not is_attacked(board, 5, -1) and not is_attacked(board, 6, -1):
                moves.append((4, 6, 0))
        # O-O-O
        if board[0] == ROOK and board[1] == 0 and board[2] == 0 and board[3] == 0:
            if not is_attacked(board, 3, -1) and not is_attacked(board, 2, -1):
                moves.append((4, 2, 0))
    else:
        ksq = 60
        if board[ksq] != -KING:
            return moves
        if is_attacked(board, ksq, 1):
            return moves
        # O-O
        if board[63] == -ROOK and board[61] == 0 and board[62] == 0:
            if not is_attacked(board, 61, 1) and not is_attacked(board, 62, 1):
                moves.append((60, 62, 0))
        # O-O-O
        if board[56] == -ROOK and board[57] == 0 and board[58] == 0 and board[59] == 0:
            if not is_attacked(board, 59, 1) and not is_attacked(board, 58, 1):
                moves.append((60, 58, 0))
    return moves


def pawn_shield(board, king_sq, side):
    f = king_sq & 7
    r = king_sq >> 3
    rr = r if side == 1 else 7 - r

    bonus = 0
    if rr <= 1:
        nr = r + 1 if side == 1 else r - 1
        if 0 <= nr < 8:
            for nf in (f - 1, f, f + 1):
                if 0 <= nf < 8:
                    p = board[nr * 8 + nf]
                    if p == side * PAWN:
                        bonus += 8
                    elif p == 0:
                        bonus -= 4
    else:
        bonus -= 5 * min(rr, 4)
    return bonus


def evaluate(board, side):
    white = 0
    black = 0
    phase = 0

    white_bishops = 0
    black_bishops = 0
    white_rook_files = []
    black_rook_files = []
    white_pawn_files = [0] * 8
    black_pawn_files = [0] * 8
    white_pawn_ranks = [[] for _ in range(8)]
    black_pawn_ranks = [[] for _ in range(8)]
    white_king_sq = -1
    black_king_sq = -1

    pieces = []

    for sq, p in enumerate(board):
        if p == 0:
            continue
        s = 1 if p > 0 else -1
        t = abs(p)
        pieces.append((sq, s, t))

        if t != PAWN and t != KING:
            phase += PHASE_VAL[t]

        f = sq & 7
        r = sq >> 3

        if t == PAWN:
            if s == 1:
                white_pawn_files[f] += 1
                white_pawn_ranks[f].append(r)
            else:
                black_pawn_files[f] += 1
                black_pawn_ranks[f].append(r)
        elif t == BISHOP:
            if s == 1:
                white_bishops += 1
            else:
                black_bishops += 1
        elif t == ROOK:
            if s == 1:
                white_rook_files.append(f)
            else:
                black_rook_files.append(f)
        elif t == KING:
            if s == 1:
                white_king_sq = sq
            else:
                black_king_sq = sq

    phase = min(24, phase)
    end_phase = 24 - phase

    for sq, s, t in pieces:
        idx = sq if s == 1 else (sq ^ 56)
        if t == KING:
            ps = (KING_MG[idx] * phase + KING_EG[idx] * end_phase) // 24
        else:
            ps = PST[t][idx]
        v = VALUE[t] + ps
        if s == 1:
            white += v
        else:
            black += v

    # Bishop pair
    if white_bishops >= 2:
        white += 30
    if black_bishops >= 2:
        black += 30

    # Pawn structure
    for f in range(8):
        if white_pawn_files[f] > 1:
            white -= 14 * (white_pawn_files[f] - 1)
        if black_pawn_files[f] > 1:
            black -= 14 * (black_pawn_files[f] - 1)

        if white_pawn_files[f]:
            left_empty = (f == 0 or white_pawn_files[f - 1] == 0)
            right_empty = (f == 7 or white_pawn_files[f + 1] == 0)
            if left_empty and right_empty:
                white -= 10 * white_pawn_files[f]

        if black_pawn_files[f]:
            left_empty = (f == 0 or black_pawn_files[f - 1] == 0)
            right_empty = (f == 7 or black_pawn_files[f + 1] == 0)
            if left_empty and right_empty:
                black -= 10 * black_pawn_files[f]

    # Passed pawns
    for f in range(8):
        for r in white_pawn_ranks[f]:
            passed = True
            for ff in (f - 1, f, f + 1):
                if 0 <= ff < 8:
                    for br in black_pawn_ranks[ff]:
                        if br > r:
                            passed = False
                            break
                if not passed:
                    break
            if passed:
                white += 12 + 10 * r

        for r in black_pawn_ranks[f]:
            passed = True
            for ff in (f - 1, f, f + 1):
                if 0 <= ff < 8:
                    for wr in white_pawn_ranks[ff]:
                        if wr < r:
                            passed = False
                            break
                if not passed:
                    break
            if passed:
                black += 12 + 10 * (7 - r)

    # Rooks on open/semi-open files
    for f in white_rook_files:
        if white_pawn_files[f] == 0 and black_pawn_files[f] == 0:
            white += 20
        elif white_pawn_files[f] == 0:
            white += 10

    for f in black_rook_files:
        if white_pawn_files[f] == 0 and black_pawn_files[f] == 0:
            black += 20
        elif black_pawn_files[f] == 0:
            black += 10

    # King safety in middlegame-ish positions
    if phase > 12:
        if white_king_sq != -1:
            white += pawn_shield(board, white_king_sq, 1)
        if black_king_sq != -1:
            black += pawn_shield(board, black_king_sq, -1)

    score = white - black
    return score if side == 1 else -score


def move_order_value(board, move, pv_move=None):
    score = 0
    if pv_move is not None and move == pv_move:
        score += 10_000_000

    fr, to, promo = move
    mover = abs(board[fr])
    target = abs(board[to])

    if promo:
        score += 90_000 + VALUE[promo]

    if target:
        score += 100_000 + 16 * VALUE[target] - VALUE[mover]

    if mover == PAWN and not target:
        # Slightly prefer advancing pawns.
        tr = to >> 3
        score += tr if board[fr] > 0 else (7 - tr)

    return score


def order_moves(board, moves, pv_move=None):
    if len(moves) <= 1:
        return moves
    return sorted(moves, key=lambda mv: move_order_value(board, mv, pv_move), reverse=True)


def quiescence(board, side, alpha, beta, ply, qdepth):
    maybe_timeout()

    if qdepth >= 8:
        return evaluate(board, side)

    king_sq = find_king(board, side)
    in_check = king_sq != -1 and is_attacked(board, king_sq, -side)

    if in_check:
        moves = generate_legal_moves(board, side, tactical_only=False)
        if not moves:
            return -MATE + ply
        moves = order_moves(board, moves)
        best = -INF
        for mv in moves:
            score = -quiescence(make_move(board, mv), -side, -beta, -alpha, ply + 1, qdepth + 1)
            if score > best:
                best = score
            if score > alpha:
                alpha = score
            if alpha >= beta:
                break
        return best

    stand_pat = evaluate(board, side)
    if stand_pat >= beta:
        return beta
    if stand_pat > alpha:
        alpha = stand_pat

    moves = generate_legal_moves(board, side, tactical_only=True)
    if not moves:
        return stand_pat

    moves = order_moves(board, moves)

    for mv in moves:
        fr, to, promo = mv
        gain = VALUE[abs(board[to])]
        if promo:
            gain += VALUE[promo] - VALUE[PAWN]

        # Simple delta pruning
        if stand_pat + gain + 120 < alpha:
            continue

        score = -quiescence(make_move(board, mv), -side, -beta, -alpha, ply + 1, qdepth + 1)
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score

    return alpha


def negamax(board, side, depth, alpha, beta, ply):
    maybe_timeout()

    if depth <= 0:
        return quiescence(board, side, alpha, beta, ply, 0)

    legal = generate_legal_moves(board, side, tactical_only=False)
    if not legal:
        king_sq = find_king(board, side)
        if king_sq != -1 and is_attacked(board, king_sq, -side):
            return -MATE + ply
        return 0

    legal = order_moves(board, legal)

    best = -INF
    for mv in legal:
        score = -negamax(make_move(board, mv), -side, depth - 1, -beta, -alpha, ply + 1)
        if score > best:
            best = score
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break

    return best


def policy(pieces: dict[str, str], to_play: str) -> str:
    global _deadline, _nodes

    side = 1 if to_play == "white" else -1
    board = board_from_pieces(pieces)

    _nodes = 0
    _deadline = time.perf_counter() + 0.95

    legal_moves = generate_legal_moves(board, side, tactical_only=False)

    if not legal_moves:
        # Emergency conservative castling fallback only because rights/history are unavailable.
        castle_moves = generate_castling_fallback(board, side)
        if castle_moves:
            return move_to_uci(castle_moves[0])

        # Final emergency fallback.
        pseudo = generate_pseudo_moves(board, side, tactical_only=False)
        if pseudo:
            return move_to_uci(pseudo[0])

        # Unreachable in non-terminal positions, but return a string regardless.
        return "a1a1"

    if len(legal_moves) == 1:
        return move_to_uci(legal_moves[0])

    piece_count = sum(1 for p in board if p)
    if piece_count <= 8:
        max_depth = 6
    elif piece_count <= 14:
        max_depth = 5
    else:
        max_depth = 4

    best_move = order_moves(board, legal_moves)[0]
    pv_move = best_move
    prev_scores = None

    for depth in range(1, max_depth + 1):
        if time.perf_counter() > _deadline:
            break

        try:
            if prev_scores is None:
                root_moves = order_moves(board, legal_moves, pv_move)
            else:
                root_moves = sorted(
                    legal_moves,
                    key=lambda mv: (prev_scores.get(mv, -INF), move_order_value(board, mv, pv_move)),
                    reverse=True,
                )

            current_best = best_move
            current_scores = {}
            alpha = -INF
            beta = INF
            best_score = -INF

            for mv in root_moves:
                score = -negamax(make_move(board, mv), -side, depth - 1, -beta, -alpha, 1)
                current_scores[mv] = score

                if score > best_score:
                    best_score = score
                    current_best = mv

                if score > alpha:
                    alpha = score

            best_move = current_best
            pv_move = current_best
            prev_scores = current_scores

            if best_score > MATE - 1000:
                break

        except TimeoutError:
            break

    return move_to_uci(best_move)
