
import random

# --- Basic board utilities (no external chess library) ---

FILES = "abcdefgh"
RANKS = "12345678"

PIECE_VALUE = {
    "P": 100,
    "N": 320,
    "B": 330,
    "R": 500,
    "Q": 900,
    "K": 20000
}

PAWN_DIR = {
    "white": 1,
    "black": -1
}

def sq_to_xy(sq: str):
    f = FILES.index(sq[0])
    r = int(sq[1]) - 1
    return f, r

def xy_to_sq(x: int, y: int):
    return FILES[x] + str(y + 1)

def in_bounds(x, y):
    return 0 <= x < 8 and 0 <= y < 8

def parse_move_uci(move: str):
    # Typical: from(2) + to(2) + optional promotion char (1)
    frm = move[0:2]
    to = move[2:4]
    promo = move[4:] if len(move) > 4 else ""
    promo_piece = None
    if promo:
        # promo is like 'q' or 'r' etc
        promo_piece = promo.upper()
        # Map to piece letter types
    return frm, to, promo_piece

def piece_color(piece_code):
    return piece_code[0]  # 'w'/'b'

def piece_type(piece_code):
    return piece_code[1]  # 'K','Q','R','B','N','P'

def opponent(color):
    return "black" if color == "white" else "white"

def find_king(pieces, color):
    k = "wK" if color == "white" else "bK"
    for sq, pc in pieces.items():
        if pc == k:
            return sq
    return None

def is_square_attacked(pieces, target_sq, by_color):
    tx, ty = sq_to_xy(target_sq)
    # Pawns
    diry = PAWN_DIR[by_color]
    pawn_attack_ranks = ty - diry  # because pawn at y+diry attacks target at ty
    for dx in (-1, 1):
        x = tx + dx
        y = pawn_attack_ranks
        if in_bounds(x, y):
            sq = xy_to_sq(x, y)
            pc = pieces.get(sq)
            if pc and piece_color(pc) == by_color and piece_type(pc) == "P":
                return True

    # Knights
    knight_steps = [(1,2),(2,1),(2,-1),(1,-2),(-1,-2),(-2,-1),(-2,1),(-1,2)]
    for dx, dy in knight_steps:
        x, y = tx+dx, ty+dy
        if in_bounds(x,y):
            sq = xy_to_sq(x,y)
            pc = pieces.get(sq)
            if pc and piece_color(pc)==by_color and piece_type(pc)=='N':
                return True

    # King
    for dx in (-1,0,1):
        for dy in (-1,0,1):
            if dx==0 and dy==0: 
                continue
            x,y=tx+dx,ty+dy
            if in_bounds(x,y):
                sq=xy_to_sq(x,y)
                pc=pieces.get(sq)
                if pc and piece_color(pc)==by_color and piece_type(pc)=='K':
                    return True

    # Sliding pieces: rooks/queens (orthogonal), bishops/queens (diagonal)
    # Orthogonal
    ortho_dirs = [(1,0),(-1,0),(0,1),(0,-1)]
    for dx,dy in ortho_dirs:
        x,y = tx+dx, ty+dy
        while in_bounds(x,y):
            sq=xy_to_sq(x,y)
            pc=pieces.get(sq)
            if pc:
                if piece_color(pc)==by_color:
                    pt=piece_type(pc)
                    if pt in ('R','Q'):
                        return True
                break
            x+=dx; y+=dy

    # Diagonal
    diag_dirs = [(1,1),(1,-1),(-1,1),(-1,-1)]
    for dx,dy in diag_dirs:
        x,y = tx+dx, ty+dy
        while in_bounds(x,y):
            sq=xy_to_sq(x,y)
            pc=pieces.get(sq)
            if pc:
                if piece_color(pc)==by_color:
                    pt=piece_type(pc)
                    if pt in ('B','Q'):
                        return True
                break
            x+=dx; y+=dy

    return False

def is_in_check(pieces, color):
    ksq = find_king(pieces, color)
    if not ksq:
        return False
    return is_square_attacked(pieces, ksq, opponent(color))

def apply_move(pieces, move, to_play_color):
    frm, to, promo_type = parse_move_uci(move)
    newp = dict(pieces)
    moving = newp.pop(frm)
    # capture if present
    if to in newp:
        newp.pop(to)
    # promotion
    if promo_type:
        # promo_type is like 'Q','R','B','N'
        newp[to] = to_play_color[0] + promo_type
    else:
        newp[to] = moving
    return newp

