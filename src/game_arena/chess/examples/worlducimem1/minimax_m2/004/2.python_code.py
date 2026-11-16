
# -------------------------------------------------------------
# Simple UCI chess engine – policy for the game arena
# -------------------------------------------------------------
import sys
import copy
from typing import Dict, List, Tuple, Optional

# -----------------------------------------------------------------
# Constants and utilities
# -----------------------------------------------------------------

# Piece material values (centipawns)
PIECE_VALUE = {
    'P': 100,
    'N': 320,
    'B': 330,
    'R': 500,
    'Q': 900,
    'K': 0,
}

# Piece‑square tables (PST) for white.
# Indexing: row = 0 (rank 8) … 7 (rank 1), col = 0 (file a) … 7 (file h)
# The table for black is obtained by mirroring vertically.
PAWN_PSQ = [
    0,  0,  0,  0,  0,  0,  0,  0,
    5, 10, 10, -20, -20, 10, 10,  5,
    5, -5, -10, 0, 0, -10, -5, 5,
    0,  0,  0, 20, 20,  0,  0,  0,
    5,  5, 10, 25, 25, 10,  5,  5,
    10, 10, 20, 30, 30, 20, 10, 10,
    50, 50, 50, 50, 50, 50, 50, 50,
    0,  0,  0,  0,  0,  0,  0,  0,
]

KNIGHT_PSQ = [
    -50, -40, -30, -30, -30, -30, -40, -50,
    -40, -20,   0,  5,  5,   0, -20, -40,
    -30,   5, 10, 15, 15, 10,   5, -30,
    -30,   0, 15, 20, 20, 15,   0, -30,
    -30,   5, 15, 20, 20, 15,   5, -30,
    -30,   0, 10, 15, 15, 10,   0, -30,
    -40, -20,   0,  0,  0,   0, -20, -40,
    -50, -40, -30, -30, -30, -30, -40, -50,
]

BISHOP_PSQ = [
    -20, -10, -10, -10, -10, -10, -10, -20,
    -10,   0,   0,   0,   0,   0,   0, -10,
    -10,   0,   5,  10, 10,   5,   0, -10,
    -10,   5,   5,  10, 10,   5,   5, -10,
    -10,   0,  10,  10, 10,  10,   0, -10,
    -10,  10,  10,  10, 10,  10,  10, -10,
    -10,   5,   0,   0,   0,   0,   5, -10,
    -20, -10, -10, -10, -10, -10, -10, -20,
]

ROOK_PSQ = [
    0,  0,  5, 10, 10,  5,  0,  0,
    -5, 0,  0,  0,  0,  0,  0, -5,
    -5, 0,  0,  0,  0,  0,  0, -5,
    -5, 0,  0,  0,  0,  0,  0, -5,
    -5, 0,  0,  0,  0,  0,  0, -5,
    -5, 0,  0,  0,  0,  0,  0, -5,
     5,10, 10, 10, 10, 10, 10,  5,
    0,  0,  0,  0,  0,  0,  0,  0,
]

QUEEN_PSQ = [
    -20, -10, -10, -5, -5, -10, -10, -20,
    -10,   0,   0,  0,  0,   0,   0, -10,
    -10,   0,   5,  5,  5,   5,   0, -10,
    -5,    0,   5,  5,  5,   5,   0,  -5,
    0,     0,   5,  5,  5,   5,   0,  -5,
    -10,   5,   5,  5,  5,   5,   0, -10,
    -10,   0,   5,  0,  0,   0,   0, -10,
    -20, -10, -10, -5, -5, -10, -10, -20,
]

KING_PSQ_MID = [
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -20, -30, -30, -40, -40, -30, -30, -20,
    -10, -20, -20, -20, -20, -20, -20, -10,
     20,  20,   0,   0,   0,   0,  20,  20,
     20,  30,  10,   0,   0,  10,  30,  20,
]

