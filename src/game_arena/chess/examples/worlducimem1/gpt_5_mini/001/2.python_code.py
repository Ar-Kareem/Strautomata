
#!/usr/bin/env python3
from typing import Dict, Tuple, List
import math
import random
import time

# Policy entry point
def policy(pieces: dict[str, str], to_play: str, memory: dict) -> tuple[str, dict]:
    # Convert pieces dict into internal board mapping
    board = dict(pieces)  # shallow copy
    color = 'w' if to_play == 'white' else 'b'

    # Generate legal moves
    legal = generate_legal_moves(board, color)
    if not legal:
        # Fallback: try pseudo-legal moves if no legal found (to guarantee a move)
        legal = generate_pseudo_legal_moves(board, color)
        if not legal:
            # Extremely degenerate: no moves at all; return a null move (shouldn't happen)
            # Return any string; but must be 4-chars. Choose a passive dummy like a1a1
            return ('a1a1', {})

    # If only one move, return it
    if len(legal) == 1:
        return (legal[0], memory)

    # Use alpha-beta minimax with depth 2 (my move then opponent)
    start = time.time()
    depth = 2

    best_score = -10**9
    best_move = legal[0]

    # Move ordering: prefer captures and promotions
    scored_moves = []
    for mv in legal:
        score = move_ordering_score(board, mv, color)
        scored_moves.append(( -score, mv ))  # negative so sort ascending gives high score first
    scored_moves.sort()
    ordered = [mv for _, mv in scored_moves]

    for mv in ordered:
        new_board = apply_move(board, mv, color)
        score = -alphabeta(new_board, opponent(color), depth-1, -10**9, 10**9, start)
        if score > best_score or (score == best_score and tie_breaker(board, mv, best_move)):
            best_score = score
            best_move = mv

    return (best_move, memory)

# Helper utilities

def tie_breaker(board, mv1, mv2):
    # Prefer captures/promotions or lexicographically smaller for determinism
    s1 = move_ordering_score(board, mv1, 'w')
    s2 = move_ordering_score(board, mv2, 'w')
    if s1 != s2:
        return s1 > s2
    return mv1 < mv2

def opponent(color: str) -> str:
    return 'b' if color == 'w' else 'w'

# Coordinate utilities
FILES = 'abcdefgh'
RANKS = '12345678'
FILE_TO_X = {f:i for i,f in enumerate(FILES)}
X_TO_FILE = {i:f for i,f in enumerate(FILES)}

def sq_to_xy(sq: str) -> Tuple[int,int]:
    return FILE_TO_X[sq[0]], int(sq[1]) - 1

def xy_to_sq(x: int, y: int) -> str:
    if 0 <= x < 8 and 0 <= y < 8:
        return X_TO_FILE[x] + str(y+1)
    else:
        return None

def on_board(x:int,y:int) -> bool:
    return 0 <= x < 8 and 0 <= y < 8

# Piece values for evaluation
PIECE_VALUES = {
    'P': 100,
    'N': 320,
    'B': 330,
    'R': 500,
    'Q': 900,
    'K': 20000
}

# Generate pseudo-legal moves (not checking king in check)
def generate_pseudo_legal_moves(board: Dict[str,str], color: str) -> List[str]:
    moves = []
    for sq, piece in list(board.items()):
        if piece[0] != color:
            continue
        ptype = piece[1]
        x,y = sq_to_xy(sq)
        if ptype == 'P':
            moves.extend(pawn_moves(board, x, y, color))
        elif ptype == 'N':
            moves.extend(knight_moves(board, x, y, color))
        elif ptype == 'B':
            moves.extend(bishop_moves(board, x, y, color))
        elif ptype == 'R':
            moves.extend(rook_moves(board, x, y, color))
        elif ptype == 'Q':
            moves.extend(queen_moves(board, x, y, color))
        elif ptype == 'K':
            moves.extend(king_moves(board, x, y, color))
    return moves

def generate_legal_moves(board: Dict[str,str], color: str) -> List[str]:
    pseudo = generate_pseudo_legal_moves(board, color)
    legal = []
    for mv in pseudo:
        newb = apply_move(board, mv, color)
        king_sq = find_king(newb, color)
        if king_sq is None:
            # King captured -> treat as legal (rare), but we'll allow
            legal.append(mv)
        else:
            if not is_square_attacked(newb, king_sq, opponent(color)):
                legal.append(mv)
    # If none, return empty list
    return legal

