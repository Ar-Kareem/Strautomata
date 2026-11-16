
import time

FILES = "abcdefgh"
BASE_VALUE = (0, 100, 320, 330, 500, 900, 0)
PROMOTION_SUFFIX = {2: "n", 3: "b", 4: "r", 5: "q"}

INF = 1_000_000
MATE = 100_000

# Piece-square tables from White's perspective. Black uses a vertical mirror.
PST_MID = [[0] * 64 for _ in range(7)]
PST_END_KING = [0] * 64

for sq in range(64):
    f = sq & 7
    r = sq >> 3
    center = (
        3.5 - abs(f - 3.5)
        + 3.5 - abs(r - 3.5)
    )

    PST_MID[1][sq] = r * 9 + int((3.5 - abs(f - 3.5)) * 2)
    PST_MID[2][sq] = int(center * 9) - 25
    PST_MID[3][sq] = int(center * 5) - 10
    PST_MID[4][sq] = r * 2
    PST_MID[5][sq] = int(center * 2) - 5

    # In the middlegame, prefer a king on the back ranks and away
    # from the center, especially near conventional castled squares.
    PST_MID[6][sq] = (
        -int(center * 9)
        + (20 if r <= 1 else -r * 6)
        + (16 if f in (2, 6) else 0)
    )
    PST_END_KING[sq] = int(center * 9) - 20


class SearchTimeout(Exception):
    pass


