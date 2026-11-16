
import math
import time

FILES = "abcdefgh"
RANKS = "12345678"
PIECE_VAL = {"P": 100, "N": 320, "B": 330, "R": 500, "Q": 900, "K": 20000}
KNIGHT_DIRS = [(1,2),(2,1),(2,-1),(1,-2),(-1,-2),(-2,-1),(-2,1),(-1,2)]
KING_DIRS = [(1,1),(1,0),(1,-1),(0,1),(0,-1),(-1,1),(-1,0),(-1,-1)]
BISHOP_DIRS = [(1,1),(1,-1),(-1,1),(-1,-1)]
ROOK_DIRS = [(1,0),(-1,0),(0,1),(0,-1)]
QUEEN_DIRS = BISHOP_DIRS + ROOK_DIRS

CENTER = {"d4","e4","d5","e5"}
EXT_CENTER = {"c3","d3","e3","f3","c4","d4","e4","f4","c5","d5","e5","f5","c6","d6","e6","f6"}

def sq_to_xy(s):
    return FILES.index(s[0]), RANKS.index(s[1])

def xy_to_sq(x, y):
    return FILES[x] + RANKS[y]

def inside(x, y):
    return 0 <= x < 8 and 0 <= y < 8

def color_code(to_play):
    return "w" if to_play == "white" else "b"

def other(c):
    return "b" if c == "w" else "w"

def enemy_to_play(to_play):
    return "black" if to_play == "white" else "white"

def find_king(board, color):
    target = color + "K"
    for s, p in board.items():
        if p == target:
            return s
    return None

def attacked_by(board, sq, attacker):
    x, y = sq_to_xy(sq)

    # Pawns
    pawn_dir = 1 if attacker == "w" else -1
    for dx in (-1, 1):
        ax, ay = x - dx, y - pawn_dir
        if inside(ax, ay) and board.get(xy_to_sq(ax, ay)) == attacker + "P":
            return True

    # Knights
    for dx, dy in KNIGHT_DIRS:
        ax, ay = x + dx, y + dy
        if inside(ax, ay) and board.get(xy_to_sq(ax, ay)) == attacker + "N":
            return True

    # King
    for dx, dy in KING_DIRS:
        ax, ay = x + dx, y + dy
        if inside(ax, ay) and board.get(xy_to_sq(ax, ay)) == attacker + "K":
            return True

    # Sliders
    for dirs, pieces in ((BISHOP_DIRS, ("B", "Q")), (ROOK_DIRS, ("R", "Q"))):
        for dx, dy in dirs:
            ax, ay = x + dx, y + dy
            while inside(ax, ay):
                p = board.get(xy_to_sq(ax, ay))
                if p:
                    if p[0] == attacker and p[1] in pieces:
                        return True
                    break
                ax += dx
                ay += dy
    return False

def in_check(board, color):
    k = find_king(board, color)
    if k is None:
        return True
    return attacked_by(board, k, other(color))

def make_move(board, move):
    nb = dict(board)
    frm, to = move[:2], move[2:4]
    p = nb.pop(frm)
    if to in nb:
        nb.pop(to)
    if len(move) > 4:
        p = p[0] + move[4].upper()
    nb[to] = p
    return nb

