
import random

# --------- Basic board utilities (no external chess libs) ----------

FILES = "abcdefgh"
RANKS = "12345678"

PIECE_VALUE = {
    "P": 100,
    "N": 320,
    "B": 330,
    "R": 500,
    "Q": 900,
    "K": 0,
}

def sq_to_xy(sq: str):
    return FILES.index(sq[0]), RANKS.index(sq[1])

def xy_to_sq(x, y):
    return FILES[x] + RANKS[y]

def in_bounds(x, y):
    return 0 <= x < 8 and 0 <= y < 8

def color_of(pc): return pc[0]
def type_of(pc): return pc[1]

def other(color): return "black" if color == "white" else "white"

def coord_to_uci(from_sq, to_sq, promo=None):
    if promo:
        return from_sq + to_sq + promo
    return from_sq + to_sq

# --------- Move generation / legality checking ----------

KNIGHT_DELTAS = [(1,2),(2,1),(-1,2),(-2,1),(1,-2),(2,-1),(-1,-2),(-2,-1)]
KING_DELTAS = [(1,1),(1,0),(1,-1),(0,1),(0,-1),(-1,1),(-1,0),(-1,-1)]
BISHOP_DIRS = [(1,1),(1,-1),(-1,1),(-1,-1)]
ROOK_DIRS = [(1,0),(-1,0),(0,1),(0,-1)]

def find_king(pieces, color):
    k = "wK" if color == "white" else "bK"
    for sq, pc in pieces.items():
        if pc == k:
            return sq
    return None

def is_square_attacked(pieces, target_sq, by_color):
    tx, ty = sq_to_xy(target_sq)
    # Pawns
    if by_color == "white":
        pawn_sources = [(tx-1, ty-1), (tx+1, ty-1)]
        for x,y in pawn_sources:
            if in_bounds(x,y):
                s = xy_to_sq(x,y)
                if pieces.get(s) == "wP":
                    return True
    else:
        pawn_sources = [(tx-1, ty+1), (tx+1, ty+1)]
        for x,y in pawn_sources:
            if in_bounds(x,y):
                s = xy_to_sq(x,y)
                if pieces.get(s) == "bP":
                    return True

    # Knights
    ncode = "wN" if by_color == "white" else "bN"
    for dx,dy in KNIGHT_DELTAS:
        x,y = tx+dx, ty+dy
        if in_bounds(x,y):
            s = xy_to_sq(x,y)
            if pieces.get(s) == ncode:
                return True

    # Bishops/Queens (diagonals)
    bcode = "wB" if by_color == "white" else "bB"
    qcode = "wQ" if by_color == "white" else "bQ"
    for dx,dy in BISHOP_DIRS:
        x,y = tx+dx, ty+dy
        while in_bounds(x,y):
            s = xy_to_sq(x,y)
            pc = pieces.get(s)
            if pc:
                if pc == bcode or pc == qcode:
                    return True
                break
            x += dx; y += dy

    # Rooks/Queens (orthogonals)
    rcode = "wR" if by_color == "white" else "bR"
    for dx,dy in ROOK_DIRS:
        x,y = tx+dx, ty+dy
        while in_bounds(x,y):
            s = xy_to_sq(x,y)
            pc = pieces.get(s)
            if pc:
                if pc == rcode or pc == qcode:
                    return True
                break
            x += dx; y += dy

    # King
    kcode = "wK" if by_color == "white" else "bK"
    for dx,dy in KING_DELTAS:
        x,y = tx+dx, ty+dy
        if in_bounds(x,y):
            s = xy_to_sq(x,y)
            if pieces.get(s) == kcode:
                return True

    return False

def in_check(pieces, color):
    ksq = find_king(pieces, color)
    if not ksq:
        return False
    by_color = other(color)
    return is_square_attacked(pieces, ksq, by_color)

def apply_move(pieces, move, to_play):
    # move: UCI like e2e4 or a7a8q
    newp = dict(pieces)
    if len(move) == 4:
        f = move[:2]; t = move[2:]
        promo = None
    else:
        f = move[:2]; t = move[2:4]
        promo_letter = move[4]
        promo_map = {'q':'Q','r':'R','b':'B','n':'N'}
        promo = promo_map.get(promo_letter, 'Q')
    pc = newp.pop(f)
    # capture
    if t in newp:
        newp.pop(t)
    if promo:
        pc = pc[0] + promo
    newp[t] = pc
    return newp

