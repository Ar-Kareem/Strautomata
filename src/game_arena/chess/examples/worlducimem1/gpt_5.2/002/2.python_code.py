
import time
from typing import Dict, Tuple, List, Optional

# ===========
# Board model
# ===========

# Square mapping: 0 = a1, 7 = h1, 56 = a8, 63 = h8
FILES = "abcdefgh"
RANKS = "12345678"

def sq_to_i(sq: str) -> int:
    return (ord(sq[0]) - 97) + 8 * (ord(sq[1]) - 49)

def i_to_sq(i: int) -> str:
    return chr(97 + (i & 7)) + chr(49 + (i >> 3))

# Piece encoding
# Positive = White, Negative = Black
PIECE_MAP = {
    "P": 1,
    "N": 2,
    "B": 3,
    "R": 4,
    "Q": 5,
    "K": 6,
}
INV_PIECE_MAP = {v: k for k, v in PIECE_MAP.items()}

def code_to_int(code: str) -> int:
    # code like "wP" or "bK"
    color = code[0]
    pt = code[1]
    val = PIECE_MAP[pt]
    return val if color == "w" else -val

def int_to_code(p: int) -> str:
    if p == 0:
        return ""
    return ("w" if p > 0 else "b") + INV_PIECE_MAP[abs(p)]

def color_of(p: int) -> int:
    # 1 for white, -1 for black, 0 for empty
    return 1 if p > 0 else (-1 if p < 0 else 0)

# Move encoding (int):
# bits: from(6) to(6) promo(3) flags(5)
# promo: 0 none, 1 N, 2 B, 3 R, 4 Q
# flags: bit0 capture, bit1 ep_capture, bit2 pawn_double, bit3 castle_k, bit4 castle_q
CAPTURE = 1 << 0
EP_CAP = 1 << 1
PAWN_DBL = 1 << 2
CASTLE_K = 1 << 3
CASTLE_Q = 1 << 4

def pack_move(fr: int, to: int, promo: int = 0, flags: int = 0) -> int:
    return (fr & 63) | ((to & 63) << 6) | ((promo & 7) << 12) | ((flags & 31) << 15)

def mv_from(m: int) -> int:
    return m & 63

def mv_to(m: int) -> int:
    return (m >> 6) & 63

def mv_promo(m: int) -> int:
    return (m >> 12) & 7

def mv_flags(m: int) -> int:
    return (m >> 15) & 31

def uci_of_move(m: int) -> str:
    fr = i_to_sq(mv_from(m))
    to = i_to_sq(mv_to(m))
    pr = mv_promo(m)
    if pr:
        # 1 N,2 B,3 R,4 Q -> 'n','b','r','q'
        ch = {1: "n", 2: "b", 3: "r", 4: "q"}[pr]
        return fr + to + ch
    return fr + to

def promo_from_char(ch: str) -> int:
    return {"n": 1, "b": 2, "r": 3, "q": 4}.get(ch, 0)

# ===========
# PST tables
# ===========

