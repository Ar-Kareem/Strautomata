
import math
from typing import Dict, List, Tuple

# Piece-square tables (from white perspective)
PST = {
    'P': [
         0,   0,   0,   0,   0,   0,   0,   0,
        50,  50,  50,  50,  50,  50,  50,  50,
        10,  10,  20,  30,  30,  20,  10,  10,
         5,   5,  10,  25,  25,  10,   5,   5,
         0,   0,   0,  20,  20,   0,   0,   0,
         5,  -5, -10,   0,   0, -10,  -5,   5,
         5,  10,  10, -20, -20,  10,  10,   5,
         0,   0,   0,   0,   0,   0,   0,   0
    ],
    'N': [
        -50, -40, -30, -30, -30, -30, -40, -50,
        -40, -20,   0,   5,   5,   0, -20, -40,
        -30,   5,  10,  15,  15,  10,   5, -30,
        -30,   0,  15,  20,  20,  15,   0, -30,
        -30,   5,  15,  20,  20,  15,   5, -30,
        -30,   0,  10,  15,  15,  10,   0, -30,
        -40, -20,   0,   0,   0,   0, -20, -40,
        -50, -40, -30, -30, -30, -30, -40, -50
    ],
    'B': [
        -20, -10, -10, -10, -10, -10, -10, -20,
        -10,   0,   0,   0,   0,   0,   0, -10,
        -10,   0,   5,  10,  10,   5,   0, -10,
        -10,   5,   5,  10,  10,   5,   5, -10,
        -10,   0,  10,  10,  10,  10,   0, -10,
        -10,  10,  10,  10,  10,  10,  10, -10,
        -10,   5,   0,   0,   0,   0,   5, -10,
        -20, -10, -10, -10, -10, -10, -10, -20
    ],
    'R': [
         0,   0,   0,   0,   0,   0,   0,   0,
         5,  10,  10,  10,  10,  10,  10,   5,
        -5,   0,   0,   0,   0,   0,   0,  -5,
        -5,   0,   0,   0,   0,   0,   0,  -5,
        -5,   0,   0,   0,   0,   0,   0,  -5,
        -5,   0,   0,   0,   0,   0,   0,  -5,
        -5,   0,   0,   0,   0,   0,   0,  -5,
         0,   0,   0,   5,   5,   0,   0,   0
    ],
    'Q': [
        -20, -10, -10,  -5,  -5, -10, -10, -20,
        -10,   0,   0,   0,   0,   0,   0, -10,
        -10,   0,   5,   5,   5,   5,   0, -10,
         -5,   0,   5,   5,   5,   5,   0,  -5,
          0,   0,   5,   5,   5,   5,   0,  -5,
        -10,   5,   5,   5,   5,   5,   0, -10,
        -10,   0,   5,   0,   0,   0,   0, -10,
        -20, -10, -10,  -5,  -5, -10, -10, -20
    ],
    'K': [
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -20, -30, -30, -40, -40, -30, -30, -20,
        -10, -20, -20, -20, -20, -20, -20, -10,
         20,  20,   0,   0,   0,   0,  20,  20,
         20,  30,  10,   0,   0,  10,  30,  20
    ]
}

PIECE_VALUE = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 0}

FILES = 'abcdefgh'
RANKS = '12345678'

def sq_to_idx(sq: str) -> int:
    return (int(sq[1]) - 1) * 8 + FILES.index(sq[0])

