
import math
import random
from typing import Dict, Tuple, List

# Simple chess engine policy: pick best move by lightweight static eval
# Exposed API:
# def policy(pieces: dict[str, str], to_play: str) -> str

# Piece values
VALUE = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}

# Board helpers
FILES = 'abcdefgh'
RANKS = '12345678'
ALL_SQUARES = [f + r for r in RANKS for f in FILES]
SQUARE_IDX = {sq: i for i, sq in enumerate(ALL_SQUARES)}

# Directions for sliding pieces
DIRS_ROOK = [(1, 0), (-1, 0), (0, 1), (0, -1)]
DIRS_BISHOP = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
DIRS_QUEEN = DIRS_ROOK + DIRS_BISHOP
KNIGHT_DIRS = [(2, 1), (1, 2), (-1, 2), (-2, 1), (-2, -1), (-1, -2), (1, -2), (2, -1)]
KING_DIRS = [(1,0), (-1,0), (0,1), (0,-1), (1,1), (1,-1), (-1,1), (-1,-1)]

# Utilities
def sq_to_coord(sq: str) -> Tuple[int,int]:
    return FILES.index(sq[0]), RANKS.index(sq[1])

def coord_to_sq(x: int, y: int) -> str:
    if 0 <= x < 8 and 0 <= y < 8:
        return FILES[x] + RANKS[y]
    return None

def on_board(x: int, y: int) -> bool:
    return 0 <= x < 8 and 0 <= y < 8

def piece_color(pc: str) -> str:
    return 'white' if pc[0] == 'w' else 'black'

def piece_type(pc: str) -> str:
    return pc[1]

# Build a board mapping for convenience
def build_board(pieces: Dict[str,str]) -> Dict[str,str]:
    board = {}
    for sq, pc in pieces.items():
        board[sq] = pc
    return board

# Apply a move (UCI-like) to a pieces dict, return new dict
def apply_move(pieces: Dict[str,str], move: str, to_play: str) -> Dict[str,str]:
    # move like 'e2e4' or 'a7a8q'
    new = dict(pieces)
    src = move[0:2]
    dst = move[2:4]
    promo = move[4] if len(move) == 5 else None
    if src not in new:
        # illegal in given pieces; just return new unchanged
        return new
    pc = new.pop(src)
    # capture if present
    if dst in new:
        new.pop(dst)
    # handle promotion
    if promo:
        color = pc[0]
        new[dst] = color + promo.upper()
    else:
        new[dst] = pc
    return new

# Generate pseudo-legal moves for a side (used as fallback or opponent mobility estimator)
def generate_pseudo_moves(pieces: Dict[str,str], side: str) -> List[str]:
    moves = []
    for src, pc in pieces.items():
        if piece_color(pc) != side:
            continue
        ptype = piece_type(pc)
        x, y = sq_to_coord(src)
        if ptype == 'P':
            dir_y = 1 if side == 'white' else -1
            # single step
            nx, ny = x, y + dir_y
            nsq = coord_to_sq(nx, ny)
            if nsq and nsq not in pieces:
                # promotion?
                if (side == 'white' and ny == 7) or (side == 'black' and ny == 0):
                    moves.append(src + nsq + 'q')
                else:
                    moves.append(src + nsq)
                # double step
                start_rank = 1 if side == 'white' else 6
                ny2 = y + 2*dir_y
                nsq2 = coord_to_sq(x, ny2)
                if y == start_rank and nsq2 and nsq not in pieces and nsq2 not in pieces:
                    moves.append(src + nsq2)
            # captures
            for dx in (-1, 1):
                nx, ny = x + dx, y + dir_y
                nsq = coord_to_sq(nx, ny)
                if nsq and nsq in pieces and piece_color(pieces[nsq]) != side:
                    if (side == 'white' and ny == 7) or (side == 'black' and ny == 0):
                        moves.append(src + nsq + 'q')
                    else:
                        moves.append(src + nsq)
            # ignore en-passant
        elif ptype == 'N':
            for dx, dy in KNIGHT_DIRS:
                nx, ny = x+dx, y+dy
                nsq = coord_to_sq(nx, ny)
                if nsq:
                    if nsq not in pieces or piece_color(pieces[nsq]) != side:
                        moves.append(src + nsq)
        elif ptype == 'B' or ptype == 'R' or ptype == 'Q':
            directions = DIRS_QUEEN if ptype == 'Q' else (DIRS_BISHOP if ptype == 'B' else DIRS_ROOK)
            for dx, dy in directions:
                nx, ny = x+dx, y+dy
                while on_board(nx, ny):
                    nsq = coord_to_sq(nx, ny)
                    if nsq not in pieces:
                        moves.append(src + nsq)
                    else:
                        if piece_color(pieces[nsq]) != side:
                            moves.append(src + nsq)
                        break
                    nx += dx; ny += dy
        elif ptype == 'K':
            for dx, dy in KING_DIRS:
                nx, ny = x+dx, y+dy
                nsq = coord_to_sq(nx, ny)
                if nsq:
                    if nsq not in pieces or piece_color(pieces[nsq]) != side:
                        moves.append(src + nsq)
            # ignore castling specifics
    # If no moves found (shouldn't happen in legal positions), just return empty
    return moves

