
import time

# Piece numbers
P, N, B, R, Q, K = 1, 2, 3, 4, 5, 6
WHITE, BLACK = 1, -1

VALUE = {
    P: 100,
    N: 320,
    B: 335,
    R: 505,
    Q: 920,
    K: 20000,
}

INF = 1_000_000
MATE = 900_000

KNIGHT_STEPS = (
    (-2, -1), (-2, 1), (-1, -2), (-1, 2),
    (1, -2), (1, 2), (2, -1), (2, 1),
)
KING_STEPS = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
)
BISHOP_DIRS = ((1, 1), (1, -1), (-1, 1), (-1, -1))
ROOK_DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))

PROMOTION_LETTER = {Q: "q", R: "r", B: "b", N: "n"}
LETTER_TO_PROMOTION = {"q": Q, "r": R, "b": B, "n": N}

# Search globals, reset on every policy call.
_deadline = 0.0
_nodes = 0
_tt = {}
_killers = [[None, None] for _ in range(64)]
_history = {}


class SearchTimeout(Exception):
    pass


def _piece_index(piece):
    if piece > 0:
        return piece - 1
    return 6 + (-piece - 1)


# Deterministic Zobrist keys.
_ZOBRIST = [[0] * 12 for _ in range(64)]
_x = 0x9E3779B97F4A7C15
for _sq in range(64):
    for _pi in range(12):
        _x ^= (_x << 13) & 0xFFFFFFFFFFFFFFFF
        _x ^= _x >> 7
        _x ^= (_x << 17) & 0xFFFFFFFFFFFFFFFF
        _x &= 0xFFFFFFFFFFFFFFFF
        _ZOBRIST[_sq][_pi] = _x
_x ^= (_x << 13) & 0xFFFFFFFFFFFFFFFF
_x ^= _x >> 7
_x ^= (_x << 17) & 0xFFFFFFFFFFFFFFFF
_SIDE_HASH = _x & 0xFFFFFFFFFFFFFFFF


def _initial_hash(board, side):
    h = 0
    for sq, piece in enumerate(board):
        if piece:
            h ^= _ZOBRIST[sq][_piece_index(piece)]
    if side == BLACK:
        h ^= _SIDE_HASH
    return h


def _child_hash(h, board, move):
    fr, to, promo = move[:3]
    piece = board[fr]
    captured = board[to]
    new_piece = piece
    if promo:
        new_piece = promo if piece > 0 else -promo

    nh = h ^ _SIDE_HASH
    nh ^= _ZOBRIST[fr][_piece_index(piece)]
    if captured:
        nh ^= _ZOBRIST[to][_piece_index(captured)]
    nh ^= _ZOBRIST[to][_piece_index(new_piece)]
    return nh


def _square_name(sq):
    return chr(97 + (sq & 7)) + str((sq >> 3) + 1)


def _move_to_uci(move):
    fr, to, promo = move[:3]
    result = _square_name(fr) + _square_name(to)
    if promo:
        result += PROMOTION_LETTER[promo]
    return result


def _parse_uci(text):
    fr = (ord(text[0]) - 97) + 8 * (ord(text[1]) - 49)
    to = (ord(text[2]) - 97) + 8 * (ord(text[3]) - 49)
    promo = LETTER_TO_PROMOTION.get(text[4], 0) if len(text) > 4 else 0
    return fr, to, promo


def _find_king(board, side):
    target = side * K
    for sq, piece in enumerate(board):
        if piece == target:
            return sq
    return -1


