
import random

# Precompute all squares
FILES = "abcdefgh"
RANKS = "12345678"
ALL_SQUARES = [f + r for r in RANKS for f in FILES]

PIECE_VALUES = {
    'P': 100,
    'N': 320,
    'B': 330,
    'R': 500,
    'Q': 900,
    'K': 0
}

MATE_VALUE = 100000

def policy(pieces: dict[str, str], to_play: str, memory: dict) -> tuple[str, dict]:
    color = 'w' if to_play == 'white' else 'b'
    opp = 'b' if color == 'w' else 'w'

    if memory is None:
        memory = {}

    # Initialize castling rights if not present
    if 'castling' not in memory:
        rights = {
            'wK': pieces.get('e1') == 'wK' and pieces.get('h1') == 'wR',
            'wQ': pieces.get('e1') == 'wK' and pieces.get('a1') == 'wR',
            'bK': pieces.get('e8') == 'bK' and pieces.get('h8') == 'bR',
            'bQ': pieces.get('e8') == 'bK' and pieces.get('a8') == 'bR'
        }
    else:
        rights = memory['castling']

    # Infer opponent last move for en passant and castling rights
    ep = None
    if 'prev_pieces' in memory:
        info = infer_move(memory['prev_pieces'], pieces)
        if info:
            move, moved_piece, captured_piece, mover_color, from_sq, to_sq = info
            # update castling rights
            update_rights(rights, moved_piece, from_sq, captured_piece, to_sq)
            # update en passant
            if moved_piece and moved_piece[1] == 'P':
                fr = int(from_sq[1])
                tr = int(to_sq[1])
                if abs(tr - fr) == 2:
                    mid_rank = (fr + tr) // 2
                    ep = from_sq[0] + str(mid_rank)

    state = {'castling': rights, 'ep': ep}

    # Generate legal moves
    legal_moves = generate_legal_moves(pieces, color, state)

    if not legal_moves:
        # No legal moves (checkmate or stalemate), return any move string
        return "0000", memory

    # Search for best move using depth-2 negamax
    best_move = legal_moves[0]
    best_score = -10**9
    for mv in legal_moves:
        b2, s2 = apply_move(pieces, mv, state, color)
        score = -negamax(b2, s2, opp, 1, -MATE_VALUE, MATE_VALUE)
        if score > best_score:
            best_score = score
            best_move = mv

    # Update memory after our move
    new_board, new_state = apply_move(pieces, best_move, state, color)
    memory['prev_pieces'] = new_board
    memory['castling'] = new_state['castling']

    return best_move, memory

def negamax(board, state, color, depth, alpha, beta):
    opp = 'b' if color == 'w' else 'w'
    if depth == 0:
        return evaluate(board, color)

    moves = generate_legal_moves(board, color, state)
    if not moves:
        if is_in_check(board, color):
            return -MATE_VALUE + depth
        else:
            return 0

    best = -10**9
    for mv in moves:
        b2, s2 = apply_move(board, mv, state, color)
        score = -negamax(b2, s2, opp, depth-1, -beta, -alpha)
        if score > best:
            best = score
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break
    return best

def evaluate(board, color):
    score = 0
    for p in board.values():
        val = PIECE_VALUES[p[1]]
        if p[0] == color:
            score += val
        else:
            score -= val
    if is_in_check(board, 'b' if color == 'w' else 'w'):
        score += 20
    return score

def generate_legal_moves(board, color, state):
    moves = []
    for sq, piece in board.items():
        if piece[0] != color:
            continue
        ptype = piece[1]
        if ptype == 'P':
            moves.extend(pawn_moves(board, sq, color, state))
        elif ptype == 'N':
            moves.extend(knight_moves(board, sq, color))
        elif ptype == 'B':
            moves.extend(sliding_moves(board, sq, color, [(1,1),(1,-1),(-1,1),(-1,-1)]))
        elif ptype == 'R':
            moves.extend(sliding_moves(board, sq, color, [(1,0),(-1,0),(0,1),(0,-1)]))
        elif ptype == 'Q':
            moves.extend(sliding_moves(board, sq, color, [(1,1),(1,-1),(-1,1),(-1,-1),(1,0),(-1,0),(0,1),(0,-1)]))
        elif ptype == 'K':
            moves.extend(king_moves(board, sq, color, state))
    # filter illegal moves (leaving king in check)
    legal = []
    for mv in moves:
        b2, s2 = apply_move(board, mv, state, color)
        if not is_in_check(b2, color):
            legal.append(mv)
    return legal

