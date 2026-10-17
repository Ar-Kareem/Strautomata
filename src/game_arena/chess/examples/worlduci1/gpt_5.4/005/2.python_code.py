
import time
from typing import List, Tuple, Dict, Optional

FILES = "abcdefgh"
RANKS = "12345678"

PIECE_VALUES = {
    'K': 0,
    'Q': 900,
    'R': 500,
    'B': 330,
    'N': 320,
    'P': 100,
}

MATE_SCORE = 100000
INF = 10**9

CENTER_SQUARES = {"d4", "e4", "d5", "e5"}

PAWN_PSQ = [
      0,   0,   0,   0,   0,   0,   0,   0,
     50,  50,  50,  50,  50,  50,  50,  50,
     10,  10,  20,  30,  30,  20,  10,  10,
      5,   5,  10,  25,  25,  10,   5,   5,
      0,   0,   0,  20,  20,   0,   0,   0,
      5,  -5, -10,   0,   0, -10,  -5,   5,
      5,  10,  10, -20, -20,  10,  10,   5,
      0,   0,   0,   0,   0,   0,   0,   0,
]
KNIGHT_PSQ = [
    -50, -40, -30, -30, -30, -30, -40, -50,
    -40, -20,   0,   0,   0,   0, -20, -40,
    -30,   0,  10,  15,  15,  10,   0, -30,
    -30,   5,  15,  20,  20,  15,   5, -30,
    -30,   0,  15,  20,  20,  15,   0, -30,
    -30,   5,  10,  15,  15,  10,   5, -30,
    -40, -20,   0,   5,   5,   0, -20, -40,
    -50, -40, -30, -30, -30, -30, -40, -50,
]
BISHOP_PSQ = [
    -20, -10, -10, -10, -10, -10, -10, -20,
    -10,   5,   0,   0,   0,   0,   5, -10,
    -10,  10,  10,  10,  10,  10,  10, -10,
    -10,   0,  10,  10,  10,  10,   0, -10,
    -10,   5,   5,  10,  10,   5,   5, -10,
    -10,   0,   5,  10,  10,   5,   0, -10,
    -10,   0,   0,   0,   0,   0,   0, -10,
    -20, -10, -10, -10, -10, -10, -10, -20,
]
ROOK_PSQ = [
      0,   0,   0,   5,   5,   0,   0,   0,
     -5,   0,   0,   0,   0,   0,   0,  -5,
     -5,   0,   0,   0,   0,   0,   0,  -5,
     -5,   0,   0,   0,   0,   0,   0,  -5,
     -5,   0,   0,   0,   0,   0,   0,  -5,
     -5,   0,   0,   0,   0,   0,   0,  -5,
      5,  10,  10,  10,  10,  10,  10,   5,
      0,   0,   0,   0,   0,   0,   0,   0,
]
QUEEN_PSQ = [
    -20, -10, -10,  -5,  -5, -10, -10, -20,
    -10,   0,   0,   0,   0,   5,   0, -10,
    -10,   0,   5,   5,   5,   5,   5, -10,
     -5,   0,   5,   5,   5,   5,   0,  -5,
      0,   0,   5,   5,   5,   5,   0,  -5,
    -10,   5,   5,   5,   5,   5,   0, -10,
    -10,   0,   5,   0,   0,   0,   0, -10,
    -20, -10, -10,  -5,  -5, -10, -10, -20,
]
KING_MID_PSQ = [
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -20, -30, -30, -40, -40, -30, -30, -20,
    -10, -20, -20, -20, -20, -20, -20, -10,
     20,  20,   0,   0,   0,   0,  20,  20,
     20,  30,  10,   0,   0,  10,  30,  20,
]

PST = {
    'P': PAWN_PSQ,
    'N': KNIGHT_PSQ,
    'B': BISHOP_PSQ,
    'R': ROOK_PSQ,
    'Q': QUEEN_PSQ,
    'K': KING_MID_PSQ,
}

