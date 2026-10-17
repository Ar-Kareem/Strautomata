
from time import perf_counter

FILES = "abcdefgh"
PIECE_VALUE = {"P": 100, "N": 320, "B": 330, "R": 500, "Q": 900, "K": 0}
PROMOS = ("q", "r", "b", "n")
MATE_SCORE = 100000

KNIGHT_DELTAS = (
    (1, 2), (2, 1), (2, -1), (1, -2),
    (-1, -2), (-2, -1), (-2, 1), (-1, 2),
)
KING_DELTAS = (
    (1, 0), (1, 1), (0, 1), (-1, 1),
    (-1, 0), (-1, -1), (0, -1), (1, -1),
)
BISHOP_DIRS = ((1, 1), (1, -1), (-1, 1), (-1, -1))
ROOK_DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
QUEEN_DIRS = BISHOP_DIRS + ROOK_DIRS

KNIGHT_MOVES = [[] for _ in range(64)]
KING_MOVES = [[] for _ in range(64)]
for sq in range(64):
    f, r = sq % 8, sq // 8
    for df, dr in KNIGHT_DELTAS:
        nf, nr = f + df, r + dr
        if 0 <= nf < 8 and 0 <= nr < 8:
            KNIGHT_MOVES[sq].append(nr * 8 + nf)
    for df, dr in KING_DELTAS:
        nf, nr = f + df, r + dr
        if 0 <= nf < 8 and 0 <= nr < 8:
            KING_MOVES[sq].append(nr * 8 + nf)

DEADLINE = 0.0


def sq_to_idx(s: str) -> int:
    return (ord(s[1]) - 49) * 8 + (ord(s[0]) - 97)


