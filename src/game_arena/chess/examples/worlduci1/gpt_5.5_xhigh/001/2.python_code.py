
import time

FILES = "abcdefgh"
SQUARE_NAMES = [FILES[f] + str(r + 1) for r in range(8) for f in range(8)]
FILE = [i & 7 for i in range(64)]
RANK = [i >> 3 for i in range(64)]
MIRROR = [FILE[i] + 8 * (7 - RANK[i]) for i in range(64)]

OTHER = {"w": "b", "b": "w"}
PROMOS = ("q", "r", "b", "n")

VAL = {
    "P": 100,
    "N": 320,
    "B": 330,
    "R": 500,
    "Q": 900,
    "K": 0,
}

MATE = 100000
INF = 10**9
TIME_LIMIT = 0.88

# ---------- Move tables ----------

KNIGHT_MOVES = [[] for _ in range(64)]
KING_MOVES = [[] for _ in range(64)]

for sq in range(64):
    f, r = FILE[sq], RANK[sq]

    for df, dr in (
        (1, 2), (2, 1), (2, -1), (1, -2),
        (-1, -2), (-2, -1), (-2, 1), (-1, 2),
    ):
        nf, nr = f + df, r + dr
        if 0 <= nf < 8 and 0 <= nr < 8:
            KNIGHT_MOVES[sq].append(nf + 8 * nr)

    for df, dr in (
        (1, 1), (1, 0), (1, -1), (0, 1),
        (0, -1), (-1, 1), (-1, 0), (-1, -1),
    ):
        nf, nr = f + df, r + dr
        if 0 <= nf < 8 and 0 <= nr < 8:
            KING_MOVES[sq].append(nf + 8 * nr)

DIRS = (
    (1, 0), (-1, 0), (0, 1), (0, -1),
    (1, 1), (1, -1), (-1, 1), (-1, -1),
)
RAYS = [[[] for _ in range(8)] for _ in range(64)]

for sq in range(64):
    f, r = FILE[sq], RANK[sq]
    for d, (df, dr) in enumerate(DIRS):
        nf, nr = f + df, r + dr
        while 0 <= nf < 8 and 0 <= nr < 8:
            RAYS[sq][d].append(nf + 8 * nr)
            nf += df
            nr += dr

# ---------- Piece-square tables ----------

def _mk_table(rows):
    # rows are rank 8 down to rank 1; output is a1..h8
    return [rows[7 - r][f] for r in range(8) for f in range(8)]

PST = {
    "P": _mk_table([
        [0, 0, 0, 0, 0, 0, 0, 0],
        [80, 80, 80, 80, 80, 80, 80, 80],
        [30, 30, 40, 50, 50, 40, 30, 30],
        [15, 15, 25, 40, 40, 25, 15, 15],
        [5, 5, 10, 30, 30, 10, 5, 5],
        [5, -5, -10, 10, 10, -10, -5, 5],
        [5, 10, 10, -20, -20, 10, 10, 5],
        [0, 0, 0, 0, 0, 0, 0, 0],
    ]),
    "N": _mk_table([
        [-50, -40, -30, -30, -30, -30, -40, -50],
        [-40, -20, 0, 5, 5, 0, -20, -40],
        [-30, 5, 10, 15, 15, 10, 5, -30],
        [-30, 0, 15, 25, 25, 15, 0, -30],
        [-30, 5, 15, 25, 25, 15, 5, -30],
        [-30, 0, 10, 15, 15, 10, 0, -30],
        [-40, -20, 0, 0, 0, 0, -20, -40],
        [-50, -40, -30, -30, -30, -30, -40, -50],
    ]),
    "B": _mk_table([
        [-20, -10, -10, -10, -10, -10, -10, -20],
        [-10, 5, 0, 0, 0, 0, 5, -10],
        [-10, 10, 10, 10, 10, 10, 10, -10],
        [-10, 0, 10, 15, 15, 10, 0, -10],
        [-10, 5, 5, 15, 15, 5, 5, -10],
        [-10, 0, 5, 10, 10, 5, 0, -10],
        [-10, 0, 0, 0, 0, 0, 0, -10],
        [-20, -10, -10, -10, -10, -10, -10, -20],
    ]),
    "R": _mk_table([
        [0, 0, 5, 10, 10, 5, 0, 0],
        [10, 15, 15, 20, 20, 15, 15, 10],
        [-5, 0, 0, 5, 5, 0, 0, -5],
        [-5, 0, 0, 5, 5, 0, 0, -5],
        [-5, 0, 0, 5, 5, 0, 0, -5],
        [-5, 0, 0, 5, 5, 0, 0, -5],
        [-5, 0, 0, 5, 5, 0, 0, -5],
        [0, 0, 5, 10, 10, 5, 0, 0],
    ]),
    "Q": _mk_table([
        [-20, -10, -10, -5, -5, -10, -10, -20],
        [-10, 0, 5, 0, 0, 0, 0, -10],
        [-10, 5, 5, 5, 5, 5, 0, -10],
        [0, 0, 5, 8, 8, 5, 0, -5],
        [-5, 0, 5, 8, 8, 5, 0, -5],
        [-10, 0, 5, 5, 5, 5, 0, -10],
        [-10, 0, 0, 0, 0, 0, 0, -10],
        [-20, -10, -10, -5, -5, -10, -10, -20],
    ]),
}

