
from typing import Dict, List, Tuple, Optional
import math
import random

FILES = "abcdefgh"
RANKS = "12345678"

PIECE_VALUES = {
    'P': 100,
    'N': 320,
    'B': 330,
    'R': 500,
    'Q': 900,
    'K': 0,
}

KNIGHT_PSQ = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50,
]
BISHOP_PSQ = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -20,-10,-10,-10,-10,-10,-10,-20,
]
ROOK_PSQ = [
     0,  0,  5, 10, 10,  5,  0,  0,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     5, 10, 10, 10, 10, 10, 10,  5,
     0,  0,  5, 10, 10,  5,  0,  0,
]
QUEEN_PSQ = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
     -5,  0,  5,  5,  5,  5,  0, -5,
      0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20,
]
KING_MID_PSQ = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
     20, 20,  0,  0,  0,  0, 20, 20,
     20, 30, 10,  0,  0, 10, 30, 20,
]
KING_END_PSQ = [
    -50,-40,-30,-20,-20,-30,-40,-50,
    -30,-20,-10,  0,  0,-10,-20,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-30,  0,  0,  0,  0,-30,-30,
    -50,-30,-30,-30,-30,-30,-30,-50,
]

def sq_to_xy(s: str) -> Tuple[int, int]:
    return FILES.index(s[0]), RANKS.index(s[1])

def xy_to_sq(x: int, y: int) -> str:
    return FILES[x] + RANKS[y]

def in_bounds(x: int, y: int) -> bool:
    return 0 <= x < 8 and 0 <= y < 8

def color_of(piece: str) -> str:
    return piece[0]

def type_of(piece: str) -> str:
    return piece[1]

def opp(color: str) -> str:
    return 'b' if color == 'w' else 'w'

def side_char(to_play: str) -> str:
    return 'w' if to_play == 'white' else 'b'

def uci_move(frm: str, to: str, promo: Optional[str] = None) -> str:
    return frm + to + (promo.lower() if promo else "")

def clone_board(board: Dict[str, str]) -> Dict[str, str]:
    return dict(board)

def king_square(board: Dict[str, str], color: str) -> Optional[str]:
    target = color + 'K'
    for sq, pc in board.items():
        if pc == target:
            return sq
    return None

def is_square_attacked(board: Dict[str, str], sq: str, by_color: str) -> bool:
    x, y = sq_to_xy(sq)

    # Pawns
    dy = 1 if by_color == 'w' else -1
    for dx in (-1, 1):
        xx, yy = x - dx, y - dy
        if in_bounds(xx, yy):
            p = board.get(xy_to_sq(xx, yy))
            if p == by_color + 'P':
                return True

    # Knights
    for dx, dy2 in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
        xx, yy = x + dx, y + dy2
        if in_bounds(xx, yy):
            p = board.get(xy_to_sq(xx, yy))
            if p == by_color + 'N':
                return True

    # Bishops / Queens
    for dx, dy2 in [(-1,-1),(-1,1),(1,-1),(1,1)]:
        xx, yy = x + dx, y + dy2
        while in_bounds(xx, yy):
            p = board.get(xy_to_sq(xx, yy))
            if p:
                if color_of(p) == by_color and type_of(p) in ('B', 'Q'):
                    return True
                break
            xx += dx
            yy += dy2

    # Rooks / Queens
    for dx, dy2 in [(-1,0),(1,0),(0,-1),(0,1)]:
        xx, yy = x + dx, y + dy2
        while in_bounds(xx, yy):
            p = board.get(xy_to_sq(xx, yy))
            if p:
                if color_of(p) == by_color and type_of(p) in ('R', 'Q'):
                    return True
                break
            xx += dx
            yy += dy2

    # King
    for dx in (-1, 0, 1):
        for dy2 in (-1, 0, 1):
            if dx == 0 and dy2 == 0:
                continue
            xx, yy = x + dx, y + dy2
            if in_bounds(xx, yy):
                p = board.get(xy_to_sq(xx, yy))
                if p == by_color + 'K':
                    return True

    return False

def in_check(board: Dict[str, str], color: str) -> bool:
    ks = king_square(board, color)
    if ks is None:
        return True
    return is_square_attacked(board, ks, opp(color))

