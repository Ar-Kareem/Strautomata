
import time

WHITE = 1
BLACK = -1

PAWN = 1
KNIGHT = 2
BISHOP = 3
ROOK = 4
QUEEN = 5
KING = 6

PIECE_TO_INT = {
    "P": PAWN, "N": KNIGHT, "B": BISHOP,
    "R": ROOK, "Q": QUEEN, "K": KING
}
INT_TO_PROMO = {
    QUEEN: "q", ROOK: "r", BISHOP: "b", KNIGHT: "n"
}
FILES = "abcdefgh"

VALUE = {
    PAWN: 100,
    KNIGHT: 320,
    BISHOP: 335,
    ROOK: 500,
    QUEEN: 900,
    KING: 0,
}

INF = 10 ** 9
MATE = 10 ** 6

DEADLINE = 0.0
NODES = 0
TT = {}
KILLERS = []
HISTORY = {}


class SearchTimeout(Exception):
    pass


def sq_to_idx(sq: str) -> int:
    return (ord(sq[0]) - 97) + 8 * (ord(sq[1]) - 49)


def idx_to_sq(i: int) -> str:
    return FILES[i & 7] + str((i >> 3) + 1)


def move_to_uci(m) -> str:
    f, t, promo = m
    s = idx_to_sq(f) + idx_to_sq(t)
    if promo:
        s += INT_TO_PROMO[promo]
    return s


def check_time():
    global NODES
    NODES += 1
    if (NODES & 2047) == 0 and time.perf_counter() > DEADLINE:
        raise SearchTimeout()


def find_king(board, side: int) -> int:
    target = side * KING
    for i, p in enumerate(board):
        if p == target:
            return i
    return -1


def is_attacked(board, sq: int, by_side: int) -> bool:
    if sq < 0:
        return False

    f = sq & 7
    r = sq >> 3

    # Pawn attacks
    if by_side == WHITE:
        if f < 7 and sq - 7 >= 0 and board[sq - 7] == WHITE * PAWN:
            return True
        if f > 0 and sq - 9 >= 0 and board[sq - 9] == WHITE * PAWN:
            return True
    else:
        if f > 0 and sq + 7 < 64 and board[sq + 7] == BLACK * PAWN:
            return True
        if f < 7 and sq + 9 < 64 and board[sq + 9] == BLACK * PAWN:
            return True

    # Knight attacks
    for df, dr in ((1, 2), (2, 1), (2, -1), (1, -2),
                   (-1, -2), (-2, -1), (-2, 1), (-1, 2)):
        nf, nr = f + df, r + dr
        if 0 <= nf < 8 and 0 <= nr < 8:
            if board[nr * 8 + nf] == by_side * KNIGHT:
                return True

    # Bishop / queen diagonals
    for df, dr in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        nf, nr = f + df, r + dr
        while 0 <= nf < 8 and 0 <= nr < 8:
            p = board[nr * 8 + nf]
            if p:
                if p * by_side > 0 and abs(p) in (BISHOP, QUEEN):
                    return True
                break
            nf += df
            nr += dr

    # Rook / queen lines
    for df, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nf, nr = f + df, r + dr
        while 0 <= nf < 8 and 0 <= nr < 8:
            p = board[nr * 8 + nf]
            if p:
                if p * by_side > 0 and abs(p) in (ROOK, QUEEN):
                    return True
                break
            nf += df
            nr += dr

    # King attacks
    for df in (-1, 0, 1):
        for dr in (-1, 0, 1):
            if df == 0 and dr == 0:
                continue
            nf, nr = f + df, r + dr
            if 0 <= nf < 8 and 0 <= nr < 8:
                if board[nr * 8 + nf] == by_side * KING:
                    return True

    return False


def is_in_check(board, side: int) -> bool:
    return is_attacked(board, find_king(board, side), -side)


def make_move(board, m):
    f, t, promo = m
    piece = board[f]
    captured = board[t]
    board[f] = 0
    board[t] = (1 if piece > 0 else -1) * promo if promo else piece
    return captured, piece