def pawn_moves(board, sq, color, state):
    moves = []
    file = FILES.index(sq[0])
    rank = int(sq[1])
    dir = 1 if color == 'w' else -1
    start_rank = 2 if color == 'w' else 7
    promo_rank = 8 if color == 'w' else 1

    # forward
    one_rank = rank + dir
    if 1 <= one_rank <= 8:
        one_sq = FILES[file] + str(one_rank)
        if one_sq not in board:
            if one_rank == promo_rank:
                for prom in "qrbn":
                    moves.append(sq + one_sq + prom)
            else:
                moves.append(sq + one_sq)
            # double
            if rank == start_rank:
                two_rank = rank + 2*dir
                two_sq = FILES[file] + str(two_rank)
                if two_sq not in board:
                    moves.append(sq + two_sq)
    # captures
    for dx in [-1, 1]:
        f = file + dx
        if 0 <= f < 8:
            cap_rank = rank + dir
            if 1 <= cap_rank <= 8:
                cap_sq = FILES[f] + str(cap_rank)
                if cap_sq in board and board[cap_sq][0] != color:
                    if cap_rank == promo_rank:
                        for prom in "qrbn":
                            moves.append(sq + cap_sq + prom)
                    else:
                        moves.append(sq + cap_sq)
                # en passant
                if state.get('ep') == cap_sq:
                    moves.append(sq + cap_sq)
    return moves

def knight_moves(board, sq, color):
    moves = []
    f = FILES.index(sq[0])
    r = int(sq[1])
    for df, dr in [(1,2),(2,1),(-1,2),(-2,1),(1,-2),(2,-1),(-1,-2),(-2,-1)]:
        nf = f + df
        nr = r + dr
        if 0 <= nf < 8 and 1 <= nr <= 8:
            nsq = FILES[nf] + str(nr)
            if nsq not in board or board[nsq][0] != color:
                moves.append(sq + nsq)
    return moves

def sliding_moves(board, sq, color, directions):
    moves = []
    f = FILES.index(sq[0])
    r = int(sq[1])
    for df, dr in directions:
        nf, nr = f + df, r + dr
        while 0 <= nf < 8 and 1 <= nr <= 8:
            nsq = FILES[nf] + str(nr)
            if nsq in board:
                if board[nsq][0] != color:
                    moves.append(sq + nsq)
                break
            else:
                moves.append(sq + nsq)
            nf += df
            nr += dr
    return moves

def king_moves(board, sq, color, state):
    moves = []
    f = FILES.index(sq[0])
    r = int(sq[1])
    for df in [-1,0,1]:
        for dr in [-1,0,1]:
            if df == 0 and dr == 0:
                continue
            nf, nr = f + df, r + dr
            if 0 <= nf < 8 and 1 <= nr <= 8:
                nsq = FILES[nf] + str(nr)
                if nsq not in board or board[nsq][0] != color:
                    moves.append(sq + nsq)

    # Castling
    if not is_in_check(board, color):
        if color == 'w':
            if state['castling'].get('wK'):
                if ('f1' not in board) and ('g1' not in board):
                    if not is_square_attacked(board, 'f1', 'b') and not is_square_attacked(board, 'g1', 'b'):
                        moves.append('e1g1')
            if state['castling'].get('wQ'):
                if ('d1' not in board) and ('c1' not in board) and ('b1' not in board):
                    if not is_square_attacked(board, 'd1', 'b') and not is_square_attacked(board, 'c1', 'b'):
                        moves.append('e1c1')
        else:
            if state['castling'].get('bK'):
                if ('f8' not in board) and ('g8' not in board):
                    if not is_square_attacked(board, 'f8', 'w') and not is_square_attacked(board, 'g8', 'w'):
                        moves.append('e8g8')
            if state['castling'].get('bQ'):
                if ('d8' not in board) and ('c8' not in board) and ('b8' not in board):
                    if not is_square_attacked(board, 'd8', 'w') and not is_square_attacked(board, 'c8', 'w'):
                        moves.append('e8c8')
    return moves

def apply_move(board, move, state, color):
    new_board = dict(board)
    from_sq = move[:2]
    to_sq = move[2:4]
    promo = move[4] if len(move) > 4 else None
    orig_piece = new_board[from_sq]
    del new_board[from_sq]
    captured_piece = new_board.get(to_sq)

    # en passant
    if orig_piece[1] == 'P' and state.get('ep') == to_sq and captured_piece is None and from_sq[0] != to_sq[0]:
        if color == 'w':
            cap_sq = to_sq[0] + str(int(to_sq[1]) - 1)
        else:
            cap_sq = to_sq[0] + str(int(to_sq[1]) + 1)
        captured_piece = new_board.pop(cap_sq, None)

    # castling
    if orig_piece[1] == 'K' and abs(FILES.index(to_sq[0]) - FILES.index(from_sq[0])) == 2:
        if to_sq[0] == 'g':
            rook_from = 'h' + from_sq[1]
            rook_to = 'f' + from_sq[1]
        else:
            rook_from = 'a' + from_sq[1]
            rook_to = 'd' + from_sq[1]
        rook_piece = new_board.pop(rook_from, None)
        if rook_piece:
            new_board[rook_to] = rook_piece

    # promotion
    new_piece = orig_piece
    if promo:
        new_piece = orig_piece[0] + promo.upper()
    new_board[to_sq] = new_piece

    # update castling rights
    new_rights = state['castling'].copy()
    update_rights(new_rights, orig_piece, from_sq, captured_piece, to_sq)

    # update en passant
    new_ep = None
    if orig_piece[1] == 'P' and abs(int(to_sq[1]) - int(from_sq[1])) == 2:
        mid_rank = (int(to_sq[1]) + int(from_sq[1])) // 2
        new_ep = from_sq[0] + str(mid_rank)

    return new_board, {'castling': new_rights, 'ep': new_ep}

