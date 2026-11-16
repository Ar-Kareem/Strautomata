
import time

FILES = "abcdefgh"
INF = 10**9
MATE = 1000000

VAL = {"P": 100, "N": 320, "B": 330, "R": 500, "Q": 900, "K": 0}
PROMOS = ("q", "r", "b", "n")

KNIGHT_STEPS = ((1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2))
KING_STEPS = ((1, 1), (1, 0), (1, -1), (0, 1), (0, -1), (-1, 1), (-1, 0), (-1, -1))
ORTHO = ((1, 0), (-1, 0), (0, 1), (0, -1))
DIAG = ((1, 1), (1, -1), (-1, 1), (-1, -1))

_deadline = 0.0
_nodes = 0
TT = {}


def _flat(rows):
    return [x for row in rows for x in row]


PAWN_TABLE = _flat([
    [0, 0, 0, 0, 0, 0, 0, 0],
    [5, 10, 10, -20, -20, 10, 10, 5],
    [5, -5, -10, 0, 0, -10, -5, 5],
    [0, 0, 0, 20, 20, 0, 0, 0],
    [5, 5, 10, 25, 25, 10, 5, 5],
    [10, 10, 20, 30, 30, 20, 10, 10],
    [50, 50, 50, 50, 50, 50, 50, 50],
    [0, 0, 0, 0, 0, 0, 0, 0],
])

KNIGHT_TABLE = _flat([
    [-50, -40, -30, -30, -30, -30, -40, -50],
    [-40, -20, 0, 0, 0, 0, -20, -40],
    [-30, 0, 10, 15, 15, 10, 0, -30],
    [-30, 5, 15, 20, 20, 15, 5, -30],
    [-30, 0, 15, 20, 20, 15, 0, -30],
    [-30, 5, 10, 15, 15, 10, 5, -30],
    [-40, -20, 0, 5, 5, 0, -20, -40],
    [-50, -40, -30, -30, -30, -30, -40, -50],
])

BISHOP_TABLE = _flat([
    [-20, -10, -10, -10, -10, -10, -10, -20],
    [-10, 0, 0, 0, 0, 0, 0, -10],
    [-10, 0, 5, 10, 10, 5, 0, -10],
    [-10, 5, 5, 10, 10, 5, 5, -10],
    [-10, 0, 10, 10, 10, 10, 0, -10],
    [-10, 10, 10, 10, 10, 10, 10, -10],
    [-10, 5, 0, 0, 0, 0, 5, -10],
    [-20, -10, -10, -10, -10, -10, -10, -20],
])

ROOK_TABLE = _flat([
    [0, 0, 0, 5, 5, 0, 0, 0],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [5, 10, 10, 10, 10, 10, 10, 5],
    [0, 0, 0, 5, 5, 0, 0, 0],
])

QUEEN_TABLE = _flat([
    [-20, -10, -10, -5, -5, -10, -10, -20],
    [-10, 0, 0, 0, 0, 0, 0, -10],
    [-10, 0, 5, 5, 5, 5, 0, -10],
    [-5, 0, 5, 5, 5, 5, 0, -5],
    [0, 0, 5, 5, 5, 5, 0, -5],
    [-10, 5, 5, 5, 5, 5, 0, -10],
    [-10, 0, 5, 0, 0, 0, 0, -10],
    [-20, -10, -10, -5, -5, -10, -10, -20],
])

KING_MID_TABLE = _flat([
    [20, 30, 10, 0, 0, 10, 30, 20],
    [20, 20, 0, 0, 0, 0, 20, 20],
    [-10, -20, -20, -20, -20, -20, -20, -10],
    [-20, -30, -30, -40, -40, -30, -30, -20],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
])

KING_END_TABLE = _flat([
    [-50, -30, -30, -30, -30, -30, -30, -50],
    [-30, -30, 0, 0, 0, 0, -30, -30],
    [-30, -10, 20, 30, 30, 20, -10, -30],
    [-30, -10, 30, 40, 40, 30, -10, -30],
    [-30, -10, 30, 40, 40, 30, -10, -30],
    [-30, -10, 20, 30, 30, 20, -10, -30],
    [-30, -20, -10, 0, 0, -10, -20, -30],
    [-50, -40, -30, -20, -20, -30, -40, -50],
])