# Compile PST dictionary for convenience
PIECE_PSQ = {
    'P': PAWN_PSQ,
    'N': KNIGHT_PSQ,
    'B': BISHOP_PSQ,
    'R': ROOK_PSQ,
    'Q': QUEEN_PSQ,
    'K': KING_PSQ_MID,
}

# Helper to convert algebraic square <-> (col,row)
def parse_sq(sq: str) -> Tuple[int, int]:
    col = ord(sq[0]) - ord('a')
    row = 8 - int(sq[1])
    return col, row

def sq_from_coords(col: int, row: int) -> str:
    return chr(ord('a') + col) + str(8 - row)

def opponent(color: str) -> str:
    return 'b' if color == 'w' else 'w'

# -----------------------------------------------------------------
# Attack detection
# -----------------------------------------------------------------
def is_square_attacked(board: Dict[str, Optional[str]], target: Tuple[int, int], attacker: str) -> bool:
    """Check whether the square `target` is attacked by any piece of colour `attacker`."""
    t_c, t_r = target
    # Pawn attacks
    if attacker == 'w':
        for dc in (-1, 1):
            pc, pr = t_c + dc, t_r + 1
            if 0 <= pc < 8 and 0 <= pr < 8:
                sq = sq_from_coords(pc, pr)
                p = board.get(sq)
                if p and p[0] == 'w' and p[1] == 'P':
                    return True
    else:
        for dc in (-1, 1):
            pc, pr = t_c + dc, t_r - 1
            if 0 <= pc < 8 and 0 <= pr < 8:
                sq = sq_from_coords(pc, pr)
                p = board.get(sq)
                if p and p[0] == 'b' and p[1] == 'P':
                    return True
    # Knight attacks
    knight_offsets = [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
                     (1, -2), (1, 2), (2, -1), (2, 1)]
    for dc, dr in knight_offsets:
        pc, pr = t_c + dc, t_r + dr
        if 0 <= pc < 8 and 0 <= pr < 8:
            p = board.get(sq_from_coords(pc, pr))
            if p and p[0] == attacker and p[1] == 'N':
                return True
    # Sliding attacks (diagonals)
    for dc, dr in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        pc, pr = t_c + dc, t_r + dr
        while 0 <= pc < 8 and 0 <= pr < 8:
            sq = sq_from_coords(pc, pr)
            p = board.get(sq)
            if p:
                if p[0] == attacker and p[1] in ('B', 'Q'):
                    return True
                break
            pc += dc
            pr += dr
    # Sliding attacks (orthogonal)
    for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        pc, pr = t_c + dc, t_r + dr
        while 0 <= pc < 8 and 0 <= pr < 8:
            sq = sq_from_coords(pc, pr)
            p = board.get(sq)
            if p:
                if p[0] == attacker and p[1] in ('R', 'Q'):
                    return True
                break
            pc += dc
            pr += dr
    # King attacks
    for dc in (-1, 0, 1):
        for dr in (-1, 0, 1):
            if dc == 0 and dr == 0:
                continue
            pc, pr = t_c + dc, t_r + dr
            if 0 <= pc < 8 and 0 <= pr < 8:
                p = board.get(sq_from_coords(pc, pr))
                if p and p[0] == attacker and p[1] == 'K':
                    return True
    return False

def find_king(board: Dict[str, Optional[str]], color: str) -> Tuple[int, int]:
    king_code = color + 'K'
    for sq, p in board.items():
        if p == king_code:
            return parse_sq(sq)
    raise ValueError(f"King not found for colour {color}")

