
from __future__ import annotations
from time import perf_counter

FILES = "abcdefgh"
RANKS = "12345678"

INF = 10**9
MATE = 1_000_000
TIME_BUDGET = 0.82
MAX_Q_PLY = 18

PIECE_VALUES = {
    "P": 100,
    "N": 320,
    "B": 330,
    "R": 500,
    "Q": 900,
    "K": 0,
}

PHASE_VALUES = {
    "P": 0,
    "N": 1,
    "B": 1,
    "R": 2,
    "Q": 4,
    "K": 0,
}

OPP = {"w": "b", "b": "w"}
PROMOS = ("q", "r", "b", "n")

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

MIRROR = [((7 - (i >> 3)) << 3) + (i & 7) for i in range(64)]
CENTER_SCORE = [
    14 - (abs((i & 7) * 2 - 7) + abs((i >> 3) * 2 - 7))
    for i in range(64)
]
PASS_BONUS = (0, 0, 8, 18, 35, 65, 110, 0)


def _tbl(rows):
    out = []
    for row in reversed(rows):
        out.extend(row)
    return out


PAWN_MG = _tbl((
    (0, 0, 0, 0, 0, 0, 0, 0),
    (50, 50, 50, 50, 50, 50, 50, 50),
    (10, 10, 20, 30, 30, 20, 10, 10),
    (5, 5, 10, 25, 25, 10, 5, 5),
    (0, 0, 0, 20, 20, 0, 0, 0),
    (5, -5, -10, 0, 0, -10, -5, 5),
    (5, 10, 10, -20, -20, 10, 10, 5),
    (0, 0, 0, 0, 0, 0, 0, 0),
))

PAWN_EG = _tbl((
    (0, 0, 0, 0, 0, 0, 0, 0),
    (90, 90, 90, 90, 90, 90, 90, 90),
    (50, 50, 55, 60, 60, 55, 50, 50),
    (30, 30, 35, 45, 45, 35, 30, 30),
    (15, 15, 20, 30, 30, 20, 15, 15),
    (5, 5, 10, 15, 15, 10, 5, 5),
    (0, 0, 0, 0, 0, 0, 0, 0),
    (0, 0, 0, 0, 0, 0, 0, 0),
))

KNIGHT_PST = _tbl((
    (-50, -40, -30, -30, -30, -30, -40, -50),
    (-40, -20, 0, 5, 5, 0, -20, -40),
    (-30, 5, 10, 15, 15, 10, 5, -30),
    (-30, 0, 15, 20, 20, 15, 0, -30),
    (-30, 5, 15, 20, 20, 15, 5, -30),
    (-30, 0, 10, 15, 15, 10, 0, -30),
    (-40, -20, 0, 0, 0, 0, -20, -40),
    (-50, -40, -30, -30, -30, -30, -40, -50),
))

BISHOP_PST = _tbl((
    (-20, -10, -10, -10, -10, -10, -10, -20),
    (-10, 5, 0, 0, 0, 0, 5, -10),
    (-10, 10, 10, 10, 10, 10, 10, -10),
    (-10, 0, 10, 10, 10, 10, 0, -10),
    (-10, 5, 5, 10, 10, 5, 5, -10),
    (-10, 0, 5, 10, 10, 5, 0, -10),
    (-10, 0, 0, 0, 0, 0, 0, -10),
    (-20, -10, -10, -10, -10, -10, -10, -20),
))

ROOK_PST = _tbl((
    (0, 0, 0, 5, 5, 0, 0, 0),
    (5, 10, 10, 10, 10, 10, 10, 5),
    (-5, 0, 0, 0, 0, 0, 0, -5),
    (-5, 0, 0, 0, 0, 0, 0, -5),
    (-5, 0, 0, 0, 0, 0, 0, -5),
    (-5, 0, 0, 0, 0, 0, 0, -5),
    (-5, 0, 0, 0, 0, 0, 0, -5),
    (0, 0, 0, 0, 0, 0, 0, 0),
))

QUEEN_PST = _tbl((
    (-20, -10, -10, -5, -5, -10, -10, -20),
    (-10, 0, 0, 0, 0, 0, 0, -10),
    (-10, 0, 5, 5, 5, 5, 0, -10),
    (-5, 0, 5, 5, 5, 5, 0, -5),
    (0, 0, 5, 5, 5, 5, 0, -5),
    (-10, 5, 5, 5, 5, 5, 0, -10),
    (-10, 0, 5, 0, 0, 0, 0, -10),
    (-20, -10, -10, -5, -5, -10, -10, -20),
))

