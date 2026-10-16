
import random

FILES = "abcdefgh"
RANKS = "12345678"

PIECE_VALUES = {
    'P': 100,
    'N': 320,
    'B': 330,
    'R': 500,
    'Q': 900,
    'K': 20000
}

# Simple piece-square tables (from white perspective). Values are centipawns-ish.
# Keep modest to stay fast and robust.
PST = {
    'P': [
        [0]*8,
        [50, 55, 60, 65, 65, 60, 55, 50],
        [15, 25, 30, 40, 40, 30, 25, 15],
        [10, 15, 20, 30, 30, 20, 15, 10],
        [5, 10, 15, 25, 25, 15, 10, 5],
        [0, 5, 10, 15, 15, 10, 5, 0],
        [0]*8,
        [0]*8
    ],
    'N': [
        [-50,-40,-30,-30,-30,-30,-40,-50],
        [-40,-20,  0,  0,  0,  0,-20,-40],
        [-30,  0, 10, 15, 15, 10,  0,-30],
        [-30,  5, 15, 20, 20, 15,  5,-30],
        [-30,  0, 15, 20, 20, 15,  0,-30],
        [-30,  5, 10, 15, 15, 10,  5,-30],
        [-40,-20,  0,  5,  5,  0,-20,-40],
        [-50,-40,-30,-30,-30,-30,-40,-50],
    ],
    'B': [
        [-20,-10,-10,-10,-10,-10,-10,-20],
        [-10,  0,  0,  0,  0,  0,  0,-10],
        [-10,  0,  5, 10, 10,  5,  0,-10],
        [-10,  5,  5, 10, 10,  5,  5,-10],
        [-10,  0, 10, 10, 10, 10,  0,-10],
        [-10, 10, 10, 10, 10, 10, 10,-10],
        [-10,  5,  0,  0,  0,  0,  5,-10],
        [-20,-10,-10,-10,-10,-10,-10,-20],
    ],
    'R': [
        [0, 0, 0, 5, 5, 0, 0, 0],
        [-5, 0, 0, 0, 0, 0, 0,-5],
        [-5, 0, 0, 0, 0, 0, 0,-5],
        [-5, 0, 0, 0, 0, 0, 0,-5],
        [-5, 0, 0, 0, 0, 0, 0,-5],
        [-5, 0, 0, 0, 0, 0, 0,-5],
        [5,10,10,10,10,10,10, 5],
        [0, 0, 0, 0, 0, 0, 0, 0],
    ],
    'Q': [
        [-20,-10,-10, -5, -5,-10,-10,-20],
        [-10,  0,  0,  0,  0,  0,  0,-10],
        [-10,  0,  5,  5,  5,  5,  0,-10],
        [ -5,  0,  5,  5,  5,  5,  0, -5],
        [  0,  0,  5,  5,  5,  5,  0,  0],
        [-10,  5,  5,  5,  5,  5,  5,-10],
        [-10,  0,  5,  0,  0,  0,  0,-10],
        [-20,-10,-10, -5, -5,-10,-10,-20],
    ],
    'K': [
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-20,-30,-30,-40,-40,-30,-30,-20],
        [-10,-20,-20,-20,-20,-20,-20,-10],
        [ 20, 20,  0,  0,  0,  0, 20, 20],
        [ 20, 30, 10,  0,  0, 10, 30, 20],
    ]
}

def sq_to_xy(sq):
    f = ord(sq[0]) - ord('a')
    r = ord(sq[1]) - ord('1')
    return f, r

def xy_to_sq(x, y):
    return f"{FILES[x]}{y+1}"

def in_bounds(x,y):
    return 0 <= x < 8 and 0 <= y < 8

def opposite(color):
    return 'b' if color == 'w' else 'w'

def king_square(pieces, color):
    k = color + 'K'
    for sq, pc in pieces.items():
        if pc == k:
            return sq
    return None