def generate_pseudo_legal_moves(pieces, color):
    moves = []
    my_prefix = "w" if color == "white" else "b"
    opp_prefix = "b" if color == "white" else "w"

    for from_sq, pc in pieces.items():
        if not pc.startswith(my_prefix):
            continue
        ptype = pc[1]
        fx, fy = sq_to_xy(from_sq)

        # Pawn
        if ptype == "P":
            diry = 1 if color == "white" else -1
            start_rank = 1 if color == "white" else 6
            promo_rank = 7 if color == "white" else 0

            # forward
            nx, ny = fx, fy + diry
            if in_bounds(nx, ny):
                to_sq = xy_to_sq(nx, ny)
                if to_sq not in pieces:
                    if ny == promo_rank:
                        for pl in ['q','r','b','n']:
                            moves.append(from_sq + to_sq + pl)
                    else:
                        moves.append(from_sq + to_sq)
                    # double
                    if fy == start_rank:
                        ny2 = fy + 2*diry
                        to_sq2 = xy_to_sq(fx, ny2)
                        if to_sq2 not in pieces:
                            moves.append(from_sq + to_sq2)

            # captures
            for dx in (-1, 1):
                nx, ny = fx + dx, fy + diry
                if in_bounds(nx, ny):
                    to_sq = xy_to_sq(nx, ny)
                    if to_sq in pieces and pieces[to_sq].startswith(opp_prefix):
                        if ny == promo_rank:
                            for pl in ['q','r','b','n']:
                                moves.append(from_sq + to_sq + pl)
                        else:
                            moves.append(from_sq + to_sq)

        # Knight
        elif ptype == "N":
            for dx,dy in KNIGHT_DELTAS:
                nx, ny = fx+dx, fy+dy
                if not in_bounds(nx, ny): 
                    continue
                to_sq = xy_to_sq(nx, ny)
                if to_sq not in pieces or pieces[to_sq].startswith(opp_prefix):
                    moves.append(from_sq + to_sq)

        # Bishop
        elif ptype == "B":
            for dx,dy in BISHOP_DIRS:
                nx, ny = fx+dx, fy+dy
                while in_bounds(nx, ny):
                    to_sq = xy_to_sq(nx, ny)
                    if to_sq in pieces:
                        if pieces[to_sq].startswith(opp_prefix):
                            moves.append(from_sq + to_sq)
                        break
                    moves.append(from_sq + to_sq)
                    nx += dx; ny += dy

        # Rook
        elif ptype == "R":
            for dx,dy in ROOK_DIRS:
                nx, ny = fx+dx, fy+dy
                while in_bounds(nx, ny):
                    to_sq = xy_to_sq(nx, ny)
                    if to_sq in pieces:
                        if pieces[to_sq].startswith(opp_prefix):
                            moves.append(from_sq + to_sq)
                        break
                    moves.append(from_sq + to_sq)
                    nx += dx; ny += dy

        # Queen
        elif ptype == "Q":
            for dx,dy in BISHOP_DIRS + ROOK_DIRS:
                nx, ny = fx+dx, fy+dy
                while in_bounds(nx, ny):
                    to_sq = xy_to_sq(nx, ny)
                    if to_sq in pieces:
                        if pieces[to_sq].startswith(opp_prefix):
                            moves.append(from_sq + to_sq)
                        break
                    moves.append(from_sq + to_sq)
                    nx += dx; ny += dy

        # King (no castling support: arena examples say castling as king move, but
        # without castling rights info we avoid generating it; still legal moves likely include
        # castling, but if provided, our move selection must match legality. If castling exists in
        # input legal list, our generator may not produce it. To be safe, we include castling
        # only if king/rook present and path empty and squares not attacked. We'll approximate.)
        elif ptype == "K":
            for dx,dy in KING_DELTAS:
                nx, ny = fx+dx, fy+dy
                if not in_bounds(nx, ny): 
                    continue
                to_sq = xy_to_sq(nx, ny)
                if to_sq not in pieces or pieces[to_sq].startswith(opp_prefix):
                    moves.append(from_sq + to_sq)

            # Castling approximation using current occupancy and attacked squares.
            # White: king e1, rooks a1/h1
            if color == "white" and from_sq == "e1":
                # King side
                if pieces.get("h1") == "wR" and "f1" not in pieces and "g1" not in pieces:
                    if not is_square_attacked(pieces, "e1", "black") and not is_square_attacked(pieces, "f1", "black") and not is_square_attacked(pieces, "g1", "black"):
                        moves.append("e1g1")
                # Queen side
                if pieces.get("a1") == "wR" and "b1" not in pieces and "c1" not in pieces and "d1" not in pieces:
                    if not is_square_attacked(pieces, "e1", "black") and not is_square_attacked(pieces, "d1", "black") and not is_square_attacked(pieces, "c1", "black"):
                        moves.append("e1c1")
            if color == "black" and from_sq == "e8":
                if pieces.get("h8") == "bR" and "f8" not in pieces and "g8" not in pieces:
                    if not is_square_attacked(pieces, "e8", "white") and not is_square_attacked(pieces, "f8", "white") and not is_square_attacked(pieces, "g8", "white"):
                        moves.append("e8g8")
                if pieces.get("a8") == "bR" and "b8" not in pieces and "c8" not in pieces and "d8" not in pieces:
                    if not is_square_attacked(pieces, "e8", "white") and not is_square_attacked(pieces, "d8", "white") and not is_square_attacked(pieces, "c8", "white"):
                        moves.append("e8c8")

    return moves

