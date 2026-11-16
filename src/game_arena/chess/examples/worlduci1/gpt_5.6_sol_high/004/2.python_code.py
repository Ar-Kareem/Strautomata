
import time

# Piece numbers:
# Pawn=1, Knight=2, Bishop=3, Rook=4, Queen=5, King=6
VALUES = (0, 100, 320, 335, 500, 900, 20000)
MATE = 1000000
INF = 2000000

KNIGHT_STEPS = (
    (-2, -1), (-2, 1), (-1, -2), (-1, 2),
    (1, -2), (1, 2), (2, -1), (2, 1)
)
BISHOP_DIRS = ((1, 1), (1, -1), (-1, 1), (-1, -1))
ROOK_DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
KING_DIRS = BISHOP_DIRS + ROOK_DIRS
PROMOTIONS = (5, 4, 3, 2)

CHAR_TO_PIECE = {
    "P": 1,
    "N": 2,
    "B": 3,
    "R": 4,
    "Q": 5,
    "K": 6,
}
PROMOTION_CHAR = {
    5: "q",
    4: "r",
    3: "b",
    2: "n",
}

# Positional tables are defined from White's point of view.
PST = [[0] * 64 for _ in range(7)]
for sq in range(64):
    f = sq & 7
    r = sq >> 3
    center_distance = abs(2 * f - 7) + abs(2 * r - 7)

    PST[1][sq] = r * 10 + max(-2, 6 - abs(2 * f - 7))
    PST[2][sq] = 28 - 4 * center_distance
    PST[3][sq] = 18 - 2 * center_distance
    PST[4][sq] = 2 * r + (10 if r == 6 else 0)
    PST[5][sq] = 8 - center_distance
    PST[6][sq] = 0


# Deterministic Zobrist keys.
def _make_zobrist():
    x = 0x9E3779B97F4A7C15
    result = [[0] * 64 for _ in range(12)]
    mask = (1 << 64) - 1

    for p in range(12):
        for sq in range(64):
            x ^= (x << 13) & mask
            x ^= x >> 7
            x ^= (x << 17) & mask
            x &= mask
            result[p][sq] = x

    x ^= (x << 13) & mask
    x ^= x >> 7
    x ^= (x << 17) & mask
    return result, x & mask


ZOBRIST, SIDE_KEY = _make_zobrist()

_deadline = 0.0
_nodes = 0
_tt = {}
_history = {}
_killers = [[None, None] for _ in range(64)]


class _SearchTimeout(Exception):
    pass


def _piece_index(piece):
    if piece > 0:
        return piece - 1
    return 6 + (-piece - 1)


def _board_hash(board):
    h = 0
    for sq, piece in enumerate(board):
        if piece:
            h ^= ZOBRIST[_piece_index(piece)][sq]
    return h


def _find_king(board, side):
    king = 6 * side
    for sq in range(64):
        if board[sq] == king:
            return sq
    return -1


def _attacked(board, square, by_side):
    if square < 0:
        return True

    f = square & 7
    r = square >> 3

    # Pawn attacks.
    if by_side == 1:
        if r > 0:
            if f > 0 and board[square - 9] == 1:
                return True
            if f < 7 and board[square - 7] == 1:
                return True
    else:
        if r < 7:
            if f > 0 and board[square + 7] == -1:
                return True
            if f < 7 and board[square + 9] == -1:
                return True

    # Knight attacks.
    enemy_knight = 2 * by_side
    for df, dr in KNIGHT_STEPS:
        nf = f + df
        nr = r + dr
        if 0 <= nf < 8 and 0 <= nr < 8:
            if board[nr * 8 + nf] == enemy_knight:
                return True

    # Bishop and queen attacks.
    for df, dr in BISHOP_DIRS:
        nf = f + df
        nr = r + dr
        while 0 <= nf < 8 and 0 <= nr < 8:
            piece = board[nr * 8 + nf]
            if piece:
                if piece * by_side > 0 and abs(piece) in (3, 5):
                    return True
                break
            nf += df
            nr += dr

    # Rook and queen attacks.
    for df, dr in ROOK_DIRS:
        nf = f + df
        nr = r + dr
        while 0 <= nf < 8 and 0 <= nr < 8:
            piece = board[nr * 8 + nf]
            if piece:
                if piece * by_side > 0 and abs(piece) in (4, 5):
                    return True
                break
            nf += df
            nr += dr

    # King attacks.
    enemy_king = 6 * by_side
    for df, dr in KING_DIRS:
        nf = f + df
        nr = r + dr
        if 0 <= nf < 8 and 0 <= nr < 8:
            if board[nr * 8 + nf] == enemy_king:
                return True

    return False