def infer_en_passant(board: Dict[str, str], color: str) -> List[str]:
    moves = []
    # Infer only from static board shape: enemy pawn appears on 5th rank (for white to capture) or 4th rank (for black to capture),
    # with an adjacent pawn able to capture onto the empty square behind it.
    # This is not perfect but legal only when resulting move passes king-safety.
    enemy = opp(color)
    if color == 'w':
        for file_idx in range(8):
            sq = xy_to_sq(file_idx, 4)  # rank 5
            if board.get(sq) == 'bP':
                for dx in (-1, 1):
                    fx = file_idx + dx
                    if in_bounds(fx, 4):
                        frm = xy_to_sq(fx, 4)
                        if board.get(frm) == 'wP':
                            to = xy_to_sq(file_idx, 5)
                            if to not in board:
                                moves.append(uci_move(frm, to))
    else:
        for file_idx in range(8):
            sq = xy_to_sq(file_idx, 3)  # rank 4
            if board.get(sq) == 'wP':
                for dx in (-1, 1):
                    fx = file_idx + dx
                    if in_bounds(fx, 3):
                        frm = xy_to_sq(fx, 3)
                        if board.get(frm) == 'bP':
                            to = xy_to_sq(file_idx, 2)
                            if to not in board:
                                moves.append(uci_move(frm, to))
    return moves

def pseudo_moves(board: Dict[str, str], color: str) -> List[str]:
    moves = []
    for frm, piece in board.items():
        if color_of(piece) != color:
            continue
        pt = type_of(piece)
        x, y = sq_to_xy(frm)

        if pt == 'P':
            diry = 1 if color == 'w' else -1
            start_rank = 1 if color == 'w' else 6
            promo_rank = 7 if color == 'w' else 0

            ny = y + diry
            if in_bounds(x, ny):
                to = xy_to_sq(x, ny)
                if to not in board:
                    if ny == promo_rank:
                        for pr in ('q', 'r', 'b', 'n'):
                            moves.append(uci_move(frm, to, pr))
                    else:
                        moves.append(uci_move(frm, to))
                    if y == start_rank:
                        ny2 = y + 2 * diry
                        to2 = xy_to_sq(x, ny2)
                        if in_bounds(x, ny2) and to2 not in board:
                            moves.append(uci_move(frm, to2))

            for dx in (-1, 1):
                nx = x + dx
                ny = y + diry
                if in_bounds(nx, ny):
                    to = xy_to_sq(nx, ny)
                    target = board.get(to)
                    if target and color_of(target) != color:
                        if ny == promo_rank:
                            for pr in ('q', 'r', 'b', 'n'):
                                moves.append(uci_move(frm, to, pr))
                        else:
                            moves.append(uci_move(frm, to))

        elif pt == 'N':
            for dx, dy in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
                nx, ny = x + dx, y + dy
                if in_bounds(nx, ny):
                    to = xy_to_sq(nx, ny)
                    target = board.get(to)
                    if not target or color_of(target) != color:
                        moves.append(uci_move(frm, to))

        elif pt in ('B', 'R', 'Q'):
            dirs = []
            if pt in ('B', 'Q'):
                dirs += [(-1,-1),(-1,1),(1,-1),(1,1)]
            if pt in ('R', 'Q'):
                dirs += [(-1,0),(1,0),(0,-1),(0,1)]
            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                while in_bounds(nx, ny):
                    to = xy_to_sq(nx, ny)
                    target = board.get(to)
                    if not target:
                        moves.append(uci_move(frm, to))
                    else:
                        if color_of(target) != color:
                            moves.append(uci_move(frm, to))
                        break
                    nx += dx
                    ny += dy

        elif pt == 'K':
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = x + dx, y + dy
                    if in_bounds(nx, ny):
                        to = xy_to_sq(nx, ny)
                        target = board.get(to)
                        if not target or color_of(target) != color:
                            moves.append(uci_move(frm, to))

            # Castling inference
            if color == 'w' and frm == 'e1':
                if board.get('h1') == 'wR' and 'f1' not in board and 'g1' not in board:
                    if not is_square_attacked(board, 'e1', 'b') and not is_square_attacked(board, 'f1', 'b') and not is_square_attacked(board, 'g1', 'b'):
                        moves.append('e1g1')
                if board.get('a1') == 'wR' and 'b1' not in board and 'c1' not in board and 'd1' not in board:
                    if not is_square_attacked(board, 'e1', 'b') and not is_square_attacked(board, 'd1', 'b') and not is_square_attacked(board, 'c1', 'b'):
                        moves.append('e1c1')
            elif color == 'b' and frm == 'e8':
                if board.get('h8') == 'bR' and 'f8' not in board and 'g8' not in board:
                    if not is_square_attacked(board, 'e8', 'w') and not is_square_attacked(board, 'f8', 'w') and not is_square_attacked(board, 'g8', 'w'):
                        moves.append('e8g8')
                if board.get('a8') == 'bR' and 'b8' not in board and 'c8' not in board and 'd8' not in board:
                    if not is_square_attacked(board, 'e8', 'w') and not is_square_attacked(board, 'd8', 'w') and not is_square_attacked(board, 'c8', 'w'):
                        moves.append('e8c8')

    moves.extend(infer_en_passant(board, color))
    return moves