def _is_attacked(board, sq, by_side):
    if sq < 0:
        return True

    f = sq & 7
    r = sq >> 3

    # Pawn attacks
    origin_rank = r - 1 if by_side == WHITE else r + 1
    if 0 <= origin_rank < 8:
        if f > 0:
            origin = origin_rank * 8 + f - 1
            if board[origin] == by_side * P:
                return True
        if f < 7:
            origin = origin_rank * 8 + f + 1
            if board[origin] == by_side * P:
                return True

    # Knight attacks
    knight = by_side * N
    for df, dr in KNIGHT_STEPS:
        nf, nr = f + df, r + dr
        if 0 <= nf < 8 and 0 <= nr < 8:
            if board[nr * 8 + nf] == knight:
                return True

    # King attacks
    king = by_side * K
    for df, dr in KING_STEPS:
        nf, nr = f + df, r + dr
        if 0 <= nf < 8 and 0 <= nr < 8:
            if board[nr * 8 + nf] == king:
                return True

    # Bishop and queen attacks
    for df, dr in BISHOP_DIRS:
        nf, nr = f + df, r + dr
        while 0 <= nf < 8 and 0 <= nr < 8:
            piece = board[nr * 8 + nf]
            if piece:
                if piece == by_side * B or piece == by_side * Q:
                    return True
                break
            nf += df
            nr += dr

    # Rook and queen attacks
    for df, dr in ROOK_DIRS:
        nf, nr = f + df, r + dr
        while 0 <= nf < 8 and 0 <= nr < 8:
            piece = board[nr * 8 + nf]
            if piece:
                if piece == by_side * R or piece == by_side * Q:
                    return True
                break
            nf += df
            nr += dr

    return False


def _pseudo_moves(board, side, tactical=False):
    moves = []

    for fr, piece in enumerate(board):
        if piece * side <= 0:
            continue

        kind = abs(piece)
        f = fr & 7
        r = fr >> 3

        if kind == P:
            direction = 1 if side == WHITE else -1
            nr = r + direction

            if 0 <= nr < 8:
                # Quiet pawn moves and non-capture promotions.
                to = nr * 8 + f
                if board[to] == 0:
                    promotion_rank = (nr == 7 if side == WHITE else nr == 0)
                    if promotion_rank:
                        for promo in (Q, R, B, N):
                            moves.append((fr, to, promo))
                    elif not tactical:
                        moves.append((fr, to, 0))
                        start_rank = 1 if side == WHITE else 6
                        if r == start_rank:
                            nr2 = r + 2 * direction
                            to2 = nr2 * 8 + f
                            if board[to2] == 0:
                                moves.append((fr, to2, 0))

                # Pawn captures.
                for df in (-1, 1):
                    nf = f + df
                    if 0 <= nf < 8:
                        to = nr * 8 + nf
                        target = board[to]
                        if target * side < 0 and abs(target) != K:
                            promotion_rank = (
                                nr == 7 if side == WHITE else nr == 0
                            )
                            if promotion_rank:
                                for promo in (Q, R, B, N):
                                    moves.append((fr, to, promo))
                            else:
                                moves.append((fr, to, 0))

        elif kind == N:
            for df, dr in KNIGHT_STEPS:
                nf, nr = f + df, r + dr
                if 0 <= nf < 8 and 0 <= nr < 8:
                    to = nr * 8 + nf
                    target = board[to]
                    if target == 0:
                        if not tactical:
                            moves.append((fr, to, 0))
                    elif target * side < 0 and abs(target) != K:
                        moves.append((fr, to, 0))

        elif kind == K:
            for df, dr in KING_STEPS:
                nf, nr = f + df, r + dr
                if 0 <= nf < 8 and 0 <= nr < 8:
                    to = nr * 8 + nf
                    target = board[to]
                    if target == 0:
                        if not tactical:
                            moves.append((fr, to, 0))
                    elif target * side < 0 and abs(target) != K:
                        moves.append((fr, to, 0))

        else:
            directions = ()
            if kind == B:
                directions = BISHOP_DIRS
            elif kind == R:
                directions = ROOK_DIRS
            elif kind == Q:
                directions = BISHOP_DIRS + ROOK_DIRS

            for df, dr in directions:
                nf, nr = f + df, r + dr
                while 0 <= nf < 8 and 0 <= nr < 8:
                    to = nr * 8 + nf
                    target = board[to]
                    if target == 0:
                        if not tactical:
                            moves.append((fr, to, 0))
                    else:
                        if target * side < 0 and abs(target) != K:
                            moves.append((fr, to, 0))
                        break
                    nf += df
                    nr += dr

    return moves