PST = {
    "P": PAWN_TABLE,
    "N": KNIGHT_TABLE,
    "B": BISHOP_TABLE,
    "R": ROOK_TABLE,
    "Q": QUEEN_TABLE,
}


def sq_to_i(s):
    return (ord(s[0]) - 97) + (ord(s[1]) - 49) * 8


def i_to_sq(i):
    return FILES[i & 7] + str((i >> 3) + 1)


def other(side):
    return "b" if side == "w" else "w"


def mirror(i):
    return (7 - (i >> 3)) * 8 + (i & 7)


def _make_start_board():
    b = ["."] * 64
    order = "RNBQKBNR"
    for f, p in enumerate(order):
        b[f] = "w" + p
        b[56 + f] = "b" + p
        b[8 + f] = "wP"
        b[48 + f] = "bP"
    return b


START_BOARD = _make_start_board()


def check_time():
    global _nodes
    _nodes += 1
    if (_nodes & 1023) == 0 and time.perf_counter() > _deadline:
        raise TimeoutError


def move_to_uci(m):
    return i_to_sq(m[0]) + i_to_sq(m[1]) + (m[2] if m[2] else "")


def make_move(board, m):
    f, t, promo = m
    piece = board[f]
    captured = board[t]
    board[f] = "."
    board[t] = piece[0] + promo.upper() if promo else piece
    return captured, piece


def undo_move(board, m, captured, old_piece):
    f, t, _ = m
    board[f] = old_piece
    board[t] = captured


def king_square(board, side):
    k = side + "K"
    for i, p in enumerate(board):
        if p == k:
            return i
    return -1


def is_attacked(board, sq, by_side):
    f = sq & 7
    r = sq >> 3

    if by_side == "w":
        if f > 0:
            j = sq - 9
            if j >= 0 and board[j] == "wP":
                return True
        if f < 7:
            j = sq - 7
            if j >= 0 and board[j] == "wP":
                return True
    else:
        if f > 0:
            j = sq + 7
            if j < 64 and board[j] == "bP":
                return True
        if f < 7:
            j = sq + 9
            if j < 64 and board[j] == "bP":
                return True

    for df, dr in KNIGHT_STEPS:
        nf, nr = f + df, r + dr
        if 0 <= nf < 8 and 0 <= nr < 8:
            p = board[nr * 8 + nf]
            if p == by_side + "N":
                return True

    for df, dr in KING_STEPS:
        nf, nr = f + df, r + dr
        if 0 <= nf < 8 and 0 <= nr < 8:
            p = board[nr * 8 + nf]
            if p == by_side + "K":
                return True

    for df, dr in ORTHO:
        nf, nr = f + df, r + dr
        while 0 <= nf < 8 and 0 <= nr < 8:
            p = board[nr * 8 + nf]
            if p != ".":
                if p[0] == by_side and (p[1] == "R" or p[1] == "Q"):
                    return True
                break
            nf += df
            nr += dr

    for df, dr in DIAG:
        nf, nr = f + df, r + dr
        while 0 <= nf < 8 and 0 <= nr < 8:
            p = board[nr * 8 + nf]
            if p != ".":
                if p[0] == by_side and (p[1] == "B" or p[1] == "Q"):
                    return True
                break
            nf += df
            nr += dr

    return False


def in_check(board, side):
    ks = king_square(board, side)
    if ks < 0:
        return False
    return is_attacked(board, ks, other(side))


