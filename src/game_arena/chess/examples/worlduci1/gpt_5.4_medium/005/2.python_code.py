
import time

FILES = "abcdefgh"
SQUARES = [FILES[i % 8] + str(i // 8 + 1) for i in range(64)]

PIECE_VALUES = {
    "P": 100,
    "N": 320,
    "B": 330,
    "R": 500,
    "Q": 900,
    "K": 0,
}

KNIGHT_OFFSETS = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
KING_OFFSETS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
BISHOP_DIRS = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
ROOK_DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

MATE_SCORE = 100000
INF = 10**9

CENTER = [0] * 64
for sq in range(64):
    x, y = sq % 8, sq // 8
    cdx = min(abs(x - 3), abs(x - 4))
    cdy = min(abs(y - 3), abs(y - 4))
    CENTER[sq] = 8 - 2 * (cdx + cdy)

class TimeUp(Exception):
    pass

def sq_to_idx(s):
    return (ord(s[0]) - 97) + 8 * (ord(s[1]) - 49)

def idx_to_sq(i):
    return SQUARES[i]

def other(color):
    return "b" if color == "w" else "w"

def move_to_uci(move):
    frm, to, promo = move
    return SQUARES[frm] + SQUARES[to] + promo if promo else SQUARES[frm] + SQUARES[to]

def find_kings(board):
    kings = {"w": -1, "b": -1}
    for i, p in enumerate(board):
        if p == "wK":
            kings["w"] = i
        elif p == "bK":
            kings["b"] = i
    return kings

def is_attacked(board, sq, by_color):
    x, y = sq % 8, sq // 8

    # Pawns
    if by_color == "w":
        if x > 0 and y > 0 and board[sq - 9] == "wP":
            return True
        if x < 7 and y > 0 and board[sq - 7] == "wP":
            return True
    else:
        if x > 0 and y < 7 and board[sq + 7] == "bP":
            return True
        if x < 7 and y < 7 and board[sq + 9] == "bP":
            return True

    # Knights
    target = by_color + "N"
    for dx, dy in KNIGHT_OFFSETS:
        nx, ny = x + dx, y + dy
        if 0 <= nx < 8 and 0 <= ny < 8:
            if board[ny * 8 + nx] == target:
                return True

    # Bishops / Queens
    b = by_color + "B"
    q = by_color + "Q"
    for dx, dy in BISHOP_DIRS:
        nx, ny = x + dx, y + dy
        while 0 <= nx < 8 and 0 <= ny < 8:
            p = board[ny * 8 + nx]
            if p:
                if p == b or p == q:
                    return True
                break
            nx += dx
            ny += dy

    # Rooks / Queens
    r = by_color + "R"
    for dx, dy in ROOK_DIRS:
        nx, ny = x + dx, y + dy
        while 0 <= nx < 8 and 0 <= ny < 8:
            p = board[ny * 8 + nx]
            if p:
                if p == r or p == q:
                    return True
                break
            nx += dx
            ny += dy

    # King
    k = by_color + "K"
    for dx, dy in KING_OFFSETS:
        nx, ny = x + dx, y + dy
        if 0 <= nx < 8 and 0 <= ny < 8:
            if board[ny * 8 + nx] == k:
                return True

    return False

def generate_pseudo_moves(board, color, captures_only=False):
    enemy = other(color)
    for i, piece in enumerate(board):
        if not piece or piece[0] != color:
            continue
        p = piece[1]
        x, y = i % 8, i // 8

        if p == "P":
            if color == "w":
                # forward
                one = i + 8
                if y < 7 and not captures_only and board[one] == "":
                    if y == 6:
                        for promo in ("q", "r", "b", "n"):
                            yield (i, one, promo)
                    else:
                        yield (i, one, "")
                        if y == 1:
                            two = i + 16
                            if board[two] == "":
                                yield (i, two, "")
                elif y == 6 and captures_only and board[one] == "":
                    for promo in ("q", "r", "b", "n"):
                        yield (i, one, promo)

                # captures
                if x > 0:
                    to = i + 7
                    if to < 64 and board[to] and board[to][0] == enemy and board[to][1] != "K":
                        if y == 6:
                            for promo in ("q", "r", "b", "n"):
                                yield (i, to, promo)
                        else:
                            yield (i, to, "")
                if x < 7:
                    to = i + 9
                    if to < 64 and board[to] and board[to][0] == enemy and board[to][1] != "K":
                        if y == 6:
                            for promo in ("q", "r", "b", "n"):
                                yield (i, to, promo)
                        else:
                            yield (i, to, "")
            else:
                one = i - 8
                if y > 0 and not captures_only and board[one] == "":
                    if y == 1:
                        for promo in ("q", "r", "b", "n"):
                            yield (i, one, promo)
                    else:
                        yield (i, one, "")
                        if y == 6:
                            two = i - 16
                            if board[two] == "":
                                yield (i, two, "")
                elif y == 1 and captures_only and board[one] == "":
                    for promo in ("q", "r", "b", "n"):
                        yield (i, one, promo)

                if x > 0:
                    to = i - 9
                    if to >= 0 and board[to] and board[to][0] == enemy and board[to][1] != "K":
                        if y == 1:
                            for promo in ("q", "r", "b", "n"):
                                yield (i, to, promo)
                        else:
                            yield (i, to, "")
                if x < 7:
                    to = i - 7
                    if to >= 0 and board[to] and board[to][0] == enemy and board[to][1] != "K":
                        if y == 1:
                            for promo in ("q", "r", "b", "n"):
                                yield (i, to, promo)
                        else:
                            yield (i, to, "")

        elif p == "N":
            for dx, dy in KNIGHT_OFFSETS:
                nx, ny = x + dx, y + dy
                if 0 <= nx < 8 and 0 <= ny < 8:
                    to = ny * 8 + nx
                    tgt = board[to]
                    if tgt == "":
                        if not captures_only:
                            yield (i, to, "")
                    elif tgt[0] == enemy and tgt[1] != "K":
                        yield (i, to, "")

        elif p == "B" or p == "R" or p == "Q":
            dirs = []
            if p == "B" or p == "Q":
                dirs += BISHOP_DIRS
            if p == "R" or p == "Q":
                dirs += ROOK_DIRS
            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                while 0 <= nx < 8 and 0 <= ny < 8:
                    to = ny * 8 + nx
                    tgt = board[to]
                    if tgt == "":
                        if not captures_only:
                            yield (i, to, "")
                    else:
                        if tgt[0] == enemy and tgt[1] != "K":
                            yield (i, to, "")
                        break
                    nx += dx
                    ny += dy

        elif p == "K":
            for dx, dy in KING_OFFSETS:
                nx, ny = x + dx, y + dy
                if 0 <= nx < 8 and 0 <= ny < 8:
                    to = ny * 8 + nx
                    tgt = board[to]
                    if tgt == "":
                        if not captures_only:
                            yield (i, to, "")
                    elif tgt[0] == enemy and tgt[1] != "K":
                        yield (i, to, "")

def apply_move(board, move, kings):
    frm, to, promo = move
    moving = board[frm]
    captured = board[to]
    new_piece = moving if not promo else moving[0] + promo.upper()
    board[frm] = ""
    board[to] = new_piece
    old_king_sq = None
    if moving[1] == "K":
        old_king_sq = kings[moving[0]]
        kings[moving[0]] = to
    return moving, captured, old_king_sq

def undo_move(board, move, kings, moving, captured, old_king_sq):
    frm, to, promo = move
    board[frm] = moving
    board[to] = captured
    if moving[1] == "K":
        kings[moving[0]] = old_king_sq

def generate_legal_moves(board, color, kings, captures_only=False):
    enemy = other(color)
    out = []
    for mv in generate_pseudo_moves(board, color, captures_only=captures_only):
        moving, captured, old_king_sq = apply_move(board, mv, kings)
        king_sq = kings[color]
        if king_sq != -1 and not is_attacked(board, king_sq, enemy):
            out.append(mv)
        undo_move(board, mv, kings, moving, captured, old_king_sq)
    return out

def plausible_castling_fallback(board, color, kings):
    enemy = other(color)
    out = []
    ksq = kings[color]
    if ksq == -1 or is_attacked(board, ksq, enemy):
        return out

    if color == "w" and ksq == 4:
        # e1g1
        if board[7] == "wR" and board[5] == "" and board[6] == "":
            if not is_attacked(board, 5, enemy) and not is_attacked(board, 6, enemy):
                out.append((4, 6, ""))
        # e1c1
        if board[0] == "wR" and board[1] == "" and board[2] == "" and board[3] == "":
            if not is_attacked(board, 3, enemy) and not is_attacked(board, 2, enemy):
                out.append((4, 2, ""))
    elif color == "b" and ksq == 60:
        # e8g8
        if board[63] == "bR" and board[61] == "" and board[62] == "":
            if not is_attacked(board, 61, enemy) and not is_attacked(board, 62, enemy):
                out.append((60, 62, ""))
        # e8c8
        if board[56] == "bR" and board[57] == "" and board[58] == "" and board[59] == "":
            if not is_attacked(board, 59, enemy) and not is_attacked(board, 58, enemy):
                out.append((60, 58, ""))
    return out

def move_order_score(board, move):
    frm, to, promo = move
    moving = board[frm]
    captured = board[to]
    score = 0
    if captured:
        score += 10 * PIECE_VALUES[captured[1]] - PIECE_VALUES[moving[1]]
    if promo:
        score += PIECE_VALUES[promo.upper()] + 50
    if moving[1] == "P" and (to // 8 == 0 or to // 8 == 7):
        score += 80
    if moving[1] == "K":
        score -= 20
    return score

def evaluate(board, kings):
    score = 0
    pawns = {"w": [[] for _ in range(8)], "b": [[] for _ in range(8)]}
    bishops = {"w": 0, "b": 0}
    rooks = {"w": [], "b": []}
    nonpawn = {"w": 0, "b": 0}

    for sq, piece in enumerate(board):
        if not piece:
            continue
        c, p = piece[0], piece[1]
        sgn = 1 if c == "w" else -1
        x, y = sq % 8, sq // 8
        rank_from_side = y if c == "w" else 7 - y

        score += sgn * PIECE_VALUES[p]

        if p != "P" and p != "K":
            nonpawn[c] += PIECE_VALUES[p]

        if p == "P":
            score += sgn * (10 * rank_from_side + CENTER[sq] * 2)
            pawns[c][x].append(y)
        elif p == "N":
            score += sgn * (CENTER[sq] * 4)
        elif p == "B":
            score += sgn * (CENTER[sq] * 3 + rank_from_side)
            bishops[c] += 1
        elif p == "R":
            score += sgn * (rank_from_side * 2)
            rooks[c].append(sq)
        elif p == "Q":
            score += sgn * (CENTER[sq] * 2)
        elif p == "K":
            endgame = (nonpawn["w"] + nonpawn["b"] <= 2600)
            if endgame:
                score += sgn * (CENTER[sq] * 4)
            else:
                back_rank = 0 if c == "w" else 7
                score += sgn * (14 if y == back_rank else -CENTER[sq] * 2)

    # Bishop pair
    if bishops["w"] >= 2:
        score += 30
    if bishops["b"] >= 2:
        score -= 30

    # Pawn structure
    for c in ("w", "b"):
        sgn = 1 if c == "w" else -1
        enemy = other(c)

        for file in range(8):
            cnt = len(pawns[c][file])
            if cnt > 1:
                score -= sgn * 10 * (cnt - 1)

        for file in range(8):
            for y in pawns[c][file]:
                # isolated
                isolated = True
                if file > 0 and pawns[c][file - 1]:
                    isolated = False
                if file < 7 and pawns[c][file + 1]:
                    isolated = False
                if isolated:
                    score -= sgn * 12

                # passed pawn
                passed = True
                for ef in range(max(0, file - 1), min(7, file + 1) + 1):
                    for ey in pawns[enemy][ef]:
                        if c == "w":
                            if ey > y:
                                passed = False
                                break
                        else:
                            if ey < y:
                                passed = False
                                break
                    if not passed:
                        break
                if passed:
                    advance = y if c == "w" else 7 - y
                    score += sgn * (20 + 8 * advance)

    # Rooks on open files
    for c in ("w", "b"):
        sgn = 1 if c == "w" else -1
        enemy = other(c)
        for sq in rooks[c]:
            f = sq % 8
            own_pawns = len(pawns[c][f])
            enemy_pawns = len(pawns[enemy][f])
            if own_pawns == 0 and enemy_pawns == 0:
                score += sgn * 18
            elif own_pawns == 0:
                score += sgn * 10

    # King shelter in middlegame
    total_nonpawn = nonpawn["w"] + nonpawn["b"]
    if total_nonpawn > 1800:
        for c in ("w", "b"):
            ksq = kings[c]
            if ksq == -1:
                continue
            sgn = 1 if c == "w" else -1
            kx, ky = ksq % 8, ksq // 8
            shield_rank = ky + 1 if c == "w" else ky - 1
            shelter = 0
            if 0 <= shield_rank < 8:
                for fx in (kx - 1, kx, kx + 1):
                    if 0 <= fx < 8:
                        p = board[shield_rank * 8 + fx]
                        if p == c + "P":
                            shelter += 1
            score += sgn * (8 * shelter)

    return score

def eval_for_side(board, kings, side):
    s = evaluate(board, kings)
    return s if side == "w" else -s

def quiescence(board, side, kings, alpha, beta, ply, deadline):
    if time.perf_counter() > deadline:
        raise TimeUp

    enemy = other(side)
    in_check = is_attacked(board, kings[side], enemy)

    if in_check:
        moves = generate_legal_moves(board, side, kings, captures_only=False)
        if not moves:
            return -MATE_SCORE + ply
    else:
        stand = eval_for_side(board, kings, side)
        if stand >= beta:
            return beta
        if stand > alpha:
            alpha = stand
        moves = generate_legal_moves(board, side, kings, captures_only=True)

    moves.sort(key=lambda mv: move_order_score(board, mv), reverse=True)

    for mv in moves:
        moving, captured, old_king_sq = apply_move(board, mv, kings)
        score = -quiescence(board, enemy, kings, -beta, -alpha, ply + 1, deadline)
        undo_move(board, mv, kings, moving, captured, old_king_sq)

        if score >= beta:
            return beta
        if score > alpha:
            alpha = score

    return alpha

def negamax(board, side, kings, depth, alpha, beta, ply, deadline):
    if time.perf_counter() > deadline:
        raise TimeUp

    enemy = other(side)

    if depth == 0:
        return quiescence(board, side, kings, alpha, beta, ply, deadline)

    moves = generate_legal_moves(board, side, kings, captures_only=False)

    if not moves:
        if is_attacked(board, kings[side], enemy):
            return -MATE_SCORE + ply
        return 0

    moves.sort(key=lambda mv: move_order_score(board, mv), reverse=True)

    best = -INF
    for mv in moves:
        moving, captured, old_king_sq = apply_move(board, mv, kings)
        score = -negamax(board, enemy, kings, depth - 1, -beta, -alpha, ply + 1, deadline)
        undo_move(board, mv, kings, moving, captured, old_king_sq)

        if score > best:
            best = score
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break

    return best

def pick_best_move(board, side, kings, legal_moves, deadline):
    if len(legal_moves) == 1:
        return legal_moves[0]

    legal_moves.sort(key=lambda mv: move_order_score(board, mv), reverse=True)

    piece_count = sum(1 for p in board if p)
    max_depth = 3
    if len(legal_moves) <= 12 or piece_count <= 10:
        max_depth = 4
    if len(legal_moves) <= 6 or piece_count <= 6:
        max_depth = 5

    best_move = legal_moves[0]
    best_score = -INF
    pv_move = best_move

    for depth in range(1, max_depth + 1):
        if time.perf_counter() > deadline:
            break
        try:
            alpha = -INF
            beta = INF
            iteration_best = pv_move
            iteration_score = -INF

            ordered = [pv_move] + [m for m in legal_moves if m != pv_move]
            ordered.sort(key=lambda mv: (mv != pv_move, -move_order_score(board, mv)))

            for mv in ordered:
                moving, captured, old_king_sq = apply_move(board, mv, kings)
                score = -negamax(board, other(side), kings, depth - 1, -beta, -alpha, 1, deadline)
                undo_move(board, mv, kings, moving, captured, old_king_sq)

                if score > iteration_score:
                    iteration_score = score
                    iteration_best = mv
                if score > alpha:
                    alpha = score

            best_move = iteration_best
            best_score = iteration_score
            pv_move = iteration_best

            if best_score > MATE_SCORE - 1000:
                break
        except TimeUp:
            break

    return best_move

def policy(pieces: dict[str, str], to_play: str) -> str:
    board = [""] * 64
    for sq, piece in pieces.items():
        board[sq_to_idx(sq)] = piece

    side = "w" if to_play == "white" else "b"
    kings = find_kings(board)

    deadline = time.perf_counter() + 0.90

    legal_moves = generate_legal_moves(board, side, kings, captures_only=False)

    if not legal_moves:
        # Very conservative fallback for missing history (castling only if otherwise no moves found).
        castles = plausible_castling_fallback(board, side, kings)
        if castles:
            return move_to_uci(castles[0])

        # Last-resort fallback: return a pseudo move if one exists.
        pseudo = list(generate_pseudo_moves(board, side, captures_only=False))
        if pseudo:
            return move_to_uci(pseudo[0])

        # Terminal positions should normally not be queried.
        return "a1a1"

    best = pick_best_move(board, side, kings, legal_moves, deadline)
    return move_to_uci(best)
