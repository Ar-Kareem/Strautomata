
from __future__ import annotations

import time

FILES = "abcdefgh"
I2S = [FILES[i % 8] + str(i // 8 + 1) for i in range(64)]
S2I = {s: i for i, s in enumerate(I2S)}

OPP = {"w": "b", "b": "w"}

VALUES = {
    "P": 100,
    "N": 320,
    "B": 330,
    "R": 500,
    "Q": 900,
    "K": 0,
}

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

PAWN_PST = [
     0,   0,   0,   0,   0,   0,   0,   0,
     5,  10,  10, -20, -20,  10,  10,   5,
     5,  -5, -10,   0,   0, -10,  -5,   5,
     0,   0,   0,  20,  20,   0,   0,   0,
     5,   5,  10,  25,  25,  10,   5,   5,
    10,  10,  20,  30,  30,  20,  10,  10,
    50,  50,  50,  50,  50,  50,  50,  50,
     0,   0,   0,   0,   0,   0,   0,   0,
]

KNIGHT_PST = [
    -50, -40, -30, -30, -30, -30, -40, -50,
    -40, -20,   0,   5,   5,   0, -20, -40,
    -30,   5,  10,  15,  15,  10,   5, -30,
    -30,   0,  15,  20,  20,  15,   0, -30,
    -30,   5,  15,  20,  20,  15,   5, -30,
    -30,   0,  10,  15,  15,  10,   0, -30,
    -40, -20,   0,   0,   0,   0, -20, -40,
    -50, -40, -30, -30, -30, -30, -40, -50,
]

BISHOP_PST = [
    -20, -10, -10, -10, -10, -10, -10, -20,
    -10,   5,   0,   0,   0,   0,   5, -10,
    -10,  10,  10,  10,  10,  10,  10, -10,
    -10,   0,  10,  10,  10,  10,   0, -10,
    -10,   5,   5,  10,  10,   5,   5, -10,
    -10,   0,   5,  10,  10,   5,   0, -10,
    -10,   0,   0,   0,   0,   0,   0, -10,
    -20, -10, -10, -10, -10, -10, -10, -20,
]

ROOK_PST = [
     0,   0,   0,   5,   5,   0,   0,   0,
    -5,   0,   0,   0,   0,   0,   0,  -5,
    -5,   0,   0,   0,   0,   0,   0,  -5,
    -5,   0,   0,   0,   0,   0,   0,  -5,
    -5,   0,   0,   0,   0,   0,   0,  -5,
    -5,   0,   0,   0,   0,   0,   0,  -5,
     5,  10,  10,  10,  10,  10,  10,   5,
     0,   0,   0,   5,   5,   0,   0,   0,
]

QUEEN_PST = [
    -20, -10, -10,  -5,  -5, -10, -10, -20,
    -10,   0,   5,   0,   0,   0,   0, -10,
    -10,   5,   5,   5,   5,   5,   0, -10,
      0,   0,   5,   5,   5,   5,   0,  -5,
     -5,   0,   5,   5,   5,   5,   0,  -5,
    -10,   0,   5,   5,   5,   5,   0, -10,
    -10,   0,   0,   0,   0,   0,   0, -10,
    -20, -10, -10,  -5,  -5, -10, -10, -20,
]

KING_MID_PST = [
     20,  30,  10,   0,   0,  10,  30,  20,
     20,  20,   0,   0,   0,   0,  20,  20,
    -10, -20, -20, -20, -20, -20, -20, -10,
    -20, -30, -30, -40, -40, -30, -30, -20,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
]

KING_END_PST = [
    -50, -30, -30, -30, -30, -30, -30, -50,
    -30, -10,   0,   0,   0,   0, -10, -30,
    -30,   0,  20,  30,  30,  20,   0, -30,
    -30,   0,  30,  40,  40,  30,   0, -30,
    -30,   0,  30,  40,  40,  30,   0, -30,
    -30,   0,  20,  30,  30,  20,   0, -30,
    -30, -10,   0,   0,   0,   0, -10, -30,
    -50, -30, -30, -30, -30, -30, -30, -50,
]

PSTS = {
    "P": PAWN_PST,
    "N": KNIGHT_PST,
    "B": BISHOP_PST,
    "R": ROOK_PST,
    "Q": QUEEN_PST,
}

INF = 100000000
MATE = 100000

_END_TIME = 0.0
_NODES = 0
_TT = {}


class _SearchTimeout(Exception):
    pass


def _tick():
    global _NODES
    _NODES += 1
    if (_NODES & 2047) == 0 and time.perf_counter() > _END_TIME:
        raise _SearchTimeout()


def _mirror(i):
    return (7 - (i >> 3)) * 8 + (i & 7)


def _on_board(f, r):
    return 0 <= f < 8 and 0 <= r < 8


def _uci(m):
    return I2S[m[0]] + I2S[m[1]] + m[2]


def _board_from_pieces(pieces):
    board = [None] * 64
    for sq, pc in pieces.items():
        idx = S2I.get(sq)
        if idx is not None and isinstance(pc, str) and len(pc) == 2:
            if pc[0] in ("w", "b") and pc[1] in ("K", "Q", "R", "B", "N", "P"):
                board[idx] = pc
    return board


def _make(board, m):
    fr, to, promo = m
    moved = board[fr]
    captured = board[to]
    board[fr] = None
    if promo:
        board[to] = moved[0] + promo.upper()
    else:
        board[to] = moved
    return moved, captured


def _undo(board, m, state):
    fr, to, _promo = m
    moved, captured = state
    board[fr] = moved
    board[to] = captured


def _attacked(board, sq, by_side):
    f = sq & 7
    r = sq >> 3

    if by_side == "w":
        pr = r - 1
        if pr >= 0:
            for pf in (f - 1, f + 1):
                if 0 <= pf < 8 and board[pr * 8 + pf] == "wP":
                    return True
    else:
        pr = r + 1
        if pr < 8:
            for pf in (f - 1, f + 1):
                if 0 <= pf < 8 and board[pr * 8 + pf] == "bP":
                    return True

    for df, dr in KNIGHT_DELTAS:
        nf, nr = f + df, r + dr
        if _on_board(nf, nr) and board[nr * 8 + nf] == by_side + "N":
            return True

    for df, dr in KING_DELTAS:
        nf, nr = f + df, r + dr
        if _on_board(nf, nr) and board[nr * 8 + nf] == by_side + "K":
            return True

    for df, dr in BISHOP_DIRS:
        nf, nr = f + df, r + dr
        while _on_board(nf, nr):
            p = board[nr * 8 + nf]
            if p is not None:
                if p[0] == by_side and p[1] in ("B", "Q"):
                    return True
                break
            nf += df
            nr += dr

    for df, dr in ROOK_DIRS:
        nf, nr = f + df, r + dr
        while _on_board(nf, nr):
            p = board[nr * 8 + nf]
            if p is not None:
                if p[0] == by_side and p[1] in ("R", "Q"):
                    return True
                break
            nf += df
            nr += dr

    return False


def _in_check(board, side):
    king = side + "K"
    for i, p in enumerate(board):
        if p == king:
            return _attacked(board, i, OPP[side])
    return False


def _gen_pseudo(board, side):
    moves = []
    enemy = OPP[side]

    for i, p in enumerate(board):
        if p is None or p[0] != side:
            continue

        f = i & 7
        r = i >> 3
        pt = p[1]

        if pt == "P":
            dr = 1 if side == "w" else -1
            start_rank = 1 if side == "w" else 6
            nr = r + dr

            if 0 <= nr < 8:
                one = nr * 8 + f
                if board[one] is None:
                    if nr == 7 or nr == 0:
                        for promo in PROMOS:
                            moves.append((i, one, promo))
                    else:
                        moves.append((i, one, ""))
                        if r == start_rank:
                            two = (r + 2 * dr) * 8 + f
                            if board[two] is None:
                                moves.append((i, two, ""))

                for df in (-1, 1):
                    nf = f + df
                    if 0 <= nf < 8:
                        to = nr * 8 + nf
                        target = board[to]
                        if target is not None and target[0] == enemy and target[1] != "K":
                            if nr == 7 or nr == 0:
                                for promo in PROMOS:
                                    moves.append((i, to, promo))
                            else:
                                moves.append((i, to, ""))

        elif pt == "N":
            for df, dr in KNIGHT_DELTAS:
                nf, nr = f + df, r + dr
                if _on_board(nf, nr):
                    to = nr * 8 + nf
                    target = board[to]
                    if target is None or (target[0] == enemy and target[1] != "K"):
                        moves.append((i, to, ""))

        elif pt in ("B", "R", "Q"):
            dirs = BISHOP_DIRS if pt == "B" else ROOK_DIRS if pt == "R" else QUEEN_DIRS
            for df, dr in dirs:
                nf, nr = f + df, r + dr
                while _on_board(nf, nr):
                    to = nr * 8 + nf
                    target = board[to]
                    if target is None:
                        moves.append((i, to, ""))
                    else:
                        if target[0] == enemy and target[1] != "K":
                            moves.append((i, to, ""))
                        break
                    nf += df
                    nr += dr

        elif pt == "K":
            for df, dr in KING_DELTAS:
                nf, nr = f + df, r + dr
                if _on_board(nf, nr):
                    to = nr * 8 + nf
                    target = board[to]
                    if target is None or (target[0] == enemy and target[1] != "K"):
                        moves.append((i, to, ""))

    return moves


def _legal_moves(board, side, tactical_only=False):
    moves = []
    currently_in_check = _in_check(board, side) if tactical_only else False

    for m in _gen_pseudo(board, side):
        if tactical_only and not currently_in_check:
            if board[m[1]] is None and not m[2]:
                continue

        st = _make(board, m)
        try:
            if not _in_check(board, side):
                moves.append(m)
        finally:
            _undo(board, m, st)

    return moves


def _evaluate(board, side):
    score = 0
    mat = {"w": 0, "b": 0}
    bishops = {"w": 0, "b": 0}
    queens = {"w": 0, "b": 0}
    pawns = {"w": [], "b": []}
    pawn_files = {"w": [0] * 8, "b": [0] * 8}
    rooks = {"w": [], "b": []}
    kings = {}

    for i, p in enumerate(board):
        if p is None:
            continue
        c, pt = p[0], p[1]
        if pt != "K":
            mat[c] += VALUES[pt]
        if pt == "B":
            bishops[c] += 1
        elif pt == "Q":
            queens[c] += 1
        elif pt == "P":
            pawns[c].append(i)
            pawn_files[c][i & 7] += 1
        elif pt == "R":
            rooks[c].append(i)
        elif pt == "K":
            kings[c] = i

    total_mat = mat["w"] + mat["b"]
    king_table = KING_END_PST if total_mat < 2200 or (queens["w"] == 0 and queens["b"] == 0 and total_mat < 3600) else KING_MID_PST

    for i, p in enumerate(board):
        if p is None:
            continue
        c, pt = p[0], p[1]
        idx = i if c == "w" else _mirror(i)
        if pt == "K":
            val = king_table[idx]
        else:
            val = VALUES[pt] + PSTS[pt][idx]
        score += val if c == "w" else -val

    for c in ("w", "b"):
        sign = 1 if c == "w" else -1
        enemy = OPP[c]

        if bishops[c] >= 2:
            score += sign * 30

        for f, cnt in enumerate(pawn_files[c]):
            if cnt > 1:
                score -= sign * 12 * (cnt - 1)

        for sq in pawns[c]:
            f = sq & 7
            r = sq >> 3

            if (f == 0 or pawn_files[c][f - 1] == 0) and (f == 7 or pawn_files[c][f + 1] == 0):
                score -= sign * 8

            passed = True
            if c == "w":
                for esq in pawns[enemy]:
                    ef, er = esq & 7, esq >> 3
                    if abs(ef - f) <= 1 and er > r:
                        passed = False
                        break
                if passed:
                    adv = r
                    score += 18 + adv * adv * 3
            else:
                for esq in pawns[enemy]:
                    ef, er = esq & 7, esq >> 3
                    if abs(ef - f) <= 1 and er < r:
                        passed = False
                        break
                if passed:
                    adv = 7 - r
                    score -= 18 + adv * adv * 3

        for sq in rooks[c]:
            f = sq & 7
            r = sq >> 3
            bonus = 0
            if pawn_files[c][f] == 0:
                bonus += 10
                if pawn_files[enemy][f] == 0:
                    bonus += 8
            if (c == "w" and r == 6) or (c == "b" and r == 1):
                bonus += 12
            score += sign * bonus

    if total_mat > 1800:
        for c in ("w", "b"):
            if c not in kings:
                continue
            sign = 1 if c == "w" else -1
            k = kings[c]
            f, r = k & 7, k >> 3
            shield = 0
            if c == "w" and r <= 2:
                sr = r + 1
                for df in (-1, 0, 1):
                    nf = f + df
                    if 0 <= nf < 8:
                        shield += 7 if board[sr * 8 + nf] == "wP" else -4
            elif c == "b" and r >= 5:
                sr = r - 1
                for df in (-1, 0, 1):
                    nf = f + df
                    if 0 <= nf < 8:
                        shield += 7 if board[sr * 8 + nf] == "bP" else -4
            score += sign * shield

    if "w" in kings and "b" in kings:
        wk, bk = kings["w"], kings["b"]
        wf, wr = wk & 7, wk >> 3
        bf, br = bk & 7, bk >> 3
        dist = abs(wf - bf) + abs(wr - br)
        material_diff = mat["w"] - mat["b"]

        if material_diff > 500:
            edge = min(bf, 7 - bf, br, 7 - br)
            score += (3 - edge) * 25 + (14 - dist) * 4
        elif material_diff < -500:
            edge = min(wf, 7 - wf, wr, 7 - wr)
            score -= (3 - edge) * 25 + (14 - dist) * 4

    return score if side == "w" else -score


def _move_order_score(board, m, side, tt_move=None):
    if tt_move is not None and m == tt_move:
        score = 10000000
    else:
        score = 0

    fr, to, promo = m
    moved = board[fr]
    target = board[to]

    if moved is None:
        return score

    if target is not None:
        score += 100000 + 10 * VALUES.get(target[1], 0) - VALUES.get(moved[1], 0)

    if promo:
        score += 80000 + VALUES.get(promo.upper(), 0)

    tf, tr = to & 7, to >> 3
    score += 14 - (abs(2 * tf - 7) + abs(2 * tr - 7))

    if moved[1] == "P":
        adv = tr if moved[0] == "w" else 7 - tr
        score += adv * 3

    if moved[1] in ("N", "B"):
        if (moved[0] == "w" and (fr >> 3) == 0) or (moved[0] == "b" and (fr >> 3) == 7):
            score += 15

    return score


def _gives_check(board, m, side):
    st = _make(board, m)
    try:
        return _in_check(board, OPP[side])
    finally:
        _undo(board, m, st)


def _order_moves(board, moves, side, tt_move=None, root=False):
    if root:
        moves.sort(
            key=lambda m: _move_order_score(board, m, side, tt_move) + (5000 if _gives_check(board, m, side) else 0),
            reverse=True,
        )
    else:
        moves.sort(key=lambda m: _move_order_score(board, m, side, tt_move), reverse=True)
    return moves


def _qsearch(board, side, alpha, beta, ply, qdepth):
    _tick()

    in_check = _in_check(board, side)

    if in_check:
        moves = _legal_moves(board, side, tactical_only=False)
        if not moves:
            return -MATE + ply
    else:
        stand = _evaluate(board, side)
        if stand >= beta:
            return beta
        if stand > alpha:
            alpha = stand

        if qdepth <= 0:
            return alpha

        moves = _legal_moves(board, side, tactical_only=True)
        if not moves:
            return alpha

    _order_moves(board, moves, side)

    for m in moves:
        st = _make(board, m)
        try:
            score = -_qsearch(board, OPP[side], -beta, -alpha, ply + 1, qdepth - 1)
        finally:
            _undo(board, m, st)

        if score >= beta:
            return beta
        if score > alpha:
            alpha = score

    return alpha


def _negamax(board, side, depth, alpha, beta, ply):
    _tick()

    if depth <= 0:
        return _qsearch(board, side, alpha, beta, ply, 4)

    alpha_start = alpha
    beta_start = beta
    tt_move = None
    key = None
    use_tt = depth >= 2

    if use_tt:
        key = (tuple(board), side)
        entry = _TT.get(key)
        if entry is not None:
            edepth, escore, eflag, emove = entry
            tt_move = emove
            if edepth >= depth:
                if eflag == 0:
                    return escore
                if eflag == 1 and escore >= beta:
                    return escore
                if eflag == 2 and escore <= alpha:
                    return escore

    in_check = _in_check(board, side)
    moves = _legal_moves(board, side, tactical_only=False)

    if not moves:
        return -MATE + ply if in_check else 0

    _order_moves(board, moves, side, tt_move=tt_move)

    best = None
    value = -INF

    for m in moves:
        st = _make(board, m)
        try:
            score = -_negamax(board, OPP[side], depth - 1, -beta, -alpha, ply + 1)
        finally:
            _undo(board, m, st)

        if score > value:
            value = score
            best = m

        if value > alpha:
            alpha = value

        if alpha >= beta:
            break

    if use_tt and key is not None and abs(value) < MATE - 1000:
        if value <= alpha_start:
            flag = 2
        elif value >= beta_start:
            flag = 1
        else:
            flag = 0
        _TT[key] = (depth, value, flag, best)

    return value


def _search_root(board, side, legal, depth):
    alpha = -INF
    beta = INF
    best = legal[0]
    best_score = -INF

    for m in legal:
        if time.perf_counter() > _END_TIME:
            raise _SearchTimeout()

        st = _make(board, m)
        try:
            score = -_negamax(board, OPP[side], depth - 1, -beta, -alpha, 1)
        finally:
            _undo(board, m, st)

        if score > best_score:
            best_score = score
            best = m

        if score > alpha:
            alpha = score

    return best, best_score


def _mate_in_one(board, side, legal):
    opp = OPP[side]
    for m in legal:
        st = _make(board, m)
        try:
            if _in_check(board, opp):
                if not _legal_moves(board, opp, tactical_only=False):
                    return m
        finally:
            _undo(board, m, st)
    return None


def _emergency_move(pieces, to_play):
    try:
        side = "w" if str(to_play).lower().startswith("w") else "b"
        board = _board_from_pieces(pieces)
        legal = _legal_moves(board, side)
        if legal:
            return _uci(legal[0])
        pseudo = _gen_pseudo(board, side)
        if pseudo:
            return _uci(pseudo[0])
    except Exception:
        pass
    return "a1a1"


def policy(pieces: dict[str, str], to_play: str) -> str:
    global _END_TIME, _NODES, _TT

    try:
        side = "w" if str(to_play).lower().startswith("w") else "b"
        board = _board_from_pieces(pieces)

        legal = _legal_moves(board, side)
        if not legal:
            return _emergency_move(pieces, to_play)
        if len(legal) == 1:
            return _uci(legal[0])

        _END_TIME = time.perf_counter() + 0.86
        _NODES = 0
        _TT = {}

        _order_moves(board, legal, side, root=True)

        mate = _mate_in_one(board, side, legal)
        if mate is not None:
            return _uci(mate)

        best_move = legal[0]
        piece_count = sum(1 for p in board if p is not None)

        if piece_count <= 6:
            max_depth = 8
        elif piece_count <= 12:
            max_depth = 7
        elif len(legal) <= 12:
            max_depth = 6
        elif len(legal) <= 28:
            max_depth = 5
        else:
            max_depth = 4

        for depth in range(1, max_depth + 1):
            if time.perf_counter() > _END_TIME:
                break

            try:
                bm, bs = _search_root(board, side, legal, depth)
                best_move = bm

                if best_move in legal:
                    legal.remove(best_move)
                    legal.insert(0, best_move)

                if abs(bs) > MATE - 1000:
                    break

            except _SearchTimeout:
                break

        return _uci(best_move)

    except Exception:
        return _emergency_move(pieces, to_play)