def unmake_move(board, m, captured, piece):
    f, t, promo = m
    board[f] = piece
    board[t] = captured


def generate_pseudo(board, side: int, noisy: bool = False):
    moves = []

    for i, p in enumerate(board):
        if p * side <= 0:
            continue

        pt = abs(p)
        f = i & 7
        r = i >> 3

        if pt == PAWN:
            direction = 8 if side == WHITE else -8
            start_rank = 1 if side == WHITE else 6
            promo_from_rank = 6 if side == WHITE else 1

            one = i + direction
            if 0 <= one < 64 and board[one] == 0:
                if r == promo_from_rank:
                    for pr in (QUEEN, ROOK, BISHOP, KNIGHT):
                        moves.append((i, one, pr))
                elif not noisy:
                    moves.append((i, one, 0))
                    two = i + 2 * direction
                    if r == start_rank and 0 <= two < 64 and board[two] == 0:
                        moves.append((i, two, 0))

            for df in (-1, 1):
                nf = f + df
                if 0 <= nf < 8:
                    to = i + direction + df
                    if 0 <= to < 64 and board[to] * side < 0 and abs(board[to]) != KING:
                        if r == promo_from_rank:
                            for pr in (QUEEN, ROOK, BISHOP, KNIGHT):
                                moves.append((i, to, pr))
                        else:
                            moves.append((i, to, 0))

        elif pt == KNIGHT:
            for df, dr in ((1, 2), (2, 1), (2, -1), (1, -2),
                           (-1, -2), (-2, -1), (-2, 1), (-1, 2)):
                nf, nr = f + df, r + dr
                if 0 <= nf < 8 and 0 <= nr < 8:
                    to = nr * 8 + nf
                    target = board[to]
                    if target == 0:
                        if not noisy:
                            moves.append((i, to, 0))
                    elif target * side < 0 and abs(target) != KING:
                        moves.append((i, to, 0))

        elif pt in (BISHOP, ROOK, QUEEN):
            dirs = []
            if pt in (BISHOP, QUEEN):
                dirs += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
            if pt in (ROOK, QUEEN):
                dirs += [(1, 0), (-1, 0), (0, 1), (0, -1)]

            for df, dr in dirs:
                nf, nr = f + df, r + dr
                while 0 <= nf < 8 and 0 <= nr < 8:
                    to = nr * 8 + nf
                    target = board[to]
                    if target == 0:
                        if not noisy:
                            moves.append((i, to, 0))
                    else:
                        if target * side < 0 and abs(target) != KING:
                            moves.append((i, to, 0))
                        break
                    nf += df
                    nr += dr

        elif pt == KING:
            for df in (-1, 0, 1):
                for dr in (-1, 0, 1):
                    if df == 0 and dr == 0:
                        continue
                    nf, nr = f + df, r + dr
                    if 0 <= nf < 8 and 0 <= nr < 8:
                        to = nr * 8 + nf
                        target = board[to]
                        if target == 0:
                            if not noisy:
                                moves.append((i, to, 0))
                        elif target * side < 0 and abs(target) != KING:
                            moves.append((i, to, 0))

    return moves


def generate_legal(board, side: int, noisy: bool = False):
    pseudo = generate_pseudo(board, side, noisy)
    ksq = find_king(board, side)
    legal = []

    for m in pseudo:
        f, t, promo = m
        captured, piece = make_move(board, m)
        new_king = t if abs(piece) == KING else ksq
        if not is_attacked(board, new_king, -side):
            legal.append(m)
        unmake_move(board, m, captured, piece)

    return legal


