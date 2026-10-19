
import copy
from typing import Dict, Tuple, List

# Piece values for static evaluation
PIECE_VALUE = {
    'P': 1,
    'N': 3,
    'B': 3,
    'R': 5,
    'Q': 9,
    'K': 0
}

# Direction vectors
KNIGHT_DIRS = [(2, 1), (1, 2), (-1, 2), (-2, 1),
               (-2, -1), (-1, -2), (1, -2), (2, -1)]
KING_DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1),
             (-1, 0), (-1, -1), (0, -1), (1, -1)]
BISHOP_DIRS = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
ROOK_DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]

FILES = 'abcdefgh'
RANKS = '12345678'

def square_to_idx(sq: str) -> Tuple[int, int]:
    """'e4' -> (4,3) where x is file 0‑7, y is rank 0‑7."""
    file = FILES.index(sq[0])
    rank = RANKS.index(sq[1])
    return file, rank

def idx_to_square(x: int, y: int) -> str:
    return f"{FILES[x]}{RANKS[y]}"

def build_board(pieces: Dict[str, str]) -> List[List[str]]:
    board = [[None for _ in range(8)] for _ in range(8)]
    for sq, pc in pieces.items():
        x, y = square_to_idx(sq)
        board[y][x] = pc  # row = rank
    return board

def inside(x: int, y: int) -> bool:
    return 0 <= x < 8 and 0 <= y < 8

def opponent(color: str) -> str:
    return 'b' if color == 'w' else 'w'

def generate_pseudo_moves(board, color) -> List[str]:
    moves = []
    dir_forward = 1 if color == 'w' else -1
    start_rank = 1 if color == 'w' else 6
    promotion_rank = 7 if color == 'w' else 0

    for y in range(8):
        for x in range(8):
            pc = board[y][x]
            if not pc or pc[0] != color:
                continue
            piece = pc[1]

            if piece == 'P':
                # single forward
                ny = y + dir_forward
                if inside(x, ny) and board[ny][x] is None:
                    # promotion?
                    if ny == promotion_rank:
                        for promo in ['q', 'r', 'b', 'n']:
                            moves.append(f"{idx_to_square(x, y)}{idx_to_square(x, ny)}{promo}")
                    else:
                        moves.append(f"{idx_to_square(x, y)}{idx_to_square(x, ny)}")
                    # double forward
                    if y == start_rank:
                        ny2 = y + 2 * dir_forward
                        if board[ny2][x] is None:
                            moves.append(f"{idx_to_square(x, y)}{idx_to_square(x, ny2)}")
                # captures
                for dx in [-1, 1]:
                    nx = x + dx
                    ny = y + dir_forward
                    if inside(nx, ny):
                        target = board[ny][nx]
                        if target and target[0] == opponent(color):
                            if ny == promotion_rank:
                                for promo in ['q', 'r', 'b', 'n']:
                                    moves.append(f"{idx_to_square(x, y)}{idx_to_square(nx, ny)}{promo}")
                            else:
                                moves.append(f"{idx_to_square(x, y)}{idx_to_square(nx, ny)}")
                # (en‑passant omitted)
            elif piece == 'N':
                for dx, dy in KNIGHT_DIRS:
                    nx, ny = x + dx, y + dy
                    if inside(nx, ny):
                        target = board[ny][nx]
                        if target is None or target[0] == opponent(color):
                            moves.append(f"{idx_to_square(x, y)}{idx_to_square(nx, ny)}")
            elif piece == 'B' or piece == 'Q':
                for dx, dy in BISHOP_DIRS:
                    nx, ny = x + dx, y + dy
                    while inside(nx, ny):
                        target = board[ny][nx]
                        if target is None:
                            moves.append(f"{idx_to_square(x, y)}{idx_to_square(nx, ny)}")
                        else:
                            if target[0] == opponent(color):
                                moves.append(f"{idx_to_square(x, y)}{idx_to_square(nx, ny)}")
                            break
                        nx += dx
                        ny += dy
            if piece == 'R' or piece == 'Q':
                for dx, dy in ROOK_DIRS:
                    nx, ny = x + dx, y + dy
                    while inside(nx, ny):
                        target = board[ny][nx]
                        if target is None:
                            moves.append(f"{idx_to_square(x, y)}{idx_to_square(nx, ny)}")
                        else:
                            if target[0] == opponent(color):
                                moves.append(f"{idx_to_square(x, y)}{idx_to_square(nx, ny)}")
                            break
                        nx += dx
                        ny += dy
            if piece == 'K':
                for dx, dy in KING_DIRS:
                    nx, ny = x + dx, y + dy
                    if inside(nx, ny):
                        target = board[ny][nx]
                        if target is None or target[0] == opponent(color):
                            moves.append(f"{idx_to_square(x, y)}{idx_to_square(nx, ny)}")
                # castling omitted for simplicity
    return moves

