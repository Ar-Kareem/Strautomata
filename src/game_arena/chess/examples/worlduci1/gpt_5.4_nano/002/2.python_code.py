
import random

PIECE_VALUE = {
    'P': 100,
    'N': 320,
    'B': 330,
    'R': 500,
    'Q': 900,
    'K': 100000
}

FILES = "abcdefgh"
RANKS = "12345678"

def sq_to_xy(sq: str):
    return (FILES.index(sq[0]), RANKS.index(sq[1]))

def xy_to_sq(x, y):
    return FILES[x] + RANKS[y]

def in_bounds(x, y):
    return 0 <= x < 8 and 0 <= y < 8

def color_of(pc): 
    return pc[0]

def type_of(pc):
    return pc[1]

def other_color(c):
    return 'b' if c == 'w' else 'w'

def king_square(pieces, c):
    k = 'wK' if c == 'w' else 'bK'
    for sq, pc in pieces.items():
        if pc == k:
            return sq
    return None

# Generate pseudo-legal moves (captures included) for a given color (ignores check legality).
# Used only for attack detection and simple legality check.
def gen_pseudo_moves(pieces, color):
    moves = []
    for sq, pc in pieces.items():
        if color_of(pc) != color:
            continue
        pt = type_of(pc)
        x, y = sq_to_xy(sq)

        def add_move(to_sq, promo=None):
            if promo:
                moves.append(sq + to_sq + promo)
            else:
                moves.append(sq + to_sq)

        if pt == 'P':
            diry = 1 if color == 'w' else -1
            start_rank = 1 if color == 'w' else 6
            promote_rank = 7 if color == 'w' else 0

            # forward
            ny = y + diry
            if in_bounds(x, ny):
                to_sq = xy_to_sq(x, ny)
                if to_sq not in pieces:
                    if ny == promote_rank:
                        for promo in ['q','r','b','n']:
                            add_move(to_sq, promo)
                    else:
                        add_move(to_sq)
                    # double
                    if y == start_rank:
                        ny2 = y + 2*diry
                        to_sq2 = xy_to_sq(x, ny2)
                        if to_sq2 not in pieces:
                            add_move(to_sq2)

            # captures
            for dx in (-1, 1):
                nx = x + dx
                ny = y + diry
                if in_bounds(nx, ny):
                    to_sq = xy_to_sq(nx, ny)
                    if to_sq in pieces and color_of(pieces[to_sq]) != color:
                        if ny == promote_rank:
                            for promo in ['q','r','b','n']:
                                add_move(to_sq, promo)
                        else:
                            add_move(to_sq)

        elif pt == 'N':
            for dx, dy in [(1,2),(2,1),(2,-1),(1,-2),(-1,-2),(-2,-1),(-2,1),(-1,2)]:
                nx, ny = x+dx, y+dy
                if not in_bounds(nx, ny): 
                    continue
                to_sq = xy_to_sq(nx, ny)
                if to_sq not in pieces or color_of(pieces[to_sq]) != color:
                    add_move(to_sq)

        elif pt in ('B','R','Q'):
            dirs = []
            if pt in ('B','Q'):
                dirs += [(1,1),(1,-1),(-1,1),(-1,-1)]
            if pt in ('R','Q'):
                dirs += [(1,0),(-1,0),(0,1),(0,-1)]
            for dx, dy in dirs:
                nx, ny = x+dx, y+dy
                while in_bounds(nx, ny):
                    to_sq = xy_to_sq(nx, ny)
                    if to_sq in pieces:
                        if color_of(pieces[to_sq]) != color:
                            add_move(to_sq)
                        break
                    add_move(to_sq)
                    nx += dx
                    ny += dy

        elif pt == 'K':
            for dx in (-1,0,1):
                for dy in (-1,0,1):
                    if dx == 0 and dy == 0: 
                        continue
                    nx, ny = x+dx, y+dy
                    if not in_bounds(nx, ny):
                        continue
                    to_sq = xy_to_sq(nx, ny)
                    if to_sq not in pieces or color_of(pieces[to_sq]) != color:
                        add_move(to_sq)
            # castling not generated here; arena legal_moves includes it, but attack detection
            # doesn't need pseudo castling.

    # remove moves that are impossible due to occupancy? Pseudo generation already respects.
    return moves