def _make_move(board, move):
    fr, to, promo = move[:3]
    piece = board[fr]
    captured = board[to]
    board[fr] = 0
    if promo:
        board[to] = promo if piece > 0 else -promo
    else:
        board[to] = piece
    return piece, captured


def _unmake_move(board, move, piece, captured):
    fr, to = move[0], move[1]
    board[fr] = piece
    board[to] = captured


def _legal_moves(board, side, tactical=False):
    result = []

    for move in _pseudo_moves(board, side, tactical):
        piece, captured = _make_move(board, move)

        if abs(piece) == K:
            king_sq = move[1]
        else:
            king_sq = _find_king(board, side)

        legal = king_sq >= 0 and not _is_attacked(board, king_sq, -side)

        gives_check = False
        if legal:
            enemy_king = _find_king(board, -side)
            if enemy_king >= 0:
                gives_check = _is_attacked(board, enemy_king, side)

        _unmake_move(board, move, piece, captured)

        if legal:
            result.append((move[0], move[1], move[2], gives_check))

    return result


def _positional_value(kind, sq):
    f = sq & 7
    r = sq >> 3
    center_distance = abs(2 * f - 7) + abs(2 * r - 7)

    if kind == P:
        advance = (0, 0, 8, 17, 29, 46, 70, 0)[r]
        center = 7 if f in (3, 4) else (3 if f in (2, 5) else 0)
        return advance + center
    if kind == N:
        return 34 - 6 * center_distance
    if kind == B:
        return 22 - 2 * center_distance
    if kind == R:
        return (18 if r == 6 else 0) + (3 if f in (3, 4) else 0)
    if kind == Q:
        return 10 - center_distance
    return 0


