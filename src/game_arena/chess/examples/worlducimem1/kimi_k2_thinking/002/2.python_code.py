
import copy

################################################################################
# Constants
################################################################################
FILES = 'abcdefgh'
RANKS = '12345678'

# piece values (centipawns)
PIECE_VALUES = {
    'P': 100,
    'N': 320,
    'B': 330,
    'R': 500,
    'Q': 900,
    'K': 0
}

# direction vectors
KING_DIRS   = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
QUEEN_DIRS  = KING_DIRS
ROOK_DIRS   = [(1, 0), (-1, 0), (0, 1), (0, -1)]
BISHOP_DIRS = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
KNIGHT_DIRS = [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]

# piece‑square tables (white point of view – rank 0 = a1)
PAWN_PST = [
    0, 0, 0, 0, 0, 0, 0, 0,
    5, 10, 10, -20, -20, 10, 10, 5,
    5, -5, -10, 0, 0, -10, -5, 5,
    0, 0, 0, 20, 20, 0, 0, 0,
    5, 5, 10, 25, 25, 10, 5, 5,
    10, 10, 20, 30, 30, 20, 10, 10,
    50, 50, 50, 50, 50, 50, 50, 50,
    0, 0, 0, 0, 0, 0, 0, 0
]

KNIGHT_PST = [
    -50, -40, -30, -30, -30, -30, -40, -50,
    -40, -20, 0, 5, 5, 0, -20, -40,
    -30, 0, 10, 15, 15, 10, 0, -30,
    -30, 0, 15, 20, 20, 15, 0, -30,
    -30, 0, 15, 20, 20, 15, 0, -30,
    -30, 0, 10, 15, 15, 10, 0, -30,
    -40, -20, 0, 0, 0, 0, -20, -40,
    -50, -40, -30, -30, -30, -30, -40, -50,
]

BISHOP_PST = [
    -20, -10, -10, -10, -10, -10, -10, -20,
    -10, 5, 0, 0, 0, 0, 5, -10,
    -10, 10, 10, 10, 10, 10, 10, -10,
    -10, 0, 10, 10, 10, 10, 0, -10,
    -10, 5, 5, 10, 10, 5, 5, -10,
    -10, 0, 5, 10, 10, 5, 0, -10,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -20, -10, -10, -10, -10, -10, -10, -20,
]

ROOK_PST = [
    0, 0, 0, 5, 5, 0, 0, 0,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    5, 10, 10, 10, 10, 10, 10, 5,
    0, 0, 0, 0, 0, 0, 0, 0,
]

QUEEN_PST = [
    -20, -10, -10, -5, -5, -10, -10, -20,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -10, 0, 5, 5, 5, 5, 0, -10,
    -5, 0, 5, 5, 5, 5, 0, -5,
    0, 0, 5, 5, 5, 5, 0, -5,
    -10, 5, 5, 5, 5, 5, 0, -10,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -20, -10, -10, -5, -5, -10, -10, -20,
]

KING_PST = [
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -20, -30, -30, -40, -40, -30, -30, -20,
    -10, -20, -20, -20, -20, -20, -20, -10,
    20, 20, 0, 0, 0, 0, 20, 20,
    20, 30, 10, 0, 0, 10, 30, 20,
]

PST = {
    'P': PAWN_PST,
    'N': KNIGHT_PST,
    'B': BISHOP_PST,
    'R': ROOK_PST,
    'Q': QUEEN_PST,
    'K': KING_PST,
}

# search‑time constants
MATE_SCORE = 1000000
INF = 10000000

################################################################################
# Helpers
################################################################################
def sq_to_coords(sq):
    """'e4' → (4, 3) (0‑based file, rank)"""
    return (ord(sq[0]) - ord('a'), int(sq[1]) - 1)

def coords_to_sq(f, r):
    """(4,3) → 'e4' """
    return FILES[f] + RANKS[r]

def opposite_color(c):
    return 'b' if c == 'w' else 'w'