def generate_pseudo_moves(board, side, tactical_only=False):
    moves = []
    for i, p in enumerate(board):
        if p == "." or p[0] != side:
            continue

        pt = p[1]
        f = i & 7
        r = i >> 3

        if pt == "P":
            direction = 1 if side == "w" else -1
            start_rank = 1 if side == "w" else 6
            promo_from = 6 if side == "w" else 1
            nr = r + direction

            if 0 <= nr < 8:
                for df in (-1, 1):
                    nf = f + df
                    if 0 <= nf < 8:
                        j = nr * 8 + nf
                        q = board[j]
                        if q != "." and q[0] != side and q[1] != "K":
                            if r == promo_from:
                                for pr in PROMOS:
                                    moves.append((i, j, pr))
                            else:
                                moves.append((i, j, ""))

                j = nr * 8 + f
                if board[j] == ".":
                    if r == promo_from:
                        for pr in PROMOS:
                            moves.append((i, j, pr))
                    elif not tactical_only:
                        moves.append((i, j, ""))
                        if r == start_rank:
                            j2 = (r + 2 * direction) * 8 + f
                            if 0 <= j2 < 64 and board[j2] == ".":
                                moves.append((i, j2, ""))

        elif pt == "N":
            for df, dr in KNIGHT_STEPS:
                nf, nr = f + df, r + dr
                if 0 <= nf < 8 and 0 <= nr < 8:
                    j = nr * 8 + nf
                    q = board[j]
                    if q == ".":
                        if not tactical_only:
                            moves.append((i, j, ""))
                    elif q[0] != side and q[1] != "K":
                        moves.append((i, j, ""))

        elif pt == "B" or pt == "R" or pt == "Q":
            dirs = DIAG if pt == "B" else ORTHO if pt == "R" else DIAG + ORTHO
            for df, dr in dirs:
                nf, nr = f + df, r + dr
                while 0 <= nf < 8 and 0 <= nr < 8:
                    j = nr * 8 + nf
                    q = board[j]
                    if q == ".":
                        if not tactical_only:
                            moves.append((i, j, ""))
                    else:
                        if q[0] != side and q[1] != "K":
                            moves.append((i, j, ""))
                        break
                    nf += df
                    nr += dr

        elif pt == "K":
            for df, dr in KING_STEPS:
                nf, nr = f + df, r + dr
                if 0 <= nf < 8 and 0 <= nr < 8:
                    j = nr * 8 + nf
                    q = board[j]
                    if q == ".":
                        if not tactical_only:
                            moves.append((i, j, ""))
                    elif q[0] != side and q[1] != "K":
                        moves.append((i, j, ""))

    return moves


def generate_legal(board, side, tactical_only=False):
    legal = []
    for m in generate_pseudo_moves(board, side, tactical_only):
        cap, old = make_move(board, m)
        if not in_check(board, side):
            legal.append(m)
        undo_move(board, m, cap, old)
    return legal