def _evaluate(board):
    score = 0
    non_pawn_material = 0

    pawn_ranks = {
        WHITE: [[] for _ in range(8)],
        BLACK: [[] for _ in range(8)],
    }
    rooks = {WHITE: [], BLACK: []}
    bishops = {WHITE: 0, BLACK: 0}
    kings = {WHITE: -1, BLACK: -1}

    for sq, piece in enumerate(board):
        if not piece:
            continue

        side = WHITE if piece > 0 else BLACK
        kind = abs(piece)
        normalized_sq = sq if side == WHITE else ((7 - (sq >> 3)) * 8 + (sq & 7))

        if kind != K:
            contribution = VALUE[kind] + _positional_value(kind, normalized_sq)
            score += side * contribution

        if kind not in (P, K):
            non_pawn_material += VALUE[kind]

        if kind == P:
            pawn_ranks[side][sq & 7].append(sq >> 3)
        elif kind == R:
            rooks[side].append(sq)
        elif kind == B:
            bishops[side] += 1
        elif kind == K:
            kings[side] = sq

    # Bishop pair.
    if bishops[WHITE] >= 2:
        score += 28
    if bishops[BLACK] >= 2:
        score -= 28

    # Pawn structure and passed pawns.
    passed_bonus = (0, 5, 11, 21, 36, 58, 90, 0)

    for side in (WHITE, BLACK):
        sign = side
        own = pawn_ranks[side]
        enemy = pawn_ranks[-side]

        for f in range(8):
            count = len(own[f])
            if count > 1:
                score -= sign * 13 * (count - 1)

            if count and not (
                (f > 0 and own[f - 1]) or (f < 7 and own[f + 1])
            ):
                score -= sign * 9 * count

            for r in own[f]:
                passed = True
                for ef in range(max(0, f - 1), min(7, f + 1) + 1):
                    if side == WHITE:
                        if any(er > r for er in enemy[ef]):
                            passed = False
                            break
                    else:
                        if any(er < r for er in enemy[ef]):
                            passed = False
                            break

                if passed:
                    advancement = r if side == WHITE else 7 - r
                    score += sign * passed_bonus[advancement]

    # Open and semi-open files for rooks.
    for side in (WHITE, BLACK):
        sign = side
        own_pawns = pawn_ranks[side]
        enemy_pawns = pawn_ranks[-side]
        for sq in rooks[side]:
            f = sq & 7
            if not own_pawns[f]:
                score += sign * (15 if not enemy_pawns[f] else 8)

    # King positioning and pawn shields.
    endgame = non_pawn_material <= 2600
    for side in (WHITE, BLACK):
        sq = kings[side]
        if sq < 0:
            continue

        normalized_sq = sq if side == WHITE else ((7 - (sq >> 3)) * 8 + (sq & 7))
        f = normalized_sq & 7
        r = normalized_sq >> 3
        center_distance = abs(2 * f - 7) + abs(2 * r - 7)

        if endgame:
            king_bonus = 42 - 4 * center_distance
        else:
            king_bonus = 3 * center_distance
            if r == 0:
                king_bonus += 15
            if (f, r) in ((6, 0), (2, 0)):
                king_bonus += 28

            actual_f = sq & 7
            actual_r = sq >> 3
            front_r = actual_r + (1 if side == WHITE else -1)
            if 0 <= front_r < 8:
                shield = 0
                for sf in range(max(0, actual_f - 1), min(7, actual_f + 1) + 1):
                    if board[front_r * 8 + sf] == side * P:
                        shield += 10
                    else:
                        shield -= 4
                king_bonus += shield

        score += side * king_bonus

    return score


def _check_time():
    global _nodes
    _nodes += 1
    if (_nodes & 255) == 0 and time.perf_counter() >= _deadline:
        raise SearchTimeout


def _move_order_score(board, move, tt_move, ply):
    fr, to, promo, gives_check = move
    key = (fr, to, promo)

    if tt_move is not None and key == tt_move:
        return 2_000_000

    score = 0
    victim = board[to]
    attacker = board[fr]

    if victim:
        score += 100_000 + 12 * VALUE[abs(victim)] - VALUE[abs(attacker)]

    if promo:
        score += 80_000 + VALUE[promo]

    if gives_check:
        score += 5_000

    if ply < len(_killers):
        if key == _killers[ply][0]:
            score += 4_000
        elif key == _killers[ply][1]:
            score += 3_000

    score += _history.get((fr, to), 0)
    return score


def _order_moves(board, moves, tt_move=None, ply=0):
    moves.sort(
        key=lambda m: _move_order_score(board, m, tt_move, ply),
        reverse=True,
    )
    return moves


def _quiescence(board, side, alpha, beta, ply, qply, h):
    _check_time()

    king_sq = _find_king(board, side)
    in_check = king_sq >= 0 and _is_attacked(board, king_sq, -side)

    if qply >= 10 and not in_check:
        return side * _evaluate(board)
    if qply >= 14:
        return side * _evaluate(board)

    if in_check:
        moves = _legal_moves(board, side, tactical=False)
        if not moves:
            return -MATE + ply
        stand_pat = -INF
    else:
        stand_pat = side * _evaluate(board)
        if stand_pat >= beta:
            return stand_pat
        if stand_pat > alpha:
            alpha = stand_pat
        moves = _legal_moves(board, side, tactical=True)
        if not moves:
            return alpha

    _order_moves(board, moves, None, ply)

    for move in moves:
        if not in_check:
            victim = board[move[1]]
            gain = VALUE[abs(victim)] if victim else 0
            if move[2]:
                gain += VALUE[move[2]] - VALUE[P]
            if not move[3] and stand_pat + gain + 140 < alpha:
                continue

        nh = _child_hash(h, board, move)
        piece, captured = _make_move(board, move)
        value = -_quiescence(
            board, -side, -beta, -alpha, ply + 1, qply + 1, nh
        )
        _unmake_move(board, move, piece, captured)

        if value >= beta:
            return value
        if value > alpha:
            alpha = value

    return alpha