KING_MID = _mk_table([
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-20, -30, -30, -40, -40, -30, -30, -20],
    [-10, -20, -20, -20, -20, -20, -20, -10],
    [20, 20, 0, 0, 0, 0, 20, 20],
    [20, 30, 10, 0, 0, 10, 30, 20],
])

KING_END = _mk_table([
    [-50, -30, -30, -30, -30, -30, -30, -50],
    [-30, -10, 0, 0, 0, 0, -10, -30],
    [-30, 0, 20, 30, 30, 20, 0, -30],
    [-30, 0, 30, 45, 45, 30, 0, -30],
    [-30, 0, 30, 45, 45, 30, 0, -30],
    [-30, 0, 20, 30, 30, 20, 0, -30],
    [-30, -10, 0, 0, 0, 0, -10, -30],
    [-50, -30, -30, -30, -30, -30, -30, -50],
])

PASS_BONUS = [0, 5, 12, 25, 45, 75, 120, 0]

# ---------- Zobrist hashing ----------

_MASK64 = (1 << 64) - 1
_zseed = 0x9E3779B97F4A7C15

def _rand64():
    global _zseed
    _zseed = (_zseed + 0x9E3779B97F4A7C15) & _MASK64
    z = _zseed
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & _MASK64
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & _MASK64
    return (z ^ (z >> 31)) & _MASK64

PIECE_CODES = [
    "wP", "wN", "wB", "wR", "wQ", "wK",
    "bP", "bN", "bB", "bR", "bQ", "bK",
]
PIECE_INDEX = {p: i for i, p in enumerate(PIECE_CODES)}
ZPIECE = [[_rand64() for _ in range(64)] for _ in range(12)]
SIDE_HASH = _rand64()

# ---------- Globals used by search ----------

class SearchTimeout(Exception):
    pass

DEADLINE = 0.0
NODES = 0
TT = {}
KILLERS = [[None, None] for _ in range(128)]
HISTORY = {}

# ---------- Board helpers ----------

def square_index(s):
    if not isinstance(s, str) or len(s) != 2:
        return -1
    f = ord(s[0].lower()) - ord("a")
    r = ord(s[1]) - ord("1")
    if 0 <= f < 8 and 0 <= r < 8:
        return f + 8 * r
    return -1

def make_board(pieces):
    board = [None] * 64
    for sq, pc in pieces.items():
        idx = square_index(sq)
        if idx < 0 or not isinstance(pc, str) or len(pc) < 2:
            continue
        c = pc[0].lower()
        t = pc[1].upper()
        if c in ("w", "b") and t in VAL:
            board[idx] = c + t
    return board

def move_to_uci(m):
    fr, to, promo = m
    return SQUARE_NAMES[fr] + SQUARE_NAMES[to] + promo