def policy(pieces: dict[str, str], to_play: str) -> str:
    board = [0] * 64
    type_number = {"P": 1, "N": 2, "B": 3, "R": 4, "Q": 5, "K": 6}

    for square, code in pieces.items():
        f = ord(square[0]) - 97
        r = ord(square[1]) - 49
        color = 1 if code[0] == "w" else -1
        board[r * 8 + f] = color * type_number[code[1]]

    root_side = 1 if to_play == "white" else -1
    start_time = time.perf_counter()
    deadline = start_time + 0.90

    nodes = 0
    transposition = {}
    history = {}
    killers = [[None, None] for _ in range(64)]

    knight_steps = (
        (-2, -1), (-2, 1), (-1, -2), (-1, 2),
        (1, -2), (1, 2), (2, -1), (2, 1),
    )
    bishop_dirs = ((1, 1), (1, -1), (-1, 1), (-1, -1))
    rook_dirs = ((1, 0), (-1, 0), (0, 1), (0, -1))
    king_dirs = bishop_dirs + rook_dirs

    def check_time():
        nonlocal nodes
        nodes += 1
        if (nodes & 511) == 0 and time.perf_counter() >= deadline:
            raise SearchTimeout

    def is_attacked(square, attacker):
        f = square & 7
        r = square >> 3

        # Pawn attacks.
        source_rank = r - 1 if attacker == 1 else r + 1
        if 0 <= source_rank < 8:
            if f > 0 and board[source_rank * 8 + f - 1] == attacker:
                return True
            if f < 7 and board[source_rank * 8 + f + 1] == attacker:
                return True

        # Knight attacks.
        attacker_knight = attacker * 2
        for df, dr in knight_steps:
            nf, nr = f + df, r + dr
            if 0 <= nf < 8 and 0 <= nr < 8:
                if board[nr * 8 + nf] == attacker_knight:
                    return True

        # Adjacent enemy king.
        attacker_king = attacker * 6
        for df, dr in king_dirs:
            nf, nr = f + df, r + dr
            if 0 <= nf < 8 and 0 <= nr < 8:
                if board[nr * 8 + nf] == attacker_king:
                    return True

        # Diagonal sliders.
        for df, dr in bishop_dirs:
            nf, nr = f + df, r + dr
            while 0 <= nf < 8 and 0 <= nr < 8:
                p = board[nr * 8 + nf]
                if p:
                    if p == attacker * 3 or p == attacker * 5:
                        return True
                    break
                nf += df
                nr += dr

        # Orthogonal sliders.
        for df, dr in rook_dirs:
            nf, nr = f + df, r + dr
            while 0 <= nf < 8 and 0 <= nr < 8:
                p = board[nr * 8 + nf]
                if p:
                    if p == attacker * 4 or p == attacker * 5:
                        return True
                    break
                nf += df
                nr += dr

        return False

    def king_square(side):
        target = side * 6
        for sq, p in enumerate(board):
            if p == target:
                return sq
        return -1

    def in_check(side):
        ksq = king_square(side)
        return ksq >= 0 and is_attacked(ksq, -side)

    def generate_pseudo(side, captures_only=False):
        moves = []
        for source, piece in enumerate(board):
            if piece * side <= 0:
                continue

            kind = abs(piece)
            f = source & 7
            r = source >> 3

            if kind == 1:
                direction = 1 if side == 1 else -1
                promotion_rank = 7 if side == 1 else 0
                start_rank = 1 if side == 1 else 6
                next_rank = r + direction

                if 0 <= next_rank < 8:
                    target = next_rank * 8 + f

                    if board[target] == 0:
                        if next_rank == promotion_rank:
                            for promoted in (5, 4, 3, 2):
                                moves.append((source, target, promoted, 0))
                        elif not captures_only:
                            moves.append((source, target, 0, 0))
                            if r == start_rank:
                                target2 = (r + 2 * direction) * 8 + f
                                if board[target2] == 0:
                                    moves.append((source, target2, 0, 0))

                    for df in (-1, 1):
                        nf = f + df
                        if not (0 <= nf < 8):
                            continue
                        target = next_rank * 8 + nf
                        captured = board[target]
                        if captured * side < 0 and abs(captured) != 6:
                            if next_rank == promotion_rank:
                                for promoted in (5, 4, 3, 2):
                                    moves.append(
                                        (source, target, promoted, captured)
                                    )
                            else:
                                moves.append((source, target, 0, captured))

            elif kind == 2:
                for df, dr in knight_steps:
                    nf, nr = f + df, r + dr
                    if not (0 <= nf < 8 and 0 <= nr < 8):
                        continue
                    target = nr * 8 + nf
                    captured = board[target]
                    if captured * side > 0 or abs(captured) == 6:
                        continue
                    if captured or not captures_only:
                        moves.append((source, target, 0, captured))

            elif kind in (3, 4, 5):
                if kind == 3:
                    directions = bishop_dirs
                elif kind == 4:
                    directions = rook_dirs
                else:
                    directions = king_dirs

                for df, dr in directions:
                    nf, nr = f + df, r + dr
                    while 0 <= nf < 8 and 0 <= nr < 8:
                        target = nr * 8 + nf
                        captured = board[target]

                        if captured:
                            if captured * side < 0 and abs(captured) != 6:
                                moves.append((source, target, 0, captured))
                            break

                        if not captures_only:
                            moves.append((source, target, 0, 0))
                        nf += df
                        nr += dr

            else:  # King
                for df, dr in king_dirs:
                    nf, nr = f + df, r + dr
                    if not (0 <= nf < 8 and 0 <= nr < 8):
                        continue
                    target = nr * 8 + nf
                    captured = board[target]
                    if captured * side > 0 or abs(captured) == 6:
                        continue
                    if captured or not captures_only:
                        moves.append((source, target, 0, captured))

        return moves

    def make_move(move, side):
        source, target, promoted, captured = move
        piece = board[source]
        board[source] = 0
        board[target] = side * promoted if promoted else piece
        return piece

    def unmake_move(move, original_piece):
        source, target, promoted, captured = move
        board[source] = original_piece
        board[target] = captured

    def generate_legal(side, captures_only=False):
        legal = []
        current_king = king_square(side)

        for move in generate_pseudo(side, captures_only):
            source, target, promoted, captured = move
            original_piece = make_move(move, side)
            resulting_king = target if abs(original_piece) == 6 else current_king

            if resulting_king >= 0 and not is_attacked(resulting_king, -side):
                legal.append(move)

            unmake_move(move, original_piece)

        return legal

    def evaluate(side):
        phase = 0
        for p in board:
            kind = abs(p)
            if 2 <= kind <= 5:
                phase += BASE_VALUE[kind]

        middlegame = phase > 1800
        score = 0
        bishop_count = [0, 0]
        pawn_files = [[0] * 8, [0] * 8]
        white_pawns = []
        black_pawns = []
        kings = [-1, -1]

        for sq, p in enumerate(board):
            if not p:
                continue

            color = 1 if p > 0 else -1
            ci = 0 if color == 1 else 1
            kind = abs(p)
            f = sq & 7
            r = sq >> 3
            oriented = sq if color == 1 else (7 - r) * 8 + f

            value = BASE_VALUE[kind]
            if kind == 6 and not middlegame:
                value += PST_END_KING[oriented]
            else:
                value += PST_MID[kind][oriented]

            score += color * value

            if kind == 1:
                pawn_files[ci][f] += 1
                if color == 1:
                    white_pawns.append(sq)
                else:
                    black_pawns.append(sq)
            elif kind == 3:
                bishop_count[ci] += 1
            elif kind == 6:
                kings[ci] = sq

        # Bishop pair.
        if bishop_count[0] >= 2:
            score += 28
        if bishop_count[1] >= 2:
            score -= 28

        # Doubled pawns.
        for f in range(8):
            if pawn_files[0][f] > 1:
                score -= 12 * (pawn_files[0][f] - 1)
            if pawn_files[1][f] > 1:
                score += 12 * (pawn_files[1][f] - 1)

        # Passed pawns.
        passed_bonus = (0, 5, 12, 22, 38, 65, 100, 0)

        for sq in white_pawns:
            f, r = sq & 7, sq >> 3
            passed = True
            for enemy in black_pawns:
                ef, er = enemy & 7, enemy >> 3
                if er > r and abs(ef - f) <= 1:
                    passed = False
                    break
            if passed:
                score += passed_bonus[r]

        for sq in black_pawns:
            f, r = sq & 7, sq >> 3
            passed = True
            for enemy in white_pawns:
                ef, er = enemy & 7, enemy >> 3
                if er < r and abs(ef - f) <= 1:
                    passed = False
                    break
            if passed:
                score -= passed_bonus[7 - r]

        # Open and semi-open files for rooks.
        for sq, p in enumerate(board):
            if abs(p) != 4:
                continue
            color = 1 if p > 0 else -1
            f = sq & 7
            own_index = 0 if color == 1 else 1
            enemy_index = 1 - own_index
            bonus = 0
            if pawn_files[own_index][f] == 0:
                bonus += 7
                if pawn_files[enemy_index][f] == 0:
                    bonus += 9
            score += color * bonus

        # Middlegame pawn cover near each king.
        if middlegame:
            for ci, color in ((0, 1), (1, -1)):
                ksq = kings[ci]
                if ksq < 0:
                    continue
                kf, kr = ksq & 7, ksq >> 3
                shield_rank = kr + (1 if color == 1 else -1)
                shield = 0
                if 0 <= shield_rank < 8:
                    for sf in range(max(0, kf - 1), min(7, kf + 1) + 1):
                        if board[shield_rank * 8 + sf] == color:
                            shield += 9
                score += color * shield

        return score if side == 1 else -score

    def move_order_score(move, side, tt_move, ply):
        source, target, promoted, captured = move

        if tt_move is not None and move == tt_move:
            return 10_000_000

        score = 0
        attacker = abs(board[source])

        if captured:
            score += 1_000_000
            score += 16 * BASE_VALUE[abs(captured)] - BASE_VALUE[attacker]

        if promoted:
            score += 800_000 + BASE_VALUE[promoted] * 10

        if ply < len(killers):
            if move == killers[ply][0]:
                score += 700_000
            elif move == killers[ply][1]:
                score += 690_000

        score += history.get((side, source, target, promoted), 0)
        return score

    def order_moves(moves, side, tt_move, ply):
        moves.sort(
            key=lambda m: move_order_score(m, side, tt_move, ply),
            reverse=True,
        )

    def pack_tt_score(value, ply):
        if value > MATE - 1000:
            return value + ply
        if value < -MATE + 1000:
            return value - ply
        return value

    def unpack_tt_score(value, ply):
        if value > MATE - 1000:
            return value - ply
        if value < -MATE + 1000:
            return value + ply
        return value

    def quiescence(alpha, beta, side, ply, qply=0):
        check_time()

        checked = in_check(side)

        if checked:
            moves = generate_legal(side, False)
            if not moves:
                return -MATE + ply

            # Bound pathological sequences of mutual checking moves.
            if qply >= 12:
                return evaluate(side)

            order_moves(moves, side, None, min(ply, 63))
            best = -INF

            for move in moves:
                original_piece = make_move(move, side)
                try:
                    value = -quiescence(
                        -beta, -alpha, -side, ply + 1, qply + 1
                    )
                finally:
                    unmake_move(move, original_piece)

                if value > best:
                    best = value
                if value > alpha:
                    alpha = value
                if alpha >= beta:
                    break

            return best

        stand_pat = evaluate(side)
        if stand_pat >= beta:
            return stand_pat
        if stand_pat > alpha:
            alpha = stand_pat

        if qply >= 10:
            return stand_pat

        moves = generate_legal(side, True)
        if not moves:
            return stand_pat

        order_moves(moves, side, None, min(ply, 63))
        best = stand_pat

        for move in moves:
            original_piece = make_move(move, side)
            try:
                value = -quiescence(
                    -beta, -alpha, -side, ply + 1, qply + 1
                )
            finally:
                unmake_move(move, original_piece)

            if value > best:
                best = value
            if value > alpha:
                alpha = value
            if alpha >= beta:
                break

        return best

    def negamax(depth, alpha, beta, side, ply):
        check_time()

        if depth <= 0:
            return quiescence(alpha, beta, side, ply)

        key = (tuple(board), side)
        alpha_start = alpha
        beta_start = beta
        tt_move = None

        entry = transposition.get(key)
        if entry is not None:
            stored_depth, stored_value, flag, tt_move = entry
            if stored_depth >= depth:
                value = unpack_tt_score(stored_value, ply)
                if flag == 0:
                    return value
                if flag == 1 and value > alpha:
                    alpha = value
                elif flag == 2 and value < beta:
                    beta = value
                if alpha >= beta:
                    return value

        moves = generate_legal(side, False)
        if not moves:
            if in_check(side):
                return -MATE + ply
            return 0

        order_moves(moves, side, tt_move, min(ply, 63))

        best_value = -INF
        best_move = moves[0]
        first = True

        for move in moves:
            original_piece = make_move(move, side)
            try:
                if first:
                    value = -negamax(
                        depth - 1, -beta, -alpha, -side, ply + 1
                    )
                    first = False
                else:
                    value = -negamax(
                        depth - 1, -alpha - 1, -alpha, -side, ply + 1
                    )
                    if alpha < value < beta:
                        value = -negamax(
                            depth - 1, -beta, -alpha, -side, ply + 1
                        )
            finally:
                unmake_move(move, original_piece)

            if value > best_value:
                best_value = value
                best_move = move

            if value > alpha:
                alpha = value

            if alpha >= beta:
                if move[3] == 0 and move[2] == 0:
                    kp = min(ply, 63)
                    if killers[kp][0] != move:
                        killers[kp][1] = killers[kp][0]
                        killers[kp][0] = move
                    hkey = (side, move[0], move[1], move[2])
                    history[hkey] = history.get(hkey, 0) + depth * depth
                break

        if best_value <= alpha_start:
            flag = 2  # Upper bound.
        elif best_value >= beta_start:
            flag = 1  # Lower bound.
        else:
            flag = 0  # Exact.

        if len(transposition) < 250_000:
            transposition[key] = (
                depth,
                pack_tt_score(best_value, ply),
                flag,
                best_move,
            )

        return best_value

    def move_to_uci(move):
        source, target, promoted, captured = move
        result = (
            FILES[source & 7]
            + str((source >> 3) + 1)
            + FILES[target & 7]
            + str((target >> 3) + 1)
        )
        if promoted:
            result += PROMOTION_SUFFIX[promoted]
        return result

    root_moves = generate_legal(root_side, False)

    # The board-only API cannot encode en-passant history. This fallback is
    # relevant only in the exceptional case where en passant is the sole
    # possible move.
    if not root_moves:
        direction = 1 if root_side == 1 else -1
        required_rank = 4 if root_side == 1 else 3
        own_pawn = root_side
        enemy_pawn = -root_side

        for source, p in enumerate(board):
            if p != own_pawn or (source >> 3) != required_rank:
                continue
            f = source & 7
            r = source >> 3

            for df in (-1, 1):
                nf = f + df
                nr = r + direction
                if not (0 <= nf < 8 and 0 <= nr < 8):
                    continue

                adjacent = r * 8 + nf
                target = nr * 8 + nf
                if board[adjacent] != enemy_pawn or board[target] != 0:
                    continue

                board[source] = 0
                board[adjacent] = 0
                board[target] = own_pawn
                ksq = king_square(root_side)
                legal = ksq >= 0 and not is_attacked(ksq, -root_side)
                board[target] = 0
                board[adjacent] = enemy_pawn
                board[source] = own_pawn

                if legal:
                    return (
                        FILES[source & 7]
                        + str((source >> 3) + 1)
                        + FILES[target & 7]
                        + str((target >> 3) + 1)
                    )

        # A policy is normally never queried after mate or stalemate.
        return "a1a1"

    order_moves(root_moves, root_side, None, 0)
    best_move = root_moves[0]
    previous_best = best_move

    # Iterative deepening ensures a completed result is always available.
    for depth in range(1, 9):
        if time.perf_counter() >= deadline:
            break

        ordered = list(root_moves)
        order_moves(ordered, root_side, previous_best, 0)

        iteration_best = ordered[0]
        iteration_score = -INF
        alpha = -INF
        completed = False

        try:
            for move in ordered:
                original_piece = make_move(move, root_side)
                try:
                    value = -negamax(
                        depth - 1, -INF, -alpha, -root_side, 1
                    )
                finally:
                    unmake_move(move, original_piece)

                if value > iteration_score:
                    iteration_score = value
                    iteration_best = move
                if value > alpha:
                    alpha = value

            completed = True
        except SearchTimeout:
            completed = False

        if not completed:
            break

        best_move = iteration_best
        previous_best = iteration_best

        if iteration_score >= MATE - 100:
            break

    return move_to_uci(best_move)