def evaluate(board, perspective: int) -> int:
    score = 0
    nonpawn_material = 0

    pawns = {WHITE: [], BLACK: []}
    rooks = {WHITE: [], BLACK: []}
    bishops = {WHITE: 0, BLACK: 0}
    kings = {WHITE: -1, BLACK: -1}

    for i, p in enumerate(board):
        if not p:
            continue

        side = WHITE if p > 0 else BLACK
        pt = abs(p)
        f = i & 7
        r = i >> 3
        oriented_rank = r if side == WHITE else 7 - r
        center_dist = abs(f - 3.5) + abs(oriented_rank - 3.5)

        if pt != PAWN and pt != KING:
            nonpawn_material += VALUE[pt]

        bonus = 0
        if pt == PAWN:
            pawns[side].append(i)
            central = 3.5 - abs(f - 3.5)
            bonus = int(6 * oriented_rank + 2 * central)
            if oriented_rank == 5:
                bonus += 12
            elif oriented_rank == 6:
                bonus += 30
        elif pt == KNIGHT:
            bonus = int(38 - 11 * center_dist)
        elif pt == BISHOP:
            bishops[side] += 1
            bonus = int(30 - 6 * center_dist)
        elif pt == ROOK:
            rooks[side].append(i)
            bonus = 5 * oriented_rank
            if oriented_rank == 6:
                bonus += 18
        elif pt == QUEEN:
            bonus = int(10 - 3 * center_dist)
        elif pt == KING:
            kings[side] = i

        score += side * (VALUE[pt] + bonus)

    phase = min(1.0, nonpawn_material / 4200.0)

    # King placement: safe in middlegame, active in endgame.
    for side in (WHITE, BLACK):
        k = kings[side]
        if k >= 0:
            f = k & 7
            r = k >> 3
            oriented_rank = r if side == WHITE else 7 - r
            center_file_penalty = 3.5 - abs(f - 3.5)
            mg = -18 * oriented_rank - 12 * center_file_penalty
            eg = 60 - 14 * (abs(f - 3.5) + abs(r - 3.5))
            score += int(side * (phase * mg + (1.0 - phase) * eg))

    # Pawn structure, passed pawns, bishop pair.
    for side in (WHITE, BLACK):
        own = pawns[side]
        enemy = pawns[-side]
        file_counts = [0] * 8
        enemy_file_counts = [0] * 8

        for sq in own:
            file_counts[sq & 7] += 1
        for sq in enemy:
            enemy_file_counts[sq & 7] += 1

        for file_idx, cnt in enumerate(file_counts):
            if cnt > 1:
                score += side * (-12 * (cnt - 1))

        for sq in own:
            f = sq & 7
            r = sq >> 3
            oriented_rank = r if side == WHITE else 7 - r

            isolated = True
            if f > 0 and file_counts[f - 1] > 0:
                isolated = False
            if f < 7 and file_counts[f + 1] > 0:
                isolated = False
            if isolated:
                score += side * -8

            passed = True
            for ep in enemy:
                ef = ep & 7
                er = ep >> 3
                if abs(ef - f) <= 1:
                    if side == WHITE and er > r:
                        passed = False
                        break
                    if side == BLACK and er < r:
                        passed = False
                        break
            if passed:
                pp_bonus = 12 + 3 * oriented_rank * oriented_rank
                if oriented_rank >= 5:
                    pp_bonus += 25 * (oriented_rank - 4)
                score += side * pp_bonus

        if bishops[side] >= 2:
            score += side * 35

        for rq in rooks[side]:
            f = rq & 7
            if file_counts[f] == 0:
                score += side * (22 if enemy_file_counts[f] == 0 else 10)

        # Pawn shield near king in middlegame.
        k = kings[side]
        if k >= 0 and phase > 0.25:
            kf = k & 7
            kr = k >> 3
            direction = 1 if side == WHITE else -1
            shield = 0
            for df in (-1, 0, 1):
                nf = kf + df
                if not (0 <= nf < 8):
                    continue
                for step in (1, 2):
                    nr = kr + direction * step
                    if 0 <= nr < 8 and board[nr * 8 + nf] == side * PAWN:
                        shield += 1
                        break
            score += int(side * phase * (8 * shield - (18 if shield == 0 else 0)))

    # Help convert large material advantages in king-and-piece endings.
    if kings[WHITE] >= 0 and kings[BLACK] >= 0 and abs(score) > 600:
        winner = WHITE if score > 0 else BLACK
        loser_king = kings[-winner]
        winner_king = kings[winner]

        lf = loser_king & 7
        lr = loser_king >> 3
        wf = winner_king & 7
        wr = winner_king >> 3

        edge_bonus = int(18 * max(abs(lf - 3.5), abs(lr - 3.5)))
        king_distance = abs(lf - wf) + abs(lr - wr)
        mating_bonus = edge_bonus + max(0, 14 - 2 * king_distance)
        score += winner * mating_bonus

    return score * perspective