# Simple PSTs oriented for White; for Black we mirror ranks.
# Values in centipawns.
PST_P = [
      0,   0,   0,   0,   0,   0,   0,   0,
     50,  55,  55,  50,  50,  55,  55,  50,
     10,  12,  15,  25,  25,  15,  12,  10,
      6,   8,  10,  18,  18,  10,   8,   6,
      2,   4,   6,  14,  14,   6,   4,   2,
      0,   2,   2,   8,   8,   2,   2,   0,
      0,   0,   0, -10, -10,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,   0,
]
PST_N = [
    -50, -40, -30, -25, -25, -30, -40, -50,
    -35, -15,  -5,   0,   0,  -5, -15, -35,
    -25,  -5,  10,  15,  15,  10,  -5, -25,
    -20,   0,  15,  20,  20,  15,   0, -20,
    -20,   0,  15,  20,  20,  15,   0, -20,
    -25,  -5,  10,  15,  15,  10,  -5, -25,
    -35, -15,  -5,   0,   0,  -5, -15, -35,
    -50, -40, -30, -25, -25, -30, -40, -50,
]
PST_B = [
    -20, -10, -10, -10, -10, -10, -10, -20,
    -10,   0,   5,   0,   0,   5,   0, -10,
    -10,   5,  10,  10,  10,  10,   5, -10,
    -10,   0,  10,  15,  15,  10,   0, -10,
    -10,   0,  10,  15,  15,  10,   0, -10,
    -10,   5,  10,  10,  10,  10,   5, -10,
    -10,   0,   5,   0,   0,   5,   0, -10,
    -20, -10, -10, -10, -10, -10, -10, -20,
]
PST_R = [
     -5,  -2,   0,   2,   2,   0,  -2,  -5,
      0,   5,   8,  10,  10,   8,   5,   0,
     -5,   0,   0,   0,   0,   0,   0,  -5,
     -5,   0,   0,   0,   0,   0,   0,  -5,
     -5,   0,   0,   0,   0,   0,   0,  -5,
     -5,   0,   0,   0,   0,   0,   0,  -5,
     -5,   0,   0,   0,   0,   0,   0,  -5,
     -5,  -2,   0,   2,   2,   0,  -2,  -5,
]
PST_Q = [
    -20, -10, -10,  -5,  -5, -10, -10, -20,
    -10,   0,   0,   0,   0,   0,   0, -10,
    -10,   0,   5,   5,   5,   5,   0, -10,
     -5,   0,   5,   8,   8,   5,   0,  -5,
     -5,   0,   5,   8,   8,   5,   0,  -5,
    -10,   0,   5,   5,   5,   5,   0, -10,
    -10,   0,   0,   0,   0,   0,   0, -10,
    -20, -10, -10,  -5,  -5, -10, -10, -20,
]
PST_K = [
     20,  30,  10,   0,   0,  10,  30,  20,
     20,  20,   0,   0,   0,   0,  20,  20,
    -10, -20, -20, -20, -20, -20, -20, -10,
    -20, -30, -30, -40, -40, -30, -30, -20,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
]

PST = {
    1: PST_P,
    2: PST_N,
    3: PST_B,
    4: PST_R,
    5: PST_Q,
    6: PST_K,
}

PIECE_VALUE = {1: 100, 2: 320, 3: 330, 4: 500, 5: 900, 6: 0}

def mirror64(i: int) -> int:
    # mirror ranks for black perspective: a1 <-> None: int) -> bool:
    return 0 <= i < 64

def file_of(i: int) -> int:
    return i & 7

def rank_of(i: int) -> int:
    return i >> 3

def step_ok(fr: int, to: int, delta: int) -> bool:
    # Prevent wrap-around for horizontal/diagonal by checking file continuity.
    ff = file_of(fr)
    tf = file_of(to)
    df = abs(tf - ff)
    if delta in (-1, 1):
        return df == 1
    if delta in (-9, 9, -7, 7):
        return df == 1
    if delta in (-17, 15, -10, 6, 10, -6, 17, -15):
        # Knight: must move 1/2 files
        return df in (1, 2)
    return True

def find_king(board: List[int], side: int) -> int:
    target = 6 * side
    for i, p in enumerate(board):
        if p == target:
            return i
    return -1

