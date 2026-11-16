
from __future__ import annotations
import time

FILES = "abcdefgh"
PROMOS = ("q", "r", "b", "n")

INF = 10**9
MATE = 100000
MAX_PHASE = 24

PIECE_VALUES = {"P": 100, "N": 320, "B": 330, "R": 500, "Q": 900, "K": 0}
PHASE = {"P": 0, "N": 1, "B": 1, "R": 2, "Q": 4, "K": 0}

KNIGHT_DELTAS = ((1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2))
KING_DELTAS = ((1, 1), (1, 0), (1, -1), (0, 1), (0, -1), (-1, 1), (-1, 0), (-1, -1))
BISHOP_DIRS = ((1, 1), (1, -1), (-1, 1), (-1, -1))
ROOK_DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))

PASSED_MG = [0, 4, 8, 16, 30, 55, 90, 0]
PASSED_EG = [0, 8, 16, 32, 60, 100, 160, 0]


def _build_tables():
    mg = {p: [0] * 64 for p in "PNBRQK"}
    eg = {p: [0] * 64 for p in "PNBRQK"}

    for r in range(8):
        for f in range(8):
            i = r * 8 + f
            center = 14 - (abs(2 * f - 7) + abs(2 * r - 7))
            file_center = 7 - abs(2 * f - 7)

            p_mg = r * 6 + file_center * 2
            if r in (3, 4):
                p_mg += 8
            if r == 5:
                p_mg += 12
            if r == 6:
                p_mg += 20
            if f in (0, 7):
                p_mg -= 2
            mg["P"][i] = p_mg
            eg["P"][i] = r * 12 + file_center + (35 if r == 6 else 0)

            edge_pen = 0
            if f in (0, 7):
                edge_pen -= 18
            if r in (0, 7):
                edge_pen -= 12
            mg["N"][i] = center * 5 + r * 2 + edge_pen
            eg["N"][i] = center * 4 + edge_pen // 2

            b = center * 3 + r * 2
            if f in (0, 7):
                b -= 5
            mg["B"][i] = b
            eg["B"][i] = center * 3

            mg["R"][i] = r * 2 + (4 if f in (2, 3, 4, 5) else 0) + (12 if r == 6 else 0)
            eg["R"][i] = r * 4 + file_center

            mg["Q"][i] = center
            eg["Q"][i] = center * 2

            file_safety = 0
            if f in (1, 2, 6):
                file_safety = 18
            elif f in (0, 7):
                file_safety = 8
            elif f in (3, 4):
                file_safety = -8

            k_mg = -4 * center - 8 * r + file_safety
            if r == 0:
                k_mg += 20
            elif r == 1:
                k_mg += 8
            mg["K"][i] = k_mg
            eg["K"][i] = center * 5

    return mg, eg


PST_MG, PST_EG = _build_tables()
MIRROR = [(7 - (i >> 3)) * 8 + (i & 7) for i in range(64)]

DEADLINE = 0.0
NODES = 0
TT = {}
KILLERS = {}
HISTORY = {}


class SearchTimeout(Exception):
    pass


def _side_from_to_play(to_play: str) -> int:
    return 1 if str(to_play).lower().startswith("w") else -1


def _idx_to_sq(i: int) -> str:
    return FILES[i & 7] + str((i >> 3) + 1)


def _sq_to_idx(s: str) -> int:
    return (ord(s[0]) - 97) + 8 * (ord(s[1]) - 49)


def _move_to_uci(mv) -> str:
    return _idx_to_sq(mv[0]) + _idx_to_sq(mv[1]) + mv[2]


def _parse_board(pieces: dict[str, str]):
    board = ["."] * 64
    for sq, code in pieces.items():
        if not isinstance(sq, str) or not isinstance(code, str) or len(sq) < 2 or len(code) < 2:
            continue
        f = ord(sq[0]) - 97
        r = ord(sq[1]) - 49
        if not (0 <= f < 8 and 0 <= r < 8):
            continue
        color = code[0].lower()
        pt = code[1].upper()
        if color not in ("w", "b") or pt not in PIECE_VALUES:
            continue
        board[r * 8 + f] = pt if color == "w" else pt.lower()
    return board