# -----------------------------------------------------------------
# Move generation
# -----------------------------------------------------------------
def gen_pawn_moves(board: Dict[str, Optional[str]], col: int, row: int,
                   color: str, ep_square: Optional[str]) -> List[Tuple[str, str, Optional[str], bool]]:
    moves = []
    direction = -1 if color == 'w' else 1
    start_row = 6 if color == 'w' else 1
    # One step forward
    f1_c, f1_r = col, row + direction
    if 0 <= f1_c < 8 and 0 <= f1_r < 8:
        f1_sq = sq_from_coords(f1_c, f1_r)
        if board.get(f1_sq) is None:
            # Promotion?
            if (color == 'w' and row == 1) or (color == 'b' and row == 6):
                for p in ('q', 'r', 'b', 'n'):
                    moves.append((sq_from_coords(col, row), f1_sq, p, False))
            else:
                moves.append((sq_from_coords(col, row), f1_sq, None, False))
            # Double step
            if row == start_row:
                f2_r = row + 2 * direction
                if 0 <= f1_c < 8 and 0 <= f2_r < 8:
                    f2_sq = sq_from_coords(f1_c, f2_r)
                    if board.get(f2_sq) is None:
                        moves.append((sq_from_coords(col, row), f2_sq, None, False))
    # Captures
    for dc in (-1, 1):
        cap_c, cap_r = col + dc, row + direction
        if 0 <= cap_c < 8 and 0 <= cap_r < 8:
            cap_sq = sq_from_coords(cap_c, cap_r)
            piece = board.get(cap_sq)
            if piece and piece[0] != color:
                # Capture with promotion?
                if (color == 'w' and row == 1) or (color == 'b' and row == 6):
                    for p in ('q', 'r', 'b', 'n'):
                        moves.append((sq_from_coords(col, row), cap_sq, p, False))
                else:
                    moves.append((sq_from_coords(col, row), cap_sq, None, False))
    # En‑passant (only if the opponent pawn really exists)
    if ep_square:
        ep_c, ep_r = parse_sq(ep_square)
        if ep_r == row + direction and abs(ep_c - col) == 1:
            # Verify the pawn to be captured is present on the square behind the ep square
            cap_sq = sq_from_coords(ep_c, ep_r - direction)
            captured = board.get(cap_sq)
            if captured and captured[0] != color:  # opponent pawn
                moves.append((sq_from_coords(col, row), ep_square, None, True))
    return moves

def gen_knight_moves(board: Dict[str, Optional[str]], col: int, row: int,
                     color: str) -> List[Tuple[str, str, Optional[str], bool]]:
    moves = []
    offsets = [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
               (1, -2), (1, 2), (2, -1), (2, 1)]
    for dc, dr in offsets:
        tc, tr = col + dc, row + dr
        if 0 <= tc < 8 and 0 <= tr < 8:
            sq = sq_from_coords(tc, tr)
            piece = board.get(sq)
            if piece is None or piece[0] != color:
                moves.append((sq_from_coords(col, row), sq, None, False))
    return moves

def gen_bishop_moves(board: Dict[str, Optional[str]], col: int, row: int,
                     color: str) -> List[Tuple[str, str, Optional[str], bool]]:
    moves = []
    for dc, dr in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        tc, tr = col + dc, row + dr
        while 0 <= tc < 8 and 0 <= tr < 8:
            sq = sq_from_coords(tc, tr)
            piece = board.get(sq)
            if piece is None:
                moves.append((sq_from_coords(col, row), sq, None, False))
                tc += dc
                tr += dr
                continue
            else:
                if piece[0] != color:
                    moves.append((sq_from_coords(col, row), sq, None, False))
                break
    return moves

def gen_rook_moves(board: Dict[str, Optional[str]], col: int, row: int,
                   color: str) -> List[Tuple[str, str, Optional[str], bool]]:
    moves = []
    for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        tc, tr = col + dc, row + dr
        while 0 <= tc < 8 and 0 <= tr < 8:
            sq = sq_from_coords(tc, tr)
            piece = board.get(sq)
            if piece is None:
                moves.append((sq_from_coords(col, row), sq, None, False))
                tc += dc
                tr += dr
                continue
            else:
                if piece[0] != color:
                    moves.append((sq_from_coords(col, row), sq, None, False))
                break
    return moves

