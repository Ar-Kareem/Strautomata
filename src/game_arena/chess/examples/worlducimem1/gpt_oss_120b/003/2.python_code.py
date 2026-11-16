
import random
from copy import deepcopy

# piece values for static evaluation (white perspective)
PIECE_VALUES = {
    'P': 1,
    'N': 3,
    'B': 3,
    'R': 5,
    'Q': 9,
    'K': 0,
}

# Directions for sliding pieces
DIRS = {
    'N': [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)],
    'B': [(-1, -1), (-1, 1), (1, -1), (1, 1)],
    'R': [(-1, 0), (1, 0), (0, -1), (0, 1)],
    'Q': [(-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)],
    'K': [(-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)],
}

FILES = 'abcdefgh'
RANKS = '12345678'

def sq_to_xy(sq: str):
    """convert algebraic square to (x, y) where a1 -> (0,0)"""
    return FILES.index(sq[0]), RANKS.index(sq[1])

def xy_to_sq(x: int, y: int):
    if 0 <= x < 8 and 0 <= y < 8:
        return FILES[x] + RANKS[y]
    return None

def inside(x, y):
    return 0 <= x < 8 and 0 <= y < 8

def opponent(color):
    return 'b' if color == 'w' else 'w'

def generate_pseudo_moves(board, color):
    """All moves ignoring own‑king safety."""
    moves = []
    for sq, piece in board.items():
        if piece[0] != color:
            continue
        ptype = piece[1]
        x, y = sq_to_xy(sq)

        if ptype == 'P':
            dir_forward = 1 if color == 'w' else -1
            start_rank = 1 if color == 'w' else 6
            promotion_rank = 7 if color == 'w' else 0

            # single forward
            ny = y + dir_forward
            if inside(x, ny):
                target = xy_to_sq(x, ny)
                if target not in board:
                    if ny == promotion_rank:
                        for promo in 'qrnb':
                            moves.append(sq + target + promo)
                    else:
                        moves.append(sq + target)

                    # double forward from start
                    if y == start_rank:
                        ny2 = y + 2 * dir_forward
                        target2 = xy_to_sq(x, ny2)
                        if target2 not in board:
                            moves.append(sq + target2)

            # captures
            for dx in (-1, 1):
                nx = x + dx
                ny = y + dir_forward
                if inside(nx, ny):
                    target = xy_to_sq(nx, ny)
                    if target in board and board[target][0] == opponent(color):
                        if ny == promotion_rank:
                            for promo in 'qrnb':
                                moves.append(sq + target + promo)
                        else:
                            moves.append(sq + target)

        elif ptype == 'N':
            for dx, dy in DIRS['N']:
                nx, ny = x + dx, y + dy
                if inside(nx, ny):
                    target = xy_to_sq(nx, ny)
                    if target not in board or board[target][0] == opponent(color):
                        moves.append(sq + target)

        elif ptype in ('B', 'R', 'Q'):
            dirs = DIRS[ptype]
            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                while inside(nx, ny):
                    target = xy_to_sq(nx, ny)
                    if target in board:
                        if board[target][0] == opponent(color):
                            moves.append(sq + target)
                        break
                    else:
                        moves.append(sq + target)
                    nx += dx
                    ny += dy

        elif ptype == 'K':
            for dx, dy in DIRS['K']:
                nx, ny = x + dx, y + dy
                if inside(nx, ny):
                    target = xy_to_sq(nx, ny)
                    if target not in board or board[target][0] == opponent(color):
                        moves.append(sq + target)
            # Castling is omitted (no history info)
    return moves