def pseudo_moves(board, color):
    moves = []
    for s, p in list(board.items()):
        if p[0] != color:
            continue
        typ = p[1]
        x, y = sq_to_xy(s)

        if typ == "P":
            d = 1 if color == "w" else -1
            start = 1 if color == "w" else 6
            promo_y = 7 if color == "w" else 0

            ny = y + d
            if inside(x, ny) and xy_to_sq(x, ny) not in board:
                to = xy_to_sq(x, ny)
                if ny == promo_y:
                    for pr in "qrbn":
                        moves.append(s + to + pr)
                else:
                    moves.append(s + to)
                    if y == start:
                        ny2 = y + 2*d
                        if inside(x, ny2) and xy_to_sq(x, ny2) not in board:
                            moves.append(s + xy_to_sq(x, ny2))

            for dx in (-1, 1):
                nx, ny = x + dx, y + d
                if inside(nx, ny):
                    to = xy_to_sq(nx, ny)
                    if to in board and board[to][0] != color:
                        if ny == promo_y:
                            for pr in "qrbn":
                                moves.append(s + to + pr)
                        else:
                            moves.append(s + to)

        elif typ == "N":
            for dx, dy in KNIGHT_DIRS:
                nx, ny = x + dx, y + dy
                if inside(nx, ny):
                    to = xy_to_sq(nx, ny)
                    if to not in board or board[to][0] != color:
                        moves.append(s + to)

        elif typ == "K":
            for dx, dy in KING_DIRS:
                nx, ny = x + dx, y + dy
                if inside(nx, ny):
                    to = xy_to_sq(nx, ny)
                    if to not in board or board[to][0] != color:
                        moves.append(s + to)

            # Conservative castling support if board position allows it.
            if color == "w" and s == "e1" and not in_check(board, color):
                if board.get("h1") == "wR" and "f1" not in board and "g1" not in board:
                    if not attacked_by(board, "f1", "b") and not attacked_by(board, "g1", "b"):
                        moves.append("e1g1")
                if board.get("a1") == "wR" and "b1" not in board and "c1" not in board and "d1" not in board:
                    if not attacked_by(board, "d1", "b") and not attacked_by(board, "c1", "b"):
                        moves.append("e1c1")
            if color == "b" and s == "e8" and not in_check(board, color):
                if board.get("h8") == "bR" and "f8" not in board and "g8" not in board:
                    if not attacked_by(board, "f8", "w") and not attacked_by(board, "g8", "w"):
                        moves.append("e8g8")
                if board.get("a8") == "bR" and "b8" not in board and "c8" not in board and "d8" not in board:
                    if not attacked_by(board, "d8", "w") and not attacked_by(board, "c8", "w"):
                        moves.append("e8c8")

        else:
            dirs = BISHOP_DIRS if typ == "B" else ROOK_DIRS if typ == "R" else QUEEN_DIRS
            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                while inside(nx, ny):
                    to = xy_to_sq(nx, ny)
                    if to in board:
                        if board[to][0] != color:
                            moves.append(s + to)
                        break
                    moves.append(s + to)
                    nx += dx
                    ny += dy
    return moves

def legal_moves(board, color):
    res = []
    for m in pseudo_moves(board, color):
        nb = make_move(board, m)
        if not in_check(nb, color):
            res.append(m)
    return res

def pst_bonus(piece, sq, color):
    x, y = sq_to_xy(sq)
    yy = y if color == "w" else 7 - y
    cx = abs(3.5 - x)
    cy = abs(3.5 - y)
    center_bonus = int(20 - 5 * (cx + cy))

    if piece == "P":
        return yy * 8 + (6 if sq in CENTER else 0) - int(cx * 2)
    if piece in ("N", "B"):
        return center_bonus + (8 if yy >= 2 else -8)
    if piece == "R":
        return yy * 2
    if piece == "Q":
        return center_bonus // 2
    if piece == "K":
        # Prefer safer edge/corner king in most simplified arena games.
        return int((cx + cy) * 3) if yy < 6 else -center_bonus
    return 0

def evaluate(board, perspective):
    opp = other(perspective)

    if find_king(board, perspective) is None:
        return -1000000
    if find_king(board, opp) is None:
        return 1000000

    score = 0
    for sq, p in board.items():
        c, t = p[0], p[1]
        val = PIECE_VAL[t] + pst_bonus(t, sq, c)
        if c == perspective:
            score += val
        else:
            score -= val

    # Mobility and check status
    try:
        score += 2 * (len(pseudo_moves(board, perspective)) - len(pseudo_moves(board, opp)))
    except Exception:
        pass

    if in_check(board, opp):
        score += 35
    if in_check(board, perspective):
        score -= 60

    return score

def move_order_score(board, m, color):
    frm, to = m[:2], m[2:4]
    p = board.get(frm, color + "P")
    score = 0
    cap = board.get(to)
    if cap:
        score += 10 * PIECE_VAL[cap[1]] - PIECE_VAL[p[1]]
    if len(m) > 4:
        score += PIECE_VAL[m[4].upper()]
    if to in CENTER:
        score += 20
    elif to in EXT_CENTER:
        score += 8
    nb = make_move(board, m)
    if in_check(nb, other(color)):
        score += 50
    return score