def find_king(board, color):
    target = color + "K"
    for i, p in enumerate(board):
        if p == target:
            return i
    return None

def zobrist_hash(board, color):
    h = SIDE_HASH if color == "b" else 0
    for sq, p in enumerate(board):
        if p is not None:
            pi = PIECE_INDEX.get(p)
            if pi is not None:
                h ^= ZPIECE[pi][sq]
    return h

def hash_after_move(h, m, piece, captured):
    fr, to, promo = m
    if piece is None:
        return h ^ SIDE_HASH
    moved = piece if not promo else piece[0] + promo.upper()
    h ^= ZPIECE[PIECE_INDEX[piece]][fr]
    if captured is not None:
        h ^= ZPIECE[PIECE_INDEX[captured]][to]
    h ^= ZPIECE[PIECE_INDEX[moved]][to]
    h ^= SIDE_HASH
    return h

def apply_move(board, m):
    fr, to, promo = m
    piece = board[fr]
    captured = board[to]
    board[fr] = None
    board[to] = piece if not promo else piece[0] + promo.upper()
    return piece, captured

def undo_move(board, m, old_piece, captured):
    fr, to, _ = m
    board[fr] = old_piece
    board[to] = captured

# ---------- Attack and legal move generation ----------

def is_attacked(board, sq, attacker):
    f, r = FILE[sq], RANK[sq]

    pawn = attacker + "P"
    if attacker == "w":
        sr = r - 1
    else:
        sr = r + 1
    if 0 <= sr < 8:
        for df in (-1, 1):
            sf = f + df
            if 0 <= sf < 8 and board[sf + 8 * sr] == pawn:
                return True

    knight = attacker + "N"
    for src in KNIGHT_MOVES[sq]:
        if board[src] == knight:
            return True

    king = attacker + "K"
    for src in KING_MOVES[sq]:
        if board[src] == king:
            return True

    for d in range(4):
        for src in RAYS[sq][d]:
            p = board[src]
            if p is not None:
                if p[0] == attacker and (p[1] == "R" or p[1] == "Q"):
                    return True
                break

    for d in range(4, 8):
        for src in RAYS[sq][d]:
            p = board[src]
            if p is not None:
                if p[0] == attacker and (p[1] == "B" or p[1] == "Q"):
                    return True
                break

    return False

def in_check(board, color):
    ksq = find_king(board, color)
    if ksq is None:
        return False
    return is_attacked(board, ksq, OTHER[color])

def gen_pseudo_moves(board, color, tactical=False):
    moves = []
    opp = OTHER[color]

    for fr, piece in enumerate(board):
        if piece is None or piece[0] != color:
            continue

        pt = piece[1]
        f, r = FILE[fr], RANK[fr]

        if pt == "P":
            dr = 1 if color == "w" else -1
            start_rank = 1 if color == "w" else 6
            promo_rank = 7 if color == "w" else 0
            tr = r + dr

            if 0 <= tr < 8:
                one = f + 8 * tr
                if board[one] is None:
                    if tr == promo_rank:
                        for pr in PROMOS:
                            moves.append((fr, one, pr))
                    elif not tactical:
                        moves.append((fr, one, ""))
                        if r == start_rank:
                            tr2 = r + 2 * dr
                            two = f + 8 * tr2
                            if 0 <= tr2 < 8 and board[two] is None:
                                moves.append((fr, two, ""))

                for df in (-1, 1):
                    tf = f + df
                    if 0 <= tf < 8:
                        to = tf + 8 * tr
                        target = board[to]
                        if target is not None and target[0] == opp and target[1] != "K":
                            if tr == promo_rank:
                                for pr in PROMOS:
                                    moves.append((fr, to, pr))
                            else:
                                moves.append((fr, to, ""))

        elif pt == "N":
            for to in KNIGHT_MOVES[fr]:
                target = board[to]
                if target is None:
                    if not tactical:
                        moves.append((fr, to, ""))
                elif target[0] == opp and target[1] != "K":
                    moves.append((fr, to, ""))

        elif pt == "K":
            for to in KING_MOVES[fr]:
                target = board[to]
                if target is None:
                    if not tactical:
                        moves.append((fr, to, ""))
                elif target[0] == opp and target[1] != "K":
                    moves.append((fr, to, ""))

        elif pt in ("B", "R", "Q"):
            if pt == "B":
                dirs = range(4, 8)
            elif pt == "R":
                dirs = range(4)
            else:
                dirs = range(8)

            for d in dirs:
                for to in RAYS[fr][d]:
                    target = board[to]
                    if target is None:
                        if not tactical:
                            moves.append((fr, to, ""))
                    else:
                        if target[0] == opp and target[1] != "K":
                            moves.append((fr, to, ""))
                        break

    return moves