KING_MG = _tbl((
    (-30, -40, -40, -50, -50, -40, -40, -30),
    (-30, -40, -40, -50, -50, -40, -40, -30),
    (-30, -40, -40, -50, -50, -40, -40, -30),
    (-30, -40, -40, -50, -50, -40, -40, -30),
    (-20, -30, -30, -40, -40, -30, -30, -20),
    (-10, -20, -20, -20, -20, -20, -20, -10),
    (20, 20, 0, 0, 0, 0, 20, 20),
    (20, 30, 10, 0, 0, 10, 30, 20),
))

KING_EG = _tbl((
    (-50, -40, -30, -20, -20, -30, -40, -50),
    (-30, -20, -10, 0, 0, -10, -20, -30),
    (-30, -10, 20, 30, 30, 20, -10, -30),
    (-30, -10, 30, 40, 40, 30, -10, -30),
    (-30, -10, 30, 40, 40, 30, -10, -30),
    (-30, -10, 20, 30, 30, 20, -10, -30),
    (-30, -30, 0, 0, 0, 0, -30, -30),
    (-50, -30, -30, -30, -30, -30, -30, -50),
))

PST_MG = {
    "P": PAWN_MG,
    "N": KNIGHT_PST,
    "B": BISHOP_PST,
    "R": ROOK_PST,
    "Q": QUEEN_PST,
    "K": KING_MG,
}

PST_EG = {
    "P": PAWN_EG,
    "N": KNIGHT_PST,
    "B": BISHOP_PST,
    "R": ROOK_PST,
    "Q": QUEEN_PST,
    "K": KING_EG,
}

DEADLINE = 0.0
NODES = 0
TT = {}
KILLERS = [[] for _ in range(64)]
HISTORY = {}


class SearchTimeout(Exception):
    pass


def check_time():
    global NODES
    NODES += 1
    if (NODES & 1023) == 0 and perf_counter() > DEADLINE:
        raise SearchTimeout()


def side_from_to_play(to_play):
    s = str(to_play).lower()
    return "w" if s.startswith("w") else "b"


def board_from_pieces(pieces):
    board = [None] * 64
    for sq, pc in pieces.items():
        sq = str(sq)
        pc = str(pc)
        if len(sq) < 2 or len(pc) < 2:
            continue
        f = ord(sq[0]) - 97
        r = ord(sq[1]) - 49
        if 0 <= f < 8 and 0 <= r < 8 and pc[0] in ("w", "b") and pc[1] in PIECE_VALUES:
            board[r * 8 + f] = pc[:2]
    return board


def move_to_uci(move):
    frm, to, promo = move
    return FILES[frm & 7] + RANKS[frm >> 3] + FILES[to & 7] + RANKS[to >> 3] + promo


def locate_king(board, side):
    code = side + "K"
    for i, pc in enumerate(board):
        if pc == code:
            return i
    return -1


def is_attacked(board, sq, by_side):
    if sq < 0:
        return False

    f = sq & 7
    r = sq >> 3

    pawn = by_side + "P"
    knight = by_side + "N"
    king = by_side + "K"

    if by_side == "w":
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

    for df, dr in KNIGHT_DELTAS:
        nf, nr = f + df, r + dr
        if 0 <= nf < 8 and 0 <= nr < 8 and board[nr * 8 + nf] == knight:
            return True

    for df, dr in KING_DELTAS:
        nf, nr = f + df, r + dr
        if 0 <= nf < 8 and 0 <= nr < 8 and board[nr * 8 + nf] == king:
            return True

    for df, dr in BISHOP_DIRS:
        nf, nr = f + df, r + dr
        while 0 <= nf < 8 and 0 <= nr < 8:
            pc = board[nr * 8 + nf]
            if pc is not None:
                if pc[0] == by_side and (pc[1] == "B" or pc[1] == "Q"):
                    return True
                break
            nf += df
            nr += dr

    for df, dr in ROOK_DIRS:
        nf, nr = f + df, r + dr
        while 0 <= nf < 8 and 0 <= nr < 8:
            pc = board[nr * 8 + nf]
            if pc is not None:
                if pc[0] == by_side and (pc[1] == "R" or pc[1] == "Q"):
                    return True
                break
            nf += df
            nr += dr

    return False


def king_in_check(board, side):
    return is_attacked(board, locate_king(board, side), OPP[side])


