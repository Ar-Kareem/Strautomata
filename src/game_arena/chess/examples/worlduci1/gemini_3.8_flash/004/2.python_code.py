
import sys

# Piece values
PIECE_VALS = {
    'P': 100,
    'N': 320,
    'B': 330,
    'R': 500,
    'Q': 900,
    'K': 20000
}

# Positional heatmaps (from White's perspective; indexed by rank 0..7 and file 0..7)
CENTER_BONUS = [
    [ 0,  0,  0,  0,  0,  0,  0,  0],
    [ 5, 10, 10, 10, 10, 10, 10,  5],
    [-5,  5, 15, 20, 20, 15,  5, -5],
    [-5,  5, 20, 30, 30, 20,  5, -5],
    [-5,  5, 20, 30, 30, 20,  5, -5],
    [-5,  5, 15, 20, 20, 15,  5, -5],
    [ 5, 10, 10, 10, 10, 10, 10,  5],
    [ 0,  0,  0,  0,  0,  0,  0,  0],
]

PAWN_BONUS_W = [
    [ 0,  0,  0,  0,  0,  0,  0,  0],
    [ 5, 10, 10,-20,-20, 10, 10,  5],
    [ 5, -5,-10,  0,  0,-10, -5,  5],
    [ 0,  0,  0, 25, 25,  0,  0,  0],
    [ 5,  5, 10, 30, 30, 10,  5,  5],
    [10, 10, 20, 35, 35, 20, 10, 10],
    [50, 50, 50, 50, 50, 50, 50, 50],
    [ 0,  0,  0,  0,  0,  0,  0,  0],
]

def sq_to_coords(sq: str):
    return ord(sq[0]) - ord('a'), int(sq[1]) - 1

def coords_to_sq(f: int, r: int):
    return chr(ord('a') + f) + str(r + 1)

def apply_move(board: dict[str, str], move: str) -> dict[str, str]:
    new_b = dict(board)
    from_sq, to_sq = move[:2], move[2:4]
    promo = move[4].upper() if len(move) > 4 else None
    
    piece = new_b.pop(from_sq, None)
    if not piece:
        return new_b
    color, ptype = piece[0], piece[1]
    
    # Castling rook movement
    if ptype == 'K':
        if from_sq == 'e1' and to_sq == 'g1':
            r = new_b.pop('h1', None)
            if r: new_b['f1'] = r
        elif from_sq == 'e1' and to_sq == 'c1':
            r = new_b.pop('a1', None)
            if r: new_b['d1'] = r
        elif from_sq == 'e8' and to_sq == 'g8':
            r = new_b.pop('h8', None)
            if r: new_b['f8'] = r
        elif from_sq == 'e8' and to_sq == 'c8':
            r = new_b.pop('a8', None)
            if r: new_b['d8'] = r
    # En passant capture
    elif ptype == 'P':
        if from_sq[0] != to_sq[0] and to_sq not in board:
            new_b.pop(to_sq[0] + from_sq[1], None)

    if promo:
        piece = color + promo
    new_b[to_sq] = piece
    return new_b

def generate_pseudo_legal_moves(board: dict[str, str], color: str) -> list[str]:
    moves = []
    f_dir = 1 if color == 'w' else -1
    start_rank = 1 if color == 'w' else 6
    promo_rank = 7 if color == 'w' else 0

    for sq, p in list(board.items()):
        if p[0] != color:
            continue
        f, r = sq_to_coords(sq)
        pt = p[1]

        if pt == 'P':
            # Single push
            nr = r + f_dir
            if 0 <= nr <= 7:
                nsq = coords_to_sq(f, nr)
                if nsq not in board:
                    if nr == promo_rank:
                        for pr in ['q', 'r', 'b', 'n']:
                            moves.append(sq + nsq + pr)
                    else:
                        moves.append(sq + nsq)
                        # Double push
                        if r == start_rank:
                            nnr = r + 2 * f_dir
                            nnsq = coords_to_sq(f, nnr)
                            if nnsq not in board:
                                moves.append(sq + nnsq)
            # Captures
            for df in (-1, 1):
                nf = f + df
                nr = r + f_dir
                if 0 <= nf <= 7 and 0 <= nr <= 7:
                    csq = coords_to_sq(nf, nr)
                    if csq in board and board[csq][0] != color:
                        if nr == promo_rank:
                            for pr in ['q', 'r', 'b', 'n']:
                                moves.append(sq + csq + pr)
                        else:
                            moves.append(sq + csq)

        elif pt == 'N':
            for df, dr in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
                nf, nr = f + df, r + dr
                if 0 <= nf <= 7 and 0 <= nr <= 7:
                    tsq = coords_to_sq(nf, nr)
                    if tsq not in board or board[tsq][0] != color:
                        moves.append(sq + tsq)

        elif pt in ('B', 'R', 'Q'):
            directions = []
            if pt in ('B', 'Q'):
                directions += [(-1,-1), (-1,1), (1,-1), (1,1)]
            if pt in ('R', 'Q'):
                directions += [(-1,0), (1,0), (0,-1), (0,1)]
            for df, dr in directions:
                cf, cr = f + df, r + dr
                while 0 <= cf <= 7 and 0 <= cr <= 7:
                    tsq = coords_to_sq(cf, cr)
                    if tsq not in board:
                        moves.append(sq + tsq)
                    else:
                        if board[tsq][0] != color:
                            moves.append(sq + tsq)
                        break
                    cf += df
                    cr += dr

        elif pt == 'K':
            for df in (-1, 0, 1):
                for dr in (-1, 0, 1):
                    if df == 0 and dr == 0:
                        continue
                    nf, nr = f + df, r + dr
                    if 0 <= nf <= 7 and 0 <= nr <= 7:
                        tsq = coords_to_sq(nf, nr)
                        if tsq not in board or board[tsq][0] != color:
                            moves.append(sq + tsq)

    return moves

