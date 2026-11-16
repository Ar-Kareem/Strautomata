
import random
import math
from typing import List, Dict, Tuple

# --- Configuration ---
PIECE_VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}

# Piece-square tables for positional evaluation
PAWN_TABLE = [0,0,0,0,0,0,0,0, 5,10,10,-20,-20,10,10,5, 5,-5,-10,0,0,-10,-5,5,
              0,0,0,20,20,0,0,0, 5,5,10,25,25,10,5,5, 10,10,20,30,30,20,10,10,
              50,50,50,50,50,50,50,50, 0,0,0,0,0,0,0,0]

KNIGHT_TABLE = [-50,-40,-30,-30,-30,-30,-40,-50, -40,-20,0,0,0,0,-20,-40,
                -30,0,10,15,15,10,0,-30, -30,5,15,20,20,15,5,-30,
                -30,0,15,20,20,15,0,-30, -30,5,10,15,15,10,5,-30,
                -40,-20,0,5,5,0,-20,-40, -50,-40,-30,-30,-30,-30,-40,-50]

BISHOP_TABLE = [-20,-10,-10,-10,-10,-10,-10,-20, -10,5,0,0,0,0,5,-10,
                -10,10,10,10,10,10,10,-10, -10,0,10,10,10,10,0,-10,
                -10,5,5,10,10,5,5,-10, -10,0,5,10,10,5,0,-10,
                -10,10,10,5,5,10,10,-10, -20,-10,-10,-10,-10,-10,-10,-20]

ROOK_TABLE = [0,0,0,5,5,0,0,0, -5,0,0,0,0,0,0,-5, -5,0,0,0,0,0,0,-5,
              -5,0,0,0,0,0,0,-5, -5,0,0,0,0,0,0,-5, 5,10,10,10,10,10,10,5,
              0,0,0,0,0,0,0,0]

QUEEN_TABLE = [-20,-10,-10,-5,-5,-10,-10,-20, -10,0,0,0,0,0,0,-10,
               -10,0,5,5,5,5,0,-10, -5,0,5,5,5,5,0,-5,
               0,0,5,5,5,5,0,-5, -10,5,5,5,5,5,0,-10,
               -10,0,5,0,0,0,0,-10, -20,-10,-10,-5,-5,-10,-10,-20]

KING_TABLE = [20,30,10,0,0,10,30,20, 20,20,0,0,0,0,20,20,
            -10,-20,-20,-20,-20,-20,-20,-10, -20,-30,-30,-40,-40,-30,-30,-20,
            -30,-40,-40,-50,-50,-40,-40,-30, -30,-40,-40,-50,-50,-40,-40,-30,
            -30,-40,-40,-50,-50,-40,-40,-30, -30,-40,-40,-50,-50,-40,-40,-30]

# Precomputed move deltas
KNIGHT_DELTAS = [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]
KING_DELTAS = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
ROOK_DIRS = [(-1,0),(1,0),(0,-1),(0,1)]
BISHOP_DIRS = [(-1,-1),(-1,1),(1,-1),(1,1)]
QUEEN_DIRS = ROOK_DIRS + BISHOP_DIRS

# --- Core Functions ---
def sq_to_idx(square: str) -> int:
    """Convert algebraic square to 0-63 index (a1=0, h8=63)"""
    file = ord(square[0]) - ord('a')
    rank = int(square[1]) - 1
    return rank * 8 + file

def idx_to_sq(idx: int) -> str:
    """Convert 0-63 index to algebraic square"""
    rank = idx // 8
    file = idx % 8
    return chr(ord('a') + file) + str(rank + 1)

def create_board(pieces: Dict[str, str]) -> List[str]:
    """Create 64-length board from pieces dict"""
    board = [''] * 64
    for sq, pc in pieces.items():
        board[sq_to_idx(sq)] = pc
    return board

