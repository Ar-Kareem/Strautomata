
# Chess move selection policy
# Implements def policy(pieces: dict[str,str], to_play: str, memory: dict) -> tuple[str, dict]
# - Generates legal moves (pseudolegal then filters out moves that leave king in check)
# - Supports pawn promotions, en-passant detection from memory, and castling when inferable
# - Evaluates leaf positions with simple material + check/mate heuristic and selects best move

from copy import deepcopy
import random

FILES = "abcdefgh"
RANKS = "12345678"
PIECE_VALUES = {'K': 0, 'Q': 900, 'R': 500, 'B': 330, 'N': 320, 'P': 100}

# Helpers to convert between coords and squares
def sq_to_xy(sq):
    return FILES.index(sq[0]), RANKS.index(sq[1])

def xy_to_sq(x, y):
    return FILES[x] + RANKS[y]

def on_board(x, y):
    return 0 <= x < 8 and 0 <= y < 8

def board_from_pieces(pieces):
    board = [[None for _ in range(8)] for __ in range(8)]
    for sq, pc in pieces.items():
        x, y = sq_to_xy(sq)
        board[y][x] = pc
    return board

def pieces_from_board(board):
    pieces = {}
    for y in range(8):
        for x in range(8):
            pc = board[y][x]
            if pc:
                pieces[xy_to_sq(x,y)] = pc
    return pieces

def find_king(board, color):
    target = color + 'K'
    for y in range(8):
        for x in range(8):
            if board[y][x] == target:
                return x, y
    return None

# Attack detection: is square (x,y) attacked by pieces of color 'w' or 'b'?
def is_attacked(board, x, y, by_color):
    # Pawn attacks
    if by_color == 'w':
        for dx in (-1, 1):
            ax, ay = x + dx, y - 1  # white pawns attack upwards in our orientation? careful: ranks index 0='1', white moves +1
            # Note: our board indexing has y=0 -> rank '1', white moves +1 (increase y). So white pawns attack from y-1? Let's reason:
            # A white pawn on rank r attacks squares at r+1 (higher y). So to see if square (x,y) is attacked by a white pawn,
            # check for a white pawn at (x+dx, y-1)? No: If white pawn at (px,py) attacks (x,y) then (py+1 == y) => py = y-1.
            # So white pawn would be at y-1. So pawn attack check for white is (x+dx, y-1).
            if on_board(ax, ay) and board[ay][ax] == 'wP':
                return True
    else:
        for dx in (-1, 1):
            ax, ay = x + dx, y + 1
            # Black pawn at (px,py) attacks (x,y) if py-1 == y => black pawn at y+1
            if on_board(ax, ay) and board[ay][ax] == 'bP':
                return True

    # Knights
    for dx, dy in [(1,2),(2,1),(2,-1),(1,-2),(-1,-2),(-2,-1),(-2,1),(-1,2)]:
        ax, ay = x+dx, y+dy
        if on_board(ax, ay):
            pc = board[ay][ax]
            if pc and pc[0] == by_color and pc[1] == 'N':
                return True

    # King adjacency
    for dx in (-1,0,1):
        for dy in (-1,0,1):
            if dx==0 and dy==0: continue
            ax, ay = x+dx, y+dy
            if on_board(ax, ay):
                pc = board[ay][ax]
                if pc and pc[0] == by_color and pc[1] == 'K':
                    return True

    # Sliding attacks: rook/queen for orthogonals, bishop/queen for diagonals
    # Directions
    for dx, dy, attackers in [
        (1,0,('R','Q')), (-1,0,('R','Q')), (0,1,('R','Q')), (0,-1,('R','Q')),
        (1,1,('B','Q')), (1,-1,('B','Q')), (-1,1,('B','Q')), (-1,-1,('B','Q'))
    ]:
        ax, ay = x+dx, y+dy
        while on_board(ax, ay):
            pc = board[ay][ax]
            if pc:
                if pc[0] == by_color and pc[1] in attackers:
                    return True
                break
            ax += dx; ay += dy
    return False

