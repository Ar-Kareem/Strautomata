
import copy
from typing import Dict, List, Tuple

# Simple chess policy: generate legal moves (no castling, no en-passant),
# filter leaves-king-in-check moves, then use 2-ply negamax with alpha-beta.
# Returns a UCI move string, e.g., 'e2e4' or 'a7a8q' for promotions.

FILES = "abcdefgh"
RANKS = "12345678"
PIECE_VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}

# Piece-square tables small heuristics (center preference)
PST = {
    'P': [
         0,  0,  0,  0,  0,  0,  0,  0,
         5, 10, 10,-20,-20, 10, 10,  5,
         5, -5,-10,  0,  0,-10, -5,  5,
         0,  0,  0, 20, 20,  0,  0,  0,
         5,  5, 10, 25, 25, 10,  5,  5,
        10, 10, 20, 30, 30, 20, 10, 10,
        50, 50, 50, 50, 50, 50, 50, 50,
         0,  0,  0,  0,  0,  0,  0,  0
    ],
    'N': [
       -50,-40,-30,-30,-30,-30,-40,-50,
       -40,-20,  0,  5,  5,  0,-20,-40,
       -30,  5, 10, 15, 15, 10,  5,-30,
       -30,  0, 15, 20, 20, 15,  0,-30,
       -30,  5, 15, 20, 20, 15,  5,-30,
       -30,  0, 10, 15, 15, 10,  0,-30,
       -40,-20,  0,  0,  0,  0,-20,-40,
       -50,-40,-30,-30,-30,-30,-40,-50,
    ],
    'B': [
       -20,-10,-10,-10,-10,-10,-10,-20,
       -10,  5,  0,  0,  0,  0,  5,-10,
       -10, 10, 10, 10, 10, 10, 10,-10,
       -10,  0, 10, 10, 10, 10,  0,-10,
       -10,  5,  5, 10, 10,  5,  5,-10,
       -10,  0,  5, 10, 10,  5,  0,-10,
       -10,  0,  0,  0,  0,  0,  0,-10,
       -20,-10,-10,-10,-10,-10,-10,-20,
    ],
    'R': [
         0,  0,  5, 10, 10,  5,  0,  0,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
         5, 10, 10, 10, 10, 10, 10,  5,
         0,  0,  0,  0,  0,  0,  0,  0,
    ],
    'Q': [
       -20,-10,-10, -5, -5,-10,-10,-20,
       -10,  0,  0,  0,  0,  0,  0,-10,
       -10,  0,  5,  5,  5,  5,  0,-10,
        -5,  0,  5,  5,  5,  5,  0, -5,
         0,  0,  5,  5,  5,  5,  0, -5,
       -10,  5,  5,  5,  5,  5,  0,-10,
       -10,  0,  5,  0,  0,  0,  0,-10,
       -20,-10,-10, -5, -5,-10,-10,-20,
    ],
    'K': [
       -30,-40,-40,-50,-50,-40,-40,-30,
       -30,-40,-40,-50,-50,-40,-40,-30,
       -30,-40,-40,-50,-50,-40,-40,-30,
       -30,-40,-40,-50,-50,-40,-40,-30,
       -20,-30,-30,-40,-40,-30,-30,-20,
       -10,-20,-20,-20,-20,-20,-20,-10,
        20, 20,  0,  0,  0,  0, 20, 20,
        20, 30, 10,  0,  0, 10, 30, 20,
    ]
}

def sq_to_xy(sq: str) -> Tuple[int,int]:
    return FILES.index(sq[0]), RANKS.index(sq[1])

def xy_to_sq(x: int, y: int) -> str:
    return FILES[x] + RANKS[y]

def in_board(x: int, y: int) -> bool:
    return 0 <= x < 8 and 0 <= y < 8

def board_from_pieces(pieces: Dict[str,str]) -> Dict[Tuple[int,int], str]:
    b = {}
    for sq, pc in pieces.items():
        x,y = sq_to_xy(sq)
        b[(x,y)] = pc
    return b

def pieces_of_color(board: Dict[Tuple[int,int], str], color: str) -> List[Tuple[Tuple[int,int], str]]:
    res = []
    for (x,y), pc in board.items():
        if pc[0] == color:
            res.append(((x,y), pc[1]))
    return res