def is_capture_or_promo(board, m) -> bool:
    return board[m[1]] != 0 or m[2] != 0


def move_score(board, m, side: int, ply: int = 0, tt_move=None) -> int:
    if tt_move is not None and m == tt_move:
        return 10_000_000

    f, t, promo = m
    piece = abs(board[f])
    captured = abs(board[t]) if board[t] else 0
    score = 0

    if captured:
        score += 100_000 + 10 * VALUE[captured] - VALUE[piece]
    if promo:
        score += 90_000 + VALUE[promo]

    if ply < len(KILLERS):
        if m == KILLERS[ply][0]:
            score += 50_000
        elif m == KILLERS[ply][1]:
            score += 40_000

    score += HISTORY.get((side, f, t, promo), 0)

    # Quiet move preferences.
    tf = t & 7
    tr = t >> 3
    oriented_rank = tr if side == WHITE else 7 - tr
    center_dist = abs(tf - 3.5) + abs(oriented_rank - 3.5)

    if piece == PAWN:
        score += oriented_rank * 8 + int(4 * (3.5 - abs(tf - 3.5)))
    elif piece in (KNIGHT, BISHOP):
        score += int(35 - 7 * center_dist)
    elif piece == ROOK:
        score += oriented_rank * 3
    elif piece == QUEEN:
        score += int(10 - 2 * center_dist)

    return score


def qsearch(board, side: int, alpha: int, beta: int, ply: int, depth_left: int) -> int:
    check_time()

    in_check = is_in_check(board, side)

    if not in_check:
        stand = evaluate(board, side)
        if stand >= beta:
            return beta
        if stand > alpha:
            alpha = stand
        if depth_left <= 0:
            return alpha
        moves = generate_legal(board, side, noisy=True)
    else:
        if depth_left <= -2:
            return evaluate(board, side) - 50
        moves = generate_legal(board, side, noisy=False)
        if not moves:
            return -MATE + ply

    moves.sort(key=lambda mv: move_score(board, mv, side, ply), reverse=True)

    for m in moves:
        captured, piece = make_move(board, m)
        try:
            score = -qsearch(board, -side, -beta, -alpha, ply + 1, depth_left - 1)
        finally:
            unmake_move(board, m, captured, piece)

        if score >= beta:
            return beta
        if score > alpha:
            alpha = score

    return alpha


def negamax(board, side: int, depth: int, alpha: int, beta: int, ply: int) -> int:
    check_time()

    if depth <= 0:
        return qsearch(board, side, alpha, beta, ply, 6)

    alpha_orig = alpha
    beta_orig = beta
    tt_move = None
    key = None

    if depth >= 2:
        key = (side, tuple(board))
        entry = TT.get(key)
        if entry is not None:
            entry_depth, entry_value, entry_flag, entry_move = entry
            tt_move = entry_move
            if entry_depth >= depth:
                if entry_flag == 0:
                    return entry_value
                elif entry_flag == 1:
                    alpha = max(alpha, entry_value)
                else:
                    beta = min(beta, entry_value)
                if alpha >= beta:
                    return entry_value

    moves = generate_legal(board, side, noisy=False)

    if not moves:
        if is_in_check(board, side):
            return -MATE + ply
        return 0

    moves.sort(key=lambda mv: move_score(board, mv, side, ply, tt_move), reverse=True)

    best_value = -INF
    best_move = moves[0]

    for m in moves:
        captured, piece = make_move(board, m)
        try:
            score = -negamax(board, -side, depth - 1, -beta, -alpha, ply + 1)
        finally:
            unmake_move(board, m, captured, piece)

        if score > best_value:
            best_value = score
            best_move = m

        if score > alpha:
            alpha = score

        if alpha >= beta:
            if not captured and not m[2]:
                if ply < len(KILLERS) and KILLERS[ply][0] != m:
                    KILLERS[ply][1] = KILLERS[ply][0]
                    KILLERS[ply][0] = m
                hkey = (side, m[0], m[1], m[2])
                HISTORY[hkey] = HISTORY.get(hkey, 0) + depth * depth
            break

    if key is not None:
        if best_value <= alpha_orig:
            flag = 2  # upper bound
        elif best_value >= beta_orig:
            flag = 1  # lower bound
        else:
            flag = 0  # exact

        if len(TT) < 200000:
            TT[key] = (depth, best_value, flag, best_move)

    return best_value


