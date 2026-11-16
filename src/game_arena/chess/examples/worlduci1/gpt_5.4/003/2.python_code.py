
from __future__ import annotations

from typing import Dict, List, Tuple, Optional

FILES = "abcdefgh"
RANKS = "12345678"
INF = 10**9

PIECE_VALUE = {
    "K": 0,
    "Q": 900,
    "R": 500,
    "B": 330,
    "N": 320,
    "P": 100,
}

PST = {
    "P": [
          0,   0,   0,   0,   0,   0,   0,   0,
         50,  50,  50,  50,  50,  50,  50,  50,
         10,  10,  20,  30,  30,  20,  10,  10,
          5,   5,  10,  25,  25,  10,   5,   5,
          0,   0,   0,  20,  20,   0,   0,   0,
          5,  -5, -10,   0,   0, -10,  -5,   5,
          5,  10,  10, -20, -20,  10,  10,   5,
          0,   0,   0,   0,   0,   0,   0,   0,
    ],
    "N": [
        -50, -40, -30, -30, -30, -30, -40, -50,
        -40, -20,   0,   5,   5,   0, -20, -40,
        -30,   5,  10,  15,  15,  10,   5, -30,
        -30,   0,  15,  20,  20,  15,   0, -30,
        -30,   5,  15,  20,  20,  15,   5, -30,
        -30,   0,  10,  15,  15,  10,   0, -30,
        -40, -20,   0,   0,   0,   0, -20, -40,
        -50, -40, -30, -30, -30, -30, -40, -50,
    ],
    "B": [
        -20, -10, -10, -10, -10, -10, -10, -20,
        -10,   5,   0,   0,   0,   0,   5, -10,
        -10,  10,  10,  10,  10,  10,  10, -10,
        -10,   0,  10,  10,  10,  10,   0, -10,
        -10,   5,   5,  10,  10,   5,   5, -10,
        -10,   0,   5,  10,  10,   5,   0, -10,
        -10,   0,   0,   0,   0,   0,   0, -10,
        -20, -10, -10, -10, -10, -10, -10, -20,
    ],
    "R": [
          0,   0,   0,   5,   5,   0,   0,   0,
         -5,   0,   0,   0,   0,   0,   0,  -5,
         -5,   0,   0,   0,   0,   0,   0,  -5,
         -5,   0,   0,   0,   0,   0,   0,  -5,
         -5,   0,   0,   0,   0,   0,   0,  -5,
         -5,   0,   0,   0,   0,   0,   0,  -5,
          5,  10,  10,  10,  10,  10,  10,   5,
          0,   0,   0,   0,   0,   0,   0,   0,
    ],
    "Q": [
        -20, -10, -10,  -5,  -5, -10, -10, -20,
        -10,   0,   0,   0,   0,   0,   0, -10,
        -10,   0,   5,   5,   5,   5,   0, -10,
         -5,   0,   5,   5,   5,   5,   0,  -5,
          0,   0,   5,   5,   5,   5,   0,  -5,
        -10,   5,   5,   5,   5,   5,   0, -10,
        -10,   0,   5,   0,   0,   0,   0, -10,
        -20, -10, -10,  -5,  -5, -10, -10, -20,
    ],
    "K": [
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -20, -30, -30, -40, -40, -30, -30, -20,
        -10, -20, -20, -20, -20, -20, -20, -10,
         20,  20,   0,   0,   0,   0,  20,  20,
         20,  30,  10,   0,   0,  10,  30,  20,
    ],
}

ENDGAME_KING = [
    -50, -40, -30, -20, -20, -30, -40, -50,
    -30, -20, -10,   0,   0, -10, -20, -30,
    -30, -10,  20,  30,  30,  20, -10, -30,
    -30, -10,  30,  40,  40,  30, -10, -30,
    -30, -10,  30,  40,  40,  30, -10, -30,
    -30, -10,  20,  30,  30,  20, -10, -30,
    -30, -30,   0,   0,   0,   0, -30, -30,
    -50, -30, -30, -30, -30, -30, -30, -50,
]


def sq_to_xy(s: str) -> Tuple[int, int]:
    return ord(s[0]) - 97, ord(s[1]) - 49


def xy_to_sq(x: int, y: int) -> str:
    return chr(97 + x) + chr(49 + y)