def generate_pseudo_moves(board: Dict[Tuple[int,int], str], color: str) -> List[Tuple[str,str,str]]:
    # returns list of (from_sq, to_sq, promotion) where promotion is '' or one of 'q','r','b','n'
    moves = []
    enemy = 'b' if color == 'w' else 'w'
    forward = 1 if color == 'w' else -1
    start_rank = 1 if color == 'w' else 6
    promote_rank = 7 if color == 'w' else 0

    for (x,y), pc in list(board.items()):
        if pc[0] != color: continue
        piece = pc[1]
        from_sq = xy_to_sq(x,y)
        if piece == 'P':
            # forward one
            ny = y + forward
            if in_board(x, ny) and (x,ny) not in board:
                # promotion?
                if ny == promote_rank:
                    for p in ['q','r','b','n']:
                        moves.append((from_sq, xy_to_sq(x,ny), p))
                else:
                    moves.append((from_sq, xy_to_sq(x,ny), ''))
                    # two squares
                    if y == start_rank:
                        ny2 = y + 2*forward
                        if in_board(x, ny2) and (x,ny2) not in board:
                            moves.append((from_sq, xy_to_sq(x,ny2), ''))
            # captures
            for dx in (-1, 1):
                nx = x + dx
                ny = y + forward
                if in_board(nx, ny) and (nx,ny) in board and board[(nx,ny)][0] == enemy:
                    if ny == promote_rank:
                        for p in ['q','r','b','n']:
                            moves.append((from_sq, xy_to_sq(nx,ny), p))
                    else:
                        moves.append((from_sq, xy_to_sq(nx,ny), ''))
            # Note: en-passant not implemented
        elif piece == 'N':
            for dx,dy in [(1,2),(2,1),(2,-1),(1,-2),(-1,-2),(-2,-1),(-2,1),(-1,2)]:
                nx,ny = x+dx, y+dy
                if not in_board(nx,ny): continue
                if (nx,ny) not in board or board[(nx,ny)][0] == enemy:
                    moves.append((from_sq, xy_to_sq(nx,ny), ''))
        elif piece == 'B' or piece == 'R' or piece == 'Q':
            directions = []
            if piece in ('B','Q'):
                directions += [(1,1),(1,-1),(-1,1),(-1,-1)]
            if piece in ('R','Q'):
                directions += [(1,0),(-1,0),(0,1),(0,-1)]
            for dx,dy in directions:
                nx,ny = x+dx, y+dy
                while in_board(nx,ny):
                    if (nx,ny) not in board:
                        moves.append((from_sq, xy_to_sq(nx,ny), ''))
                    else:
                        if board[(nx,ny)][0] == enemy:
                            moves.append((from_sq, xy_to_sq(nx,ny), ''))
                        break
                    nx += dx; ny += dy
        elif piece == 'K':
            for dx in (-1,0,1):
                for dy in (-1,0,1):
                    if dx==0 and dy==0: continue
                    nx,ny = x+dx, y+dy
                    if not in_board(nx,ny): continue
                    if (nx,ny) not in board or board[(nx,ny)][0] == enemy:
                        moves.append((from_sq, xy_to_sq(nx,ny), ''))
            # Note: castling not implemented
    return moves

def make_move(board: Dict[Tuple[int,int], str], move: Tuple[str,str,str], color: str) -> Dict[Tuple[int,int], str]:
    newb = board.copy()
    fx,fy = sq_to_xy(move[0])
    tx,ty = sq_to_xy(move[1])
    pc = newb.pop((fx,fy))
    # promotion
    promo = move[2]
    if promo:
        newb[(tx,ty)] = (color + promo.upper())
    else:
        newb[(tx,ty)] = pc
    return newb

def find_king(board: Dict[Tuple[int,int], str], color: str) -> None:
    for (x,y), pc in board.items():
        if pc == color + 'K':
            return (x,y)
    return None

def generate_attack_squares(board: Dict[Tuple[int,int], str], by_color: str) -> List[Tuple[int,int]]:
    # Return list of squares attacked by by_color pieces (may include occupied squares).
    attacks = []
    enemy = 'b' if by_color == 'w' else 'w'
    for (x,y), pc in board.items():
        if pc[0] != by_color: continue
        piece = pc[1]
        if piece == 'P':
            forward = 1 if by_color == 'w' else -1
            for dx in (-1,1):
                nx,ny = x+dx, y+forward
                if in_board(nx,ny):
                    attacks.append((nx,ny))
        elif piece == 'N':
            for dx,dy in [(1,2),(2,1),(2,-1),(1,-2),(-1,-2),(-2,-1),(-2,1),(-1,2)]:
                nx,ny = x+dx, y+dy
                if in_board(nx,ny):
                    attacks.append((nx,ny))
        elif piece in ('B','R','Q'):
            directions = []
            if piece in ('B','Q'):
                directions += [(1,1),(1,-1),(-1,1),(-1,-1)]
            if piece in ('R','Q'):
                directions += [(1,0),(-1,0),(0,1),(0,-1)]
            for dx,dy in directions:
                nx,ny = x+dx, y+dy
                while in_board(nx,ny):
                    attacks.append((nx,ny))
                    if (nx,ny) in board:
                        break
                    nx += dx; ny += dy
        elif piece == 'K':
            for dx in (-1,0,1):
                for dy in (-1,0,1):
                    if dx==0 and dy==0: continue
                    nx,ny = x+dx, y+dy
                    if in_board(nx,ny):
                        attacks.append((nx,ny))
    return attacks