def _in_check(board, side):
    return _attacked(board, _find_king(board, side), -side)


def _pseudo_moves(board, side):
    moves = []

    for source in range(64):
        piece = board[source]
        if piece * side <= 0:
            continue

        kind = abs(piece)
        f = source & 7
        r = source >> 3

        if kind == 1:
            if side == 1:
                one = source + 8
                if r < 7 and board[one] == 0:
                    if r == 6:
                        for promotion in PROMOTIONS:
                            moves.append((source, one, promotion))
                    else:
                        moves.append((source, one, 0))
                        if r == 1:
                            two = source + 16
                            if board[two] == 0:
                                moves.append((source, two, 0))

                if r < 7:
                    if f > 0:
                        target = source + 7
                        captured = board[target]
                        if captured < 0 and abs(captured) != 6:
                            if r == 6:
                                for promotion in PROMOTIONS:
                                    moves.append((source, target, promotion))
                            else:
                                moves.append((source, target, 0))
                    if f < 7:
                        target = source + 9
                        captured = board[target]
                        if captured < 0 and abs(captured) != 6:
                            if r == 6:
                                for promotion in PROMOTIONS:
                                    moves.append((source, target, promotion))
                            else:
                                moves.append((source, target, 0))
            else:
                one = source - 8
                if r > 0 and board[one] == 0:
                    if r == 1:
                        for promotion in PROMOTIONS:
                            moves.append((source, one, promotion))
                    else:
                        moves.append((source, one, 0))
                        if r == 6:
                            two = source - 16
                            if board[two] == 0:
                                moves.append((source, two, 0))

                if r > 0:
                    if f > 0:
                        target = source - 9
                        captured = board[target]
                        if captured > 0 and abs(captured) != 6:
                            if r == 1:
                                for promotion in PROMOTIONS:
                                    moves.append((source, target, promotion))
                            else:
                                moves.append((source, target, 0))
                    if f < 7:
                        target = source - 7
                        captured = board[target]
                        if captured > 0 and abs(captured) != 6:
                            if r == 1:
                                for promotion in PROMOTIONS:
                                    moves.append((source, target, promotion))
                            else:
                                moves.append((source, target, 0))

        elif kind == 2:
            for df, dr in KNIGHT_STEPS:
                nf = f + df
                nr = r + dr
                if 0 <= nf < 8 and 0 <= nr < 8:
                    target = nr * 8 + nf
                    captured = board[target]
                    if captured * side <= 0 and abs(captured) != 6:
                        moves.append((source, target, 0))

        elif kind in (3, 4, 5):
            if kind == 3:
                directions = BISHOP_DIRS
            elif kind == 4:
                directions = ROOK_DIRS
            else:
                directions = KING_DIRS

            for df, dr in directions:
                nf = f + df
                nr = r + dr
                while 0 <= nf < 8 and 0 <= nr < 8:
                    target = nr * 8 + nf
                    captured = board[target]
                    if captured == 0:
                        moves.append((source, target, 0))
                    else:
                        if captured * side < 0 and abs(captured) != 6:
                            moves.append((source, target, 0))
                        break
                    nf += df
                    nr += dr

        elif kind == 6:
            for df, dr in KING_DIRS:
                nf = f + df
                nr = r + dr
                if 0 <= nf < 8 and 0 <= nr < 8:
                    target = nr * 8 + nf
                    captured = board[target]
                    if captured * side <= 0 and abs(captured) != 6:
                        moves.append((source, target, 0))

    return moves