def generate_legal_moves(pieces, to_play, memory):
    board = board_from_pieces(pieces)
    color = 'w' if to_play == 'white' else 'b'
    opp = 'b' if color == 'w' else 'w'
    en_passant_target = None

    # detect last move from memory to enable en-passant
    last_pieces = memory.get('last_pieces')
    if last_pieces:
        # find move squares by comparing last and current piece maps
        # find piece that moved to a new square (present in current but absent or different in last)
        moved_from = None
        moved_to = None
        # create reverse mapping of pieces with identity by position
        # We attempt to detect a single piece move
        last_sq_set = set(last_pieces.keys())
        cur_sq_set = set(pieces.keys())
        added = cur_sq_set - last_sq_set
        removed = last_sq_set - cur_sq_set
        # also detect if a piece changed square (same piece type)
        # find candidate moved squares by matching piece types
        # fallback: if exactly one removed and one added, that's likely last move
        if len(added) == 1 and len(removed) == 1:
            moved_to = list(added)[0]
            moved_from = list(removed)[0]
        else:
            # more complex: try to find a pawn that moved two squares
            for sq_from, pc in last_pieces.items():
                # find if this piece exists elsewhere in current
                found = None
                for sq_to, pc2 in pieces.items():
                    if pc == pc2 and sq_to != sq_from and sq_to not in last_pieces:
                        found = sq_to
                        break
                if found:
                    moved_from = sq_from
                    moved_to = found
                    break
        if moved_from and moved_to:
            pc = last_pieces.get(moved_from)
            if pc and pc[1] == 'P' and pc[0] != color:
                # opponent pawn moved; check if moved two squares
                fx, fy = sq_to_xy(moved_from)
                tx, ty = sq_to_xy(moved_to)
                if abs(ty - fy) == 2:
                    # en-passant target square is the square passed over
                    mid_y = (fy + ty) // 2
                    en_passant_target = (tx, mid_y)

    # generate pseudo-legal moves
    moves = []  # each move: (from_x,from_y,to_x,to_y,prom)
    king_pos = find_king(board, color)
    if not king_pos:
        # no king found; return no moves
        return [], memory
    kx0, ky0 = king_pos

    # Helper to add move and later filter legality
    def add_move(fx, fy, tx, ty, prom=None, special=None):
        moves.append((fx,fy,tx,ty,prom,special))

    # iterate pieces
    for y in range(8):
        for x in range(8):
            pc = board[y][x]
            if not pc or pc[0] != color:
                continue
            ptype = pc[1]
            if ptype == 'P':
                diry = 1 if color == 'w' else -1
                start_rank = 1 if color == 'w' else 6
                # one forward
                ny = y + diry
                if on_board(x, ny) and board[ny][x] is None:
                    # promotion?
                    if ny == 7 if color == 'w' else ny == 0:
                        for prom in ['q','r','b','n']:
                            add_move(x,y,x,ny,prom)
                    else:
                        add_move(x,y,x,ny,None)
                        # two squares
                        if y == start_rank:
                            ny2 = y + 2*diry
                            if on_board(x, ny2) and board[ny2][x] is None:
                                add_move(x,y,x,ny2,None)
                # captures
                for dx in (-1, 1):
                    nx = x + dx
                    ny = y + diry
                    if on_board(nx, ny):
                        target = board[ny][nx]
                        if target and target[0] == opp:
                            if ny == 7 if color == 'w' else ny == 0:
                                for prom in ['q','r','b','n']:
                                    add_move(x,y,nx,ny,prom)
                            else:
                                add_move(x,y,nx,ny,None)
                # en-passant: if en_passant_target exists and our pawn can move to it by capture
                if en_passant_target:
                    ex, ey = en_passant_target
                    if ey == y + diry and abs(ex - x) == 1:
                        # ensure the pawn to be captured is on (ex, y) (the pawn moved two to ex,ey but is actually on ex, y+dir?)
                        cap_x, cap_y = ex, y
                        if on_board(cap_x, cap_y) and board[cap_y][cap_x] and board[cap_y][cap_x][0] == opp and board[cap_y][cap_x][1] == 'P':
                            add_move(x,y,ex,ey,None,'ep')

            elif ptype == 'N':
                for dx,dy in [(1,2),(2,1),(2,-1),(1,-2),(-1,-2),(-2,-1),(-2,1),(-1,2)]:
                    nx, ny = x+dx, y+dy
                    if on_board(nx, ny):
                        tgt = board[ny][nx]
                        if tgt is None or tgt[0] == opp:
                            add_move(x,y,nx,ny,None)
            elif ptype == 'B' or ptype == 'R' or ptype == 'Q':
                directions = []
                if ptype in ('B','Q'):
                    directions += [(1,1),(1,-1),(-1,1),(-1,-1)]
                if ptype in ('R','Q'):
                    directions += [(1,0),(-1,0),(0,1),(0,-1)]
                for dx,dy in directions:
                    nx, ny = x+dx, y+dy
                    while on_board(nx, ny):
                        tgt = board[ny][nx]
                        if tgt is None:
                            add_move(x,y,nx,ny,None)
                        else:
                            if tgt[0] == opp:
                                add_move(x,y,nx,ny,None)
                            break
                        nx += dx; ny += dy
            elif ptype == 'K':
                for dx in (-1,0,1):
                    for dy in (-1,0,1):
                        if dx==0 and dy==0: continue
                        nx, ny = x+dx, y+dy
                        if on_board(nx, ny):
                            tgt = board[ny][nx]
                            if tgt is None or tgt[0] == opp:
                                add_move(x,y,nx,ny,None)
                # Castling: infer rights from memory
                rights = memory.get('castle_rights')
                if rights is None:
                    rights = {'white': {'K': False, 'Q': False}, 'black': {'K': False, 'Q': False}}
                # king must be on original square and not moved; typical original squares e1 (4,0) and e8 (4,7)
                if color == 'w' and x == 4 and y == 0:
                    # king-side
                    if rights.get('white',{}).get('K', False):
                        # squares f1 (5,0) and g1 (6,0) must be empty and not attacked; rook on h1
                        if board[0][5] is None and board[0][6] is None and board[0][7] == 'wR':
                            # king is not in check and squares f1,g1 not attacked
                            if not is_attacked(board,4,0,opp) and not is_attacked(board,5,0,opp) and not is_attacked(board,6,0,opp):
                                add_move(4,0,6,0,None,'castleK')
                    # queen-side
                    if rights.get('white',{}).get('Q', False):
                        # squares d1 (3,0), c1 (2,0), b1 (1,0) between and rook at a1
                        if board[0][3] is None and board[0][2] is None and board[0][1] is None and board[0][0] == 'wR':
                            if not is_attacked(board,4,0,opp) and not is_attacked(board,3,0,opp) and not is_attacked(board,2,0,opp):
                                add_move(4,0,2,0,None,'castleQ')
                if color == 'b' and x == 4 and y == 7:
                    if rights.get('black',{}).get('K', False):
                        if board[7][5] is None and board[7][6] is None and board[7][7] == 'bR':
                            if not is_attacked(board,4,7,opp) and not is_attacked(board,5,7,opp) and not is_attacked(board,6,7,opp):
                                add_move(4,7,6,7,None,'castleK')
                    if rights.get('black',{}).get('Q', False):
                        if board[7][3] is None and board[7][2] is None and board[7][1] is None and board[7][0] == 'bR':
                            if not is_attacked(board,4,7,opp) and not is_attacked(board,3,7,opp) and not is_attacked(board,2,7,opp):
                                add_move(4,7,2,7,None,'castleQ')

    # Filter moves to ensure king not left in check (legal moves)
    legal = []
    for fx,fy,tx,ty,prom,special in moves:
        newb = deepcopy(board)
        moving = newb[fy][fx]
        # apply move
        # en-passant: if special == 'ep', remove pawn behind target
        if special == 'ep':
            # captured pawn is at (tx, fy)
            newb[fy][fx] = None
            newb[fy][tx] = None
            newb[ty][tx] = moving  # place pawn at target
        elif special == 'castleK':
            # king from e to g, rook from h to f
            newb[fy][fx] = None
            newb[ty][tx] = moving
            # rook move
            if color == 'w':
                newb[0][7], newb[0][5] = None, 'wR'
            else:
                newb[7][7], newb[7][5] = None, 'bR'
        elif special == 'castleQ':
            newb[fy][fx] = None
            newb[ty][tx] = moving
            if color == 'w':
                newb[0][0], newb[0][3] = None, 'wR'
            else:
                newb[7][0], newb[7][3] = None, 'bR'
        else:
            # normal move or promotion
            newb[fy][fx] = None
            # promotion
            if prom and moving[1] == 'P' and (ty == 7 or ty == 0):
                newb[ty][tx] = color + prom.upper()
            else:
                newb[ty][tx] = moving

        # Find our king in new position (it could have moved)
        new_king = find_king(newb, color)
        if not new_king:
            # illegal if king missing (captured)
            continue
        nkx, nky = new_king
        # If king is in check by opponent, move is illegal
        if is_attacked(newb, nkx, nky, opp):
            continue
        # Also ensure kings not adjacent (illegal)
        opp_king = find_king(newb, opp)
        if opp_king:
            okx, oky = opp_king
            if abs(okx - nkx) <= 1 and abs(oky - nky) <= 1:
                continue
        legal.append((fx,fy,tx,ty,prom,special))

    return legal, memory

