
import time

FILES = "abcdefgh"
PIECE_VALUES = {
    "P": 100,
    "N": 320,
    "B": 330,
    "R": 500,
    "Q": 900,
    "K": 0,
}

MATE_SCORE = 100000
INF = 10**9

KNIGHT_MOVES = [[] for _ in range(64)]
KING_MOVES = [[] for _ in range(64)]
for sq in range(64):
    f = sq & 7
    r = sq >> 3
    for df, dr in [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]:
        nf, nr = f + df, r + dr
        if 0 <= nf < 8 and 0 <= nr < 8:
            KNIGHT_MOVES[sq].append(nr * 8 + nf)
    for df, dr in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
        nf, nr = f + df, r + dr
        if 0 <= nf < 8 and 0 <= nr < 8:
            KING_MOVES[sq].append(nr * 8 + nf)

_deadline = 0.0
_nodes = 0


def square_to_idx(s):
    return (ord(s[1]) - 49) * 8 + (ord(s[0]) - 97)


def idx_to_square(i):
    return FILES[i & 7] + str((i >> 3) + 1)


def move_to_uci(move):
    fr, to, promo = move
    if promo:
        return idx_to_square(fr) + idx_to_square(to) + promo
    return idx_to_square(fr) + idx_to_square(to)


def opposite(color):
    return "b" if color == "w" else "w"


def center_bonus(sq):
    f = sq & 7
    r = sq >> 3
    return int((3.5 - abs(f - 3.5) + 3.5 - abs(r - 3.5)) * 2)


def find_king(board, color):
    target = color + "K"
    for i, p in enumerate(board):
        if p == target:
            return i
    return -1


def is_attacked(board, sq, by_color):
    f = sq & 7
    r = sq >> 3

    if by_color == "w":
        if r > 0:
            if f > 0 and board[sq - 9] == "wP":
                return True
            if f < 7 and board[sq - 7] == "wP":
                return True
    else:
        if r < 7:
            if f > 0 and board[sq + 7] == "bP":
                return True
            if f < 7 and board[sq + 9] == "bP":
                return True

    for nsq in KNIGHT_MOVES[sq]:
        p = board[nsq]
        if p and p[0] == by_color and p[1] == "N":
            return True

    for df, dr in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
        nf, nr = f + df, r + dr
        while 0 <= nf < 8 and 0 <= nr < 8:
            tsq = nr * 8 + nf
            p = board[tsq]
            if p:
                if p[0] == by_color and (p[1] == "R" or p[1] == "Q"):
                    return True
                break
            nf += df
            nr += dr

    for df, dr in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
        nf, nr = f + df, r + dr
        while 0 <= nf < 8 and 0 <= nr < 8:
            tsq = nr * 8 + nf
            p = board[tsq]
            if p:
                if p[0] == by_color and (p[1] == "B" or p[1] == "Q"):
                    return True
                break
            nf += df
            nr += dr

    for nsq in KING_MOVES[sq]:
        p = board[nsq]
        if p and p[0] == by_color and p[1] == "K":
            return True

    return False


def in_check(board, color):
    ks = find_king(board, color)
    if ks == -1:
        return True
    return is_attacked(board, ks, opposite(color))


def make_move(board, move):
    fr, to, promo = move
    piece = board[fr]
    new_board = board[:]
    new_board[fr] = None
    if promo:
        new_board[to] = piece[0] + promo.upper()
    else:
        new_board[to] = piece
    return new_board