def search(board, color, perspective, depth, alpha, beta, end_time):
    if time.time() > end_time:
        return evaluate(board, perspective)

    moves = legal_moves(board, color)
    if not moves:
        if in_check(board, color):
            return -999000 if color == perspective else 999000
        return 0

    if depth <= 0:
        # Simple quiescence: examine only captures/promotions/checks one ply.
        stand = evaluate(board, perspective)
        noisy = []
        for m in moves:
            if board.get(m[2:4]) or len(m) > 4:
                noisy.append(m)
        if not noisy:
            return stand
        if color == perspective:
            best = stand
            for m in sorted(noisy, key=lambda x: move_order_score(board, x, color), reverse=True)[:8]:
                best = max(best, search(make_move(board, m), other(color), perspective, -1, alpha, beta, end_time))
                alpha = max(alpha, best)
                if beta <= alpha:
                    break
            return best
        else:
            best = stand
            for m in sorted(noisy, key=lambda x: move_order_score(board, x, color), reverse=True)[:8]:
                best = min(best, search(make_move(board, m), other(color), perspective, -1, alpha, beta, end_time))
                beta = min(beta, best)
                if beta <= alpha:
                    break
            return best

    ordered = sorted(moves, key=lambda x: move_order_score(board, x, color), reverse=True)

    if color == perspective:
        best = -10**9
        for m in ordered:
            val = search(make_move(board, m), other(color), perspective, depth-1, alpha, beta, end_time)
            if val > best:
                best = val
            alpha = max(alpha, best)
            if beta <= alpha:
                break
        return best
    else:
        best = 10**9
        for m in ordered:
            val = search(make_move(board, m), other(color), perspective, depth-1, alpha, beta, end_time)
            if val < best:
                best = val
            beta = min(beta, best)
            if beta <= alpha:
                break
        return best

def policy(pieces: dict[str, str], to_play: str) -> str:
    try:
        color = color_code(to_play)
        moves = legal_moves(pieces, color)

        # Absolute fallback: if generator somehow finds none, return a pseudo move.
        if not moves:
            pm = pseudo_moves(pieces, color)
            return pm[0] if pm else "a1a1"

        end_time = time.time() + 0.90

        # Immediate mate / king capture style wins.
        opp = other(color)
        for m in sorted(moves, key=lambda x: move_order_score(pieces, x, color), reverse=True):
            nb = make_move(pieces, m)
            om = legal_moves(nb, opp)
            if not om and in_check(nb, opp):
                return m
            if find_king(nb, opp) is None:
                return m

        # Depth selection by branching.
        n = len(moves)
        depth = 3
        if n > 35:
            depth = 2
        if len(pieces) <= 10 and n <= 25:
            depth = 4

        best_move = moves[0]
        best_val = -10**9

        ordered = sorted(moves, key=lambda x: move_order_score(pieces, x, color), reverse=True)

        # Iterative deepening for reliability.
        for d in range(1, depth + 1):
            if time.time() > end_time:
                break
            cur_best = best_move
            cur_val = -10**9
            alpha, beta = -10**9, 10**9
            for m in ordered:
                if time.time() > end_time:
                    break
                nb = make_move(pieces, m)
                val = search(nb, opp, color, d-1, alpha, beta, end_time)

                # Small root tactical bonuses.
                cap = pieces.get(m[2:4])
                if cap:
                    val += PIECE_VAL[cap[1]] // 20
                if len(m) > 4 and m[4] == "q":
                    val += 50
                if in_check(nb, opp):
                    val += 15

                if val > cur_val:
                    cur_val = val
                    cur_best = m
                alpha = max(alpha, cur_val)
            if time.time() <= end_time:
                best_move, best_val = cur_best, cur_val
                ordered = [best_move] + [m for m in ordered if m != best_move]

        return best_move if best_move in moves else moves[0]

    except Exception:
        # Last-resort legality-oriented fallback.
        try:
            color = color_code(to_play)
            ms = legal_moves(pieces, color)
            if ms:
                return ms[0]
            ps = pseudo_moves(pieces, color)
            if ps:
                return ps[0]
        except Exception:
            pass
        return "a1a1"