def _own(piece: str, side: int) -> bool:
    return piece != "." and (piece.isupper() == (side == 1))


def _enemy(piece: str, side: int) -> bool:
    return piece != "." and (piece.isupper() != (side == 1))


def _is_attacked(board, sq: int, by_side: int) -> bool:
    f = sq & 7
    r = sq >> 3

    if by_side == 1:
        pr = r - 1
        if pr >= 0:
            if f > 0 and board[pr * 8 + f - 1] == "P":
                return True
            if f < 7 and board[pr * 8 + f + 1] == "P":
                return True
        n_char, b_char, r_char, q_char, k_char = "N", "B", "R", "Q", "K"
    else:
        pr = r + 1
        if pr < 8:
            if f > 0 and board[pr * 8 + f - 1] == "p":
                return True
            if f < 7 and board[pr * 8 + f + 1] == "p":
                return True
        n_char, b_char, r_char, q_char, k_char = "n", "b", "r", "q", "k"

    for df, dr in KNIGHT_DELTAS:
        nf, nr = f + df, r + dr
        if 0 <= nf < 8 and 0 <= nr < 8 and board[nr * 8 + nf] == n_char:
            return True

    for df, dr in KING_DELTAS:
        nf, nr = f + df, r + dr
        if 0 <= nf < 8 and 0 <= nr < 8 and board[nr * 8 + nf] == k_char:
            return True

    for df, dr in BISHOP_DIRS:
        nf, nr = f + df, r + dr
        while 0 <= nf < 8 and 0 <= nr < 8:
            pc = board[nr * 8 + nf]
            if pc != ".":
                if pc == b_char or pc == q_char:
                    return True
                break
            nf += df
            nr += dr

    for df, dr in ROOK_DIRS:
        nf, nr = f + df, r + dr
        while 0 <= nf < 8 and 0 <= nr < 8:
            pc = board[nr * 8 + nf]
            if pc != ".":
                if pc == r_char or pc == q_char:
                    return True
                break
            nf += df
            nr += dr

    return False


def _king_square(board, side: int) -> int:
    target = "K" if side == 1 else "k"
    try:
        return board.index(target)
    except ValueError:
        return -1


def _in_check(board, side: int) -> bool:
    ks = _king_square(board, side)
    return False if ks < 0 else _is_attacked(board, ks, -side)


def _make_move(board, mv):
    fr, to, promo = mv
    nb = board.copy()
    pc = nb[fr]
    nb[fr] = "."

    if pc != "." and pc.upper() == "K" and abs((to & 7) - (fr & 7)) == 2:
        nb[to] = pc
        if (to & 7) == 6:
            rook_from, rook_to = fr + 3, fr + 1
        else:
            rook_from, rook_to = fr - 4, fr - 1
        if 0 <= rook_from < 64 and 0 <= rook_to < 64:
            nb[rook_to] = nb[rook_from]
            nb[rook_from] = "."
        return nb

    if promo and pc != ".":
        nb[to] = promo.upper() if pc.isupper() else promo.lower()
    else:
        nb[to] = pc
    return nb


def _generate_castles(board, side: int):
    res = []
    if side == 1:
        if board[4] != "K" or _in_check(board, side):
            return res
        if board[7] == "R" and board[5] == "." and board[6] == ".":
            if not _is_attacked(board, 5, -side) and not _is_attacked(board, 6, -side):
                res.append((4, 6, ""))
        if board[0] == "R" and board[1] == "." and board[2] == "." and board[3] == ".":
            if not _is_attacked(board, 3, -side) and not _is_attacked(board, 2, -side):
                res.append((4, 2, ""))
    else:
        if board[60] != "k" or _in_check(board, side):
            return res
        if board[63] == "r" and board[61] == "." and board[62] == ".":
            if not _is_attacked(board, 61, -side) and not _is_attacked(board, 62, -side):
                res.append((60, 62, ""))
        if board[56] == "r" and board[57] == "." and board[58] == "." and board[59] == ".":
            if not _is_attacked(board, 59, -side) and not _is_attacked(board, 58, -side):
                res.append((60, 58, ""))
    return res