def update_rights(rights, moved_piece, from_sq, captured_piece, to_sq):
    if moved_piece:
        if moved_piece[1] == 'K':
            if moved_piece[0] == 'w':
                rights['wK'] = False
                rights['wQ'] = False
            else:
                rights['bK'] = False
                rights['bQ'] = False
        if moved_piece[1] == 'R':
            if from_sq == 'h1': rights['wK'] = False
            if from_sq == 'a1': rights['wQ'] = False
            if from_sq == 'h8': rights['bK'] = False
            if from_sq == 'a8': rights['bQ'] = False
    if captured_piece and captured_piece[1] == 'R':
        if to_sq == 'h1': rights['wK'] = False
        if to_sq == 'a1': rights['wQ'] = False
        if to_sq == 'h8': rights['bK'] = False
        if to_sq == 'a8': rights['bQ'] = False

def is_in_check(board, color):
    king_sq = None
    for sq, p in board.items():
        if p == color + 'K':
            king_sq = sq
            break
    if not king_sq:
        return True
    opp = 'b' if color == 'w' else 'w'
    return is_square_attacked(board, king_sq, opp)

def is_square_attacked(board, sq, by_color):
    f = FILES.index(sq[0])
    r = int(sq[1])

    # pawns
    dir = 1 if by_color == 'w' else -1
    for df in [-1, 1]:
        nf, nr = f + df, r - dir
        if 0 <= nf < 8 and 1 <= nr <= 8:
            nsq = FILES[nf] + str(nr)
            if board.get(nsq) == by_color + 'P':
                return True

    # knights
    for df, dr in [(1,2),(2,1),(-1,2),(-2,1),(1,-2),(2,-1),(-1,-2),(-2,-1)]:
        nf, nr = f + df, r + dr
        if 0 <= nf < 8 and 1 <= nr <= 8:
            nsq = FILES[nf] + str(nr)
            if board.get(nsq) == by_color + 'N':
                return True

    # bishops/queens
    for df, dr in [(1,1),(1,-1),(-1,1),(-1,-1)]:
        nf, nr = f + df, r + dr
        while 0 <= nf < 8 and 1 <= nr <= 8:
            nsq = FILES[nf] + str(nr)
            if nsq in board:
                if board[nsq][0] == by_color and board[nsq][1] in ('B','Q'):
                    return True
                break
            nf += df
            nr += dr

    # rooks/queens
    for df, dr in [(1,0),(-1,0),(0,1),(0,-1)]:
        nf, nr = f + df, r + dr
        while 0 <= nf < 8 and 1 <= nr <= 8:
            nsq = FILES[nf] + str(nr)
            if nsq in board:
                if board[nsq][0] == by_color and board[nsq][1] in ('R','Q'):
                    return True
                break
            nf += df
            nr += dr

    # king
    for df in [-1,0,1]:
        for dr in [-1,0,1]:
            if df == 0 and dr == 0:
                continue
            nf, nr = f + df, r + dr
            if 0 <= nf < 8 and 1 <= nr <= 8:
                nsq = FILES[nf] + str(nr)
                if board.get(nsq) == by_color + 'K':
                    return True
    return False

def infer_move(prev, curr):
    diff = [sq for sq in ALL_SQUARES if prev.get(sq) != curr.get(sq)]
    if not diff:
        return None
    to_squares = [sq for sq in diff if curr.get(sq) and curr.get(sq) != prev.get(sq)]
    from_squares = [sq for sq in diff if prev.get(sq) and prev.get(sq) != curr.get(sq)]

    mover_color = curr[to_squares[0]][0] if to_squares else prev[from_squares[0]][0]

    # Castling
    king_from = None
    king_to = None
    for fs in from_squares:
        if prev[fs][0] == mover_color and prev[fs][1] == 'K':
            king_from = fs
    if king_from:
        for ts in to_squares:
            if curr.get(ts) and curr[ts][0] == mover_color and curr[ts][1] == 'K':
                king_to = ts
        if king_to:
            move = king_from + king_to
            return move, prev[king_from], None, mover_color, king_from, king_to

    from_sq = None
    to_sq = None
    for fs in from_squares:
        if prev[fs][0] == mover_color:
            from_sq = fs
            break
    for ts in to_squares:
        if curr[ts][0] == mover_color:
            to_sq = ts
            break
    if not from_sq or not to_sq:
        return None

    moved_piece = prev[from_sq]
    captured_piece = prev.get(to_sq)
    # en passant capture
    if moved_piece[1] == 'P' and captured_piece is None and from_sq[0] != to_sq[0]:
        cap_sq = to_sq[0] + from_sq[1]
        captured_piece = prev.get(cap_sq)

    promo = ''
    if moved_piece[1] == 'P' and curr[to_sq][1] != 'P':
        promo = curr[to_sq][1].lower()

    move = from_sq + to_sq + promo
    return move, moved_piece, captured_piece, mover_color, from_sq, to_sq
