
import time
import random
from typing import Dict, List, Tuple, Optional

# =========================
# Helpers: board coordinates
# =========================

FILES = "abcdefgh"
RANKS = "12345678"

def sq_to_i(sq: str) -> int:
    # a1 -> 0, h8 -> 63
    f = FILES.index(sq[0])
    r = RANKS.index(sq[1])
    return r * 8 + f

def i_to_sq(i: int) -> str:
    return FILES[i % 8] + RANKS[i // 8]

def on_board(i: int) -> bool:
    return 0 <= i < 64

def file_of(i: int) -> int:
    return i % 8

def rank_of(i: int) -> int:
    return i // 8

# =========================
# Piece / side
# =========================

PIECE_VALUES = {
    'P': 100,
    'N': 320,
    'B': 330,
    'R': 500,
    'Q': 900,
    'K': 0
}

# Piece-square tables (middlegame-ish), indexed a1..h8 for White perspective.
# For Black, mirror ranks.
PST_P = [
     0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    12, 12, 20, 30, 30, 20, 12, 12,
     6,  6, 12, 25, 25, 12,  6,  6,
     2,  2,  6, 18, 18,  6,  2,  2,
     1,  1,  3,  6,  6,  3,  1,  1,
     0,  0,  0, -8, -8,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0
]
PST_N = [
   -50,-40,-30,-30,-30,-30,-40,-50,
   -40,-20,  0,  5,  5,  0,-20,-40,
   -30,  5, 10, 15, 15, 10,  5,-30,
   -30,  0, 15, 20, 20, 15,  0,-30,
   -30,  5, 15, 20, 20, 15,  5,-30,
   -30,  0, 10, 15, 15, 10,  0,-30,
   -40,-20,  0,  0,  0,  0,-20,-40,
   -50,-40,-30,-30,-30,-30,-40,-50
]
PST_B = [
   -20,-10,-10,-10,-10,-10,-10,-20,
   -10,  5,  0,  0,  0,  0,  5,-10,
   -10, 10, 10, 10, 10, 10, 10,-10,
   -10,  0, 10, 10, 10, 10,  0,-10,
   -10,  5,  5, 10, 10,  5,  5,-10,
   -10,  0,  5, 10, 10,  5,  0,-10,
   -10,  0,  0,  0,  0,  0,  0,-10,
   -20,-10,-10,-10,-10,-10,-10,-20
]
PST_R = [
     0,  0,  0,  5,  5,  0,  0,  0,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     5, 10, 10, 10, 10, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0
]
PST_Q = [
   -20,-10,-10, -5, -5,-10,-10,-20,
   -10,  0,  0,  0,  0,  0,  0,-10,
   -10,  0,  5,  5,  5,  5,  0,-10,
    -5,  0,  5,  5,  5,  5,  0, -5,
     0,  0,  5,  5,  5,  5,  0, -5,
   -10,  5,  5,  5,  5,  5,  0,-10,
   -10,  0,  5,  0,  0,  0,  0,-10,
   -20,-10,-10, -5, -5,-10,-10,-20
]
PST_K = [
   -30,-40,-40,-50,-50,-40,-40,-30,
   -30,-40,-40,-50,-50,-40,-40,-30,
   -30,-40,-40,-50,-50,-40,-40,-30,
   -30,-40,-40,-50,-50,-40,-40,-30,
   -20,-30,-30,-40,-40,-30,-30,-20,
   -10,-20,-20,-20,-20,-20,-20,-10,
    20, 20,  0,  0,  0,  0, 20, 20,
    20, 30, 10,  0,  0, 10, 30, 20
]

PST = {'P': PST_P, 'N': PST_N, 'B': PST_B, 'R': PST_R, 'Q': PST_Q, 'K': PST_K}

# Move representation: (from_i, to_i, promo_char_or_None, flags_int)
# flags bits: 1 capture, 2 castle, 4 promotion, 8 gives_check (for ordering)
CAPTURE = 1
CASTLE = 2
PROMO = 4
CHECK = 8

KNIGHT_DELTAS = (-17,-15,-10,-6,6,10,15,17)
KING_DELTAS = (-9,-8,-7,-1,1,7,8,9)
BISHOP_DIRS = (-9,-7,7,9)
ROOK_DIRS = (-8,-1,1,8)
QUEEN_DIRS = BISHOP_DIRS + ROOK_DIRS

INF = 10**9
MATE = 10**8

# =========================
# Core chess mechanics
# =========================

def color_of(piece: str) -> str:
    return piece[0]

def type_of(piece: str) -> str:
    return piece[1]

def mirror_index(i: int) -> int:
    # mirror ranks for black PST usage
    return (7 - rank_of(i)) * 8 + file_of(i)

def find_king(board: List[Optional[str]], side: str) -> int:
    target = ('w' if side == 'white' else 'b') + 'K'
    for i, p in enumerate(board):
        if p == target:
            return i
    return -1

def is_attacked(board: List[Optional[str]], sq: int, by_side: str) -> bool:
    """Is sq attacked by by_side ('white'/'black')?"""
    by_c = 'w' if by_side == 'white' else 'b'
    opp_c = by_c

    f = file_of(sq)
    r = rank_of(sq)

    # Pawn attacks
    if by_side == 'white':
        # white pawns attack up (towards higher ranks): from sq-7 and sq-9
        for d in (-7, -9):
            fr = sq + d
            if on_board(fr):
                # ensure correct file shift
                if abs(file_of(fr) - f) == 1 and board[fr] == opp_c + 'P':
                    return True
    else:
        # black pawns attack down: from sq+7 and sq+9
        for d in (7, 9):
            fr = sq + d
            if on_board(fr):
                if abs(file_of(fr) - f) == 1 and board[fr] == opp_c + 'P':
                    return True

    # Knight attacks
    for d in KNIGHT_DELTAS:
        fr = sq + d
        if not on_board(fr):
            continue
        # ensure no wrap: knight moves change file by 1 or 2
        if abs(file_of(fr) - f) not in (1, 2):
            continue
        p = board[fr]
        if p is not None and p == opp_c + 'N':
            return True

    # King attacks
    for d in KING_DELTAS:
        fr = sq + d
        if not on_board(fr):
            continue
        if abs(file_of(fr) - f) > 1:
            continue
        p = board[fr]
        if p is not None and p == opp_c + 'K':
            return True

    # Sliding attacks
    # Bishop/Queen
    for d in BISHOP_DIRS:
        fr = sq + d
        while on_board(fr) and abs(file_of(fr) - file_of(fr - d)) == 1:
            p = board[fr]
            if p is None:
                fr += d
                continue
            if color_of(p) == opp_c and type_of(p) in ('B', 'Q'):
                return True
            break

    # Rook/Queen
    for d in ROOK_DIRS:
        fr = sq + d
        while on_board(fr) and (d in (-8, 8) or abs(file_of(fr) - file_of(fr - d)) == 1):
            p = board[fr]
            if p is None:
                fr += d
                continue
            if color_of(p) == opp_c and type_of(p) in ('R', 'Q'):
                return True
            break

    return False

def in_check(board: List[Optional[str]], side: str) -> bool:
    k = find_king(board, side)
    if k < 0:
        # illegal position; treat as in check to be safe
        return True
    other = 'black' if side == 'white' else 'white'
    return is_attacked(board, k, other)

def make_move(board: List[Optional[str]], side: str, mv: Tuple[int,int,Optional[str],int]) -> Tuple[List[Optional[str]], str]:
    fr, to, promo, flags = mv
    nb = board[:]  # copy
    piece = nb[fr]
    nb[fr] = None

    # Handle castling rook move
    if flags & CASTLE and piece is not None and type_of(piece) == 'K':
        # Identify side by destination
        if side == 'white':
            if fr == sq_to_i('e1') and to == sq_to_i('g1'):
                # rook h1->f1
                rook_from = sq_to_i('h1'); rook_to = sq_to_i('f1')
                nb[rook_to] = nb[rook_from]
                nb[rook_from] = None
            elif fr == sq_to_i('e1') and to == sq_to_i('c1'):
                rook_from = sq_to_i('a1'); rook_to = sq_to_i('d1')
                nb[rook_to] = nb[rook_from]
                nb[rook_from] = None
        else:
            if fr == sq_to_i('e8') and to == sq_to_i('g8'):
                rook_from = sq_to_i('h8'); rook_to = sq_to_i('f8')
                nb[rook_to] = nb[rook_from]
                nb[rook_from] = None
            elif fr == sq_to_i('e8') and to == sq_to_i('c8'):
                rook_from = sq_to_i('a8'); rook_to = sq_to_i('d8')
                nb[rook_to] = nb[rook_from]
                nb[rook_from] = None

    # normal capture overwrite
    if promo is not None and piece is not None and type_of(piece) == 'P':
        # promo is lower-case: q r b n
        new_piece = ('w' if side == 'white' else 'b') + promo.upper()
        nb[to] = new_piece
    else:
        nb[to] = piece

    return nb, ('black' if side == 'white' else 'white')

def gives_check(board: List[Optional[str]], side: str, mv: Tuple[int,int,Optional[str],int]) -> bool:
    nb, nside = make_move(board, side, mv)
    # after side moves, opponent is nside
    return in_check(nb, nside)

def gen_pseudo_moves(board: List[Optional[str]], side: str) -> List[Tuple[int,int,Optional[str],int]]:
    c = 'w' if side == 'white' else 'b'
    other_c = 'b' if c == 'w' else 'w'
    moves = []

    def add(fr, to, promo=None, flags=0):
        moves.append((fr, to, promo, flags))

    for i, p in enumerate(board):
        if p is None or color_of(p) != c:
            continue
        pt = type_of(p)

        if pt == 'P':
            r = rank_of(i); f = file_of(i)
            if side == 'white':
                one = i + 8
                if on_board(one) and board[one] is None:
                    if rank_of(one) == 7:
                        for pr in ('q','r','b','n'):
                            add(i, one, pr, PROMO)
                    else:
                        add(i, one)
                    # two-step
                    if r == 1:
                        two = i + 16
                        if board[two] is None:
                            add(i, two)
                # captures
                for df in (-1, 1):
                    if 0 <= f + df < 8:
                        cap = i + 8 + df
                        if on_board(cap) and board[cap] is not None and color_of(board[cap]) == other_c:
                            if rank_of(cap) == 7:
                                for pr in ('q','r','b','n'):
                                    add(i, cap, pr, PROMO | CAPTURE)
                            else:
                                add(i, cap, None, CAPTURE)
            else:
                one = i - 8
                if on_board(one) and board[one] is None:
                    if rank_of(one) == 0:
                        for pr in ('q','r','b','n'):
                            add(i, one, pr, PROMO)
                    else:
                        add(i, one)
                    if r == 6:
                        two = i - 16
                        if board[two] is None:
                            add(i, two)
                for df in (-1, 1):
                    if 0 <= f + df < 8:
                        cap = i - 8 + df
                        if on_board(cap) and board[cap] is not None and color_of(board[cap]) == other_c:
                            if rank_of(cap) == 0:
                                for pr in ('q','r','b','n'):
                                    add(i, cap, pr, PROMO | CAPTURE)
                            else:
                                add(i, cap, None, CAPTURE)

        elif pt == 'N':
            f0 = file_of(i)
            for d in KNIGHT_DELTAS:
                to = i + d
                if not on_board(to):
                    continue
                if abs(file_of(to) - f0) not in (1, 2):
                    continue
                tp = board[to]
                if tp is None:
                    add(i, to)
                elif color_of(tp) == other_c:
                    add(i, to, None, CAPTURE)

        elif pt == 'B':
            for d in BISHOP_DIRS:
                to = i + d
                while on_board(to) and abs(file_of(to) - file_of(to - d)) == 1:
                    tp = board[to]
                    if tp is None:
                        add(i, to)
                    else:
                        if color_of(tp) == other_c:
                            add(i, to, None, CAPTURE)
                        break
                    to += d

        elif pt == 'R':
            for d in ROOK_DIRS:
                to = i + d
                while on_board(to) and (d in (-8, 8) or abs(file_of(to) - file_of(to - d)) == 1):
                    tp = board[to]
                    if tp is None:
                        add(i, to)
                    else:
                        if color_of(tp) == other_c:
                            add(i, to, None, CAPTURE)
                        break
                    to += d

        elif pt == 'Q':
            for d in QUEEN_DIRS:
                to = i + d
                while on_board(to) and (d in (-8, 8) or abs(file_of(to) - file_of(to - d)) == 1):
                    tp = board[to]
                    if tp is None:
                        add(i, to)
                    else:
                        if color_of(tp) == other_c:
                            add(i, to, None, CAPTURE)
                        break
                    to += d

        elif pt == 'K':
            f0 = file_of(i)
            for d in KING_DELTAS:
                to = i + d
                if not on_board(to):
                    continue
                if abs(file_of(to) - f0) > 1:
                    continue
                tp = board[to]
                if tp is None:
                    add(i, to)
                elif color_of(tp) == other_c:
                    add(i, to, None, CAPTURE)

            # Castling (best-effort; assumes rights from piece placement)
            # Only if king on start square and corresponding rook exists and squares empty.
            if side == 'white' and i == sq_to_i('e1'):
                # Kingside
                if board[sq_to_i('h1')] == 'wR' and board[sq_to_i('f1')] is None and board[sq_to_i('g1')] is None:
                    add(i, sq_to_i('g1'), None, CASTLE)
                # Queenside
                if board[sq_to_i('a1')] == 'wR' and board[sq_to_i('b1')] is None and board[sq_to_i('c1')] is None and board[sq_to_i('d1')] is None:
                    add(i, sq_to_i('c1'), None, CASTLE)
            if side == 'black' and i == sq_to_i('e8'):
                if board[sq_to_i('h8')] == 'bR' and board[sq_to_i('f8')] is None and board[sq_to_i('g8')] is None:
                    add(i, sq_to_i('g8'), None, CASTLE)
                if board[sq_to_i('a8')] == 'bR' and board[sq_to_i('b8')] is None and board[sq_to_i('c8')] is None and board[sq_to_i('d8')] is None:
                    add(i, sq_to_i('c8'), None, CASTLE)

    return moves

def filter_legal_moves(board: List[Optional[str]], side: str, pseudo: List[Tuple[int,int,Optional[str],int]]) -> List[Tuple[int,int,Optional[str],int]]:
    legal = []
    # for castling need additional constraints: king not in check, transit squares not attacked
    for mv in pseudo:
        fr, to, promo, flags = mv
        piece = board[fr]
        if piece is None:
            continue
        if flags & CASTLE:
            # basic check: king not in check now, and squares passed not attacked
            if in_check(board, side):
                continue
            if side == 'white':
                if to == sq_to_i('g1'):
                    if is_attacked(board, sq_to_i('f1'), 'black') or is_attacked(board, sq_to_i('g1'), 'black'):
                        continue
                elif to == sq_to_i('c1'):
                    if is_attacked(board, sq_to_i('d1'), 'black') or is_attacked(board, sq_to_i('c1'), 'black'):
                        continue
            else:
                if to == sq_to_i('g8'):
                    if is_attacked(board, sq_to_i('f8'), 'white') or is_attacked(board, sq_to_i('g8'), 'white'):
                        continue
                elif to == sq_to_i('c8'):
                    if is_attacked(board, sq_to_i('d8'), 'white') or is_attacked(board, sq_to_i('c8'), 'white'):
                        continue

        nb, nside = make_move(board, side, mv)
        if not in_check(nb, side):
            legal.append(mv)
    return legal

def move_to_uci(mv: Tuple[int,int,Optional[str],int]) -> str:
    fr, to, promo, flags = mv
    s = i_to_sq(fr) + i_to_sq(to)
    if promo is not None:
        s += promo
    return s

# =========================
# Evaluation
# =========================

def evaluate(board: List[Optional[str]], side_to_move: str) -> int:
    """Evaluation in centipawns from the perspective of side_to_move (positive is good for side_to_move)."""
    white_score = 0
    black_score = 0

    # Material + PST
    for i, p in enumerate(board):
        if p is None:
            continue
        c = color_of(p)
        t = type_of(p)
        val = PIECE_VALUES[t]
        pst = PST[t]
        if c == 'w':
            white_score += val + pst[i]
        else:
            black_score += val + pst[mirror_index(i)]

    # Mobility (lightweight)
    w_moves = len(filter_legal_moves(board, 'white', gen_pseudo_moves(board, 'white')))
    b_moves = len(filter_legal_moves(board, 'black', gen_pseudo_moves(board, 'black')))
    white_score += 3 * w_moves
    black_score += 3 * b_moves

    # King safety: small penalty if in check (should not happen for side to move in legal positions)
    if in_check(board, 'white'):
        white_score -= 25
    if in_check(board, 'black'):
        black_score -= 25

    score_from_white = white_score - black_score
    return score_from_white if side_to_move == 'white' else -score_from_white

# =========================
# Search
# =========================

class TimeUp(Exception):
    pass

def mvv_lva(board: List[Optional[str]], mv: Tuple[int,int,Optional[str],int], side: str) -> int:
    fr, to, promo, flags = mv
    score = 0
    if flags & PROMO:
        # prefer queen promotions strongly
        promo_map = {'q': 900, 'r': 500, 'b': 330, 'n': 320}
        score += 800 + promo_map.get(promo, 0)
    if flags & CAPTURE:
        victim = board[to]
        attacker = board[fr]
        if victim is not None and attacker is not None:
            score += 10 * PIECE_VALUES[type_of(victim)] - PIECE_VALUES[type_of(attacker)]
        else:
            score += 100
    if flags & CASTLE:
        score += 30
    return score

def order_moves(board: List[Optional[str]], side: str, moves: List[Tuple[int,int,Optional[str],int]]) -> List[Tuple[int,int,Optional[str],int]]:
    # compute check-giving for top candidates only (avoid too much overhead)
    scored = []
    # pre-score
    prelim = []
    for mv in moves:
        prelim.append((mvv_lva(board, mv, side), mv))
    prelim.sort(key=lambda x: x[0], reverse=True)
    # For top N, compute check bonus
    N = 10
    top = prelim[:N]
    rest = prelim[N:]
    for sc, mv in top:
        if gives_check(board, side, mv):
            sc += 120
            mv = (mv[0], mv[1], mv[2], mv[3] | CHECK)
        scored.append((sc, mv))
    scored.extend(rest)
    scored.sort(key=lambda x: x[0], reverse=True)
    return [mv for _, mv in scored]

def quiescence(board: List[Optional[str]], side: str, alpha: int, beta: int, start: float, limit: float, ply: int, qdepth: int) -> int:
    if time.time() - start > limit:
        raise TimeUp
    stand = evaluate(board, side)
    if stand >= beta:
        return beta
    if alpha < stand:
        alpha = stand
    if qdepth <= 0:
        return stand

    pseudo = gen_pseudo_moves(board, side)
    # only captures and promotions in quiescence
    pseudo = [mv for mv in pseudo if (mv[3] & CAPTURE) or (mv[3] & PROMO)]
    moves = filter_legal_moves(board, side, pseudo)
    moves = order_moves(board, side, moves)

    for mv in moves:
        nb, nside = make_move(board, side, mv)
        score = -quiescence(nb, nside, -beta, -alpha, start, limit, ply + 1, qdepth - 1)
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
    return alpha

def negamax(board: List[Optional[str]], side: str, depth: int, alpha: int, beta: int,
            start: float, limit: float, ply: int) -> int:
    if time.time() - start > limit:
        raise TimeUp

    pseudo = gen_pseudo_moves(board, side)
    legal = filter_legal_moves(board, side, pseudo)

    if not legal:
        # mate or stalemate
        if in_check(board, side):
            return -MATE + ply
        return 0

    if depth <= 0:
        return quiescence(board, side, alpha, beta, start, limit, ply, qdepth=3)

    legal = order_moves(board, side, legal)

    best = -INF
    for mv in legal:
        nb, nside = make_move(board, side, mv)
        score = -negamax(nb, nside, depth - 1, -beta, -alpha, start, limit, ply + 1)
        if score > best:
            best = score
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break
    return best

def choose_move(board: List[Optional[str]], side: str, time_limit: float) -> Tuple[int,int,Optional[str],int]:
    start = time.time()
    pseudo = gen_pseudo_moves(board, side)
    legal = filter_legal_moves(board, side, pseudo)
    if not legal:
        return (0, 0, None, 0)

    # Immediate tactical: mate in 1 if exists
    for mv in legal:
        nb, nside = make_move(board, side, mv)
        op_legal = filter_legal_moves(nb, nside, gen_pseudo_moves(nb, nside))
        if not op_legal and in_check(nb, nside):
            return mv

    best_move = legal[0]
    best_score = -INF

    # Iterative deepening
    depth = 1
    # order at root
    root_moves = order_moves(board, side, legal)

    while True:
        if time.time() - start > time_limit:
            break
        cur_best = None
        cur_best_score = -INF
        alpha = -INF
        beta = INF
        try:
            for mv in root_moves:
                if time.time() - start > time_limit:
                    raise TimeUp
                nb, nside = make_move(board, side, mv)
                score = -negamax(nb, nside, depth - 1, -beta, -alpha, start, time_limit, 1)
                # small deterministic-ish tie-break + random jitter
                if score > cur_best_score or (score == cur_best_score and (mv[3] & CHECK) and not (cur_best and (cur_best[3] & CHECK))):
                    cur_best_score = score
                    cur_best = mv
                if score > alpha:
                    alpha = score
            if cur_best is not None:
                best_move = cur_best
                best_score = cur_best_score
                # reorder root moves with best first for next iteration
                root_moves = [best_move] + [m for m in root_moves if m != best_move]
            depth += 1
            if depth > 6:
                break
        except TimeUp:
            break

    # If multiple equivalent moves, add mild randomness to avoid predictability
    # (only among top few by static ordering)
    top = order_moves(board, side, legal)[:4]
    if best_move not in top:
        top = [best_move] + top[:3]
    # Choose best by shallow eval among top to reduce blunders if search cut early
    scored = []
    for mv in top:
        nb, nside = make_move(board, side, mv)
        sc = -evaluate(nb, nside)
        # prefer the searched best move slightly
        if mv == best_move:
            sc += 5
        scored.append((sc, mv))
    scored.sort(key=lambda x: x[0], reverse=True)
    best_candidates = [scored[0][1]]
    for sc, mv in scored[1:]:
        if sc == scored[0][0]:
            best_candidates.append(mv)
    return random.choice(best_candidates)

# =========================
# Public API
# =========================

def policy(pieces: Dict[str, str], to_play: str) -> str:
    # Build board array
    board: List[Optional[str]] = [None] * 64
    for sq, pc in pieces.items():
        try:
            idx = sq_to_i(sq)
            board[idx] = pc
        except Exception:
            continue

    side = 'white' if to_play == 'white' else 'black'

    # Time budget (seconds). Keep conservative under 1s.
    # If position is sparse, search can go deeper; but fixed limit is safest.
    time_limit = 0.85

    mv = choose_move(board, side, time_limit)

    # Ensure returned move is legal (final guard)
    pseudo = gen_pseudo_moves(board, side)
    legal = filter_legal_moves(board, side, pseudo)
    if legal:
        uci = move_to_uci(mv)
        legal_uci = {move_to_uci(x) for x in legal}
        if uci in legal_uci:
            return uci
        # fallback: pick first legal deterministically
        return move_to_uci(order_moves(board, side, legal)[0])

    # Terminal positions shouldn't be queried; fallback anyway.
    return "e2e4"
