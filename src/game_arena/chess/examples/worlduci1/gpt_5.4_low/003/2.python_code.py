
from typing import Dict, List, Tuple, Optional

FILES = "abcdefgh"
RANKS = "12345678"

PIECE_VALUE = {
    "P": 100,
    "N": 320,
    "B": 330,
    "R": 500,
    "Q": 900,
    "K": 0,
}

KNIGHT_DIRS = [(1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2)]
KING_DIRS = [(1, 1), (1, 0), (1, -1), (0, 1), (0, -1), (-1, 1), (-1, 0), (-1, -1)]
BISHOP_DIRS = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
ROOK_DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]
QUEEN_DIRS = BISHOP_DIRS + ROOK_DIRS

CENTER_BONUS = {
    "d4": 12, "e4": 12, "d5": 12, "e5": 12,
    "c3": 8, "d3": 8, "e3": 8, "f3": 8,
    "c4": 8, "f4": 8, "c5": 8, "f5": 8,
    "c6": 8, "d6": 8, "e6": 8, "f6": 8,
}

MATE_SCORE = 1000000


def sq_to_xy(sq: str) -> Tuple[int, int]:
    return FILES.index(sq[0]), RANKS.index(sq[1])


def xy_to_sq(x: int, y: int) -> str:
    return FILES[x] + RANKS[y]


def on_board(x: int, y: int) -> bool:
    return 0 <= x < 8 and 0 <= y < 8


def color_of(piece: str) -> str:
    return piece[0]


def type_of(piece: str) -> str:
    return piece[1]


def side_char(to_play: str) -> str:
    return "w" if to_play == "white" else "b"


def opp(c: str) -> str:
    return "b" if c == "w" else "w"


def king_square(board: Dict[str, str], side: str) -> Optional[str]:
    target = side + "K"
    for sq, p in board.items():
        if p == target:
            return sq
    return None


def is_square_attacked(board: Dict[str, str], sq: str, by_side: str) -> bool:
    x, y = sq_to_xy(sq)

    # Pawn attacks
    if by_side == "w":
        for dx in (-1, 1):
            xx, yy = x + dx, y - 1
            if on_board(xx, yy):
                p = board.get(xy_to_sq(xx, yy))
                if p == "wP":
                    return True
    else:
        for dx in (-1, 1):
            xx, yy = x + dx, y + 1
            if on_board(xx, yy):
                p = board.get(xy_to_sq(xx, yy))
                if p == "bP":
                    return True

    # Knight attacks
    for dx, dy in KNIGHT_DIRS:
        xx, yy = x + dx, y + dy
        if on_board(xx, yy):
            p = board.get(xy_to_sq(xx, yy))
            if p == by_side + "N":
                return True

    # Bishop / Queen diagonals
    for dx, dy in BISHOP_DIRS:
        xx, yy = x + dx, y + dy
        while on_board(xx, yy):
            p = board.get(xy_to_sq(xx, yy))
            if p:
                if color_of(p) == by_side and type_of(p) in ("B", "Q"):
                    return True
                break
            xx += dx
            yy += dy

    # Rook / Queen lines
    for dx, dy in ROOK_DIRS:
        xx, yy = x + dx, y + dy
        while on_board(xx, yy):
            p = board.get(xy_to_sq(xx, yy))
            if p:
                if color_of(p) == by_side and type_of(p) in ("R", "Q"):
                    return True
                break
            xx += dx
            yy += dy

    # King attacks
    for dx, dy in KING_DIRS:
        xx, yy = x + dx, y + dy
        if on_board(xx, yy):
            p = board.get(xy_to_sq(xx, yy))
            if p == by_side + "K":
                return True

    return False


def in_check(board: Dict[str, str], side: str) -> bool:
    ks = king_square(board, side)
    if ks is None:
        return True
    return is_square_attacked(board, ks, opp(side))


def make_move(board: Dict[str, str], move: str) -> Dict[str, str]:
    newb = dict(board)
    frm = move[:2]
    to = move[2:4]
    promo = move[4] if len(move) == 5 else None
    piece = newb.pop(frm)
    if to in newb:
        del newb[to]
    if promo:
        newb[to] = color_of(piece) + promo.upper()
    else:
        newb[to] = piece
    return newb