def _generate_pseudo(board, side: int, captures_only: bool = False):
    moves = []
    own_white = side == 1

    for fr, pc in enumerate(board):
        if pc == "." or pc.isupper() != own_white:
            continue

        pt = pc.upper()
        f = fr & 7
        r = fr >> 3

        if pt == "P":
            dr = 1 if side == 1 else -1
            start_rank = 1 if side == 1 else 6
            promo_rank = 7 if side == 1 else 0
            nr = r + dr

            if 0 <= nr < 8:
                to = nr * 8 + f
                if board[to] == ".":
                    if nr == promo_rank:
                        for pr in PROMOS:
                            moves.append((fr, to, pr))
                    elif not captures_only:
                        moves.append((fr, to, ""))
                        if r == start_rank:
                            nr2 = r + 2 * dr
                            to2 = nr2 * 8 + f
                            if board[to2] == ".":
                                moves.append((fr, to2, ""))

                for df in (-1, 1):
                    nf = f + df
                    if 0 <= nf < 8:
                        to = nr * 8 + nf
                        target = board[to]
                        if _enemy(target, side) and target.upper() != "K":
                            if nr == promo_rank:
                                for pr in PROMOS:
                                    moves.append((fr, to, pr))
                            else:
                                moves.append((fr, to, ""))

        elif pt == "N":
            for df, dr in KNIGHT_DELTAS:
                nf, nr = f + df, r + dr
                if 0 <= nf < 8 and 0 <= nr < 8:
                    to = nr * 8 + nf
                    target = board[to]
                    if target == ".":
                        if not captures_only:
                            moves.append((fr, to, ""))
                    elif _enemy(target, side) and target.upper() != "K":
                        moves.append((fr, to, ""))

        elif pt in ("B", "R", "Q"):
            if pt == "B":
                dirs = BISHOP_DIRS
            elif pt == "R":
                dirs = ROOK_DIRS
            else:
                dirs = BISHOP_DIRS + ROOK_DIRS

            for df, dr in dirs:
                nf, nr = f + df, r + dr
                while 0 <= nf < 8 and 0 <= nr < 8:
                    to = nr * 8 + nf
                    target = board[to]
                    if target == ".":
                        if not captures_only:
                            moves.append((fr, to, ""))
                    else:
                        if _enemy(target, side) and target.upper() != "K":
                            moves.append((fr, to, ""))
                        break
                    nf += df
                    nr += dr

        elif pt == "K":
            for df, dr in KING_DELTAS:
                nf, nr = f + df, r + dr
                if 0 <= nf < 8 and 0 <= nr < 8:
                    to = nr * 8 + nf
                    target = board[to]
                    if target == ".":
                        if not captures_only:
                            moves.append((fr, to, ""))
                    elif _enemy(target, side) and target.upper() != "K":
                        moves.append((fr, to, ""))

    return moves


def _generate_legal(board, side: int, captures_only: bool = False, include_castling: bool = False):
    cand = _generate_pseudo(board, side, captures_only)
    if include_castling and not captures_only:
        cand += _generate_castles(board, side)

    legal = []
    for mv in cand:
        nb = _make_move(board, mv)
        if not _in_check(nb, side):
            legal.append(mv)
    return legal


def _king_dist(a: int, b: int) -> int:
    return max(abs((a & 7) - (b & 7)), abs((a >> 3) - (b >> 3)))