def generate_legal_moves_for_state(pieces, to_play_color):
    # We are not given legal_moves here; arena provides it externally.
    # But the API requirement says we only choose from provided legal_moves.
    # However the prompt does NOT include legal_moves in inputs.
    # Therefore we must reconstruct legal moves. We'll do a lightweight pseudo-legal generator
    # and filter by king safety. This is more work but required to be able to return a legal move.
    #
    # Note: Castling is encoded as king move by arena, but we will not implement castling
    # exhaustively; instead rely on pseudo-legal and king safety. For robust legality,
    # we still attempt castling if the position permits.
    #
    # This generator may not cover all special cases; but should handle common play.

    color = to_play_color
    opp = opponent(color)

    def own_piece(sq):
        pc = pieces.get(sq)
        return pc and piece_color(pc) == color

    def opp_piece(sq):
        pc = pieces.get(sq)
        return pc and piece_color(pc) == opp

    king_sq = find_king(pieces, color)
    if not king_sq:
        return []

    legal = []

    # Helper to test if move leaves king in check
    def consider(frm, to, promo_type=None):
        mv = frm + to + (promo_type.lower() if promo_type else "")
        # If promotion, UCI expects 5 chars: e.g., a2a1q
        # We'll build accordingly outside parsing.
        if promo_type:
            mv = frm + to + promo_type.lower()
        else:
            mv = frm + to
        newp = apply_move(pieces, mv, color)
        if not is_in_check(newp, color):
            legal.append(mv)

    # Generate pseudo-legal moves
    for sq, pc in pieces.items():
        if piece_color(pc) != color:
            continue
        pt = piece_type(pc)
        x,y = sq_to_xy(sq)

        if pt == 'P':
            diry = PAWN_DIR[color]
            # forward 1
            ny = y + diry
            if in_bounds(x, ny):
                nsq = xy_to_sq(x, ny)
                if nsq not in pieces:
                    # promotion?
                    if (color == 'white' and ny == 7) or (color == 'black' and ny == 0):
                        for pr in ('Q','R','B','N'):
                            consider(sq, nsq, pr)
                    else:
                        consider(sq, nsq, None)
                    # forward 2
                    start_rank = 1 if color == 'white' else 6  # 0-based
                    if y == start_rank:
                        ny2 = y + 2*diry
                        nsq2 = xy_to_sq(x, ny2)
                        if nsq2 not in pieces:
                            consider(sq, nsq2, None)
            # captures
            for dx in (-1,1):
                nx = x + dx
                ny = y + diry
                if in_bounds(nx, ny):
                    nsq = xy_to_sq(nx, ny)
                    if opp_piece(nsq):
                        if (color == 'white' and ny == 7) or (color == 'black' and ny == 0):
                            for pr in ('Q','R','B','N'):
                                consider(sq, nsq, pr)
                        else:
                            consider(sq, nsq, None)
            # en passant not implemented

        elif pt == 'N':
            for dx,dy in [(1,2),(2,1),(2,-1),(1,-2),(-1,-2),(-2,-1),(-2,1),(-1,2)]:
                nx,ny=x+dx,y+dy
                if not in_bounds(nx,ny): 
                    continue
                nsq=xy_to_sq(nx,ny)
                if not own_piece(nsq):
                    consider(sq, nsq, None)

        elif pt in ('B','R','Q'):
            dirs=[]
            if pt in ('B','Q'):
                dirs += [(1,1),(1,-1),(-1,1),(-1,-1)]
            if pt in ('R','Q'):
                dirs += [(1,0),(-1,0),(0,1),(0,-1)]
            for dx,dy in dirs:
                nx,ny=x+dx,y+dy
                while in_bounds(nx,ny):
                    nsq=xy_to_sq(nx,ny)
                    if own_piece(nsq):
                        break
                    if opp_piece(nsq):
                        consider(sq, nsq, None)
                        break
                    consider(sq, nsq, None)
                    nx+=dx; ny+=dy

        elif pt == 'K':
            for dx in (-1,0,1):
                for dy in (-1,0,1):
                    if dx==0 and dy==0: 
                        continue
                    nx,ny=x+dx,y+dy
                    if not in_bounds(nx,ny): 
                        continue
                    nsq=xy_to_sq(nx,ny)
                    if not own_piece(nsq):
                        consider(sq, nsq, None)
            # Castling (approximate, not tracking moved rights; only if squares empty and not in check)
            # We'll assume standard initial rook positions if present and path squares empty.
            # King must not be in check and squares it crosses not attacked.
            if color == 'white' and y==0 and x==4:
                # king e1
                if king_sq == 'e1':
                    # kingside: e1g1, rook h1
                    rook_sq='h1'
                    if pieces.get(rook_sq)=='wR' and 'f1' not in pieces and 'g1' not in pieces:
                        if not is_square_attacked(pieces, 'e1', opp) and not is_square_attacked(pieces, 'f1', opp) and not is_square_attacked(pieces, 'g1', opp):
                            consider('e1','g1', None)
                    # queenside: e1c1, rook a1, squares b1,c1,d1 empty
                    rook_sq='a1'
                    if pieces.get(rook_sq)=='wR' and 'd1' not in pieces and 'c1' not in pieces and 'b1' not in pieces:
                        if not is_square_attacked(pieces, 'e1', opp) and not is_square_attacked(pieces, 'd1', opp) and not is_square_attacked(pieces, 'c1', opp):
                            consider('e1','c1', None)
            if color == 'black' and y==7 and x==4:
                if king_sq == 'e8':
                    rook_sq='h8'
                    if pieces.get(rook_sq)=='bR' and 'f8' not in pieces and 'g8' not in pieces:
                        if not is_square_attacked(pieces, 'e8', opp) and not is_square_attacked(pieces, 'f8', opp) and not is_square_attacked(pieces, 'g8', opp):
                            consider('e8','g8', None)
                    rook_sq='a8'
                    if pieces.get(rook_sq)=='bR' and 'd8' not in pieces and 'c8' not in pieces and 'b8' not in pieces:
                        if not is_square_attacked(pieces, 'e8', opp) and not is_square_attacked(pieces, 'd8', opp) and not is_square_attacked(pieces, 'c8', opp):
                            consider('e8','c8', None)

    return legal