def generate_pseudo(board, side, captures_only=False, ep_square=-1):
    moves = []
    enemy = OPP[side]

    for i, pc in enumerate(board):
        if pc is None or pc[0] != side:
            continue

        pt = pc[1]
        f = i & 7
        r = i >> 3

        if pt == "P":
            step = 8 if side == "w" else -8
            start_rank = 1 if side == "w" else 6
            promo_rank = 7 if side == "w" else 0
            nr = r + (1 if side == "w" else -1)

            if 0 <= nr < 8:
                one = i + step
                if board[one] is None:
                    if nr == promo_rank:
                        for pr in PROMOS:
                            moves.append((i, one, pr))
                    elif not captures_only:
                        moves.append((i, one, ""))
                        if r == start_rank:
                            two = i + 2 * step
                            if board[two] is None:
                                moves.append((i, two, ""))

                for df in (-1, 1):
                    nf = f + df
                    if not (0 <= nf < 8):
                        continue
                    to = one + df
                    target = board[to]
                    if target is not None:
                        if target[0] == enemy and target[1] != "K":
                            if nr == promo_rank:
                                for pr in PROMOS:
                                    moves.append((i, to, pr))
                            else:
                                moves.append((i, to, ""))
                    elif ep_square == to:
                        cap_sq = to - step
                        if 0 <= cap_sq < 64 and board[cap_sq] == enemy + "P":
                            moves.append((i, to, ""))

        elif pt == "N":
            for df, dr in KNIGHT_DELTAS:
                nf, nr = f + df, r + dr
                if 0 <= nf < 8 and 0 <= nr < 8:
                    to = nr * 8 + nf
                    target = board[to]
                    if target is None:
                        if not captures_only:
                            moves.append((i, to, ""))
                    elif target[0] != side and target[1] != "K":
                        moves.append((i, to, ""))

        elif pt == "B" or pt == "R" or pt == "Q":
            dirs = BISHOP_DIRS if pt == "B" else ROOK_DIRS if pt == "R" else QUEEN_DIRS
            for df, dr in dirs:
                nf, nr = f + df, r + dr
                while 0 <= nf < 8 and 0 <= nr < 8:
                    to = nr * 8 + nf
                    target = board[to]
                    if target is None:
                        if not captures_only:
                            moves.append((i, to, ""))
                    else:
                        if target[0] != side and target[1] != "K":
                            moves.append((i, to, ""))
                        break
                    nf += df
                    nr += dr

        elif pt == "K":
            for df, dr in KING_DELTAS:
                nf, nr = f + df, r + dr
                if 0 <= nf < 8 and 0 <= nr < 8:
                    to = nr * 8 + nf
                    target = board[to]
                    if target is None:
                        if not captures_only:
                            moves.append((i, to, ""))
                    elif target[0] != side and target[1] != "K":
                        moves.append((i, to, ""))

    return moves


def do_move(board, move, ep_square=-1):
    frm, to, promo = move
    piece = board[frm]
    captured = board[to]
    cap_sq = to

    board[frm] = None

    if (
        piece is not None
        and piece[1] == "P"
        and to == ep_square
        and captured is None
        and (frm & 7) != (to & 7)
    ):
        step = 8 if piece[0] == "w" else -8
        cap_sq = to - step
        captured = board[cap_sq]
        board[cap_sq] = None

    if promo:
        board[to] = piece[0] + promo.upper()
    else:
        board[to] = piece

    return piece, captured, cap_sq


def undo_move(board, move, state):
    frm, to, promo = move
    piece, captured, cap_sq = state

    board[frm] = piece
    if cap_sq != to:
        board[to] = None
        board[cap_sq] = captured
    else:
        board[to] = captured


def next_ep_square(piece, frm, to):
    if piece is not None and piece[1] == "P" and abs(to - frm) == 16:
        return (to + frm) // 2
    return -1


def generate_legal(board, side, captures_only=False, ep_square=-1):
    legal = []
    king_sq = locate_king(board, side)
    enemy = OPP[side]

    for move in generate_pseudo(board, side, captures_only, ep_square):
        moving = board[move[0]]
        state = do_move(board, move, ep_square)
        try:
            new_king = move[1] if moving is not None and moving[1] == "K" else king_sq
            if new_king < 0 or not is_attacked(board, new_king, enemy):
                legal.append(move)
        finally:
            undo_move(board, move, state)

    return legal