KNIGHT_DIRS = [(-2,-1), (-2,1), (-1,-2), (-1,2), (1,-2), (1,2), (2,-1), (2,1)]
BISHOP_DIRS = [(-1,-1), (-1,1), (1,-1), (1,1)]
ROOK_DIRS = [(-1,0), (1,0), (0,-1), (0,1)]
KING_DIRS = BISHOP_DIRS + ROOK_DIRS

def sq_to_xy(s: str) -> Tuple[int, int]:
    return ord(s[0]) - 97, ord(s[1]) - 49

def xy_to_sq(x: int, y: int) -> str:
    return chr(97 + x) + chr(49 + y)

def in_bounds(x: int, y: int) -> bool:
    return 0 <= x < 8 and 0 <= y < 8

def color_of(piece: str) -> str:
    return piece[0]

def type_of(piece: str) -> str:
    return piece[1]

def opp(c: str) -> str:
    return 'b' if c == 'w' else 'w'

def to_color_char(to_play: str) -> str:
    return 'w' if to_play == 'white' else 'b'

def idx_from_xy(x: int, y: int) -> int:
    return y * 8 + x

def pst_value(piece: str, sq: str) -> int:
    x, y = sq_to_xy(sq)
    idx = idx_from_xy(x, y)
    t = type_of(piece)
    if color_of(piece) == 'w':
        return PST[t][idx]
    else:
        return PST[t][idx_from_xy(x, 7 - y)]

def find_king(board: Dict[str, str], side: str) -> Optional[str]:
    target = side + 'K'
    for sq, p in board.items():
        if p == target:
            return sq
    return None

def is_square_attacked(board: Dict[str, str], square: str, by_side: str) -> bool:
    x, y = sq_to_xy(square)

    pawn_dir = 1 if by_side == 'w' else -1
    for dx in (-1, 1):
        px, py = x - dx, y - pawn_dir
        if in_bounds(px, py):
            p = board.get(xy_to_sq(px, py))
            if p == by_side + 'P':
                return True

    for dx, dy in KNIGHT_DIRS:
        nx, ny = x + dx, y + dy
        if in_bounds(nx, ny):
            p = board.get(xy_to_sq(nx, ny))
            if p == by_side + 'N':
                return True

    for dx, dy in BISHOP_DIRS:
        nx, ny = x + dx, y + dy
        while in_bounds(nx, ny):
            p = board.get(xy_to_sq(nx, ny))
            if p:
                if color_of(p) == by_side and type_of(p) in ('B', 'Q'):
                    return True
                break
            nx += dx
            ny += dy

    for dx, dy in ROOK_DIRS:
        nx, ny = x + dx, y + dy
        while in_bounds(nx, ny):
            p = board.get(xy_to_sq(nx, ny))
            if p:
                if color_of(p) == by_side and type_of(p) in ('R', 'Q'):
                    return True
                break
            nx += dx
            ny += dy

    for dx, dy in KING_DIRS:
        nx, ny = x + dx, y + dy
        if in_bounds(nx, ny):
            p = board.get(xy_to_sq(nx, ny))
            if p == by_side + 'K':
                return True

    return False

def in_check(board: Dict[str, str], side: str) -> bool:
    ks = find_king(board, side)
    if ks is None:
        return True
    return is_square_attacked(board, ks, opp(side))

def can_castle_kingside(board: Dict[str, str], side: str) -> bool:
    if side == 'w':
        if board.get('e1') != 'wK' or board.get('h1') != 'wR':
            return False
        if any(s in board for s in ('f1', 'g1')):
            return False
        if in_check(board, 'w'):
            return False
        if is_square_attacked(board, 'f1', 'b') or is_square_attacked(board, 'g1', 'b'):
            return False
        return True
    else:
        if board.get('e8') != 'bK' or board.get('h8') != 'bR':
            return False
        if any(s in board for s in ('f8', 'g8')):
            return False
        if in_check(board, 'b'):
            return False
        if is_square_attacked(board, 'f8', 'w') or is_square_attacked(board, 'g8', 'w'):
            return False
        return True