def is_attacked(board, square, attacker_color):
    """Return True if square is attacked by any piece of attacker_color."""
    tx, ty = sq_to_xy(square)

    # pawn attacks
    dir_forward = 1 if attacker_color == 'w' else -1
    for dx in (-1, 1):
        nx, ny = tx + dx, ty + dir_forward
        if inside(nx, ny):
            sq = xy_to_sq(nx, ny)
            if sq in board and board[sq] == attacker_color + 'P':
                return True

    # knight attacks
    for dx, dy in DIRS['N']:
        nx, ny = tx + dx, ty + dy
        if inside(nx, ny):
            sq = xy_to_sq(nx, ny)
            if sq in board and board[sq] == attacker_color + 'N':
                return True

    # sliding pieces
    for piece_type, dirs in (('B', DIRS['B']), ('R', DIRS['R']), ('Q', DIRS['Q'])):
        for dx, dy in dirs:
            nx, ny = tx + dx, ty + dy
            while inside(nx, ny):
                sq = xy_to_sq(nx, ny)
                if sq in board:
                    if board[sq][0] == attacker_color and board[sq][1] in (piece_type, 'Q'):
                        return True
                    break
                nx += dx
                ny += dy

    # king attacks (adjacent)
    for dx, dy in DIRS['K']:
        nx, ny = tx + dx, ty + dy
        if inside(nx, ny):
            sq = xy_to_sq(nx, ny)
            if sq in board and board[sq] == attacker_color + 'K':
                return True

    return False

def locate_king(board, color):
    for sq, piece in board.items():
        if piece == color + 'K':
            return sq
    return None

def make_move(board, move):
    """Return a new board dict after applying UCI move (including promotions)."""
    new_board = deepcopy(board)
    src = move[:2]
    dst = move[2:4]
    promo = move[4] if len(move) == 5 else None

    piece = new_board.pop(src)
    if promo:
        piece = piece[0] + promo.upper()
    new_board[dst] = piece
    return new_board

def is_king_in_check(board, color):
    king_sq = locate_king(board, color)
    if king_sq is None:
        # King captured – treat as check
        return True
    return is_attacked(board, king_sq, opponent(color))

def legal_moves(board, color):
    """Return list of moves that do not leave own king in check."""
    pseudo = generate_pseudo_moves(board, color)
    legal = []
    for mv in pseudo:
        nb = make_move(board, mv)
        if not is_king_in_check(nb, color):
            legal.append(mv)
    return legal

def evaluate(board):
    """Material evaluation from White's perspective."""
    total = 0
    for piece in board.values():
        val = PIECE_VALUES[piece[1]]
        total += val if piece[0] == 'w' else -val
    return total

def policy(pieces: dict, to_play: str, memory: dict):
    # Convert color string to single char
    color = 'w' if to_play == 'white' else 'b'
    opp_color = opponent(color)

    # Generate all legal moves
    moves = legal_moves(pieces, color)

    # If somehow no moves (stalemate/checkmate), just return a dummy move
    if not moves:
        # pick any pseudo move to avoid crash; arena should not call in this case
        return ('a1a1', memory)

    best_move = None
    best_score = None

    for mv in moves:
        new_board = make_move(pieces, mv)

        # Check for opponent checkmate
        opp_legal = legal_moves(new_board, opp_color)
        opp_king_sq = locate_king(new_board, opp_color)
        opp_in_check = is_king_in_check(new_board, opp_color)
        if opp_in_check and not opp_legal:
            # Mate! give huge score
            score = 100000 if color == 'w' else -100000
        else:
            # Simple material evaluation
            eval_score = evaluate(new_board)

            # Small bonus for delivering check
            if opp_in_check:
                eval_score += 0.5 if color == 'w' else -0.5

            # Score should be from the perspective of the moving side
            score = eval_score if color == 'w' else -eval_score

        # Update best move
        if best_move is None:
            best_move = mv
            best_score = score
        else:
            if color == 'w':
                if score > best_score:
                    best_move, best_score = mv, score
            else:
                if score < best_score:
                    best_move, best_score = mv, score

    # If multiple moves have the same best score, pick randomly among them
    # (optional – here we already have one; could be refined)
    return (best_move, memory)