def gen_legal_moves(board, color, tactical=False):
    pseudo = gen_pseudo_moves(board, color, tactical)
    if not pseudo:
        return []

    legal = []
    ksq = find_king(board, color)
    opp = OTHER[color]

    for m in pseudo:
        fr, to, promo = m
        piece = board[fr]
        captured = board[to]

        board[fr] = None
        board[to] = piece if not promo else piece[0] + promo.upper()

        new_ksq = to if piece[1] == "K" else ksq
        if new_ksq is None or not is_attacked(board, new_ksq, opp):
            legal.append(m)

        board[fr] = piece
        board[to] = captured

    return legal

# ---------- Evaluation ----------

def _piece_square(pt, color, sq, phase=1.0):
    idx = sq if color == "w" else MIRROR[sq]
    if pt == "K":
        return int(phase * KING_MID[idx] + (1.0 - phase) * KING_END[idx])
    return PST[pt][idx]

def evaluate(board, perspective):
    score_side = {"w": 0, "b": 0}
    material = {"w": 0, "b": 0}
    pawns = {"w": [], "b": []}
    pawn_files = {"w": [0] * 8, "b": [0] * 8}
    bishops = {"w": 0, "b": 0}
    rooks = {"w": [], "b": []}
    queens = {"w": [], "b": []}
    knights = {"w": [], "b": []}
    kings = {}
    nonpawn = 0

    for sq, p in enumerate(board):
        if p is None:
            continue
        c, pt = p[0], p[1]
        idx = sq if c == "w" else MIRROR[sq]

        if pt == "K":
            kings[c] = sq
            continue

        v = VAL[pt]
        material[c] += v
        if pt in "NBRQ":
            nonpawn += v

        score_side[c] += v + PST[pt][idx]

        if pt == "P":
            pawns[c].append(sq)
            pawn_files[c][FILE[sq]] += 1
        elif pt == "B":
            bishops[c] += 1
        elif pt == "R":
            rooks[c].append(sq)
        elif pt == "Q":
            queens[c].append(sq)
        elif pt == "N":
            knights[c].append(sq)

    phase = min(1.0, nonpawn / 6400.0)

    for c in ("w", "b"):
        if c in kings:
            score_side[c] += _piece_square("K", c, kings[c], phase)

    for c in ("w", "b"):
        opp = OTHER[c]

        if bishops[c] >= 2:
            score_side[c] += 35

        for f in range(8):
            cnt = pawn_files[c][f]
            if cnt > 1:
                score_side[c] -= 12 * (cnt - 1)

        for psq in pawns[c]:
            f, r = FILE[psq], RANK[psq]
            advance = r if c == "w" else 7 - r

            left = pawn_files[c][f - 1] if f > 0 else 0
            right = pawn_files[c][f + 1] if f < 7 else 0
            if left == 0 and right == 0:
                score_side[c] -= 8

            support_rank = r - 1 if c == "w" else r + 1
            protected = False
            if 0 <= support_rank < 8:
                for df in (-1, 1):
                    sf = f + df
                    if 0 <= sf < 8 and board[sf + 8 * support_rank] == c + "P":
                        protected = True
                        break
            if protected:
                score_side[c] += 4 + advance

            passed = True
            for ep in pawns[opp]:
                ef, er = FILE[ep], RANK[ep]
                if abs(ef - f) <= 1:
                    if (c == "w" and er > r) or (c == "b" and er < r):
                        passed = False
                        break
            if passed:
                score_side[c] += PASS_BONUS[advance]

        for rsq in rooks[c]:
            f, r = FILE[rsq], RANK[rsq]
            if pawn_files[c][f] == 0:
                score_side[c] += 18 if pawn_files[opp][f] == 0 else 9
            if (c == "w" and r == 6) or (c == "b" and r == 1):
                score_side[c] += 18

        for qsq in queens[c]:
            r = RANK[qsq]
            if (c == "w" and r == 6) or (c == "b" and r == 1):
                score_side[c] += 8

        for nsq in knights[c]:
            f, r = FILE[nsq], RANK[nsq]
            advance = r if c == "w" else 7 - r
            if advance >= 3:
                support_rank = r - 1 if c == "w" else r + 1
                if 0 <= support_rank < 8:
                    for df in (-1, 1):
                        sf = f + df
                        if 0 <= sf < 8 and board[sf + 8 * support_rank] == c + "P":
                            score_side[c] += 10
                            break

    # Middlegame king safety.
    if phase > 0.05:
        for c in ("w", "b"):
            if c not in kings:
                continue
            ksq = kings[c]
            kf, kr = FILE[ksq], RANK[ksq]
            forward = 1 if c == "w" else -1
            safety = 0

            for df in (-1, 0, 1):
                sf = kf + df
                if not (0 <= sf < 8):
                    continue

                r1 = kr + forward
                if 0 <= r1 < 8:
                    p = board[sf + 8 * r1]
                    if p == c + "P":
                        safety += 12 if df == 0 else 10
                    elif p is None:
                        safety -= 4
                    else:
                        safety -= 2

                r2 = kr + 2 * forward
                if 0 <= r2 < 8 and board[sf + 8 * r2] == c + "P":
                    safety += 4

            if c == "w":
                if kr >= 2:
                    safety -= 8 * (kr - 1)
            else:
                if kr <= 5:
                    safety -= 8 * (6 - kr)

            if 2 <= kf <= 5:
                safety -= 4

            score_side[c] += int(safety * phase)

    # Endgame: when winning, push enemy king to the edge and bring own king closer.
    if "w" in kings and "b" in kings:
        diff = material["w"] - material["b"]
        if abs(diff) >= 350:
            strong = "w" if diff > 0 else "b"
            weak = OTHER[strong]
            if material[weak] <= 650:
                wk = kings[weak]
                sk = kings[strong]
                edge = max(abs(FILE[wk] - 3.5), abs(RANK[wk] - 3.5))
                dist = abs(FILE[wk] - FILE[sk]) + abs(RANK[wk] - RANK[sk])
                score_side[strong] += int(edge * 20 + (14 - dist) * 4)

    return int(score_side[perspective] - score_side[OTHER[perspective]] + 8)

