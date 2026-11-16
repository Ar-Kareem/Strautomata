
import time

FILES = "abcdefgh"
INF = 10**9
MATE = 10**7

VAL = {
    "P": 100,
    "N": 320,
    "B": 330,
    "R": 500,
    "Q": 900,
    "K": 0,
}

KNIGHT_DIRS = [
    (1, 2), (2, 1), (-1, 2), (-2, 1),
    (1, -2), (2, -1), (-1, -2), (-2, -1)
]
KING_DIRS = [
    (1, 0), (-1, 0), (0, 1), (0, -1),
    (1, 1), (1, -1), (-1, 1), (-1, -1)
]
BISHOP_DIRS = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
ROOK_DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def policy(pieces: dict[str, str], to_play: str) -> str:
    start_time = time.time()
    deadline = start_time + 0.92

    us = "w" if to_play == "white" else "b"
    them = "b" if us == "w" else "w"

    board = dict(pieces)

    def now_too_late():
        return time.time() > deadline

    def opp(c):
        return "b" if c == "w" else "w"

    def sq(f, r):
        return FILES[f] + str(r + 1)

    def coord(s):
        return ord(s[0]) - 97, ord(s[1]) - 49

    def inside(f, r):
        return 0 <= f < 8 and 0 <= r < 8

    def find_king(b, color):
        k = color + "K"
        for s, p in b.items():
            if p == k:
                return s
        return None

    def attacked(b, target, by_color):
        tf, tr = coord(target)

        # Pawn attacks
        if by_color == "w":
            pr = tr - 1
            for pf in (tf - 1, tf + 1):
                if inside(pf, pr) and b.get(sq(pf, pr)) == "wP":
                    return True
        else:
            pr = tr + 1
            for pf in (tf - 1, tf + 1):
                if inside(pf, pr) and b.get(sq(pf, pr)) == "bP":
                    return True

        # Knight attacks
        for df, dr in KNIGHT_DIRS:
            f, r = tf + df, tr + dr
            if inside(f, r) and b.get(sq(f, r)) == by_color + "N":
                return True

        # King attacks
        for df, dr in KING_DIRS:
            f, r = tf + df, tr + dr
            if inside(f, r) and b.get(sq(f, r)) == by_color + "K":
                return True

        # Bishop / queen diagonals
        for df, dr in BISHOP_DIRS:
            f, r = tf + df, tr + dr
            while inside(f, r):
                p = b.get(sq(f, r))
                if p:
                    if p[0] == by_color and p[1] in ("B", "Q"):
                        return True
                    break
                f += df
                r += dr

        # Rook / queen lines
        for df, dr in ROOK_DIRS:
            f, r = tf + df, tr + dr
            while inside(f, r):
                p = b.get(sq(f, r))
                if p:
                    if p[0] == by_color and p[1] in ("R", "Q"):
                        return True
                    break
                f += df
                r += dr

        return False

    def in_check(b, color):
        ksq = find_king(b, color)
        if ksq is None:
            return True
        return attacked(b, ksq, opp(color))

    def make_move(b, m):
        nb = dict(b)
        fr = m[:2]
        to = m[2:4]
        promo = m[4].upper() if len(m) > 4 else None
        piece = nb.pop(fr)

        ff, rr = coord(fr)
        tf, tr = coord(to)

        # En-passant support if a provided legal move uses it.
        if piece[1] == "P" and ff != tf and to not in nb:
            cap_sq = sq(tf, rr)
            if cap_sq in nb:
                nb.pop(cap_sq)

        # Castling support if a provided legal move uses it.
        if piece[1] == "K" and abs(tf - ff) == 2:
            if tf > ff:
                rook_from = sq(7, rr)
                rook_to = sq(5, rr)
            else:
                rook_from = sq(0, rr)
                rook_to = sq(3, rr)
            rook = nb.pop(rook_from, None)
            if rook:
                nb[rook_to] = rook

        if promo:
            piece = piece[0] + promo

        nb[to] = piece
        return nb

    def pseudo_moves(b, color):
        moves = []
        for s0, p in list(b.items()):
            if p[0] != color:
                continue

            f, r = coord(s0)
            pt = p[1]

            if pt == "P":
                direction = 1 if color == "w" else -1
                start_rank = 1 if color == "w" else 6
                promo_rank = 7 if color == "w" else 0

                # One step
                r1 = r + direction
                if inside(f, r1) and sq(f, r1) not in b:
                    dst = sq(f, r1)
                    if r1 == promo_rank:
                        for pr in "qrbn":
                            moves.append(s0 + dst + pr)
                    else:
                        moves.append(s0 + dst)

                    # Two steps
                    r2 = r + 2 * direction
                    if r == start_rank and inside(f, r2) and sq(f, r2) not in b:
                        moves.append(s0 + sq(f, r2))

                # Captures
                for df in (-1, 1):
                    f1 = f + df
                    if inside(f1, r1):
                        dst = sq(f1, r1)
                        target = b.get(dst)
                        if target and target[0] != color and target[1] != "K":
                            if r1 == promo_rank:
                                for pr in "qrbn":
                                    moves.append(s0 + dst + pr)
                            else:
                                moves.append(s0 + dst)

            elif pt == "N":
                for df, dr in KNIGHT_DIRS:
                    f1, r1 = f + df, r + dr
                    if inside(f1, r1):
                        dst = sq(f1, r1)
                        target = b.get(dst)
                        if not target or (target[0] != color and target[1] != "K"):
                            moves.append(s0 + dst)

            elif pt in ("B", "R", "Q"):
                dirs = []
                if pt in ("B", "Q"):
                    dirs += BISHOP_DIRS
                if pt in ("R", "Q"):
                    dirs += ROOK_DIRS

                for df, dr in dirs:
                    f1, r1 = f + df, r + dr
                    while inside(f1, r1):
                        dst = sq(f1, r1)
                        target = b.get(dst)
                        if not target:
                            moves.append(s0 + dst)
                        else:
                            if target[0] != color and target[1] != "K":
                                moves.append(s0 + dst)
                            break
                        f1 += df
                        r1 += dr

            elif pt == "K":
                for df, dr in KING_DIRS:
                    f1, r1 = f + df, r + dr
                    if inside(f1, r1):
                        dst = sq(f1, r1)
                        target = b.get(dst)
                        if not target or (target[0] != color and target[1] != "K"):
                            moves.append(s0 + dst)

                # Castling is deliberately not generated from board alone because
                # castling rights are not present in the state representation.

        return moves

    def legal_moves_for(b, color):
        out = []
        for m in pseudo_moves(b, color):
            nb = make_move(b, m)
            if not in_check(nb, color):
                out.append(m)
        return out

    def material_phase(b):
        total = 0
        for p in b.values():
            if p[1] != "K":
                total += VAL[p[1]]
        return total

    def eval_board(b, color):
        score = 0
        phase = material_phase(b)
        endgame = phase < 2200

        for s0, p in b.items():
            c, pt = p[0], p[1]
            f, r = coord(s0)
            sign = 1 if c == color else -1
            val = VAL[pt]

            # Positional terms
            center_dist = abs(f - 3.5) + abs(r - 3.5)
            bonus = 0

            if pt == "P":
                adv = r if c == "w" else 7 - r
                bonus += adv * 8
                if f in (3, 4):
                    bonus += 8
                if f in (0, 7):
                    bonus -= 4
                if adv >= 5:
                    bonus += 15 * (adv - 4)

            elif pt == "N":
                bonus += int(35 - 10 * center_dist)

            elif pt == "B":
                bonus += int(20 - 5 * center_dist)

            elif pt == "R":
                if (c == "w" and r == 6) or (c == "b" and r == 1):
                    bonus += 25
                if (c == "w" and r == 7) or (c == "b" and r == 0):
                    bonus -= 8

            elif pt == "Q":
                bonus += int(10 - 2 * center_dist)

            elif pt == "K":
                if endgame:
                    bonus += int(40 - 10 * center_dist)
                else:
                    home_rank = 0 if c == "w" else 7
                    bonus -= int(8 * abs(r - home_rank))
                    if f in (1, 2, 6, 7):
                        bonus += 12

            score += sign * (val + bonus)

        return score

    def move_order_score(b, m):
        fr, to = m[:2], m[2:4]
        piece = b.get(fr, "")
        target = b.get(to)
        score = 0

        if len(m) > 4:
            promo_piece = m[4].upper()
            score += VAL.get(promo_piece, 0) + 800

        if target and piece:
            score += 10 * VAL[target[1]] - VAL[piece[1]]

        # Prefer central destinations slightly
        tf, tr = coord(to)
        score += int(8 - (abs(tf - 3.5) + abs(tr - 3.5)))

        return score

    def ordered_moves(b, moves):
        return sorted(moves, key=lambda m: move_order_score(b, m), reverse=True)

    nodes = [0]

    def quiescence(b, color, alpha, beta, qdepth):
        nodes[0] += 1
        if nodes[0] & 255 == 0 and now_too_late():
            raise TimeoutError

        stand = eval_board(b, color)

        if qdepth <= 0:
            return stand

        checked = in_check(b, color)
        if not checked:
            if stand >= beta:
                return beta
            if stand > alpha:
                alpha = stand

        moves = legal_moves_for(b, color)
        if not moves:
            if checked:
                return -MATE
            return 0

        if not checked:
            tactical = []
            for m in moves:
                if len(m) > 4 or b.get(m[2:4]):
                    tactical.append(m)
            moves = tactical

        for m in ordered_moves(b, moves):
            nb = make_move(b, m)
            val = -quiescence(nb, opp(color), -beta, -alpha, qdepth - 1)
            if val >= beta:
                return beta
            if val > alpha:
                alpha = val

        return alpha

    def negamax(b, color, depth, alpha, beta, ply):
        nodes[0] += 1
        if nodes[0] & 255 == 0 and now_too_late():
            raise TimeoutError

        moves = legal_moves_for(b, color)

        if not moves:
            if in_check(b, color):
                return -MATE + ply
            return 0

        if depth <= 0:
            return quiescence(b, color, alpha, beta, 2)

        best = -INF

        for m in ordered_moves(b, moves):
            nb = make_move(b, m)
            val = -negamax(nb, opp(color), depth - 1, -beta, -alpha, ply + 1)

            if val > best:
                best = val
            if val > alpha:
                alpha = val
            if alpha >= beta:
                break

        return best

    # If the arena happens to expose legal_moves globally, respect it.
    supplied = globals().get("legal_moves", None)
    if isinstance(supplied, list) and supplied:
        root_moves = list(supplied)
    else:
        root_moves = legal_moves_for(board, us)

    if not root_moves:
        return ""

    root_moves = ordered_moves(board, root_moves)
    best_move = root_moves[0]

    piece_count = len(board)
    branch = len(root_moves)

    if piece_count <= 8:
        max_depth = 5
    elif branch <= 18:
        max_depth = 4
    else:
        max_depth = 3

    last_completed_best = best_move

    for depth in range(1, max_depth + 1):
        if now_too_late():
            break

        try:
            alpha = -INF
            beta = INF
            current_best = last_completed_best
            current_score = -INF

            # Search previous best first.
            search_moves = [last_completed_best] + [m for m in root_moves if m != last_completed_best]

            for m in search_moves:
                if now_too_late():
                    raise TimeoutError

                nb = make_move(board, m)
                val = -negamax(nb, them, depth - 1, -beta, -alpha, 1)

                if val > current_score:
                    current_score = val
                    current_best = m

                if val > alpha:
                    alpha = val

            last_completed_best = current_best
            best_move = current_best

            # Immediate mate found.
            if current_score > MATE // 2:
                break

        except TimeoutError:
            break

    return best_move