def can_castle_queenside(board: Dict[str, str], side: str) -> bool:
    if side == 'w':
        if board.get('e1') != 'wK' or board.get('a1') != 'wR':
            return False
        if any(s in board for s in ('b1', 'c1', 'd1')):
            return False
        if in_check(board, 'w'):
            return False
        if is_square_attacked(board, 'd1', 'b') or is_square_attacked(board, 'c1', 'b'):
            return False
        return True
    else:
        if board.get('e8') != 'bK' or board.get('a8') != 'bR':
            return False
        if any(s in board for s in ('b8', 'c8', 'd8')):
            return False
        if in_check(board, 'b'):
            return False
        if is_square_attacked(board, 'd8', 'w') or is_square_attacked(board, 'c8', 'w'):
            return False
        return True

def make_move(board: Dict[str, str], move: str) -> Dict[str, str]:
    nb = dict(board)
    frm, to = move[:2], move[2:4]
    piece = nb.pop(frm)
    promo = move[4] if len(move) == 5 else None

    if type_of(piece) == 'K':
        if frm == 'e1' and to == 'g1' and piece == 'wK':
            nb.pop('h1', None)
            nb['f1'] = 'wR'
        elif frm == 'e1' and to == 'c1' and piece == 'wK':
            nb.pop('a1', None)
            nb['d1'] = 'wR'
        elif frm == 'e8' and to == 'g8' and piece == 'bK':
            nb.pop('h8', None)
            nb['f8'] = 'bR'
        elif frm == 'e8' and to == 'c8' and piece == 'bK':
            nb.pop('a8', None)
            nb['d8'] = 'bR'

    nb.pop(to, None)

    if promo:
        nb[to] = color_of(piece) + promo.upper()
    else:
        nb[to] = piece
    return nb

def pseudo_moves(board: Dict[str, str], side: str) -> List[str]:
    moves = []
    for frm, piece in board.items():
        if color_of(piece) != side:
            continue
        t = type_of(piece)
        x, y = sq_to_xy(frm)

        if t == 'P':
            dy = 1 if side == 'w' else -1
            start_rank = 1 if side == 'w' else 6
            promo_rank = 7 if side == 'w' else 0

            ny = y + dy
            if in_bounds(x, ny):
                to = xy_to_sq(x, ny)
                if to not in board:
                    if ny == promo_rank:
                        for pr in 'qrbn':
                            moves.append(frm + to + pr)
                    else:
                        moves.append(frm + to)
                    if y == start_rank:
                        ny2 = y + 2 * dy
                        to2 = xy_to_sq(x, ny2)
                        if in_bounds(x, ny2) and to2 not in board:
                            moves.append(frm + to2)

            for dx in (-1, 1):
                nx, ny = x + dx, y + dy
                if in_bounds(nx, ny):
                    to = xy_to_sq(nx, ny)
                    p = board.get(to)
                    if p and color_of(p) != side:
                        if ny == promo_rank:
                            for pr in 'qrbn':
                                moves.append(frm + to + pr)
                        else:
                            moves.append(frm + to)

        elif t == 'N':
            for dx, dy in KNIGHT_DIRS:
                nx, ny = x + dx, y + dy
                if in_bounds(nx, ny):
                    to = xy_to_sq(nx, ny)
                    p = board.get(to)
                    if p is None or color_of(p) != side:
                        moves.append(frm + to)

        elif t == 'B':
            for dx, dy in BISHOP_DIRS:
                nx, ny = x + dx, y + dy
                while in_bounds(nx, ny):
                    to = xy_to_sq(nx, ny)
                    p = board.get(to)
                    if p is None:
                        moves.append(frm + to)
                    else:
                        if color_of(p) != side:
                            moves.append(frm + to)
                        break
                    nx += dx
                    ny += dy

        elif t == 'R':
            for dx, dy in ROOK_DIRS:
                nx, ny = x + dx, y + dy
                while in_bounds(nx, ny):
                    to = xy_to_sq(nx, ny)
                    p = board.get(to)
                    if p is None:
                        moves.append(frm + to)
                    else:
                        if color_of(p) != side:
                            moves.append(frm + to)
                        break
                    nx += dx
                    ny += dy

        elif t == 'Q':
            for dx, dy in KING_DIRS:
                nx, ny = x + dx, y + dy
                while in_bounds(nx, ny):
                    to = xy_to_sq(nx, ny)
                    p = board.get(to)
                    if p is None:
                        moves.append(frm + to)
                    else:
                        if color_of(p) != side:
                            moves.append(frm + to)
                        break
                    nx += dx
                    ny += dy

        elif t == 'K':
            for dx, dy in KING_DIRS:
                nx, ny = x + dx, y + dy
                if in_bounds(nx, ny):
                    to = xy_to_sq(nx, ny)
                    p = board.get(to)
                    if p is None or color_of(p) != side:
                        moves.append(frm + to)
            if side == 'w':
                if can_castle_kingside(board, 'w'):
                    moves.append('e1g1')
                if can_castle_queenside(board, 'w'):
                    moves.append('e1c1')
            else:
                if can_castle_kingside(board, 'b'):
                    moves.append('e8g8')
                if can_castle_queenside(board, 'b'):
                    moves.append('e8c8')
    return moves