def is_move_legal(pieces, move, color):
    # handle castling rook movement for applying legality
    if move in ("e1g1","e1c1","e8g8","e8c8"):
        newp = dict(pieces)
        k_from = move[:2]; k_to = move[2:4]
        king = newp.pop(k_from)
        # move rook accordingly
        if move == "e1g1":
            rook_from, rook_to = "h1", "f1"
        elif move == "e1c1":
            rook_from, rook_to = "a1", "d1"
        elif move == "e8g8":
            rook_from, rook_to = "h8", "f8"
        else:
            rook_from, rook_to = "a8", "d8"
        rook = newp.pop(rook_from)
        newp[rook_to] = rook
        # capture on destination if any (shouldn't happen)
        if k_to in newp:
            newp.pop(k_to)
        newp[k_to] = king
        # king safety
        return not in_check(newp, color)

    # normal
    newp = apply_move(pieces, move, color)
    return not in_check(newp, color)

def generate_legal_moves(pieces, color):
    pseudo = generate_pseudo_legal_moves(pieces, color)
    legal = []
    for m in pseudo:
        if is_move_legal(pieces, m, color):
            legal.append(m)
    return legal

# --------- Scoring / selection ----------

def material_score(pieces, color):
    my_prefix = "w" if color == "white" else "b"
    opp_prefix = "b" if color == "white" else "w"
    s = 0
    for pc in pieces.values():
        t = pc[1]
        v = PIECE_VALUE[t]
        if pc.startswith(my_prefix):
            s += v
        else:
            s -= v
    return s

def mvv_lva(attacker_piece, captured_piece):
    if captured_piece is None:
        return 0
    return PIECE_VALUE[captured_piece[1]] - PIECE_VALUE[attacker_piece[1]]//10

def evaluate(pieces, color):
    # simple: material + king safety (if in check penalty) + centralization
    s = material_score(pieces, color)
    if in_check(pieces, color):
        s -= 500
    # piece-square light centralization
    center = {"d4":10,"e4":10,"d5":10,"e5":10,
              "c4":5,"f4":5,"c5":5,"f5":5}
    for sq, pc in pieces.items():
        if pc[0] == ("w" if color=="white" else "b"):
            s += center.get(sq,0)
    return s

def move_gives_mate(pieces, move, color):
    # make move, if opponent in checkmate (no legal moves and in check)
    newp = apply_move(pieces, move, color) if move not in ("e1g1","e1c1","e8g8","e8c8") else None
    if move in ("e1g1","e1c1","e8g8","e8c8"):
        newp = dict(pieces)
        k_from = move[:2]; k_to = move[2:4]
        king = newp.pop(k_from)
        if move == "e1g1":
            rook_from, rook_to = "h1", "f1"
        elif move == "e1c1":
            rook_from, rook_to = "a1", "d1"
        elif move == "e8g8":
            rook_from, rook_to = "h8", "f8"
        else:
            rook_from, rook_to = "a8", "d8"
        newp.pop(rook_from)
        newp[rook_to] = pieces[rook_from]
        if k_to in newp:
            newp.pop(k_to)
        newp[k_to] = king
    opp = other(color)
    if not in_check(newp, opp):
        return False
    opp_legal = generate_legal_moves(newp, opp)
    return len(opp_legal) == 0