def pseudo_moves_for_piece(board: Dict[str, str], sq: str, piece: str) -> List[str]:
    moves = []
    side = color_of(piece)
    ptype = type_of(piece)
    x, y = sq_to_xy(sq)

    if ptype == "P":
        direction = 1 if side == "w" else -1
        start_rank = 1 if side == "w" else 6
        promote_rank = 7 if side == "w" else 0

        # One step
        ny = y + direction
        if on_board(x, ny):
            to = xy_to_sq(x, ny)
            if to not in board:
                if ny == promote_rank:
                    for pr in "qrbn":
                        moves.append(sq + to + pr)
                else:
                    moves.append(sq + to)
                    # Two step
                    if y == start_rank:
                        nny = y + 2 * direction
                        to2 = xy_to_sq(x, nny)
                        if on_board(x, nny) and to2 not in board:
                            moves.append(sq + to2)

        # Captures
        for dx in (-1, 1):
            nx, ny = x + dx, y + direction
            if on_board(nx, ny):
                to = xy_to_sq(nx, ny)
                if to in board and color_of(board[to]) != side:
                    if ny == promote_rank:
                        for pr in "qrbn":
                            moves.append(sq + to + pr)
                    else:
                        moves.append(sq + to)

    elif ptype == "N":
        for dx, dy in KNIGHT_DIRS:
            nx, ny = x + dx, y + dy
            if on_board(nx, ny):
                to = xy_to_sq(nx, ny)
                if to not in board or color_of(board[to]) != side:
                    moves.append(sq + to)

    elif ptype == "B":
        for dx, dy in BISHOP_DIRS:
            nx, ny = x + dx, y + dy
            while on_board(nx, ny):
                to = xy_to_sq(nx, ny)
                if to in board:
                    if color_of(board[to]) != side:
                        moves.append(sq + to)
                    break
                moves.append(sq + to)
                nx += dx
                ny += dy

    elif ptype == "R":
        for dx, dy in ROOK_DIRS:
            nx, ny = x + dx, y + dy
            while on_board(nx, ny):
                to = xy_to_sq(nx, ny)
                if to in board:
                    if color_of(board[to]) != side:
                        moves.append(sq + to)
                    break
                moves.append(sq + to)
                nx += dx
                ny += dy

    elif ptype == "Q":
        for dx, dy in QUEEN_DIRS:
            nx, ny = x + dx, y + dy
            while on_board(nx, ny):
                to = xy_to_sq(nx, ny)
                if to in board:
                    if color_of(board[to]) != side:
                        moves.append(sq + to)
                    break
                moves.append(sq + to)
                nx += dx
                ny += dy

    elif ptype == "K":
        for dx, dy in KING_DIRS:
            nx, ny = x + dx, y + dy
            if on_board(nx, ny):
                to = xy_to_sq(nx, ny)
                if to not in board or color_of(board[to]) != side:
                    moves.append(sq + to)

    return moves


def legal_moves(board: Dict[str, str], side: str) -> List[str]:
    out = []
    for sq, piece in board.items():
        if color_of(piece) != side:
            continue
        for mv in pseudo_moves_for_piece(board, sq, piece):
            nb = make_move(board, mv)
            if not in_check(nb, side):
                out.append(mv)
    return out


def move_score_heuristic(board: Dict[str, str], move: str) -> int:
    frm = move[:2]
    to = move[2:4]
    piece = board[frm]
    score = 0

    if to in board:
        score += 10 * PIECE_VALUE[type_of(board[to])] - PIECE_VALUE[type_of(piece)]
    if len(move) == 5:
        promo_piece = move[4].upper()
        score += PIECE_VALUE[promo_piece] + 500
    score += CENTER_BONUS.get(to, 0)
    return score


