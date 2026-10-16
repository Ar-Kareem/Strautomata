
import random
import math
from typing import Dict, List, Tuple, Optional

# Piece values
VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}

# Piece-square tables (from White's perspective, 0=a1, 63=h8)
PST = {
    'P': [
        0,  0,  0,  0,  0,  0,  0,  0,
        50, 50, 50, 50, 50, 50, 50, 50,
        10, 10, 20, 30, 30, 20, 10, 10,
        5,  5, 10, 25, 25, 10,  5,  5,
        0,  0,  0, 20, 20,  0,  0,  0,
        5, -5,-10,  0,  0,-10, -5,  5,
        5, 10, 10,-20,-20, 10, 10,  5,
        0,  0,  0,  0,  0,  0,  0,  0
    ],
    'N': [
        -50,-40,-30,-30,-30,-30,-40,-50,
        -40,-20,  0,  0,  0,  0,-20,-40,
        -30,  0, 10, 15, 15, 10,  0,-30,
        -30,  5, 15, 20, 20, 15,  5,-30,
        -30,  0, 15, 20, 20, 15,  0,-30,
        -30,  5, 10, 15, 15, 10,  5,-30,
        -40,-20,  0,  5,  5,  0,-20,-40,
        -50,-40,-30,-30,-30,-30,-40,-50
    ],
    'B': [
        -20,-10,-10,-10,-10,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5, 10, 10,  5,  0,-10,
        -10,  5,  5, 10, 10,  5,  5,-10,
        -10,  0, 10, 10, 10, 10,  0,-10,
        -10, 10, 10, 10, 10, 10, 10,-10,
        -10,  5,  0,  0,  0,  0,  5,-10,
        -20,-10,-10,-10,-10,-10,-10,-20
    ],
    'R': [
        0,  0,  0,  0,  0,  0,  0,  0,
        5, 10, 10, 10, 10, 10, 10,  5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        0,  0,  0,  5,  5,  0,  0,  0
    ],
    'Q': [
        -20,-10,-10, -5, -5,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5,  5,  5,  5,  0,-10,
        -5,  0,  5,  5,  5,  5,  0, -5,
        0,  0,  5,  5,  5,  5,  0, -5,
        -10,  5,  5,  5,  5,  5,  0,-10,
        -10,  0,  5,  0,  0,  0,  0,-10,
        -20,-10,-10, -5, -5,-10,-10,-20
    ],
    'K': [
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -20,-30,-30,-40,-40,-30,-30,-20,
        -10,-20,-20,-20,-20,-20,-20,-10,
        20, 20,  0,  0,  0,  0, 20, 20,
        20, 30, 10,  0,  0, 10, 30, 20
    ]
}

# Precompute knight and king moves for all squares
KNIGHT_MOVES = {}
KING_MOVES = {}
for x in range(8):
    for y in range(8):
        idx = y * 8 + x
        KNIGHT_MOVES[idx] = []
        KING_MOVES[idx] = []
        # Knight
        for dx, dy in [(-2,-1), (-2,1), (-1,-2), (-1,2), (1,-2), (1,2), (2,-1), (2,1)]:
            nx, ny = x+dx, y+dy
            if 0 <= nx < 8 and 0 <= ny < 8:
                KNIGHT_MOVES[idx].append(ny*8 + nx)
        # King
        for dx, dy in [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]:
            nx, ny = x+dx, y+dy
            if 0 <= nx < 8 and 0 <= ny < 8:
                KING_MOVES[idx].append(ny*8 + nx)

def sq_to_idx(sq: str) -> int:
    file = ord(sq[0]) - ord('a')
    rank = int(sq[1]) - 1
    return rank * 8 + file

def idx_to_sq(idx: int) -> str:
    rank = idx // 8
    file = idx % 8
    return chr(ord('a') + file) + str(rank + 1)