def make_move(board, move: str) -> List[List[str]]:
    """Return a new board after applying move. Handles promotions."""
    new_board = copy.deepcopy(board)
    from_sq = move[:2]
    to_sq = move[2:4]
    promo = move[4] if len(move) == 5 else None
    fx, fy = square_to_idx(from_sq)
    tx, ty = square_to_idx(to_sq)
    piece = new_board[fy][fx]
    new_board[fy][fx] = None
    if promo:
        piece = piece[0] + promo.upper()
    new_board[ty][tx] = piece
    return new_board

def find_king(board, color) -> Tuple[int, int]:
    for y in range(8):
        for x in range(8):
            pc = board[y][x]
            if pc == f"{color}K":
                return x, y
    raise ValueError("King not found")

def is_square_attacked(board, x: int, y: int, attacker_color: str) -> bool:
    # Pawns
    dir_forward = -1 if attacker_color == 'w' else 1
    for dx in [-1, 1]:
        nx, ny = x + dx, y + dir_forward
        if inside(nx, ny):
            pc = board[ny][nx]
            if pc == f"{attacker_color}P":
                return True
    # Knights
    for dx, dy in KNIGHT_DIRS:
        nx, ny = x + dx, y + dy
        if inside(nx, ny):
            pc = board[ny][nx]
            if pc == f"{attacker_color}N":
                return True
    # Sliding pieces
    # Bishops / Queens (diagonals)
    for dx, dy in BISHOP_DIRS:
        nx, ny = x + dx, y + dy
        while inside(nx, ny):
            pc = board[ny][nx]
            if pc:
                if pc[0] == attacker_color and (pc[1] in ('B', 'Q')):
                    return True
                break
            nx += dx
            ny += dy
    # Rooks / Queens (orthogonal)
    for dx, dy in ROOK_DIRS:
        nx, ny = x + dx, y + dy
        while inside(nx, ny):
            pc = board[ny][nx]
            if pc:
                if pc[0] == attacker_color and (pc[1] in ('R', 'Q')):
                    return True
                break
            nx += dx
            ny += dy
    # King
    for dx, dy in KING_DIRS:
        nx, ny = x + dx, y + dy
        if inside(nx, ny):
            pc = board[ny][nx]
            if pc == f"{attacker_color}K":
                return True
    return False

def is_in_check(board, color) -> bool:
    kx, ky = find_king(board, color)
    return is_square_attacked(board, kx, ky, opponent(color))

def material_score(board, color) -> int:
    """Return material balance (own - opponent)."""
    total = 0
    for row in board:
        for pc in row:
            if pc:
                val = PIECE_VALUE[pc[1]]
                if pc[0] == color:
                    total += val
                else:
                    total -= val
    return total

def move_gives_check(board, move, color) -> bool:
    new_board = make_move(board, move)
    return is_in_check(new_board, opponent(color))

def policy(pieces: dict, to_play: str, memory: dict) -> tuple:
    # Translate color string
    color = 'w' if to_play == 'white' else 'b'

    board = build_board(pieces)

    pseudo_moves = generate_pseudo_moves(board, color)

    legal_moves = []
    for mv in pseudo_moves:
        new_board = make_move(board, mv)
        if not is_in_check(new_board, color):
            legal_moves.append(mv)

    # If somehow no legal moves (checkmate/stalemate), return a dummy move
    if not legal_moves:
        return ("0000", memory)

    best_move = None
    best_score = -10**9

    for mv in legal_moves:
        new_board = make_move(board, mv)
        score = material_score(new_board, color)

        # Bonus for delivering check
        if move_gives_check(board, mv, color):
            score += 0.5

        # Huge bonus for promotion to queen (already accounted in material via queen value)
        if len(mv) == 5 and mv[4] == 'q':
            score += 0.2

        if score > best_score:
            best_score = score
            best_move = mv

    return (best_move, memory)
