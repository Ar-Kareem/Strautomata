
import time

WHITE = 1
BLACK = -1

PAWN = 1
KNIGHT = 2
BISHOP = 3
ROOK = 4
QUEEN = 5
KING = 6

PIECE_VALUE = [0, 100, 320, 330, 500, 900, 0]
PHASE_WEIGHT = [0, 0, 1, 1, 2, 4, 0]

PROMOTION_PIECES = (QUEEN, ROOK, BISHOP, KNIGHT)
PROMO_CHAR = {QUEEN: "q", ROOK: "r", BISHOP: "b", KNIGHT: "n"}
PIECE_FROM_CHAR = {
    "P": PAWN,
    "N": KNIGHT,
    "B": BISHOP,
    "R": ROOK,
    "Q": QUEEN,
    "K": KING,
}

INF = 10**9
MATE = 1_000_000
TT_LIMIT = 250_000

SQUARES = []
SQ_INDEX = {}
for _r in range(8):
    for _f in range(8):
        _s = chr(97 + _f) + chr(49 + _r)
        _i = _r * 8 + _f
        SQUARES.append(_s)
        SQ_INDEX[_s] = _i

MIRROR = [((7 - (i >> 3)) << 3) + (i & 7) for i in range(64)]


def _step_moves(deltas):
    table = []
    for sq in range(64):
        f = sq & 7
        r = sq >> 3
        moves = []
        for df, dr in deltas:
            nf = f + df
            nr = r + dr
            if 0 <= nf < 8 and 0 <= nr < 8:
                moves.append(nr * 8 + nf)
        table.append(tuple(moves))
    return table


KNIGHT_MOVES = _step_moves(
    ((1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2))
)
KING_MOVES = _step_moves(
    ((1, 1), (1, 0), (1, -1), (0, 1), (0, -1), (-1, 1), (-1, 0), (-1, -1))
)

BISHOP_DIRS = ((1, 1), (1, -1), (-1, 1), (-1, -1))
ROOK_DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _build_rays(dirs):
    table = []
    for sq in range(64):
        f = sq & 7
        r = sq >> 3
        rays = []
        for df, dr in dirs:
            ray = []
            nf = f + df
            nr = r + dr
            while 0 <= nf < 8 and 0 <= nr < 8:
                ray.append(nr * 8 + nf)
                nf += df
                nr += dr
            rays.append(tuple(ray))
        table.append(tuple(rays))
    return table


BISHOP_RAYS = _build_rays(BISHOP_DIRS)
ROOK_RAYS = _build_rays(ROOK_DIRS)

PST_MID = [[0] * 64 for _ in range(7)]
PST_END = [[0] * 64 for _ in range(7)]
CENTER_SCORE = [0] * 64

_PAWN_MID_RANK = [0, 2, 10, 22, 35, 55, 90, 0]
_PAWN_END_RANK = [0, 4, 12, 28, 50, 85, 135, 0]

