
import time

EMPTY = "."
INF = 10**9
MATE = 100000

PIECE_VALUE = {
    "p": 100,
    "n": 320,
    "b": 335,
    "r": 500,
    "q": 900,
    "k": 0,
}

KNIGHT_STEPS = (
    (-2, -1), (-2, 1), (-1, -2), (-1, 2),
    (1, -2), (1, 2), (2, -1), (2, 1),
)

KING_STEPS = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),            (0, 1),
    (1, -1),  (1, 0),   (1, 1),
)

BISHOP_DIRS = ((1, 1), (1, -1), (-1, 1), (-1, -1))
ROOK_DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))

_deadline = 0.0
_nodes = 0
_tt = {}
_killers = {}
_history = {}


class SearchTimeout(Exception):
    pass


def _check_time():
    global _nodes
    _nodes += 1
    if (_nodes & 127) == 0 and time.perf_counter() >= _deadline:
        raise SearchTimeout


def _square_index(square):
    return (ord(square[1]) - ord("1")) * 8 + ord(square[0]) - ord("a")


def _index_square(index):
    return chr(ord("a") + index % 8) + chr(ord("1") + index // 8)


def _make_move(board, move):
    source, target, promotion = move
    result = board.copy()
    piece = result[source]
    result[source] = EMPTY

    if promotion:
        result[target] = promotion if piece.isupper() else promotion.lower()
    else:
        result[target] = piece

    return result


def _move_string(move):
    source, target, promotion = move
    text = _index_square(source) + _index_square(target)
    if promotion:
        text += promotion.lower()
    return text


def _is_attacked(board, square, by_white):
    file_index = square & 7
    rank_index = square >> 3

    pawn = "P" if by_white else "p"
    pawn_source_rank = rank_index - 1 if by_white else rank_index + 1
    if 0 <= pawn_source_rank < 8:
        if file_index > 0:
            source = pawn_source_rank * 8 + file_index - 1
            if board[source] == pawn:
                return True
        if file_index < 7:
            source = pawn_source_rank * 8 + file_index + 1
            if board[source] == pawn:
                return True

    knight = "N" if by_white else "n"
    for df, dr in KNIGHT_STEPS:
        nf = file_index + df
        nr = rank_index + dr
        if 0 <= nf < 8 and 0 <= nr < 8:
            if board[nr * 8 + nf] == knight:
                return True

    king = "K" if by_white else "k"
    for df, dr in KING_STEPS:
        nf = file_index + df
        nr = rank_index + dr
        if 0 <= nf < 8 and 0 <= nr < 8:
            if board[nr * 8 + nf] == king:
                return True

    for df, dr in BISHOP_DIRS:
        nf = file_index + df
        nr = rank_index + dr
        while 0 <= nf < 8 and 0 <= nr < 8:
            piece = board[nr * 8 + nf]
            if piece != EMPTY:
                if piece.isupper() == by_white and piece.lower() in ("b", "q"):
                    return True
                break
            nf += df
            nr += dr

    for df, dr in ROOK_DIRS:
        nf = file_index + df
        nr = rank_index + dr
        while 0 <= nf < 8 and 0 <= nr < 8:
            piece = board[nr * 8 + nf]
            if piece != EMPTY:
                if piece.isupper() == by_white and piece.lower() in ("r", "q"):
                    return True
                break
            nf += df
            nr += dr

    return False


def _king_square(board, white):
    king = "K" if white else "k"
    try:
        return board.index(king)
    except ValueError:
        return -1


def _in_check(board, white):
    square = _king_square(board, white)
    if square < 0:
        return True
    return _is_attacked(board, square, not white)


def _pseudo_moves(board, white):
    moves = []

    for source, piece in enumerate(board):
        if piece == EMPTY or piece.isupper() != white:
            continue

        file_index = source & 7
        rank_index = source >> 3
        kind = piece.lower()

        if kind == "p":
            direction = 8 if white else -8
            promotion_rank = 7 if white else 0
            start_rank = 1 if white else 6

            target = source + direction
            if 0 <= target < 64 and board[target] == EMPTY:
                target_rank = target >> 3
                if target_rank == promotion_rank:
                    for promotion in ("Q", "R", "B", "N"):
                        moves.append((source, target, promotion))
                else:
                    moves.append((source, target, ""))

                    if rank_index == start_rank:
                        double_target = source + 2 * direction
                        if board[double_target] == EMPTY:
                            moves.append((source, double_target, ""))

            capture_rank = rank_index + (1 if white else -1)
            if 0 <= capture_rank < 8:
                for df in (-1, 1):
                    capture_file = file_index + df
                    if not 0 <= capture_file < 8:
                        continue

                    target = capture_rank * 8 + capture_file
                    captured = board[target]
                    if (
                        captured != EMPTY
                        and captured.isupper() != white
                        and captured.lower() != "k"
                    ):
                        if capture_rank == promotion_rank:
                            for promotion in ("Q", "R", "B", "N"):
                                moves.append((source, target, promotion))
                        else:
                            moves.append((source, target, ""))

        elif kind == "n":
            for df, dr in KNIGHT_STEPS:
                nf = file_index + df
                nr = rank_index + dr
                if 0 <= nf < 8 and 0 <= nr < 8:
                    target = nr * 8 + nf
                    captured = board[target]
                    if captured == EMPTY or (
                        captured.isupper() != white and captured.lower() != "k"
                    ):
                        moves.append((source, target, ""))

        elif kind in ("b", "r", "q"):
            directions = []
            if kind in ("b", "q"):
                directions += BISHOP_DIRS
            if kind in ("r", "q"):
                directions += ROOK_DIRS

            for df, dr in directions:
                nf = file_index + df
                nr = rank_index + dr
                while 0 <= nf < 8 and 0 <= nr < 8:
                    target = nr * 8 + nf
                    captured = board[target]

                    if captured == EMPTY:
                        moves.append((source, target, ""))
                    else:
                        if (
                            captured.isupper() != white
                            and captured.lower() != "k"
                        ):
                            moves.append((source, target, ""))
                        break

                    nf += df
                    nr += dr

        elif kind == "k":
            for df, dr in KING_STEPS:
                nf = file_index + df
                nr = rank_index + dr
                if 0 <= nf < 8 and 0 <= nr < 8:
                    target = nr * 8 + nf
                    captured = board[target]
                    if captured == EMPTY or (
                        captured.isupper() != white and captured.lower() != "k"
                    ):
                        moves.append((source, target, ""))

    return moves


def _legal_moves(board, white):
    king_square = _king_square(board, white)
    if king_square < 0:
        return []

    legal = []
    for move in _pseudo_moves(board, white):
        next_board = _make_move(board, move)
        next_king_square = move[1] if move[0] == king_square else king_square
        if not _is_attacked(next_board, next_king_square, not white):
            legal.append(move)

    return legal


def _evaluate(board):
    score = 0
    non_pawn_material = 0

    white_pawns = []
    black_pawns = []
    white_rooks = []
    black_rooks = []
    white_bishops = 0
    black_bishops = 0
    white_king = -1
    black_king = -1

    for square, piece in enumerate(board):
        if piece == EMPTY:
            continue

        white = piece.isupper()
        sign = 1 if white else -1
        kind = piece.lower()
        file_index = square & 7
        rank_index = square >> 3

        center = 14 - (
            abs(2 * file_index - 7) + abs(2 * rank_index - 7)
        )

        bonus = 0
        if kind == "p":
            advance = rank_index - 1 if white else 6 - rank_index
            bonus += advance * 7
            if file_index in (3, 4):
                bonus += 8
            elif file_index in (2, 5):
                bonus += 3

            if white:
                white_pawns.append((file_index, rank_index))
            else:
                black_pawns.append((file_index, rank_index))

        elif kind == "n":
            bonus += center * 5
            non_pawn_material += PIECE_VALUE[kind]

        elif kind == "b":
            bonus += center * 3
            non_pawn_material += PIECE_VALUE[kind]
            if white:
                white_bishops += 1
            else:
                black_bishops += 1

        elif kind == "r":
            bonus += center
            relative_rank = rank_index if white else 7 - rank_index
            if relative_rank == 6:
                bonus += 22
            non_pawn_material += PIECE_VALUE[kind]
            if white:
                white_rooks.append((file_index, rank_index))
            else:
                black_rooks.append((file_index, rank_index))

        elif kind == "q":
            bonus += center
            non_pawn_material += PIECE_VALUE[kind]

        elif kind == "k":
            if white:
                white_king = square
            else:
                black_king = square

        score += sign * (PIECE_VALUE[kind] + bonus)

    white_files = [0] * 8
    black_files = [0] * 8
    for file_index, _ in white_pawns:
        white_files[file_index] += 1
    for file_index, _ in black_pawns:
        black_files[file_index] += 1

    for file_index in range(8):
        if white_files[file_index] > 1:
            score -= 13 * (white_files[file_index] - 1)
        if black_files[file_index] > 1:
            score += 13 * (black_files[file_index] - 1)

    for file_index, rank_index in white_pawns:
        if (
            (file_index == 0 or white_files[file_index - 1] == 0)
            and (file_index == 7 or white_files[file_index + 1] == 0)
        ):
            score -= 9

        passed = True
        for enemy_file, enemy_rank in black_pawns:
            if abs(enemy_file - file_index) <= 1 and enemy_rank > rank_index:
                passed = False
                break
        if passed:
            advance = max(0, rank_index - 1)
            score += 12 + advance * 12

    for file_index, rank_index in black_pawns:
        if (
            (file_index == 0 or black_files[file_index - 1] == 0)
            and (file_index == 7 or black_files[file_index + 1] == 0)
        ):
            score += 9

        passed = True
        for enemy_file, enemy_rank in white_pawns:
            if abs(enemy_file - file_index) <= 1 and enemy_rank < rank_index:
                passed = False
                break
        if passed:
            advance = max(0, 6 - rank_index)
            score -= 12 + advance * 12

    if white_bishops >= 2:
        score += 28
    if black_bishops >= 2:
        score -= 28

    for file_index, _ in white_rooks:
        if white_files[file_index] == 0:
            score += 9
            if black_files[file_index] == 0:
                score += 8

    for file_index, _ in black_rooks:
        if black_files[file_index] == 0:
            score -= 9
            if white_files[file_index] == 0:
                score -= 8

    endgame = non_pawn_material <= 1500

    if white_king >= 0:
        file_index = white_king & 7
        rank_index = white_king >> 3
        center = 14 - (
            abs(2 * file_index - 7) + abs(2 * rank_index - 7)
        )

        if endgame:
            score += center * 4
        else:
            score -= center * 2
            if rank_index <= 1 and file_index in (1, 2, 6, 7):
                score += 20
            shield_rank = rank_index + 1
            if shield_rank < 8:
                for shield_file in range(max(0, file_index - 1),
                                         min(8, file_index + 2)):
                    if board[shield_rank * 8 + shield_file] == "P":
                        score += 8

    if black_king >= 0:
        file_index = black_king & 7
        rank_index = black_king >> 3
        center = 14 - (
            abs(2 * file_index - 7) + abs(2 * rank_index - 7)
        )

        if endgame:
            score -= center * 4
        else:
            score += center * 2
            if rank_index >= 6 and file_index in (1, 2, 6, 7):
                score -= 20
            shield_rank = rank_index - 1
            if shield_rank >= 0:
                for shield_file in range(max(0, file_index - 1),
                                         min(8, file_index + 2)):
                    if board[shield_rank * 8 + shield_file] == "p":
                        score -= 8

    return score


def _static_score(board, white):
    score = _evaluate(board)
    return (score if white else -score) + 8


def _move_order_score(board, move, white, tt_move=None, ply=0):
    source, target, promotion = move
    moving_piece = board[source]
    captured_piece = board[target]
    score = 0

    if move == tt_move:
        score += 2_000_000

    if captured_piece != EMPTY:
        score += (
            100_000
            + 16 * PIECE_VALUE[captured_piece.lower()]
            - PIECE_VALUE[moving_piece.lower()]
        )

    if promotion:
        score += 90_000 + PIECE_VALUE[promotion.lower()]

    killers = _killers.get(ply, ())
    if captured_piece == EMPTY and not promotion:
        if len(killers) > 0 and move == killers[0]:
            score += 80_000
        elif len(killers) > 1 and move == killers[1]:
            score += 70_000

        score += _history.get((white, source, target), 0)

        target_file = target & 7
        target_rank = target >> 3
        center = 14 - (
            abs(2 * target_file - 7) + abs(2 * target_rank - 7)
        )
        score += center * 2

        if moving_piece.lower() == "p":
            source_rank = source >> 3
            score += (
                (target_rank - source_rank)
                if white
                else (source_rank - target_rank)
            ) * 3

    return score


def _ordered_moves(board, moves, white, tt_move=None, ply=0):
    return sorted(
        moves,
        key=lambda move: _move_order_score(
            board, move, white, tt_move, ply
        ),
        reverse=True,
    )


def _pack_tt_score(score, ply):
    if score > MATE - 1000:
        return score + ply
    if score < -MATE + 1000:
        return score - ply
    return score


def _unpack_tt_score(score, ply):
    if score > MATE - 1000:
        return score - ply
    if score < -MATE + 1000:
        return score + ply
    return score


def _quiescence(board, white, alpha, beta, ply, qply=0):
    _check_time()

    checked = _in_check(board, white)

    if not checked:
        stand_pat = _static_score(board, white)
        if stand_pat >= beta:
            return stand_pat
        if stand_pat > alpha:
            alpha = stand_pat

    moves = _legal_moves(board, white)
    if not moves:
        if checked:
            return -MATE + ply
        return 0

    if qply >= 10:
        return _static_score(board, white)

    if not checked:
        moves = [
            move for move in moves
            if board[move[1]] != EMPTY or bool(move[2])
        ]
        if not moves:
            return alpha

    moves = _ordered_moves(board, moves, white, None, ply)

    for move in moves:
        next_board = _make_move(board, move)
        score = -_quiescence(
            next_board, not white, -beta, -alpha, ply + 1, qply + 1
        )

        if score >= beta:
            return score
        if score > alpha:
            alpha = score

    return alpha


def _negamax(board, white, depth, alpha, beta, ply):
    _check_time()

    if depth <= 0:
        return _quiescence(board, white, alpha, beta, ply)

    original_alpha = alpha
    key = (tuple(board), white)
    tt_move = None

    entry = _tt.get(key)
    if entry is not None:
        entry_depth, packed_score, flag, tt_move = entry
        if entry_depth >= depth:
            score = _unpack_tt_score(packed_score, ply)
            if flag == 0:
                return score
            if flag == 1:
                alpha = max(alpha, score)
            else:
                beta = min(beta, score)
            if alpha >= beta:
                return score

    checked = _in_check(board, white)
    moves = _legal_moves(board, white)

    if not moves:
        if checked:
            return -MATE + ply
        return 0

    moves = _ordered_moves(board, moves, white, tt_move, ply)
    best_score = -INF
    best_move = moves[0]

    for move in moves:
        next_board = _make_move(board, move)
        score = -_negamax(
            next_board, not white, depth - 1, -beta, -alpha, ply + 1
        )

        if score > best_score:
            best_score = score
            best_move = move

        if score > alpha:
            alpha = score

        if alpha >= beta:
            if board[move[1]] == EMPTY and not move[2]:
                killers = _killers.setdefault(ply, [])
                if move not in killers:
                    killers.insert(0, move)
                    del killers[2:]
                key_history = (white, move[0], move[1])
                _history[key_history] = (
                    _history.get(key_history, 0) + depth * depth
                )
            break

    if best_score <= original_alpha:
        flag = 2
    elif best_score >= beta:
        flag = 1
    else:
        flag = 0

    if len(_tt) < 200000:
        _tt[key] = (
            depth,
            _pack_tt_score(best_score, ply),
            flag,
            best_move,
        )

    return best_score


def _root_order(board, moves, white, previous_best=None):
    scored = []

    for move in moves:
        score = _move_order_score(
            board, move, white, previous_best, 0
        )
        next_board = _make_move(board, move)
        if _in_check(next_board, not white):
            score += 500
        scored.append((score, move))

    scored.sort(reverse=True, key=lambda item: item[0])
    return [move for _, move in scored]


def _root_search(board, white, moves, depth, previous_best):
    ordered = _root_order(board, moves, white, previous_best)
    alpha = -INF
    beta = INF
    best_score = -INF
    best_move = ordered[0]

    for move in ordered:
        _check_time()
        next_board = _make_move(board, move)
        score = -_negamax(
            next_board, not white, depth - 1, -beta, -alpha, 1
        )

        if score > best_score:
            best_score = score
            best_move = move

        if score > alpha:
            alpha = score

    return best_move, best_score


def _fallback_castle(board, white):
    home = 4 if white else 60
    king = "K" if white else "k"
    rook = "R" if white else "r"

    if board[home] != king or _is_attacked(board, home, not white):
        return None

    kingside_rook = home + 3
    if (
        board[kingside_rook] == rook
        and board[home + 1] == EMPTY
        and board[home + 2] == EMPTY
    ):
        pass_board = board.copy()
        pass_board[home] = EMPTY
        pass_board[home + 1] = king

        final_board = board.copy()
        final_board[home] = EMPTY
        final_board[kingside_rook] = EMPTY
        final_board[home + 2] = king
        final_board[home + 1] = rook

        if (
            not _is_attacked(pass_board, home + 1, not white)
            and not _is_attacked(final_board, home + 2, not white)
        ):
            return _index_square(home) + _index_square(home + 2)

    queenside_rook = home - 4
    if (
        board[queenside_rook] == rook
        and board[home - 1] == EMPTY
        and board[home - 2] == EMPTY
        and board[home - 3] == EMPTY
    ):
        pass_board = board.copy()
        pass_board[home] = EMPTY
        pass_board[home - 1] = king

        final_board = board.copy()
        final_board[home] = EMPTY
        final_board[queenside_rook] = EMPTY
        final_board[home - 2] = king
        final_board[home - 1] = rook

        if (
            not _is_attacked(pass_board, home - 1, not white)
            and not _is_attacked(final_board, home - 2, not white)
        ):
            return _index_square(home) + _index_square(home - 2)

    return None


def policy(pieces: dict[str, str], to_play: str) -> str:
    global _deadline, _nodes, _tt, _killers, _history

    start_time = time.perf_counter()
    _deadline = start_time + 0.90
    _nodes = 0
    _tt = {}
    _killers = {}
    _history = {}

    board = [EMPTY] * 64
    for square, code in pieces.items():
        if len(square) != 2 or len(code) != 2:
            continue

        color = code[0]
        kind = code[1]
        piece = kind.upper() if color == "w" else kind.lower()
        board[_square_index(square)] = piece

    white = to_play.lower().startswith("w")
    legal = _legal_moves(board, white)

    if not legal:
        castle = _fallback_castle(board, white)
        if castle is not None:
            return castle
        return "0000"

    ordered = _root_order(board, legal, white)
    best_move = ordered[0]

    if len(legal) == 1:
        return _move_string(best_move)

    for depth in range(1, 9):
        try:
            candidate, score = _root_search(
                board, white, legal, depth, best_move
            )
            best_move = candidate

            if score >= MATE - 100:
                break
        except SearchTimeout:
            break

    return _move_string(best_move)