def on_board(x: int, y: int) -> bool:
    return 0 <= x < 8 and 0 <= y < 8


def idx(x: int, y: int) -> int:
    return y * 8 + x


def mirror_index(i: int) -> int:
    x = i % 8
    y = i // 8
    return (7 - y) * 8 + x


class Position:
    __slots__ = ("board", "side", "castle", "ep")

    def __init__(self, board: Dict[str, str], side: str, castle: str = "", ep: Optional[str] = None):
        self.board = board
        self.side = side
        self.castle = castle
        self.ep = ep

    def copy(self) -> "Position":
        return Position(dict(self.board), self.side, self.castle, self.ep)


def infer_castling_rights(board: Dict[str, str]) -> str:
    rights = ""
    if board.get("e1") == "wK":
        if board.get("h1") == "wR":
            rights += "K"
        if board.get("a1") == "wR":
            rights += "Q"
    if board.get("e8") == "bK":
        if board.get("h8") == "bR":
            rights += "k"
        if board.get("a8") == "bR":
            rights += "q"
    return rights


def infer_ep(board: Dict[str, str], side: str) -> Optional[str]:
    mover = "w" if side == "white" else "b"
    enemy = "b" if mover == "w" else "w"
    if mover == "w":
        candidates = []
        for sq, p in board.items():
            if p == enemy + "P":
                x, y = sq_to_xy(sq)
                if y == 4:
                    for dx in (-1, 1):
                        nx = x + dx
                        if on_board(nx, 4):
                            if board.get(xy_to_sq(nx, 4)) == "wP":
                                candidates.append(xy_to_sq(x, 5))
        if len(candidates) == 1:
            return candidates[0]
    else:
        candidates = []
        for sq, p in board.items():
            if p == enemy + "P":
                x, y = sq_to_xy(sq)
                if y == 3:
                    for dx in (-1, 1):
                        nx = x + dx
                        if on_board(nx, 3):
                            if board.get(xy_to_sq(nx, 3)) == "bP":
                                candidates.append(xy_to_sq(x, 2))
        if len(candidates) == 1:
            return candidates[0]
    return None


def king_square(board: Dict[str, str], color: str) -> Optional[str]:
    target = color + "K"
    for sq, p in board.items():
        if p == target:
            return sq
    return None


def is_attacked(board: Dict[str, str], sq: str, by_color: str) -> bool:
    x, y = sq_to_xy(sq)

    pawn_dir = 1 if by_color == "w" else -1
    py = y - pawn_dir
    for dx in (-1, 1):
        px = x + dx
        if on_board(px, py):
            if board.get(xy_to_sq(px, py)) == by_color + "P":
                return True

    for dx, dy in ((1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2)):
        nx, ny = x + dx, y + dy
        if on_board(nx, ny):
            if board.get(xy_to_sq(nx, ny)) == by_color + "N":
                return True

    for dx, dy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        nx, ny = x + dx, y + dy
        while on_board(nx, ny):
            piece = board.get(xy_to_sq(nx, ny))
            if piece:
                if piece[0] == by_color and piece[1] in ("B", "Q"):
                    return True
                break
            nx += dx
            ny += dy

    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nx, ny = x + dx, y + dy
        while on_board(nx, ny):
            piece = board.get(xy_to_sq(nx, ny))
            if piece:
                if piece[0] == by_color and piece[1] in ("R", "Q"):
                    return True
                break
            nx += dx
            ny += dy

    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            nx, ny = x + dx, y + dy
            if on_board(nx, ny):
                if board.get(xy_to_sq(nx, ny)) == by_color + "K":
                    return True

    return False


def in_check(pos: Position, color: str) -> bool:
    ks = king_square(pos.board, color)
    if ks is None:
        return True
    return is_attacked(pos.board, ks, "b" if color == "w" else "w")