def gen_queen_moves(board: Dict[str, Optional[str]], col: int, row: int,
                    color: str) -> List[Tuple[str, str, Optional[str], bool]]:
    return gen_bishop_moves(board, col, row, color) + gen_rook_moves(board, col, row, color)

def gen_king_moves(board: Dict[str, Optional[str]], col: int, row: int,
                   color: str) -> List[Tuple[str, str, Optional[str], bool]]:
    moves = []
    for dc in (-1, 0, 1):
        for dr in (-1, 0, 1):
            if dc == 0 and dr == 0:
                continue
            tc, tr = col + dc, row + dr
            if 0 <= tc < 8 and 0 <= tr < 8:
                sq = sq_from_coords(tc, tr)
                piece = board.get(sq)
                if piece is None or piece[0] != color:
                    moves.append((sq_from_coords(col, row), sq, None, False))
    return moves

def gen_castling_moves(board: Dict[str, Optional[str]], color: str) -> List[Tuple[str, str, Optional[str], bool]]:
    """Generate castling moves only if legal."""
    moves = []
    # White castling
    if color == 'w':
        if board.get('e1') != 'wK':
            return moves
        # King side (e1g1)
        if (board.get('f1') is None and board.get('g1') is None and
                board.get('h1') == 'wR' and
                not is_square_attacked(board, (5, 7), 'b') and
                not is_square_attacked(board, (6, 7), 'b')):
            moves.append(('e1', 'g1', None, False))
        # Queen side (e1c1)
        if (board.get('d1') is None and board.get('c1') is None and board.get('b1') is None and
                board.get('a1') == 'wR' and
                not is_square_attacked(board, (3, 7), 'b') and
                not is_square_attacked(board, (2, 7), 'b')):
            moves.append(('e1', 'c1', None, False))
    else:  # Black castling
        if board.get('e8') != 'bK':
            return moves
        if (board.get('f8') is None and board.get('g8') is None and
                board.get('h8') == 'bR' and
                not is_square_attacked(board, (5, 0), 'w') and
                not is_square_attacked(board, (6, 0), 'w')):
            moves.append(('e8', 'g8', None, False))
        if (board.get('d8') is None and board.get('c8') is None and board.get('b8') is None and
                board.get('a8') == 'bR' and
                not is_square_attacked(board, (3, 0), 'w') and
                not is_square_attacked(board, (2, 0), 'w')):
            moves.append(('e8', 'c8', None, False))
    return moves

def generate_pseudo_moves(board: Dict[str, Optional[str]], color: str,
                          ep_square: Optional[str]) -> List[Tuple[str, str, Optional[str], bool]]:
    moves = []
    for sq, piece in board.items():
        if piece is None or piece[0] != color:
            continue
        col, row = parse_sq(sq)
        ptype = piece[1]
        if ptype == 'P':
            moves.extend(gen_pawn_moves(board, col, row, color, ep_square))
        elif ptype == 'N':
            moves.extend(gen_knight_moves(board, col, row, color))
        elif ptype == 'B':
            moves.extend(gen_bishop_moves(board, col, row, color))
        elif ptype == 'R':
            moves.extend(gen_rook_moves(board, col, row, color))
        elif ptype == 'Q':
            moves.extend(gen_queen_moves(board, col, row, color))
        elif ptype == 'K':
            moves.extend(gen_king_moves(board, col, row, color))
    # Castling moves
    moves.extend(gen_castling_moves(board, color))
    return moves