def apply_move(board: Dict[str, str], move: str, color: str) -> Dict[str, str]:
    b = dict(board)
    frm, to = move[:2], move[2:4]
    promo = move[4] if len(move) > 4 else None
    piece = b.get(frm)
    if piece is None:
        return b

    pt = type_of(piece)

    # Castling
    if pt == 'K' and frm == 'e1' and to == 'g1':
        b.pop('e1', None)
        b.pop('h1', None)
        b['g1'] = 'wK'
        b['f1'] = 'wR'
        return b
    if pt == 'K' and frm == 'e1' and to == 'c1':
        b.pop('e1', None)
        b.pop('a1', None)
        b['c1'] = 'wK'
        b['d1'] = 'wR'
        return b
    if pt == 'K' and frm == 'e8' and to == 'g8':
        b.pop('e8', None)
        b.pop('h8', None)
        b['g8'] = 'bK'
        b['f8'] = 'bR'
        return b
    if pt == 'K' and frm == 'e8' and to == 'c8':
        b.pop('e8', None)
        b.pop('a8', None)
        b['c8'] = 'bK'
        b['d8'] = 'bR'
        return b

    # En passant
    if pt == 'P' and frm[0] != to[0] and to not in b:
        fx, fy = sq_to_xy(frm)
        tx, ty = sq_to_xy(to)
        if abs(tx - fx) == 1:
            cap_sq = xy_to_sq(tx, fy)
            if b.get(cap_sq) == opp(color) + 'P':
                b.pop(cap_sq, None)

    b.pop(frm, None)
    b.pop(to, None)
    if promo and pt == 'P':
        b[to] = color + promo.upper()
    else:
        b[to] = piece
    return b

def legal_moves(board: Dict[str, str], color: str) -> List[str]:
    result = []
    for mv in pseudo_moves(board, color):
        nb = apply_move(board, mv, color)
        if not in_check(nb, color):
            result.append(mv)
    return result

def move_gives_check(board: Dict[str, str], move: str, color: str) -> bool:
    nb = apply_move(board, move, color)
    return in_check(nb, opp(color))

def move_score_order(board: Dict[str, str], move: str, color: str) -> int:
    frm, to = move[:2], move[2:4]
    piece = board.get(frm)
    if not piece:
        return 0
    score = 0
    target = board.get(to)
    if target:
        score += 10 * PIECE_VALUES[type_of(target)] - PIECE_VALUES[type_of(piece)]
    if len(move) > 4:
        score += 800
    if move_gives_check(board, move, color):
        score += 120
    pt = type_of(piece)
    if pt == 'P':
        _, ty = sq_to_xy(to)
        score += (ty if color == 'w' else (7 - ty)) * 8
    return score

