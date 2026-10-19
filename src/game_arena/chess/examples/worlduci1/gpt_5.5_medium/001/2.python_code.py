
import time

FILES = "abcdefgh"
INF = 10**9
MATE = 100000

PIECE_VALUE = {
    "P": 100,
    "N": 320,
    "B": 330,
    "R": 500,
    "Q": 900,
    "K": 0,
}

KNIGHT_DIRS = [
    (2, 1), (2, -1), (-2, 1), (-2, -1),
    (1, 2), (1, -2), (-1, 2), (-1, -2)
]
KING_DIRS = [
    (1, 0), (-1, 0), (0, 1), (0, -1),
    (1, 1), (1, -1), (-1, 1), (-1, -1)
]
BISHOP_DIRS = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
ROOK_DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]
QUEEN_DIRS = BISHOP_DIRS + ROOK_DIRS

DEADLINE = 0.0
NODES = 0


class SearchTimeout(Exception):
    pass


def policy(pieces: dict[str, str], to_play: str) -> str:
    global DEADLINE, NODES

    start = time.time()
    DEADLINE = start + 0.88
    NODES = 0

    color = "w" if to_play == "white" else "b"
    board = dict(pieces)

    legal = generate_legal_moves(board, color)

    # If the arena happens to expose a legal_moves global, respect it.
    provided = globals().get("legal_moves", None)
    if provided:
        try:
            provided_set = set(provided)
            filtered = [m for m in legal if m in provided_set]
            if filtered:
                legal = filtered
            elif provided_set:
                return sorted(provided_set)[0]
        except Exception:
            pass

    if not legal:
        pseudo = generate_pseudo_moves(board, color)
        return pseudo[0] if pseudo else "a1a1"

    if len(legal) == 1:
        return legal[0]

    ordered = order_moves(board, legal, color)

    best_move = ordered[0]
    best_score = -INF

    piece_count = len(board)
    root_branching = len(legal)

    max_depth = 3
    if piece_count <= 14:
        max_depth = 4
    if piece_count <= 8:
        max_depth = 5
    if piece_count <= 5:
        max_depth = 6
    if root_branching <= 10:
        max_depth = max(max_depth, 4)
    if root_branching <= 5:
        max_depth = max(max_depth, 5)

    # Iterative deepening: always keep the best completed depth.
    for depth in range(1, max_depth + 1):
        try:
            alpha = -INF
            beta = INF
            local_best = best_move
            local_best_score = -INF

            for mv in ordered:
                check_time()
                nb = make_move(board, mv)
                score = -negamax(nb, opposite(color), depth - 1, -beta, -alpha, 1)

                if score > local_best_score:
                    local_best_score = score
                    local_best = mv

                if score > alpha:
                    alpha = score

            best_move = local_best
            best_score = local_best_score

            # Found forced mate; no need to search deeper.
            if best_score > MATE - 1000:
                break

        except SearchTimeout:
            break
        except Exception:
            break

    return best_move


def check_time():
    global NODES
    NODES += 1
    if (NODES & 1023) == 0 and time.time() > DEADLINE:
        raise SearchTimeout()


def opposite(color):
    return "b" if color == "w" else "w"


def in_bounds(r, c):
    return 0 <= r < 8 and 0 <= c < 8


def sq_to_rc(sq):
    return int(sq[1]) - 1, ord(sq[0]) - 97


def rc_to_sq(r, c):
    return chr(97 + c) + str(r + 1)


def find_king(board, color):
    target = color + "K"
    for sq, pc in board.items():
        if pc == target:
            return sq
    return None


def is_square_attacked(board, square, by_color):
    tr, tc = sq_to_rc(square)

    for sq, pc in board.items():
        if pc[0] != by_color:
            continue

        r, c = sq_to_rc(sq)
        pt = pc[1]

        if pt == "P":
            dr = 1 if by_color == "w" else -1
            if (r + dr == tr) and (c + 1 == tc or c - 1 == tc):
                return True

        elif pt == "N":
            for dr, dc in KNIGHT_DIRS:
                if r + dr == tr and c + dc == tc:
                    return True

        elif pt == "K":
            if max(abs(r - tr), abs(c - tc)) == 1:
                return True

        elif pt in ("B", "R", "Q"):
            if pt == "B":
                dirs = BISHOP_DIRS
            elif pt == "R":
                dirs = ROOK_DIRS
            else:
                dirs = QUEEN_DIRS

            for dr, dc in dirs:
                nr, nc = r + dr, c + dc
                while in_bounds(nr, nc):
                    nsq = rc_to_sq(nr, nc)
                    if nr == tr and nc == tc:
                        return True
                    if nsq in board:
                        break
                    nr += dr
                    nc += dc

    return False


def in_check(board, color):
    ksq = find_king(board, color)
    if ksq is None:
        return False
    return is_square_attacked(board, ksq, opposite(color))