def _legal_moves(board, side):
    king_square = _find_king(board, side)
    if king_square < 0:
        return []

    legal = []
    for move in _pseudo_moves(board, side):
        source, target, promotion = move
        moving = board[source]
        captured = board[target]

        board[source] = 0
        board[target] = side * promotion if promotion else moving

        new_king_square = target if abs(moving) == 6 else king_square
        if not _attacked(board, new_king_square, -side):
            legal.append(move)

        board[source] = moving
        board[target] = captured

    return legal


def _do_move(board, move, side, position_hash):
    source, target, promotion = move
    moving = board[source]
    captured = board[target]
    placed = side * promotion if promotion else moving

    new_hash = position_hash
    new_hash ^= ZOBRIST[_piece_index(moving)][source]
    if captured:
        new_hash ^= ZOBRIST[_piece_index(captured)][target]
    new_hash ^= ZOBRIST[_piece_index(placed)][target]

    board[source] = 0
    board[target] = placed
    return moving, captured, new_hash


def _undo_move(board, move, moving, captured):
    source, target, _ = move
    board[source] = moving
    board[target] = captured


def _evaluate(board):
    score = 0
    phase = 0
    white_bishops = 0
    black_bishops = 0
    white_king = -1
    black_king = -1

    for sq, piece in enumerate(board):
        if piece == 0:
            continue

        side = 1 if piece > 0 else -1
        kind = abs(piece)

        if side == 1:
            positional_sq = sq
        else:
            positional_sq = (7 - (sq >> 3)) * 8 + (sq & 7)

        score += side * (VALUES[kind] + PST[kind][positional_sq])

        if kind in (2, 3, 4, 5):
            phase += VALUES[kind]
        if kind == 3:
            if side == 1:
                white_bishops += 1
            else:
                black_bishops += 1
        elif kind == 6:
            if side == 1:
                white_king = sq
            else:
                black_king = sq

    if white_bishops >= 2:
        score += 24
    if black_bishops >= 2:
        score -= 24

    endgame = phase <= 1500

    for side, king_sq in ((1, white_king), (-1, black_king)):
        if king_sq < 0:
            continue

        f = king_sq & 7
        r = king_sq >> 3
        relative_rank = r if side == 1 else 7 - r
        center_distance = abs(2 * f - 7) + abs(2 * r - 7)

        if endgame:
            king_score = 40 - 3 * center_distance
        else:
            king_score = -10 * relative_rank
            if f <= 2 or f >= 5:
                king_score += 18
            else:
                king_score -= 10

            forward_rank = r + side
            if 0 <= forward_rank < 8:
                shield = 0
                for shield_file in (f - 1, f, f + 1):
                    if 0 <= shield_file < 8:
                        if board[forward_rank * 8 + shield_file] == side:
                            shield += 1
                king_score += 9 * shield

        score += side * king_score

    return score


def _check_time():
    global _nodes
    _nodes += 1
    if (_nodes & 511) == 0 and time.perf_counter() >= _deadline:
        raise _SearchTimeout


def _move_order_score(board, move, side, tt_move, ply):
    source, target, promotion = move

    if move == tt_move:
        return 10000000

    moving_kind = abs(board[source])
    captured_kind = abs(board[target])
    score = 0

    if captured_kind:
        score += 1000000 + 16 * VALUES[captured_kind] - VALUES[moving_kind]

    if promotion:
        score += 800000 + VALUES[promotion]

    if not captured_kind and not promotion and ply < len(_killers):
        if move == _killers[ply][0]:
            score += 700000
        elif move == _killers[ply][1]:
            score += 650000

    score += _history.get((side, source, target, promotion), 0)
    return score


def _ordered_moves(board, moves, side, tt_move, ply):
    moves.sort(
        key=lambda move: _move_order_score(
            board, move, side, tt_move, ply
        ),
        reverse=True,
    )
    return moves


def _score_to_tt(score, ply):
    if score > MATE - 10000:
        return score + ply
    if score < -MATE + 10000:
        return score - ply
    return score


def _score_from_tt(score, ply):
    if score > MATE - 10000:
        return score - ply
    if score < -MATE + 10000:
        return score + ply
    return score