def evaluate(board: Dict[str, str], side: str) -> int:
    my_side = side
    their_side = opp(side)
    score = 0

    # Material + piece-square-ish bonuses
    for sq, p in board.items():
        val = PIECE_VALUE[type_of(p)]
        x, y = sq_to_xy(sq)

        # Mild positional bonuses
        pos = CENTER_BONUS.get(sq, 0)

        if type_of(p) == "P":
            advance = y if color_of(p) == "w" else (7 - y)
            pos += advance * 6
        elif type_of(p) == "N":
            pos += 14 - 2 * (abs(3.5 - x) + abs(3.5 - y))
        elif type_of(p) == "B":
            pos += 8 - (abs(3.5 - x) + abs(3.5 - y))
        elif type_of(p) == "R":
            pos += 2 * (y if color_of(p) == "w" else (7 - y))
        elif type_of(p) == "Q":
            pos += 4 - 0.5 * (abs(3.5 - x) + abs(3.5 - y))
        elif type_of(p) == "K":
            # Slight preference for safer edge/corner in middlegame-like positions
            pos -= 3 * (3.5 - abs(3.5 - x))
            pos -= 3 * (3.5 - abs(3.5 - y))

        if color_of(p) == my_side:
            score += val + int(pos)
        else:
            score -= val + int(pos)

    # Mobility
    my_moves = len(legal_moves(board, my_side))
    op_moves = len(legal_moves(board, their_side))
    score += 4 * (my_moves - op_moves)

    # Check pressure
    if in_check(board, their_side):
        score += 35
    if in_check(board, my_side):
        score -= 35

    return score


def negamax(board: Dict[str, str], side: str, depth: int, alpha: int, beta: int) -> int:
    moves = legal_moves(board, side)

    if not moves:
        if in_check(board, side):
            return -MATE_SCORE + (10 - depth)
        return 0

    if depth == 0:
        return evaluate(board, side)

    moves.sort(key=lambda m: move_score_heuristic(board, m), reverse=True)

    best = -10**9
    for mv in moves:
        nb = make_move(board, mv)
        val = -negamax(nb, opp(side), depth - 1, -beta, -alpha)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best


def choose_move(board: Dict[str, str], side: str) -> str:
    moves = legal_moves(board, side)
    if not moves:
        return ""

    moves.sort(key=lambda m: move_score_heuristic(board, m), reverse=True)

    # 1. Immediate mate if available
    for mv in moves:
        nb = make_move(board, mv)
        opp_moves = legal_moves(nb, opp(side))
        if not opp_moves and in_check(nb, opp(side)):
            return mv

    # 2. Avoid immediate self-loss / detect tactical wins
    best_move = moves[0]
    best_score = -10**9

    # Adaptive depth: keep it small for speed
    piece_count = len(board)
    depth = 3 if piece_count <= 10 else 2

    alpha = -10**9
    beta = 10**9

    for mv in moves:
        nb = make_move(board, mv)
        val = -negamax(nb, opp(side), depth - 1, -beta, -alpha)

        # Small direct bonuses
        to = mv[2:4]
        if to in board:
            val += PIECE_VALUE[type_of(board[to])] // 8
        if len(mv) == 5:
            val += 80

        if val > best_score:
            best_score = val
            best_move = mv
        if val > alpha:
            alpha = val

    return best_move


def policy(pieces: dict[str, str], to_play: str) -> str:
    board = dict(pieces)
    side = side_char(to_play)

    try:
        moves = legal_moves(board, side)
        if moves:
            return choose_move(board, side)
    except Exception:
        pass

    # Emergency fallback: return any syntactically legal move we can find
    try:
        for sq, p in board.items():
            if color_of(p) == side:
                pm = pseudo_moves_for_piece(board, sq, p)
                for mv in pm:
                    nb = make_move(board, mv)
                    if not in_check(nb, side):
                        return mv
    except Exception:
        pass

    # Last-resort fallback if position is somehow malformed:
    # try to return something deterministic, though this should almost never happen.
    for sq, p in board.items():
        if color_of(p) == side:
            x, y = sq_to_xy(sq)
            for dx, dy in KING_DIRS + KNIGHT_DIRS + QUEEN_DIRS:
                nx, ny = x + dx, y + dy
                if on_board(nx, ny):
                    mv = sq + xy_to_sq(nx, ny)
                    return mv

    return "a1a1"