def generate_pseudo_moves(board, color):
    moves = []

    for sq, pc in list(board.items()):
        if pc[0] != color:
            continue

        r, c = sq_to_rc(sq)
        pt = pc[1]

        if pt == "P":
            dr = 1 if color == "w" else -1
            start_rank = 1 if color == "w" else 6
            promotion_rank = 7 if color == "w" else 0

            # One step forward.
            nr = r + dr
            if in_bounds(nr, c):
                nsq = rc_to_sq(nr, c)
                if nsq not in board:
                    if nr == promotion_rank:
                        for promo in "qrbn":
                            moves.append(sq + nsq + promo)
                    else:
                        moves.append(sq + nsq)

                    # Two steps forward.
                    nr2 = r + 2 * dr
                    if r == start_rank and in_bounds(nr2, c):
                        nsq2 = rc_to_sq(nr2, c)
                        if nsq2 not in board:
                            moves.append(sq + nsq2)

            # Captures.
            for dc in (-1, 1):
                nr, nc = r + dr, c + dc
                if not in_bounds(nr, nc):
                    continue
                nsq = rc_to_sq(nr, nc)
                target = board.get(nsq)
                if target and target[0] != color and target[1] != "K":
                    if nr == promotion_rank:
                        for promo in "qrbn":
                            moves.append(sq + nsq + promo)
                    else:
                        moves.append(sq + nsq)

        elif pt == "N":
            for dr, dc in KNIGHT_DIRS:
                nr, nc = r + dr, c + dc
                if not in_bounds(nr, nc):
                    continue
                nsq = rc_to_sq(nr, nc)
                target = board.get(nsq)
                if target is None or (target[0] != color and target[1] != "K"):
                    moves.append(sq + nsq)

        elif pt == "K":
            for dr, dc in KING_DIRS:
                nr, nc = r + dr, c + dc
                if not in_bounds(nr, nc):
                    continue
                nsq = rc_to_sq(nr, nc)
                target = board.get(nsq)
                if target is None or (target[0] != color and target[1] != "K"):
                    moves.append(sq + nsq)

        elif pt in ("B", "R", "Q"):
            if pt == "B":
                dirs = BISHOP_DIRS
            elif pt == "R":
                dirs = ROOK_DIRS
            else:
                dirs = QUEEN_DIRS

            for dr, dc in dirs:
                nr, nc = r + dr, c + dc
                while in_bounds(nr, nc):
                    nsq = rc_to_sq(nr, nc)
                    target = board.get(nsq)

                    if target is None:
                        moves.append(sq + nsq)
                    else:
                        if target[0] != color and target[1] != "K":
                            moves.append(sq + nsq)
                        break

                    nr += dr
                    nc += dc

    return moves


def generate_legal_moves(board, color):
    legal = []
    opp = opposite(color)

    for mv in generate_pseudo_moves(board, color):
        nb = make_move(board, mv)
        ksq = find_king(nb, color)
        if ksq is not None and not is_square_attacked(nb, ksq, opp):
            legal.append(mv)

    return legal


def make_move(board, mv):
    nb = board.copy()
    frm = mv[:2]
    to = mv[2:4]
    pc = nb.pop(frm)
    nb.pop(to, None)

    if len(mv) == 5:
        pc = pc[0] + mv[4].upper()

    nb[to] = pc
    return nb


def order_moves(board, moves, color):
    def score_move(mv):
        frm = mv[:2]
        to = mv[2:4]
        pc = board.get(frm, "")
        target = board.get(to)
        score = 0

        if len(mv) == 5:
            promo_value = PIECE_VALUE.get(mv[4].upper(), 0)
            score += 8000 + promo_value

        if target and pc:
            victim = PIECE_VALUE.get(target[1], 0)
            attacker = PIECE_VALUE.get(pc[1], 1)
            score += 10000 + victim * 10 - attacker

        # Prefer centralizing non-pawns slightly.
        if pc:
            r, c = sq_to_rc(to)
            center_bonus = int(14 - 2 * (abs(r - 3.5) + abs(c - 3.5)))
            if pc[1] in ("N", "B", "Q", "K"):
                score += center_bonus
            elif pc[1] == "P":
                advancement = r if color == "w" else 7 - r
                score += advancement * 3 + center_bonus // 2

        return score

    return sorted(moves, key=score_move, reverse=True)


def negamax(board, color, depth, alpha, beta, ply):
    check_time()

    if depth <= 0:
        return quiescence(board, color, alpha, beta, ply, 0)

    legal = generate_legal_moves(board, color)

    if not legal:
        if in_check(board, color):
            return -MATE + ply
        return 0

    legal = order_moves(board, legal, color)

    best = -INF

    for mv in legal:
        nb = make_move(board, mv)
        score = -negamax(nb, opposite(color), depth - 1, -beta, -alpha, ply + 1)

        if score > best:
            best = score
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break

    return best