def is_square_attacked(board: List[str], target_idx: int, attacker_color: str) -> bool:
    """Check if a square is attacked by given color"""
    target_file, target_rank = target_idx % 8, target_idx // 8
    
    # Knights
    for df, dr in KNIGHT_DELTAS:
        f, r = target_file + df, target_rank + dr
        if 0 <= f < 8 and 0 <= r < 8:
            idx = r * 8 + f
            if board[idx] == attacker_color + 'N':
                return True
    
    # Kings
    for df, dr in KING_DELTAS:
        f, r = target_file + df, target_rank + dr
        if 0 <= f < 8 and 0 <= r < 8:
            idx = r * 8 + f
            if board[idx] == attacker_color + 'K':
                return True
    
    # Pawns
    direction = -1 if attacker_color == 'w' else 1
    for df in [-1, 1]:
        f, r = target_file + df, target_rank - direction
        if 0 <= f < 8 and 0 <= r < 8:
            idx = r * 8 + f
            if board[idx] == attacker_color + 'P':
                return True
    
    # Sliding pieces (Queen/Rook)
    for df, dr in ROOK_DIRS:
        f, r = target_file + df, target_rank + dr
        while 0 <= f < 8 and 0 <= r < 8:
            idx = r * 8 + f
            pc = board[idx]
            if pc:
                if pc[0] == attacker_color and pc[1] in ('R', 'Q'):
                    return True
                break
            f += df
            r += dr
    
    # Sliding pieces (Queen/Bishop)
    for df, dr in BISHOP_DIRS:
        f, r = target_file + df, target_rank + dr
        while 0 <= f < 8 and 0 <= r < 8:
            idx = r * 8 + f
            pc = board[idx]
            if pc:
                if pc[0] == attacker_color and pc[1] in ('B', 'Q'):
                    return True
                break
            f += df
            r += dr
    
    return False

def in_check(board: List[str], color: str) -> bool:
    """Check if king of given color is in check"""
    king_idx = next((i for i, pc in enumerate(board) if pc == color + 'K'), None)
    if king_idx is None:
        return False
    opponent = 'b' if color == 'w' else 'w'
    return is_square_attacked(board, king_idx, opponent)

def generate_pseudo_moves(board: List[str], from_idx: int, piece: str) -> List[int]:
    """Generate pseudo-legal moves ignoring check validation"""
    piece_color, piece_type = piece[0], piece[1]
    from_file, from_rank = from_idx % 8, from_idx // 8
    moves = []
    
    if piece_type == 'N':
        for df, dr in KNIGHT_DELTAS:
            f, r = from_file + df, from_rank + dr
            if 0 <= f < 8 and 0 <= r < 8:
                to_idx = r * 8 + f
                if not board[to_idx] or board[to_idx][0] != piece_color:
                    moves.append(to_idx)
    
    elif piece_type == 'K':
        for df, dr in KING_DELTAS:
            f, r = from_file + df, from_rank + dr
            if 0 <= f < 8 and 0 <= r < 8:
                to_idx = r * 8 + f
                if not board[to_idx] or board[to_idx][0] != piece_color:
                    moves.append(to_idx)
    
    elif piece_type == 'R':
        for df, dr in ROOK_DIRS:
            f, r = from_file + df, from_rank + dr
            while 0 <= f < 8 and 0 <= r < 8:
                to_idx = r * 8 + f
                if not board[to_idx]:
                    moves.append(to_idx)
                else:
                    if board[to_idx][0] != piece_color:
                        moves.append(to_idx)
                    break
                f += df
                r += dr
    
    elif piece_type == 'B':
        for df, dr in BISHOP_DIRS:
            f, r = from_file + df, from_rank + dr
            while 0 <= f < 8 and 0 <= r < 8:
                to_idx = r * 8 + f
                if not board[to_idx]:
                    moves.append(to_idx)
                else:
                    if board[to_idx][0] != piece_color:
                        moves.append(to_idx)
                    break
                f += df
                r += dr
    
    elif piece_type == 'Q':
        for df, dr in QUEEN_DIRS:
            f, r = from_file + df, from_rank + dr
            while 0 <= f < 8 and 0 <= r < 8:
                to_idx = r * 8 + f
                if not board[to_idx]:
                    moves.append(to_idx)
                else:
                    if board[to_idx][0] != piece_color:
                        moves.append(to_idx)
                    break
                f += df
                r += dr
    
    elif piece_type == 'P':
        direction = 1 if piece_color == 'w' else -1
        start_rank = 1 if piece_color == 'w' else 6
        
        # Forward push
        to_rank = from_rank + direction
        if 0 <= to_rank < 8:
            to_idx = to_rank * 8 + from_file
            if not board[to_idx]:
                moves.append(to_idx)
                # Two square push
                if from_rank == start_rank:
                    to_rank2 = from_rank + 2 * direction
                    if 0 <= to_rank2 < 8:
                        to_idx2 = to_rank2 * 8 + from_file
                        if not board[to_idx2]:
                            moves.append(to_idx2)
        
        # Captures
        for df in [-1, 1]:
            to_file = from_file + df
            to_rank = from_rank + direction
            if 0 <= to_file < 8 and 0 <= to_rank < 8:
                to_idx = to_rank * 8 + to_file
                if board[to_idx] and board[to_idx][0] != piece_color:
                    moves.append(to_idx)
    
    return moves

def is_legal_move(board: List[str], color: str, move: str) -> bool:
    """Validate that move doesn't leave king in check"""
    new_board = make_move(board, move)
    return not in_check(new_board, color)