def gen_pseudo_moves(pos: Position, captures_only: bool = False) -> List[str]:
    board = pos.board
    color = "w" if pos.side == "white" else "b"
    enemy = "b" if color == "w" else "w"
    moves: List[str] = []

    for from_sq, piece in list(board.items()):
        if piece[0] != color:
            continue
        p = piece[1]
        x, y = sq_to_xy(from_sq)

        if p == "P":
            diry = 1 if color == "w" else -1
            start_rank = 1 if color == "w" else 6
            promo_rank = 7 if color == "w" else 0

            ny = y + diry
            if not captures_only and on_board(x, ny):
                to_sq = xy_to_sq(x, ny)
                if to_sq not in board:
                    if ny == promo_rank:
                        for pr in "qrbn":
                            moves.append(from_sq + to_sq + pr)
                    else:
                        moves.append(from_sq + to_sq)
                    ny2 = y + 2 * diry
                    to_sq2 = xy_to_sq(x, ny2) if on_board(x, ny2) else None
                    if y == start_rank and to_sq2 and to_sq2 not in board:
                        moves.append(from_sq + to_sq2)

            for dx in (-1, 1):
                nx = x + dx
                ny = y + diry
                if not on_board(nx, ny):
                    continue
                to_sq = xy_to_sq(nx, ny)
                target = board.get(to_sq)
                if target and target[0] == enemy:
                    if ny == promo_rank:
                        for pr in "qrbn":
                            moves.append(from_sq + to_sq + pr)
                    else:
                        moves.append(from_sq + to_sq)
                elif pos.ep == to_sq:
                    cap_sq = xy_to_sq(nx, y)
                    if board.get(cap_sq) == enemy + "P":
                        moves.append(from_sq + to_sq)

        elif p == "N":
            for dx, dy in ((1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2)):
                nx, ny = x + dx, y + dy
                if not on_board(nx, ny):
                    continue
                to_sq = xy_to_sq(nx, ny)
                target = board.get(to_sq)
                if target is None:
                    if not captures_only:
                        moves.append(from_sq + to_sq)
                elif target[0] == enemy:
                    moves.append(from_sq + to_sq)

        elif p in ("B", "R", "Q"):
            dirs = []
            if p in ("B", "Q"):
                dirs += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
            if p in ("R", "Q"):
                dirs += [(1, 0), (-1, 0), (0, 1), (0, -1)]
            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                while on_board(nx, ny):
                    to_sq = xy_to_sq(nx, ny)
                    target = board.get(to_sq)
                    if target is None:
                        if not captures_only:
                            moves.append(from_sq + to_sq)
                    else:
                        if target[0] == enemy:
                            moves.append(from_sq + to_sq)
                        break
                    nx += dx
                    ny += dy

        elif p == "K":
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = x + dx, y + dy
                    if not on_board(nx, ny):
                        continue
                    to_sq = xy_to_sq(nx, ny)
                    target = board.get(to_sq)
                    if target is None:
                        if not captures_only:
                            moves.append(from_sq + to_sq)
                    elif target[0] == enemy:
                        moves.append(from_sq + to_sq)

            if not captures_only:
                if color == "w" and from_sq == "e1":
                    if "K" in pos.castle and board.get("f1") is None and board.get("g1") is None:
                        if not is_attacked(board, "e1", "b") and not is_attacked(board, "f1", "b") and not is_attacked(board, "g1", "b"):
                            if board.get("h1") == "wR":
                                moves.append("e1g1")
                    if "Q" in pos.castle and board.get("d1") is None and board.get("c1") is None and board.get("b1") is None:
                        if not is_attacked(board, "e1", "b") and not is_attacked(board, "d1", "b") and not is_attacked(board, "c1", "b"):
                            if board.get("a1") == "wR":
                                moves.append("e1c1")
                elif color == "b" and from_sq == "e8":
                    if "k" in pos.castle and board.get("f8") is None and board.get("g8") is None:
                        if not is_attacked(board, "e8", "w") and not is_attacked(board, "f8", "w") and not is_attacked(board, "g8", "w"):
                            if board.get("h8") == "bR":
                                moves.append("e8g8")
                    if "q" in pos.castle and board.get("d8") is None and board.get("c8") is None and board.get("b8") is None:
                        if not is_attacked(board, "e8", "w") and not is_attacked(board, "d8", "w") and not is_attacked(board, "c8", "w"):
                            if board.get("a8") == "bR":
                                moves.append("e8c8")

    return moves


