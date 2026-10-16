
import numpy as np

# ---------------------------------------
# Board geometry helpers
# ---------------------------------------
FILE = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
RANKS_STR = list(range(1, 9))
RANK_TO_INDEX = {str(r): r - 1 for r in RANKS_STR}
INDEX_TO_RANK = {0: '1', 1: '2', 2: '3', 3: '4', 4: '5', 5: '6', 6: '7', 7: '8'}

def square_from_file_and_rank(f: str, r_idx: int) -> str:
    return f'{f}{INDEX_TO_RANK[r_idx]}'

def rank_index_from_square(sq: str) -> int:
    return RANK_TO_INDEX[sq[1]]

# ---------------------------------------
# Core move generation per piece type
# ---------------------------------------
def king_moves(board, src: str, pc: str, color: str) -> list:
    moves = []
    file, r = src[0], src[1]
    f_idx = FILE.index(file)
    r_idx = rank_index_from_square(r)
    dirs = [(-1, -1), (-1, 0), (-1, 1),
            (0, -1),          (0, 1),
            (1, -1),  (1, 0),  (1, 1)]
    for df, dr in dirs:
        nf = f_idx + df
        nr = r_idx + dr
        if not (0 <= nf <= 7 and 0 <= nr <= 7):
            continue
        dst = square_from_file_and_rank(FILE[nf], INDEX_TO_RANK[nr])
        if board.get(dst) is None or board[dst][0] != color:
            moves.append(f'{src}{dst}')
    return moves

def rook_moves(board, src: str, pc: str, color: str) -> list:
    moves = []
    file, r = src[0], src[1]
    f_idx = FILE.index(file)
    r_idx = rank_index_from_square(r)
    # Horizontal
    for df in (-1, 1):
        nf = f_idx + df
        dst = square_from_file_and_rank(FILE[nf], r)
        while 0 <= nf <= 7:
            sq = square_from_file_and_rank(FILE[nf], r)
            if board.get(sq) is None:        # empty
                moves.append(f'{src}{sq}')
                nf += df
            elif board[sq][0] == color:     # own piece blocks
                break
            else:                           # opponent piece captures
                moves.append(f'{src}{sq}')
                break
    # Vertical
    for dr in (-1, 1):
        nr = r_idx + dr
        dst = square_from_file_and_rank(file, INDEX_TO_RANK[nr])
        while 0 <= nr <= 7:
            sq = square_from_file_and_rank(file, INDEX_TO_RANK[nr])
            if board.get(sq) is None:
                moves.append(f'{src}{sq}')
                nr += dr
            elif board[sq][0] == color:
                break
            else:
                moves.append(f'{src}{sq}')
                break
    return moves

def bishop_moves(board, src: str, pc: str, color: str) -> list:
    moves = []
    file, r = src[0], src[1]
    f_idx = FILE.index(file)
    r_idx = rank_index_from_square(r)
    dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    for df, dr in dirs:
        nf = f_idx + df
        nr = r_idx + dr
        while 0 <= nf <= 7 and 0 <= nr <= 7:
            sq = square_from_file_and_rank(FILE[nf], INDEX_TO_RANK[nr])
            if board.get(sq) is None:
                moves.append(f'{src}{sq}')
                nf += df
                nr += dr
            elif board[sq][0] == color:
                break
            else:
                moves.append(f'{src}{sq}')
                nf += df
                nr += dr
                break
    return moves

def knight_moves(board, src: str, pc: str, color: str) -> list:
    moves = []
    file, r = src[0], src[1]
    f_idx = FILE.index(file)
    r_idx = rank_index_from_square(r)
    offsets = [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
               (1, -2),  (1, 2),  (2, -1),  (2, 1)]
    for df, dr in offsets:
        nf = f_idx + df
        nr = r_idx + dr
        if not (0 <= nf <= 7 and 0 <= nr <= 7):
            continue
        dst = square_from_file_and_rank(FILE[nf], INDEX_TO_RANK[nr])
        if board.get(dst) is None or board[dst][0] != color:
            moves.append(f'{src}{dst}')
    return moves