def legal_moves(board: Dict[str, str], side: str) -> List[str]:
    out = []
    for mv in pseudo_moves(board, side):
        nb = make_move(board, mv)
        if not in_check(nb, side):
            out.append(mv)
    return out

def game_over_score(board: Dict[str, str], side: str, ply: int) -> Optional[int]:
    lm = legal_moves(board, side)
    if lm:
        return None
    if in_check(board, side):
        return -MATE_SCORE + ply
    return 0

def evaluate(board: Dict[str, str], side: str) -> int:
    score = 0
    white_bishops = 0
    black_bishops = 0

    for sq, piece in board.items():
        val = PIECE_VALUES[type_of(piece)] + pst_value(piece, sq)
        if color_of(piece) == 'w':
            score += val
            if type_of(piece) == 'B':
                white_bishops += 1
        else:
            score -= val
            if type_of(piece) == 'B':
                black_bishops += 1

        if sq in CENTER_SQUARES:
            score += 12 if color_of(piece) == 'w' else -12

        if type_of(piece) == 'P':
            x, y = sq_to_xy(sq)
            advance = y if color_of(piece) == 'w' else (7 - y)
            score += 8 * advance if color_of(piece) == 'w' else -8 * advance

    if white_bishops >= 2:
        score += 30
    if black_bishops >= 2:
        score -= 30

    w_king = find_king(board, 'w')
    b_king = find_king(board, 'b')
    if w_king:
        wx, wy = sq_to_xy(w_king)
        shield = 0
        for dx in (-1, 0, 1):
            nx, ny = wx + dx, wy + 1
            if in_bounds(nx, ny) and board.get(xy_to_sq(nx, ny)) == 'wP':
                shield += 10
        score += shield
    if b_king:
        bx, by = sq_to_xy(b_king)
        shield = 0
        for dx in (-1, 0, 1):
            nx, ny = bx + dx, by - 1
            if in_bounds(nx, ny) and board.get(xy_to_sq(nx, ny)) == 'bP':
                shield += 10
        score -= shield

    wm = len(pseudo_moves(board, 'w'))
    bm = len(pseudo_moves(board, 'b'))
    score += 2 * (wm - bm)

    return score if side == 'w' else -score

def move_score(board: Dict[str, str], move: str, side: str) -> int:
    frm, to = move[:2], move[2:4]
    piece = board[frm]
    target = board.get(to)
    score = 0

    if len(move) == 5:
        promo_piece = move[4].upper()
        score += PIECE_VALUES[promo_piece] + 700

    if target:
        score += 10 * PIECE_VALUES[type_of(target)] - PIECE_VALUES[type_of(piece)]

    nb = make_move(board, move)
    if in_check(nb, opp(side)):
        score += 80

    if type_of(piece) == 'K' and frm in ('e1', 'e8') and to in ('g1', 'c1', 'g8', 'c8'):
        score += 60

    if to in CENTER_SQUARES:
        score += 15

    return score