def apply_move(pieces: Dict[str, str], move: str) -> Dict[str, str]:
    """Apply a UCI move and return new position dict."""
    new_pieces = dict(pieces)
    start = move[:2]
    end = move[2:4]
    promo = move[4] if len(move) > 4 else None
    
    piece = new_pieces.pop(start, None)
    if piece is None:
        return new_pieces  # Should not happen
    
    # Remove captured piece
    if end in new_pieces:
        del new_pieces[end]
    
    # Handle promotion
    if promo:
        color = piece[0]
        piece = color + promo.upper()
    else:
        # Handle castling (move rook)
        if piece[1] == 'K':
            if start == 'e1' and end == 'g1':
                new_pieces.pop('h1', None)
                new_pieces['f1'] = 'wR'
            elif start == 'e1' and end == 'c1':
                new_pieces.pop('a1', None)
                new_pieces['d1'] = 'wR'
            elif start == 'e8' and end == 'g8':
                new_pieces.pop('h8', None)
                new_pieces['f8'] = 'bR'
            elif start == 'e8' and end == 'c8':
                new_pieces.pop('a8', None)
                new_pieces['d8'] = 'bR'
    
    new_pieces[end] = piece
    return new_pieces

def is_attacked(pieces: Dict[str, str], sq_idx: int, by_color: str) -> bool:
    """Check if square is attacked by given color."""
    x, y = sq_idx % 8, sq_idx // 8
    
    # Pawns
    if by_color == 'w':
        # White pawns attack up-left and up-right (y+1)
        if y < 7:
            if x > 0:
                pc = pieces.get(idx_to_sq(sq_idx + 7))
                if pc == 'wP':
                    return True
            if x < 7:
                pc = pieces.get(idx_to_sq(sq_idx + 9))
                if pc == 'wP':
                    return True
    else:
        # Black pawns attack down-left and down-right (y-1)
        if y > 0:
            if x > 0:
                pc = pieces.get(idx_to_sq(sq_idx - 9))
                if pc == 'bP':
                    return True
            if x < 7:
                pc = pieces.get(idx_to_sq(sq_idx - 7))
                if pc == 'bP':
                    return True
    
    # Knights
    for nidx in KNIGHT_MOVES[sq_idx]:
        pc = pieces.get(idx_to_sq(nidx))
        if pc and pc[0] == by_color and pc[1] == 'N':
            return True
    
    # King
    for kidx in KING_MOVES[sq_idx]:
        pc = pieces.get(idx_to_sq(kidx))
        if pc and pc[0] == by_color and pc[1] == 'K':
            return True
    
    # Rays (Bishop, Rook, Queen)
    directions = [(-1,-1), (-1,1), (1,-1), (1,1), (-1,0), (1,0), (0,-1), (0,1)]
    for i, (dx, dy) in enumerate(directions):
        nx, ny = x, y
        dist = 0
        while True:
            nx += dx
            ny += dy
            dist += 1
            if not (0 <= nx < 8 and 0 <= ny < 8):
                break
            idx = ny*8 + nx
            pc = pieces.get(idx_to_sq(idx))
            if pc:
                if pc[0] == by_color:
                    ptype = pc[1]
                    if i < 4:  # Diagonals
                        if ptype in ('B', 'Q'):
                            return True
                    else:  # Orthogonals
                        if ptype in ('R', 'Q'):
                            return True
                break  # Blocked
    return False

def find_king(pieces: Dict[str, str], color: str) -> Optional[str]:
    king = color + 'K'
    for sq, pc in pieces.items():
        if pc == king:
            return sq
    return None

def is_in_check(pieces: Dict[str, str], color: str) -> bool:
    king_sq = find_king(pieces, color)
    if not king_sq:
        return False
    opp = 'b' if color == 'w' else 'w'
    return is_attacked(pieces, sq_to_idx(king_sq), opp)

