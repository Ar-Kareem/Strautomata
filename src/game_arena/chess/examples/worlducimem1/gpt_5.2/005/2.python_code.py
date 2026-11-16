
import time
import random
import re
from typing import Dict, List, Tuple, Optional

# -----------------------------
# Utilities: squares / board
# -----------------------------
FILES = "abcdefgh"
RANKS = "12345678"

PIECE_VALUES = {
    "P": 100,
    "N": 320,
    "B": 330,
    "R": 500,
    "Q": 900,
    "K": 0,
}

# Piece-square tables (middlegame-ish), from White POV. Black mirrors.
PST = {
    "P": [
         0,  0,  0,  0,  0,  0,  0,  0,
        50, 50, 50, 50, 50, 50, 50, 50,
        10, 10, 20, 30, 30, 20, 10, 10,
         5,  5, 10, 25, 25, 10,  5,  5,
         0,  0,  0, 20, 20,  0,  0,  0,
         5, -5,-10,  0,  0,-10, -5,  5,
         5, 10, 10,-20,-20, 10, 10,  5,
         0,  0,  0,  0,  0,  0,  0,  0,
    ],
    "N": [
        -50,-40,-30,-30,-30,-30,-40,-50,
        -40,-20,  0,  0,  0,  0,-20,-40,
        -30,  0, 10, 15, 15, 10,  0,-30,
        -30,  5, 15, 20, 20, 15,  5,-30,
        -30,  0, 15, 20, 20, 15,  0,-30,
        -30,  5, 10, 15, 15, 10,  5,-30,
        -40,-20,  0,  5,  5,  0,-20,-40,
        -50,-40,-30,-30,-30,-30,-40,-50,
    ],
    "B": [
        -20,-10,-10,-10,-10,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5, 10, 10,  5,  0,-10,
        -10,  5,  5, 10, 10,  5,  5,-10,
        -10,  0, 10, 10, 10, 10,  0,-10,
        -10, 10, 10, 10, 10, 10, 10,-10,
        -10,  5,  0,  0,  0,  0,  5,-10,
        -20,-10,-10,-10,-10,-10,-10,-20,
    ],
    "R": [
         0,  0,  0,  0,  0,  0,  0,  0,
         5, 10, 10, 10, 10, 10, 10,  5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
         0,  0,  0,  5,  5,  0,  0,  0,
    ],
    "Q": [
        -20,-10,-10, -5, -5,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5,  5,  5,  5,  0,-10,
         -5,  0,  5,  5,  5,  5,  0, -5,
          0,  0,  5,  5,  5,  5,  0, -5,
        -10,  5,  5,  5,  5,  5,  0,-10,
        -10,  0,  5,  0,  0,  0,  0,-10,
        -20,-10,-10, -5, -5,-10,-10,-20,
    ],
    "K": [
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -20,-30,-30,-40,-40,-30,-30,-20,
        -10,-20,-20,-20,-20,-20,-20,-10,
         20, 20,  0,  0,  0,  0, 20, 20,
         20, 30, 10,  0,  0, 10, 30, 20,
    ],
}

KNIGHT_OFFSETS = (-17, -15, -10, -6, 6, 10, 15, 17)
KING_OFFSETS = (-9, -8, -7, -1, 1, 7, 8, 9)
BISHOP_DIRS = (-9, -7, 7, 9)
ROOK_DIRS = (-8, -1, 1, 8)
QUEEN_DIRS = BISHOP_DIRS + ROOK_DIRS

MATE_SCORE = 10_000_000
INF = 10_000_000_000

UCI_RE = re.compile(r"^[a-h][1-8][a-h][1-8][qrbn]?$")

def sq_to_idx(sq: str) -> int:
    f = FILES.index(sq[0])
    r = RANKS.index(sq[1])
    return r * 8 + f