################################################################################
# Attack detection
################################################################################
def is_pawn_attacking(target_sq, attacker_color, board):
    f, r = sq_to_coords(target_sq)
    if attacker_color == 'w':
        # white pawns attack (f‑1, r‑1) and (f+1, r‑1)
        for df in (-1, 1):
            cf, cr = f + df, r - 1
            if 0 <= cf < 8 and 0 <= cr < 8:
                sq = coords_to_sq(cf, cr)
                if board.get(sq) == 'wP':
                    return True
    else:
        for df in (-1, 1):
            cf, cr = f + df, r + 1
            if 0 <= cf < 8 and 0 <= cr < 8:
                sq = coords_to_sq(cf, cr)
                if board.get(sq) == 'bP':
                    return True
    return False

def is_square_attacked(board, target_sq, attacker_color):
    """Can any piece of attacker_color attack target_sq?"""
    # pawn attacks
    if is_pawn_attacking(target_sq, attacker_color, board):
        return True

    f, r = sq_to_coords(target_sq)

    # knights
    for df, dr in KNIGHT_DIRS:
        cf, cr = f + df, r + dr
        if 0 <= cf < 8 and 0 <= cr < 8:
            sq = coords_to_sq(cf, cr)
            pc = board.get(sq)
            if pc == attacker_color + 'N':
                return True

    # king
    for df, dr in KING_DIRS:
        cf, cr = f + df, r + dr
        if 0 <= cf < 8 and 0 <= cr < 8:
            sq = coords_to_sq(cf, cr)
            if board.get(sq) == attacker_color + 'K':
                return True

    # rook / queen on straight lines
    for df, dr in ROOK_DIRS:
        cf, cr = f + df, r + dr
        while 0 <= cf < 8 and 0 <= cr < 8:
            sq = coords_to_sq(cf, cr)
            pc = board.get(sq)
            if pc:
                if pc[0] == attacker_color and pc[1] in ('R', 'Q'):
                    return True
                break
            cf += df
            cr += dr

    # bishop / queen on diagonals
    for df, dr in BISHOP_DIRS:
        cf, cr = f + df, r + dr
        while 0 <= cf < 8 and 0 <= cr < 8:
            sq = coords_to_sq(cf, cr)
            pc = board.get(sq)
            if pc:
                if pc[0] == attacker_color and pc[1] in ('B', 'Q'):
                    return True
                break
            cf += df
            cr += dr

    return False

def is_in_check(board, color):
    king_sq = None
    king_code = color + 'K'
    for sq, pc in board.items():
        if pc == king_code:
            king_sq = sq
            break
    if king_sq is None:
        return False
    opp = opposite_color(color)
    return is_square_attacked(board, king_sq, opp)

################################################################################
# Move generation
################################################################################
def generate_pawn_moves(sq, color, board, en_passant_target):
    moves = []
    f, r = sq_to_coords(sq)
    forward = 1 if color == 'w' else -1
    start_rank = 1 if color == 'w' else 6
    promo_rank = 7 if color == 'w' else 0

    # one step forward
    r1 = r + forward
    if 0 <= r1 < 8:
        dest = coords_to_sq(f, r1)
        if dest not in board:
            if r1 == promo_rank:
                for promo in ('Q', 'R', 'B', 'N'):
                    moves.append(sq + dest + promo)
            else:
                moves.append(sq + dest)
            # two squares from start
            if r == start_rank:
                r2 = r + 2 * forward
                dest2 = coords_to_sq(f, r2)
                if dest2 not in board:
                    moves.append(sq + dest2)

    # captures (including en‑passant)
    for df in (-1, 1):
        cf = f + df
        cr = r + forward
        if 0 <= cf < 8 and 0 <= cr < 8:
            dest = coords_to_sq(cf, cr)
            target = board.get(dest)
            # normal capture
            if target and target[0] != color:
                if cr == promo_rank:
                    for promo in ('Q', 'R', 'B', 'N'):
                        moves.append(sq + dest + promo)
                else:
                    moves.append(sq + dest)
            # en‑passant capture
            if en_passant_target and dest == en_passant_target:
                moves.append(sq + dest)

    return moves

def generate_knight_moves(sq, color, board):
    moves = []
    f, r = sq_to_coords(sq)
    for df, dr in KNIGHT_DIRS:
        cf, cr = f + df, r + dr
        if 0 <= cf < 8 and 0 <= cr < 8:
            dest = coords_to_sq(cf, cr)
            target = board.get(dest)
            if target is None or target[0] != color:
                moves.append(sq + dest)
    return moves