def psq_value(pt: str, x: int, y: int, color: str, endgame: bool) -> int:
    idx = y * 8 + x
    if color == 'b':
        idx = (7 - y) * 8 + x
    if pt == 'N':
        return KNIGHT_PSQ[idx]
    if pt == 'B':
        return BISHOP_PSQ[idx]
    if pt == 'R':
        return ROOK_PSQ[idx]
    if pt == 'Q':
        return QUEEN_PSQ[idx]
    if pt == 'K':
        return (KING_END_PSQ if endgame else KING_MID_PSQ)[idx]
    if pt == 'P':
        advance = y if color == 'w' else (7 - y)
        center = 3 - abs(3.5 - x)
        return int(advance * 10 + center * 4)
    return 0

def evaluate(board: Dict[str, str], color: str) -> int:
    total_material = 0
    white = 0
    black = 0
    for sq, piece in board.items():
        val = PIECE_VALUES[type_of(piece)]
        total_material += val
        if color_of(piece) == 'w':
            white += val
        else:
            black += val
    endgame = total_material < 2600

    score = 0
    for sq, piece in board.items():
        x, y = sq_to_xy(sq)
        c = color_of(piece)
        pt = type_of(piece)
        val = PIECE_VALUES[pt]
        v = val + psq_value(pt, x, y, c, endgame)
        if pt == 'P':
            advance = y if c == 'w' else (7 - y)
            v += advance * 6
        if c == color:
            score += v
        else:
            score -= v

    my_moves = legal_moves(board, color)
    opp_moves = legal_moves(board, opp(color))
    score += 3 * (len(my_moves) - len(opp_moves))

    if in_check(board, opp(color)):
        score += 40
    if in_check(board, color):
        score -= 50

    return score

def search(board: Dict[str, str], color: str, depth: int, alpha: int, beta: int, root_color: str) -> Tuple[int, Optional[str]]:
    moves = legal_moves(board, color)
    if not moves:
        if in_check(board, color):
            mate_score = -100000 + (4 - depth)
            return (mate_score if color == root_color else -mate_score), None
        return 0, None

    if depth == 0:
        return evaluate(board, root_color), None

    moves.sort(key=lambda m: move_score_order(board, m, color), reverse=True)

    best_move = moves[0]
    if color == root_color:
        best = -10**9
        for mv in moves:
            nb = apply_move(board, mv, color)
            sc, _ = search(nb, opp(color), depth - 1, alpha, beta, root_color)
            if sc > best:
                best = sc
                best_move = mv
            alpha = max(alpha, best)
            if beta <= alpha:
                break
        return best, best_move
    else:
        best = 10**9
        for mv in moves:
            nb = apply_move(board, mv, color)
            sc, _ = search(nb, opp(color), depth - 1, alpha, beta, root_color)
            if sc < best:
                best = sc
                best_move = mv
            beta = min(beta, best)
            if beta <= alpha:
                break
        return best, best_move

def policy(pieces: Dict[str, str], to_play: str) -> str:
    board = dict(pieces)
    color = side_char(to_play)
    moves = legal_moves(board, color)
    if not moves:
        # Should not happen in valid arena states, but must always return a string.
        return "a1a1"

    # 1. Immediate mate
    mating = []
    for mv in moves:
        nb = apply_move(board, mv, color)
        opp_legal = legal_moves(nb, opp(color))
        if not opp_legal and in_check(nb, opp(color)):
            mating.append(mv)
    if mating:
        mating.sort(key=lambda m: move_score_order(board, m, color), reverse=True)
        return mating[0]

    # 2. Avoid moves allowing immediate mate if alternatives exist
    safe_moves = []
    for mv in moves:
        nb = apply_move(board, mv, color)
        bad = False
        for omv in legal_moves(nb, opp(color)):
            nnb = apply_move(nb, omv, opp(color))
            our = legal_moves(nnb, color)
            if not our and in_check(nnb, color):
                bad = True
                break
        if not bad:
            safe_moves.append(mv)
    if safe_moves:
        moves = safe_moves

    # 3. Search
    depth = 3
    if len(moves) <= 12:
        depth = 4
    _, best = search(board, color, depth, -10**9, 10**9, color)
    if best in moves:
        return best

    # 4. Tactical fallback
    moves.sort(key=lambda m: move_score_order(board, m, color), reverse=True)
    return moves[0]