# Move generators for piece types
def pawn_moves(board, x, y, color):
    moves = []
    dir = 1 if color == 'w' else -1
    start_rank = 1 if color == 'w' else 6
    # forward one
    nx, ny = x, y + dir
    if on_board(nx, ny) and xy_to_sq(nx,ny) not in board:
        # promotion?
        if ny == 7 or ny == 0:
            for promo in 'qrbn':
                moves.append(xy_to_sq(x,y) + xy_to_sq(nx,ny) + promo)
        else:
            moves.append(xy_to_sq(x,y) + xy_to_sq(nx,ny))
            # forward two
            if y == start_rank:
                ny2 = y + 2*dir
                if on_board(x, ny2) and xy_to_sq(x,ny2) not in board:
                    moves.append(xy_to_sq(x,y) + xy_to_sq(x,ny2))
    # captures
    for dx in (-1,1):
        cx, cy = x+dx, y+dir
        if on_board(cx, cy):
            sq = xy_to_sq(cx,cy)
            if sq in board and board[sq][0] != color:
                if cy == 7 or cy == 0:
                    for promo in 'qrbn':
                        moves.append(xy_to_sq(x,y) + sq + promo)
                else:
                    moves.append(xy_to_sq(x,y) + sq)
    # Note: en passant ignored
    return moves

KNIGHT_OFFSETS = [(2,1),(1,2),(-1,2),(-2,1),(-2,-1),(-1,-2),(1,-2),(2,-1)]
def knight_moves(board, x, y, color):
    moves = []
    for dx,dy in KNIGHT_OFFSETS:
        nx, ny = x+dx, y+dy
        if on_board(nx, ny):
            sq = xy_to_sq(nx,ny)
            if sq not in board or board[sq][0] != color:
                moves.append(xy_to_sq(x,y) + sq)
    return moves

DIAGONALS = [(1,1),(1,-1),(-1,1),(-1,-1)]
STRAIGHTS = [(1,0),(-1,0),(0,1),(0,-1)]
def sliding_moves(board, x, y, color, directions):
    moves = []
    for dx,dy in directions:
        nx, ny = x+dx, y+dy
        while on_board(nx, ny):
            sq = xy_to_sq(nx,ny)
            if sq not in board:
                moves.append(xy_to_sq(x,y) + sq)
            else:
                if board[sq][0] != color:
                    moves.append(xy_to_sq(x,y) + sq)
                break
            nx += dx
            ny += dy
    return moves

def bishop_moves(board, x, y, color):
    return sliding_moves(board, x, y, color, DIAGONALS)

def rook_moves(board, x, y, color):
    return sliding_moves(board, x, y, color, STRAIGHTS)

def queen_moves(board, x, y, color):
    return sliding_moves(board, x, y, color, DIAGONALS + STRAIGHTS)

def king_moves(board, x, y, color):
    moves = []
    for dx in (-1,0,1):
        for dy in (-1,0,1):
            if dx == 0 and dy == 0:
                continue
            nx, ny = x+dx, y+dy
            if on_board(nx, ny):
                sq = xy_to_sq(nx,ny)
                if sq not in board or board[sq][0] != color:
                    moves.append(xy_to_sq(x,y) + sq)
    # Castling omitted
    return moves

def apply_move(board: Dict[str,str], move: str, color: str) -> Dict[str,str]:
    # move like e2e4 or e7e8q
    newb = dict(board)
    frm = move[0:2]
    to = move[2:4]
    promo = move[4] if len(move) > 4 else None
    if frm not in newb:
        # invalid move applied; return unchanged
        return newb
    piece = newb.pop(frm)
    # If capturing, replace
    if promo:
        # promote to specified piece of color
        piece = color + promo.upper()
    newb[to] = piece
    return newb

def find_king(board: Dict[str,str], color: str):
    for sq,p in board.items():
        if p == color + 'K':
            return sq
    return None