def generate_bishop_moves(sq, color, board):
    moves = []
    f, r = sq_to_coords(sq)
    for df, dr in BISHOP_DIRS:
        cf, cr = f + df, r + dr
        while 0 <= cf < 8 and 0 <= cr < 8:
            dest = coords_to_sq(cf, cr)
            target = board.get(dest)
            if target is None:
                moves.append(sq + dest)
            else:
                if target[0] != color:
                    moves.append(sq + dest)
                break
            cf += df
            cr += dr
    return moves

def generate_rook_moves(sq, color, board):
    moves = []
    f, r = sq_to_coords(sq)
    for df, dr in ROOK_DIRS:
        cf, cr = f + df, r + dr
        while 0 <= cf < 8 and 0 <= cr < 8:
            dest = coords_to_sq(cf, cr)
            target = board.get(dest)
            if target is None:
                moves.append(sq + dest)
            else:
                if target[0] != color:
                    moves.append(sq + dest)
                break
            cf += df
            cr += dr
    return moves

def generate_queen_moves(sq, color, board):
    # combine rook and bishop
    return generate_rook_moves(sq, color, board) + generate_bishop_moves(sq, color, board)

def generate_castling_moves(king_sq, color, board, flags):
    moves = []
    if color == 'w':
        if not flags.get('w_king_moved', False):
            # kingside
            if not flags.get('w_rook_h1_moved', False):
                if board.get('f1') is None and board.get('g1') is None:
                    if not is_in_check(board, 'w') and not is_square_attacked(board, 'f1', 'b') and not is_square_attacked(board, 'g1', 'b'):
                        moves.append('e1g1')
            # queenside
            if not flags.get('w_rook_a1_moved', False):
                if board.get('b1') is None and board.get('c1') is None and board.get('d1') is None:
                    if not is_in_check(board, 'w') and not is_square_attacked(board, 'c1', 'b') and not is_square_attacked(board, 'd1', 'b'):
                        moves.append('e1c1')
    else:
        if not flags.get('b_king_moved', False):
            # kingside
            if not flags.get('b_rook_h8_moved', False):
                if board.get('f8') is None and board.get('g8') is None:
                    if not is_in_check(board, 'b') and not is_square_attacked(board, 'f8', 'w') and not is_square_attacked(board, 'g8', 'w'):
                        moves.append('e8g8')
            # queenside
            if not flags.get('b_rook_a8_moved', False):
                if board.get('b8') is None and board.get('c8') is None and board.get('d8') is None:
                    if not is_in_check(board, 'b') and not is_square_attacked(board, 'c8', 'w') and not is_square_attacked(board, 'd8', 'w'):
                        moves.append('e8c8')
    return moves

def generate_king_moves(sq, color, board, flags):
    moves = []
    f, r = sq_to_coords(sq)
    for df, dr in KING_DIRS:
        cf, cr = f + df, r + dr
        if 0 <= cf < 8 and 0 <= cr < 8:
            dest = coords_to_sq(cf, cr)
            target = board.get(dest)
            if target is None or target[0] != color:
                moves.append(sq + dest)
    # castling
    moves.extend(generate_castling_moves(sq, color, board, flags))
    return moves

def generate_pseudo_moves(board, color, en_passant_target, flags):
    moves = []
    for sq, pc in board.items():
        if pc[0] != color:
            continue
        pt = pc[1]
        if pt == 'P':
            moves.extend(generate_pawn_moves(sq, color, board, en_passant_target))
        elif pt == 'N':
            moves.extend(generate_knight_moves(sq, color, board))
        elif pt == 'B':
            moves.extend(generate_bishop_moves(sq, color, board))
        elif pt == 'R':
            moves.extend(generate_rook_moves(sq, color, board))
        elif pt == 'Q':
            moves.extend(generate_queen_moves(sq, color, board))
        elif pt == 'K':
            moves.extend(generate_king_moves(sq, color, board, flags))
    return moves

def generate_legal_moves(board, color, en_passant_target, flags):
    pseudo = generate_pseudo_moves(board, color, en_passant_target, flags)
    legal = []
    for mv in pseudo:
        nb, new_ep = apply_move(board, mv, en_passant_target, flags)
        nf = update_flags(flags, mv, board)
        if not is_in_check(nb, color):
            legal.append(mv)
    return legal