def evaluate(board, side):
    score = 0
    pawn_files = {"w": [0] * 8, "b": [0] * 8}
    pawn_squares = {"w": [], "b": []}
    bishops = {"w": 0, "b": 0}
    kings = {"w": -1, "b": -1}
    material = {"w": 0, "b": 0}
    nonpawn = 0
    piece_count = 0

    for i, p in enumerate(board):
        if p == ".":
            continue
        piece_count += 1
        c, pt = p[0], p[1]
        material[c] += VAL[pt]
        if pt not in ("P", "K"):
            nonpawn += VAL[pt]
        if pt == "P":
            pawn_files[c][i & 7] += 1
            pawn_squares[c].append(i)
        elif pt == "B":
            bishops[c] += 1
        elif pt == "K":
            kings[c] = i

    endgame = nonpawn <= 1800

    for i, p in enumerate(board):
        if p == ".":
            continue
        c, pt = p[0], p[1]
        sign = 1 if c == "w" else -1
        idx = i if c == "w" else mirror(i)

        if pt == "K":
            val = KING_END_TABLE[idx] if endgame else KING_MID_TABLE[idx]
        else:
            val = VAL[pt] + PST[pt][idx]

        score += sign * val

        if pt == "R":
            f = i & 7
            own_pawns = pawn_files[c][f]
            enemy_pawns = pawn_files[other(c)][f]
            if own_pawns == 0:
                score += sign * (18 if enemy_pawns == 0 else 10)
            rank = i >> 3
            if (c == "w" and rank == 6) or (c == "b" and rank == 1):
                score += sign * 15

    if bishops["w"] >= 2:
        score += 30
    if bishops["b"] >= 2:
        score -= 30

    passed_bonus = [0, 5, 10, 18, 35, 60, 100, 0]

    for c in ("w", "b"):
        sign = 1 if c == "w" else -1
        opp = other(c)
        for f, cnt in enumerate(pawn_files[c]):
            if cnt > 1:
                score += sign * (-12 * (cnt - 1))

        for sq in pawn_squares[c]:
            f = sq & 7
            r = sq >> 3

            isolated = True
            if f > 0 and pawn_files[c][f - 1]:
                isolated = False
            if f < 7 and pawn_files[c][f + 1]:
                isolated = False
            if isolated:
                score += sign * -8

            passed = True
            for esq in pawn_squares[opp]:
                ef = esq & 7
                er = esq >> 3
                if abs(ef - f) <= 1:
                    if c == "w" and er > r:
                        passed = False
                        break
                    if c == "b" and er < r:
                        passed = False
                        break

            if passed:
                adv = r if c == "w" else 7 - r
                score += sign * passed_bonus[adv]

    if not endgame:
        for c in ("w", "b"):
            ks = kings[c]
            if ks < 0:
                continue
            sign = 1 if c == "w" else -1
            f = ks & 7
            r = ks >> 3
            direction = 1 if c == "w" else -1
            shelter = 0
            for df in (-1, 0, 1):
                nf = f + df
                if not (0 <= nf < 8):
                    continue
                for step in (1, 2):
                    nr = r + direction * step
                    if 0 <= nr < 8 and board[nr * 8 + nf] == c + "P":
                        shelter += 1
                        break
            score += sign * (-(max(0, 3 - shelter) * 12))

    mat_diff = material["w"] - material["b"]
    if abs(mat_diff) >= 500 and piece_count <= 10 and kings["w"] >= 0 and kings["b"] >= 0:
        strong = "w" if mat_diff > 0 else "b"
        weak = other(strong)
        sk = kings[strong]
        wk = kings[weak]
        wf, wr = wk & 7, wk >> 3
        sf, sr = sk & 7, sk >> 3
        edge = max(abs(wf - 3.5), abs(wr - 3.5))
        dist = abs(wf - sf) + abs(wr - sr)
        bonus = int(edge * 30 + (14 - dist) * 8)
        score += bonus if strong == "w" else -bonus

    return int(score if side == "w" else -score)


def order_score(board, m, tt_move=None):
    if tt_move is not None and m == tt_move:
        return 10000000

    f, t, promo = m
    piece = board[f]
    if piece == ".":
        return 0

    pt = piece[1]
    cap = board[t]
    score = 0

    if promo:
        score += 800000 + VAL[promo.upper()]

    if cap != ".":
        score += 1000000 + 10 * VAL[cap[1]] - VAL[pt]

    tf = t & 7
    tr = t >> 3
    center = 14 - (abs(2 * tf - 7) + abs(2 * tr - 7))
    score += center

    if pt == "N" or pt == "B":
        score += center * 3
    elif pt == "P":
        score += (tr if piece[0] == "w" else 7 - tr) * 2

    return score


def qsearch(board, side, alpha, beta, ply, qdepth):
    check_time()
    chk = in_check(board, side)

    if chk:
        if qdepth < -1:
            return evaluate(board, side) - 75
        moves = generate_legal(board, side, False)
        if not moves:
            return -MATE + ply
        moves.sort(key=lambda m: order_score(board, m), reverse=True)
        value = -INF
        opp = other(side)
        for m in moves:
            cap, old = make_move(board, m)
            sc = -qsearch(board, opp, -beta, -alpha, ply + 1, qdepth - 1)
            undo_move(board, m, cap, old)
            if sc >= beta:
                return beta
            if sc > value:
                value = sc
            if sc > alpha:
                alpha = sc
        return alpha

    stand = evaluate(board, side)
    if stand >= beta:
        return beta
    if stand > alpha:
        alpha = stand
    if qdepth <= 0:
        return alpha

    moves = generate_legal(board, side, True)
    if not moves:
        return alpha

    moves.sort(key=lambda m: order_score(board, m), reverse=True)
    opp = other(side)

    for m in moves:
        cap, old = make_move(board, m)
        sc = -qsearch(board, opp, -beta, -alpha, ply + 1, qdepth - 1)
        undo_move(board, m, cap, old)
        if sc >= beta:
            return beta
        if sc > alpha:
            alpha = sc

    return alpha