# ---------- Move ordering/search ----------

def _check_time():
    global NODES
    NODES += 1
    if (NODES & 1023) == 0 and time.perf_counter() > DEADLINE:
        raise SearchTimeout()

def quick_move_score(board, m, color, ply=0, tt_move=None):
    if tt_move is not None and m == tt_move:
        return 10_000_000

    fr, to, promo = m
    piece = board[fr]
    if piece is None:
        return 0

    pt = piece[1]
    captured = board[to]
    score = 0

    if captured is not None:
        score += 1_000_000 + 20 * VAL[captured[1]] - VAL[pt]

    if promo:
        score += 900_000 + VAL[promo.upper()]

    if ply < len(KILLERS):
        if m == KILLERS[ply][0]:
            score += 800_000
        elif m == KILLERS[ply][1]:
            score += 700_000

    score += HISTORY.get((color, fr, to, promo), 0)

    new_pt = promo.upper() if promo else pt
    score += _piece_square(new_pt, color, to, 1.0) - _piece_square(pt, color, fr, 1.0)
    return score

def order_moves(moves, board, color, ply=0, tt_move=None):
    moves.sort(key=lambda mv: quick_move_score(board, mv, color, ply, tt_move), reverse=True)

def remember_cutoff(m, color, depth, ply):
    if ply < len(KILLERS):
        if KILLERS[ply][0] != m:
            KILLERS[ply][1] = KILLERS[ply][0]
            KILLERS[ply][0] = m

    key = (color, m[0], m[1], m[2])
    HISTORY[key] = min(HISTORY.get(key, 0) + depth * depth, 1_000_000)