def is_attacked(board: List[int], sq: int, by_side: int, ep_sq: int = -1) -> bool:
    # by_side: 1 white attacks, -1 black attacks
    # Pawn attacks
    r = rank_of(sq)
    f = file_of(sq)
    if by_side == 1:
        # white pawns attack from below: (sq-7, sq-9) are pawn positions
        for d in (-7, -9):
            p = sq - d  # invert: pawn at sq - d attacks sq if it can move by d to reach
        # Actually simpler: attacker squares for white pawns are sq-7 and sq-9 (pawns on those squares attack sq)
        for attacker in (sq - 7, sq - 9):
            if on_board(attacker) and abs(file_of(attacker) - f) == 1 and board[attacker] == 1:
                return True
    else:
        for attacker in (sq + 7, sq + 9):
            if on_board(attacker) and abs(file_of(attacker) - f) == 1 and board[attacker] == -1:
                return True

    # Knights
    for d in KNIGHT_DELTAS:
        a = sq + d
        if on_board(a) and step_ok(sq, a, d):
            if board[a] == 2 * by_side:
                return True

    # King
    for d in KING_DELTAS:
        a = sq + d
        if on_board(a) and step_ok(sq, a, d):
            if board[a] == 6 * by_side:
                return True

    # Sliders: bishops/queens (diagonal)
    for d in BISHOP_DIRS:
        a = sq + d
        while on_board(a) and step_ok(a - d, a, d):
            p = board[a]
            if p != 0:
                if p == 3 * by_side or p == 5 * by_side:
                    return True
                break
            a += d

    # Sliders: rooks/queens (orthogonal)
    for d in ROOK_DIRS:
        a = sq + d
        while on_board(a) and step_ok(a - d, a, d):
            p = board[a]
            if p != 0:
                if p == 4 * by_side or p == 5 * by_side:
                    return True
                break
            a += d

    return False

