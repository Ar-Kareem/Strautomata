
import random
from copy import deepcopy

# piece values for simple material evaluation
PIECE_VALUE = {
    'P': 1,
    'N': 3,
    'B': 3,
    'R': 5,
    'Q': 9,
    'K': 0,
}

# directions for sliding pieces
DIRS = {
    'N': [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)],
    'B': [(-1, -1), (-1, 1), (1, -1), (1, 1)],
    'R': [(-1, 0), (1, 0), (0, -1), (0, 1)],
    'Q': [(-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)],
    'K': [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)],
}

def square_to_xy(sq: str):
    return ord(sq[0]) - ord('a'), int(sq[1]) - 1

def xy_to_square(x: int, y: int):
    return chr(ord('a') + x) + str(y + 1)

def inside(x, y):
    return 0 <= x < 8 and 0 <= y < 8

def opponent(color):
    return 'b' if color == 'w' else 'w'

def generate_pseudo_moves(board, color):
    moves = []
    forward = 1 if color == 'w' else -1
    start_rank = 1 if color == 'w' else 6   # 0‑based index
    promotion_rank = 7 if color == 'w' else 0

    for sq, piece in board.items():
        if piece[0] != color:
            continue
        p_type = piece[1]
        x, y = square_to_xy(sq)

        if p_type == 'P':
            # single forward
            nx, ny = x, y + forward
            if inside(nx, ny):
                dest = xy_to_square(nx, ny)
                if dest not in board:
                    # promotion?
                    if ny == promotion_rank:
                        moves.append((sq, dest, 'q'))
                    else:
                        moves.append((sq, dest, None))
                    # double forward from start rank
                    if y == start_rank:
                        nx2, ny2 = x, y + 2 * forward
                        dest2 = xy_to_square(nx2, ny2)
                        if dest2 not in board:
                            moves.append((sq, dest2, None))
            # captures
            for dx in (-1, 1):
                nx, ny = x + dx, y + forward
                if inside(nx, ny):
                    dest = xy_to_square(nx, ny)
                    if dest in board and board[dest][0] == opponent(color):
                        if ny == promotion_rank:
                            moves.append((sq, dest, 'q'))
                        else:
                            moves.append((sq, dest, None))

        elif p_type == 'N':
            for dx, dy in DIRS['N']:
                nx, ny = x + dx, y + dy
                if inside(nx, ny):
                    dest = xy_to_square(nx, ny)
                    if dest not in board or board[dest][0] == opponent(color):
                        moves.append((sq, dest, None))

        elif p_type in ('B', 'R', 'Q'):
            dirs = DIRS[p_type]
            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                while inside(nx, ny):
                    dest = xy_to_square(nx, ny)
                    if dest not in board:
                        moves.append((sq, dest, None))
                    else:
                        if board[dest][0] == opponent(color):
                            moves.append((sq, dest, None))
                        break
                    nx += dx
                    ny += dy

        elif p_type == 'K':
            for dx, dy in DIRS['K']:
                nx, ny = x + dx, y + dy
                if inside(nx, ny):
                    dest = xy_to_square(nx, ny)
                    if dest not in board or board[dest][0] == opponent(color):
                        moves.append((sq, dest, None))
            # castling ignored for simplicity

    return moves

def apply_move(board, src, dst, promo):
    new_board = deepcopy(board)
    piece = new_board.pop(src)
    if promo:
        piece = piece[0] + promo.upper()
    # capture
    new_board.pop(dst, None)
    new_board[dst] = piece
    return new_board

def king_position(board, color):
    for sq, pc in board.items():
        if pc == color + 'K':
            return sq
    return None

def square_attacked(board, target_sq, attacker_color):
    tx, ty = square_to_xy(target_sq)
    opp = attacker_color

    # pawn attacks
    pawn_dir = -1 if opp == 'w' else 1
    for dx in (-1, 1):
        nx, ny = tx + dx, ty + pawn_dir
        if inside(nx, ny):
            sq = xy_to_square(nx, ny)
            if sq in board and board[sq] == opp + 'P':
                return True

    # knights
    for dx, dy in DIRS['N']:
        nx, ny = tx + dx, ty + dy
        if inside(nx, ny):
            sq = xy_to_square(nx, ny)
            if sq in board and board[sq] == opp + 'N':
                return True

    # sliding pieces
    for dirs, attackers in [ (DIRS['B'], ('B', 'Q')),
                             (DIRS['R'], ('R', 'Q')) ]:
        for dx, dy in dirs:
            nx, ny = tx + dx, ty + dy
            while inside(nx, ny):
                sq = xy_to_square(nx, ny)
                if sq in board:
                    pc = board[sq]
                    if pc[0] == opp and pc[1] in attackers:
                        return True
                    break
                nx += dx
                ny += dy

    # king
    for dx, dy in DIRS['K']:
        nx, ny = tx + dx, ty + dy
        if inside(nx, ny):
            sq = xy_to_square(nx, ny)
            if sq in board and board[sq] == opp + 'K':
                return True

    return False

def legal_moves(board, color):
    pseudo = generate_pseudo_moves(board, color)
    legal = []
    for src, dst, promo in pseudo:
        nb = apply_move(board, src, dst, promo)
        king_sq = king_position(nb, color)
        if king_sq is None:   # should not happen
            continue
        if not square_attacked(nb, king_sq, opponent(color)):
            move_str = src + dst
            if promo:
                move_str += promo
            legal.append((move_str, src, dst, promo))
    return legal

def evaluate_move(board, src, dst, promo):
    # simple capture value, promotion not considered beyond queen value
    captured = board.get(dst)
    if captured:
        return PIECE_VALUE.get(captured[1], 0)
    return 0

def policy(pieces: dict, to_play: str, memory: dict):
    color = 'w' if to_play == 'white' else 'b'
    legal = legal_moves(pieces, color)

    if not legal:
        # no legal move – return a null move (should not be called in practice)
        return ('', memory)

    # score moves
    best_score = -1
    best_move = None
    for move_str, src, dst, promo in legal:
        score = evaluate_move(pieces, src, dst, promo)
        if score > best_score:
            best_score = score
            best_move = move_str

    # if no capture, just pick the first legal move
    if best_move is None:
        best_move = legal[0][0]

    return (best_move, memory)