def generate_pseudo_moves(board, color, captures_only=False):
    opp = opposite(color)
    moves = []

    for sq, piece in enumerate(board):
        if not piece or piece[0] != color:
            continue

        pt = piece[1]
        f = sq & 7
        r = sq >> 3

        if pt == "P":
            if color == "w":
                one = sq + 8
                if not captures_only:
                    if r < 7 and board[one] is None:
                        if r == 6:
                            for promo in "qrbn":
                                moves.append((sq, one, promo))
                        else:
                            moves.append((sq, one, None))
                            if r == 1 and board[sq + 16] is None:
                                moves.append((sq, sq + 16, None))
                else:
                    if r == 6 and board[one] is None:
                        for promo in "qrbn":
                            moves.append((sq, one, promo))

                if f > 0:
                    to = sq + 7
                    target = board[to]
                    if target and target[0] == opp and target[1] != "K":
                        if r == 6:
                            for promo in "qrbn":
                                moves.append((sq, to, promo))
                        else:
                            moves.append((sq, to, None))
                if f < 7:
                    to = sq + 9
                    target = board[to]
                    if target and target[0] == opp and target[1] != "K":
                        if r == 6:
                            for promo in "qrbn":
                                moves.append((sq, to, promo))
                        else:
                            moves.append((sq, to, None))
            else:
                one = sq - 8
                if not captures_only:
                    if r > 0 and board[one] is None:
                        if r == 1:
                            for promo in "qrbn":
                                moves.append((sq, one, promo))
                        else:
                            moves.append((sq, one, None))
                            if r == 6 and board[sq - 16] is None:
                                moves.append((sq, sq - 16, None))
                else:
                    if r == 1 and board[one] is None:
                        for promo in "qrbn":
                            moves.append((sq, one, promo))

                if f > 0:
                    to = sq - 9
                    target = board[to]
                    if target and target[0] == opp and target[1] != "K":
                        if r == 1:
                            for promo in "qrbn":
                                moves.append((sq, to, promo))
                        else:
                            moves.append((sq, to, None))
                if f < 7:
                    to = sq - 7
                    target = board[to]
                    if target and target[0] == opp and target[1] != "K":
                        if r == 1:
                            for promo in "qrbn":
                                moves.append((sq, to, promo))
                        else:
                            moves.append((sq, to, None))

        elif pt == "N":
            for to in KNIGHT_MOVES[sq]:
                target = board[to]
                if target is None:
                    if not captures_only:
                        moves.append((sq, to, None))
                elif target[0] == opp and target[1] != "K":
                    moves.append((sq, to, None))

        elif pt == "B":
            for df, dr in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
                nf, nr = f + df, r + dr
                while 0 <= nf < 8 and 0 <= nr < 8:
                    to = nr * 8 + nf
                    target = board[to]
                    if target is None:
                        if not captures_only:
                            moves.append((sq, to, None))
                    else:
                        if target[0] == opp and target[1] != "K":
                            moves.append((sq, to, None))
                        break
                    nf += df
                    nr += dr

        elif pt == "R":
            for df, dr in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nf, nr = f + df, r + dr
                while 0 <= nf < 8 and 0 <= nr < 8:
                    to = nr * 8 + nf
                    target = board[to]
                    if target is None:
                        if not captures_only:
                            moves.append((sq, to, None))
                    else:
                        if target[0] == opp and target[1] != "K":
                            moves.append((sq, to, None))
                        break
                    nf += df
                    nr += dr

        elif pt == "Q":
            for df, dr in [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
                nf, nr = f + df, r + dr
                while 0 <= nf < 8 and 0 <= nr < 8:
                    to = nr * 8 + nf
                    target = board[to]
                    if target is None:
                        if not captures_only:
                            moves.append((sq, to, None))
                    else:
                        if target[0] == opp and target[1] != "K":
                            moves.append((sq, to, None))
                        break
                    nf += df
                    nr += dr

        elif pt == "K":
            for to in KING_MOVES[sq]:
                target = board[to]
                if target is None:
                    if not captures_only:
                        moves.append((sq, to, None))
                elif target[0] == opp and target[1] != "K":
                    moves.append((sq, to, None))

    return moves


def generate_legal_moves(board, color, captures_only=False):
    legal = []
    for mv in generate_pseudo_moves(board, color, captures_only):
        nb = make_move(board, mv)
        if not in_check(nb, color):
            legal.append(mv)
    return legal


def move_order_score(board, move):
    fr, to, promo = move
    mover = board[fr]
    target = board[to]
    score = 0
    if target:
        score += 10 * PIECE_VALUES[target[1]] - PIECE_VALUES[mover[1]]
    if promo:
        score += PIECE_VALUES[promo.upper()] + 200
    if mover[1] == "P" and target:
        score += 20
    if mover[1] == "K":
        score -= 10
    return score


def passed_pawn_bonus(board, sq, color):
    f = sq & 7
    r = sq >> 3
    enemy = opposite(color) + "P"
    if color == "w":
        for ef in (f - 1, f, f + 1):
            if 0 <= ef < 8:
                for rr in range(r + 1, 8):
                    if board[rr * 8 + ef] == enemy:
                        return 0
        return 20 + r * 8
    else:
        for ef in (f - 1, f, f + 1):
            if 0 <= ef < 8:
                for rr in range(r - 1, -1, -1):
                    if board[rr * 8 + ef] == enemy:
                        return 0
        return 20 + (7 - r) * 8


def king_eval(board, sq, color, phase):
    if sq == -1:
        return -50000
    f = sq & 7
    r = sq >> 3
    c = center_bonus(sq)
    score = 0
    if phase >= 8:
        score -= c * 3
        front = r + 1 if color == "w" else r - 1
        if 0 <= front < 8:
            for nf in (f - 1, f, f + 1):
                if 0 <= nf < 8 and board[front * 8 + nf] == color + "P":
                    score += 14
    else:
        score += c * 2
    return score


def evaluate(board, color):
    white_score = 0
    black_score = 0
    white_bishops = 0
    black_bishops = 0
    white_king = -1
    black_king = -1
    phase = 0

    for sq, p in enumerate(board):
        if not p:
            continue
        pc = p[0]
        pt = p[1]
        val = PIECE_VALUES[pt]
        score = val

        if pt == "P":
            adv = (sq >> 3) if pc == "w" else (7 - (sq >> 3))
            score += adv * 10
            score += center_bonus(sq)
            score += passed_pawn_bonus(board, sq, pc)
        elif pt == "N":
            score += center_bonus(sq) * 6
            phase += 1
        elif pt == "B":
            score += center_bonus(sq) * 4
            phase += 1
            if pc == "w":
                white_bishops += 1
            else:
                black_bishops += 1
        elif pt == "R":
            score += center_bonus(sq) * 2
            rank = sq >> 3
            if (pc == "w" and rank == 6) or (pc == "b" and rank == 1):
                score += 25
            phase += 2
        elif pt == "Q":
            score += center_bonus(sq)
            phase += 4
        elif pt == "K":
            if pc == "w":
                white_king = sq
            else:
                black_king = sq

        if pc == "w":
            white_score += score
        else:
            black_score += score

    if white_bishops >= 2:
        white_score += 30
    if black_bishops >= 2:
        black_score += 30

    white_score += king_eval(board, white_king, "w", phase)
    black_score += king_eval(board, black_king, "b", phase)

    score = white_score - black_score
    return score if color == "w" else -score


def time_check():
    global _nodes
    _nodes += 1
    if (_nodes & 511) == 0 and time.perf_counter() > _deadline:
        raise TimeoutError


def quiescence(board, color, alpha, beta, ply):
    time_check()

    if in_check(board, color):
        moves = generate_legal_moves(board, color, captures_only=False)
        if not moves:
            return -MATE_SCORE + ply
        moves.sort(key=lambda m: move_order_score(board, m), reverse=True)
        best = -INF
        opp = opposite(color)
        for mv in moves:
            score = -quiescence(make_move(board, mv), opp, -beta, -alpha, ply + 1)
            if score > best:
                best = score
            if score > alpha:
                alpha = score
            if alpha >= beta:
                break
        return best

    stand = evaluate(board, color)
    if stand >= beta:
        return beta
    if stand > alpha:
        alpha = stand

    moves = generate_legal_moves(board, color, captures_only=True)
    if not moves:
        return stand

    moves.sort(key=lambda m: move_order_score(board, m), reverse=True)
    opp = opposite(color)
    for mv in moves:
        score = -quiescence(make_move(board, mv), opp, -beta, -alpha, ply + 1)
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
    return alpha


def negamax(board, color, depth, alpha, beta, ply):
    time_check()

    if depth == 0:
        return quiescence(board, color, alpha, beta, ply)

    moves = generate_legal_moves(board, color, captures_only=False)
    if not moves:
        if in_check(board, color):
            return -MATE_SCORE + ply
        return 0

    moves.sort(key=lambda m: move_order_score(board, m), reverse=True)

    best = -INF
    opp = opposite(color)

    for mv in moves:
        score = -negamax(make_move(board, mv), opp, depth - 1, -beta, -alpha, ply + 1)
        if score > best:
            best = score
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break

    return best


def policy(pieces: dict[str, str], to_play: str) -> str:
    global _deadline, _nodes
    board = [None] * 64
    for sq, piece in pieces.items():
        board[square_to_idx(sq)] = piece

    color = "w" if to_play.startswith("w") else "b"
    legal_moves = generate_legal_moves(board, color, captures_only=False)

    if not legal_moves:
        pseudo = generate_pseudo_moves(board, color, captures_only=False)
        if pseudo:
            return move_to_uci(pseudo[0])
        return "a1a1"

    legal_moves.sort(key=lambda m: move_order_score(board, m), reverse=True)
    best_move = legal_moves[0]

    piece_count = sum(1 for p in board if p)
    if piece_count <= 8:
        max_depth = 5
    elif piece_count <= 14:
        max_depth = 4
    else:
        max_depth = 4

    start = time.perf_counter()
    _deadline = start + 0.95
    _nodes = 0

    try:
        root_moves = legal_moves[:]
        for depth in range(1, max_depth + 1):
            best_score = -INF
            current_best = best_move

            root_moves.sort(
                key=lambda m: move_order_score(board, m) + (1000000 if m == best_move else 0),
                reverse=True,
            )

            alpha = -INF
            beta = INF
            opp = opposite(color)

            for mv in root_moves:
                score = -negamax(make_move(board, mv), opp, depth - 1, -beta, -alpha, 1)
                if score > best_score:
                    best_score = score
                    current_best = mv
                if score > alpha:
                    alpha = score

            best_move = current_best

    except TimeoutError:
        pass

    return move_to_uci(best_move)