def quiesce(board, color, alpha, beta, ply, h, qleft):
    _check_time()

    checked = in_check(board, color)
    if checked:
        moves = gen_legal_moves(board, color, False)
        if not moves:
            return -MATE + ply
        if qleft < 0:
            return evaluate(board, color) - 75

        order_moves(moves, board, color, ply, None)
        opp = OTHER[color]

        for m in moves:
            piece = board[m[0]]
            captured = board[m[1]]
            h2 = hash_after_move(h, m, piece, captured)
            old_piece, old_captured = apply_move(board, m)
            try:
                val = -quiesce(board, opp, -beta, -alpha, ply + 1, h2, qleft - 1)
            finally:
                undo_move(board, m, old_piece, old_captured)

            if val >= beta:
                return beta
            if val > alpha:
                alpha = val
        return alpha

    stand = evaluate(board, color)
    if stand >= beta:
        return beta
    if stand > alpha:
        alpha = stand

    if qleft <= 0:
        return alpha

    moves = gen_legal_moves(board, color, True)
    if not moves:
        return alpha

    order_moves(moves, board, color, ply, None)
    opp = OTHER[color]

    for m in moves:
        piece = board[m[0]]
        captured = board[m[1]]
        h2 = hash_after_move(h, m, piece, captured)
        old_piece, old_captured = apply_move(board, m)
        try:
            val = -quiesce(board, opp, -beta, -alpha, ply + 1, h2, qleft - 1)
        finally:
            undo_move(board, m, old_piece, old_captured)

        if val >= beta:
            return beta
        if val > alpha:
            alpha = val

    return alpha

def negamax(board, color, depth, alpha, beta, ply, h):
    _check_time()

    alpha_orig = alpha
    tt_move = None
    entry = TT.get(h)

    if entry is not None:
        tt_depth, tt_flag, tt_value, tt_best = entry
        tt_move = tt_best
        if tt_depth >= depth:
            if tt_flag == 0:
                return tt_value
            if tt_flag == 1 and tt_value > alpha:
                alpha = tt_value
            elif tt_flag == 2 and tt_value < beta:
                beta = tt_value
            if alpha >= beta:
                return tt_value

    if depth <= 0:
        return quiesce(board, color, alpha, beta, ply, h, 4)

    moves = gen_legal_moves(board, color, False)
    if not moves:
        return -MATE + ply if in_check(board, color) else 0

    order_moves(moves, board, color, ply, tt_move)
    opp = OTHER[color]
    best = -INF
    best_move = None

    for m in moves:
        piece = board[m[0]]
        captured = board[m[1]]
        h2 = hash_after_move(h, m, piece, captured)
        old_piece, old_captured = apply_move(board, m)
        try:
            val = -negamax(board, opp, depth - 1, -beta, -alpha, ply + 1, h2)
        finally:
            undo_move(board, m, old_piece, old_captured)

        if val > best:
            best = val
            best_move = m
        if val > alpha:
            alpha = val
        if alpha >= beta:
            if captured is None and not m[2]:
                remember_cutoff(m, color, depth, ply)
            break

    if best <= alpha_orig:
        flag = 2  # upper bound
    elif best >= beta:
        flag = 1  # lower bound
    else:
        flag = 0  # exact

    if len(TT) < 200000:
        TT[h] = (depth, flag, best, best_move)

    return best