def apply_move(pieces, move, to_play):
    # move is UCI like e2e4, or a7a8q
    from_sq = move[0:2]
    to_sq = move[2:4]
    promo = move[4] if len(move) > 4 else None

    new = dict(pieces)
    pc = new.pop(from_sq)
    # capture
    if to_sq in new:
        new.pop(to_sq)
    if promo:
        # promote to same color with type promo
        # promo is 'q','r','b','n'
        new[to_sq] = to_play + promo.upper()
    else:
        new[to_sq] = pc
    return new

def is_square_attacked(pieces, sq, by_color):
    # compute if sq is attacked by any piece of by_color using pseudo move patterns
    # We'll do pattern-based ray/knight/pawn/king attacks for speed.
    x, y = sq_to_xy(sq)

    # Pawns
    diry = 1 if by_color == 'w' else -1
    pawn_from_y = y - diry
    for dx in (-1, 1):
        nx = x + dx
        ny = pawn_from_y
        if in_bounds(nx, ny):
            from_sq = xy_to_sq(nx, ny)
            if from_sq in pieces and pieces[from_sq] == by_color + 'P':
                return True

    # Knights
    for dx, dy in [(1,2),(2,1),(2,-1),(1,-2),(-1,-2),(-2,-1),(-2,1),(-1,2)]:
        nx, ny = x+dx, y+dy
        if in_bounds(nx, ny):
            from_sq = xy_to_sq(nx, ny)
            if from_sq in pieces and pieces[from_sq] == by_color + 'N':
                return True

    # King
    for dx in (-1,0,1):
        for dy in (-1,0,1):
            if dx == 0 and dy == 0: 
                continue
            nx, ny = x+dx, y+dy
            if in_bounds(nx, ny):
                from_sq = xy_to_sq(nx, ny)
                if from_sq in pieces and pieces[from_sq] == by_color + 'K':
                    return True

    # Sliding pieces
    def ray_attack(dxs, dys, attackers):
        for dx, dy in zip(dxs, dys):
            nx, ny = x+dx, y+dy
            while in_bounds(nx, ny):
                s = xy_to_sq(nx, ny)
                if s in pieces:
                    if pieces[s][0] == by_color and pieces[s][1] in attackers:
                        return True
                    break
                nx += dx
                ny += dy
        return False

    # Bishops/Queens on diagonals
    if ray_attack([1,1,-1,-1],[1,-1,1,-1], {'B','Q'}):
        return True
    # Rooks/Queens on orthogonals
    if ray_attack([1,-1,0,0],[0,0,1,-1], {'R','Q'}):
        return True

    return False

def is_in_check(pieces, color):
    ksq = king_square(pieces, color)
    if not ksq:
        return False
    return is_square_attacked(pieces, ksq, other_color(color))

def legal_moves_from_given(pieces, to_play, legal_moves):
    # We trust arena's provided legal_moves; still need to evaluate legality after hypothetical moves.
    return legal_moves