def apply_move(board: Dict[str, Optional[str]],
               move: Tuple[str, str, Optional[str], bool]) -> Dict[str, Optional[str]]:
    """Return a new board after executing `move`."""
    from_sq, to_sq, promotion, ep_flag = move
    new_board = copy.deepcopy(board)  # shallow copy is enough (strings immutable)
    moving_piece = new_board[from_sq]
    # Normal capture (or en‑passant handled separately)
    if ep_flag:
        # En‑passant capture: remove the opponent pawn on the square behind the target
        col_to, row_to = parse_sq(to_sq)
        direction = -1 if moving_piece[0] == 'w' else 1
        cap_sq = sq_from_coords(col_to, row_to - direction)
        if cap_sq in new_board:
            del new_board[cap_sq]
    else:
        # Normal capture
        if to_sq in new_board:
            del new_board[to_sq]
    # Move the piece
    new_board[from_sq] = None
    if promotion:
        moving_piece = moving_piece[0] + promotion.upper()
    new_board[to_sq] = moving_piece
    # Castling – move the rook as well
    if moving_piece[1] == 'K' and from_sq in ('e1', 'e8'):
        col_from, row_from = parse_sq(from_sq)
        col_to, row_to = parse_sq(to_sq)
        if abs(col_to - col_from) == 2:  # Kingside or queenside
            if moving_piece[0] == 'w':
                if col_to == 6:  # g1
                    new_board['h1'] = None
                    new_board['f1'] = 'wR'
                elif col_to == 2:  # c1
                    new_board['a1'] = None
                    new_board['d1'] = 'wR'
            else:
                if col_to == 6:  # g8
                    new_board['h8'] = None
                    new_board['f8'] = 'bR'
                elif col_to == 2:  # c8
                    new_board['a8'] = None
                    new_board['d8'] = 'bR'
    return new_board

def generate_legal_moves(board: Dict[str, Optional[str]], color: str,
                         ep_square: Optional[str]) -> List[Tuple[str, str, Optional[str], bool]]:
    """Generate all legal moves for `color` in the given position."""
    pseudo = generate_pseudo_moves(board, color, ep_square)
    legal = []
    opp = opponent(color)
    for mv in pseudo:
        new_board = apply_move(board, mv)
        # Find our king in the new board
        king_pos = find_king(new_board, color)
        if not is_square_attacked(new_board, king_pos, opp):
            legal.append(mv)
    return legal

# -----------------------------------------------------------------
# Move ordering and evaluation
# -----------------------------------------------------------------
def order_moves(board: Dict[str, Optional[str]],
                moves: List[Tuple[str, str, Optional[str], bool]]) -> List[Tuple[str, str, Optional[str], bool]]:
    """Order moves to improve alpha‑beta pruning."""
    scored = []
    for mv in moves:
        from_sq, to_sq, promo, ep_flag = mv
        priority = 0
        # Captures
        victim = board.get(to_sq)
        if victim:
            attacker = board.get(from_sq)
            if attacker:
                priority += PIECE_VALUE[victim[1]] * 10 - PIECE_VALUE[attacker[1]]
        # Promotions
        if promo:
            priority += 5000
        # En‑passant (treated like a capture)
        if ep_flag:
            priority += 3000
        # Checks – evaluate after making the move (cheap test)
        new_board = apply_move(board, mv)
        opp = opponent(board[from_sq][0])
        opp_king = find_king(new_board, opp)
        if opp_king is not None and is_square_attacked(new_board, opp_king, board[from_sq][0]):
            priority += 2000
        scored.append((priority, mv))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in scored]

def evaluate(board: Dict[str, Optional[str]], perspective: str) -> int:
    """Static evaluation from `perspective` (white or black)."""
    white = 0
    black = 0
    for sq, p in board.items():
        if p is None:
            continue
        col, row = parse_sq(sq)
        idx = row * 8 + col
        base = PIECE_VALUE[p[1]]
        pst = PIECE_PSQ[p[1]][idx]
        # For black pieces we mirror the PST vertically
        if p[0] == 'w':
            white += base + pst
        else:
            black += base + PIECE_PSQ[p[1]][(7 - row) * 8 + col]
    if perspective == 'w':
        return white - black
    else:
        return black - white