def _search(board, side, depth, alpha, beta, ply, h):
    _check_time()

    if depth <= 0:
        return _quiescence(board, side, alpha, beta, ply, 0, h)

    original_alpha = alpha
    original_beta = beta
    tt_move = None

    entry = _tt.get(h)
    if entry is not None:
        stored_depth, stored_value, flag, tt_move = entry
        if stored_depth >= depth:
            if flag == 0:
                return stored_value
            if flag == 1:
                alpha = max(alpha, stored_value)
            elif flag == 2:
                beta = min(beta, stored_value)
            if alpha >= beta:
                return stored_value

    king_sq = _find_king(board, side)
    in_check = king_sq >= 0 and _is_attacked(board, king_sq, -side)
    moves = _legal_moves(board, side, tactical=False)

    if not moves:
        if in_check:
            return -MATE + ply
        return 0

    _order_moves(board, moves, tt_move, ply)

    best_value = -INF
    best_move = None

    for move in moves:
        nh = _child_hash(h, board, move)
        piece, captured = _make_move(board, move)
        value = -_search(
            board, -side, depth - 1, -beta, -alpha, ply + 1, nh
        )
        _unmake_move(board, move, piece, captured)

        if value > best_value:
            best_value = value
            best_move = move[:3]

        if value > alpha:
            alpha = value

        if alpha >= beta:
            if captured == 0 and move[2] == 0 and ply < len(_killers):
                key = move[:3]
                if key != _killers[ply][0]:
                    _killers[ply][1] = _killers[ply][0]
                    _killers[ply][0] = key
                hist_key = (move[0], move[1])
                _history[hist_key] = _history.get(hist_key, 0) + depth * depth
            break

    if best_value <= original_alpha:
        flag = 2
    elif best_value >= original_beta:
        flag = 1
    else:
        flag = 0

    _tt[h] = (depth, best_value, flag, best_move)
    return best_value


def _starting_board():
    board = [0] * 64
    back = (R, N, B, Q, K, B, N, R)
    for f, piece in enumerate(back):
        board[f] = piece
        board[8 + f] = P
        board[48 + f] = -P
        board[56 + f] = -piece
    return board


def _apply_text_move(board, text):
    fr, to, promo = _parse_uci(text)
    piece = board[fr]
    board[fr] = 0
    if promo:
        board[to] = promo if piece > 0 else -promo
    else:
        board[to] = piece


_OPENING_BOOK = {}


def _add_book_line(sequence, reply):
    board = _starting_board()
    for text in sequence:
        _apply_text_move(board, text)
    side = WHITE if len(sequence) % 2 == 0 else BLACK
    _OPENING_BOOK[(tuple(board), side)] = reply


_add_book_line((), "e2e4")
_add_book_line(("e2e4",), "e7e5")
_add_book_line(("d2d4",), "g8f6")
_add_book_line(("c2c4",), "e7e5")
_add_book_line(("g1f3",), "d7d5")

_add_book_line(("e2e4", "e7e5"), "g1f3")
_add_book_line(("e2e4", "c7c5"), "g1f3")
_add_book_line(("e2e4", "e7e6"), "d2d4")
_add_book_line(("e2e4", "c7c6"), "d2d4")
_add_book_line(("e2e4", "d7d5"), "e4d5")
_add_book_line(("d2d4", "g8f6"), "c2c4")
_add_book_line(("d2d4", "d7d5"), "c2c4")
_add_book_line(("c2c4", "e7e5"), "b1c3")