def idx_to_sq(i: int) -> str:
    return chr(97 + (i % 8)) + chr(49 + (i // 8))


def move_to_uci(move):
    fr, to, promo = move
    if promo:
        return idx_to_sq(fr) + idx_to_sq(to) + promo
    return idx_to_sq(fr) + idx_to_sq(to)


def other(color: str) -> str:
    return "b" if color == "w" else "w"


def find_king(board, color):
    target = color + "K"
    for sq, p in board.items():
        if p == target:
            return sq
    return None


def is_attacked(board, sq, by_color):
    f, r = sq % 8, sq // 8

    # Pawn attacks
    if by_color == "w":
        if f > 0:
            s = sq - 9
            if s in board and board[s] == "wP":
                return True
        if f < 7:
            s = sq - 7
            if s in board and board[s] == "wP":
                return True
    else:
        if f > 0:
            s = sq + 7
            if s in board and board[s] == "bP":
                return True
        if f < 7:
            s = sq + 9
            if s in board and board[s] == "bP":
                return True

    # Knight attacks
    attacker_knight = by_color + "N"
    for s in KNIGHT_MOVES[sq]:
        if board.get(s) == attacker_knight:
            return True

    # King attacks
    attacker_king = by_color + "K"
    for s in KING_MOVES[sq]:
        if board.get(s) == attacker_king:
            return True

    # Bishop / Queen diagonals
    for df, dr in BISHOP_DIRS:
        nf, nr = f + df, r + dr
        while 0 <= nf < 8 and 0 <= nr < 8:
            s = nr * 8 + nf
            p = board.get(s)
            if p:
                if p[0] == by_color and (p[1] == "B" or p[1] == "Q"):
                    return True
                break
            nf += df
            nr += dr

    # Rook / Queen orthogonals
    for df, dr in ROOK_DIRS:
        nf, nr = f + df, r + dr
        while 0 <= nf < 8 and 0 <= nr < 8:
            s = nr * 8 + nf
            p = board.get(s)
            if p:
                if p[0] == by_color and (p[1] == "R" or p[1] == "Q"):
                    return True
                break
            nf += df
            nr += dr

    return False


def in_check(board, color):
    ksq = find_king(board, color)
    if ksq is None:
        return True
    return is_attacked(board, ksq, other(color))


def make_move(board, move):
    fr, to, promo = move
    p = board[fr]
    nb = board.copy()
    nb.pop(fr, None)
    nb.pop(to, None)

    # Castling rook move
    if p[1] == "K" and abs(to - fr) == 2:
        if to > fr:  # kingside
            rook_from = fr + 3
            rook_to = fr + 1
        else:  # queenside
            rook_from = fr - 4
            rook_to = fr - 1
        rook = nb.pop(rook_from, None)
        if rook:
            nb[rook_to] = rook

    if promo:
        nb[to] = p[0] + promo.upper()
    else:
        nb[to] = p
    return nb


def generate_pseudo_moves(board, color):
    moves = []
    enemy = other(color)

    for fr, p in board.items():
        if p[0] != color:
            continue
        piece = p[1]
        f, r = fr % 8, fr // 8

        if piece == "P":
            if color == "w":
                one = fr + 8
                if r < 7 and one not in board:
                    if r == 6:
                        for pr in PROMOS:
                            moves.append((fr, one, pr))
                    else:
                        moves.append((fr, one, None))
                        if r == 1:
                            two = fr + 16
                            if two not in board:
                                moves.append((fr, two, None))
                if f > 0:
                    to = fr + 7
                    cap = board.get(to)
                    if cap and cap[0] == enemy:
                        if r == 6:
                            for pr in PROMOS:
                                moves.append((fr, to, pr))
                        else:
                            moves.append((fr, to, None))
                if f < 7:
                    to = fr + 9
                    cap = board.get(to)
                    if cap and cap[0] == enemy:
                        if r == 6:
                            for pr in PROMOS:
                                moves.append((fr, to, pr))
                        else:
                            moves.append((fr, to, None))
            else:
                one = fr - 8
                if r > 0 and one not in board:
                    if r == 1:
                        for pr in PROMOS:
                            moves.append((fr, one, pr))
                    else:
                        moves.append((fr, one, None))
                        if r == 6:
                            two = fr - 16
                            if two not in board:
                                moves.append((fr, two, None))
                if f > 0:
                    to = fr - 9
                    cap = board.get(to)
                    if cap and cap[0] == enemy:
                        if r == 1:
                            for pr in PROMOS:
                                moves.append((fr, to, pr))
                        else:
                            moves.append((fr, to, None))
                if f < 7:
                    to = fr - 7
                    cap = board.get(to)
                    if cap and cap[0] == enemy:
                        if r == 1:
                            for pr in PROMOS:
                                moves.append((fr, to, pr))
                        else:
                            moves.append((fr, to, None))

        elif piece == "N":
            for to in KNIGHT_MOVES[fr]:
                cap = board.get(to)
                if not cap or cap[0] == enemy:
                    moves.append((fr, to, None))

        elif piece == "B":
            for df, dr in BISHOP_DIRS:
                nf, nr = f + df, r + dr
                while 0 <= nf < 8 and 0 <= nr < 8:
                    to = nr * 8 + nf
                    cap = board.get(to)
                    if not cap:
                        moves.append((fr, to, None))
                    else:
                        if cap[0] == enemy:
                            moves.append((fr, to, None))
                        break
                    nf += df
                    nr += dr

        elif piece == "R":
            for df, dr in ROOK_DIRS:
                nf, nr = f + df, r + dr
                while 0 <= nf < 8 and 0 <= nr < 8:
                    to = nr * 8 + nf
                    cap = board.get(to)
                    if not cap:
                        moves.append((fr, to, None))
                    else:
                        if cap[0] == enemy:
                            moves.append((fr, to, None))
                        break
                    nf += df
                    nr += dr

        elif piece == "Q":
            for df, dr in QUEEN_DIRS:
                nf, nr = f + df, r + dr
                while 0 <= nf < 8 and 0 <= nr < 8:
                    to = nr * 8 + nf
                    cap = board.get(to)
                    if not cap:
                        moves.append((fr, to, None))
                    else:
                        if cap[0] == enemy:
                            moves.append((fr, to, None))
                        break
                    nf += df
                    nr += dr

        elif piece == "K":
            for to in KING_MOVES[fr]:
                cap = board.get(to)
                if not cap or cap[0] == enemy:
                    moves.append((fr, to, None))

            # Conservative inferred castling
            if color == "w" and fr == 4 and board.get(4) == "wK":
                # O-O
                if board.get(7) == "wR" and 5 not in board and 6 not in board:
                    if not is_attacked(board, 4, "b") and not is_attacked(board, 5, "b") and not is_attacked(board, 6, "b"):
                        moves.append((4, 6, None))
                # O-O-O
                if board.get(0) == "wR" and 1 not in board and 2 not in board and 3 not in board:
                    if not is_attacked(board, 4, "b") and not is_attacked(board, 3, "b") and not is_attacked(board, 2, "b"):
                        moves.append((4, 2, None))
            elif color == "b" and fr == 60 and board.get(60) == "bK":
                # O-O
                if board.get(63) == "bR" and 61 not in board and 62 not in board:
                    if not is_attacked(board, 60, "w") and not is_attacked(board, 61, "w") and not is_attacked(board, 62, "w"):
                        moves.append((60, 62, None))
                # O-O-O
                if board.get(56) == "bR" and 57 not in board and 58 not in board and 59 not in board:
                    if not is_attacked(board, 60, "w") and not is_attacked(board, 59, "w") and not is_attacked(board, 58, "w"):
                        moves.append((60, 58, None))
    return moves


def generate_legal_moves(board, color):
    legal = []
    for mv in generate_pseudo_moves(board, color):
        nb = make_move(board, mv)
        if not in_check(nb, color):
            legal.append(mv)
    return legal


def tactical_moves(board, color):
    tacts = []
    for mv in generate_pseudo_moves(board, color):
        fr, to, promo = mv
        cap = board.get(to)
        if cap or promo:
            nb = make_move(board, mv)
            if not in_check(nb, color):
                tacts.append(mv)
    return tacts


def score_move(board, move):
    fr, to, promo = move
    mover = board[fr]
    victim = board.get(to)
    score = 0
    if victim:
        score += 10 * PIECE_VALUE[victim[1]] - PIECE_VALUE[mover[1]]
    if promo:
        score += 800 + PIECE_VALUE[promo.upper()]
    if mover[1] == "K" and abs(to - fr) == 2:
        score += 50
    # Centralizing / advancing nudges
    tf, tr = to % 8, to // 8
    ff, frk = fr % 8, fr // 8
    score += int((3.5 - abs(tf - 3.5) + 3.5 - abs(tr - 3.5)) * 2)
    score -= int((3.5 - abs(ff - 3.5) + 3.5 - abs(frk - 3.5)))
    return score


def ordered_moves(board, moves):
    return sorted(moves, key=lambda mv: score_move(board, mv), reverse=True)


def eval_piece_square(piece_type, color, f, r, endgame):
    rr = r if color == "w" else 7 - r
    center = (3.5 - abs(f - 3.5)) + (3.5 - abs(rr - 3.5))

    if piece_type == "P":
        return rr * 10 + int((3.5 - abs(f - 3.5)) * 2)
    if piece_type == "N":
        return int(center * 8) - (8 if f in (0, 7) or rr in (0, 7) else 0)
    if piece_type == "B":
        return int(center * 5) + rr * 2
    if piece_type == "R":
        bonus = rr * 2
        if rr == 6:
            bonus += 20
        return bonus
    if piece_type == "Q":
        return int(center * 3)
    if piece_type == "K":
        if endgame:
            return int(center * 8)
        bonus = -rr * 10 - int((3.5 - abs(f - 3.5)) * 5)
        if rr == 0 and f in (1, 6):
            bonus += 25
        return bonus
    return 0


def evaluate(board, color):
    score = 0
    bishop_count_w = 0
    bishop_count_b = 0
    nonpawn_material = 0

    for p in board.values():
        if p[1] in ("N", "B", "R", "Q"):
            nonpawn_material += PIECE_VALUE[p[1]]

    endgame = nonpawn_material <= 2600

    for sq, p in board.items():
        c, t = p[0], p[1]
        f, r = sq % 8, sq // 8
        val = PIECE_VALUE[t] + eval_piece_square(t, c, f, r, endgame)
        if t == "B":
            if c == "w":
                bishop_count_w += 1
            else:
                bishop_count_b += 1
        if c == "w":
            score += val
        else:
            score -= val

    if bishop_count_w >= 2:
        score += 30
    if bishop_count_b >= 2:
        score -= 30

    # Mild king-in-check penalty to encourage safety
    if in_check(board, "w"):
        score -= 25
    if in_check(board, "b"):
        score += 25

    return score if color == "w" else -score


def quiescence(board, color, alpha, beta, ply):
    if perf_counter() >= DEADLINE:
        return evaluate(board, color)

    legal_tacts = tactical_moves(board, color)
    if not legal_tacts and in_check(board, color):
        return -MATE_SCORE + ply

    stand = evaluate(board, color)
    if stand >= beta:
        return beta
    if stand > alpha:
        alpha = stand

    for mv in ordered_moves(board, legal_tacts):
        nb = make_move(board, mv)
        score = -quiescence(nb, other(color), -beta, -alpha, ply + 1)
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
    return alpha


def negamax(board, color, depth, alpha, beta, ply):
    if perf_counter() >= DEADLINE:
        return evaluate(board, color)

    legal = generate_legal_moves(board, color)

    if not legal:
        if in_check(board, color):
            return -MATE_SCORE + ply
        return 0

    if depth <= 0:
        if in_check(board, color):
            depth = 1
        else:
            return quiescence(board, color, alpha, beta, ply)

    best = -10**9
    for mv in ordered_moves(board, legal):
        nb = make_move(board, mv)
        score = -negamax(nb, other(color), depth - 1, -beta, -alpha, ply + 1)
        if score > best:
            best = score
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
        if perf_counter() >= DEADLINE:
            break
    return best


def choose_depth(board, legal_count):
    piece_count = len(board)
    if piece_count <= 8 or legal_count <= 8:
        return 4
    if piece_count >= 26 or legal_count >= 36:
        return 2
    return 3


def policy(pieces: dict[str, str], to_play: str) -> str:
    global DEADLINE
    DEADLINE = perf_counter() + 0.95

    color = "w" if to_play == "white" else "b"
    board = {sq_to_idx(sq): piece for sq, piece in pieces.items()}

    legal = generate_legal_moves(board, color)
    if not legal:
        # Should not happen in non-terminal arena states, but provide a deterministic fallback.
        pseudo = generate_pseudo_moves(board, color)
        if pseudo:
            return move_to_uci(pseudo[0])
        return "a1a1"

    ordered = ordered_moves(board, legal)

    # Immediate mate / strong tactical shortcut
    for mv in ordered:
        nb = make_move(board, mv)
        opp_legal = generate_legal_moves(nb, other(color))
        if not opp_legal and in_check(nb, other(color)):
            return move_to_uci(mv)

    depth = choose_depth(board, len(legal))
    best_move = ordered[0]
    best_score = -10**9
    alpha = -10**9
    beta = 10**9

    for mv in ordered:
        if perf_counter() >= DEADLINE:
            break
        nb = make_move(board, mv)
        score = -negamax(nb, other(color), depth - 1, -beta, -alpha, 1)
        if score > best_score:
            best_score = score
            best_move = mv
        if score > alpha:
            alpha = score

    return move_to_uci(best_move)