# Attack detection: does any piece of 'attacker' attack target square?
def is_square_attacked(pieces: Dict[str,str], target_sq: str, attacker: str) -> bool:
    tx, ty = sq_to_coord(target_sq)
    for sq, pc in pieces.items():
        if piece_color(pc) != attacker:
            continue
        ptype = piece_type(pc)
        x, y = sq_to_coord(sq)
        dx = tx - x
        dy = ty - y
        if ptype == 'P':
            dir_y = 1 if attacker == 'white' else -1
            # pawn attacks diagonally
            if dy == dir_y and abs(dx) == 1:
                return True
        elif ptype == 'N':
            if (abs(dx), abs(dy)) in [(1,2),(2,1)]:
                return True
        elif ptype == 'B':
            if abs(dx) == abs(dy) and dx != 0:
                step_x = 1 if dx>0 else -1
                step_y = 1 if dy>0 else -1
                cx, cy = x+step_x, y+step_y
                blocked = False
                while (cx, cy) != (tx, ty):
                    sqc = coord_to_sq(cx, cy)
                    if sqc in pieces:
                        blocked = True
                        break
                    cx += step_x; cy += step_y
                if not blocked:
                    return True
        elif ptype == 'R':
            if (dx == 0) ^ (dy == 0):
                step_x = 0 if dx==0 else (1 if dx>0 else -1)
                step_y = 0 if dy==0 else (1 if dy>0 else -1)
                cx, cy = x+step_x, y+step_y
                blocked = False
                while (cx, cy) != (tx, ty):
                    sqc = coord_to_sq(cx, cy)
                    if sqc in pieces:
                        blocked = True
                        break
                    cx += step_x; cy += step_y
                if not blocked:
                    return True
        elif ptype == 'Q':
            if (abs(dx) == abs(dy) and dx != 0) or ((dx == 0) ^ (dy == 0)):
                step_x = 0 if dx==0 else (1 if dx>0 else -1) if dx!=0 else 0
                step_y = 0 if dy==0 else (1 if dy>0 else -1) if dy!=0 else 0
                cx, cy = x+step_x, y+step_y
                blocked = False
                while (cx, cy) != (tx, ty):
                    sqc = coord_to_sq(cx, cy)
                    if sqc in pieces:
                        blocked = True
                        break
                    cx += step_x; cy += step_y
                if not blocked:
                    return True
        elif ptype == 'K':
            if max(abs(dx), abs(dy)) == 1:
                return True
    return False

# Material sum for side
def material_sum(pieces: Dict[str,str], side: str) -> int:
    s = 0
    for pc in pieces.values():
        if piece_color(pc) == side:
            s += VALUE.get(piece_type(pc), 0)
    return s

# Evaluate static position for side to play (higher better for side)
def evaluate_position(pieces: Dict[str,str], side: str) -> float:
    my = material_sum(pieces, side)
    opp = material_sum(pieces, 'white' if side == 'black' else 'black')
    score = my - opp
    # King safety: penalize if our king is attacked
    # Locate kings
    myking = None
    oppking = None
    for sq, pc in pieces.items():
        if pc == ('wK' if side == 'white' else 'bK'):
            myking = sq
        if pc == ('bK' if side == 'white' else 'wK'):
            oppking = sq
    if myking and is_square_attacked(pieces, myking, 'white' if side=='black' else 'black'):
        score -= 500  # being in check is bad
    if oppking and is_square_attacked(pieces, oppking, side):
        score += 400  # attacking king is good
    # Mobility: count pseudo moves
    my_moves = len(generate_pseudo_moves(pieces, side))
    opp_moves = len(generate_pseudo_moves(pieces, 'white' if side=='black' else 'black'))
    score += 10 * (my_moves - opp_moves)
    return score

# Main policy function
def policy(pieces: Dict[str,str], to_play: str) -> str:
    # Try to get provided legal_moves global variable
    legal = None
    try:
        legal = globals().get('legal_moves', None)
    except Exception:
        legal = None
    # If not provided, generate pseudo-legal moves for side
    if not legal:
        legal = generate_pseudo_moves(pieces, to_play)
        # Ensure there is at least one move; if none, return a dummy (shouldn't happen)
        if not legal:
            # find any move-like fallback
            for s in pieces:
                pc = pieces[s]
                if piece_color(pc) == to_play:
                    for t in ALL_SQUARES:
                        if t != s:
                            return s + t
            return next(iter(pieces.keys())) + next(iter(pieces.keys()))
    # Evaluate each move
    best_move = legal[0]
    best_score = -1e9
    for m in legal:
        new_pos = apply_move(pieces, m, to_play)
        # immediate capture bonus (value of captured piece)
        capture_bonus = 0
        dst = m[2:4]
        promo = m[4] if len(m) == 5 else None
        if dst in pieces and piece_color(pieces[dst]) != to_play:
            capture_bonus += VALUE.get(piece_type(pieces[dst]), 0)
        if promo:
            # treat promotion to queen
            capture_bonus += VALUE.get(promo.upper(), 900)
        # evaluate static position from our perspective
        score = evaluate_position(new_pos, to_play)
        # combine
        total = score + 0.01 * capture_bonus
        # additional heuristics:
        # if move gives check to opponent king, big boost
        # find opponent king
        opp = 'white' if to_play == 'black' else 'black'
        oppking_sq = None
        for sq, pc in new_pos.items():
            if pc == ('wK' if opp == 'white' else 'bK'):
                oppking_sq = sq
                break
        if oppking_sq and is_square_attacked(new_pos, oppking_sq, to_play):
            total += 5000
        # Penalize if our king becomes attacked
        myking_sq = None
        for sq, pc in new_pos.items():
            if pc == ('wK' if to_play == 'white' else 'bK'):
                myking_sq = sq
                break
        if myking_sq and is_square_attacked(new_pos, myking_sq, opp):
            total -= 2000
        # Slightly prefer promotions to queen
        if promo:
            if promo.lower() == 'q':
                total += 800
            else:
                total += 300
        # choose maximum
        if total > best_score:
            best_score = total
            best_move = m
    return best_move

# If module is run directly, provide a tiny test (no output expected)
if __name__ == "__main__":
    # simple sanity check (won't be executed by the arena)
    pass