def negamax(board, side, depth, alpha, beta, ply):
    global TT
    check_time()

    if depth <= 0:
        return qsearch(board, side, alpha, beta, ply, 3)

    alpha_orig = alpha
    beta_orig = beta
    key = (tuple(board), side)
    tt_move = None

    ent = TT.get(key)
    if ent is not None:
        ent_depth, ent_flag, ent_val, ent_move = ent
        tt_move = ent_move
        if ent_depth >= depth:
            if ent_flag == 0:
                return ent_val
            elif ent_flag == 1:
                alpha = max(alpha, ent_val)
            else:
                beta = min(beta, ent_val)
            if alpha >= beta:
                return ent_val

    chk = in_check(board, side)
    moves = generate_legal(board, side, False)

    if not moves:
        return -MATE + ply if chk else 0

    moves.sort(key=lambda m: order_score(board, m, tt_move), reverse=True)

    best_val = -INF
    best_move = moves[0]
    opp = other(side)

    for m in moves:
        cap, old = make_move(board, m)
        sc = -negamax(board, opp, depth - 1, -beta, -alpha, ply + 1)
        undo_move(board, m, cap, old)

        if sc > best_val:
            best_val = sc
            best_move = m
        if sc > alpha:
            alpha = sc
        if alpha >= beta:
            break

    if best_val <= alpha_orig:
        flag = 2
    elif best_val >= beta_orig:
        flag = 1
    else:
        flag = 0

    if len(TT) < 120000:
        TT[key] = (depth, flag, best_val, best_move)

    return best_val


def root_search(board, side, moves, depth, previous_best):
    ordered = list(moves)
    ordered.sort(key=lambda m: order_score(board, m, previous_best), reverse=True)

    best = ordered[0]
    best_score = -INF
    alpha = -INF
    beta = INF
    opp = other(side)

    for m in ordered:
        cap, old = make_move(board, m)
        sc = -negamax(board, opp, depth - 1, -beta, -alpha, 1)
        undo_move(board, m, cap, old)

        if sc > best_score:
            best_score = sc
            best = m
        if sc > alpha:
            alpha = sc

    return best_score, best


def choose_greedy(board, side, moves):
    best = moves[0]
    best_score = -INF
    opp = other(side)

    for m in moves:
        cap, old = make_move(board, m)
        sc = evaluate(board, side)
        if in_check(board, opp):
            sc += 35
            if not generate_legal(board, opp, False):
                sc += MATE // 2
        undo_move(board, m, cap, old)

        sc += order_score(board, m) // 1000

        if sc > best_score:
            best_score = sc
            best = m

    return best


def _find_uci(moves, uci):
    for m in moves:
        if move_to_uci(m) == uci:
            return m
    return None


def _match_start_with(board, changes):
    for i in range(64):
        exp = changes[i] if i in changes else START_BOARD[i]
        if board[i] != exp:
            return False
    return True