def quick_select(board, side: int, moves):
    best = moves[0]
    best_score = -INF

    ordered = sorted(moves, key=lambda mv: move_score(board, mv, side), reverse=True)

    for m in ordered:
        captured, piece = make_move(board, m)

        if is_in_check(board, -side):
            replies = generate_legal(board, -side, noisy=False)
            if not replies:
                unmake_move(board, m, captured, piece)
                return m, MATE

        score = evaluate(board, side)
        unmake_move(board, m, captured, piece)

        score += move_score(board, m, side) // 1000

        if score > best_score:
            best_score = score
            best = m

    return best, best_score


def choose_move(board, side: int) -> str:
    global DEADLINE, NODES, TT, KILLERS, HISTORY

    DEADLINE = time.perf_counter() + 0.85
    NODES = 0
    TT = {}
    KILLERS = [[None, None] for _ in range(96)]
    HISTORY = {}

    legal = generate_legal(board, side, noisy=False)
    if not legal:
        return "0000"
    if len(legal) == 1:
        return move_to_uci(legal[0])

    best, best_score = quick_select(board, side, legal)
    if best_score >= MATE:
        return move_to_uci(best)

    piece_count = sum(1 for p in board if p)
    if piece_count <= 5:
        max_depth = 12
    elif piece_count <= 8:
        max_depth = 9
    elif piece_count <= 12:
        max_depth = 7
    elif piece_count <= 22:
        max_depth = 5
    else:
        max_depth = 4

    root_moves = sorted(legal, key=lambda mv: move_score(board, mv, side), reverse=True)
    if best in root_moves:
        root_moves.remove(best)
        root_moves.insert(0, best)

    depth = 1

    try:
        while depth <= max_depth and time.perf_counter() < DEADLINE:
            alpha = -INF
            beta = INF
            current_best = best
            current_best_score = -INF
            root_scores = {}

            for m in root_moves:
                captured, piece = make_move(board, m)
                try:
                    score = -negamax(board, -side, depth - 1, -beta, -alpha, 1)
                finally:
                    unmake_move(board, m, captured, piece)

                root_scores[m] = score

                if score > current_best_score:
                    current_best_score = score
                    current_best = m

                if score > alpha:
                    alpha = score

            best = current_best
            best_score = current_best_score

            root_moves.sort(
                key=lambda mv: (
                    1 if mv == best else 0,
                    root_scores.get(mv, -INF),
                    move_score(board, mv, side)
                ),
                reverse=True
            )

            if best_score > MATE - 1000:
                break

            depth += 1

    except SearchTimeout:
        pass

    return move_to_uci(best)


def policy(pieces: dict[str, str], to_play: str) -> str:
    board = [0] * 64

    try:
        for sq, pc in pieces.items():
            if len(sq) != 2 or len(pc) != 2:
                continue
            idx = sq_to_idx(sq)
            color = WHITE if pc[0] == "w" else BLACK
            pt = PIECE_TO_INT.get(pc[1])
            if pt is not None and 0 <= idx < 64:
                board[idx] = color * pt

        side = WHITE if to_play and to_play[0].lower() == "w" else BLACK
        return choose_move(board, side)

    except Exception:
        # Emergency fallback: return the first strictly legal normal move if possible.
        try:
            side = WHITE if to_play and to_play[0].lower() == "w" else BLACK
            legal = generate_legal(board, side, noisy=False)
            if legal:
                return move_to_uci(legal[0])
        except Exception:
            pass
        return "0000"