def _king_shield(board, king_sq: int, side: int) -> int:
    if king_sq < 0:
        return 0
    f = king_sq & 7
    r = king_sq >> 3
    pawn = "P" if side == 1 else "p"
    dr = 1 if side == 1 else -1
    score = 0

    for df in (-1, 0, 1):
        nf = f + df
        if not (0 <= nf < 8):
            continue
        nr = r + dr
        if 0 <= nr < 8 and board[nr * 8 + nf] == pawn:
            score += 9
        else:
            nr2 = r + 2 * dr
            if 0 <= nr2 < 8 and board[nr2 * 8 + nf] == pawn:
                score += 4
    return score


def _mate_drive_bonus(winner_king: int, loser_king: int) -> int:
    lf = loser_king & 7
    lr = loser_king >> 3
    wf = winner_king & 7
    wr = winner_king >> 3
    edge = abs(2 * lf - 7) + abs(2 * lr - 7)
    king_distance = abs(wf - lf) + abs(wr - lr)
    return edge * 8 + (14 - king_distance) * 4


def _evaluate_white(board) -> int:
    mg = 0
    eg = 0
    phase = 0

    wp_files = [0] * 8
    bp_files = [0] * 8
    wp_by_file = [[] for _ in range(8)]
    bp_by_file = [[] for _ in range(8)]
    wpawns, bpawns = [], []
    wrooks, brooks = [], []

    white_bishops = 0
    black_bishops = 0
    white_material = 0
    black_material = 0
    wk = -1
    bk = -1

    for i, pc in enumerate(board):
        if pc == ".":
            continue
        color = 1 if pc.isupper() else -1
        pt = pc.upper()
        if pt not in PIECE_VALUES:
            continue

        sq = i if color == 1 else MIRROR[i]
        mg += color * (PIECE_VALUES[pt] + PST_MG[pt][sq])
        eg += color * (PIECE_VALUES[pt] + PST_EG[pt][sq])
        phase += PHASE[pt]

        if pt != "K":
            if color == 1:
                white_material += PIECE_VALUES[pt]
            else:
                black_material += PIECE_VALUES[pt]

        if pt == "P":
            f = i & 7
            r = i >> 3
            if color == 1:
                wpawns.append(i)
                wp_files[f] += 1
                wp_by_file[f].append(r)
            else:
                bpawns.append(i)
                bp_files[f] += 1
                bp_by_file[f].append(r)
        elif pt == "B":
            if color == 1:
                white_bishops += 1
            else:
                black_bishops += 1
        elif pt == "R":
            if color == 1:
                wrooks.append(i)
            else:
                brooks.append(i)
        elif pt == "K":
            if color == 1:
                wk = i
            else:
                bk = i

    phase = min(MAX_PHASE, phase)
    eg_weight = MAX_PHASE - phase
    score = (mg * phase + eg * eg_weight) // MAX_PHASE

    structure = 0

    if white_bishops >= 2:
        structure += 30
    if black_bishops >= 2:
        structure -= 30

    for f in range(8):
        if wp_files[f] > 1:
            structure -= 12 * (wp_files[f] - 1)
        if bp_files[f] > 1:
            structure += 12 * (bp_files[f] - 1)

    for sq in wpawns:
        f = sq & 7
        r = sq >> 3
        if (f == 0 or wp_files[f - 1] == 0) and (f == 7 or wp_files[f + 1] == 0):
            structure -= 8

        passed = True
        for ef in range(max(0, f - 1), min(7, f + 1) + 1):
            for br in bp_by_file[ef]:
                if br > r:
                    passed = False
                    break
            if not passed:
                break

        if passed:
            bonus = (PASSED_MG[r] * phase + PASSED_EG[r] * eg_weight) // MAX_PHASE
            structure += bonus
            if eg_weight and wk >= 0 and bk >= 0:
                promo_sq = 56 + f
                structure += (_king_dist(bk, promo_sq) - _king_dist(wk, promo_sq)) * 3 * eg_weight // MAX_PHASE

    for sq in bpawns:
        f = sq & 7
        r = sq >> 3
        rr = 7 - r
        if (f == 0 or bp_files[f - 1] == 0) and (f == 7 or bp_files[f + 1] == 0):
            structure += 8

        passed = True
        for ef in range(max(0, f - 1), min(7, f + 1) + 1):
            for wr in wp_by_file[ef]:
                if wr < r:
                    passed = False
                    break
            if not passed:
                break

        if passed:
            bonus = (PASSED_MG[rr] * phase + PASSED_EG[rr] * eg_weight) // MAX_PHASE
            structure -= bonus
            if eg_weight and wk >= 0 and bk >= 0:
                promo_sq = f
                structure -= (_king_dist(wk, promo_sq) - _king_dist(bk, promo_sq)) * 3 * eg_weight // MAX_PHASE

    for sq in wrooks:
        f = sq & 7
        r = sq >> 3
        if wp_files[f] == 0:
            structure += 10
            if bp_files[f] == 0:
                structure += 12
        if r == 6:
            structure += 15

    for sq in brooks:
        f = sq & 7
        r = sq >> 3
        if bp_files[f] == 0:
            structure -= 10
            if wp_files[f] == 0:
                structure -= 12
        if r == 1:
            structure -= 15

    if phase:
        structure += (_king_shield(board, wk, 1) - _king_shield(board, bk, -1)) * phase // MAX_PHASE

    if eg_weight and wk >= 0 and bk >= 0:
        mat_diff = white_material - black_material
        if mat_diff > 250:
            structure += _mate_drive_bonus(wk, bk) * eg_weight // MAX_PHASE
        elif mat_diff < -250:
            structure -= _mate_drive_bonus(bk, wk) * eg_weight // MAX_PHASE

    return score + structure