def pawn_moves(board, src: str, pc: str, color: str) -> list:
    moves = []
    file = src[0]
    rank_char = src[1]
    rank_idx = rank_index_from_square(rank_char)
    direction = 1 if color == 'white' else -1
    forward_rank = rank_idx + direction
    dst_rank = forward_rank + direction   # one step forward
    # Single step
    if 0 <= dst_rank <= 7:
        dst = square_from_file_and_rank(file, INDEX_TO_RANK[dst_rank])
        if board.get(dst) is None:
            moves.append(f'{src}{dst}')
    # Double step (only from starting rank)
    if rank_idx == (1 if color == 'white' else 6):
        dst2 = square_from_file_and_rank(file, INDEX_TO_RANK[forward_rank])
        if board.get(dst2) is None and board.get(dst) is None:
            moves.append(f'{src}{dst2}')
    # Captures left/right
    for df in (-1, 1):
        dfile = FILE[FILE.index(file) + df]
        dst = square_from_file_and_rank(dfile, INDEX_TO_RANK[forward_rank])
        if board.get(dst) is not None and board[dst][0] != color:
            moves.append(f'{src}{dst}')
    return moves

def castle_moves(board, color: str) -> list:
    moves = []
    opp_color = 'black' if color == 'white' else 'white'
    # Locate own king
    own_king = next(sq for sq, pc in board.items() if pc[0] == color and pc[1] == 'K')
    if not own_king:
        return moves
    # Are we already in check?
    if square_attacked(board, own_king, opp_color):
        return moves

    # Determine rook start squares
    rook_start = ['a1' if color == 'white' else 'a8',
                  'h1' if color == 'white' else 'h8']
    rook_available = None
    for rs in rook_start:
        if board.get(rs) == f'{color}R':
            rook_available = rs
            break
    if rook_available is None:
        return moves

    # Square between king and rook must be empty and not under attack
    inter1 = next(rs for rs in rook_start if rs != rook_available)
    # Short castle (c1/g1) path: squares inter1, own_king
    # Long castle (g1/c1) path: squares own_king+1 (next file), own_king, rook_available
    # Define paths
    if rook_available == ('h' + ('1' if color == 'white' else '8')):
        # long castle via g-file
        # squares: file-1, file, file+1
        gsq = ('f' if color == 'white' else 'g')
        if not board.get(gsq):
            inter = [own_king, gsq]
        else:
            inter = []
        # short castle via f-file
        fsq = ('d' if color == 'white' else 'e')
        inter_short = []
    else:
        # short castle via a-file
        if not board.get(('d' if color == 'white' else 'e')):
            inter = [own_king, inter1]
        else:
            inter = []
        # long castle via g-file
        gsq = ('f' if color == 'white' else 'g')
        inter_long = []
    # Evaluate legality for each possible direction
    # Short castle (king side)
    if inter1 == ('h' + ('1' if color == 'white' else '8')):
        short_dst = ('c' if color == 'white' else 'e') + ('1' if color == 'white' else '8')
        if not board.get(('d' if color == 'white' else 'e')) and not board.get(own_king) and \
           not square_attacked(board, short_dst, opp_color):
            moves.append(f'{own_king}{short_dst}')
    else:
        long_dst = ('g' if color == 'white' else 'c') + ('1' if color == 'white' else '8')
        if not board.get(('f' if color == 'white' else 'g')) and not board.get(own_king) and \
           not square_attacked(board, long_dst, opp_color):
            moves.append(f'{own_king}{long_dst}')
    return moves

# ---------------------------------------
# Generic helpers
# ---------------------------------------
def square_attacked(board, target: str, attacker_color: str) -> bool:
    """Return True if any piece of attacker_color can move to target on the current board."""
    for sq, pc in board.items():
        if pc[0] != attacker_color:
            continue
        # generate moves for this piece
        if pc[1] == 'K':
            moves = king_moves(board, sq, pc, attacker_color)
        elif pc[1] == 'Q':
            moves = rook_moves(board, sq, pc, attacker_color) + bishop_moves(board, sq, pc, attacker_color)
        elif pc[1] == 'R':
            moves = rook_moves(board, sq, pc, attacker_color)
        elif pc[1] == 'B':
            moves = bishop_moves(board, sq, pc, attacker_color)
        elif pc[1] == 'N':
            moves = knight_moves(board, sq, pc, attacker_color)
        elif pc[1] == 'P':
            moves = pawn_moves(board, sq, pc, attacker_color)
        else:
            moves = []
        if target in moves:
            return True
    return False

def find_king(board, color: str) -> str | None:
    return next((sq for sq, pc in board.items() if pc[0] == color and pc[1] == 'K'), None)

def apply_move(board: dict, move: str, color: str) -> dict:
    """Return a new board after applying the move."""
    src, dst = move[:2], move[2:]
    piece = board[src]
    # Promotion handling (we only promote to queen for simplicity)
    if piece[1] == 'P' and rank_index_from_square(dst) == 7 if color == 'white' else 0:
        # promotion to queen
        new_piece = f"{color}Q"
    else:
        new_piece = piece
    new_board = dict(board)  # shallow copy
    new_board[dst] = new_piece
    new_board[src] = None
    return new_board