def has_any_legal_move(board, side, ep_square=-1):
    king_sq = locate_king(board, side)
    enemy = OPP[side]

    for move in generate_pseudo(board, side, False, ep_square):
        moving = board[move[0]]
        state = do_move(board, move, ep_square)
        try:
            new_king = move[1] if moving is not None and moving[1] == "K" else king_sq
            if new_king < 0 or not is_attacked(board, new_king, enemy):
                return True
        finally:
            undo_move(board, move, state)

    return False


def is_ep_capture(board, move, ep_square):
    frm, to, promo = move
    pc = board[frm]
    return (
        ep_square == to
        and pc is not None
        and pc[1] == "P"
        and board[to] is None
        and (frm & 7) != (to & 7)
    )


def is_quiet_move(board, move, ep_square):
    return move[2] == "" and board[move[1]] is None and not is_ep_capture(board, move, ep_square)


def record_killer(move, ply):
    if 0 <= ply < len(KILLERS):
        ks = KILLERS[ply]
        if move not in ks:
            ks.insert(0, move)
            if len(ks) > 2:
                ks.pop()


def move_order_score(board, move, side, ep_square, tt_move, ply):
    if move == tt_move:
        return 10_000_000

    frm, to, promo = move
    pc = board[frm]
    target = board[to]
    score = 0

    victim_value = 0
    if target is not None:
        victim_value = PIECE_VALUES.get(target[1], 0)
    elif is_ep_capture(board, move, ep_square):
        victim_value = 100

    if victim_value:
        attacker_value = PIECE_VALUES.get(pc[1], 0) if pc else 0
        score += 1_000_000 + 10 * victim_value - attacker_value

    if promo:
        score += 900_000 + PIECE_VALUES.get(promo.upper(), 0)
        if promo == "q":
            score += 50_000

    if 0 <= ply < len(KILLERS):
        ks = KILLERS[ply]
        if move in ks:
            score += 500_000 if ks and move == ks[0] else 450_000

    score += HISTORY.get(move, 0)

    if pc is not None and not promo:
        pt = pc[1]
        table = PST_MG.get(pt)
        if table is not None:
            rf = frm if pc[0] == "w" else MIRROR[frm]
            rt = to if pc[0] == "w" else MIRROR[to]
            score += table[rt] - table[rf]

    score += CENTER_SCORE[to]
    return score


def order_moves(board, moves, side, ep_square, tt_move=None, ply=0):
    if len(moves) <= 1:
        return list(moves)
    scored = [
        (move_order_score(board, m, side, ep_square, tt_move, ply), m)
        for m in moves
    ]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in scored]


def piece_count_lte(board, limit):
    n = 0
    for pc in board:
        if pc is not None:
            n += 1
            if n > limit:
                return False
    return True