def move_gives_check(pieces, move, color):
    newp = apply_move(pieces, move, color)
    return is_in_check(newp, opponent(color))  # opponent king attacked

def move_results_in_checkmate(pieces, move, color):
    # after move, opponent to play is in checkmate?
    newp = apply_move(pieces, move, color)
    opp = opponent(color)
    if not is_in_check(newp, opp):
        return False
    # If opponent has any legal move to escape, not mate
    opp_legal = generate_legal_moves_for_state(newp, opp)
    return len(opp_legal) == 0

def evaluate_move(pieces, move, color):
    frm, to, promo_type = parse_move_uci(move)
    moving = pieces.get(frm)
    if not moving:
        return -10**9
    mt = piece_type(moving)
    mc = piece_color(moving)
    assert mc == color
    opp = opponent(color)

    captured_value = 0
    if to in pieces and piece_color(pieces[to]) == opp:
        captured_value = PIECE_VALUE[piece_type(pieces[to])]

    # One-ply recapture safety estimate:
    newp = apply_move(pieces, move, color)
    # Determine if our moved piece is immediately capturable by opponent
    # Find moved piece square
    moved_sq = to
    # If we captured, opponent might capture something else; still approximate
    # by checking if any opponent move captures moved_sq.
    # We'll generate opponent legal moves quickly.
    opp_moves = generate_legal_moves_for_state(newp, opp)
    attacked_by_opp = False
    best_recapture = 0
    for om in opp_moves:
        _, ot, _promo = parse_move_uci(om)
        # if opponent lands on moved_sq, it's a capture (or could be non-capture if same square)
        if ot == moved_sq:
            # compute what they capture: piece currently on moved_sq (ours)
            if moved_sq in newp and piece_color(newp[moved_sq]) == color:
                attacked_by_opp = True
                best_recapture = max(best_recapture, PIECE_VALUE[piece_type(newp[moved_sq])])
    hang_penalty = 0
    if attacked_by_opp:
        # punish losing piece, but less if it was already a trade
        hang_penalty = 0.9 * PIECE_VALUE[mt]

    # Prefer check
    check_bonus = 0
    if is_square_attacked(newp, find_king(newp, opp), color):
        # opponent is in check after move
        check_bonus = 250

    # Prefer centralization for non-king pieces
    cx = sq_to_xy(to)[0]
    cy = sq_to_xy(to)[1]
    center_dist = abs(cx-3.5) + abs(cy-3.5)  # lower better
    center_bonus = int(40 * (4.0 - center_dist))

    # King safety: moving king to safer square (not attacked)
    king_bonus = 0
    if mt == 'K':
        if not is_square_attacked(newp, to, opp):
            king_bonus = 200

    promo_bonus = 0
    if promo_type:
        promo_bonus = PIECE_VALUE[promo_type] - PIECE_VALUE['P'] + 800

    score = (captured_value - hang_penalty) + check_bonus + center_bonus + king_bonus + promo_bonus
    return score

def policy(pieces: dict[str, str], to_play: str) -> str:
    color = to_play  # 'white'/'black'
    legal_moves = generate_legal_moves_for_state(pieces, color)
    if not legal_moves:
        # Fallback: if generator fails, choose a deterministic move among pseudo moves (should not happen)
        # Return any move-like string is disallowed; must be legal. Here, just return a first legal if empty can't.
        return "a1a1"

    # 1) Mate in one / immediate checkmate
    mates = []
    for mv in legal_moves:
        if move_results_in_checkmate(pieces, mv, color):
            mates.append(mv)
    if mates:
        # deterministic pick
        return sorted(mates)[0]

    # 2) Any checking move (prefer those that also capture)
    checking = []
    for mv in legal_moves:
        if move_gives_check(pieces, mv, color):
            checking.append(mv)
    if checking:
        # choose best among checking moves
        best = None
        best_score = -10**18
        for mv in checking:
            sc = evaluate_move(pieces, mv, color) + 5000  # strong preference for check
            if sc > best_score:
                best_score = sc
                best = mv
        return best if best is not None else sorted(checking)[0]

    # 3) Otherwise best material/capture/safety move
    best = None
    best_score = -10**18
    # Small determinism: random tie-break seeded by position
    seed = 0
    for sq, pc in sorted(pieces.items()):
        seed = (seed * 1315423911 + hash(sq) + hash(pc)) & 0xFFFFFFFF
    rng = random.Random(seed)

    for mv in legal_moves:
        sc = evaluate_move(pieces, mv, color)
        # Add tiny noise to break ties stably
        sc += rng.randint(0, 3) * 0.01
        if sc > best_score:
            best_score = sc
            best = mv

    return best if best is not None else legal_moves[0]