def is_square_attacked(board: Dict[Tuple[int,int], str], sq: Tuple[int,int], by_color: str) -> bool:
    # faster check by enumerating attackers directly
    ax,ay = sq
    # pawns
    if by_color == 'w':
        for dx in (-1,1):
            px,py = ax+dx, ay-1  # white pawns attack down->y-1? Wait: coordinate mapping: rank index 0 is '1'. White moves up (y+1).
            # Correction: white pawn attacks y+1.
        # We'll implement consistent: sq_to_xy maps '1'->0, '8'->7; white forward is +1.
    # Instead use generate_attack_squares:
    attacks = generate_attack_squares(board, by_color)
    return sq in attacks

def legal_moves(board: Dict[Tuple[int,int], str], color: str) -> List[Tuple[str,str,str]]:
    pseudo = generate_pseudo_moves(board, color)
    legal = []
    enemy = 'b' if color == 'w' else 'w'
    for move in pseudo:
        newb = make_move(board, move, color)
        # find king square after move
        king_sq = find_king(newb, color)
        if king_sq is None:
            # Shouldn't happen but skip move if no king (illegal)
            continue
        if is_square_attacked(newb, king_sq, enemy):
            continue
        legal.append(move)
    return legal

def evaluate_board(board: Dict[Tuple[int,int], str], color: str) -> int:
    # Score from perspective of 'color' (positive good for color)
    my = 0
    opp = 0
    for (x,y), pc in board.items():
        val = PIECE_VALUES.get(pc[1], 0)
        pst = PST.get(pc[1], [0]*64)
        idx = y*8 + x
        if pc[0] == color:
            my += val + pst[idx]//1
        else:
            opp += val + pst[idx]//1
    # mobility small bonus
    my_moves = len(legal_moves(board, color))
    opp_moves = len(legal_moves(board, 'b' if color == 'w' else 'w'))
    score = (my - opp) + 10*(my_moves - opp_moves)
    return score

def negamax(board: Dict[Tuple[int,int], str], color: str, depth: int, alpha: int, beta: int) -> None:
    # returns (score, best_move)
    legal = legal_moves(board, color)
    if depth == 0 or not legal:
        # check terminal
        if not legal:
            # if no legal moves: check for checkmate or stalemate
            king_sq = find_king(board, color)
            enemy = 'b' if color == 'w' else 'w'
            if king_sq is not None and is_square_attacked(board, king_sq, enemy):
                return (-999999, None)  # checkmate for side to move
            else:
                return (0, None)  # stalemate
        return (evaluate_board(board, color), None)
    best_move = None
    best_score = -10**9
    # Move ordering: try captures/promotions first (MVV-LVA simple heuristic)
    def move_score_for_order(mv):
        _, to_sq, promo = mv
        tx,ty = sq_to_xy(to_sq)
        target = board.get((tx,ty))
        score = 0
        if target:
            score += PIECE_VALUES.get(target[1], 0)
        if promo:
            score += 900  # promotions are important
        return -score  # negative for sorting ascending to try big captures first
    legal_sorted = sorted(legal, key=move_score_for_order)
    for mv in legal_sorted:
        newb = make_move(board, mv, color)
        enemy = 'b' if color == 'w' else 'w'
        sc, _ = negamax(newb, enemy, depth-1, -beta, -alpha)
        sc = -sc
        if sc > best_score:
            best_score = sc
            best_move = mv
        alpha = max(alpha, sc)
        if alpha >= beta:
            break
    return best_score, best_move

def policy(pieces: Dict[str,str], to_play: str) -> str:
    # main entry point
    color = 'w' if to_play == 'white' else 'b'
    board = board_from_pieces(pieces)
    # generate legal moves
    legal = legal_moves(board, color)
    if not legal:
        # no legal moves: return a dummy (shouldn't happen in arena); pick any pseudo-legal move if exists
        pseudo = generate_pseudo_moves(board, color)
        if pseudo:
            mv = pseudo[0]
            return mv[0] + mv[1] + (mv[2] if mv[2] else '')
        # forced fallback
        return 'a1a1'
    # If only one legal move, return it
    if len(legal) == 1:
        m = legal[0]
        return m[0] + m[1] + (m[2] if m[2] else '')
    # Use 2-ply search
    _, best = negamax(board, color, depth=2, alpha=-10**9, beta=10**9)
    if best is None:
        # fallback to best material capture or first legal
        # prefer captures
        captures = []
        for mv in legal:
            tx,ty = sq_to_xy(mv[1])
            if (tx,ty) in board:
                captures.append(mv)
        mv = captures[0] if captures else legal[0]
    else:
        mv = best
    return mv[0] + mv[1] + (mv[2] if mv[2] else '')

# Expose policy as module-level function
if __name__ == "__main__":
    # Simple test position if run standalone
    sample = {'e2': 'wP', 'e7': 'bP', 'e1':'wK', 'e8':'bK', 'd1':'wQ'}
    print(policy(sample, 'white'))