def idx_to_sq(idx: int) -> str:
    return FILES[idx % 8] + RANKS[idx // 8]

def in_bounds(file: int, rank: int) -> bool:
    return 0 <= file < 8 and 0 <= rank < 8

def find_king(board: Dict[str,str], color: str) -> str:
    target = color + 'K'
    for sq, p in board.items():
        if p == target:
            return sq
    return ""

def is_square_attacked(board: Dict[str,str], square: str, by_color: str) -> bool:
    f = FILES.index(square[0])
    r = RANKS.index(square[1])

    # Pawn attacks
    pawn_dir = 1 if by_color == 'w' else -1
    for df in (-1, 1):
        nf, nr = f + df, r + pawn_dir
        if in_bounds(nf, nr):
            sq = FILES[nf] + RANKS[nr]
            if board.get(sq) == by_color + 'P':
                return True

    # Knight attacks
    knight_moves = [(1,2),(2,1),(2,-1),(1,-2),(-1,-2),(-2,-1),(-2,1),(-1,2)]
    for df, dr in knight_moves:
        nf, nr = f+df, r+dr
        if in_bounds(nf, nr):
            sq = FILES[nf] + RANKS[nr]
            if board.get(sq) == by_color + 'N':
                return True

    # King attacks
    for df in (-1,0,1):
        for dr in (-1,0,1):
            if df==0 and dr==0: continue
            nf, nr = f+df, r+dr
            if in_bounds(nf, nr):
                sq = FILES[nf] + RANKS[nr]
                if board.get(sq) == by_color + 'K':
                    return True

    # Sliding pieces
    directions = {
        'B': [(1,1),(1,-1),(-1,1),(-1,-1)],
        'R': [(1,0),(-1,0),(0,1),(0,-1)],
        'Q': [(1,1),(1,-1),(-1,1),(-1,-1),(1,0),(-1,0),(0,1),(0,-1)]
    }
    for piece, dirs in directions.items():
        for df, dr in dirs:
            nf, nr = f+df, r+dr
            while in_bounds(nf, nr):
                sq = FILES[nf] + RANKS[nr]
                if sq in board:
                    if board[sq] == by_color + piece or board[sq] == by_color + 'Q':
                        return True
                    break
                nf += df
                nr += dr

    return False

def in_check(board: Dict[str,str], color: str) -> bool:
    king_sq = find_king(board, color)
    if not king_sq:
        return False
    opp = 'b' if color == 'w' else 'w'
    return is_square_attacked(board, king_sq, opp)

def generate_pseudo_moves(board: Dict[str,str], color: str) -> List[str]:
    moves = []
    opp = 'b' if color == 'w' else 'w'
    for sq, piece in board.items():
        if piece[0] != color:
            continue
        ptype = piece[1]
        f = FILES.index(sq[0])
        r = RANKS.index(sq[1])
        if ptype == 'P':
            direction = 1 if color == 'w' else -1
            start_rank = 1 if color == 'w' else 6
            promote_rank = 7 if color == 'w' else 0
            # one step
            nf, nr = f, r + direction
            if in_bounds(nf, nr):
                to_sq = FILES[nf] + RANKS[nr]
                if to_sq not in board:
                    if nr == promote_rank:
                        for promo in 'qrbn':
                            moves.append(sq + to_sq + promo)
                    else:
                        moves.append(sq + to_sq)
                    # two steps
                    if r == start_rank:
                        nr2 = r + 2*direction
                        to_sq2 = FILES[nf] + RANKS[nr2]
                        if to_sq2 not in board:
                            moves.append(sq + to_sq2)
            # captures
            for df in (-1,1):
                nf, nr = f+df, r+direction
                if in_bounds(nf, nr):
                    to_sq = FILES[nf] + RANKS[nr]
                    if to_sq in board and board[to_sq][0] == opp:
                        if nr == promote_rank:
                            for promo in 'qrbn':
                                moves.append(sq + to_sq + promo)
                        else:
                            moves.append(sq + to_sq)
        elif ptype == 'N':
            for df, dr in [(1,2),(2,1),(2,-1),(1,-2),(-1,-2),(-2,-1),(-2,1),(-1,2)]:
                nf, nr = f+df, r+dr
                if in_bounds(nf, nr):
                    to_sq = FILES[nf] + RANKS[nr]
                    if to_sq not in board or board[to_sq][0] == opp:
                        moves.append(sq + to_sq)
        elif ptype in ('B','R','Q'):
            dirs = []
            if ptype in ('B','Q'):
                dirs += [(1,1),(1,-1),(-1,1),(-1,-1)]
            if ptype in ('R','Q'):
                dirs += [(1,0),(-1,0),(0,1),(0,-1)]
            for df, dr in dirs:
                nf, nr = f+df, r+dr
                while in_bounds(nf, nr):
                    to_sq = FILES[nf] + RANKS[nr]
                    if to_sq in board:
                        if board[to_sq][0] == opp:
                            moves.append(sq + to_sq)
                        break
                    moves.append(sq + to_sq)
                    nf += df
                    nr += dr
        elif ptype == 'K':
            for df in (-1,0,1):
                for dr in (-1,0,1):
                    if df==0 and dr==0: continue
                    nf, nr = f+df, r+dr
                    if in_bounds(nf, nr):
                        to_sq = FILES[nf] + RANKS[nr]
                        if to_sq not in board or board[to_sq][0] == opp:
                            moves.append(sq + to_sq)
            # castling (by position)
            if color == 'w' and sq == 'e1':
                if board.get('h1') == 'wR' and 'f1' not in board and 'g1' not in board:
                    if not in_check(board, color) and not is_square_attacked(board, 'f1', opp) and not is_square_attacked(board, 'g1', opp):
                        moves.append('e1g1')
                if board.get('a1') == 'wR' and 'b1' not in board and 'c1' not in board and 'd1' not in board:
                    if not in_check(board, color) and not is_square_attacked(board, 'd1', opp) and not is_square_attacked(board, 'c1', opp):
                        moves.append('e1c1')
            if color == 'b' and sq == 'e8':
                if board.get('h8') == 'bR' and 'f8' not in board and 'g8' not in board:
                    if not in_check(board, color) and not is_square_attacked(board, 'f8', opp) and not is_square_attacked(board, 'g8', opp):
                        moves.append('e8g8')
                if board.get('a8') == 'bR' and 'b8' not in board and 'c8' not in board and 'd8' not in board:
                    if not in_check(board, color) and not is_square_attacked(board, 'd8', opp) and not is_square_attacked(board, 'c8', opp):
                        moves.append('e8c8')
    return moves

def make_move(board: Dict[str,str], move: str) -> Dict[str,str]:
    new_board = dict(board)
    frm = move[:2]
    to = move[2:4]
    promo = move[4] if len(move) > 4 else None
    piece = new_board.pop(frm)
    if to in new_board:
        new_board.pop(to)
    if promo:
        piece = piece[0] + promo.upper()
    # handle castling rook move
    if piece[1] == 'K':
        if frm == 'e1' and to == 'g1':
            # move rook
            if 'h1' in new_board:
                new_board.pop('h1')
                new_board['f1'] = 'wR'
        elif frm == 'e1' and to == 'c1':
            if 'a1' in new_board:
                new_board.pop('a1')
                new_board['d1'] = 'wR'
        elif frm == 'e8' and to == 'g8':
            if 'h8' in new_board:
                new_board.pop('h8')
                new_board['f8'] = 'bR'
        elif frm == 'e8' and to == 'c8':
            if 'a8' in new_board:
                new_board.pop('a8')
                new_board['d8'] = 'bR'
    new_board[to] = piece
    return new_board

def generate_legal_moves(board: Dict[str,str], color: str) -> List[str]:
    moves = []
    for mv in generate_pseudo_moves(board, color):
        nb = make_move(board, mv)
        if not in_check(nb, color):
            moves.append(mv)
    return moves

def evaluate(board: Dict[str,str], color: str) -> int:
    score = 0
    for sq, piece in board.items():
        pcolor, ptype = piece[0], piece[1]
        idx = sq_to_idx(sq)
        if pcolor == 'w':
            score += PIECE_VALUE[ptype] + PST[ptype][idx]
        else:
            # mirror for black
            midx = 63 - idx
            score -= PIECE_VALUE[ptype] + PST[ptype][midx]
    return score if color == 'w' else -score

MATE = 100000

def negamax(board: Dict[str,str], color: str, depth: int, alpha: int, beta: int) -> Tuple[int, str]:
    legal = generate_legal_moves(board, color)
    if depth == 0 or not legal:
        if not legal:
            if in_check(board, color):
                return -MATE, ""
            else:
                return 0, ""
        return evaluate(board, color), ""
    best_move = legal[0]
    # move ordering: captures first
    def is_capture(mv):
        return mv[2:4] in board
    legal.sort(key=lambda m: (not is_capture(m), len(m)), reverse=False)
    for mv in legal:
        nb = make_move(board, mv)
        score, _ = negamax(nb, 'b' if color == 'w' else 'w', depth-1, -beta, -alpha)
        score = -score
        if score > alpha:
            alpha = score
            best_move = mv
        if alpha >= beta:
            break
    return alpha, best_move

def policy(pieces: Dict[str,str], to_play: str, memory: dict) -> Tuple[str, dict]:
    color = 'w' if to_play == 'white' else 'b'
    legal = generate_legal_moves(pieces, color)
    if not legal:
        # no legal moves; return any string to satisfy interface
        return ("0000", memory)
    # search depth
    depth = 3
    _, best = negamax(pieces, color, depth, -MATE, MATE)
    if best not in legal:
        best = legal[0]
    return best, memory