def is_attacked(pieces, attacker_color, target_sq):
    tx, ty = sq_to_xy(target_sq)
    # Generate attacks from each attacker piece type (pseudo)
    for sq, pc in pieces.items():
        if pc[0] != attacker_color:
            continue
        p = pc[1]
        x, y = sq_to_xy(sq)
        if p == 'P':
            diry = 1 if attacker_color == 'w' else -1
            for dx in (-1, 1):
                nx, ny = x + dx, y + diry
                if in_bounds(nx, ny) and nx == tx and ny == ty:
                    return True
        elif p == 'N':
            for dx, dy in ((1,2),(2,1),(2,-1),(1,-2),(-1,-2),(-2,-1),(-2,1),(-1,2)):
                nx, ny = x+dx, y+dy
                if in_bounds(nx, ny) and nx == tx and ny == ty:
                    return True
        elif p in ('B','R','Q'):
            dirs = []
            if p in ('B','Q'):
                dirs += [(1,1),(1,-1),(-1,1),(-1,-1)]
            if p in ('R','Q'):
                dirs += [(1,0),(-1,0),(0,1),(0,-1)]
            for dx,dy in dirs:
                nx, ny = x+dx, y+dy
                while in_bounds(nx,ny):
                    if nx == tx and ny == ty:
                        return True
                    if xy_to_sq(nx,ny) in pieces:
                        break
                    nx += dx
                    ny += dy
        elif p == 'K':
            for dx in (-1,0,1):
                for dy in (-1,0,1):
                    if dx==0 and dy==0: 
                        continue
                    nx, ny = x+dx, y+dy
                    if in_bounds(nx,ny) and nx==tx and ny==ty:
                        return True
    return False

def generate_pseudo_moves(pieces, color):
    moves = []
    enemy = opposite(color)

    for sq, pc in pieces.items():
        if pc[0] != color:
            continue
        p = pc[1]
        x, y = sq_to_xy(sq)

        if p == 'P':
            diry = 1 if color == 'w' else -1
            start_rank = 1 if color == 'w' else 6
            promote_rank = 7 if color == 'w' else 0

            # forward
            nx, ny = x, y + diry
            if in_bounds(nx, ny):
                nsq = xy_to_sq(nx, ny)
                if nsq not in pieces:
                    if ny == promote_rank:
                        for promo in 'qrbn':
                            moves.append(f"{sq}{nsq}{promo}")
                    else:
                        moves.append(f"{sq}{nsq}")
                    # double
                    if y == start_rank:
                        nx2, ny2 = x, y + 2*diry
                        nsq2 = xy_to_sq(nx2, ny2)
                        if nsq2 not in pieces:
                            moves.append(f"{sq}{nsq2}")

            # captures
            for dx in (-1, 1):
                cx, cy = x+dx, y+diry
                if in_bounds(cx, cy):
                    tsq = xy_to_sq(cx, cy)
                    if tsq in pieces and pieces[tsq][0] == enemy:
                        if cy == promote_rank:
                            for promo in 'qrbn':
                                moves.append(f"{sq}{tsq}{promo}")
                        else:
                            moves.append(f"{sq}{tsq}")

        elif p == 'N':
            for dx, dy in ((1,2),(2,1),(2,-1),(1,-2),(-1,-2),(-2,-1),(-2,1),(-1,2)):
                nx, ny = x+dx, y+dy
                if not in_bounds(nx,ny): 
                    continue
                tsq = xy_to_sq(nx, ny)
                if tsq not in pieces or pieces[tsq][0] == enemy:
                    moves.append(f"{sq}{tsq}")

        elif p in ('B','R','Q'):
            dirs = []
            if p in ('B','Q'):
                dirs += [(1,1),(1,-1),(-1,1),(-1,-1)]
            if p in ('R','Q'):
                dirs += [(1,0),(-1,0),(0,1),(0,-1)]
            for dx,dy in dirs:
                nx, ny = x+dx, y+dy
                while in_bounds(nx,ny):
                    tsq = xy_to_sq(nx, ny)
                    if tsq in pieces:
                        if pieces[tsq][0] == enemy:
                            moves.append(f"{sq}{tsq}")
                        break
                    moves.append(f"{sq}{tsq}")
                    nx += dx
                    ny += dy

        elif p == 'K':
            for dx in (-1,0,1):
                for dy in (-1,0,1):
                    if dx==0 and dy==0: 
                        continue
                    nx, ny = x+dx, y+dy
                    if not in_bounds(nx,ny): 
                        continue
                    tsq = xy_to_sq(nx, ny)
                    if tsq not in pieces or pieces[tsq][0] == enemy:
                        moves.append(f"{sq}{tsq}")

            # Note: we omit castling generation because state doesn't include rook/rights history.
            # Arena typically provides legal_moves; but we generate ourselves and also will filter by legality with check.
            # Castling could be legal without rights tracking; to avoid illegal moves, we don't generate castling.
        else:
            pass

    return moves