def gen_pseudo_moves(board: List[int], side: int, castling: int, ep_sq: int) -> List[int]:
    # castling bitmask: 1=WK,2=WQ,4=BK,8=BQ
    moves: List[int] = []
    us = side
    them = -side

    for fr, p in enumerate(board):
        if p == 0 or color_of(p) != us:
            continue
        pt = abs(p)

        if pt == 1:  # pawn
            f = file_of(fr)
            r = rank_of(fr)
            forward = 8 * us  # white +8, black -8
            one = fr + forward
            promo_rank = 7 if us == 1 else 0
            start_rank = 1 if us == 1 else 6

            # single push
            if on_board(one) and board[one] == 0:
                if rank_of(one) == promo_rank:
                    for pr in (4, 3, 2, 1):  # prefer Q,R,B,N
                        moves.append(pack_move(fr, one, pr, 0))
                else:
                    moves.append(pack_move(fr, one, 0, 0))
                    # double push
                    two = one + forward
                    if r == start_rank and on_board(two) and board[two] == 0:
                        moves.append(pack_move(fr, two, 0, PAWN_DBL))

            # captures
            for df in (-1, 1):
                if not (0 <= f + df <= 7):
                    continue
                to = fr + forward + df
                if not on_board(to) or abs(file_of(to) - f) != 1:
                    continue
                if board[to] != 0 and color_of(board[to]) == them:
                    if rank_of(to) == promo_rank:
                        for pr in (4, 3, 2, 1):
                            moves.append(pack_move(fr, to, pr, CAPTURE))
                    else:
                        moves.append(pack_move(fr, to, 0, CAPTURE))

            # en passant
            if ep_sq != -1:
                # If ep_sq is on diagonal forward squares
                for df in (-1, 1):
                    if not (0 <= f + df <= 7):
                        continue
                    to = fr + forward + df
                    if to == ep_sq:
                        moves.append(pack_move(fr, to, 0, EP_CAP | CAPTURE))

        elif pt == 2:  # knight
            for d in KNIGHT_DELTAS:
                to = fr + d
                if not on_board(to) or not step_ok(fr, to, d):
                    continue
                tp = board[to]
                if tp == 0:
                    moves.append(pack_move(fr, to, 0, 0))
                elif color_of(tp) == them:
                    moves.append(pack_move(fr, to, 0, CAPTURE))

        elif pt == 3:  # bishop
            for d in BISHOP_DIRS:
                to = fr + d
                while on_board(to) and step_ok(to - d, to, d):
                    tp = board[to]
                    if tp == 0:
                        moves.append(pack_move(fr, to, 0, 0))
                    else:
                        if color_of(tp) == them:
                            moves.append(pack_move(fr, to, 0, CAPTURE))
                        break
                    to += d

        elif pt == 4:  # rook
            for d in ROOK_DIRS:
                to = fr + d
                while on_board(to) and step_ok(to - d, to, d):
                    tp = board[to]
                    if tp == 0:
                        moves.append(pack_move(fr, to, 0, 0))
                    else:
                        if color_of(tp) == them:
                            moves.append(pack_move(fr, to, 0, CAPTURE))
                        break
                    to += d

        elif pt == 5:  # queen
            for d in QUEEN_DIRS:
                to = fr + d
                while on_board(to) and step_ok(to - d, to, d):
                    tp = board[to]
                    if tp == 0:
                        moves.append(pack_move(fr, to, 0, 0))
                    else:
                        if color_of(tp) == them:
                            moves.append(pack_move(fr, to, 0, CAPTURE))
                        break
                    to += d

        elif pt == 6:  # king
            for d in KING_DELTAS:
                to = fr + d
                if not on_board(to) or not step_ok(fr, to, d):
                    continue
                tp = board[to]
                if tp == 0:
                    moves.append(pack_move(fr, to, 0, 0))
                elif color_of(tp) == them:
                    moves.append(pack_move(fr, to, 0, CAPTURE))

            # Castling (only if rights indicate and basic emptiness; legality checked later)
            if us == 1 and fr == sq_to_i("e1"):
                if castling & 1:  # WK
                    if board[sq_to_i("f1")] == 0 and board[sq_to_i("g1")] == 0 and board[sq_to_i("h1")] == 4:
                        moves.append(pack_move(fr, sq_to_i("g1"), 0, CASTLE_K))
                if castling & 2:  # WQ
                    if board[sq_to_i("d1")] == 0 and board[sq_to_i("c1")] == 0 and board[sq_to_i("b1")] == 0 and board[sq_to_i("a1")] == 4:
                        moves.append(pack_move(fr, sq_to_i("c1"), 0, CASTLE_Q))
            elif us == -1 and fr == sq_to_i("e8"):
                if castling & 4:  # BK
                    if board[sq_to_i("f8")] == 0 and board[sq_to_i("g8")] == 0 and board[sq_to_i("h8")] == -4:
                        moves.append(pack_move(fr, sq_to_i("g8"), 0, CASTLE_K))
                if castling & 8:  # BQ
                    if board[sq_to_i("d8")] == 0 and board[sq_to_i("c8")] == 0 and board[sq_to_i("b8")] == 0 and board[sq_to_i("a8")] == -4:
                        moves.append(pack_move(fr, sq_to_i("c8"), 0, CASTLE_Q))

    return moves