def board_gives_check(board: dict, to_play: str) -> bool:
    opp_color = 'white' if to_play == 'black' else 'black'
    opp_king_sq = find_king(board, opp_color)
    if opp_king_sq is None:
        return False
    for sq, pc in board.items():
        if pc[0] == to_play:
            # Generate moves for our pieces and see if any attacks opponent king
            if pc[1] == 'K':
                moves = king_moves(board, sq, pc, to_play)
            elif pc[1] == 'Q':
                moves = rook_moves(board, sq, pc, to_play) + bishop_moves(board, sq, pc, to_play)
            elif pc[1] == 'R':
                moves = rook_moves(board, sq, pc, to_play)
            elif pc[1] == 'B':
                moves = bishop_moves(board, sq, pc, to_play)
            elif pc[1] == 'N':
                moves = knight_moves(board, sq, pc, to_play)
            elif pc[1] == 'P':
                moves = pawn_moves(board, sq, pc, to_play)
            else:
                moves = []
            if opp_king_sq in moves:
                return True
    return False

def piece_moves_by_type(board, src: str, pc: str, color: str):
    """Dispatch to per‑piece generator."""
    piece_type = pc[1]
    if piece_type == 'K':
        return king_moves(board, src, pc, color)
    if piece_type == 'Q':
        return rook_moves(board, src, pc, color) + bishop_moves(board, src, pc, color)
    if piece_type == 'R':
        return rook_moves(board, src, pc, color)
    if piece_type == 'B':
        return bishop_moves(board, src, pc, color)
    if piece_type == 'N':
        return knight_moves(board, src, pc, color)
    if piece_type == 'P':
        return pawn_moves(board, src, pc, color)
    return []

def generate_moves(board: dict, to_play: str) -> list:
    """Return list of all legal UCI moves for the side to move."""
    legal = set()
    for src, pc in board.items():
        if pc[0] != to_play:
            continue
        legal.update(piece_moves_by_type(board, src, pc, to_play))
    # Castling
    legal.update(castle_moves(board, to_play))
    # Filter out moves that leave our king in check
    filtered = []
    for move in legal:
        new_board = apply_move(board, move, to_play)
        if not find_king(new_board, to_play):
            continue  # should not happen
        opp_color = 'white' if to_play == 'black' else 'black'
        if square_attacked(new_board, find_king(new_board, to_play), opp_color):
            continue
        filtered.append(move)
    return filtered

# ---------------------------------------
# Simple evaluation
# ---------------------------------------
PIECE_VALUE = {
    'wP': 1, 'bP': -1,
    'wN': 3, 'bN': -3,
    'wB': 3, 'bB': -3,
    'wR': 5, 'bR': -5,
    'wQ': 9, 'bQ': -9,
    'wK': 0, 'bK': 0
}

def piece_square_bonus(board: dict, color: str) -> int:
    """Basic central‑square bonus (white +5, black -5)"""
    bonus = 0
    for sq, pc in board.items():
        if pc[0] != color:
            continue
        file = FILE.index(sq[0])
        rank = rank_index_from_square(sq)
        # central squares (d/e, 4/5)
        if file in (3, 4) and rank in (3, 4):
            bonus += 5
    return bonus

def evaluate(board: dict, to_play: str) -> int:
    """Material value + piece‑square bonus + check bonus."""
    val = sum(PIECE_VALUE.get(pc, 0) for pc in board.values())
    val += piece_square_bonus(board, to_play)
    # Give a strong boost for delivering check
    if board_gives_check(board, to_play):
        val += 5000
    return val

def is_capture(pieces: dict, move: str, to_play: str) -> bool:
    src, dst = move[:2], move[2:]
    if pieces.get(dst) and pieces[dst][0] != to_play:
        return True
    return False

# ---------------------------------------
# Main policy function
# ---------------------------------------
def policy(pieces: dict[str, str], to_play: str) -> str:
    moves = generate_moves(pieces, to_play)
    # Moves must always be non‑empty (by problem definition)
    best_move = moves[0]
    best_eval = evaluate(pieces, to_play)  # placeholder
    # Compute evaluation after each move
    for move in moves:
        new_board = apply_move(pieces, move, to_play)
        ev = evaluate(new_board, to_play)
        if ev > best_eval or (ev == best_eval and is_capture(pieces, move, to_play)):
            best_eval = ev
            best_move = move
    return best_move