# Check if a square is attacked by color_attacker pieces
def is_square_attacked(board: Dict[str,str], square: str, color_attacker: str) -> bool:
    x, y = sq_to_xy(square)
    # pawn attacks
    if color_attacker == 'w':
        # white pawns attack from (x-1,y-1) and (x+1,y-1)
        for dx in (-1,1):
            sx, sy = x + dx, y - 1
            if on_board(sx, sy):
                sq2 = xy_to_sq(sx, sy)
                if sq2 in board and board[sq2] == 'wP':
                    return True
    else:
        # black pawns attack from (x-1,y+1) and (x+1,y+1)
        for dx in (-1,1):
            sx, sy = x + dx, y + 1
            if on_board(sx, sy):
                sq2 = xy_to_sq(sx, sy)
                if sq2 in board and board[sq2] == 'bP':
                    return True
    # knight attacks
    for dx,dy in KNIGHT_OFFSETS:
        sx, sy = x+dx, y+dy
        if on_board(sx, sy):
            sq2 = xy_to_sq(sx, sy)
            if sq2 in board and board[sq2] == color_attacker + 'N':
                return True
    # sliding attacks: rook/queen
    for dx,dy in STRAIGHTS:
        sx, sy = x+dx, y+dy
        while on_board(sx, sy):
            sq2 = xy_to_sq(sx, sy)
            if sq2 in board:
                p = board[sq2]
                if p[0] == color_attacker and (p[1] == 'R' or p[1] == 'Q'):
                    return True
                else:
                    break
            sx += dx; sy += dy
    # sliding attacks: bishop/queen
    for dx,dy in DIAGONALS:
        sx, sy = x+dx, y+dy
        while on_board(sx, sy):
            sq2 = xy_to_sq(sx, sy)
            if sq2 in board:
                p = board[sq2]
                if p[0] == color_attacker and (p[1] == 'B' or p[1] == 'Q'):
                    return True
                else:
                    break
            sx += dx; sy += dy
    # king attacks (adjacent)
    for dx in (-1,0,1):
        for dy in (-1,0,1):
            if dx == 0 and dy == 0:
                continue
            sx, sy = x+dx, y+dy
            if on_board(sx, sy):
                sq2 = xy_to_sq(sx, sy)
                if sq2 in board and board[sq2] == color_attacker + 'K':
                    return True
    return False

# Evaluation function
def evaluate(board: Dict[str,str], color_turn: str) -> int:
    # positive is good for 'w', negative good for 'b'. We'll return relative to the side to move.
    mat = 0
    mobility = 0
    for sq,p in board.items():
        val = PIECE_VALUES.get(p[1], 0)
        if p[0] == 'w':
            mat += val
        else:
            mat -= val
    # mobility: number of pseudo-legal moves difference (cheap)
    w_moves = len(generate_pseudo_legal_moves(board, 'w'))
    b_moves = len(generate_pseudo_legal_moves(board, 'b'))
    mobility = (w_moves - b_moves) * 5
    score = mat + mobility
    # Return score from perspective of color_turn
    return score if color_turn == 'w' else -score

# Alpha-beta search (negamax-style)
def alphabeta(board: Dict[str,str], color: str, depth: int, alpha: int, beta: int, start_time: float) -> int:
    # Simple time cutoff
    if time.time() - start_time > 0.95:
        return evaluate(board, color)
    # Terminal detection: king missing for side to move
    king_sq = find_king(board, color)
    if king_sq is None:
        # No king => lost
        return -100000
    moves = generate_legal_moves(board, color)
    if depth == 0 or not moves:
        # If no moves, checkmate or stalemate
        if not moves:
            # if king is attacked -> checkmate
            if is_square_attacked(board, king_sq, opponent(color)):
                return -100000  # checkmate
            else:
                return 0  # stalemate
        return evaluate(board, color)
    # Order moves: captures/promotions first
    moves.sort(key=lambda m: -move_ordering_score(board, m, color))
    value = -10**9
    for mv in moves:
        newb = apply_move(board, mv, color)
        val = -alphabeta(newb, opponent(color), depth-1, -beta, -alpha, start_time)
        if val > value:
            value = val
        if value > alpha:
            alpha = value
        if alpha >= beta:
            break
    return value

def move_ordering_score(board, mv, color):
    # heuristic score: capture value + promotion bonus
    frm = mv[0:2]; to = mv[2:4]
    score = 0
    if to in board:
        captured = board[to]
        # MVV-LVA: value of captured minus value of mover
        mover = board.get(frm, color + '?')
        score += PIECE_VALUES.get(captured[1],0) * 10
        score += 100 - PIECE_VALUES.get(mover[1],0)
    if len(mv) > 4:
        # promotion
        promo = mv[4]
        # prefer queen
        if promo == 'q':
            score += 800
        else:
            score += 700
    # small random to diversify equal scores
    score += random.randint(0,9)
    return score