def apply_move(board: List[int], side: int, castling: int, ep_sq: int, m: int) -> Tuple[List[int], int, int]:
    # returns (new_board, new_castling, new_ep)
    fr = mv_from(m)
    to = mv_to(m)
    promo = mv_promo(m)
    flags = mv_flags(m)

    b = board[:]  # copy
    piece = b[fr]
    b[fr] = 0

    new_castling = castling
    new_ep = -1

    # Update castling rights due to moving pieces or capturing rooks
    # If king moves: lose both for that side
    if abs(piece) == 6:
        if side == 1:
            new_castling &= ~3
        else:
            new_castling &= ~12
    # If rook moves from original squares: lose corresponding
    if abs(piece) == 4:
        if fr == sq_to_i("h1"):
            new_castling &= ~1
        elif fr == sq_to_i("a1"):
            new_castling &= ~2
        elif fr == sq_to_i("h8"):
            new_castling &= ~4
        elif fr == sq_to_i("a8"):
            new_castling &= ~8

    # Handle captures affecting opponent castling rights
    captured = b[to]
    if captured != 0 and abs(captured) == 4:
        if to == sq_to_i("h1"):
            new_castling &= ~1
        elif to == sq_to_i("a1"):
            new_castling &= ~2
        elif to == sq_to_i("h8"):
            new_castling &= ~4
        elif to == sq_to_i("a8"):
            new_castling &= ~8

    # En passant capture
    if flags & EP_CAP:
        # Captured pawn is behind destination
        cap_sq = to - 8 * side
        b[cap_sq] = 0

    # Castling: move rook too
    if flags & CASTLE_K:
        # king to g-file, rook to f-file
        if side == 1:
            b[sq_to_i("h1")] = 0
            b[sq_to_i("f1")] = 4
        else:
            b[sq_to_i("h8")] = 0
            b[sq_to_i("f8")] = -4
    elif flags & CASTLE_Q:
        if side == 1:
            b[sq_to_i("a1")] = 0
            b[sq_to_i("d1")] = 4
        else:
            b[sq_to_i("a8")] = 0
            b[sq_to_i("d8")] = -4

    # Pawn double sets ep square
    if flags & PAWN_DBL:
        new_ep = (fr + to) // 2

    # Promotion
    if promo and abs(piece) == 1:
        # promo 1=N,2=B,3=R,4=Q
        promoted = {1: 2, 2: 3, 3: 4, 4: 5}[promo] * side
        b[to] = promoted
    else:
        b[to] = piece

    return b, new_castling, new_ep

def legal_moves(board: List[int], side: int, castling: int, ep_sq: int) -> List[int]:
    ps = gen_pseudo_moves(board, side, castling, ep_sq)
    leg: List[int] = []
    king_sq = find_king(board, side)
    in_check = is_attacked(board, king_sq, -side, ep_sq)
    for m in ps:
        flags = mv_flags(m)
        # For castling, need extra checks: not in check, squares passed through not attacked.
        if flags & (CASTLE_K | CASTLE_Q):
            if in_check:
                continue
            if side == 1:
                if flags & CASTLE_K:
                    if is_attacked(board, sq_to_i("f1"), -side, ep_sq) or is_attacked(board, sq_to_i("g1"), -side, ep_sq):
                        continue
                else:
                    if is_attacked(board, sq_to_i("d1"), -side, ep_sq) or is_attacked(board, sq_to_i("c1"), -side, ep_sq):
                        continue
            else:
                if flags & CASTLE_K:
                    if is_attacked(board, sq_to_i("f8"), -side, ep_sq) or is_attacked(board, sq_to_i("g8"), -side, ep_sq):
                        continue
                else:
                    if is_attacked(board, sq_to_i("d8"), -side, ep_sq) or is_attacked(board, sq_to_i("c8"), -side, ep_sq):
                        continue

        nb, nc, nep = apply_move(board, side, castling, ep_sq, m)
        nking = king_sq
        if abs(board[mv_from(m)]) == 6:
            nking = mv_to(m)
        if not is_attacked(nb, nking, -side, nep):
            leg.append(m)
    return leg

# ===========
# Evaluation
# ===========

def eval_board(board: List[int], side: int) -> int:
    # Score from perspective of 'side' to move (positive good for side)
    score = 0
    w_mob = 0
    b_mob = 0

    # Material + PST
    for i, p in enumerate(board):
        if p == 0:
            continue
        sgn = 1 if p > 0 else -1
        pt = abs(p)
        score += sgn * PIECE_VALUE[pt]
        if pt in PST:
            idx = i if sgn == 1 else mirror64(i)
            score += sgn * PST[pt][idx]

    # Mobility (cheap approximation: pseudo move count without legality filtering)
    # Keep small weight.
    # Note: to avoid heavy calls, do simplified: count piece moves directions quickly.
    # We'll use full pseudo generator but no legality for simplicity and correctness of speed.
    w_mob = len(gen_pseudo_moves(board, 1, 0, -1))
    b_mob = len(gen_pseudo_moves(board, -1, 0, -1))
    score += 2 * (w_mob - b_mob)

    # King safety: penalty if king is too central in middlegame (very small)
    wk = find_king(board, 1)
    bk = find_king(board, -1)
    if wk != -1:
        wf = file_of(wk); wr = rank_of(wk)
        score -= (3 - abs(wf - 3.5)) * 2
        score -= (3 - abs(wr - 0.5)) * 2
    if bk != -1:
        bf = file_of(bk); br = rank_of(bk)
        score += (3 - abs(bf - 3.5)) * 2
        score += (3 - abs(br - 7.5)) * 2

    return score if side == 1 else -score