def idx_to_sq(i: int) -> str:
    return FILES[i % 8] + RANKS[i // 8]

def color_to_char(to_play: str) -> str:
    return "w" if to_play == "white" else "b"

def opp(c: str) -> str:
    return "b" if c == "w" else "w"

def mirror_idx(i: int) -> int:
    # Mirror vertically for black PST lookup
    return (7 - (i // 8)) * 8 + (i % 8)

def in_bounds(i: int) -> bool:
    return 0 <= i < 64

def same_row(a: int, b: int) -> bool:
    return (a // 8) == (b // 8)

def is_white_piece(p: str) -> bool:
    return p[0] == "w"

def is_black_piece(p: str) -> bool:
    return p[0] == "b"

def piece_type(p: str) -> str:
    return p[1]

# -----------------------------
# Zobrist / TT
# -----------------------------
def init_zobrist(seed: int = 1337):
    rnd = random.Random(seed)
    pieces = [c + t for c in ("w", "b") for t in ("P", "N", "B", "R", "Q", "K")]
    z = {pc: [rnd.getrandbits(64) for _ in range(64)] for pc in pieces}
    z_turn = rnd.getrandbits(64)
    return z, z_turn

def compute_hash(board: List[Optional[str]], side: str, ztab, zturn) -> int:
    h = 0
    for i, p in enumerate(board):
        if p is not None:
            h ^= ztab[p][i]
    if side == "w":
        h ^= zturn
    return h

# -----------------------------
# Attack detection
# -----------------------------
def is_attacked(board: List[Optional[str]], sq: int, by: str) -> bool:
    # Pawn attacks
    if by == "w":
        # white pawns attack up: from (sq-7, sq-9) to sq
        for d in (-7, -9):
            s = sq - d  # reverse
        # easier forward: attackers are at sq-7 and sq-9
        for d in (-7, -9):
            a = sq + d
            if in_bounds(a):
                # file constraint
                if abs((a % 8) - (sq % 8)) == 1:
                    p = board[a]
                    if p == "wP":
                        return True
    else:
        for d in (7, 9):
            a = sq + d
            if in_bounds(a):
                if abs((a % 8) - (sq % 8)) == 1:
                    p = board[a]
                    if p == "bP":
                        return True

    # Knight attacks
    for d in KNIGHT_OFFSETS:
        a = sq + d
        if not in_bounds(a):
            continue
        # prevent wrap: knight moves change file by 1 or 2
        df = abs((a % 8) - (sq % 8))
        dr = abs((a // 8) - (sq // 8))
        if (df, dr) not in ((1, 2), (2, 1)):
            continue
        p = board[a]
        if p is not None and p[0] == by and p[1] == "N":
            return True

    # King attacks
    for d in KING_OFFSETS:
        a = sq + d
        if not in_bounds(a):
            continue
        df = abs((a % 8) - (sq % 8))
        dr = abs((a // 8) - (sq // 8))
        if max(df, dr) != 1:
            continue
        p = board[a]
        if p is not None and p[0] == by and p[1] == "K":
            return True

    # Sliding pieces
    # Bishops/Queens diagonals
    for d in BISHOP_DIRS:
        a = sq + d
        while in_bounds(a):
            # diagonal step must change file by 1 each rank step; detect wrap
            if abs((a % 8) - ((a - d) % 8)) != 1:
                break
            p = board[a]
            if p is not None:
                if p[0] == by and (p[1] == "B" or p[1] == "Q"):
                    return True
                break
            a += d

    # Rooks/Queens orthogonals
    for d in ROOK_DIRS:
        a = sq + d
        while in_bounds(a):
            if d in (-1, 1) and not same_row(a, a - d):
                break
            p = board[a]
            if p is not None:
                if p[0] == by and (p[1] == "R" or p[1] == "Q"):
                    return True
                break
            a += d

    return False

def find_king(board: List[Optional[str]], side: str) -> int:
    target = side + "K"
    for i, p in enumerate(board):
        if p == target:
            return i
    return -1

# -----------------------------
# Move encoding/decoding
# -----------------------------
def parse_uci(move: str) -> Tuple[int, int, Optional[str]]:
    f = sq_to_idx(move[0:2])
    t = sq_to_idx(move[2:4])
    promo = move[4] if len(move) == 5 else None
    return f, t, promo

def to_uci(fr: int, to: int, promo: Optional[str] = None) -> str:
    s = idx_to_sq(fr) + idx_to_sq(to)
    if promo:
        s += promo
    return s

def is_capture(board: List[Optional[str]], fr: int, to: int) -> bool:
    return board[to] is not None

# -----------------------------
# Make / unmake
# -----------------------------
class Undo:
    __slots__ = ("fr", "to", "moved", "captured", "promo_old", "rook_from", "rook_to", "rook_piece")
    def __init__(self, fr, to, moved, captured, promo_old=None, rook_from=None, rook_to=None, rook_piece=None):
        self.fr = fr
        self.to = to
        self.moved = moved
        self.captured = captured
        self.promo_old = promo_old
        self.rook_from = rook_from
        self.rook_to = rook_to
        self.rook_piece = rook_piece

def make_move(board: List[Optional[str]], fr: int, to: int, promo: Optional[str]) -> Undo:
    moved = board[fr]
    captured = board[to]
    rook_from = rook_to = rook_piece = None
    promo_old = None

    # Castling: king moves two squares
    if moved is not None and moved[1] == "K" and abs((to % 8) - (fr % 8)) == 2 and same_row(fr, to):
        if to % 8 == 6:  # king side
            rook_from = fr + 3
            rook_to = fr + 1
        else:  # queen side
            rook_from = fr - 4
            rook_to = fr - 1
        rook_piece = board[rook_from]
        board[rook_to] = rook_piece
        board[rook_from] = None

    board[to] = moved
    board[fr] = None

    # Promotion
    if promo is not None and moved is not None and moved[1] == "P":
        promo_old = board[to]
        color = moved[0]
        board[to] = color + promo.upper()

    return Undo(fr, to, moved, captured, promo_old=promo_old,
                rook_from=rook_from, rook_to=rook_to, rook_piece=rook_piece)

def unmake_move(board: List[Optional[str]], u: Undo):
    # Undo promotion
    if u.promo_old is not None:
        board[u.to] = u.promo_old

    # Undo main move
    board[u.fr] = u.moved
    board[u.to] = u.captured

    # Undo castling rook move
    if u.rook_from is not None:
        board[u.rook_from] = u.rook_piece
        board[u.rook_to] = None

# -----------------------------
# Move generation (pseudo + legal filter)
# -----------------------------
def gen_pseudo_moves(board: List[Optional[str]], side: str) -> List[Tuple[int, int, Optional[str]]]:
    moves = []
    forward = 8 if side == "w" else -8
    start_rank = 1 if side == "w" else 6   # 0-based rank index
    promo_rank = 7 if side == "w" else 0

    for i, p in enumerate(board):
        if p is None or p[0] != side:
            continue
        pt = p[1]

        if pt == "P":
            r = i // 8
            # forward move
            one = i + forward
            if in_bounds(one) and board[one] is None:
                if (one // 8) == promo_rank:
                    for pr in ("q", "r", "b", "n"):
                        moves.append((i, one, pr))
                else:
                    moves.append((i, one, None))
                # double move
                two = i + 2 * forward
                if r == start_rank and in_bounds(two) and board[two] is None:
                    moves.append((i, two, None))
            # captures
            for dc in (-1, 1):
                cap = i + forward + dc
                if not in_bounds(cap):
                    continue
                if abs((cap % 8) - (i % 8)) != 1:
                    continue
                target = board[cap]
                if target is not None and target[0] == opp(side):
                    if (cap // 8) == promo_rank:
                        for pr in ("q", "r", "b", "n"):
                            moves.append((i, cap, pr))
                    else:
                        moves.append((i, cap, None))

        elif pt == "N":
            for d in KNIGHT_OFFSETS:
                to = i + d
                if not in_bounds(to):
                    continue
                df = abs((to % 8) - (i % 8))
                dr = abs((to // 8) - (i // 8))
                if (df, dr) not in ((1, 2), (2, 1)):
                    continue
                t = board[to]
                if t is None or t[0] != side:
                    moves.append((i, to, None))

        elif pt in ("B", "R", "Q"):
            dirs = BISHOP_DIRS if pt == "B" else ROOK_DIRS if pt == "R" else QUEEN_DIRS
            for d in dirs:
                to = i + d
                while in_bounds(to):
                    # prevent wrap on horizontal and diagonal
                    if d in (-1, 1) and not same_row(to, to - d):
                        break
                    if d in (-9, -7, 7, 9) and abs((to % 8) - ((to - d) % 8)) != 1:
                        break
                    t = board[to]
                    if t is None:
                        moves.append((i, to, None))
                    else:
                        if t[0] != side:
                            moves.append((i, to, None))
                        break
                    to += d

        elif pt == "K":
            for d in KING_OFFSETS:
                to = i + d
                if not in_bounds(to):
                    continue
                df = abs((to % 8) - (i % 8))
                dr = abs((to // 8) - (i // 8))
                if max(df, dr) != 1:
                    continue
                t = board[to]
                if t is None or t[0] != side:
                    moves.append((i, to, None))

            # Castling (best-effort, rights unknown)
            # Only consider if king on starting square and rook present and path empty.
            if side == "w" and i == sq_to_idx("e1"):
                # King-side: e1g1 with rook h1
                if board[sq_to_idx("h1")] == "wR" and board[sq_to_idx("f1")] is None and board[sq_to_idx("g1")] is None:
                    moves.append((i, sq_to_idx("g1"), None))
                # Queen-side: e1c1 with rook a1
                if board[sq_to_idx("a1")] == "wR" and board[sq_to_idx("d1")] is None and board[sq_to_idx("c1")] is None and board[sq_to_idx("b1")] is None:
                    moves.append((i, sq_to_idx("c1"), None))
            elif side == "b" and i == sq_to_idx("e8"):
                if board[sq_to_idx("h8")] == "bR" and board[sq_to_idx("f8")] is None and board[sq_to_idx("g8")] is None:
                    moves.append((i, sq_to_idx("g8"), None))
                if board[sq_to_idx("a8")] == "bR" and board[sq_to_idx("d8")] is None and board[sq_to_idx("c8")] is None and board[sq_to_idx("b8")] is None:
                    moves.append((i, sq_to_idx("c8"), None))

    return moves

def gen_legal_moves(board: List[Optional[str]], side: str) -> List[Tuple[int, int, Optional[str]]]:
    pseudo = gen_pseudo_moves(board, side)
    legal = []
    ksq = find_king(board, side)
    for fr, to, promo in pseudo:
        u = make_move(board, fr, to, promo)
        # Update king square if moved
        nk = to if (u.moved is not None and u.moved[1] == "K") else ksq
        ok = (nk != -1 and not is_attacked(board, nk, opp(side)))
        unmake_move(board, u)
        if ok:
            # Additional castling legality: king cannot castle out of/through check
            if u.moved is not None and u.moved[1] == "K" and abs((to % 8) - (fr % 8)) == 2 and same_row(fr, to):
                # squares king passes through
                step = 1 if (to % 8) > (fr % 8) else -1
                mid = fr + step
                # must not be in check at start, mid, end
                if ksq == -1:
                    continue
                if is_attacked(board, ksq, opp(side)):
                    continue
                # simulate passing square attack on original board (no need to move rook)
                u2 = make_move(board, fr, mid, None)
                mid_ok = not is_attacked(board, mid, opp(side))
                unmake_move(board, u2)
                if not mid_ok:
                    continue
                # end square already checked by ok
            legal.append((fr, to, promo))
    return legal

# -----------------------------
# Evaluation
# -----------------------------
def evaluate(board: List[Optional[str]], side: str) -> int:
    # Positive means good for 'side'
    score = 0
    material = 0
    for i, p in enumerate(board):
        if p is None:
            continue
        c = p[0]
        t = p[1]
        val = PIECE_VALUES[t]
        material += val
        pst = PST[t][i] if c == "w" else PST[t][mirror_idx(i)]
        s = val + pst
        if c == side:
            score += s
        else:
            score -= s

    # Small mobility bonus
    # (cheap: count pseudo moves; avoid heavy legal calc)
    my_mob = len(gen_pseudo_moves(board, side))
    op_mob = len(gen_pseudo_moves(board, opp(side)))
    score += 2 * (my_mob - op_mob)

    # King safety: discourage king in center in middlegame
    # Use material to infer phase: more material => stronger king shelter needed
    phase = min(1.0, material / 8000.0)
    k_my = find_king(board, side)
    k_op = find_king(board, opp(side))
    if k_my != -1:
        kmf = k_my % 8
        kmr = k_my // 8
        dist_center = abs(kmf - 3.5) + abs(kmr - 3.5)
        score += int(-8 * phase * (4.0 - min(4.0, dist_center)))
    if k_op != -1:
        kof = k_op % 8
        kor = k_op // 8
        dist_center = abs(kof - 3.5) + abs(kor - 3.5)
        score += int(8 * phase * (4.0 - min(4.0, dist_center)))

    return score

# -----------------------------
# Search
# -----------------------------
def mvv_lva(board: List[Optional[str]], fr: int, to: int) -> int:
    cap = board[to]
    mover = board[fr]
    if cap is None or mover is None:
        return 0
    return 10 * PIECE_VALUES[cap[1]] - PIECE_VALUES[mover[1]]

def gives_check(board: List[Optional[str]], side: str, fr: int, to: int, promo: Optional[str]) -> bool:
    u = make_move(board, fr, to, promo)
    oking = find_king(board, opp(side))
    chk = (oking != -1 and is_attacked(board, oking, side))
    unmake_move(board, u)
    return chk

def order_moves(board: List[Optional[str]], side: str, moves: List[Tuple[int, int, Optional[str]]]) -> List[Tuple[int, int, Optional[str]]]:
    scored = []
    for fr, to, promo in moves:
        s = 0
        # promotions first
        if promo is not None:
            s += 9000 + ("qrbn".index(promo) * -10)
        # captures
        if board[to] is not None:
            s += 5000 + mvv_lva(board, fr, to)
        # checks
        # (cheap but do it; helps tactics)
        if gives_check(board, side, fr, to, promo):
            s += 2000
        scored.append((s, fr, to, promo))
    scored.sort(reverse=True, key=lambda x: x[0])
    return [(fr, to, promo) for s, fr, to, promo in scored]

def quiescence(board: List[Optional[str]], side: str, alpha: int, beta: int, start: float, time_limit: float) -> int:
    if time.time() - start > time_limit:
        return evaluate(board, side)

    stand = evaluate(board, side)
    if stand >= beta:
        return beta
    if alpha < stand:
        alpha = stand

    # Only consider captures (and promotions)
    moves = gen_pseudo_moves(board, side)
    caps = []
    for fr, to, promo in moves:
        if promo is not None or board[to] is not None:
            caps.append((fr, to, promo))

    # Filter legality quickly
    legal_caps = []
    ksq = find_king(board, side)
    for fr, to, promo in caps:
        u = make_move(board, fr, to, promo)
        nk = to if (u.moved is not None and u.moved[1] == "K") else ksq
        ok = (nk != -1 and not is_attacked(board, nk, opp(side)))
        unmake_move(board, u)
        if ok:
            legal_caps.append((fr, to, promo))

    legal_caps = order_moves(board, side, legal_caps)
    for fr, to, promo in legal_caps:
        if time.time() - start > time_limit:
            break
        u = make_move(board, fr, to, promo)
        score = -quiescence(board, opp(side), -beta, -alpha, start, time_limit)
        unmake_move(board, u)
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
    return alpha

def negamax(board: List[Optional[str]], side: str, depth: int, alpha: int, beta: int,
            start: float, time_limit: float, tt: Dict[int, Tuple[int, int, int]], ztab, zturn) -> int:
    if time.time() - start > time_limit:
        return evaluate(board, side)

    h = compute_hash(board, side, ztab, zturn)
    entry = tt.get(h)
    if entry is not None:
        # entry: (stored_depth, flag, value), where flag: 0 exact, -1 upper, 1 lower
        sd, flag, val = entry
        if sd >= depth:
            if flag == 0:
                return val
            elif flag == 1 and val > alpha:
                alpha = val
            elif flag == -1 and val < beta:
                beta = val
            if alpha >= beta:
                return val

    if depth <= 0:
        return quiescence(board, side, alpha, beta, start, time_limit)

    legal = gen_legal_moves(board, side)
    if not legal:
        ksq = find_king(board, side)
        if ksq != -1 and is_attacked(board, ksq, opp(side)):
            return -MATE_SCORE + 1  # checkmated
        return 0  # stalemate

    legal = order_moves(board, side, legal)

    best = -INF
    a0 = alpha
    for fr, to, promo in legal:
        if time.time() - start > time_limit:
            break
        u = make_move(board, fr, to, promo)
        score = -negamax(board, opp(side), depth - 1, -beta, -alpha, start, time_limit, tt, ztab, zturn)
        unmake_move(board, u)
        if score > best:
            best = score
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    # Store TT
    flag = 0
    if best <= a0:
        flag = -1
    elif best >= beta:
        flag = 1
    tt[h] = (depth, flag, best)
    return best

# -----------------------------
# Root move selection
# -----------------------------
def extract_legal_moves_from_memory(memory: dict) -> Optional[List[str]]:
    # Common keys
    for k in ("legal_moves", "moves", "actions", "valid_moves", "valid_actions"):
        v = memory.get(k)
        if isinstance(v, list) and (not v or isinstance(v[0], str)):
            # quick validation of format
            if all(isinstance(x, str) and UCI_RE.match(x) for x in v):
                return v

    # Otherwise scan any list value that looks like UCI moves
    for v in memory.values():
        if isinstance(v, list) and v and all(isinstance(x, str) for x in v):
            if all(UCI_RE.match(x) for x in v):
                return v
    return None

def board_from_pieces(pieces: Dict[str, str]) -> List[Optional[str]]:
    board = [None] * 64
    for sq, pc in pieces.items():
        # pc like 'wK'
        board[sq_to_idx(sq)] = pc
    return board

def apply_uci(board: List[Optional[str]], move: str) -> Undo:
    fr, to, promo = parse_uci(move)
    return make_move(board, fr, to, promo)

def is_mate_in_one(board: List[Optional[str]], side: str, move: str) -> bool:
    fr, to, promo = parse_uci(move)
    u = make_move(board, fr, to, promo)
    oside = opp(side)
    omoves = gen_legal_moves(board, oside)
    oking = find_king(board, oside)
    in_check = (oking != -1 and is_attacked(board, oking, side))
    unmake_move(board, u)
    return in_check and (len(omoves) == 0)

def policy(pieces: Dict[str, str], to_play: str, memory: dict) -> Tuple[str, dict]:
    # Initialize persistent structures
    if memory is None:
        memory = {}
    if "ztab" not in memory or "zturn" not in memory:
        ztab, zturn = init_zobrist(1337)
        memory["ztab"] = ztab
        memory["zturn"] = zturn
    else:
        ztab, zturn = memory["ztab"], memory["zturn"]

    tt = memory.get("tt")
    if not isinstance(tt, dict):
        tt = {}
    # Keep TT bounded
    if len(tt) > 60000:
        tt.clear()

    board = board_from_pieces(pieces)
    side = color_to_char(to_play)

    provided = extract_legal_moves_from_memory(memory)
    if provided is None:
        # Fall back: generate our own (best-effort).
        root_moves = [to_uci(fr, to, promo) for fr, to, promo in gen_legal_moves(board, side)]
        if not root_moves:
            # As ultimate fallback, return any pseudo move (or dummy if none)
            pseudo = gen_pseudo_moves(board, side)
            if pseudo:
                fr, to, promo = pseudo[0]
                return to_uci(fr, to, promo), memory
            # No moves at all: return a syntactically valid but harmless move (shouldn't happen in real games)
            return "a1a1", memory
    else:
        root_moves = provided[:]  # must return one of these

    # If only one legal move, play it.
    if len(root_moves) == 1:
        memory["tt"] = tt
        return root_moves[0], memory

    # Mate in 1 check (fast)
    for mv in root_moves:
        if is_mate_in_one(board, side, mv):
            memory["tt"] = tt
            return mv, memory

    start = time.time()
    # Time budget: keep margin for overhead
    time_limit = 0.92

    # Iterative deepening
    best_move = root_moves[0]
    best_score = -INF

    # Basic move ordering at root using captures/promotions/checks heuristics
    root_trip = []
    for mv in root_moves:
        fr, to, promo = parse_uci(mv)
        s = 0
        if promo is not None:
            s += 9000
        if board[to] is not None:
            s += 5000 + mvv_lva(board, fr, to)
        if gives_check(board, side, fr, to, promo):
            s += 2000
        root_trip.append((s, mv))
    root_trip.sort(reverse=True, key=lambda x: x[0])
    ordered_root = [mv for _, mv in root_trip]

    max_depth = 5
    for depth in range(1, max_depth + 1):
        if time.time() - start > time_limit:
            break
        local_best_move = best_move
        local_best_score = -INF
        alpha = -INF
        beta = INF

        for mv in ordered_root:
            if time.time() - start > time_limit:
                break
            fr, to, promo = parse_uci(mv)
            u = make_move(board, fr, to, promo)
            score = -negamax(board, opp(side), depth - 1, -beta, -alpha, start, time_limit, tt, ztab, zturn)
            unmake_move(board, u)

            if score > local_best_score:
                local_best_score = score
                local_best_move = mv
            if score > alpha:
                alpha = score

        # If we completed this depth, accept it
        if time.time() - start <= time_limit:
            best_move = local_best_move
            best_score = local_best_score

        # Early exit if we found a forced mate line
        if best_score >= MATE_SCORE - 1000:
            break

    memory["tt"] = tt
    return best_move, memory