def ordered_moves(board: Dict[str, str], side: str) -> List[str]:
    moves = legal_moves(board, side)
    moves.sort(key=lambda m: move_score(board, m, side), reverse=True)
    return moves

class Timeout(Exception):
    pass

def alphabeta(board: Dict[str, str], side: str, depth: int, alpha: int, beta: int, start: float, limit: float, ply: int) -> Tuple[int, Optional[str]]:
    if time.time() - start > limit:
        raise Timeout

    terminal = game_over_score(board, side, ply)
    if terminal is not None:
        return terminal, None

    if depth == 0:
        return evaluate(board, side), None

    best_move = None
    moves = ordered_moves(board, side)
    if not moves:
        return evaluate(board, side), None

    for mv in moves:
        nb = make_move(board, mv)
        score, _ = alphabeta(nb, opp(side), depth - 1, -beta, -alpha, start, limit, ply + 1)
        score = -score
        if score > alpha:
            alpha = score
            best_move = mv
            if alpha >= beta:
                break
    return alpha, best_move

def choose_move(board: Dict[str, str], side: str) -> str:
    moves = ordered_moves(board, side)
    if not moves:
        return ""

    for mv in moves:
        nb = make_move(board, mv)
        opp_moves = legal_moves(nb, opp(side))
        if not opp_moves and in_check(nb, opp(side)):
            return mv

    start = time.time()
    limit = 0.85

    best = moves[0]
    depth = 1
    try:
        while depth <= 4:
            score, mv = alphabeta(board, side, depth, -INF, INF, start, limit, 0)
            if mv is not None:
                best = mv
            depth += 1
    except Timeout:
        pass

    return best

def policy(pieces: dict[str, str], to_play: str) -> str:
    side = to_color_char(to_play)
    try:
        lm = legal_moves(pieces, side)
        if not lm:
            return ""
        mv = choose_move(pieces, side)
        if mv in lm:
            return mv
        return lm[0]
    except Exception:
        side = to_color_char(to_play)
        try:
            lm = legal_moves(pieces, side)
            return lm[0] if lm else ""
        except Exception:
            for frm, piece in pieces.items():
                if color_of(piece) == side:
                    x, y = sq_to_xy(frm)
                    t = type_of(piece)
                    candidates = []
                    if t == 'P':
                        dy = 1 if side == 'w' else -1
                        for nx, ny in [(x, y + dy), (x + 1, y + dy), (x - 1, y + dy)]:
                            if in_bounds(nx, ny):
                                to = xy_to_sq(nx, ny)
                                candidates.append(frm + to)
                    elif t == 'N':
                        for dx, dy in KNIGHT_DIRS:
                            nx, ny = x + dx, y + dy
                            if in_bounds(nx, ny):
                                candidates.append(frm + xy_to_sq(nx, ny))
                    elif t == 'B':
                        for dx, dy in BISHOP_DIRS:
                            nx, ny = x + dx, y + dy
                            if in_bounds(nx, ny):
                                candidates.append(frm + xy_to_sq(nx, ny))
                    elif t == 'R':
                        for dx, dy in ROOK_DIRS:
                            nx, ny = x + dx, y + dy
                            if in_bounds(nx, ny):
                                candidates.append(frm + xy_to_sq(nx, ny))
                    elif t == 'Q':
                        for dx, dy in KING_DIRS:
                            nx, ny = x + dx, y + dy
                            if in_bounds(nx, ny):
                                candidates.append(frm + xy_to_sq(nx, ny))
                    elif t == 'K':
                        for dx, dy in KING_DIRS:
                            nx, ny = x + dx, y + dy
                            if in_bounds(nx, ny):
                                candidates.append(frm + xy_to_sq(nx, ny))
                    if candidates:
                        return candidates[0]
            return ""