def make_move(pos: Position, move: str) -> Position:
    board = dict(pos.board)
    side = pos.side
    color = "w" if side == "white" else "b"
    enemy = "b" if color == "w" else "w"
    from_sq = move[:2]
    to_sq = move[2:4]
    promo = move[4] if len(move) == 5 else None
    piece = board.pop(from_sq)
    captured = board.get(to_sq)

    new_castle = pos.castle
    new_ep = None

    if piece[1] == "K":
        if color == "w":
            new_castle = new_castle.replace("K", "").replace("Q", "")
            if from_sq == "e1" and to_sq == "g1":
                board.pop("h1", None)
                board["f1"] = "wR"
            elif from_sq == "e1" and to_sq == "c1":
                board.pop("a1", None)
                board["d1"] = "wR"
        else:
            new_castle = new_castle.replace("k", "").replace("q", "")
            if from_sq == "e8" and to_sq == "g8":
                board.pop("h8", None)
                board["f8"] = "bR"
            elif from_sq == "e8" and to_sq == "c8":
                board.pop("a8", None)
                board["d8"] = "bR"

    if piece[1] == "R":
        if from_sq == "h1":
            new_castle = new_castle.replace("K", "")
        elif from_sq == "a1":
            new_castle = new_castle.replace("Q", "")
        elif from_sq == "h8":
            new_castle = new_castle.replace("k", "")
        elif from_sq == "a8":
            new_castle = new_castle.replace("q", "")

    if captured == "wR":
        if to_sq == "h1":
            new_castle = new_castle.replace("K", "")
        elif to_sq == "a1":
            new_castle = new_castle.replace("Q", "")
    elif captured == "bR":
        if to_sq == "h8":
            new_castle = new_castle.replace("k", "")
        elif to_sq == "a8":
            new_castle = new_castle.replace("q", "")

    if piece[1] == "P":
        fx, fy = sq_to_xy(from_sq)
        tx, ty = sq_to_xy(to_sq)
        if pos.ep == to_sq and fx != tx and to_sq not in board:
            cap_sq = xy_to_sq(tx, fy)
            board.pop(cap_sq, None)
        if abs(ty - fy) == 2:
            new_ep = xy_to_sq(fx, (fy + ty) // 2)

    board.pop(to_sq, None)
    if promo:
        board[to_sq] = color + promo.upper()
    else:
        board[to_sq] = piece

    return Position(board, "black" if side == "white" else "white", new_castle, new_ep)


def gen_legal_moves(pos: Position, captures_only: bool = False) -> List[str]:
    color = "w" if pos.side == "white" else "b"
    moves = []
    for mv in gen_pseudo_moves(pos, captures_only):
        nxt = make_move(pos, mv)
        if not in_check(nxt, color):
            moves.append(mv)
    return moves


def move_score(pos: Position, mv: str) -> int:
    board = pos.board
    from_sq = mv[:2]
    to_sq = mv[2:4]
    promo = mv[4] if len(mv) == 5 else None
    piece = board[from_sq]
    target = board.get(to_sq)
    score = 0

    if target:
        score += 10 * PIECE_VALUE[target[1]] - PIECE_VALUE[piece[1]]
    else:
        fx, fy = sq_to_xy(from_sq)
        tx, ty = sq_to_xy(to_sq)
        if piece[1] == "P" and fx != tx and pos.ep == to_sq:
            score += 10 * PIECE_VALUE["P"] - PIECE_VALUE["P"]

    if promo:
        score += PIECE_VALUE[promo.upper()] + 800

    nxt = make_move(pos, mv)
    enemy = "b" if piece[0] == "w" else "w"
    if in_check(nxt, enemy):
        score += 50

    if piece[1] == "K" and abs(ord(from_sq[0]) - ord(to_sq[0])) == 2:
        score += 40

    return score


def material_phase(board: Dict[str, str]) -> int:
    total = 0
    for p in board.values():
        if p[1] != "K":
            total += PIECE_VALUE[p[1]]
    return total


def evaluate(pos: Position) -> int:
    board = pos.board
    score = 0
    phase = material_phase(board)
    endgame = phase < 2200

    for sq, piece in board.items():
        color = 1 if piece[0] == "w" else -1
        p = piece[1]
        x, y = sq_to_xy(sq)
        i = idx(x, y)
        pst_i = i if piece[0] == "w" else mirror_index(i)

        score += color * PIECE_VALUE[p]
        if p == "K" and endgame:
            score += color * ENDGAME_KING[pst_i]
        else:
            score += color * PST[p][pst_i]

        if p == "P":
            advance = y if piece[0] == "w" else 7 - y
            score += color * advance * 8
            blocked = False
            for yy in range(y + (1 if piece[0] == "w" else -1), 8 if piece[0] == "w" else -1, 1 if piece[0] == "w" else -1):
                if board.get(xy_to_sq(x, yy)) == piece:
                    continue
            passed = True
            for fx in (x - 1, x, x + 1):
                if 0 <= fx < 8:
                    yy = y + (1 if piece[0] == "w" else -1)
                    while 0 <= yy < 8:
                        q = board.get(xy_to_sq(fx, yy))
                        if q == ("bP" if piece[0] == "w" else "wP"):
                            passed = False
                            break
                        yy += 1 if piece[0] == "w" else -1
                if not passed:
                    break
            if passed:
                score += color * (20 + advance * 12)

        elif p in ("N", "B"):
            if 2 <= x <= 5 and 2 <= y <= 5:
                score += color * 12
        elif p == "R":
            file_open = True
            for yy in range(8):
                q = board.get(xy_to_sq(x, yy))
                if q and q[1] == "P":
                    file_open = False
                    break
            if file_open:
                score += color * 18
        elif p == "Q":
            if 2 <= x <= 5 and 2 <= y <= 5:
                score += color * 6

    for color_char in ("w", "b"):
        ks = king_square(board, color_char)
        if ks:
            x, y = sq_to_xy(ks)
            shield = 0
            diry = 1 if color_char == "w" else -1
            home = 0 if color_char == "w" else 7
            if abs(y - home) <= 1:
                for dx in (-1, 0, 1):
                    nx, ny = x + dx, y + diry
                    if on_board(nx, ny):
                        if board.get(xy_to_sq(nx, ny)) == color_char + "P":
                            shield += 1
            score += (15 * shield) if color_char == "w" else (-15 * shield)

    side_mult = 1 if pos.side == "white" else -1
    return score * side_mult


def quiescence(pos: Position, alpha: int, beta: int, depth: int) -> int:
    stand = evaluate(pos)
    if stand >= beta:
        return beta
    if alpha < stand:
        alpha = stand
    if depth <= 0:
        return stand

    moves = gen_legal_moves(pos, captures_only=True)
    moves.sort(key=lambda m: move_score(pos, m), reverse=True)
    for mv in moves:
        score = -quiescence(make_move(pos, mv), -beta, -alpha, depth - 1)
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
    return alpha


def alphabeta(pos: Position, depth: int, alpha: int, beta: int) -> int:
    legal = gen_legal_moves(pos)
    if depth == 0:
        return quiescence(pos, alpha, beta, 3)

    if not legal:
        color = "w" if pos.side == "white" else "b"
        if in_check(pos, color):
            return -100000 + (4 - depth)
        return 0

    legal.sort(key=lambda m: move_score(pos, m), reverse=True)

    best = -INF
    for mv in legal:
        nxt = make_move(pos, mv)
        score = -alphabeta(nxt, depth - 1, -beta, -alpha)
        if score > best:
            best = score
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best


def choose_move(pos: Position) -> str:
    legal = gen_legal_moves(pos)
    if not legal:
        return ""

    legal.sort(key=lambda m: move_score(pos, m), reverse=True)

    for mv in legal:
        nxt = make_move(pos, mv)
        if not gen_legal_moves(nxt):
            enemy = "w" if nxt.side == "white" else "b"
            if in_check(nxt, enemy):
                return mv

    best_move = legal[0]
    best_score = -INF

    piece_count = len(pos.board)
    if piece_count <= 8:
        depth = 4
    elif piece_count <= 14:
        depth = 3
    else:
        depth = 3

    alpha = -INF
    beta = INF
    for mv in legal:
        nxt = make_move(pos, mv)
        score = -alphabeta(nxt, depth - 1, -beta, -alpha)
        if score > best_score:
            best_score = score
            best_move = mv
        if score > alpha:
            alpha = score

    return best_move


def policy(pieces: dict[str, str], to_play: str) -> str:
    board = dict(pieces)
    castle = infer_castling_rights(board)
    ep = infer_ep(board, to_play)
    pos = Position(board, to_play, castle, ep)
    legal = gen_legal_moves(pos)
    if not legal:
        all_pseudo = gen_pseudo_moves(pos)
        if all_pseudo:
            return all_pseudo[0]
        return "a1a1"
    mv = choose_move(pos)
    if mv in legal:
        return mv
    return legal[0]