def is_check_move(pieces, move, color):
    newp = apply_move(pieces, move, color) if move not in ("e1g1","e1c1","e8g8","e8c8") else None
    if move in ("e1g1","e1c1","e8g8","e8c8"):
        newp = dict(pieces)
        k_from = move[:2]; k_to = move[2:4]
        king = newp.pop(k_from)
        if move == "e1g1":
            rook_from, rook_to = "h1", "f1"
        elif move == "e1c1":
            rook_from, rook_to = "a1", "d1"
        elif move == "e8g8":
            rook_from, rook_to = "h8", "f8"
        else:
            rook_from, rook_to = "a8", "d8"
        rook = newp.pop(rook_from)
        newp[rook_to] = rook
        if k_to in newp:
            newp.pop(k_to)
        newp[k_to] = king
    opp = other(color)
    return in_check(newp, opp)

def choose_move(pieces, color, legal_moves):
    # Immediate mate
    for m in legal_moves:
        if move_gives_mate(pieces, m, color):
            return m

    best = None
    best_score = -10**18

    my_prefix = "w" if color == "white" else "b"
    opp_prefix = "b" if color == "white" else "w"

    for m in legal_moves:
        f = m[:2]; t = m[2:4]
        promo = m[4] if len(m) == 5 else None
        attacker = pieces.get(f)
        captured = pieces.get(t)
        score = 0

        # checks
        if is_check_move(pieces, m, color):
            score += 400

        # captures/material gain
        if captured:
            score += 250 + mvv_lva(attacker, captured)

        # promotions: big bonus
        if promo:
            score += 800  # queen-like by default
            # discourage underpromotion a bit
            if promo in ('n','b','r'):
                score -= 50

        # king safety / avoid blunders: prefer not allowing immediate recapture large
        newp = apply_move(pieces, m, color) if m not in ("e1g1","e1c1","e8g8","e8c8") else None
        if m in ("e1g1","e1c1","e8g8","e8c8"):
            newp = dict(pieces)
            k_from = m[:2]; k_to = m[2:4]
            king = newp.pop(k_from)
            if m == "e1g1":
                rook_from, rook_to = "h1", "f1"
            elif m == "e1c1":
                rook_from, rook_to = "a1", "d1"
            elif m == "e8g8":
                rook_from, rook_to = "h8", "f8"
            else:
                rook_from, rook_to = "a8", "d8"
            rook = newp.pop(rook_from)
            newp[rook_to] = rook
            if k_to in newp:
                newp.pop(k_to)
            newp[k_to] = king

        # if we move into check (shouldn't happen), huge penalty
        if in_check(newp, color):
            score -= 10**7

        # if opponent can capture our moved piece immediately with high value, penalize
        opp = other(color)
        opp_moves = generate_pseudo_legal_moves(newp, opp)
        moved_piece_sq = t
        # Determine captured on t after move already happened; only consider if our piece exists there.
        our_piece_after = newp.get(moved_piece_sq)
        if our_piece_after and our_piece_after.startswith(my_prefix):
            # see if any opponent pseudo move captures that square
            for om in opp_moves:
                ot = om[2:4]
                if len(om) == 4 and ot == moved_piece_sq:
                    # only count captures
                    # check if target actually has our piece (it does)
                    score -= PIECE_VALUE[our_piece_after[1]] * 0.15

        score += evaluate(newp, color)

        # random tiebreak to avoid determinism traps
        score += random.random() * 1e-3

        if score > best_score:
            best_score = score
            best = m

    return best if best is not None else random.choice(legal_moves)

def policy(pieces: dict[str, str], to_play: str) -> str:
    color = "white" if to_play == "white" else "black"
    legal_moves = generate_legal_moves(pieces, color)
    # Fallback: if our generator somehow fails, pick any pseudo-legal legal-ish by safety
    if not legal_moves:
        pseudo = generate_pseudo_legal_moves(pieces, color)
        for m in pseudo:
            if is_move_legal(pieces, m, color):
                return m
        # last resort
        return pseudo[0]
    return choose_move(pieces, color, legal_moves)