def _quiescence(board, side, alpha, beta, ply, qdepth, position_hash):
    _check_time()

    checked = _in_check(board, side)
    moves = _legal_moves(board, side)

    if not moves:
        if checked:
            return -MATE + ply
        return 0

    static_score = side * _evaluate(board)

    if not checked:
        if static_score >= beta:
            return static_score
        if static_score > alpha:
            alpha = static_score

        if qdepth >= 10:
            return static_score

        tactical = [
            move for move in moves
            if board[move[1]] != 0 or move[2] != 0
        ]
        if not tactical:
            return alpha
    else:
        if qdepth >= 12:
            return static_score
        tactical = moves

    _ordered_moves(board, tactical, side, None, ply)

    for move in tactical:
        moving, captured, new_hash = _do_move(
            board, move, side, position_hash
        )
        try:
            score = -_quiescence(
                board, -side, -beta, -alpha,
                ply + 1, qdepth + 1, new_hash
            )
        finally:
            _undo_move(board, move, moving, captured)

        if score >= beta:
            return score
        if score > alpha:
            alpha = score

    return alpha


def _negamax(board, side, depth, alpha, beta, ply, position_hash):
    _check_time()

    if depth <= 0:
        return _quiescence(
            board, side, alpha, beta, ply, 0, position_hash
        )

    key = position_hash if side == 1 else position_hash ^ SIDE_KEY
    original_alpha = alpha
    tt_move = None

    entry = _tt.get(key)
    if entry is not None:
        entry_depth, stored_score, flag, tt_move = entry
        if entry_depth >= depth:
            tt_score = _score_from_tt(stored_score, ply)
            if flag == 0:
                return tt_score
            if flag == 1 and tt_score >= beta:
                return tt_score
            if flag == 2 and tt_score <= alpha:
                return tt_score

    checked = _in_check(board, side)
    moves = _legal_moves(board, side)

    if not moves:
        if checked:
            return -MATE + ply
        return 0

    _ordered_moves(board, moves, side, tt_move, ply)

    best_score = -INF
    best_move = None

    for index, move in enumerate(moves):
        moving, captured, new_hash = _do_move(
            board, move, side, position_hash
        )
        try:
            if index == 0:
                score = -_negamax(
                    board, -side, depth - 1,
                    -beta, -alpha, ply + 1, new_hash
                )
            else:
                score = -_negamax(
                    board, -side, depth - 1,
                    -alpha - 1, -alpha, ply + 1, new_hash
                )
                if alpha < score < beta:
                    score = -_negamax(
                        board, -side, depth - 1,
                        -beta, -alpha, ply + 1, new_hash
                    )
        finally:
            _undo_move(board, move, moving, captured)

        if score > best_score:
            best_score = score
            best_move = move

        if score > alpha:
            alpha = score

        if alpha >= beta:
            if captured == 0 and move[2] == 0:
                if ply < len(_killers) and move != _killers[ply][0]:
                    _killers[ply][1] = _killers[ply][0]
                    _killers[ply][0] = move

                history_key = (side, move[0], move[1], move[2])
                _history[history_key] = (
                    _history.get(history_key, 0) + depth * depth
                )
            break

    if best_score <= original_alpha:
        flag = 2  # Upper bound
    elif best_score >= beta:
        flag = 1  # Lower bound
    else:
        flag = 0  # Exact

    _tt[key] = (
        depth,
        _score_to_tt(best_score, ply),
        flag,
        best_move,
    )
    return best_score


def _root_search(board, side, moves, depth, position_hash, hint):
    root_moves = list(moves)
    _ordered_moves(board, root_moves, side, hint, 0)

    alpha = -INF
    beta = INF
    best_score = -INF
    best_move = root_moves[0]

    for index, move in enumerate(root_moves):
        if time.perf_counter() >= _deadline:
            raise _SearchTimeout

        moving, captured, new_hash = _do_move(
            board, move, side, position_hash
        )
        try:
            if index == 0:
                score = -_negamax(
                    board, -side, depth - 1,
                    -beta, -alpha, 1, new_hash
                )
            else:
                score = -_negamax(
                    board, -side, depth - 1,
                    -alpha - 1, -alpha, 1, new_hash
                )
                if alpha < score < beta:
                    score = -_negamax(
                        board, -side, depth - 1,
                        -beta, -alpha, 1, new_hash
                    )
        finally:
            _undo_move(board, move, moving, captured)

        if score > best_score:
            best_score = score
            best_move = move

        if score > alpha:
            alpha = score

    return best_move, best_score