def book_move(board, side, moves):
    if sum(1 for x in board if x != ".") != 32:
        return None

    if side == "w" and board == START_BOARD:
        for u in ("e2e4", "d2d4", "g1f3", "c2c4"):
            m = _find_uci(moves, u)
            if m:
                return m

    e2, e4 = sq_to_i("e2"), sq_to_i("e4")
    d2, d4 = sq_to_i("d2"), sq_to_i("d4")
    c2, c4 = sq_to_i("c2"), sq_to_i("c4")
    g1, f3 = sq_to_i("g1"), sq_to_i("f3")
    e7, e5 = sq_to_i("e7"), sq_to_i("e5")
    d7, d5 = sq_to_i("d7"), sq_to_i("d5")
    c7, c5 = sq_to_i("c7"), sq_to_i("c5")

    if side == "b":
        if _match_start_with(board, {e2: ".", e4: "wP"}):
            for u in ("c7c5", "e7e5", "e7e6", "c7c6"):
                m = _find_uci(moves, u)
                if m:
                    return m
        if _match_start_with(board, {d2: ".", d4: "wP"}):
            for u in ("d7d5", "g8f6", "e7e6"):
                m = _find_uci(moves, u)
                if m:
                    return m
        if _match_start_with(board, {c2: ".", c4: "wP"}):
            for u in ("e7e5", "c7c5", "g8f6"):
                m = _find_uci(moves, u)
                if m:
                    return m
        if _match_start_with(board, {g1: ".", f3: "wN"}):
            for u in ("d7d5", "g8f6", "c7c5"):
                m = _find_uci(moves, u)
                if m:
                    return m

    if side == "w":
        if _match_start_with(board, {e2: ".", e4: "wP", e7: ".", e5: "bP"}):
            for u in ("g1f3", "d2d4", "f1c4"):
                m = _find_uci(moves, u)
                if m:
                    return m
        if _match_start_with(board, {e2: ".", e4: "wP", c7: ".", c5: "bP"}):
            for u in ("g1f3", "d2d4", "c2c3"):
                m = _find_uci(moves, u)
                if m:
                    return m
        if _match_start_with(board, {d2: ".", d4: "wP", d7: ".", d5: "bP"}):
            for u in ("c2c4", "g1f3", "b1c3"):
                m = _find_uci(moves, u)
                if m:
                    return m

    return None


def _policy(pieces, to_play):
    global _deadline, _nodes, TT

    start = time.perf_counter()
    _deadline = start + 0.84
    _nodes = 0
    TT = {}

    board = ["."] * 64
    for sq, pc in pieces.items():
        if len(sq) == 2 and sq[0] in FILES and sq[1] in "12345678" and len(pc) == 2:
            board[sq_to_i(sq)] = pc

    side = "w" if str(to_play).lower().startswith("w") else "b"

    external_moves = globals().get("legal_moves", None)

    moves = generate_legal(board, side, False)

    if not moves:
        if isinstance(external_moves, (list, tuple, set)) and external_moves:
            return list(external_moves)[0]
        pseudo = generate_pseudo_moves(board, side, False)
        return move_to_uci(pseudo[0]) if pseudo else "a1a1"

    if len(moves) == 1:
        return move_to_uci(moves[0])

    bm = book_move(board, side, moves)
    if bm is not None:
        return move_to_uci(bm)

    best = choose_greedy(board, side, moves)

    piece_count = sum(1 for x in board if x != ".")
    if piece_count <= 5:
        max_depth = 8
    elif piece_count <= 10:
        max_depth = 7
    elif piece_count <= 16:
        max_depth = 6
    elif piece_count <= 24:
        max_depth = 5
    else:
        max_depth = 4

    previous = best

    try:
        for depth in range(1, max_depth + 1):
            score, mv = root_search(board, side, moves, depth, previous)
            best = mv
            previous = mv
            if score > MATE - 1000:
                break
            if time.perf_counter() > _deadline - 0.03:
                break
    except TimeoutError:
        pass

    result = move_to_uci(best)

    if isinstance(external_moves, (list, tuple, set)) and external_moves:
        if result in external_moves:
            return result
        generated = {move_to_uci(m) for m in moves}
        for u in external_moves:
            if u in generated:
                return u
        return list(external_moves)[0]

    return result


def policy(pieces: dict[str, str], to_play: str) -> str:
    try:
        return _policy(pieces, to_play)
    except Exception:
        lm = globals().get("legal_moves", None)
        if isinstance(lm, (list, tuple, set)) and lm:
            return list(lm)[0]
        return "a1a1"
