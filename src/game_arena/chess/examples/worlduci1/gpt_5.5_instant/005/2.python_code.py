
import math
import time

FILES = "abcdefgh"
RANKS = "12345678"
PIECE_VAL = {"P": 100, "N": 320, "B": 330, "R": 500, "Q": 900, "K": 0}
DIRS_BISHOP = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
DIRS_ROOK = [(1, 0), (-1, 0), (0, 1), (0, -1)]
DIRS_QUEEN = DIRS_BISHOP + DIRS_ROOK
KNIGHT_DIRS = [(1, 2), (2, 1), (-1, 2), (-2, 1), (1, -2), (2, -1), (-1, -2), (-2, -1)]
KING_DIRS = DIRS_QUEEN

PST = {
    "P": [
        0, 0, 0, 0, 0, 0, 0, 0,
        50, 50, 50, 50, 50, 50, 50, 50,
        10, 10, 20, 30, 30, 20, 10, 10,
        5, 5, 10, 27, 27, 10, 5, 5,
        0, 0, 0, 25, 25, 0, 0, 0,
        5, -5, -10, 0, 0, -10, -5, 5,
        5, 10, 10, -25, -25, 10, 10, 5,
        0, 0, 0, 0, 0, 0, 0, 0
    ],
    "N": [
        -50, -40, -30, -30, -30, -30, -40, -50,
        -40, -20, 0, 5, 5, 0, -20, -40,
        -30, 5, 10, 15, 15, 10, 5, -30,
        -30, 0, 15, 20, 20, 15, 0, -30,
        -30, 5, 15, 20, 20, 15, 5, -30,
        -30, 0, 10, 15, 15, 10, 0, -30,
        -40, -20, 0, 0, 0, 0, -20, -40,
        -50, -40, -30, -30, -30, -30, -40, -50
    ],
    "B": [
        -20, -10, -10, -10, -10, -10, -10, -20,
        -10, 5, 0, 0, 0, 0, 5, -10,
        -10, 10, 10, 10, 10, 10, 10, -10,
        -10, 0, 10, 10, 10, 10, 0, -10,
        -10, 5, 5, 10, 10, 5, 5, -10,
        -10, 0, 5, 10, 10, 5, 0, -10,
        -10, 0, 0, 0, 0, 0, 0, -10,
        -20, -10, -10, -10, -10, -10, -10, -20
    ],
    "R": [
        0, 0, 5, 10, 10, 5, 0, 0,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        5, 10, 10, 10, 10, 10, 10, 5,
        0, 0, 0, 0, 0, 0, 0, 0
    ],
    "Q": [
        -20, -10, -10, -5, -5, -10, -10, -20,
        -10, 0, 0, 0, 0, 0, 0, -10,
        -10, 0, 5, 5, 5, 5, 0, -10,
        -5, 0, 5, 5, 5, 5, 0, -5,
        0, 0, 5, 5, 5, 5, 0, -5,
        -10, 5, 5, 5, 5, 5, 0, -10,
        -10, 0, 5, 0, 0, 0, 0, -10,
        -20, -10, -10, -5, -5, -10, -10, -20
    ],
    "K": [
        20, 30, 10, 0, 0, 10, 30, 20,
        20, 20, 0, 0, 0, 0, 20, 20,
        -10, -20, -20, -20, -20, -20, -20, -10,
        -20, -30, -30, -40, -40, -30, -30, -20,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30
    ]
}

def sq_to_xy(s):
    return ord(s[0]) - 97, ord(s[1]) - 49

def xy_to_sq(x, y):
    return chr(97 + x) + chr(49 + y)

def onb(x, y):
    return 0 <= x < 8 and 0 <= y < 8

def side_color(to_play):
    return "w" if to_play == "white" else "b"

def other(c):
    return "b" if c == "w" else "w"

def to_name(c):
    return "white" if c == "w" else "black"

def pst_value(pt, x, y, color):
    idx = y * 8 + x if color == "w" else (7 - y) * 8 + x
    return PST.get(pt, [0] * 64)[idx]

def find_king(board, color):
    k = color + "K"
    for s, p in board.items():
        if p == k:
            return s
    return None