# -----------------------------------------------------------------
# Search (negamax with alpha‑beta)
# -----------------------------------------------------------------
def search(board: Dict[str, Optional[str]], depth: int,
           alpha: int, beta: int, to_play: str) -> int:
    """Negamax search returning evaluation from the point of view of `to_play`."""
    if depth == 0:
        return evaluate(board, to_play)
    moves = generate_legal_moves(board, to_play, ep_square=None)
    if not moves:
        # Checkmate or stalemate
        king_pos = find_king(board, to_play)
        if is_square_attacked(board, king_pos, opponent(to_play)):
            return -1000000  # mate for side to move
        return 0  # stalemate
    # Move ordering
    moves = order_moves(board, moves)
    # Alpha‑beta loop
    for mv in moves:
        child = apply_move(board, mv)
        score = -search(child, depth - 1, -beta, -alpha, opponent(to_play))
        if score > alpha:
            alpha = score
            if alpha >= beta:
                break
    return alpha

# -----------------------------------------------------------------
# En‑passant detection (by comparing previous board with current board)
# -----------------------------------------------------------------
def detect_double_pawn_push(prev_board: Dict[str, Optional[str]],
                           curr_board: Dict[str, Optional[str]]) -> Optional[str]:
    """If an opponent pawn performed a double push, return the EP square as a string."""
    # Look for a pawn that moved two squares from its start rank
    for from_sq, piece in prev_board.items():
        if piece is None or piece[1] != 'P':
            continue
        col, row = parse_sq(from_sq)
        if piece[0] == 'w' and row == 6:          # white start rank (rank 2)
            to_sq = sq_from_coords(col, row - 2)
            if prev_board.get(to_sq) is None and curr_board.get(to_sq) == 'wP':
                return sq_from_coords(col, row - 1)  # EP square = passed square
        elif piece[0] == 'b' and row == 1:        # black start rank (rank 7)
            to_sq = sq_from_coords(col, row + 2)
            if prev_board.get(to_sq) is None and curr_board.get(to_sq) == 'bP':
                return sq_from_coords(col, row + 1)
    return None

# -----------------------------------------------------------------
# UCI conversion
# -----------------------------------------------------------------
def move_to_uci(move: Tuple[str, str, Optional[str], bool]) -> str:
    from_sq, to_sq, promo, _ = move
    uci = from_sq + to_sq
    if promo:
        uci += promo
    return uci

# -----------------------------------------------------------------
# Public policy entry point
# -----------------------------------------------------------------
def policy(pieces: Dict[str, str], to_play: str, memory: Dict) -> Tuple[str, Dict]:
    # Ensure `memory` is a dict even if empty
    if memory is None:
        memory = {}
    # Convert "white"/"black" to piece colour character
    color = to_play[0]

    # Initialise / update memory
    if 'prev_board' not in memory:
        memory['prev_board'] = pieces
    else:
        # Detect opponent double pawn push and store EP square
        ep_sq = detect_double_pawn_push(memory['prev_board'], pieces)
        if ep_sq is not None:
            memory['ep_square'] = ep_sq
        else:
            memory['ep_square'] = None

    ep_square = memory.get('ep_square', None)

    # Generate all legal moves
    legal_moves = generate_legal_moves(pieces, color, ep_square)

    # Fallback (should never happen in a legal game)
    if not legal_moves:
        # No legal moves – treat as checkmate or stalemate (choose arbitrary)
        raise RuntimeError("No legal moves found – illegal state.")

    # Choose the best move using a limited search
    best_move = None
    best_score = -10**9
    for mv in legal_moves:
        new_board = apply_move(pieces, mv)
        # One‑ply evaluation (search depth 1) is enough inside the loop
        score = -search(new_board, 1, -10**9, 10**9, opponent(color))
        if score > best_score:
            best_score = score
            best_move = mv

    # Convert selected move to UCI string
    action = move_to_uci(best_move)

    # Prepare memory for next turn (store current board as previous)
    memory['prev_board'] = pieces
    # Keep ep_square for the next ply only if it was set; otherwise it will be cleared next time
    return action, memory
