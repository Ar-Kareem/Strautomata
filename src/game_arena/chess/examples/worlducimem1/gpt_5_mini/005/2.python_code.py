
#!/usr/bin/env python3
# Chess move selection policy implementing the required API.
# - Generates legal moves (no castling, no en-passant due to lack of history).
# - Evaluates moves by material + tactical bonuses (captures, promotions, checks).
# - Returns a move string from the generated legal moves (falls back to pseudo-legal if needed).

from typing import Dict, Tuple, List

PIECE_VALUES = {
    'P': 100,
    'N': 320,
    'B': 330,
    'R': 500,
    'Q': 900,
    'K': 20000
}

FILES = 'abcdefgh'
RANKS = '12345678'

def sq_to_xy(sq: str):
    return FILES.index(sq[0]), RANKS.index(sq[1])

def xy_to_sq(x: int, y: int):
    if 0 <= x < 8 and 0 <= y < 8:
        return FILES[x] + RANKS[y]
    return None

def in_board(x: int, y: int):
    return 0 <= x < 8 and 0 <= y < 8

def copy_board(board: Dict[str,str]) -> Dict[str,str]:
    return dict(board)

def find_king(board: Dict[str,str], color: str):
    target = ('w' if color=='white' else 'b') + 'K'
    for sq, p in board.items():
        if p == target:
            return sq
    return None

def is_attacked(square: str, by_color: str, board: Dict[str,str]) -> bool:
    # Return True if square is attacked by any piece of by_color ('white'/'black')
    bx, by = sq_to_xy(square)
    attacker_prefix = 'w' if by_color == 'white' else 'b'
    # Pawn attacks
    if by_color == 'white':
        # white pawns capture from rank-1 to rank (so pawn at y-1 attacks y)
        for dx in (-1, 1):
            sx = bx + dx
            sy = by - 1
            if in_board(sx, sy):
                s = xy_to_sq(sx, sy)
                if board.get(s) == attacker_prefix + 'P':
                    return True
    else:
        for dx in (-1, 1):
            sx = bx + dx
            sy = by + 1
            if in_board(sx, sy):
                s = xy_to_sq(sx, sy)
                if board.get(s) == attacker_prefix + 'P':
                    return True
    # Knights
    for dx, dy in [(1,2),(2,1),(2,-1),(1,-2),(-1,-2),(-2,-1),(-2,1),(-1,2)]:
        sx, sy = bx+dx, by+dy
        if in_board(sx, sy):
            s = xy_to_sq(sx, sy)
            if board.get(s) == attacker_prefix + 'N':
                return True
    # Sliding pieces: Rooks/Queens (orthogonal), Bishops/Queens (diagonal)
    # Orthogonal
    for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
        sx, sy = bx+dx, by+dy
        while in_board(sx, sy):
            s = xy_to_sq(sx, sy)
            p = board.get(s)
            if p:
                if p[0] == attacker_prefix:
                    if p[1] in ('R','Q'):
                        return True
                break
            sx += dx; sy += dy
    # Diagonals
    for dx, dy in [(1,1),(1,-1),(-1,1),(-1,-1)]:
        sx, sy = bx+dx, by+dy
        while in_board(sx, sy):
            s = xy_to_sq(sx, sy)
            p = board.get(s)
            if p:
                if p[0] == attacker_prefix:
                    if p[1] in ('B','Q'):
                        return True
                break
            sx += dx; sy += dy
    # King adjacency
    for dx in (-1,0,1):
        for dy in (-1,0,1):
            if dx == 0 and dy == 0:
                continue
            sx, sy = bx+dx, by+dy
            if in_board(sx, sy):
                s = xy_to_sq(sx, sy)
                if board.get(s) == attacker_prefix + 'K':
                    return True
    return False