_add_book_line(("e2e4", "e7e5", "g1f3"), "b8c6")
_add_book_line(("e2e4", "c7c5", "g1f3"), "d7d6")
_add_book_line(("e2e4", "e7e6", "d2d4"), "d7d5")
_add_book_line(("e2e4", "c7c6", "d2d4"), "d7d5")
_add_book_line(("e2e4", "d7d5", "e4d5"), "d8d5")
_add_book_line(("d2d4", "g8f6", "c2c4"), "e7e6")

_add_book_line(
    ("e2e4", "e7e5", "g1f3", "b8c6"),
    "f1c4",
)
_add_book_line(
    ("e2e4", "e7e5", "g1f3", "b8c6", "f1c4"),
    "f8c5",
)
_add_book_line(
    ("e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "f8c5"),
    "d2d3",
)
_add_book_line(
    (
        "e2e4", "e7e5", "g1f3", "b8c6",
        "f1c4", "f8c5", "d2d3",
    ),
    "g8f6",
)
_add_book_line(
    (
        "e2e4", "e7e5", "g1f3", "b8c6",
        "f1c4", "f8c5", "d2d3", "g8f6",
    ),
    "b1c3",
)


def policy(pieces: dict[str, str], to_play: str) -> str:
    global _deadline, _nodes, _tt, _killers, _history

    board = [0] * 64
    type_map = {
        "P": P,
        "N": N,
        "B": B,
        "R": R,
        "Q": Q,
        "K": K,
    }

    for square, code in pieces.items():
        if len(square) != 2 or len(code) != 2:
            continue
        f = ord(square[0]) - 97
        r = ord(square[1]) - 49
        if not (0 <= f < 8 and 0 <= r < 8):
            continue
        kind = type_map.get(code[1])
        if kind is None:
            continue
        side = WHITE if code[0] == "w" else BLACK
        board[r * 8 + f] = side * kind

    side = WHITE if to_play == "white" else BLACK

    legal = _legal_moves(board, side, tactical=False)
    if not legal:
        # The API is expected to call the policy only in non-terminal positions.
        return "a1a1"

    legal_by_key = {move[:3]: move for move in legal}

    # Exact-position opening book, always checked against generated legality.
    book_text = _OPENING_BOOK.get((tuple(board), side))
    if book_text is not None:
        book_move = _parse_uci(book_text)
        if book_move in legal_by_key:
            return book_text

    _deadline = time.perf_counter() + 0.90
    _nodes = 0
    _tt = {}
    _killers = [[None, None] for _ in range(64)]
    _history = {}

    root_hash = _initial_hash(board, side)
    _order_moves(board, legal, None, 0)

    # A legal fallback is established before any timed search.
    completed_best = legal[0]
    previous_best = None

    piece_count = sum(1 for piece in board if piece)
    max_depth = 8 if piece_count <= 10 else (7 if piece_count <= 16 else 6)

    try:
        for depth in range(1, max_depth + 1):
            if time.perf_counter() >= _deadline:
                break

            root_moves = list(legal)
            _order_moves(board, root_moves, previous_best, 0)

            iteration_best = root_moves[0]
            iteration_score = -INF
            alpha = -INF

            for move in root_moves:
                if time.perf_counter() >= _deadline:
                    raise SearchTimeout

                nh = _child_hash(root_hash, board, move)
                piece, captured = _make_move(board, move)
                score = -_search(
                    board,
                    -side,
                    depth - 1,
                    -INF,
                    -alpha,
                    1,
                    nh,
                )
                _unmake_move(board, move, piece, captured)

                if score > iteration_score:
                    iteration_score = score
                    iteration_best = move

                if score > alpha:
                    alpha = score

            completed_best = iteration_best
            previous_best = iteration_best[:3]

            if iteration_score >= MATE - 100:
                break

    except SearchTimeout:
        pass

    return _move_to_uci(completed_best)