def evaluate(board, side):
    mg = 0
    eg = 0
    phase = 0
    material = 0

    pawn_files = {"w": [0] * 8, "b": [0] * 8}
    pawns = {"w": [], "b": []}
    bishops = {"w": 0, "b": 0}
    rooks = []
    kings = {"w": -1, "b": -1}

    for idx, pc in enumerate(board):
        if pc is None:
            continue

        color = pc[0]
        pt = pc[1]
        if pt not in PIECE_VALUES:
            continue

        sign = 1 if color == "w" else -1
        rel = idx if color == "w" else MIRROR[idx]
        val = PIECE_VALUES[pt]

        mg += sign * (val + PST_MG[pt][rel])
        eg += sign * (val + PST_EG[pt][rel])
        material += sign * val
        phase += PHASE_VALUES.get(pt, 0)

        if pt == "P":
            pawn_files[color][idx & 7] += 1
            pawns[color].append(idx)
        elif pt == "B":
            bishops[color] += 1
        elif pt == "R":
            rooks.append((idx, color))
        elif pt == "K":
            kings[color] = idx

    if phase > 24:
        phase = 24

    score = (mg * phase + eg * (24 - phase)) // 24
    features = 0

    if bishops["w"] >= 2:
        features += 35
    if bishops["b"] >= 2:
        features -= 35

    for color in ("w", "b"):
        sign = 1 if color == "w" else -1
        enemy = OPP[color]
        own_files = pawn_files[color]
        enemy_pawns = pawns[enemy]

        for f, cnt in enumerate(own_files):
            if cnt > 1:
                features -= sign * 14 * (cnt - 1)

        for pidx in pawns[color]:
            f = pidx & 7
            r = pidx >> 3

            isolated = True
            if f > 0 and own_files[f - 1] > 0:
                isolated = False
            if f < 7 and own_files[f + 1] > 0:
                isolated = False
            if isolated:
                features -= sign * 10

            protected = False
            if color == "w" and r > 0:
                if f > 0 and board[pidx - 9] == "wP":
                    protected = True
                if f < 7 and board[pidx - 7] == "wP":
                    protected = True
            elif color == "b" and r < 7:
                if f > 0 and board[pidx + 7] == "bP":
                    protected = True
                if f < 7 and board[pidx + 9] == "bP":
                    protected = True
            if protected:
                features += sign * 4

            passed = True
            for ep in enemy_pawns:
                ef = ep & 7
                er = ep >> 3
                if abs(ef - f) <= 1:
                    if color == "w" and er > r:
                        passed = False
                        break
                    if color == "b" and er < r:
                        passed = False
                        break
            if passed:
                adv = r if color == "w" else 7 - r
                features += sign * PASS_BONUS[adv]

    for ridx, color in rooks:
        sign = 1 if color == "w" else -1
        enemy = OPP[color]
        f = ridx & 7
        r = ridx >> 3

        if pawn_files[color][f] == 0:
            features += sign * 10
            if pawn_files[enemy][f] == 0:
                features += sign * 10

        if (color == "w" and r == 6) or (color == "b" and r == 1):
            features += sign * 18

    if phase > 0:
        safety = 0
        for color in ("w", "b"):
            k = kings[color]
            if k < 0:
                continue

            sign = 1 if color == "w" else -1
            enemy = OPP[color]
            kf = k & 7
            kr = k >> 3
            direction = 1 if color == "w" else -1
            shield = 0

            front = kr + direction
            front2 = kr + 2 * direction
            own_pawn = color + "P"

            for df in (-1, 0, 1):
                ff = kf + df
                if not (0 <= ff < 8):
                    continue

                if 0 <= front < 8:
                    pc1 = board[front * 8 + ff]
                    if pc1 == own_pawn:
                        shield += 10
                    elif 0 <= front2 < 8 and board[front2 * 8 + ff] == own_pawn:
                        shield += 3
                    else:
                        shield -= 6
                else:
                    shield -= 8

                if pawn_files[color][ff] == 0:
                    shield -= 4
                    if pawn_files[enemy][ff] == 0:
                        shield -= 3

            safety += sign * shield

        features += safety * phase // 24

    if phase < 10 and abs(material) >= 400:
        strong = "w" if material > 0 else "b"
        weak = OPP[strong]
        sk = kings[strong]
        wk = kings[weak]

        if sk >= 0 and wk >= 0:
            sf, sr = sk & 7, sk >> 3
            wf, wr = wk & 7, wk >> 3

            edge = abs(wf * 2 - 7) + abs(wr * 2 - 7)
            dist = abs(sf - wf) + abs(sr - wr)
            bonus = edge * 5 + (14 - 2 * dist) * 3

            features += (1 if strong == "w" else -1) * bonus * (10 - phase) // 10

    score += features
    perspective = score if side == "w" else -score
    return perspective + 6


def qsearch(board, side, ep_square, alpha, beta, ply):
    check_time()

    incheck = king_in_check(board, side)

    if incheck:
        moves = generate_legal(board, side, False, ep_square)
        if not moves:
            return -MATE + ply
        if ply >= MAX_Q_PLY:
            return evaluate(board, side)
    else:
        stand = evaluate(board, side)
        if stand >= beta:
            return beta
        if stand > alpha:
            alpha = stand
        if ply >= MAX_Q_PLY:
            return alpha

        moves = generate_legal(board, side, True, ep_square)
        if not moves:
            if piece_count_lte(board, 7) and not has_any_legal_move(board, side, ep_square):
                return 0
            return alpha

    ordered = order_moves(board, moves, side, ep_square, None, ply)
    enemy = OPP[side]

    for move in ordered:
        piece = board[move[0]]
        state = do_move(board, move, ep_square)
        child_ep = next_ep_square(piece, move[0], move[1])

        try:
            score = -qsearch(board, enemy, child_ep, -beta, -alpha, ply + 1)
        finally:
            undo_move(board, move, state)

        if score >= beta:
            return beta
        if score > alpha:
            alpha = score

    return alpha