def is_attacked(board, sq, by_color):
    x, y = sq_to_xy(sq)
    pawn_dir = 1 if by_color == "w" else -1
    for dx in (-1, 1):
        px, py = x - dx, y - pawn_dir
        if onb(px, py) and board.get(xy_to_sq(px, py)) == by_color + "P":
            return True
    for dx, dy in KNIGHT_DIRS:
        nx, ny = x + dx, y + dy
        if onb(nx, ny) and board.get(xy_to_sq(nx, ny)) == by_color + "N":
            return True
    for dx, dy in DIRS_BISHOP:
        nx, ny = x + dx, y + dy
        while onb(nx, ny):
            p = board.get(xy_to_sq(nx, ny))
            if p:
                if p[0] == by_color and p[1] in ("B", "Q"):
                    return True
                break
            nx += dx
            ny += dy
    for dx, dy in DIRS_ROOK:
        nx, ny = x + dx, y + dy
        while onb(nx, ny):
            p = board.get(xy_to_sq(nx, ny))
            if p:
                if p[0] == by_color and p[1] in ("R", "Q"):
                    return True
                break
            nx += dx
            ny += dy
    for dx, dy in KING_DIRS:
        nx, ny = x + dx, y + dy
        if onb(nx, ny) and board.get(xy_to_sq(nx, ny)) == by_color + "K":
            return True
    return False

def in_check(board, color):
    ksq = find_king(board, color)
    return bool(ksq and is_attacked(board, ksq, other(color)))

def pseudo_moves(board, color):
    moves = []
    for s, p in list(board.items()):
        if p[0] != color:
            continue
        x, y = sq_to_xy(s)
        pt = p[1]
        if pt == "P":
            d = 1 if color == "w" else -1
            start = 1 if color == "w" else 6
            prom_y = 7 if color == "w" else 0
            ny = y + d
            if onb(x, ny) and xy_to_sq(x, ny) not in board:
                dest = xy_to_sq(x, ny)
                if ny == prom_y:
                    for pr in "qrbn":
                        moves.append(s + dest + pr)
                else:
                    moves.append(s + dest)
                    ny2 = y + 2 * d
                    if y == start and onb(x, ny2) and xy_to_sq(x, ny2) not in board:
                        moves.append(s + xy_to_sq(x, ny2))
            for dx in (-1, 1):
                nx, ny = x + dx, y + d
                if onb(nx, ny):
                    dest = xy_to_sq(nx, ny)
                    q = board.get(dest)
                    if q and q[0] != color:
                        if ny == prom_y:
                            for pr in "qrbn":
                                moves.append(s + dest + pr)
                        else:
                            moves.append(s + dest)
        elif pt == "N":
            for dx, dy in KNIGHT_DIRS:
                nx, ny = x + dx, y + dy
                if onb(nx, ny):
                    dest = xy_to_sq(nx, ny)
                    q = board.get(dest)
                    if not q or q[0] != color:
                        moves.append(s + dest)
        elif pt in ("B", "R", "Q"):
            dirs = DIRS_BISHOP if pt == "B" else DIRS_ROOK if pt == "R" else DIRS_QUEEN
            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                while onb(nx, ny):
                    dest = xy_to_sq(nx, ny)
                    q = board.get(dest)
                    if not q:
                        moves.append(s + dest)
                    else:
                        if q[0] != color:
                            moves.append(s + dest)
                        break
                    nx += dx
                    ny += dy
        elif pt == "K":
            for dx, dy in KING_DIRS:
                nx, ny = x + dx, y + dy
                if onb(nx, ny):
                    dest = xy_to_sq(nx, ny)
                    q = board.get(dest)
                    if not q or q[0] != color:
                        moves.append(s + dest)
            # permissive castling if position has clear path; legality filtered by king safety after move
            if color == "w" and s == "e1":
                if board.get("h1") == "wR" and "f1" not in board and "g1" not in board:
                    moves.append("e1g1")
                if board.get("a1") == "wR" and "b1" not in board and "c1" not in board and "d1" not in board:
                    moves.append("e1c1")
            if color == "b" and s == "e8":
                if board.get("h8") == "bR" and "f8" not in board and "g8" not in board:
                    moves.append("e8g8")
                if board.get("a8") == "bR" and "b8" not in board and "c8" not in board and "d8" not in board:
                    moves.append("e8c8")
    return moves

def make_move(board, mv):
    nb = dict(board)
    frm, to = mv[:2], mv[2:4]
    p = nb.pop(frm, None)
    if not p:
        return nb
    # castling rook move
    if p[1] == "K" and abs(ord(to[0]) - ord(frm[0])) == 2:
        if to == "g1" and nb.get("h1") == "wR":
            nb.pop("h1"); nb["f1"] = "wR"
        elif to == "c1" and nb.get("a1") == "wR":
            nb.pop("a1"); nb["d1"] = "wR"
        elif to == "g8" and nb.get("h8") == "bR":
            nb.pop("h8"); nb["f8"] = "bR"
        elif to == "c8" and nb.get("a8") == "bR":
            nb.pop("a8"); nb["d8"] = "bR"
    if to in nb:
        nb.pop(to)
    if len(mv) > 4 and p[1] == "P":
        p = p[0] + mv[4].upper()
    nb[to] = p
    return nb