# Simple static evaluation: material + check bonus
def evaluate_board(board, color):
    # positive score favors 'color'
    score = 0
    for y in range(8):
        for x in range(8):
            pc = board[y][x]
            if pc:
                val = PIECE_VALUES.get(pc[1], 0)
                if pc[0] == color:
                    score += val
                else:
                    score -= val
    return score

def apply_move_to_board(board, move):
    fx,fy,tx,ty,prom,special = move
    newb = deepcopy(board)
    moving = newb[fy][fx]
    if special == 'ep':
        newb[fy][fx] = None
        # captured pawn at (tx, fy)
        newb[fy][tx] = None
        newb[ty][tx] = moving
    elif special == 'castleK':
        newb[fy][fx] = None
        newb[ty][tx] = moving
        # rook
        if moving[0] == 'w':
            newb[0][7], newb[0][5] = None, 'wR'
        else:
            newb[7][7], newb[7][5] = None, 'bR'
    elif special == 'castleQ':
        newb[fy][fx] = None
        newb[ty][tx] = moving
        if moving[0] == 'w':
            newb[0][0], newb[0][3] = None, 'wR'
        else:
            newb[7][0], newb[7][3] = None, 'bR'
    else:
        newb[fy][fx] = None
        if prom and moving[1] == 'P' and (ty == 7 or ty == 0):
            newb[ty][tx] = moving[0] + prom.upper()
        else:
            newb[ty][tx] = moving
    return newb