def negamax(board, side, ep_square, depth, alpha, beta, ply):
    check_time()

    if depth <= 0:
        return qsearch(board, side, ep_square, alpha, beta, ply)

    key = (side, ep_square, tuple(board))
    original_alpha = alpha
    original_beta = beta

    entry = TT.get(key)
    tt_move = None

    if entry is not None:
        edepth, flag, val, mv = entry
        tt_move = mv
        if edepth >= depth:
            if flag == 0:
                return val
            if flag == 1 and val > alpha:
                alpha = val
            elif flag == -1 and val < beta:
                beta = val
            if alpha >= beta:
                return val

    incheck = king_in_check(board, side)
    moves = generate_legal(board, side, False, ep_square)

    if not moves:
        return -MATE + ply if incheck else 0

    ordered = order_moves(board, moves, side, ep_square, tt_move, ply)
    best = -INF
    best_move = ordered[0]
    enemy = OPP[side]

    for move in ordered:
        quiet = is_quiet_move(board, move, ep_square)
        piece = board[move[0]]
        state = do_move(board, move, ep_square)
        child_ep = next_ep_square(piece, move[0], move[1])

        try:
            score = -negamax(board, enemy, child_ep, depth - 1, -beta, -alpha, ply + 1)
        finally:
            undo_move(board, move, state)

        if score > best:
            best = score
            best_move = move

        if score > alpha:
            alpha = score

        if alpha >= beta:
            if quiet:
                record_killer(move, ply)
                HISTORY[move] = HISTORY.get(move, 0) + depth * depth
            break

    flag = 0
    if best <= original_alpha:
        flag = -1
    elif best >= original_beta:
        flag = 1

    if len(TT) < 200_000:
        TT[key] = (depth, flag, best, best_move)

    return best


def external_legal_list():
    obj = globals().get("legal_moves", None)
    if obj is None:
        return None
    try:
        return list(obj)
    except Exception:
        return None


def policy(pieces: dict[str, str], to_play: str) -> str:
    global DEADLINE, NODES, TT, KILLERS, HISTORY

    ext_list = external_legal_list()

    try:
        start = perf_counter()
        DEADLINE = start + TIME_BUDGET
        NODES = 0
        TT = {}
        KILLERS = [[] for _ in range(64)]
        HISTORY = {}

        board = board_from_pieces(pieces)
        side = side_from_to_play(to_play)
        ep_square = -1

        legal = generate_legal(board, side, False, ep_square)

        ext_set = None
        if ext_list:
            ext_set = set(ext_list)
            filtered = [m for m in legal if move_to_uci(m) in ext_set]
            if filtered:
                legal = filtered
            else:
                return ext_list[0]

        if not legal:
            if ext_list:
                return ext_list[0]
            pseudo = generate_pseudo(board, side, False, ep_square)
            return move_to_uci(pseudo[0]) if pseudo else "a1a1"

        if len(legal) == 1:
            return move_to_uci(legal[0])

        ordered = order_moves(board, legal, side, ep_square, None, 0)
        best = ordered[0]
        best_score = -INF

        piece_count = sum(1 for pc in board if pc is not None)
        if piece_count <= 6:
            max_depth = 7
        elif piece_count <= 10:
            max_depth = 6
        elif piece_count <= 16 or len(legal) <= 12:
            max_depth = 5
        elif len(legal) > 38:
            max_depth = 3
        else:
            max_depth = 4

        enemy = OPP[side]

        for depth in range(1, max_depth + 1):
            try:
                if perf_counter() > DEADLINE:
                    raise SearchTimeout()

                current_best = best
                current_score = -INF
                alpha = -INF
                beta = INF

                ordered = order_moves(board, legal, side, ep_square, best, 0)

                for move in ordered:
                    if perf_counter() > DEADLINE:
                        raise SearchTimeout()

                    piece = board[move[0]]
                    state = do_move(board, move, ep_square)
                    child_ep = next_ep_square(piece, move[0], move[1])

                    try:
                        score = -negamax(board, enemy, child_ep, depth - 1, -beta, -alpha, 1)
                    finally:
                        undo_move(board, move, state)

                    if score > current_score:
                        current_score = score
                        current_best = move

                    if score > alpha:
                        alpha = score

                best = current_best
                best_score = current_score

                if best_score >= MATE - 1000:
                    break

            except SearchTimeout:
                break

        result = move_to_uci(best)
        if ext_set is not None and result not in ext_set:
            return ext_list[0]
        return result

    except Exception:
        if ext_list:
            return ext_list[0]
        try:
            board = board_from_pieces(pieces)
            side = side_from_to_play(to_play)
            moves = generate_legal(board, side, False, -1)
            if moves:
                return move_to_uci(order_moves(board, moves, side, -1, None, 0)[0])
            pseudo = generate_pseudo(board, side, False, -1)
            if pseudo:
                return move_to_uci(pseudo[0])
        except Exception:
            pass
        return "a1a1"