def generate_pseudo_legal_moves(board: Dict[str,str], color: str) -> List[str]:
    moves = []
    prefix = 'w' if color == 'white' else 'b'
    pawn_dir = 1 if color == 'white' else -1
    for sq, piece in list(board.items()):
        if not piece.startswith(prefix):
            continue
        ptype = piece[1]
        x, y = sq_to_xy(sq)
        if ptype == 'P':
            # forward 1
            ny = y + pawn_dir
            if in_board(x, ny):
                to_sq = xy_to_sq(x, ny)
                if to_sq not in board:
                    # promotion?
                    if ny == 7 or ny == 0:
                        # generate promotions (choose queen primarily)
                        for promo in ['q','r','b','n']:
                            moves.append(sq + to_sq + promo)
                    else:
                        moves.append(sq + to_sq)
                    # forward 2
                    start_rank = 1 if color == 'white' else 6
                    ny2 = y + 2*pawn_dir
                    if y == start_rank and in_board(x, ny2):
                        mid_sq = xy_to_sq(x, y + pawn_dir)
                        to_sq2 = xy_to_sq(x, ny2)
                        if mid_sq not in board and to_sq2 not in board:
                            moves.append(sq + to_sq2)
            # captures
            for dx in (-1, 1):
                nx = x + dx
                ny = y + pawn_dir
                if in_board(nx, ny):
                    to_sq = xy_to_sq(nx, ny)
                    target = board.get(to_sq)
                    if target and not target.startswith(prefix):
                        if ny == 7 or ny == 0:
                            for promo in ['q','r','b','n']:
                                moves.append(sq + to_sq + promo)
                        else:
                            moves.append(sq + to_sq)
            # Note: en-passant not implemented (requires history)
        elif ptype == 'N':
            for dx, dy in [(1,2),(2,1),(2,-1),(1,-2),(-1,-2),(-2,-1),(-2,1),(-1,2)]:
                nx, ny = x+dx, y+dy
                if in_board(nx, ny):
                    to_sq = xy_to_sq(nx, ny)
                    target = board.get(to_sq)
                    if not target or not target.startswith(prefix):
                        moves.append(sq + to_sq)
        elif ptype == 'B' or ptype == 'R' or ptype == 'Q':
            directions = []
            if ptype in ('B','Q'):
                directions += [(1,1),(1,-1),(-1,1),(-1,-1)]
            if ptype in ('R','Q'):
                directions += [(1,0),(-1,0),(0,1),(0,-1)]
            for dx, dy in directions:
                nx, ny = x+dx, y+dy
                while in_board(nx, ny):
                    to_sq = xy_to_sq(nx, ny)
                    target = board.get(to_sq)
                    if not target:
                        moves.append(sq + to_sq)
                    else:
                        if not target.startswith(prefix):
                            moves.append(sq + to_sq)
                        break
                    nx += dx; ny += dy
        elif ptype == 'K':
            for dx in (-1,0,1):
                for dy in (-1,0,1):
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = x+dx, y+dy
                    if in_board(nx, ny):
                        to_sq = xy_to_sq(nx, ny)
                        target = board.get(to_sq)
                        if not target or not target.startswith(prefix):
                            moves.append(sq + to_sq)
            # Castling omitted (no history)
        else:
            # unknown piece type - skip
            pass
    return moves

def make_move(board: Dict[str,str], move: str, color: str) -> Dict[str,str]:
    nb = copy_board(board)
    from_sq = move[0:2]
    to_sq = move[2:4]
    piece = nb.get(from_sq)
    if not piece:
        return nb
    # handle promotion
    if len(move) == 5:
        promo = move[4].upper()
        # place promoted piece
        nb[to_sq] = ('w' if color=='white' else 'b') + promo
    else:
        nb[to_sq] = piece
    if from_sq in nb:
        del nb[from_sq]
    # capture handled by overwriting
    return nb

def generate_legal_moves(board: Dict[str,str], color: str) -> List[str]:
    pseudo = generate_pseudo_legal_moves(board, color)
    legal = []
    for mv in pseudo:
        nb = make_move(board, mv, color)
        king_sq = find_king(nb, color)
        if not king_sq:
            # no king (shouldn't happen normally) - treat as illegal
            continue
        if not is_attacked(king_sq, 'white' if color=='black' else 'black', nb):
            legal.append(mv)
    # fallback: if no legal moves, return pseudo-legal to ensure a move is returned
    if not legal and pseudo:
        return pseudo
    return legal