def legal_moves_for(board, color):
    res = []
    for mv in pseudo_moves(board, color):
        nb = make_move(board, mv)
        if not in_check(nb, color):
            # extra castling rule: cannot castle out of/through check
            if mv in ("e1g1", "e1c1", "e8g8", "e8c8"):
                if in_check(board, color):
                    continue
                through = {"e1g1": "f1", "e1c1": "d1", "e8g8": "f8", "e8c8": "d8"}[mv]
                if is_attacked(board, through, other(color)):
                    continue
            res.append(mv)
    return res

def evaluate(board, root):
    score = 0
    material_count = 0
    kings = {}
    for s, p in board.items():
        c, pt = p[0], p[1]
        x, y = sq_to_xy(s)
        val = PIECE_VAL[pt] + pst_value(pt, x, y, c)
        if pt != "K":
            material_count += PIECE_VAL[pt]
        if c == root:
            score += val
        else:
            score -= val
        if pt == "K":
            kings[c] = (x, y)
    if material_count < 1800:
        for c, (x, y) in kings.items():
            center = 14 - 4 * (abs(x - 3.5) + abs(y - 3.5))
            score += center if c == root else -center
    try:
        score += 3 * (len(pseudo_moves(board, root)) - len(pseudo_moves(board, other(root))))
    except Exception:
        pass
    return score

def move_score(board, mv, color):
    frm, to = mv[:2], mv[2:4]
    p = board.get(frm, color + "P")
    cap = board.get(to)
    sc = 0
    if cap:
        sc += 10 * PIECE_VAL[cap[1]] - PIECE_VAL[p[1]]
    if len(mv) > 4:
        sc += PIECE_VAL.get(mv[4].upper(), 900)
    if p[1] == "P" and to[1] in ("1", "8"):
        sc += 800
    return sc

def ordered_moves(board, color):
    ms = legal_moves_for(board, color)
    ms.sort(key=lambda m: move_score(board, m, color), reverse=True)
    return ms

def search(board, color, root, depth, alpha, beta, end_time):
    if time.time() > end_time:
        raise TimeoutError
    moves = ordered_moves(board, color)
    if not moves:
        if in_check(board, color):
            return -100000 + (3 - depth) if color == root else 100000 - (3 - depth)
        return 0
    if depth <= 0:
        stand = evaluate(board, root)
        # brief capture-only quiescence
        caps = [m for m in moves if board.get(m[2:4]) or len(m) > 4]
        if not caps:
            return stand
        best = stand
        for m in caps[:8]:
            val = search(make_move(board, m), other(color), root, -1, alpha, beta, end_time)
            if color == root:
                best = max(best, val); alpha = max(alpha, best)
            else:
                best = min(best, val); beta = min(beta, best)
            if beta <= alpha:
                break
        return best
    if color == root:
        best = -10**9
        for m in moves:
            val = search(make_move(board, m), other(color), root, depth - 1, alpha, beta, end_time)
            if val > best:
                best = val
            alpha = max(alpha, best)
            if beta <= alpha:
                break
        return best
    else:
        best = 10**9
        for m in moves:
            val = search(make_move(board, m), other(color), root, depth - 1, alpha, beta, end_time)
            if val < best:
                best = val
            beta = min(beta, best)
            if beta <= alpha:
                break
        return best

def policy(pieces: dict[str, str], to_play: str) -> str:
    try:
        color = side_color(to_play)
        moves = ordered_moves(pieces, color)
        if not moves:
            return "0000"
        best_move = moves[0]
        best_val = -10**9
        end_time = time.time() + 0.85

        # Immediate mate/capture promotion checks and iterative deepening.
        for depth in (1, 2, 3):
            if time.time() > end_time:
                break
            local_best = best_move
            local_val = -10**9
            try:
                for mv in moves:
                    nb = make_move(pieces, mv)
                    om = legal_moves_for(nb, other(color))
                    if not om and in_check(nb, other(color)):
                        return mv
                    val = search(nb, other(color), color, depth - 1, -10**9, 10**9, end_time)
                    # small deterministic tie-break by tactical move score
                    val += move_score(pieces, mv, color) * 0.01
                    if val > local_val:
                        local_val = val
                        local_best = mv
                best_move, best_val = local_best, local_val
            except TimeoutError:
                break
        return best_move if best_move in legal_moves_for(pieces, color) else moves[0]
    except Exception:
        try:
            color = side_color(to_play)
            ms = legal_moves_for(pieces, color)
            return ms[0] if ms else "0000"
        except Exception:
            return "0000"