def apply_move(pieces, move, color):
    # Returns new pieces dict after move; move may be promotion with length 5 or 6? In examples: 'a2a1q' length 5.
    # UCI here: fromsq(2) to sq(2) + optional promo(1)
    frm = move[0:2]
    to = move[2:4]
    promo = move[4] if len(move) == 5 else None

    newp = dict(pieces)
    moving = newp.pop(frm)
    # capture if any
    if to in newp:
        newp.pop(to)
    if promo:
        newp[to] = color + promo.upper()
    else:
        newp[to] = moving
    return newp

def legal_moves(pieces, color):
    # generate pseudo and filter by king safety
    enemy = opposite(color)
    king_sq = king_square(pieces, color)
    if king_sq is None:
        return []
    ps = generate_pseudo_moves(pieces, color)
    leg = []
    for mv in ps:
        newp = apply_move(pieces, mv, color)
        ksq2 = king_square(newp, color)
        if ksq2 is None:
            continue
        if not is_attacked(newp, enemy, ksq2):
            leg.append(mv)
    return leg

def material_score(pieces):
    s = 0
    for pc in pieces.values():
        color = pc[0]
        p = pc[1]
        v = PIECE_VALUES.get(p, 0)
        s += v if color == 'w' else -v
    return s

def pst_bonus(pieces):
    bonus = 0
    for sq, pc in pieces.items():
        color = pc[0]
        p = pc[1]
        if p in PST:
            x,y = sq_to_xy(sq)
            # flip for black
            if color == 'w':
                yy = y
            else:
                yy = 7 - y
            val = PST[p][yy][x]
            bonus += val if color == 'w' else -val
    return bonus

def king_safety(pieces, color):
    # small heuristic: penalize being attacked by enemy near king
    ksq = king_square(pieces, color)
    if not ksq:
        return -10**9
    enemy = opposite(color)
    if is_attacked(pieces, enemy, ksq):
        return -800
    # also count attacked adjacent squares
    x,y = sq_to_xy(ksq)
    attacked = 0
    for dx in (-1,0,1):
        for dy in (-1,0,1):
            if dx==0 and dy==0: 
                continue
            nx, ny = x+dx, y+dy
            if in_bounds(nx,ny):
                tsq = xy_to_sq(nx,ny)
                if is_attacked(pieces, enemy, tsq):
                    attacked += 1
    return -attacked * 40

def move_score(pieces, to_play, mv):
    enemy = opposite(to_play)
    frm = mv[0:2]
    to = mv[2:4]
    promo = mv[4] if len(mv) == 5 else None
    moving_piece = pieces[frm]
    p = moving_piece[1]
    captured = pieces[to][1] if to in pieces and pieces[to][0] == enemy else None
    score = 0

    newp = apply_move(pieces, mv, to_play)

    # Check / mate bonus
    enemy_king = king_square(newp, enemy)
    if enemy_king:
        if is_attacked(newp, to_play, enemy_king):
            score += 2000
            # crude mate check: if enemy has no legal moves and is in check
            if not legal_moves(newp, enemy):
                score += 100000

    # Captures
    if captured:
        score += 400 + (PIECE_VALUES[captured] * 2 - PIECE_VALUES[p])

    # Promotion
    if promo:
        score += 800 + PIECE_VALUES[promo.upper()]

    # Avoid self-exposure already filtered by legality, but add small penalty if move puts king in attack (redundant)
    # Positional PST
    if p in PST:
        x,y = sq_to_xy(to)
        yy = y if to_play == 'w' else 7-y
        score += PST[p][yy][x] * (1 if to_play=='w' else -1) * 0.1  # scale down

    # King safety heuristic
    score += king_safety(newp, to_play) * 0.05

    # Mild preference for center
    cx, cy = sq_to_xy(to)
    dist = abs(cx-3.5)+abs(cy-3.5)
    score += max(0, 120 - int(dist*40)) * 0.5

    # Slight randomness to break ties deterministically-ish
    score += random.random() * 1e-3
    return score

def policy(pieces: dict[str, str], to_play: str) -> str:
    color = 'w' if to_play == 'white' else 'b'
    legal = legal_moves(pieces, color)
    if not legal:
        # No legal moves; return any (but ideally shouldn't happen). Fallback: empty string illegal.
        # We'll return a move that might be legal by assumption; but safer to pick first pseudo.
        ps = generate_pseudo_moves(pieces, color)
        return ps[0] if ps else ""
    # Choose best by scoring
    best_mv = None
    best_sc = -10**18
    for mv in legal:
        sc = move_score(pieces, color, mv)
        if sc > best_sc:
            best_sc = sc
            best_mv = mv
    return best_mv