def quiescence(board, color, alpha, beta, ply, qply):
    check_time()

    side_in_check = in_check(board, color)

    if qply >= 5 and not side_in_check:
        return evaluate(board, color)

    if not side_in_check:
        stand_pat = evaluate(board, color)
        if stand_pat >= beta:
            return beta
        if stand_pat > alpha:
            alpha = stand_pat

    legal = generate_legal_moves(board, color)

    if not legal:
        if side_in_check:
            return -MATE + ply
        return 0

    if side_in_check:
        noisy = legal
    else:
        noisy = []
        for mv in legal:
            if len(mv) == 5 or board.get(mv[2:4]) is not None:
                noisy.append(mv)

    if not noisy:
        return alpha

    noisy = order_moves(board, noisy, color)

    for mv in noisy:
        nb = make_move(board, mv)
        score = -quiescence(nb, opposite(color), -beta, -alpha, ply + 1, qply + 1)

        if score >= beta:
            return beta
        if score > alpha:
            alpha = score

    return alpha


def evaluate(board, color):
    absolute = evaluate_absolute(board)
    return absolute if color == "w" else -absolute


def evaluate_absolute(board):
    total = 0

    bishops = {"w": 0, "b": 0}
    pawn_files = {
        "w": [[] for _ in range(8)],
        "b": [[] for _ in range(8)],
    }
    kings = {}

    non_pawn_material = 0

    for sq, pc in board.items():
        col, pt = pc[0], pc[1]
        r, c = sq_to_rc(sq)

        if pt != "P" and pt != "K":
            non_pawn_material += PIECE_VALUE[pt]

        if pt == "P":
            pawn_files[col][c].append(r)
        elif pt == "B":
            bishops[col] += 1
        elif pt == "K":
            kings[col] = (r, c)

    endgame = non_pawn_material <= 2200

    for sq, pc in board.items():
        col, pt = pc[0], pc[1]
        sign = 1 if col == "w" else -1
        r, c = sq_to_rc(sq)

        base = PIECE_VALUE[pt]
        pst = positional_bonus(pt, col, r, c, endgame)

        total += sign * (base + pst)

    # Bishop pair.
    if bishops["w"] >= 2:
        total += 35
    if bishops["b"] >= 2:
        total -= 35

    # Pawn structure and passed pawns.
    for col in ("w", "b"):
        sign = 1 if col == "w" else -1
        opp = opposite(col)
        own = pawn_files[col]
        enemy = pawn_files[opp]

        for f in range(8):
            if len(own[f]) > 1:
                total += sign * (-15 * (len(own[f]) - 1))

            for r in own[f]:
                isolated = True
                if f > 0 and own[f - 1]:
                    isolated = False
                if f < 7 and own[f + 1]:
                    isolated = False
                if isolated:
                    total += sign * -10

                passed = True
                for ef in (f - 1, f, f + 1):
                    if 0 <= ef < 8:
                        for er in enemy[ef]:
                            if col == "w":
                                if er > r:
                                    passed = False
                            else:
                                if er < r:
                                    passed = False
                if passed:
                    adv = r if col == "w" else 7 - r
                    total += sign * (20 + adv * adv * 4)

    # Rook open files.
    for sq, pc in board.items():
        col, pt = pc[0], pc[1]
        if pt != "R":
            continue
        sign = 1 if col == "w" else -1
        _, c = sq_to_rc(sq)
        own_pawns = pawn_files[col][c]
        enemy_pawns = pawn_files[opposite(col)][c]
        if not own_pawns:
            total += sign * 10
            if not enemy_pawns:
                total += sign * 10

    # King pawn shield.
    for col in ("w", "b"):
        if col not in kings:
            continue
        sign = 1 if col == "w" else -1
        kr, kc = kings[col]
        dr = 1 if col == "w" else -1
        shield = 0
        for dc in (-1, 0, 1):
            f = kc + dc
            if not (0 <= f < 8):
                continue
            for step, val in ((1, 8), (2, 4)):
                rr = kr + dr * step
                if 0 <= rr < 8 and rr in pawn_files[col][f]:
                    shield += val
        total += sign * shield

    return total


def positional_bonus(pt, col, r, c, endgame):
    # r is 0 for rank 1. For black, advancement and home rank are mirrored.
    advancement = r if col == "w" else 7 - r
    home_distance = r if col == "w" else 7 - r
    center_dist = abs(r - 3.5) + abs(c - 3.5)
    central = max(0, int(70 - center_dist * 10))

    if pt == "P":
        bonus = advancement * 10
        if c in (3, 4):
            bonus += 6
        elif c in (2, 5):
            bonus += 3
        if advancement >= 5:
            bonus += (advancement - 4) * 18
        return bonus

    if pt == "N":
        return central - 5

    if pt == "B":
        return central // 2 + 5

    if pt == "R":
        seventh = 18 if advancement == 6 else 0
        return advancement * 3 + seventh

    if pt == "Q":
        return central // 4

    if pt == "K":
        if endgame:
            return central // 2
        # In the middlegame, prefer being near the home rank and not centralized.
        return 25 - home_distance * 10 - central // 3

    return 0