################################################################################
# Applying a move
################################################################################
def apply_move(board, move, en_passant_target, flags):
    """
    Returns (new_board, new_en_passant_target).
    move is a UCI string, e.g. 'e2e4' or 'a7a8q'.
    """
    nb = dict(board)
    from_sq = move[:2]
    to_sq = move[2:4]
    promo = move[4] if len(move) == 5 else None

    piece = nb.get(from_sq)
    if piece is None:
        # should never happen for a legal move
        return nb, None

    color = piece[0]
    ptype = piece[1]

    # ----- castling ---------------------------------------------------------
    if ptype == 'K' and abs(ord(from_sq[0]) - ord(to_sq[0])) == 2:
        # move king already handled later; move the rook here
        if color == 'w':
            if to_sq == 'g1':    # kingside
                rook_from, rook_to = 'h1', 'f1'
            else:                # queenside
                rook_from, rook_to = 'a1', 'd1'
        else:
            if to_sq == 'g8':
                rook_from, rook_to = 'h8', 'f8'
            else:
                rook_from, rook_to = 'a8', 'd8'
        # move rook
        nb[rook_to] = nb.pop(rook_from)

    # ----- en‑passant capture ----------------------------------------------
    if ptype == 'P' and to_sq == en_passant_target:
        # remove the pawn that just moved two squares
        if color == 'w':
            captured = to_sq[0] + str(int(to_sq[1]) + 1)
        else:
            captured = to_sq[0] + str(int(to_sq[1]) - 1)
        nb.pop(captured, None)

    # ----- normal move / capture -------------------------------------------
    # remove destination piece if present
    nb.pop(to_sq, None)
    # place moving piece
    if ptype == 'P' and promo:
        nb[to_sq] = color + promo
    else:
        nb[to_sq] = piece
    nb.pop(from_sq, None)

    # ----- en‑passant target for the next move -----------------------------
    new_ep = None
    if ptype == 'P' and abs(int(to_sq[1]) - int(from_sq[1])) == 2:
        # pawn moved two squares – set the square it passed over as target
        passed_rank = (int(from_sq[1]) + int(to_sq[1])) // 2
        new_ep = from_sq[0] + str(passed_rank)

    return nb, new_ep

################################################################################
# Updating castling / rook‑moved flags
################################################################################
FLAG_KEYS = [
    'w_king_moved', 'b_king_moved',
    'w_rook_a1_moved', 'w_rook_h1_moved',
    'b_rook_a8_moved', 'b_rook_h8_moved'
]

def update_flags(flags, move, board):
    """Copy flags and set any that changed because of *move*."""
    nf = dict(flags)
    from_sq = move[:2]
    to_sq = move[2:4]
    piece = board.get(from_sq)
    if piece is None:
        return nf
    color = piece[0]
    ptype = piece[1]

    # king moved
    if ptype == 'K':
        if color == 'w':
            nf['w_king_moved'] = True
        else:
            nf['b_king_moved'] = True

        # castling also moves a rook – handle that here
        if abs(ord(from_sq[0]) - ord(to_sq[0])) == 2:   # castling
            if color == 'w':
                if to_sq == 'g1':
                    nf['w_rook_h1_moved'] = True
                elif to_sq == 'c1':
                    nf['w_rook_a1_moved'] = True
            else:
                if to_sq == 'g8':
                    nf['b_rook_h8_moved'] = True
                elif to_sq == 'c8':
                    nf['b_rook_a8_moved'] = True

    # rook moved (or captured) from its original square
    if ptype == 'R':
        if color == 'w':
            if from_sq == 'a1':
                nf['w_rook_a1_moved'] = True
            elif from_sq == 'h1':
                nf['w_rook_h1_moved'] = True
        else:
            if from_sq == 'a8':
                nf['b_rook_a8_moved'] = True
            elif from_sq == 'h8':
                nf['b_rook_h8_moved'] = True

    # capture of a rook on its home square
    target_piece = board.get(to_sq)
    if target_piece and target_piece[1] == 'R':
        if target_piece[0] == 'w':
            if to_sq == 'a1':
                nf['w_rook_a1_moved'] = True
            elif to_sq == 'h1':
                nf['w_rook_h1_moved'] = True
        else:
            if to_sq == 'a8':
                nf['b_rook_a8_moved'] = True
            elif to_sq == 'h8':
                nf['b_rook_h8_moved'] = True

    return nf