def score_move(pieces, move, to_play, legal_moves_opponent_after=None):
    enemy = other_color('w' if to_play=='white' else 'b')
    # translate to_play string to color code
    c = 'w' if to_play == 'white' else 'b'
    opp = other_color(c)

    from_sq = move[0:2]
    to_sq = move[2:4]
    promo = move[4] if len(move) > 4 else None

    pc = pieces[from_sq]
    pt = type_of(pc)

    new_pieces = apply_move(pieces, move, c)

    # Checkmate detection: opponent has no legal moves and is in check (or at least no legal)
    # We can only infer checkmate if we can generate opponent legal moves, but arena doesn't give those.
    # We'll do a lightweight legality filter by generating pseudo moves and removing those that leave king in check.
    def opponent_legal_moves(gen_color):
        pseudo = gen_pseudo_moves(new_pieces, gen_color)
        # Filter by ensuring move is among provided by arena? not available.
        # We'll do full legality filtering using check constraint.
        leg = []
        for m in pseudo:
            # Only consider moves that match to_sq/from_sq structure and promotion if needed.
            # Since pseudo might include illegal castling, it's fine; castling isn't in pseudo.
            # For accuracy, require that m equals UCI for move; but we don't know capture etc.
            # Better: accept all pseudo then filter by king safety.
            test = apply_move(new_pieces, m, gen_color)
            if not is_in_check(test, gen_color):
                leg.append(m)
        return leg

    opp_legals = opponent_legal_moves(opp)

    # If opponent has no legal moves, it's mate or stalemate; prefer mate.
    if len(opp_legals) == 0:
        if is_in_check(new_pieces, opp):
            return 1e9  # mate
        else:
            return 0  # stalemate

    # Immediate check bonus
    gives_check = is_in_check(new_pieces, opp)
    score = 0
    if gives_check:
        score += 200000

    # Material gain from capture
    captured_value = 0
    if to_sq in pieces and pieces[to_sq][0] == opp:
        captured_value = PIECE_VALUE[type_of(pieces[to_sq])]
        score += captured_value * 10

    # Promotions: strong bonus
    if promo:
        score += 80000
        # small adjustment: promote to queen generally
        score += {'q': 12000, 'r': 6000, 'b': 4000, 'n': 3000}.get(promo, 0)

    # Avoid hanging pieces: penalize if destination is attacked by opponent and the moving piece can be captured
    # (approximate by whether to_sq is attacked)
    if is_square_attacked(new_pieces, to_sq, opp):
        # If move was a non-capture and piece is attacked, penalize.
        if not (to_sq in pieces and pieces[to_sq][0] == opp):
            score -= PIECE_VALUE.get(pt, 0) * 0.7
        else:
            score -= PIECE_VALUE.get(pt, 0) * 0.25

    # Positional: center preference and pawn advancement
    x, y = sq_to_xy(to_sq)
    center_dist = abs(x-3.5) + abs(y-3.5)
    score += int((7 - center_dist) * 12)

    if pt == 'P':
        # reward advancing
        rank = int(to_sq[1])
        score += rank * (10 if c == 'w' else 90)  # just monotonic in direction

    # King safety: if king moves, prefer towards safety (being less attacked)
    if pt == 'K':
        if is_square_attacked(new_pieces, to_sq, opp):
            score -= 50000
        else:
            score += 2000

    # Random tie-break to avoid deterministic blunders
    score += random.randint(-50, 50)
    return score

def policy(pieces: dict[str, str], to_play: str) -> str:
    # Arena provides legal_moves externally, but our API doesn't explicitly pass them.
    # However, the prompt implies 'legal_moves' is available from environment when evaluating.
    # To comply with "Return exactly ONE move string that is an element of legal_moves",
    # we must retrieve legal_moves from a global variable if present.
    #
    # In many arenas, legal moves are passed as an additional argument or stored globally.
    # Here, we attempt to read from globals; if absent, we generate pseudo-legal moves
    # and pick the best legal among them. This keeps the function robust.
    c = 'w' if to_play == 'white' else 'b'

    legal_moves = globals().get("legal_moves", None)
    if not legal_moves:
        # Fallback: generate legal moves by filtering pseudo moves for king safety.
        pseudo = gen_pseudo_moves(pieces, c)
        leg = []
        for m in pseudo:
            test = apply_move(pieces, m, c)
            if not is_in_check(test, c):
                leg.append(m)
        legal_moves = leg

    # If no legal moves, return empty (but should not happen in valid games).
    if not legal_moves:
        return ""

    # Evaluate all legal moves and pick max score
    best = None
    best_score = -1e18
    for m in legal_moves:
        s = score_move(pieces, m, to_play)
        if s > best_score:
            best_score = s
            best = m
    return best