def is_king_in_check(board: dict[str, str], color: str) -> bool:
    target_k = color + 'K'
    k_sq = None
    for sq, p in board.items():
        if p == target_k:
            k_sq = sq
            break
    if not k_sq:
        return True
    opp_color = 'b' if color == 'w' else 'w'
    opp_moves = generate_pseudo_legal_moves(board, opp_color)
    for m in opp_moves:
        if m[2:4] == k_sq:
            return True
    return False

def get_strictly_legal_moves(board: dict[str, str], color: str) -> list[str]:
    pseudo = generate_pseudo_legal_moves(board, color)
    legal = []
    for m in pseudo:
        nb = apply_move(board, m)
        if not is_king_in_check(nb, color):
            legal.append(m)
    return legal

def evaluate_board(board: dict[str, str], my_color: str) -> float:
    score = 0.0
    for sq, p in board.items():
        c, pt = p[0], p[1]
        val = PIECE_VALS.get(pt, 0)
        f, r = sq_to_coords(sq)
        
        # Positional bonuses
        pos_val = 0
        if pt == 'P':
            pos_val = PAWN_BONUS_W[r][f] if c == 'w' else PAWN_BONUS_W[7 - r][f]
        elif pt in ('N', 'B'):
            pos_val = CENTER_BONUS[r][f]

        total = val + pos_val
        if c == my_color:
            score += total
        else:
            score -= total
    return score

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str] = None, *args, **kwargs) -> str:
    my_color = 'w' if (to_play.lower() in ('white', 'w')) else 'b'
    opp_color = 'b' if my_color == 'w' else 'w'

    if legal_moves is None:
        legal_moves = kwargs.get('legal_moves', None)

    if not legal_moves:
        legal_moves = get_strictly_legal_moves(pieces, my_color)

    if not legal_moves:
        # Ultimate fallback
        return 'e2e4'

    best_move = legal_moves[0]
    best_score = -1e9

    for m in legal_moves:
        b1 = apply_move(pieces, m)
        
        # Quick checkmate or opponent king elimination check
        opp_k = opp_color + 'K'
        if opp_k not in b1.values():
            return m

        opp_moves = generate_pseudo_legal_moves(b1, opp_color)
        
        # Minimize opponent's best score
        min_opp_eval = 1e9
        # Filter pseudo moves to plausible captures/responses for efficiency
        opp_moves.sort(key=lambda mv: 1 if mv[2:4] in b1 else 0, reverse=True)
        eval_sample = opp_moves[:20] if len(opp_moves) > 20 else opp_moves

        if not eval_sample:
            # Opponent has no moves
            score = 100000.0
        else:
            for om in eval_sample:
                b2 = apply_move(b1, om)
                ev = evaluate_board(b2, my_color)
                if ev < min_opp_eval:
                    min_opp_eval = ev
            score = min_opp_eval

        # Tie-breaker preferences: Queen promotions & central control
        if len(m) > 4 and m[4] == 'q':
            score += 500
        dest = m[2:4]
        if dest in ('d4', 'd5', 'e4', 'e5'):
            score += 15

        if score > best_score:
            best_score = score
            best_move = m

    return best_move
