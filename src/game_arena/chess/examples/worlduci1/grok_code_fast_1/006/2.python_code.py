
import sys
from typing import Dict, List, Tuple, Optional

# Piece weights for evaluation
PIECE_VALUES = {
    'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000
}

# Basic piece-square tables (flipped for black)
PST_PAWN = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [50, 50, 50, 50, 50, 50, 50, 50],
    [10, 10, 20, 30, 30, 20, 10, 10],
    [5, 5, 10, 25, 25, 10, 5, 5],
    [0, 0, 0, 20, 20, 0, 0, 0],
    [5, -5, -10, 0, 0, -10, -5, 5],
    [5, 10, 10, -20, -20, 10, 10, 5],
    [0, 0, 0, 0, 0, 0, 0, 0]
]

PST_KNIGHT = [
    [-50, -40, -30, -30, -30, -30, -40, -50],
    [-40, -20, 0, 0, 0, 0, -20, -40],
    [-30, 0, 10, 15, 15, 10, 0, -30],
    [-30, 5, 15, 20, 20, 15, 5, -30],
    [-30, 0, 15, 20, 20, 15, 0, -30],
    [-30, 5, 10, 15, 15, 10, 5, -30],
    [-40, -20, 0, 5, 5, 0, -20, -40],
    [-50, -40, -30, -30, -30, -30, -40, -50]
]

PST_BISHOP = [
    [-20, -10, -10, -10, -10, -10, -10, -20],
    [-10, 0, 0, 0, 0, 0, 0, -10],
    [-10, 0, 5, 10, 10, 5, 0, -10],
    [-10, 5, 5, 10, 10, 5, 5, -10],
    [-10, 0, 10, 10, 10, 10, 0, -10],
    [-10, 10, 10, 10, 10, 10, 10, -10],
    [-10, 5, 0, 0, 0, 0, 5, -10],
    [-20, -10, -10, -10, -10, -10, -10, -20]
]

PST_ROOK = [
    [0, 0, 0, 5, 5, 0, 0, 0],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [5, 10, 10, 10, 10, 10, 10, 5],
    [0, 0, 0, 0, 0, 0, 0, 0]
]

PST_QUEEN = [
    [-20, -10, -10, -5, -5, -10, -10, -20],
    [-10, 0, 0, 0, 0, 0, 0, -10],
    [-10, 0, 5, 5, 5, 5, 0, -10],
    [-5, 0, 5, 5, 5, 5, 0, -5],
    [0, 0, 5, 5, 5, 5, 0, -5],
    [-10, 5, 5, 5, 5, 5, 0, -10],
    [-10, 0, 5, 0, 0, 0, 0, -10],
    [-20, -10, -10, -5, -5, -10, -10, -20]
]

PST_KING = [
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-20, -30, -30, -40, -40, -30, -30, -20],
    [-10, -20, -20, -20, -20, -20, -20, -10],
    [20, 20, 0, 0, 0, 0, 20, 20],
    [20, 30, 10, 0, 0, 10, 30, 20]
]

PST = {
    'P': PST_PAWN,
    'N': PST_KNIGHT,
    'B': PST_BISHOP,
    'R': PST_ROOK,
    'Q': PST_QUEEN,
    'K': PST_KING
}

def square_to_cords(square: str) -> Tuple[int, int]:
    file, rank = ord(square[0]) - ord('a'), int(square[1]) - 1
    return rank, file

def cords_to_square(rank: int, file: int) -> str:
    return chr(ord('a') + file) + str(rank + 1)