# ===========
# Search
# ===========

MATE_SCORE = 100000
INF = 10**9

def mvv_lva_score(board: List[int], m: int) -> int:
    flags = mv_flags(m)
    to = mv_to(m)
    fr = mv_from(m)
    promo = mv_promo(m)
    score = 0
    if flags & CAPTURE:
        victim = abs(board[to]) if not (flags & EP_CAP) else 1
        attacker = abs(board[fr])
        score += 10_000 + (PIECE_VALUE.get(victim, 0) * 10) - PIECE_VALUE.get(attacker, 0)
    if promo:
        score += 8_000 + {4: 900, 3: 500, 2: 330, 1: 320}.get(promo, 0)
    if flags & (CASTLE_K | CASTLE_Q):
        score += 100
    return score

def negamax(board: List[int], side: int, castling: int, ep_sq: int,
            depth: int, alpha: int, beta: int,
            ply: int, t_end: float,
            tt: Dict[Tuple[bytes, int, int, int], Tuple[int, int]],
            killer: Dict[int, int]) -> int:
    if time.perf_counter() >= t_end:
        raise TimeoutError

    # Transposition key (board bytes + side + castling + ep)
    # board fits in signed bytes; convert to bytes for hashing
    bkey = bytes((p + 6) & 0xFF for p in board)  # offset to keep in 0..255
    key = (bkey, side, castling, ep_sq)
    entry = tt.get(key)
    if entry is not None:
        stored_depth, stored_val = entry
        if stored_depth >= depth:
            return stored_val

    # Generate legal moves
    moves = legal_moves(board, side, castling, ep_sq)
    if not moves:
        ksq = find_king(board, side)
        if ksq != -1 and is_attacked(board, ksq, -side, ep_sq):
            return -MATE_SCORE + ply
        return 0

    if depth <= 0:
        # Quiescence: only captures/promotions (and EP)
        stand = eval_board(board, side)
        if stand >= beta:
            return stand
        if stand > alpha:
            alpha = stand

        caps = [m for m in moves if (mv_flags(m) & CAPTURE) or mv_promo(m)]
        caps.sort(key=lambda m: mvv_lva_score(board, m), reverse=True)
        for m in caps:
            nb, nc, nep = apply_move(board, side, castling, ep_sq, m)
            val = -negamax(nb, -side, nc, nep, 0, -beta, -alpha, ply + 1, t_end, tt, killer)
            if val >= beta:
                return val
            if val > alpha:
                alpha = val
        tt[key] = (depth, alpha)
        return alpha

    # Move ordering: TT/killer first, then MVV-LVA/promo
    km = killer.get(ply)
    if km is not None and km in moves:
        moves.remove(km)
        moves.insert(0, km)
    moves.sort(key=lambda m: mvv_lva_score(board, m), reverse=True)

    best = -INF
    for m in moves:
        nb, nc, nep = apply_move(board, side, castling, ep_sq, m)
        val = -negamax(nb, -side, nc, nep, depth - 1, -beta, -alpha, ply + 1, t_end, tt, killer)
        if val > best:
            best = val
        if val > alpha:
            alpha = val
        if alpha >= beta:
            # store killer for quiet moves
            if not (mv_flags(m) & CAPTURE) and not mv_promo(m):
                killer[ply] = m
            break

    tt[key] = (depth, best)
    return best