def evaluate_board(board: Dict[str,str], my_color: str) -> int:
    # Positive means advantage for my_color
    my_pref = 'w' if my_color == 'white' else 'b'
    score = 0
    for p in board.values():
        val = PIECE_VALUES.get(p[1], 0)
        if p[0] == my_pref:
            score += val
        else:
            score -= val
    return score

def move_score(board: Dict[str,str], move: str, color: str) -> Tuple[int, int]:
    # Returns (primary_score, secondary) - higher better. secondary for tie-breaking.
    legal_after = True
    from_sq = move[0:2]
    to_sq = move[2:4]
    piece = board.get(from_sq)
    target = board.get(to_sq)
    score = 0
    # capture value
    if target:
        score += PIECE_VALUES.get(target[1], 0) * 10  # weight captures heavily
    # promotion
    if len(move) == 5:
        # big bonus
        score += 20000
    # simulate
    nb = make_move(board, move, color)
    # check whether move gives check to opponent
    opponent = 'white' if color == 'black' else 'black'
    king_sq = find_king(nb, opponent)
    if king_sq and is_attacked(king_sq, color, nb):
        score += 250  # bonus for check
    # material evaluation (1-ply)
    mat = evaluate_board(nb, color)
    # mobility after move
    opp_moves = generate_legal_moves(nb, opponent)
    mobility = len(opp_moves)
    # Combine: material + tactical score - opponent mobility (prefer to reduce opp mobility)
    primary = mat * 1 + score - mobility * 5
    # secondary tie-breaker: prefer moves that increase our mobility
    our_moves_after = generate_legal_moves(nb, color)
    secondary = len(our_moves_after)
    return int(primary), int(secondary)

def find_best_move(board: Dict[str,str], color: str) -> str:
    legal = generate_legal_moves(board, color)
    if not legal:
        # no moves found: should not happen frequently; fallback to some pseudo-legal or arbitrary
        pseudo = generate_pseudo_legal_moves(board, color)
        if pseudo:
            return pseudo[0]
        else:
            # No moves at all: return a noop-like (not ideal). Choose first movable piece to adjacent if possible.
            for sq, p in board.items():
                if p[0] == ('w' if color=='white' else 'b'):
                    x,y = sq_to_xy(sq)
                    for dx in (-1,0,1):
                        for dy in (-1,0,1):
                            if dx==0 and dy==0: continue
                            nx,ny = x+dx, y+dy
                            if in_board(nx,ny):
                                to = xy_to_sq(nx,ny)
                                return sq + to
            # ultimate fallback (shouldn't get here)
            return next(iter(board.keys())) + next(iter(board.keys()))
    # Search for mate first
    for mv in legal:
        nb = make_move(board, mv, color)
        opponent = 'white' if color == 'black' else 'black'
        opp_leg = generate_legal_moves(nb, opponent)
        king_sq = find_king(nb, opponent)
        in_check = king_sq and is_attacked(king_sq, color, nb)
        if in_check and not opp_leg:
            return mv  # mate
    # Evaluate moves
    best = None
    best_score = None
    for mv in legal:
        primary, secondary = move_score(board, mv, color)
        key = (primary, secondary)
        if best is None or key > best_score:
            best = mv
            best_score = key
    return best

def policy(pieces: Dict[str,str], to_play: str, memory: Dict) -> Tuple[str, Dict]:
    """
    pieces: dict mapping squares to piece codes (e.g., 'e1': 'wK')
    to_play: 'white' or 'black'
    memory: dict persisted between calls (not used here)
    Returns: (move_string, memory)
    """
    # Defensive copy of pieces
    board = dict(pieces)
    mv = find_best_move(board, to_play)
    return mv, memory if memory is not None else {}

# If run as script, provide a tiny self-test (does not execute in the arena)
if __name__ == "__main__":
    # Simple starting mini-test position
    pieces = {
        'e1': 'wK', 'e8': 'bK',
        'd1': 'wQ', 'd8': 'bQ',
        'a2': 'wP', 'a7': 'bP'
    }
    move, mem = policy(pieces, 'white', {})
    print("Chosen move:", move)