def policy(pieces: dict[str, str], to_play: str) -> str:
    color = to_play[0]  # 'w' or 'b'
    enemy = 'b' if color == 'w' else 'w'
    
    # Build board
    board = [[None] * 8 for _ in range(8)]
    king_pos = {}
    for sq, p in pieces.items():
        r, f = square_to_cords(sq)
        board[r][f] = p
        if p[1] == 'K':
            king_pos[p[0]] = (r, f)
    
    def is_in_check(board, color, king_pos):
        kr, kf = king_pos[color]
        for dr in [-1, 0, 1]:
            for df in [-1, 0, 1]:
                if dr == 0 and df == 0: continue
                nr, nf = kr + dr, kf + df
                if 0 <= nr < 8 and 0 <= nf < 8:
                    piece = board[nr][nf]
                    if piece and piece[0] == enemy:
                        if piece[1] in ['Q', 'R', 'B', 'N', 'P', 'K']:
                            if can_attack(board, nr, nf, kr, kf, enemy):
                                return True
        return False
    
    def can_attack(board, sr, sf, tr, tf, color):
        piece = board[sr][sf]
        if not piece or piece[0] != color: return False
        pt = piece[1]
        dr, df = tr - sr, tf - sf
        if pt == 'P':
            if color == 'w':
                return df in [-1, 1] and dr == -1
            else:
                return df in [-1, 1] and dr == 1
        elif pt == 'N':
            return abs(dr * df) in [2, -2]
        elif pt in ['R', 'B', 'Q']:
            dir_valid = False
            if pt == 'R' and (dr == 0 or df == 0):
                dir_valid = True
            elif pt == 'B' and abs(dr) == abs(df):
                dir_valid = True
            elif pt == 'Q':
                dir_valid = abs(dr) == abs(df) or dr == 0 or df == 0
            if dir_valid:
                step_r = 1 if dr > 0 else (-1 if dr < 0 else 0)
                step_f = 1 if df > 0 else (-1 if df < 0 else 0)
                r, f = sr + step_r, sf + step_f
                while r != tr or f != tf:
                    if board[r][f]:
                        return False
                    r += step_r
                    f += step_f
                return True
        elif pt == 'K':
            return abs(dr) <= 1 and abs(df) <= 1
        return False
    
    def is_legal_move(board, from_r, from_f, to_r, to_f, color, king_pos):
        piece = board[from_r][from_f]
        if not piece or piece[0] != color: return False
        pt = piece[1]
        dr, df = to_r - from_r, to_f - from_f
        # Basic reach
        can_reach = can_attack(board, from_r, from_f, to_r, to_f, color)
        if not can_reach: return False
        # Special for pawns
        if pt == 'P':
            cap = board[to_r][to_f] is not None
            if cap and df == 0: return False
            if not cap and df != 0: return False
        # Simulate move
        orig_piece = board[to_r][to_f]
        board[to_r][to_f] = piece
        board[from_r][from_f] = None
        if pt == 'K':
            king_pos[color] = (to_r, to_f)
        in_check = is_in_check(board, color, king_pos)
        # Restore
        board[from_r][from_f] = piece
        board[to_r][to_f] = orig_piece
        if pt == 'K':
            king_pos[color] = (from_r, from_f)
        return not in_check
    
    def generate_moves(board, color, king_pos):
        moves = []
        for r in range(8):
            for f in range(8):
                piece = board[r][f]
                if piece and piece[0] == color:
                    pt = piece[1]
                    if pt == 'P':
                        drs = [-1] if color == 'w' else [1]
                        for dr in drs:
                            for df in [-1, 0, 1]:
                                nr, nf = r + dr, f + df
                                if 0 <= nr < 8 and 0 <= nf < 8:
                                    if df == 0 and not board[nr][nf]:  # push
                                        if nr == 0 or nr == 7:  # promotion
                                            for p in ['q', 'r', 'b', 'n']:
                                                move = cords_to_square(r, f) + cords_to_square(nr, nf) + p
                                                moves.append(move)
                                        else:
                                            move = cords_to_square(r, f) + cords_to_square(nr, nf)
                                            moves.append(move)
                                    elif df in [-1, 1] and board[nr][nf] and board[nr][nf][0] != color:  # cap
                                        if nr == 0 or nr == 7:
                                            for p in ['q', 'r', 'b', 'n']:
                                                move = cords_to_square(r, f) + cords_to_square(nr, nf) + p
                                                moves.append(move)
                                        else:
                                            move = cords_to_square(r, f) + cords_to_square(nr, nf)
                                            moves.append(move)
                        # double push
                        if (r == 6 and color == 'w') or (r == 1 and color == 'b'):
                            nr = r + drs[0] * 2
                            if not board[r + drs[0]][f] and not board[nr][f]:
                                moves.append(cords_to_square(r, f) + cords_to_square(nr, f))
                    elif pt == 'N':
                        for dr, df in [(-2,-1), (-2,1), (-1,-2), (-1,2), (1,-2), (1,2), (2,-1), (2,1)]:
                            nr, nf = r + dr, f + df
                            if 0 <= nr < 8 and 0 <= nf < 8:
                                target = board[nr][nf]
                                if not target or target[0] != color:
                                    move = cords_to_square(r, f) + cords_to_square(nr, nf)
                                    moves.append(move)
                    elif pt in ['R', 'B', 'Q']:
                        dirs = []
                        if pt == 'R': dirs = [(0,1),(0,-1),(1,0),(-1,0)]
                        elif pt == 'B': dirs = [(1,1),(1,-1),(-1,1),(-1,-1)]
                        else: dirs = [(0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]
                        for dr, df in dirs:
                            nr, nf = r + dr, f + df
                            while 0 <= nr < 8 and 0 <= nf < 8:
                                target = board[nr][nf]
                                if target and target[0] == color: break
                                move = cords_to_square(r, f) + cords_to_square(nr, nf)
                                moves.append(move)
                                if target: break
                                nr += dr
                                nf += df
                    elif pt == 'K':
                        for dr in [-1, 0, 1]:
                            for df in [-1, 0, 1]:
                                if dr == 0 and df == 0: continue
                                nr, nf = r + dr, f + df
                                if 0 <= nr < 8 and 0 <= nf < 8:
                                    target = board[nr][nf]
                                    if not target or target[0] != color:
                                        move = cords_to_square(r, f) + cords_to_square(nr, nf)
                                        moves.append(move)
                        # Castling
                        if not is_in_check(board, color, king_pos):
                            if color == 'w':
                                if r == 7 and f == 4:
                                    # kingside
                                    if not board[7][5] and not board[7][6] and board[7][7] == 'wR':
                                        if not is_legal_move(board, 7, 4, 7, 5, color, king_pos) and not is_legal_move(board, 7, 4, 7, 6, color, king_pos):
                                            moves.append('e1g1')
                                    # queenside
                                    if not board[7][1] and not board[7][2] and not board[7][3] and board[7][0] == 'wR':
                                        if not is_legal_move(board, 7, 4, 7, 3, color, king_pos) and not is_legal_move(board, 7, 4, 7, 2, color, king_pos):
                                            moves.append('e1c1')
                            else:
                                if r == 0 and f == 4:
                                    # kingside
                                    if not board[0][5] and not board[0][6] and board[0][7] == 'bR':
                                        if not is_legal_move(board, 0, 4, 0, 5, color, king_pos) and not is_legal_move(board, 0, 4, 0, 6, color, king_pos):
                                            moves.append('e8g8')
                                    # queenside
                                    if not board[0][1] and not board[0][2] and not board[0][3] and board[0][0] == 'bR':
                                        if not is_legal_move(board, 0, 4, 0, 3, color, king_pos) and not is_legal_move(board, 0, 4, 0, 2, color, king_pos):
                                            moves.append('e8c8')
        # Filter legal
        legal = []
        for m in moves:
            if len(m) == 4:
                fr, to = m[:2], m[2:]
            elif len(m) == 5:
                fr, to = m[:2], m[2:4]
            else:
                continue
            fr_r, fr_f = square_to_cords(fr)
            to_r, to_f = square_to_cords(to)
            if is_legal_move(board, fr_r, fr_f, to_r, to_f, color, king_pos):
                legal.append(m)
        return legal
    
    def evaluate(board, color, king_pos):
        score = 0
        for r in range(8):
            for f in range(8):
                piece = board[r][f]
                if piece:
                    val = PIECE_VALUES[piece[1]]
                    pst = PST[piece[1]]
                    if piece[0] == 'w':
                        score += val + pst[7 - r][f]
                    else:
                        score -= val + pst[r][f]
        if is_in_check(board, enemy, king_pos):  # enemy in check
            if not generate_moves(board, enemy, king_pos):  # checkmate
                return 99999 if color == to_play[0] else -99999
        if not is_in_check(board, color, king_pos) and not generate_moves(board, color, king_pos):  # stalemate
            return 0
        return score if color == 'w' else -score
    
    moves = generate_moves(board, color, king_pos)
    if not moves:
        return ''  # Should not happen
    
    best_move = None
    best_score = -sys.maxsize
    for m in moves:
        # Simulate move
        fr, to = m[:2], m[2:4] if len(m) == 4 else m[2:4]
        fr_r, fr_f = square_to_cords(fr)
        to_r, to_f = square_to_cords(to)
        prom = m[4] if len(m) > 4 else None
        piece = board[fr_r][fr_f]
        orig_to = board[to_r][to_f]
        board[to_r][to_f] = piece if not prom else color + prom.upper()
        board[fr_r][fr_f] = None
        if piece[1] == 'K':
            new_k_pos = king_pos.copy()
            new_k_pos[color] = (to_r, to_f)
        else:
            new_k_pos = king_pos
        score = evaluate(board, color, new_k_pos)
        # Restore
        board[fr_r][fr_f] = piece
        board[to_r][to_f] = orig_to
        if score > best_score:
            best_score = score
            best_move = m
    
    return best_move if best_move else moves[0]