def move_to_ucistr(move):
    fx,fy,tx,ty,prom,special = move
    s = xy_to_sq(fx,fy) + xy_to_sq(tx,ty)
    if prom:
        s += prom
    return s

# Main policy
def policy(pieces: dict, to_play: str, memory: dict):
    # initialize memory structures
    if 'initial_pieces' not in memory:
        memory['initial_pieces'] = dict(pieces)
    if 'last_pieces' not in memory:
        memory['last_pieces'] = dict(pieces)
    if 'castle_rights' not in memory:
        # infer initial rough castling rights from initial position
        rights = {'white': {'K': False, 'Q': False}, 'black': {'K': False, 'Q': False}}
        # white
        if pieces.get('e1') == 'wK' and pieces.get('h1') == 'wR':
            rights['white']['K'] = True
        if pieces.get('e1') == 'wK' and pieces.get('a1') == 'wR':
            rights['white']['Q'] = True
        if pieces.get('e8') == 'bK' and pieces.get('h8') == 'bR':
            rights['black']['K'] = True
        if pieces.get('e8') == 'bK' and pieces.get('a8') == 'bR':
            rights['black']['Q'] = True
        memory['castle_rights'] = rights

    # update castle rights by detecting if king/rook moved since last position
    prev = memory.get('last_pieces', {})
    # for each side, if a king or rook presence changed from prev to current, revoke rights
    for side in ('white','black'):
        color = 'w' if side == 'white' else 'b'
        # King squares
        if side == 'white':
            king_sq = 'e1'; rk_sq = 'h1'; rq_sq = 'a1'
        else:
            king_sq = 'e8'; rk_sq = 'h8'; rq_sq = 'a8'
        # if king was in prev and now absent from same square -> moved
        if prev.get(king_sq) != pieces.get(king_sq):
            memory['castle_rights'][side]['K'] = False
            memory['castle_rights'][side]['Q'] = False
        # if rook moved from king-side square
        if prev.get(rk_sq) != pieces.get(rk_sq):
            memory['castle_rights'][side]['K'] = False
        if prev.get(rq_sq) != pieces.get(rq_sq):
            memory['castle_rights'][side]['Q'] = False

    legal_moves, memory = generate_legal_moves(pieces, to_play, memory)

    # store current pieces as last_pieces for next call
    memory['last_pieces'] = dict(pieces)

    if not legal_moves:
        # No legal moves: return a dummy legal-looking move (should not happen in proper calls)
        # Try to find any pseudo-move (move one king if available)
        # but must return some string; best effort:
        for sq, pc in pieces.items():
            if pc[0] == ('w' if to_play=='white' else 'b') and pc[1] == 'K':
                fx,fy = sq_to_xy(sq)
                for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
                    nx,ny = fx+dx, fy+dy
                    if on_board(nx,ny):
                        s = xy_to_sq(fx,fy)+xy_to_sq(nx,ny)
                        return s, memory
        # fallback arbitrary
        return 'a1a1', memory

    # score each legal move with shallow eval + checks for mate
    board = board_from_pieces(pieces)
    color = 'w' if to_play == 'white' else 'b'
    opp = 'b' if color == 'w' else 'w'

    best_score = -10**9
    best_moves = []
    for mv in legal_moves:
        newb = apply_move_to_board(board, mv)
        # detect opponent king
        opp_king = find_king(newb, opp)
        # check if opponent has any legal moves (for mate detection)
        mate = False
        if opp_king:
            # quick check: if opponent king is under attack and opponent has no legal replies, it's mate
            if is_attacked(newb, opp_king[0], opp_king[1], color):
                # generate opponent legal moves to see if any reply exists
                # build pieces mapping for newb
                new_pieces = pieces_from_board(newb)
                opp_to_play = 'white' if opp == 'w' else 'black'
                opp_legal, _ = generate_legal_moves(new_pieces, opp_to_play, {})  # pass empty memory to avoid altering global
                if not opp_legal:
                    mate = True

        score = 0
        if mate:
            score = 10**7
        else:
            # material evaluation from perspective of 'color'
            score = evaluate_board(newb, color)
            # bonus for giving check
            if opp_king and is_attacked(newb, opp_king[0], opp_king[1], color):
                score += 50
            # small positional randomness to break ties
            score += random.random() * 1e-6

            # prefer captures by material gain: compute captured piece value
            fx,fy,tx,ty,prom,special = mv
            captured = None
            if special == 'ep':
                # captured pawn at (tx, fy)
                cap = board[fy][tx]
                captured = cap
            elif special and special.startswith('castle'):
                captured = None
            else:
                captured = board[ty][tx]
            if captured and captured[0] == opp:
                score += PIECE_VALUES.get(captured[1],0) * 10  # amplify capture importance

            # promotion heuristic
            if prom:
                # promote to queen best
                score += PIECE_VALUES.get('Q',900) * 10

        if score > best_score:
            best_score = score
            best_moves = [mv]
        elif score == best_score:
            best_moves.append(mv)

    chosen = random.choice(best_moves)
    move_str = move_to_ucistr(chosen)
    return move_str, memory

# expose policy at module level
# The following line ensures functions are available when module is imported.
if __name__ == "__main__":
    # simple self-test on starting position
    start_pieces = {}
    # set up basic starting pieces quickly for test
    for i, f in enumerate(FILES):
        start_pieces[f+'2'] = 'wP'
        start_pieces[f+'7'] = 'bP'
    start_pieces.update({'a1':'wR','h1':'wR','b1':'wN','g1':'wN','c1':'wB','f1':'wB','d1':'wQ','e1':'wK'})
    start_pieces.update({'a8':'bR','h8':'bR','b8':'bN','g8':'bN','c8':'bB','f8':'bB','d8':'bQ','e8':'bK'})
    mv, mem = policy(start_pieces, 'white', {})
    print("Sample move:", mv)