def generate_legal_moves(board: List[str], color: str) -> List[str]:
    """Generate all legal UCI moves for given color"""
    moves = []
    for from_idx, pc in enumerate(board):
        if pc and pc[0] == color:
            to_idxs = generate_pseudo_moves(board, from_idx, pc)
            for to_idx in to_idxs:
                move = idx_to_sq(from_idx) + idx_to_sq(to_idx)
                # Handle promotion
                if pc[1] == 'P' and (to_idx // 8 == 0 or to_idx // 8 == 7):
                    for promo in 'qrbn':
                        promo_move = move + promo
                        if is_legal_move(board, color, promo_move):
                            moves.append(promo_move)
                elif is_legal_move(board, color, move):
                    moves.append(move)
    return moves

def make_move(board: List[str], move: str) -> List[str]:
    """Execute move on board copy and return new board"""
    new_board = board[:]
    from_idx = sq_to_idx(move[:2])
    to_idx = sq_to_idx(move[2:4])
    
    promo = move[4] if len(move) == 5 else None
    piece = new_board[from_idx]
    
    new_board[from_idx] = ''
    if promo:
        new_board[to_idx] = piece[0] + promo.upper()
    else:
        new_board[to_idx] = piece
    
    return new_board

def evaluate_board(board: List[str], perspective: str) -> float:
    """Evaluate position from perspective color"""
    score = 0
    for idx, pc in enumerate(board):
        if not pc:
            continue
        color, ptype = pc[0], pc[1]
        value = PIECE_VALUES[ptype]
        bonus = 0
        
        if ptype == 'P':
            bonus = PAWN_TABLE[idx] if color == 'w' else PAWN_TABLE[63-idx]
        elif ptype == 'N':
            bonus = KNIGHT_TABLE[idx] if color == 'w' else KNIGHT_TABLE[63-idx]
        elif ptype == 'B':
            bonus = BISHOP_TABLE[idx] if color == 'w' else BISHOP_TABLE[63-idx]
        elif ptype == 'R':
            bonus = ROOK_TABLE[idx] if color == 'w' else ROOK_TABLE[63-idx]
        elif ptype == 'Q':
            bonus = QUEEN_TABLE[idx] if color == 'w' else QUEEN_TABLE[63-idx]
        elif ptype == 'K':
            bonus = KING_TABLE[idx] if color == 'w' else KING_TABLE[63-idx]
        
        if color == 'w':
            score += value + bonus
        else:
            score -= value + bonus
    
    return score if perspective == 'w' else -score

def alpha_beta(board: List[str], depth: int, alpha: float, beta: float,
               current_color: str, root_color: str) -> float:
    """Alpha-beta search with capture-first move ordering"""
    if depth == 0:
        return evaluate_board(board, root_color)
    
    legal_moves = generate_legal_moves(board, current_color)
    
    if not legal_moves:
        if in_check(board, current_color):
            return -float('inf') if current_color == root_color else float('inf')
        return 0
    
    # Move ordering: captures first
    scored = []
    for move in legal_moves:
        to_idx = sq_to_idx(move[2:4])
        captured = board[to_idx]
        score = PIECE_VALUES.get(captured[1], 0) if captured else 0
        scored.append((-score, move))
    scored.sort()
    ordered_moves = [m for _, m in scored]
    
    is_max = (current_color == root_color)
    next_color = 'b' if current_color == 'w' else 'w'
    
    for move in ordered_moves:
        new_board = make_move(board, move)
        eval = alpha_beta(new_board, depth-1, alpha, beta, next_color, root_color)
        
        if is_max:
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        else:
            beta = min(beta, eval)
            if beta <= alpha:
                break
    
    return alpha if is_max else beta

def policy(pieces: Dict[str, str], to_play: str, memory: Dict) -> Tuple[str, Dict]:
    """Select best move using alpha-beta search with dynamic depth"""
    board = create_board(pieces)
    my_color = 'w' if to_play == 'white' else 'b'
    
    # Get legal moves
    legal_moves = generate_legal_moves(board, my_color)
    if not legal_moves:
        return "", memory
    
    # Dynamic depth based on move count
    move_count = len(legal_moves)
    max_depth = 2 if move_count > 30 else 3 if move_count > 10 else 4
    
    best_move = legal_moves[0]
    best_score = -float('inf')
    
    # Iterative deepening
    for depth in range(1, max_depth + 1):
        for move in legal_moves:
            new_board = make_move(board, move)
            score = alpha_beta(new_board, depth-1, -float('inf'), float('inf'),
                             'b' if my_color == 'w' else 'w', my_color)
            if score > best_score:
                best_score = score
                best_move = move
    
    return best_move, memory
