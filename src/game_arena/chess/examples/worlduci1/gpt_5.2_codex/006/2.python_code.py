
import math
from typing import Dict, Tuple, List, Optional

# Piece values for evaluation
PIECE_VALUES = {
    'P': 100,
    'N': 320,
    'B': 330,
    'R': 500,
    'Q': 900,
    'K': 0
}

FILES = 'abcdefgh'
RANKS = '12345678'

def square_to_coord(sq: str) -> Tuple[int, int]:
    return ord(sq[0]) - 97, int(sq[1]) - 1

def coord_to_square(coord: Tuple[int, int]) -> str:
    return chr(coord[0] + 97) + str(coord[1] + 1)

def in_bounds(x: int, y: int) -> bool:
    return 0 <= x < 8 and 0 <= y < 8

def find_king(board: Dict[Tuple[int,int], str], color: str) -> Optional[Tuple[int,int]]:
    for pos, piece in board.items():
        if piece == color + 'K':
            return pos
    return None

def is_attacked(board: Dict[Tuple[int,int], str], sq: Tuple[int,int], attacker: str) -> bool:
    x, y = sq
    # Pawns
    direction = 1 if attacker == 'w' else -1
    for dx in [-1, 1]:
        nx, ny = x + dx, y - direction
        if in_bounds(nx, ny):
            piece = board.get((nx, ny))
            if piece == attacker + 'P':
                return True
    # Knights
    knight_moves = [(1,2),(2,1),(-1,2),(-2,1),(1,-2),(2,-1),(-1,-2),(-2,-1)]
    for dx, dy in knight_moves:
        nx, ny = x + dx, y + dy
        if in_bounds(nx, ny):
            if board.get((nx, ny)) == attacker + 'N':
                return True
    # Sliding pieces
    directions = [
        (1,0),(-1,0),(0,1),(0,-1), # rook
        (1,1),(-1,-1),(1,-1),(-1,1) # bishop
    ]
    for dx, dy in directions:
        nx, ny = x + dx, y + dy
        while in_bounds(nx, ny):
            piece = board.get((nx, ny))
            if piece:
                if piece[0] == attacker:
                    if (dx == 0 or dy == 0) and piece[1] in ['R','Q']:
                        return True
                    if (dx != 0 and dy != 0) and piece[1] in ['B','Q']:
                        return True
                break
            nx += dx
            ny += dy
    # King
    for dx in [-1,0,1]:
        for dy in [-1,0,1]:
            if dx == 0 and dy == 0: 
                continue
            nx, ny = x + dx, y + dy
            if in_bounds(nx, ny):
                if board.get((nx, ny)) == attacker + 'K':
                    return True
    return False

def generate_pseudo_moves(board: Dict[Tuple[int,int], str], color: str) -> List[Tuple[Tuple[int,int], Tuple[int,int], Optional[str]]]:
    moves = []
    enemy = 'b' if color == 'w' else 'w'
    for (x, y), piece in board.items():
        if piece[0] != color:
            continue
        p = piece[1]
        if p == 'P':
            direction = 1 if color == 'w' else -1
            start_rank = 1 if color == 'w' else 6
            promotion_rank = 7 if color == 'w' else 0
            # forward
            nx, ny = x, y + direction
            if in_bounds(nx, ny) and (nx, ny) not in board:
                if ny == promotion_rank:
                    for promo in ['q','r','b','n']:
                        moves.append(((x,y),(nx,ny),promo))
                else:
                    moves.append(((x,y),(nx,ny),None))
                # double
                if y == start_rank:
                    nx2, ny2 = x, y + 2*direction
                    if in_bounds(nx2, ny2) and (nx2, ny2) not in board:
                        moves.append(((x,y),(nx2,ny2),None))
            # captures
            for dx in [-1,1]:
                nx, ny = x + dx, y + direction
                if in_bounds(nx, ny) and (nx, ny) in board and board[(nx, ny)][0] == enemy:
                    if ny == promotion_rank:
                        for promo in ['q','r','b','n']:
                            moves.append(((x,y),(nx,ny),promo))
                    else:
                        moves.append(((x,y),(nx,ny),None))
        elif p == 'N':
            for dx, dy in [(1,2),(2,1),(-1,2),(-2,1),(1,-2),(2,-1),(-1,-2),(-2,-1)]:
                nx, ny = x + dx, y + dy
                if in_bounds(nx, ny):
                    if (nx, ny) not in board or board[(nx, ny)][0] == enemy:
                        moves.append(((x,y),(nx,ny),None))
        elif p in ['B','R','Q']:
            dirs = []
            if p in ['B','Q']:
                dirs += [(1,1),(-1,-1),(1,-1),(-1,1)]
            if p in ['R','Q']:
                dirs += [(1,0),(-1,0),(0,1),(0,-1)]
            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                while in_bounds(nx, ny):
                    if (nx, ny) in board:
                        if board[(nx, ny)][0] == enemy:
                            moves.append(((x,y),(nx,ny),None))
                        break
                    moves.append(((x,y),(nx,ny),None))
                    nx += dx
                    ny += dy
        elif p == 'K':
            for dx in [-1,0,1]:
                for dy in [-1,0,1]:
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = x + dx, y + dy
                    if in_bounds(nx, ny):
                        if (nx, ny) not in board or board[(nx, ny)][0] == enemy:
                            moves.append(((x,y),(nx,ny),None))
            # Castling
            if color == 'w' and (x, y) == (4,0):
                if board.get((7,0)) == 'wR':
                    if (5,0) not in board and (6,0) not in board:
                        if not is_attacked(board, (4,0), enemy) and not is_attacked(board, (5,0), enemy) and not is_attacked(board, (6,0), enemy):
                            moves.append(((4,0),(6,0),None))
                if board.get((0,0)) == 'wR':
                    if (1,0) not in board and (2,0) not in board and (3,0) not in board:
                        if not is_attacked(board, (4,0), enemy) and not is_attacked(board, (3,0), enemy) and not is_attacked(board, (2,0), enemy):
                            moves.append(((4,0),(2,0),None))
            if color == 'b' and (x, y) == (4,7):
                if board.get((7,7)) == 'bR':
                    if (5,7) not in board and (6,7) not in board:
                        if not is_attacked(board, (4,7), enemy) and not is_attacked(board, (5,7), enemy) and not is_attacked(board, (6,7), enemy):
                            moves.append(((4,7),(6,7),None))
                if board.get((0,7)) == 'bR':
                    if (1,7) not in board and (2,7) not in board and (3,7) not in board:
                        if not is_attacked(board, (4,7), enemy) and not is_attacked(board, (3,7), enemy) and not is_attacked(board, (2,7), enemy):
                            moves.append(((4,7),(2,7),None))
    return moves