def generate_pseudo_legal(pieces: Dict[str, str], color: str) -> List[str]:
    """Generate pseudo-legal moves (including castling, excluding en passant)."""
    moves = []
    opp = 'b' if color == 'w' else 'w'
    
    for sq, pc in pieces.items():
        if pc[0] != color:
            continue
        ptype = pc[1]
        idx = sq_to_idx(sq)
        x, y = idx % 8, idx // 8
        
        if ptype == 'P':
            dy = 1 if color == 'w' else -1
            start_rank = 1 if color == 'w' else 6
            promo_rank = 7 if color == 'w' else 0
            
            # Forward 1
            ny = y + dy
            if 0 <= ny < 8:
                nidx = ny*8 + x
                nsq = idx_to_sq(nidx)
                if nsq not in pieces:
                    if ny == promo_rank:
                        for promo in ['q', 'r', 'b', 'n']:
                            moves.append(sq + nsq + promo)
                    else:
                        moves.append(sq + nsq)
                    
                    # Forward 2 from start
                    if y == start_rank:
                        ny2 = y + 2*dy
                        nidx2 = ny2*8 + x
                        nsq2 = idx_to_sq(nidx2)
                        if nsq2 not in pieces:
                            moves.append(sq + nsq2)
            
            # Captures
            for dx in [-1, 1]:
                nx = x + dx
                if 0 <= nx < 8:
                    ny_cap = y + dy
                    if 0 <= ny_cap < 8:
                        cap_idx = ny_cap*8 + nx
                        cap_sq = idx_to_sq(cap_idx)
                        if cap_sq in pieces and pieces[cap_sq][0] == opp:
                            if ny_cap == promo_rank:
                                for promo in ['q', 'r', 'b', 'n']:
                                    moves.append(sq + cap_sq + promo)
                            else:
                                moves.append(sq + cap_sq)
        
        elif ptype == 'N':
            for nidx in KNIGHT_MOVES[idx]:
                nsq = idx_to_sq(nidx)
                if nsq not in pieces or pieces[nsq][0] == opp:
                    moves.append(sq + nsq)
        
        elif ptype == 'K':
            for kidx in KING_MOVES[idx]:
                ksq = idx_to_sq(kidx)
                if ksq not in pieces or pieces[ksq][0] == opp:
                    moves.append(sq + ksq)
            
            # Castling
            if color == 'w' and sq == 'e1':
                # Kingside
                if 'f1' not in pieces and 'g1' not in pieces:
                    if pieces.get('h1') == 'wR':
                        if not is_in_check(pieces, 'w'):
                            if not is_attacked(pieces, sq_to_idx('f1'), 'b'):
                                if not is_attacked(pieces, sq_to_idx('g1'), 'b'):
                                    moves.append('e1g1')
                # Queenside
                if 'b1' not in pieces and 'c1' not in pieces and 'd1' not in pieces:
                    if pieces.get('a1') == 'wR':
                        if not is_in_check(pieces, 'w'):
                            if not is_attacked(pieces, sq_to_idx('d1'), 'b'):
                                if not is_attacked(pieces, sq_to_idx('c1'), 'b'):
                                    moves.append('e1c1')
            elif color == 'b' and sq == 'e8':
                # Kingside
                if 'f8' not in pieces and 'g8' not in pieces:
                    if pieces.get('h8') == 'bR':
                        if not is_in_check(pieces, 'b'):
                            if not is_attacked(pieces, sq_to_idx('f8'), 'w'):
                                if not is_attacked(pieces, sq_to_idx('g8'), 'w'):
                                    moves.append('e8g8')
                # Queenside
                if 'b8' not in pieces and 'c8' not in pieces and 'd8' not in pieces:
                    if pieces.get('a8') == 'bR':
                        if not is_in_check(pieces, 'b'):
                            if not is_attacked(pieces, sq_to_idx('d8'), 'w'):
                                if not is_attacked(pieces, sq_to_sq('c8'), 'w'):
                                    moves.append('e8c8')
        
        elif ptype in ('B', 'R', 'Q'):
            dirs = []
            if ptype in ('B', 'Q'):
                dirs = [(-1,-1), (-1,1), (1,-1), (1,1)]
            if ptype in ('R', 'Q'):
                dirs += [(-1,0), (1,0), (0,-1), (0,1)]
            
            for dx, dy in dirs:
                nx, ny = x, y
                while True:
                    nx += dx
                    ny += dy
                    if not (0 <= nx < 8 and 0 <= ny < 8):
                        break
                    nidx = ny*8 + nx
                    nsq = idx_to_sq(nidx)
                    if nsq in pieces:
                        if pieces[nsq][0] == opp:
                            moves.append(sq + nsq)
                        break
                    moves.append(sq + nsq)
    
    return moves