def _move_to_uci(move):
    source, target, promotion = move
    result = (
        chr(ord("a") + (source & 7))
        + str((source >> 3) + 1)
        + chr(ord("a") + (target & 7))
        + str((target >> 3) + 1)
    )
    if promotion:
        result += PROMOTION_CHAR[promotion]
    return result


def _fallback_castle(board, side):
    # Used only if there are no ordinary legal moves. Castling rights are not
    # represented by the API, so castling is never assumed during normal play.
    if side == 1:
        king_sq = 4
        enemy = -1

        if board[king_sq] == 6 and not _attacked(board, 4, enemy):
            if (
                board[7] == 4
                and board[5] == 0
                and board[6] == 0
                and not _attacked(board, 5, enemy)
                and not _attacked(board, 6, enemy)
            ):
                return "e1g1"
            if (
                board[0] == 4
                and board[1] == 0
                and board[2] == 0
                and board[3] == 0
                and not _attacked(board, 3, enemy)
                and not _attacked(board, 2, enemy)
            ):
                return "e1c1"
    else:
        king_sq = 60
        enemy = 1

        if board[king_sq] == -6 and not _attacked(board, 60, enemy):
            if (
                board[63] == -4
                and board[61] == 0
                and board[62] == 0
                and not _attacked(board, 61, enemy)
                and not _attacked(board, 62, enemy)
            ):
                return "e8g8"
            if (
                board[56] == -4
                and board[57] == 0
                and board[58] == 0
                and board[59] == 0
                and not _attacked(board, 59, enemy)
                and not _attacked(board, 58, enemy)
            ):
                return "e8c8"

    return None


def policy(pieces: dict[str, str], to_play: str) -> str:
    global _deadline, _nodes, _tt, _history, _killers

    board = [0] * 64
    for square, code in pieces.items():
        if (
            len(square) != 2
            or len(code) != 2
            or code[1] not in CHAR_TO_PIECE
        ):
            continue

        file_index = ord(square[0]) - ord("a")
        rank_index = ord(square[1]) - ord("1")
        if not (0 <= file_index < 8 and 0 <= rank_index < 8):
            continue

        side = 1 if code[0] == "w" else -1
        board[rank_index * 8 + file_index] = (
            side * CHAR_TO_PIECE[code[1]]
        )

    side = 1 if to_play.lower().startswith("w") else -1
    legal = _legal_moves(board, side)

    if not legal:
        castle = _fallback_castle(board, side)
        if castle is not None:
            return castle

        # A policy should not be called for a terminal position. This final
        # branch merely guarantees a string return for malformed input.
        for move in _pseudo_moves(board, side):
            return _move_to_uci(move)
        return "a1a2"

    _deadline = time.perf_counter() + 0.88
    _nodes = 0
    _tt = {}
    _history = {}
    _killers = [[None, None] for _ in range(64)]

    position_hash = _board_hash(board)

    # Establish a legal tactical/positional fallback and detect mate in one.
    best_move = legal[0]
    best_fallback_score = -INF

    for move in legal:
        moving, captured, new_hash = _do_move(
            board, move, side, position_hash
        )
        try:
            score = side * _evaluate(board)

            if captured:
                score += VALUES[abs(captured)] // 8
            if move[2]:
                score += VALUES[move[2]] // 10

            if _in_check(board, -side):
                score += 45
                opponent_moves = _legal_moves(board, -side)
                if not opponent_moves:
                    return _move_to_uci(move)
        finally:
            _undo_move(board, move, moving, captured)

        if score > best_fallback_score:
            best_fallback_score = score
            best_move = move

    # Keep the result of the last fully completed iteration.
    hint = best_move
    try:
        for depth in range(1, 9):
            iteration_move, iteration_score = _root_search(
                board, side, legal, depth, position_hash, hint
            )
            best_move = iteration_move
            hint = iteration_move

            if iteration_score >= MATE - 100:
                break
            if time.perf_counter() >= _deadline:
                break
    except _SearchTimeout:
        pass

    return _move_to_uci(best_move)