def make_move(board: Dict[Tuple[int,int], str], move: Tuple[Tuple[int,int], Tuple[int,int], Optional[str]]) -> Dict[Tuple[int,int], str]:
    (fx, fy), (tx, ty), promo = move
    piece = board[(fx, fy)]
    new_board = dict(board)
    del new_board[(fx, fy)]
    # Castling
    if piece[1] == 'K' and abs(tx - fx) == 2:
        if tx == 6:  # kingside
            rook_from = (7, fy)
            rook_to = (5, fy)
        else:        # queenside
            rook_from = (0, fy)
            rook_to = (3, fy)
        if rook_from in new_board:
            rook_piece = new_board[rook_from]
            del new_board[rook_from]
            new_board[rook_to] = rook_piece
    # Capture
    if (tx, ty) in new_board:
        del new_board[(tx, ty)]
    # Promotion
    if promo:
        new_board[(tx, ty)] = piece[0] + promo.upper()
    else:
        new_board[(tx, ty)] = piece
    return new_board

def generate_legal_moves(board: Dict[Tuple[int,int], str], color: str) -> List[Tuple[Tuple[int,int], Tuple[int,int], Optional[str]]]:
    moves = generate_pseudo_moves(board, color)
    legal = []
    for mv in moves:
        new_board = make_move(board, mv)
        king_pos = find_king(new_board, color)
        if king_pos and not is_attacked(new_board, king_pos, 'b' if color == 'w' else 'w'):
            legal.append(mv)
    return legal

def evaluate(board: Dict[Tuple[int,int], str], root_color: str) -> int:
    score = 0
    for piece in board.values():
        val = PIECE_VALUES[piece[1]]
        score += val if piece[0] == root_color else -val
    return score

def minimax(board: Dict[Tuple[int,int], str], color: str, depth: int, alpha: int, beta: int, root_color: str) -> int:
    legal = generate_legal_moves(board, color)
    if not legal:
        king_pos = find_king(board, color)
        if king_pos and is_attacked(board, king_pos, 'b' if color == 'w' else 'w'):
            return -100000 if color == root_color else 100000
        return 0
    if depth == 0:
        return evaluate(board, root_color)
    maximizing = (color == root_color)
    if maximizing:
        value = -math.inf
        for mv in legal:
            new_board = make_move(board, mv)
            value = max(value, minimax(new_board, 'b' if color == 'w' else 'w', depth-1, alpha, beta, root_color))
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value
    else:
        value = math.inf
        for mv in legal:
            new_board = make_move(board, mv)
            value = min(value, minimax(new_board, 'b' if color == 'w' else 'w', depth-1, alpha, beta, root_color))
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value

def move_to_uci(move: Tuple[Tuple[int,int], Tuple[int,int], Optional[str]]) -> str:
    (fx, fy), (tx, ty), promo = move
    s = coord_to_square((fx, fy)) + coord_to_square((tx, ty))
    if promo:
        s += promo
    return s

def policy(pieces: Dict[str, str], to_play: str) -> str:
    board = {}
    for sq, pc in pieces.items():
        board[square_to_coord(sq)] = pc
    color = 'w' if to_play == 'white' else 'b'
    legal = generate_legal_moves(board, color)
    if not legal:
        return ""
    # quick checkmate search
    for mv in legal:
        nb = make_move(board, mv)
        opp = 'b' if color == 'w' else 'w'
        if not generate_legal_moves(nb, opp):
            king_pos = find_king(nb, opp)
            if king_pos and is_attacked(nb, king_pos, color):
                return move_to_uci(mv)
    depth = 3 if len(legal) <= 8 else 2
    best_score = -math.inf
    best_move = legal[0]
    for mv in legal:
        nb = make_move(board, mv)
        score = minimax(nb, 'b' if color == 'w' else 'w', depth-1, -math.inf, math.inf, color)
        if score > best_score:
            best_score = score
            best_move = mv
    return move_to_uci(best_move)