def _evaluate(board, side: int) -> int:
    return _evaluate_white(board) * side


def _tick():
    global NODES
    NODES += 1
    if (NODES & 127) == 0 and time.perf_counter() > DEADLINE:
        raise SearchTimeout()


def _psqt_delta(board, mv) -> int:
    fr, to, promo = mv
    pc = board[fr]
    if pc == ".":
        return 0

    color = 1 if pc.isupper() else -1
    before = fr if color == 1 else MIRROR[fr]
    after = to if color == 1 else MIRROR[to]
    pt = pc.upper()

    if pt == "K" and abs((to & 7) - (fr & 7)) == 2:
        return 30

    if promo:
        npt = promo.upper()
        return PIECE_VALUES[npt] - PIECE_VALUES["P"] + PST_MG[npt][after] - PST_MG["P"][before]

    return PST_MG[pt][after] - PST_MG[pt][before]


def _move_order_score(board, mv, side: int, ply: int, tt_best) -> int:
    if tt_best is not None and mv == tt_best:
        return 10_000_000

    fr, to, promo = mv
    pc = board[fr]
    target = board[to]
    score = 0

    if target != ".":
        score += 100_000 + 10 * PIECE_VALUES.get(target.upper(), 0) - PIECE_VALUES.get(pc.upper(), 0)

    if promo:
        score += 90_000 + PIECE_VALUES[promo.upper()]

    if target == "." and not promo:
        killers = KILLERS.get(ply)
        if killers:
            if mv == killers[0]:
                score += 80_000
            elif len(killers) > 1 and mv == killers[1]:
                score += 70_000
        score += min(HISTORY.get((side, fr, to, promo), 0), 60_000)

    score += _psqt_delta(board, mv)
    return score


def _record_cutoff(board, mv, side: int, depth: int, ply: int):
    if board[mv[1]] != "." or mv[2]:
        return

    killers = KILLERS.get(ply)
    if killers is None:
        KILLERS[ply] = (mv, None)
    elif killers[0] != mv:
        KILLERS[ply] = (mv, killers[0])

    key = (side, mv[0], mv[1], mv[2])
    HISTORY[key] = min(200_000, HISTORY.get(key, 0) + depth * depth * 4)