for sq in range(64):
    f = sq & 7
    r = sq >> 3
    dfc = f - 3.5
    drc = r - 3.5
    dist2 = dfc * dfc + drc * drc

    pawn_center = 12 if f in (3, 4) else 6 if f in (2, 5) else 2 if f in (1, 6) else -4
    PST_MID[PAWN][sq] = int(_PAWN_MID_RANK[r] + pawn_center)
    PST_END[PAWN][sq] = int(_PAWN_END_RANK[r] + pawn_center // 2)

    PST_MID[KNIGHT][sq] = int(24 - 4.2 * dist2)
    PST_END[KNIGHT][sq] = int(12 - 3.2 * dist2)

    diag_bonus = 4 if (f == r or f + r == 7) else 0
    PST_MID[BISHOP][sq] = int(14 - 2.2 * dist2 + diag_bonus)
    PST_END[BISHOP][sq] = int(12 - 2.0 * dist2 + diag_bonus)

    PST_MID[ROOK][sq] = int(r * 2 + (18 if r == 6 else 0) + (4 if f in (3, 4) else 0))
    PST_END[ROOK][sq] = int(r * 3 + (12 if r == 6 else 0))

    PST_MID[QUEEN][sq] = int(8 - 1.2 * dist2)
    PST_END[QUEEN][sq] = int(18 - 2.0 * dist2)

    PST_MID[KING][sq] = int(12 * abs(f - 3.5) - 18 * r)
    if r == 0:
        PST_MID[KING][sq] += 12
    if f in (1, 2, 6):
        PST_MID[KING][sq] += 8
    if f in (3, 4) and r <= 1:
        PST_MID[KING][sq] -= 6
    PST_END[KING][sq] = int(45 - 6.0 * dist2)

    CENTER_SCORE[sq] = int(20 - 3.0 * dist2)


MASK64 = (1 << 64) - 1


def _splitmix_next(x):
    x = (x + 0x9E3779B97F4A7C15) & MASK64
    z = x
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK64
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK64
    return x, (z ^ (z >> 31)) & MASK64


_seed = 0xBAD5EED123456789
ZOBRIST = []
for _sq in range(64):
    _row = []
    for _ in range(12):
        _seed, _v = _splitmix_next(_seed)
        _row.append(_v)
    ZOBRIST.append(tuple(_row))
_seed, SIDE_HASH = _splitmix_next(_seed)


def _piece_index(piece):
    t = abs(piece) - 1
    return t if piece > 0 else 6 + t


def _make_start_board():
    b = [0] * 64
    back = [ROOK, KNIGHT, BISHOP, QUEEN, KING, BISHOP, KNIGHT, ROOK]
    for f, t in enumerate(back):
        b[f] = WHITE * t
        b[8 + f] = WHITE * PAWN
        b[48 + f] = BLACK * PAWN
        b[56 + f] = BLACK * t
    return tuple(b)


START_TUPLE = _make_start_board()

TT = {}
HISTORY = {}
KILLERS = [[None, None] for _ in range(128)]
DEADLINE = 0.0
NODES = 0


class SearchTimeout(Exception):
    pass


def _parse_board(pieces):
    board = [0] * 64
    for sq, code in pieces.items():
        idx = SQ_INDEX.get(sq)
        if idx is None or not code or len(code) < 2:
            continue
        side = WHITE if code[0] == "w" else BLACK
        ptype = PIECE_FROM_CHAR.get(code[1].upper())
        if ptype:
            board[idx] = side * ptype
    return board


def _move_to_uci(move):
    fr, to, promo = move
    s = SQUARES[fr] + SQUARES[to]
    if promo:
        s += PROMO_CHAR[promo]
    return s


def _hash_board(board):
    h = 0
    for sq, p in enumerate(board):
        if p:
            h ^= ZOBRIST[sq][_piece_index(p)]
    return h


def _hash_after(h, move, piece, captured):
    fr, to, promo = move
    h ^= ZOBRIST[fr][_piece_index(piece)]
    if captured:
        h ^= ZOBRIST[to][_piece_index(captured)]
    new_piece = piece if promo == 0 else (WHITE if piece > 0 else BLACK) * promo
    h ^= ZOBRIST[to][_piece_index(new_piece)]
    return h


def _make_move(board, move):
    fr, to, promo = move
    piece = board[fr]
    captured = board[to]
    board[fr] = 0
    board[to] = piece if promo == 0 else (WHITE if piece > 0 else BLACK) * promo
    return piece, captured


def _unmake_move(board, move, piece, captured):
    fr, to, _ = move
    board[fr] = piece
    board[to] = captured


def _find_king(board, color):
    target = color * KING
    for i, p in enumerate(board):
        if p == target:
            return i
    return -1


def _is_attacked(board, sq, by_color):
    if sq < 0:
        return False

    f = sq & 7
    r = sq >> 3
    pawn = by_color * PAWN

    if by_color == WHITE:
        if r > 0:
            if f > 0 and board[sq - 9] == pawn:
                return True
            if f < 7 and board[sq - 7] == pawn:
                return True
    else:
        if r < 7:
            if f > 0 and board[sq + 7] == pawn:
                return True
            if f < 7 and board[sq + 9] == pawn:
                return True

    knight = by_color * KNIGHT
    for to in KNIGHT_MOVES[sq]:
        if board[to] == knight:
            return True

    king = by_color * KING
    for to in KING_MOVES[sq]:
        if board[to] == king:
            return True

    for ray in BISHOP_RAYS[sq]:
        for to in ray:
            p = board[to]
            if p:
                if p * by_color > 0:
                    t = abs(p)
                    if t == BISHOP or t == QUEEN:
                        return True
                break

    for ray in ROOK_RAYS[sq]:
        for to in ray:
            p = board[to]
            if p:
                if p * by_color > 0:
                    t = abs(p)
                    if t == ROOK or t == QUEEN:
                        return True
                break

    return False


def _generate_pseudo(board, color, captures_only=False):
    moves = []
    enemy = -color

    for sq, piece in enumerate(board):
        if piece * color <= 0:
            continue

        t = abs(piece)

        if t == PAWN:
            f = sq & 7
            r = sq >> 3
            direction = 8 if color == WHITE else -8
            start_rank = 1 if color == WHITE else 6
            last_rank = 7 if color == WHITE else 0

            one = sq + direction
            if 0 <= one < 64 and board[one] == 0:
                if (one >> 3) == last_rank:
                    for promo in PROMOTION_PIECES:
                        moves.append((sq, one, promo))
                elif not captures_only:
                    moves.append((sq, one, 0))
                    if r == start_rank:
                        two = sq + 2 * direction
                        if 0 <= two < 64 and board[two] == 0:
                            moves.append((sq, two, 0))

            for df in (-1, 1):
                nf = f + df
                if 0 <= nf < 8:
                    to = sq + direction + df
                    if 0 <= to < 64:
                        target = board[to]
                        if target * color < 0 and abs(target) != KING:
                            if (to >> 3) == last_rank:
                                for promo in PROMOTION_PIECES:
                                    moves.append((sq, to, promo))
                            else:
                                moves.append((sq, to, 0))

        elif t == KNIGHT:
            for to in KNIGHT_MOVES[sq]:
                target = board[to]
                if target == 0:
                    if not captures_only:
                        moves.append((sq, to, 0))
                elif target * color < 0 and abs(target) != KING:
                    moves.append((sq, to, 0))

        elif t == BISHOP or t == ROOK or t == QUEEN:
            if t == BISHOP:
                ray_tables = (BISHOP_RAYS[sq],)
            elif t == ROOK:
                ray_tables = (ROOK_RAYS[sq],)
            else:
                ray_tables = (BISHOP_RAYS[sq], ROOK_RAYS[sq])

            for rays in ray_tables:
                for ray in rays:
                    for to in ray:
                        target = board[to]
                        if target == 0:
                            if not captures_only:
                                moves.append((sq, to, 0))
                        else:
                            if target * color < 0 and abs(target) != KING:
                                moves.append((sq, to, 0))
                            break

        elif t == KING:
            for to in KING_MOVES[sq]:
                target = board[to]
                if target == 0:
                    if not captures_only:
                        moves.append((sq, to, 0))
                elif target * color < 0 and abs(target) != KING:
                    moves.append((sq, to, 0))

    return moves


def _generate_legal(board, color, captures_only=False, king_sq=None):
    pseudo = _generate_pseudo(board, color, captures_only)
    if not pseudo:
        return []

    if king_sq is None:
        king_sq = _find_king(board, color)

    if king_sq == -1:
        return pseudo

    legal = []
    enemy = -color
    own_king = color * KING

    for move in pseudo:
        fr, to, _ = move
        piece = board[fr]
        new_king_sq = to if piece == own_king else king_sq
        moved, captured = _make_move(board, move)
        try:
            if not _is_attacked(board, new_king_sq, enemy):
                legal.append(move)
        finally:
            _unmake_move(board, move, moved, captured)

    return legal


def _plausible_castles(board, color):
    moves = []
    enemy = -color

    if color == WHITE:
        ksq = SQ_INDEX["e1"]
        if board[ksq] != WHITE * KING or _is_attacked(board, ksq, enemy):
            return moves
        if (
            board[SQ_INDEX["h1"]] == WHITE * ROOK
            and board[SQ_INDEX["f1"]] == 0
            and board[SQ_INDEX["g1"]] == 0
            and not _is_attacked(board, SQ_INDEX["f1"], enemy)
            and not _is_attacked(board, SQ_INDEX["g1"], enemy)
        ):
            moves.append((SQ_INDEX["e1"], SQ_INDEX["g1"], 0))
        if (
            board[SQ_INDEX["a1"]] == WHITE * ROOK
            and board[SQ_INDEX["b1"]] == 0
            and board[SQ_INDEX["c1"]] == 0
            and board[SQ_INDEX["d1"]] == 0
            and not _is_attacked(board, SQ_INDEX["d1"], enemy)
            and not _is_attacked(board, SQ_INDEX["c1"], enemy)
        ):
            moves.append((SQ_INDEX["e1"], SQ_INDEX["c1"], 0))
    else:
        ksq = SQ_INDEX["e8"]
        if board[ksq] != BLACK * KING or _is_attacked(board, ksq, enemy):
            return moves
        if (
            board[SQ_INDEX["h8"]] == BLACK * ROOK
            and board[SQ_INDEX["f8"]] == 0
            and board[SQ_INDEX["g8"]] == 0
            and not _is_attacked(board, SQ_INDEX["f8"], enemy)
            and not _is_attacked(board, SQ_INDEX["g8"], enemy)
        ):
            moves.append((SQ_INDEX["e8"], SQ_INDEX["g8"], 0))
        if (
            board[SQ_INDEX["a8"]] == BLACK * ROOK
            and board[SQ_INDEX["b8"]] == 0
            and board[SQ_INDEX["c8"]] == 0
            and board[SQ_INDEX["d8"]] == 0
            and not _is_attacked(board, SQ_INDEX["d8"], enemy)
            and not _is_attacked(board, SQ_INDEX["c8"], enemy)
        ):
            moves.append((SQ_INDEX["e8"], SQ_INDEX["c8"], 0))

    return moves


def _evaluate(board, color):
    mid = 0
    end = 0
    phase = 0

    pawns = {WHITE: [[] for _ in range(8)], BLACK: [[] for _ in range(8)]}
    rooks = {WHITE: [], BLACK: []}
    bishops = {WHITE: 0, BLACK: 0}
    kings = {WHITE: -1, BLACK: -1}

    for sq, piece in enumerate(board):
        if piece == 0:
            continue

        side = WHITE if piece > 0 else BLACK
        sign = 1 if side == WHITE else -1
        t = abs(piece)
        psq = sq if side == WHITE else MIRROR[sq]

        mid += sign * (PIECE_VALUE[t] + PST_MID[t][psq])
        end += sign * (PIECE_VALUE[t] + PST_END[t][psq])
        phase += PHASE_WEIGHT[t]

        if t == PAWN:
            pawns[side][sq & 7].append(sq >> 3)
        elif t == ROOK:
            rooks[side].append(sq)
        elif t == BISHOP:
            bishops[side] += 1
        elif t == KING:
            kings[side] = sq

    if phase > 24:
        phase = 24

    score = (mid * phase + end * (24 - phase)) // 24
    end_weight = 24 - phase

    passed_mid = [0, 2, 8, 16, 30, 55, 90, 0]
    passed_end = [0, 8, 18, 38, 70, 120, 190, 0]

    for side in (WHITE, BLACK):
        sign = 1 if side == WHITE else -1
        own = pawns[side]
        enemy = pawns[-side]

        if bishops[side] >= 2:
            score += sign * 28

        for f in range(8):
            ranks = own[f]
            if len(ranks) > 1:
                score -= sign * (14 * (len(ranks) - 1))

            for r in ranks:
                rel = r if side == WHITE else 7 - r

                isolated = (f == 0 or not own[f - 1]) and (f == 7 or not own[f + 1])
                if isolated:
                    score -= sign * 10

                connected = False
                for af in (f - 1, f + 1):
                    if 0 <= af < 8:
                        for ar in own[af]:
                            if abs(ar - r) <= 1:
                                connected = True
                                break
                    if connected:
                        break
                if connected:
                    score += sign * (4 + 2 * rel)

                passed = True
                for ef in range(max(0, f - 1), min(7, f + 1) + 1):
                    for er in enemy[ef]:
                        if (side == WHITE and er > r) or (side == BLACK and er < r):
                            passed = False
                            break
                    if not passed:
                        break

                if passed:
                    bonus = (passed_mid[rel] * phase + passed_end[rel] * end_weight) // 24
                    enemy_king = kings[-side]
                    own_king = kings[side]
                    promo_rank = 7 if side == WHITE else 0
                    if enemy_king != -1 and own_king != -1 and end_weight > 8:
                        ed = max(abs((enemy_king & 7) - f), abs((enemy_king >> 3) - promo_rank))
                        od = max(abs((own_king & 7) - f), abs((own_king >> 3) - r))
                        bonus += (ed - od) * 2
                    score += sign * bonus

        for sq in rooks[side]:
            f = sq & 7
            r = sq >> 3
            rel = r if side == WHITE else 7 - r
            if not own[f]:
                score += sign * (18 if not enemy[f] else 10)
            if rel == 6:
                score += sign * 18

        king_sq = kings[side]
        if king_sq != -1 and phase >= 10:
            kf = king_sq & 7
            kr = king_sq >> 3
            direction = 1 if side == WHITE else -1
            shield = 0
            for df in (-1, 0, 1):
                ff = kf + df
                if 0 <= ff < 8:
                    r1 = kr + direction
                    r2 = kr + 2 * direction
                    if 0 <= r1 < 8 and r1 in own[ff]:
                        shield += 8
                    elif 0 <= r2 < 8 and r2 in own[ff]:
                        shield += 4
                    else:
                        shield -= 6
            score += sign * ((shield * phase) // 24)

    return score * color + 8


def _move_order_score(board, move, tt_move, ply):
    if tt_move is not None and move == tt_move:
        return 10_000_000

    fr, to, promo = move
    piece = board[fr]
    captured = board[to]
    t = abs(piece)
    score = 0

    if captured:
        score += 1_000_000 + 20 * PIECE_VALUE[abs(captured)] - PIECE_VALUE[t]

    if promo:
        score += 900_000 + PIECE_VALUE[promo]

    if captured == 0 and promo == 0:
        if ply < len(KILLERS):
            if KILLERS[ply][0] == move:
                score += 700_000
            elif KILLERS[ply][1] == move:
                score += 600_000
        score += HISTORY.get((piece, to), 0)

    score += CENTER_SCORE[to]

    if t == PAWN:
        rel_to = (to >> 3) if piece > 0 else 7 - (to >> 3)
        score += rel_to * 3
    elif t in (KNIGHT, BISHOP):
        score += CENTER_SCORE[to] * 2

    return score


def _order_moves(board, moves, tt_move=None, ply=0):
    moves.sort(key=lambda m: _move_order_score(board, m, tt_move, ply), reverse=True)


def _record_cutoff(move, piece, depth, ply):
    if ply < len(KILLERS):
        if KILLERS[ply][0] != move:
            KILLERS[ply][1] = KILLERS[ply][0]
            KILLERS[ply][0] = move

    key = (piece, move[1])
    HISTORY[key] = min(1_000_000, HISTORY.get(key, 0) + depth * depth + 1)


def _time_check():
    global NODES
    NODES += 1
    if (NODES & 511) == 0 and time.perf_counter() > DEADLINE:
        raise SearchTimeout


def _quiescence(board, color, alpha, beta, ply, board_hash):
    _time_check()

    if ply >= 64:
        return _evaluate(board, color)

    king_sq = _find_king(board, color)
    in_check = king_sq != -1 and _is_attacked(board, king_sq, -color)

    if in_check:
        moves = _generate_legal(board, color, False, king_sq)
        if not moves:
            return -MATE + ply
        _order_moves(board, moves, None, ply)
    else:
        stand = _evaluate(board, color)
        if stand >= beta:
            return stand
        if stand > alpha:
            alpha = stand
        if ply >= 28:
            return alpha

        moves = _generate_legal(board, color, True, king_sq)
        if not moves:
            return alpha
        _order_moves(board, moves, None, ply)

    for move in moves:
        fr, to, _ = move
        piece = board[fr]
        captured = board[to]
        new_hash = _hash_after(board_hash, move, piece, captured)

        moved, cap = _make_move(board, move)
        try:
            score = -_quiescence(board, -color, -beta, -alpha, ply + 1, new_hash)
        finally:
            _unmake_move(board, move, moved, cap)

        if score >= beta:
            return score
        if score > alpha:
            alpha = score

    return alpha


def _negamax(board, color, depth, alpha, beta, ply, board_hash):
    _time_check()

    if ply >= 96:
        return _evaluate(board, color)

    king_sq = _find_king(board, color)
    in_check = king_sq != -1 and _is_attacked(board, king_sq, -color)

    if in_check:
        depth += 1

    if depth <= 0:
        return _quiescence(board, color, alpha, beta, ply, board_hash)

    alpha = max(alpha, -MATE + ply)
    beta = min(beta, MATE - ply - 1)
    if alpha >= beta:
        return alpha

    node_key = board_hash ^ (SIDE_HASH if color == BLACK else 0)
    alpha_orig = alpha
    tt_move = None

    entry = TT.get(node_key)
    if entry is not None:
        e_depth, e_value, e_flag, e_move = entry
        tt_move = e_move
        if e_depth >= depth:
            if e_flag == 0:
                return e_value
            if e_flag == 1:
                if e_value > alpha:
                    alpha = e_value
            elif e_flag == 2:
                if e_value < beta:
                    beta = e_value
            if alpha >= beta:
                return e_value

    moves = _generate_legal(board, color, False, king_sq)
    if not moves:
        return -MATE + ply if in_check else 0

    _order_moves(board, moves, tt_move, ply)

    best_score = -INF
    best_move = None
    searched = 0

    for move in moves:
        fr, to, promo = move
        piece = board[fr]
        captured = board[to]
        new_hash = _hash_after(board_hash, move, piece, captured)

        moved, cap = _make_move(board, move)
        try:
            new_depth = depth - 1

            if searched == 0:
                score = -_negamax(board, -color, new_depth, -beta, -alpha, ply + 1, new_hash)
            else:
                reduction = 0
                if depth >= 3 and searched >= 4 and not in_check and captured == 0 and promo == 0:
                    reduction = 1
                    if depth >= 5 and searched >= 12:
                        reduction = 2

                if reduction:
                    score = -_negamax(
                        board,
                        -color,
                        new_depth - reduction,
                        -alpha - 1,
                        -alpha,
                        ply + 1,
                        new_hash,
                    )
                    if score > alpha:
                        score = -_negamax(
                            board,
                            -color,
                            new_depth,
                            -alpha - 1,
                            -alpha,
                            ply + 1,
                            new_hash,
                        )
                        if alpha < score < beta:
                            score = -_negamax(
                                board,
                                -color,
                                new_depth,
                                -beta,
                                -alpha,
                                ply + 1,
                                new_hash,
                            )
                else:
                    score = -_negamax(
                        board,
                        -color,
                        new_depth,
                        -alpha - 1,
                        -alpha,
                        ply + 1,
                        new_hash,
                    )
                    if alpha < score < beta:
                        score = -_negamax(
                            board,
                            -color,
                            new_depth,
                            -beta,
                            -alpha,
                            ply + 1,
                            new_hash,
                        )
        finally:
            _unmake_move(board, move, moved, cap)

        searched += 1

        if score > best_score:
            best_score = score
            best_move = move

        if score > alpha:
            alpha = score
            if alpha >= beta:
                if captured == 0 and promo == 0:
                    _record_cutoff(move, piece, depth, ply)
                break

    flag = 0
    if best_score <= alpha_orig:
        flag = 2
    elif best_score >= beta:
        flag = 1

    if len(TT) < TT_LIMIT:
        TT[node_key] = (depth, best_score, flag, best_move)

    return best_score


def _search_root(board, color, depth, board_hash, legal_moves):
    alpha = -INF
    beta = INF

    root_key = board_hash ^ (SIDE_HASH if color == BLACK else 0)
    entry = TT.get(root_key)
    tt_move = entry[3] if entry is not None else None

    moves = list(legal_moves)
    _order_moves(board, moves, tt_move, 0)

    best_score = -INF
    best_move = moves[0]
    searched = 0

    for move in moves:
        if time.perf_counter() > DEADLINE:
            raise SearchTimeout

        fr, to, _ = move
        piece = board[fr]
        captured = board[to]
        new_hash = _hash_after(board_hash, move, piece, captured)

        moved, cap = _make_move(board, move)
        try:
            if searched == 0:
                score = -_negamax(board, -color, depth - 1, -beta, -alpha, 1, new_hash)
            else:
                score = -_negamax(board, -color, depth - 1, -alpha - 1, -alpha, 1, new_hash)
                if alpha < score < beta:
                    score = -_negamax(board, -color, depth - 1, -beta, -alpha, 1, new_hash)
        finally:
            _unmake_move(board, move, moved, cap)

        searched += 1

        if score > best_score:
            best_score = score
            best_move = move

        if score > alpha:
            alpha = score

    if len(TT) < TT_LIMIT:
        TT[root_key] = (depth, best_score, 0, best_move)

    return best_score, best_move


def _match_start_changes(board, changes):
    for i, start_piece in enumerate(START_TUPLE):
        if board[i] != changes.get(i, start_piece):
            return False
    return True


def _opening_move(board, color, legal_moves):
    legal = {_move_to_uci(m): m for m in legal_moves}

    def first(candidates):
        for u in candidates:
            m = legal.get(u)
            if m is not None:
                return m
        return None

    bt = tuple(board)
    if bt == START_TUPLE:
        if color == WHITE:
            return first(("e2e4", "d2d4", "g1f3", "c2c4"))
        return first(("e7e5", "d7d5", "g8f6", "c7c5"))

    WP = WHITE * PAWN
    WN = WHITE * KNIGHT
    BP = BLACK * PAWN
    BN = BLACK * KNIGHT

    if color == BLACK:
        if _match_start_changes(board, {SQ_INDEX["e2"]: 0, SQ_INDEX["e4"]: WP}):
            return first(("c7c5", "e7e5", "e7e6", "c7c6"))
        if _match_start_changes(board, {SQ_INDEX["d2"]: 0, SQ_INDEX["d4"]: WP}):
            return first(("g8f6", "d7d5", "e7e6"))
        if _match_start_changes(board, {SQ_INDEX["c2"]: 0, SQ_INDEX["c4"]: WP}):
            return first(("g8f6", "e7e5", "c7c5"))
        if _match_start_changes(board, {SQ_INDEX["g1"]: 0, SQ_INDEX["f3"]: WN}):
            return first(("d7d5", "g8f6", "c7c5"))
    else:
        if _match_start_changes(
            board,
            {SQ_INDEX["e2"]: 0, SQ_INDEX["e4"]: WP, SQ_INDEX["e7"]: 0, SQ_INDEX["e5"]: BP},
        ):
            return first(("g1f3", "f1c4", "d2d4"))
        if _match_start_changes(
            board,
            {SQ_INDEX["e2"]: 0, SQ_INDEX["e4"]: WP, SQ_INDEX["c7"]: 0, SQ_INDEX["c5"]: BP},
        ):
            return first(("g1f3", "d2d4", "c2c3"))
        if _match_start_changes(
            board,
            {SQ_INDEX["d2"]: 0, SQ_INDEX["d4"]: WP, SQ_INDEX["d7"]: 0, SQ_INDEX["d5"]: BP},
        ):
            return first(("c2c4", "g1f3", "c1f4"))
        if _match_start_changes(
            board,
            {SQ_INDEX["d2"]: 0, SQ_INDEX["d4"]: WP, SQ_INDEX["g8"]: 0, SQ_INDEX["f6"]: BN},
        ):
            return first(("c2c4", "g1f3", "c1f4"))

    return None


def _choose_static(board, color, legal_moves):
    best = legal_moves[0]
    best_score = -INF

    for i, move in enumerate(legal_moves):
        if (i & 7) == 0 and time.perf_counter() > DEADLINE:
            break

        fr, to, promo = move
        piece = board[fr]
        captured = board[to]

        moved, cap = _make_move(board, move)
        try:
            score = -_evaluate(board, -color)

            opp_king = _find_king(board, -color)
            if opp_king != -1 and _is_attacked(board, opp_king, color):
                score += 40
                if not _generate_legal(board, -color, False, opp_king):
                    score += MATE // 2
        finally:
            _unmake_move(board, move, moved, cap)

        if promo:
            score += PIECE_VALUE[promo] // 4
        if captured:
            score += PIECE_VALUE[abs(captured)] // 12

        if score > best_score:
            best_score = score
            best = move

    return best


def policy(pieces: dict[str, str], to_play: str) -> str:
    global TT, HISTORY, KILLERS, DEADLINE, NODES

    start_time = time.perf_counter()

    board = _parse_board(pieces)
    color = WHITE if str(to_play).lower().startswith("w") else BLACK

    legal_moves = _generate_legal(board, color, False)
    if not legal_moves:
        castles = _plausible_castles(board, color)
        if castles:
            return _move_to_uci(castles[0])
        pseudo = _generate_pseudo(board, color, False)
        if pseudo:
            return _move_to_uci(pseudo[0])
        return "a1a1"

    if len(legal_moves) == 1:
        return _move_to_uci(legal_moves[0])

    book = _opening_move(board, color, legal_moves)
    if book is not None:
        return _move_to_uci(book)

    move_count = len(legal_moves)
    if move_count <= 8:
        budget = 0.88
    elif move_count > 45:
        budget = 0.74
    elif move_count > 32:
        budget = 0.80
    else:
        budget = 0.84

    DEADLINE = start_time + budget

    best_move = _choose_static(board, color, legal_moves)

    TT = {}
    HISTORY = {}
    KILLERS = [[None, None] for _ in range(128)]
    NODES = 0

    board_hash = _hash_board(board)

    if move_count <= 5:
        max_depth = 9
    elif move_count <= 12:
        max_depth = 7
    elif move_count <= 25:
        max_depth = 6
    else:
        max_depth = 5

    try:
        for depth in range(1, max_depth + 1):
            if time.perf_counter() > DEADLINE:
                break

            score, move = _search_root(board, color, depth, board_hash, legal_moves)
            if move is not None:
                best_move = move

            if score >= MATE - 500 or score <= -MATE + 500:
                break

    except SearchTimeout:
        pass
    except Exception:
        pass

    return _move_to_uci(best_move)