################################################################################
# Evaluation
################################################################################
def evaluate(board, color):
    """Raw material + PST score from *color*'s point of view."""
    score = 0
    for sq, pc in board.items():
        pc_type = pc[1]
        value = PIECE_VALUES[pc_type]
        # PST index from the piece's own perspective
        f = ord(sq[0]) - ord('a')
        r = int(sq[1]) - 1
        if pc[0] == 'w':
            idx = r * 8 + f
            score += value + PST[pc_type][idx]
        else:
            idx = (7 - r) * 8 + f
            score -= value + PST[pc_type][idx]
    if color == 'b':
        score = -score
    return score

################################################################################
# Alpha‑beta search
################################################################################
def search(board, color, depth, alpha, beta, en_passant_target, flags):
    # terminal depth – static evaluation
    if depth == 0:
        return None, evaluate(board, color)

    legal = generate_legal_moves(board, color, en_passant_target, flags)

    if not legal:
        if is_in_check(board, color):
            return None, -MATE_SCORE + depth
        else:
            return None, 0

    best_move = legal[0]
    best_score = -INF

    for mv in legal:
        nb, new_ep = apply_move(board, mv, en_passant_target, flags)
        nf = update_flags(flags, mv, board)
        _, sc = search(nb, opposite_color(color), depth - 1, -beta, -alpha, new_ep, nf)
        sc = -sc
        if sc > best_score:
            best_score = sc
            best_move = mv
            alpha = max(alpha, sc)
            if alpha >= beta:
                break
    return best_move, best_score

################################################################################
# Public API
################################################################################
def policy(pieces, to_play, memory):
    """
    pieces : dict  square → piece_code (e.g. {'e1':'wK', ...})
    to_play: 'white' or 'black'
    memory : dict that persists between calls within one game
    returns (move_uci, new_memory)
    """
    color = 'w' if to_play == 'white' else 'b'

    # initialise flag keys if missing
    for k in FLAG_KEYS:
        memory.setdefault(k, False)

    # -----------------------------------------------------------------
    # update castling flags from the current board (once per turn)
    # -----------------------------------------------------------------
    if not memory['w_king_moved'] and pieces.get('e1') != 'wK':
        memory['w_king_moved'] = True
    if not memory['w_rook_a1_moved'] and pieces.get('a1') != 'wR':
        memory['w_rook_a1_moved'] = True
    if not memory['w_rook_h1_moved'] and pieces.get('h1') != 'wR':
        memory['w_rook_h1_moved'] = True

    if not memory['b_king_moved'] and pieces.get('e8') != 'bK':
        memory['b_king_moved'] = True
    if not memory['b_rook_a8_moved'] and pieces.get('a8') != 'bR':
        memory['b_rook_a8_moved'] = True
    if not memory['b_rook_h8_moved'] and pieces.get('h8') != 'bR':
        memory['b_rook_h8_moved'] = True

    # current en‑passant target (set by the opponent on the previous move)
    en_passant_target = memory.get('en_passant_target', None)

    # pack the flags for the search
    flags = {k: memory[k] for k in FLAG_KEYS}

    # -----------------------------------------------------------------
    # generate legal moves for the side to move
    # -----------------------------------------------------------------
    legal_moves = generate_legal_moves(pieces, color, en_passant_target, flags)

    # safety fallback – should never happen in a real game, but guarantee a legal answer
    if not legal_moves:
        # return the first pseudo‑legal move (or a null move if even that is impossible)
        pseudo = generate_pseudo_moves(pieces, color, en_passant_target, flags)
        sel = pseudo[0] if pseudo else 'a1a1'
        return sel, memory

    # -----------------------------------------------------------------
    # choose a move with a small alpha‑beta search
    # -----------------------------------------------------------------
    depth = 3      # safe depth – finishes well under 1 s
    best_move, _ = search(pieces, color, depth, -INF, INF, en_passant_target, flags)

    if best_move is None:                     # extremely unlikely – pick first legal move
        best_move = legal_moves[0]

    # -----------------------------------------------------------------
    # update memory with the state *after* our move
    # -----------------------------------------------------------------
    new_board, new_ep = apply_move(pieces, best_move, en_passant_target, flags)
    new_flags = update_flags(flags, best_move, pieces)

    memory['en_passant_target'] = new_ep
    for k in FLAG_KEYS:
        memory[k] = new_flags[k]

    return best_move, memory