def _quiescence(board, side: int, alpha: int, beta: int, ply: int, qdepth: int) -> int:
    _tick()

    in_chk = _in_check(board, side)
    if in_chk:
        moves = _generate_legal(board, side)
        if not moves:
            return -MATE + ply
        if qdepth < -2:
            return _evaluate(board, side) - 80

        moves.sort(key=lambda m: _move_order_score(board, m, side, ply, None), reverse=True)
        for mv in moves:
            nb = _make_move(board, mv)
            score = -_quiescence(nb, -side, -beta, -alpha, ply + 1, qdepth - 1)
            if score >= beta:
                return score
            if score > alpha:
                alpha = score
        return alpha

    stand_pat = _evaluate(board, side)
    if stand_pat >= beta:
        return stand_pat
    if stand_pat > alpha:
        alpha = stand_pat

    if qdepth <= 0:
        return alpha

    moves = _generate_legal(board, side, captures_only=True)
    if not moves:
        return alpha

    moves.sort(key=lambda m: _move_order_score(board, m, side, ply, None), reverse=True)
    for mv in moves:
        nb = _make_move(board, mv)
        score = -_quiescence(nb, -side, -beta, -alpha, ply + 1, qdepth - 1)
        if score >= beta:
            return score
        if score > alpha:
            alpha = score

    return alpha


def _negamax(board, side: int, depth: int, alpha: int, beta: int, ply: int) -> int:
    _tick()

    if depth <= 0:
        return _quiescence(board, side, alpha, beta, ply, 4)

    alpha_orig = alpha
    beta_orig = beta
    key = "".join(board) + ("w" if side == 1 else "b")

    tt_best = None
    entry = TT.get(key)
    if entry is not None:
        e_depth, e_flag, e_val, e_best = entry
        tt_best = e_best
        if e_depth >= depth:
            if e_flag == 0:
                return e_val
            if e_flag == 1:
                alpha = max(alpha, e_val)
            elif e_flag == 2:
                beta = min(beta, e_val)
            if alpha >= beta:
                return e_val

    in_chk = _in_check(board, side)
    moves = _generate_legal(board, side)

    if not moves:
        return -MATE + ply if in_chk else 0

    moves.sort(key=lambda m: _move_order_score(board, m, side, ply, tt_best), reverse=True)

    best_val = -INF
    best_move = None

    for i, mv in enumerate(moves):
        nb = _make_move(board, mv)

        if i == 0:
            score = -_negamax(nb, -side, depth - 1, -beta, -alpha, ply + 1)
        else:
            score = -_negamax(nb, -side, depth - 1, -alpha - 1, -alpha, ply + 1)
            if alpha < score < beta:
                score = -_negamax(nb, -side, depth - 1, -beta, -alpha, ply + 1)

        if score > best_val:
            best_val = score
            best_move = mv

        if score > alpha:
            alpha = score

        if alpha >= beta:
            _record_cutoff(board, mv, side, depth, ply)
            break

    if best_val <= alpha_orig:
        flag = 2
    elif best_val >= beta_orig:
        flag = 1
    else:
        flag = 0

    TT[key] = (depth, flag, best_val, best_move)
    return best_val


def _root_static_score(board, nb, side: int, mv, piece_count: int) -> int:
    score = _evaluate(nb, side)

    fr, to, promo = mv
    pc = board[fr]
    if pc == ".":
        return score

    pt = pc.upper()
    if piece_count >= 24:
        home_rank = 0 if side == 1 else 7
        if pt in ("N", "B") and (fr >> 3) == home_rank:
            score += 12
        if pt == "Q":
            score -= 10
        if pt == "P" and (to & 7) in (3, 4):
            score += 6
        if pt == "P" and abs((to >> 3) - (fr >> 3)) == 2 and (to & 7) in (3, 4):
            score += 8

    if promo:
        score += 25

    return score


