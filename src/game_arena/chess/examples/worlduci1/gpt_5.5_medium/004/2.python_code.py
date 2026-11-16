
import time
import math

FILES = "abcdefgh"
VALUES = {"P": 100, "N": 320, "B": 330, "R": 500, "Q": 900, "K": 0}
MATE = 1000000
INF = 10**9

_ENDTIME = 0.0


class _Timeout(Exception):
    pass


def _idx(s):
    return (ord(s[1]) - 49) * 8 + (ord(s[0]) - 97)


def _sq(i):
    return FILES[i % 8] + str(i // 8 + 1)


def _color(to_play):
    return "w" if to_play.lower().startswith("w") else "b"


def _opp(c):
    return "b" if c == "w" else "w"


def _board_from_pieces(pieces):
    b = [None] * 64
    for s, p in pieces.items():
        if len(s) == 2 and s[0] in FILES and s[1] in "12345678":
            b[_idx(s)] = p
    return b


def _find_king(board, color):
    target = color + "K"
    for i, p in enumerate(board):
        if p == target:
            return i
    return -1


def _attacked(board, sq, by_color):
    f, r = sq % 8, sq // 8

    # Pawn attacks
    pawn_dir = 1 if by_color == "w" else -1
    pr = r - pawn_dir
    if 0 <= pr < 8:
        for df in (-1, 1):
            pf = f - df
            if 0 <= pf < 8:
                if board[pr * 8 + pf] == by_color + "P":
                    return True

    # Knight attacks
    for df, dr in ((1, 2), (2, 1), (-1, 2), (-2, 1),
                   (1, -2), (2, -1), (-1, -2), (-2, -1)):
        nf, nr = f + df, r + dr
        if 0 <= nf < 8 and 0 <= nr < 8:
            if board[nr * 8 + nf] == by_color + "N":
                return True

    # King attacks
    for df in (-1, 0, 1):
        for dr in (-1, 0, 1):
            if df == 0 and dr == 0:
                continue
            nf, nr = f + df, r + dr
            if 0 <= nf < 8 and 0 <= nr < 8:
                if board[nr * 8 + nf] == by_color + "K":
                    return True

    # Sliding attacks
    for df, dr, attackers in (
        (1, 0, "RQ"), (-1, 0, "RQ"), (0, 1, "RQ"), (0, -1, "RQ"),
        (1, 1, "BQ"), (1, -1, "BQ"), (-1, 1, "BQ"), (-1, -1, "BQ")
    ):
        nf, nr = f + df, r + dr
        while 0 <= nf < 8 and 0 <= nr < 8:
            p = board[nr * 8 + nf]
            if p is not None:
                return p[0] == by_color and p[1] in attackers
            nf += df
            nr += dr

    return False


def _in_check(board, color):
    k = _find_king(board, color)
    if k < 0:
        return False
    return _attacked(board, k, _opp(color))


def _apply(board, move):
    nb = board[:]
    fr = _idx(move[:2])
    to = _idx(move[2:4])
    piece = nb[fr]
    if piece is None:
        return nb

    color, typ = piece[0], piece[1]
    target = nb[to]
    nb[fr] = None

    # En-passant-like move, if such a legal move was supplied externally.
    if typ == "P" and target is None and abs((to % 8) - (fr % 8)) == 1:
        cap = to - 8 if color == "w" else to + 8
        if 0 <= cap < 64 and nb[cap] == _opp(color) + "P":
            nb[cap] = None

    # Castling rook move.
    if typ == "K" and abs((to % 8) - (fr % 8)) == 2:
        if to % 8 == 6:
            rf, rt = fr + 3, fr + 1
        else:
            rf, rt = fr - 4, fr - 1
        if 0 <= rf < 64 and nb[rf] == color + "R":
            nb[rt] = nb[rf]
            nb[rf] = None

    if len(move) > 4 and typ == "P":
        nb[to] = color + move[4].upper()
    else:
        nb[to] = piece
    return nb


def _add_move(moves, fr, to, promo=False):
    if promo:
        base = _sq(fr) + _sq(to)
        moves.extend([base + "q", base + "r", base + "b", base + "n"])
    else:
        moves.append(_sq(fr) + _sq(to))


def _pseudo_moves(board, color, include_castle=False):
    moves = []
    enemy = _opp(color)

    for fr, p in enumerate(board):
        if p is None or p[0] != color:
            continue

        typ = p[1]
        f, r = fr % 8, fr // 8

        if typ == "P":
            step = 8 if color == "w" else -8
            start_rank = 1 if color == "w" else 6
            promo_rank = 7 if color == "w" else 0

            one = fr + step
            if 0 <= one < 64 and board[one] is None:
                _add_move(moves, fr, one, one // 8 == promo_rank)
                two = fr + 2 * step
                if r == start_rank and 0 <= two < 64 and board[two] is None:
                    _add_move(moves, fr, two)

            for df in (-1, 1):
                nf = f + df
                if 0 <= nf < 8:
                    to = fr + step + df
                    if 0 <= to < 64:
                        q = board[to]
                        if q is not None and q[0] == enemy and q[1] != "K":
                            _add_move(moves, fr, to, to // 8 == promo_rank)

        elif typ == "N":
            for df, dr in ((1, 2), (2, 1), (-1, 2), (-2, 1),
                           (1, -2), (2, -1), (-1, -2), (-2, -1)):
                nf, nr = f + df, r + dr
                if 0 <= nf < 8 and 0 <= nr < 8:
                    to = nr * 8 + nf
                    q = board[to]
                    if q is None or (q[0] == enemy and q[1] != "K"):
                        _add_move(moves, fr, to)

        elif typ in ("B", "R", "Q"):
            dirs = []
            if typ in ("B", "Q"):
                dirs += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
            if typ in ("R", "Q"):
                dirs += [(1, 0), (-1, 0), (0, 1), (0, -1)]

            for df, dr in dirs:
                nf, nr = f + df, r + dr
                while 0 <= nf < 8 and 0 <= nr < 8:
                    to = nr * 8 + nf
                    q = board[to]
                    if q is None:
                        _add_move(moves, fr, to)
                    else:
                        if q[0] == enemy and q[1] != "K":
                            _add_move(moves, fr, to)
                        break
                    nf += df
                    nr += dr

        elif typ == "K":
            for df in (-1, 0, 1):
                for dr in (-1, 0, 1):
                    if df == 0 and dr == 0:
                        continue
                    nf, nr = f + df, r + dr
                    if 0 <= nf < 8 and 0 <= nr < 8:
                        to = nr * 8 + nf
                        q = board[to]
                        if q is None or (q[0] == enemy and q[1] != "K"):
                            _add_move(moves, fr, to)

            # Conservative castling generation for fallback-only situations.
            if include_castle and not _in_check(board, color):
                if color == "w" and fr == 4:
                    if board[7] == "wR" and board[5] is None and board[6] is None:
                        if not _attacked(board, 5, enemy) and not _attacked(board, 6, enemy):
                            moves.append("e1g1")
                    if board[0] == "wR" and board[1] is None and board[2] is None and board[3] is None:
                        if not _attacked(board, 3, enemy) and not _attacked(board, 2, enemy):
                            moves.append("e1c1")
                elif color == "b" and fr == 60:
                    if board[63] == "bR" and board[61] is None and board[62] is None:
                        if not _attacked(board, 61, enemy) and not _attacked(board, 62, enemy):
                            moves.append("e8g8")
                    if board[56] == "bR" and board[57] is None and board[58] is None and board[59] is None:
                        if not _attacked(board, 59, enemy) and not _attacked(board, 58, enemy):
                            moves.append("e8c8")

    return moves


def _legal_moves(board, color, include_castle=False):
    out = []
    for m in _pseudo_moves(board, color, include_castle):
        nb = _apply(board, m)
        if not _in_check(nb, color):
            out.append(m)
    return out


def _passed_pawn(board, sq, color):
    f, r = sq % 8, sq // 8
    enemy = _opp(color) + "P"
    if color == "w":
        ranks = range(r + 1, 8)
    else:
        ranks = range(r - 1, -1, -1)
    for rr in ranks:
        for ff in (f - 1, f, f + 1):
            if 0 <= ff < 8 and board[rr * 8 + ff] == enemy:
                return False
    return True


def _eval_white_minus_black(board):
    score = 0
    bishops = {"w": 0, "b": 0}
    nonpawn_material = 0

    for p in board:
        if p and p[1] not in ("P", "K"):
            nonpawn_material += VALUES[p[1]]

    endgame = nonpawn_material <= 2400

    for sq, p in enumerate(board):
        if p is None:
            continue

        c, t = p[0], p[1]
        f, r = sq % 8, sq // 8
        rr = r if c == "w" else 7 - r
        sign = 1 if c == "w" else -1
        val = VALUES[t]
        bonus = 0

        center_manhattan = abs(f - 3.5) + abs(r - 3.5)
        center_euclid = (f - 3.5) ** 2 + (r - 3.5) ** 2

        if t == "P":
            bonus += rr * 10
            bonus += int(12 - 4 * abs(f - 3.5))
            if _passed_pawn(board, sq, c):
                bonus += 15 + rr * rr * 4
            # Encourage dangerous advanced pawns.
            if rr >= 5:
                bonus += (rr - 4) * 18

        elif t == "N":
            bonus += int(45 - 9 * center_euclid)
            if rr <= 1:
                bonus -= 12

        elif t == "B":
            bishops[c] += 1
            bonus += int(35 - 5 * center_manhattan)
            # Long diagonals are useful.
            if f == r or f + r == 7:
                bonus += 8

        elif t == "R":
            bonus += rr * 3
            if rr == 6:
                bonus += 25
            own_pawn = c + "P"
            enemy_pawn = _opp(c) + "P"
            file_has_own = any(board[rank * 8 + f] == own_pawn for rank in range(8))
            file_has_enemy = any(board[rank * 8 + f] == enemy_pawn for rank in range(8))
            if not file_has_own and not file_has_enemy:
                bonus += 25
            elif not file_has_own:
                bonus += 12

        elif t == "Q":
            bonus += int(15 - 2 * center_manhattan)

        elif t == "K":
            if endgame:
                bonus += int(35 - 6 * center_manhattan)
            else:
                # Prefer a safer back-rank/castled king in middlegames.
                bonus -= int(10 * (3.5 - abs(f - 3.5)))
                bonus -= rr * 8
                shield = 0
                front_rank = r + (1 if c == "w" else -1)
                if 0 <= front_rank < 8:
                    for ff in (f - 1, f, f + 1):
                        if 0 <= ff < 8 and board[front_rank * 8 + ff] == c + "P":
                            shield += 1
                bonus += shield * 12

        score += sign * (val + bonus)

    if bishops["w"] >= 2:
        score += 35
    if bishops["b"] >= 2:
        score -= 35

    # Endgame king pressure: drive enemy king to the edge and approach it.
    if endgame:
        wk, bk = _find_king(board, "w"), _find_king(board, "b")
        if wk >= 0 and bk >= 0:
            wf, wr = wk % 8, wk // 8
            bf, br = bk % 8, bk // 8
            b_edge = abs(bf - 3.5) + abs(br - 3.5)
            w_edge = abs(wf - 3.5) + abs(wr - 3.5)
            king_dist = abs(wf - bf) + abs(wr - br)
            material_balance = sum((1 if p and p[0] == "w" else -1 if p else 0) * VALUES[p[1]]
                                   for p in board)
            if material_balance > 300:
                score += int(b_edge * 12 + (14 - king_dist) * 4)
            elif material_balance < -300:
                score -= int(w_edge * 12 + (14 - king_dist) * 4)

    return score


def _evaluate(board, side):
    s = _eval_white_minus_black(board)
    return s if side == "w" else -s


def _move_order_score(board, move, side):
    fr = _idx(move[:2])
    to = _idx(move[2:4])
    p = board[fr]
    if p is None:
        return 0
    score = 0
    target = board[to]

    if target is not None:
        score += 10 * VALUES[target[1]] - VALUES[p[1]]

    if len(move) > 4:
        score += VALUES.get(move[4].upper(), 0) + 800

    # En-passant-like supplied move.
    if p[1] == "P" and target is None and abs((to % 8) - (fr % 8)) == 1:
        score += 900

    # Prefer checking moves slightly.
    try:
        nb = _apply(board, move)
        if _in_check(nb, _opp(side)):
            score += 70
    except Exception:
        pass

    # Small centralization preference.
    tf, tr = to % 8, to // 8
    score += int(8 - (abs(tf - 3.5) + abs(tr - 3.5)))
    return score


def _quiesce(board, side, alpha, beta, ply):
    if time.perf_counter() > _ENDTIME:
        raise _Timeout()

    stand = _evaluate(board, side)
    if stand >= beta:
        return beta
    if stand > alpha:
        alpha = stand

    if ply >= 4:
        return alpha

    moves = _legal_moves(board, side, False)
    noisy = []
    enemy = _opp(side)
    for m in moves:
        fr = _idx(m[:2])
        to = _idx(m[2:4])
        p = board[fr]
        if p is None:
            continue
        if board[to] is not None or len(m) > 4:
            noisy.append(m)
        elif p[1] == "P" and abs((to % 8) - (fr % 8)) == 1:
            noisy.append(m)

    noisy.sort(key=lambda m: _move_order_score(board, m, side), reverse=True)

    for m in noisy:
        nb = _apply(board, m)
        score = -_quiesce(nb, enemy, -beta, -alpha, ply + 1)
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score

    return alpha


def _negamax(board, side, depth, alpha, beta, ply):
    if time.perf_counter() > _ENDTIME:
        raise _Timeout()

    in_chk = _in_check(board, side)
    moves = _legal_moves(board, side, False)

    if not moves:
        if in_chk:
            return -MATE + ply
        return 0

    if depth <= 0:
        if in_chk:
            depth = 1
        else:
            return _quiesce(board, side, alpha, beta, ply)

    moves.sort(key=lambda m: _move_order_score(board, m, side), reverse=True)
    best = -INF
    enemy = _opp(side)

    for m in moves:
        nb = _apply(board, m)
        score = -_negamax(nb, enemy, depth - 1, -beta, -alpha, ply + 1)
        if score > best:
            best = score
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break

    return best


def _get_external_legal_moves():
    lm = globals().get("legal_moves", None)
    if lm is None:
        lm = globals().get("LEGAL_MOVES", None)
    if isinstance(lm, (list, tuple, set)):
        return list(lm)
    return None


def policy(pieces: dict[str, str], to_play: str) -> str:
    global _ENDTIME

    start = time.perf_counter()
    _ENDTIME = start + 0.88

    board = _board_from_pieces(pieces)
    side = _color(to_play)

    external = _get_external_legal_moves()
    if external is not None:
        root_moves = [m for m in external if isinstance(m, str) and len(m) >= 4]
    else:
        root_moves = _legal_moves(board, side, True)

    if not root_moves:
        return ""
    if len(root_moves) == 1:
        return root_moves[0]

    # Deterministic safe fallback.
    root_moves = list(root_moves)
    root_moves.sort(key=lambda m: _move_order_score(board, m, side), reverse=True)
    best_move = root_moves[0]

    # Immediate mate/capture sanity pass.
    try:
        for m in root_moves:
            nb = _apply(board, m)
            opp_moves = _legal_moves(nb, _opp(side), False)
            if not opp_moves and _in_check(nb, _opp(side)):
                return m
    except Exception:
        pass

    max_depth = 3
    if len(root_moves) <= 10:
        max_depth = 4
    if len(root_moves) <= 5:
        max_depth = 5
    if len(root_moves) >= 38:
        max_depth = 3

    scores = {}

    try:
        for depth in range(1, max_depth + 1):
            if time.perf_counter() > _ENDTIME:
                break

            ordered = root_moves[:]
            ordered.sort(
                key=lambda m: (m == best_move, scores.get(m, -INF), _move_order_score(board, m, side)),
                reverse=True
            )

            alpha = -INF
            beta = INF
            current_best = best_move
            current_score = -INF
            enemy = _opp(side)

            for m in ordered:
                if time.perf_counter() > _ENDTIME:
                    raise _Timeout()

                nb = _apply(board, m)
                score = -_negamax(nb, enemy, depth - 1, -beta, -alpha, 1)
                scores[m] = score

                if score > current_score:
                    current_score = score
                    current_best = m

                if score > alpha:
                    alpha = score

            best_move = current_best

    except _Timeout:
        pass
    except Exception:
        # On any unexpected issue, keep the best legal fallback found so far.
        pass

    if best_move in root_moves:
        return best_move
    return root_moves[0]