def generate_legal_moves(pieces: Dict[str, str], color: str) -> List[str]:
    """Filter pseudo-legal moves to ensure king safety."""
    pseudo = generate_pseudo_legal(pieces, color)
    legal = []
    for move in pseudo:
        new_pieces = apply_move(pieces, move)
        if not is_in_check(new_pieces, color):
            legal.append(move)
    return legal

def evaluate(pieces: Dict[str, str]) -> int:
    """Evaluate from White's perspective (positive = White good)."""
    score = 0
    for sq, pc in pieces.items():
        color, ptype = pc[0], pc[1]
        idx = sq_to_idx(sq)
        val = VALUES[ptype]
        pst = PST[ptype]
        
        if color == 'w':
            pos_val = pst[idx]
            score += val + pos_val
        else:
            # Flip index for Black
            pos_val = pst[63 - idx]
            score -= val + pos_val
    
    # Penalize being in check (for side to move)
    return score

def is_capture(pieces: Dict[str, str], move: str) -> bool:
    end = move[2:4]
    return end in pieces

def search(pieces: Dict[str, str], color: str, depth: int, alpha: int, beta: int) -> Tuple[int, Optional[str]]:
    """Negamax search."""
    if depth == 0:
        # Quiescence: evaluate
        val = evaluate(pieces)
        if color == 'b':
            val = -val
        return val, None
    
    moves = generate_legal_moves(pieces, color)
    
    if not moves:
        # Checkmate or stalemate
        if is_in_check(pieces, color):
            return -1000000 + (10 - depth), None  # Checkmate is bad
        else:
            return 0, None  # Stalemate
    
    # Move ordering: captures first
    moves.sort(key=lambda m: (is_capture(pieces, m), random.random()), reverse=True)
    
    best_move = None
    for move in moves:
        new_pieces = apply_move(pieces, move)
        score, _ = search(new_pieces, 'b' if color == 'w' else 'w', depth - 1, -beta, -alpha)
        score = -score
        
        if score > alpha:
            alpha = score
            best_move = move
            if alpha >= beta:
                break
    
    return alpha, best_move

def policy(pieces: Dict[str, str], to_play: str, legal_moves: List[str] = None) -> str:
    """Select best move from legal_moves."""
    color = 'w' if to_play == 'white' else 'b'
    
    # Handle case where legal_moves might be passed as 3rd argument or keyword
    if legal_moves is None:
        # Try to generate if not provided (fallback)
        legal_moves = generate_legal_moves(pieces, color)
    
    if not legal_moves:
        return ""
    
    if len(legal_moves) == 1:
        return legal_moves[0]
    
    # Evaluate each root move with shallow search
    best_move = legal_moves[0]
    best_score = -999999
    
    # Limit depth based on number of moves to stay within time
    depth = 3 if len(legal_moves) < 15 else 2
    
    for move in legal_moves:
        new_pieces = apply_move(pieces, move)
        # Search opponent's reply
        opp_color = 'b' if color == 'w' else 'w'
        score, _ = search(new_pieces, opp_color, depth - 1, -999999, 999999)
        score = -score  # Negate because we want score from our perspective
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