def pick_move(board: List[int], side: int, castling: int, ep_sq: int, time_limit: float) -> int:
    t0 = time.perf_counter()
    t_end = t0 + max(0.02, time_limit)
    moves = legal_moves(board, side, castling, ep_sq)
    if not moves:
        return 0

    # Immediate mate finder: if any move gives mate, take it.
    for m in moves:
        nb, nc, nep = apply_move(board, side, castling, ep_sq, m)
        opp_moves = legal_moves(nb, -side, nc, nep)
        if not opp_moves:
            ksq = find_king(nb, -side)
            if ksq != -1 and is_attacked(nb, ksq, side, nep):
                return m

    # Iterative deepening
    best_move = moves[0]
    tt: Dict[Tuple[bytes, int, int, int], Tuple[int, int]] = {}
    killer: Dict[int, int] = {}

    # Initial ordering
    moves.sort(key=lambda m: mvv_lva_score(board, m), reverse=True)

    last_best_val = -INF
    for depth in (1, 2, 3, 4, 5):
        if time.perf_counter() >= t_end:
            break
        alpha, beta = -INF, INF
        cur_best = best_move
        cur_best_val = -INF

        # Reorder with current best first
        if cur_best in moves:
            moves.remove(cur_best)
            moves.insert(0, cur_best)

        for m in moves:
            if time.perf_counter() >= t_end:
                break
            nb, nc, nep = apply_move(board, side, castling, ep_sq, m)
            try:
                val = -negamax(nb, -side, nc, nep, depth - 1, -beta, -alpha, 1, t_end, tt, killer)
            except TimeoutError:
                break

            if val > cur_best_val:
                cur_best_val = val
                cur_best = m
            if val > alpha:
                alpha = val

        # If depth completed, accept result
        if cur_best_val > -INF // 2:
            best_move = cur_best
            last_best_val = cur_best_val

        # If we found forced mate, stop
        if last_best_val > MATE_SCORE // 2:
            break

    return best_move

# ===========
# State inference (opponent move) to keep castling/ep accurate across turns
# ===========

def pieces_to_board(pieces: Dict[str, str]) -> List[int]:
    b = [0] * 64
    for sq, code in pieces.items():
        if not isinstance(sq, str) or len(sq) != 2:
            continue
        if not isinstance(code, str) or len(code) != 2:
            continue
        try:
            i = sq_to_i(sq)
        except Exception:
            continue
        b[i] = code_to_int(code)
    return b

def initial_castling_from_board(board: List[int]) -> int:
    c = 0
    # White
    if board[sq_to_i("e1")] == 6 and board[sq_to_i("h1")] == 4:
        c |= 1
    if board[sq_to_i("e1")] == 6 and board[sq_to_i("a1")] == 4:
        c |= 2
    # Black
    if board[sq_to_i("e8")] == -6 and board[sq_to_i("h8")] == -4:
        c |= 4
    if board[sq_to_i("e8")] == -6 and board[sq_to_i("a8")] == -4:
        c |= 8
    return c