def _max_depth(piece_count: int, move_count: int) -> int:
    if piece_count <= 4:
        d = 10
    elif piece_count <= 6:
        d = 9
    elif piece_count <= 8:
        d = 8
    elif piece_count <= 12:
        d = 7
    elif piece_count <= 18:
        d = 6
    elif piece_count <= 24:
        d = 5
    else:
        d = 4

    if move_count <= 8:
        d += 1
    if move_count >= 45:
        d -= 1

    return max(3, d)


def _fallback(pieces: dict[str, str], to_play: str) -> str:
    try:
        board = _parse_board(pieces)
        side = _side_from_to_play(to_play)
        moves = _generate_legal(board, side)
        if not moves:
            moves = _generate_legal(board, side, include_castling=True)
        if moves:
            return _move_to_uci(moves[0])
        pseudo = _generate_pseudo(board, side)
        if pseudo:
            return _move_to_uci(pseudo[0])
    except Exception:
        pass
    return "a1a1"


def _policy_core(pieces: dict[str, str], to_play: str) -> str:
    global DEADLINE, NODES, TT, KILLERS, HISTORY

    start = time.perf_counter()
    DEADLINE = start + 0.86
    NODES = 0
    TT = {}
    KILLERS = {}
    HISTORY = {}

    board = _parse_board(pieces)
    side = _side_from_to_play(to_play)

    moves = _generate_legal(board, side)
    if not moves:
        castle_moves = _generate_legal(board, side, include_castling=True)
        if castle_moves:
            return _move_to_uci(castle_moves[0])
        pseudo = _generate_pseudo(board, side)
        return _move_to_uci(pseudo[0]) if pseudo else "a1a1"

    if len(moves) == 1:
        return _move_to_uci(moves[0])

    piece_count = sum(1 for p in board if p != ".")

    scored = []
    for mv in moves:
        nb = _make_move(board, mv)
        gives_check = _in_check(nb, -side)
        score = _root_static_score(board, nb, side, mv, piece_count)
        if gives_check:
            score += 45
            if not _generate_legal(nb, -side):
                return _move_to_uci(mv)
        scored.append((score, mv))

    scored.sort(key=lambda x: x[0], reverse=True)
    best = scored[0][1]
    root_scores = {mv: score for score, mv in scored}

    max_depth = _max_depth(piece_count, len(moves))

    for depth in range(1, max_depth + 1):
        if time.perf_counter() > DEADLINE:
            break

        try:
            ordered = sorted(
                moves,
                key=lambda m: (
                    m == best,
                    root_scores.get(m, -INF),
                    _move_order_score(board, m, side, 0, None),
                ),
                reverse=True,
            )

            alpha = -INF
            beta = INF
            current_best = None
            current_score = -INF
            searched = 0

            for mv in ordered:
                if time.perf_counter() > DEADLINE:
                    raise SearchTimeout()

                nb = _make_move(board, mv)
                if searched == 0:
                    score = -_negamax(nb, -side, depth - 1, -beta, -alpha, 1)
                else:
                    score = -_negamax(nb, -side, depth - 1, -alpha - 1, -alpha, 1)
                    if alpha < score < beta:
                        score = -_negamax(nb, -side, depth - 1, -beta, -alpha, 1)

                root_scores[mv] = score
                searched += 1

                if score > current_score:
                    current_score = score
                    current_best = mv
                if score > alpha:
                    alpha = score

            if searched == len(ordered) and current_best is not None:
                best = current_best
                if current_score > MATE - 1000:
                    break

        except SearchTimeout:
            break

    return _move_to_uci(best)


def _respect_external_legal_moves(answer: str) -> str:
    lm = globals().get("legal_moves", None)
    if lm is None:
        return answer
    try:
        if isinstance(lm, str):
            legal = [lm]
        else:
            legal = [str(x) for x in lm]
        if not legal:
            return answer
        if answer in legal:
            return answer
        return legal[0]
    except Exception:
        return answer


def policy(pieces: dict[str, str], to_play: str) -> str:
    try:
        ans = _policy_core(pieces, to_play)
    except Exception:
        ans = _fallback(pieces, to_play)
    return _respect_external_legal_moves(ans)