def search_root(board, color, moves, depth, h, best_hint):
    root_moves = list(moves)
    order_moves(root_moves, board, color, 0, best_hint)

    alpha = -INF
    beta = INF
    best_score = -INF
    best_move = best_hint if best_hint is not None else root_moves[0]
    opp = OTHER[color]

    for m in root_moves:
        piece = board[m[0]]
        captured = board[m[1]]
        h2 = hash_after_move(h, m, piece, captured)
        old_piece, old_captured = apply_move(board, m)
        try:
            val = -negamax(board, opp, depth - 1, -beta, -alpha, 1, h2)
        finally:
            undo_move(board, m, old_piece, old_captured)

        if val > best_score:
            best_score = val
            best_move = m
        if val > alpha:
            alpha = val

    return best_score, best_move

def static_select(board, color, moves):
    opp = OTHER[color]
    best = moves[0]
    best_score = -INF
    best_tie = -INF

    for m in moves:
        tie = quick_move_score(board, m, color, 0, None)
        old_piece, old_captured = apply_move(board, m)
        try:
            score = -evaluate(board, opp)
            if in_check(board, opp):
                score += 25
        finally:
            undo_move(board, m, old_piece, old_captured)

        if score > best_score or (score == best_score and tie > best_tie):
            best_score = score
            best_tie = tie
            best = m

    return best

def choose_max_depth(piece_count, move_count):
    if move_count > 45:
        return 3
    if piece_count <= 5:
        return 7
    if piece_count <= 8:
        return 6
    if piece_count <= 12:
        return 5
    if piece_count <= 20:
        return 5 if move_count <= 18 else 4
    return 4 if move_count <= 30 else 3

# Optional compatibility if an arena exposes a global legal_moves list.
def _external_legal_list():
    lm = globals().get("legal_moves", None)
    if lm is None or callable(lm):
        return None
    try:
        out = [x for x in lm if isinstance(x, str)]
    except Exception:
        return None
    return out if out else None

def _finalize_return(move, candidates, external):
    u = move_to_uci(move) if move is not None else None

    if external:
        ext_set = set(external)
        if u in ext_set:
            return u
        for m in candidates:
            s = move_to_uci(m)
            if s in ext_set:
                return s
        return external[0]

    return u if u is not None else "0000"

def _policy_impl(pieces, to_play, external):
    global DEADLINE, NODES

    start = time.perf_counter()
    DEADLINE = start + TIME_LIMIT
    NODES = 0
    TT.clear()

    for k in KILLERS:
        k[0] = None
        k[1] = None

    if len(HISTORY) > 50000:
        HISTORY.clear()

    color = "w" if str(to_play).lower().startswith("w") else "b"
    board = make_board(pieces)
    moves = gen_legal_moves(board, color, False)

    if not moves:
        if external:
            return external[0]
        return "0000"

    if len(moves) == 1:
        return _finalize_return(moves[0], moves, external)

    ordered = list(moves)
    order_moves(ordered, board, color, 0, None)
    opp = OTHER[color]

    # Immediate mate-in-one.
    for m in ordered:
        if time.perf_counter() > DEADLINE - 0.05:
            break
        old_piece, old_captured = apply_move(board, m)
        try:
            if in_check(board, opp) and not gen_legal_moves(board, opp, False):
                return _finalize_return(m, ordered, external)
        finally:
            undo_move(board, m, old_piece, old_captured)

    best_move = static_select(board, color, ordered)
    best_score = -INF

    h = zobrist_hash(board, color)
    piece_count = sum(1 for p in board if p is not None)
    max_depth = choose_max_depth(piece_count, len(moves))

    for depth in range(1, max_depth + 1):
        if time.perf_counter() > DEADLINE - 0.02:
            break
        try:
            score, move = search_root(board, color, moves, depth, h, best_move)
            if move is not None:
                best_move = move
                best_score = score
            if best_score > MATE - 1000:
                break
        except SearchTimeout:
            break

    return _finalize_return(best_move, moves, external)

def policy(pieces: dict[str, str], to_play: str) -> str:
    external = _external_legal_list()
    try:
        return _policy_impl(pieces, to_play, external)
    except Exception:
        if external:
            return external[0]
        try:
            color = "w" if str(to_play).lower().startswith("w") else "b"
            board = make_board(pieces)
            moves = gen_legal_moves(board, color, False)
            if moves:
                return move_to_uci(moves[0])
        except Exception:
            pass
        return "0000"