def infer_last_move(prev_board: List[int], cur_board: List[int]) -> Optional[Tuple[int, int, int, int]]:
    """
    Tries to infer (fr,to,piece_moved,captured_piece_or0) from board difference.
    Returns None on failure.
    """
    diffs = [i for i in range(64) if prev_board[i] != cur_board[i]]
    if not diffs:
        return None

    # Typical move/capture: 2 squares differ; promotion 2 squares; castling 4 squares; en passant 3 squares.
    if len(diffs) == 2:
        a, b = diffs
        # from square becomes empty; to becomes piece
        if prev_board[a] != 0 and cur_board[a] == 0 and prev_board[b] != cur_board[b] and cur_board[b] != 0:
            fr, to = a, b
        elif prev_board[b] != 0 and cur_board[b] == 0 and cur_board[a] != 0:
            fr, to = b, a
        else:
            return None
        piece_moved = prev_board[fr]
        captured = prev_board[to] if prev_board[to] != 0 and color_of(prev_board[to]) != color_of(piece_moved) else 0
        return fr, to, piece_moved, captured

    if len(diffs) == 3:
        # Possible en passant: from empty, to pawn, captured pawn removed
        # We'll do a best-effort:
        # Identify from (prev!=0->cur==0), to (cur!=0), cap (prev pawn -> cur empty)
        fr = next((i for i in diffs if prev_board[i] != 0 and cur_board[i] == 0), None)
        to = next((i for i in diffs if cur_board[i] != 0 and prev_board[i] == 0), None)
        cap = next((i for i in diffs if prev_board[i] != 0 and cur_board[i] == 0 and i != fr), None)
        if fr is None or to is None or cap is None:
            return None
        piece_moved = prev_board[fr]
        captured = prev_board[cap]
        return fr, to, piece_moved, captured

    if len(diffs) == 4:
        # Possibly castling; ignore exact inference; still can update castling rights by king move.
        return None

    return None

def update_state_from_inferred(prev_board: List[int], cur_board: List[int], castling: int, ep_sq: int) -> Tuple[int, int]:
    # Reset EP by default unless we detect a pawn double
    new_ep = -1
    new_castling = castling

    inf = infer_last_move(prev_board, cur_board)
    if inf is None:
        return new_castling, new_ep

    fr, to, piece_moved, captured = inf
    side = color_of(piece_moved)

    # Update castling rights
    if abs(piece_moved) == 6:
        if side == 1:
            new_castling &= ~3
        else:
            new_castling &= ~12
    elif abs(piece_moved) == 4:
        if fr == sq_to_i("h1"):
            new_castling &= ~1
        elif fr == sq_to_i("a1"):
            new_castling &= ~2
        elif fr == sq_to_i("h8"):
            new_castling &= ~4
        elif fr == sq_to_i("a8"):
            new_castling &= ~8

    if captured != 0 and abs(captured) == 4:
        if to == sq_to_i("h1"):
            new_castling &= ~1
        elif to == sq_to_i("a1"):
            new_castling &= ~2
        elif to == sq_to_i("h8"):
            new_castling &= ~4
        elif to == sq_to_i("a8"):
            new_castling &= ~8

    # Detect pawn double move for EP square
    if abs(piece_moved) == 1:
        if abs(to - fr) == 16:
            new_ep = (fr + to) // 2

    return new_castling, new_ep

# ===========
# Policy API
# ===========

def policy(pieces: Dict[str, str], to_play: str, memory: Dict) -> Tuple[str, Dict]:
    board = pieces_to_board(pieces)
    side = 1 if to_play == "white" else -1

    # Initialize / update state
    castling = memory.get("castling")
    ep_sq = memory.get("ep_sq", -1)
    prev_board = memory.get("prev_board")

    if castling is None:
        # conservative-but-useful default based on current placement
        castling = initial_castling_from_board(board)

    if isinstance(prev_board, list) and len(prev_board) == 64:
        castling, ep_sq = update_state_from_inferred(prev_board, board, castling, ep_sq)
    else:
        ep_sq = -1

    # Pick best move
    # time budget: keep under ~1s total; use ~0.92s for search.
    m = pick_move(board, side, castling, ep_sq, time_limit=0.92)

    # Safety fallback: if something went wrong, just return the first legal move
    if m == 0:
        ms = legal_moves(board, side, castling, ep_sq)
        if ms:
            m = ms[0]
        else:
            # No legal moves: return a dummy string that at least is syntactically valid.
            # (In standard chess this is checkmate/stalemate; environment should not ask for a move.)
            return "a1a1", memory

    action = uci_of_move(m)

    # Update memory by applying our move so next call can infer opponent move properly
    nb, nc, nep = apply_move(board, side, castling, ep_sq, m)
    memory["prev_board"] = nb
    memory["castling"] = nc
    memory["ep_sq"] = nep

    return action, memory
