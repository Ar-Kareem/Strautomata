
import time

# ----------------------------------------------------------------------
# Constants and tables
# ----------------------------------------------------------------------
piece_value = {
    'P': 100,
    'N': 320,
    'B': 330,
    'R': 500,
    'Q': 900,
    'K': 20000
}

# Piece‑square tables (from white’s perspective)
pawntable = [
    [0,  0,  0,  0,  0,  0,  0,  0],
    [50, 50, 50, 50, 50, 50, 50, 50],
    [10, 10, 20, 30, 30, 20, 10, 10],
    [5,  5, 10, 25, 25, 10,  5,  5],
    [0,  0,  0, 20, 20,  0,  0,  0],
    [5, -5,-10,  0,  0,-10, -5,  5],
    [5, 10, 10,-20,-20, 10, 10,  5],
    [0,  0,  0,  0,  0,  0,  0,  0]
]

knighttable = [
    [-50,-40,-30,-30,-30,-30,-40,-50],
    [-40,-20,  0,  0,  0,  0,-20,-40],
    [-30,  0, 10, 15, 15, 10,  0,-30],
    [-30,  5, 15, 20, 20, 15,  5,-30],
    [-30,  0, 15, 20, 20, 15,  0,-30],
    [-30,  5, 10, 15, 15, 10,  5,-30],
    [-40,-20,  0,  5,  5,  0,-20,-40],
    [-50,-40,-30,-30,-30,-30,-40,-50]
]

bishoptable = [
    [-20,-10,-10,-10,-10,-10,-10,-20],
    [-10,  0,  0,  0,  0,  0,  0,-10],
    [-10,  0,  5, 10, 10,  5,  0,-10],
    [-10,  5,  5, 10, 10,  5,  5,-10],
    [-10,  0, 10, 10, 10, 10,  0,-10],
    [-10, 10, 10, 10, 10, 10, 10,-10],
    [-10,  5,  0,  0,  0,  0,  5,-10],
    [-20,-10,-10,-10,-10,-10,-10,-20]
]

rooktable = [
    [0,  0,  0,  0,  0,  0,  0,  0],
    [5, 10, 10, 10, 10, 10, 10,  5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0,  5],
    [0,  0,  0,  5,  5,  0,  0,  0]
]

queentable = [
    [-20,-10,-10, -5, -5,-10,-10,-20],
    [-10,  0,  0,  0,  0,  0,  0,-10],
    [-10,  0,  5,  5,  5,  5,  0,-10],
    [-5,  0,  5,  5,  5,  5,  0, -5],
    [0,  0,  5,  5,  5,  5,  0, -5],
    [-10,  5,  5,  5,  5,  5,  0,-10],
    [-10,  0,  5,  0,  0,  0,  0,-10],
    [-20,-10,-10, -5, -5,-10,-10,-20]
]

kingtable = [
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-20,-30,-30,-40,-40,-30,-30,-20],
    [-10,-20,-20,-20,-20,-20,-20,-10],
    [20, 20,  0,  0,  0,  0, 20, 20],
    [20, 30, 10,  0,  0, 10, 30, 20]
]

pst = {
    'P': pawntable,
    'N': knighttable,
    'B': bishoptable,
    'R': rooktable,
    'Q': queentable,
    'K': kingtable
}

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def parse_square(sq):
    col = ord(sq[0]) - ord('a')
    row = int(sq[1]) - 1
    return row, col

def square_str(row, col):
    return chr(ord('a') + col) + str(row + 1)

def copy_board(board):
    return [row[:] for row in board]

# ----------------------------------------------------------------------
# Move generation
# ----------------------------------------------------------------------
knight_moves = [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]
king_moves   = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
bishop_dirs  = [(-1,-1),(-1,1),(1,-1),(1,1)]
rook_dirs    = [(-1,0),(1,0),(0,-1),(0,1)]

def pseudo_moves(board, r, c, color):
    piece = board[r][c]
    ptype = piece[1]
    moves = []
    if ptype == 'P':
        direction = 1 if color == 'w' else -1
        start_rank = 1 if color == 'w' else 6

        # forward one
        nr = r + direction
        if 0 <= nr < 8:
            if board[nr][c] is None:
                if nr == 7 or nr == 0:  # promotion
                    for promo in ['q','r','b','n']:
                        moves.append(square_str(r, c) + square_str(nr, c) + promo)
                else:
                    moves.append(square_str(r, c) + square_str(nr, c))
                # double step
                if r == start_rank:
                    nr2 = r + 2 * direction
                    if board[nr2][c] is None:
                        moves.append(square_str(r, c) + square_str(nr2, c))
            # captures
            for dc in (-1, 1):
                nc = c + dc
                if 0 <= nc < 8:
                    target = board[nr][nc]
                    if target is not None and target[0] != color:
                        if nr == 7 or nr == 0:
                            for promo in ['q','r','b','n']:
                                moves.append(square_str(r, c) + square_str(nr, nc) + promo)
                        else:
                            moves.append(square_str(r, c) + square_str(nr, nc))

    elif ptype == 'N':
        for dr, dc in knight_moves:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                target = board[nr][nc]
                if target is None or target[0] != color:
                    moves.append(square_str(r, c) + square_str(nr, nc))

    elif ptype == 'B':
        for dr, dc in bishop_dirs:
            for step in range(1, 8):
                nr, nc = r + dr * step, c + dc * step
                if not (0 <= nr < 8 and 0 <= nc < 8):
                    break
                target = board[nr][nc]
                if target is None:
                    moves.append(square_str(r, c) + square_str(nr, nc))
                else:
                    if target[0] != color:
                        moves.append(square_str(r, c) + square_str(nr, nc))
                    break

    elif ptype == 'R':
        for dr, dc in rook_dirs:
            for step in range(1, 8):
                nr, nc = r + dr * step, c + dc * step
                if not (0 <= nr < 8 and 0 <= nc < 8):
                    break
                target = board[nr][nc]
                if target is None:
                    moves.append(square_str(r, c) + square_str(nr, nc))
                else:
                    if target[0] != color:
                        moves.append(square_str(r, c) + square_str(nr, nc))
                    break

    elif ptype == 'Q':
        # queen = rook + bishop
        for dr, dc in bishop_dirs + rook_dirs:
            for step in range(1, 8):
                nr, nc = r + dr * step, c + dc * step
                if not (0 <= nr < 8 and 0 <= nc < 8):
                    break
                target = board[nr][nc]
                if target is None:
                    moves.append(square_str(r, c) + square_str(nr, nc))
                else:
                    if target[0] != color:
                        moves.append(square_str(r, c) + square_str(nr, nc))
                    break

    elif ptype == 'K':
        for dr, dc in king_moves:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                target = board[nr][nc]
                if target is None or target[0] != color:
                    moves.append(square_str(r, c) + square_str(nr, nc))
        # castling is handled separately
    return moves

def add_castling(board, color, moves):
    if color == 'w':
        if board[0][4] == 'wK':
            # king side
            if board[0][7] == 'wR' and board[0][5] is None and board[0][6] is None:
                if not is_attacked(board, (0,4), 'b') and \
                   not is_attacked(board, (0,5), 'b') and \
                   not is_attacked(board, (0,6), 'b'):
                    moves.append('e1g1')
            # queen side
            if board[0][0] == 'wR' and board[0][1] is None and board[0][2] is None and board[0][3] is None:
                if not is_attacked(board, (0,4), 'b') and \
                   not is_attacked(board, (0,3), 'b') and \
                   not is_attacked(board, (0,2), 'b'):
                    moves.append('e1c1')
    else:
        if board[7][4] == 'bK':
            # king side
            if board[7][7] == 'bR' and board[7][5] is None and board[7][6] is None:
                if not is_attacked(board, (7,4), 'w') and \
                   not is_attacked(board, (7,5), 'w') and \
                   not is_attacked(board, (7,6), 'w'):
                    moves.append('e8g8')
            # queen side
            if board[7][0] == 'bR' and board[7][1] is None and board[7][2] is None and board[7][3] is None:
                if not is_attacked(board, (7,4), 'w') and \
                   not is_attacked(board, (7,3), 'w') and \
                   not is_attacked(board, (7,2), 'w'):
                    moves.append('e8c8')

# ----------------------------------------------------------------------
# Attack detection
# ----------------------------------------------------------------------
def is_attacked(board, square, by_color):
    r, c = square

    # pawns
    if by_color == 'w':
        for dc in (-1, 1):
            nr, nc = r + 1, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                p = board[nr][nc]
                if p and p[0] == 'w' and p[1] == 'P':
                    return True
    else:
        for dc in (-1, 1):
            nr, nc = r - 1, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                p = board[nr][nc]
                if p and p[0] == 'b' and p[1] == 'P':
                    return True

    # knights
    for dr, dc in knight_moves:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 8 and 0 <= nc < 8:
            p = board[nr][nc]
            if p and p[0] == by_color and p[1] == 'N':
                return True

    # king
    for dr, dc in king_moves:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 8 and 0 <= nc < 8:
            p = board[nr][nc]
            if p and p[0] == by_color and p[1] == 'K':
                return True

    # sliding pieces – bishops/queen (diagonal)
    for dr, dc in bishop_dirs:
        for step in range(1, 8):
            nr, nc = r + dr * step, c + dc * step
            if not (0 <= nr < 8 and 0 <= nc < 8):
                break
            p = board[nr][nc]
            if p is None:
                continue
            if p[0] == by_color:
                if p[1] in ('B', 'Q'):
                    return True
                else:
                    break
            else:
                break

    # rooks/queen (orthogonal)
    for dr, dc in rook_dirs:
        for step in range(1, 8):
            nr, nc = r + dr * step, c + dc * step
            if not (0 <= nr < 8 and 0 <= nc < 8):
                break
            p = board[nr][nc]
            if p is None:
                continue
            if p[0] == by_color:
                if p[1] in ('R', 'Q'):
                    return True
                else:
                    break
            else:
                break

    return False

def is_king_in_check(board, color):
    king_sq = None
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if p and p[0] == color and p[1] == 'K':
                king_sq = (r, c)
                break
        if king_sq:
            break
    if king_sq is None:
        return False
    opponent = 'b' if color == 'w' else 'w'
    return is_attacked(board, king_sq, opponent)

# ----------------------------------------------------------------------
# Apply a move
# ----------------------------------------------------------------------
def apply_move(board, move_str, color):
    new_board = copy_board(board)

    src = move_str[:2]
    dst = move_str[2:4]
    promo = move_str[4:] if len(move_str) > 4 else ''

    sr, sc = parse_square(src)
    dr, dc = parse_square(dst)

    piece = new_board[sr][sc]
    if promo:
        piece = color + promo.upper()
    new_board[dr][dc] = piece
    new_board[sr][sc] = None

    # castling – move rook as well
    if piece[1] == 'K' and abs(dc - sc) == 2:
        if dc > sc:  # king side
            rook_src = (sr, 7)
            rook_dst = (sr, 5)
        else:        # queen side
            rook_src = (sr, 0)
            rook_dst = (sr, 3)
        rook = new_board[rook_src[0]][rook_src[1]]
        new_board[rook_dst[0]][rook_dst[1]] = rook
        new_board[rook_src[0]][rook_src[1]] = None

    return new_board

# ----------------------------------------------------------------------
# Legal move generation
# ----------------------------------------------------------------------
def generate_legal_moves(board, color):
    moves = []
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if p and p[0] == color:
                for m in pseudo_moves(board, r, c, color):
                    nb = apply_move(board, m, color)
                    # locate king after move
                    kr = kc = -1
                    for rr in range(8):
                        for cc in range(8):
                            pp = nb[rr][cc]
                            if pp and pp[0] == color and pp[1] == 'K':
                                kr, kc = rr, cc
                                break
                        if kr != -1:
                            break
                    if kr == -1:
                        continue
                    opp = 'b' if color == 'w' else 'w'
                    if not is_attacked(nb, (kr, kc), opp):
                        moves.append(m)

    # castling (checked separately)
    add_castling(board, color, moves)
    return moves

# ----------------------------------------------------------------------
# Evaluation
# ----------------------------------------------------------------------
def evaluate(board):
    total = 0
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if p:
                col = p[0]
                typ = p[1]
                val = piece_value[typ]
                pst_val = pst[typ][r][c]
                if col == 'w':
                    total += val + pst_val
                else:
                    total -= val + pst[typ][7 - r][c]
    return total

def evaluation_for_side(board, side):
    # returns evaluation from the perspective of the side to move
    if side == 'white':
        return evaluate(board)
    else:
        return -evaluate(board)

# ----------------------------------------------------------------------
# Search
# ----------------------------------------------------------------------
def move_priority(board, move, color):
    # simple heuristic: captures, promotions first
    dst = move[2:4]
    dr, dc = parse_square(dst)
    target = board[dr][dc]
    priority = 0
    if target:
        priority = piece_value[target[1]] * 10 - piece_value[board[parse_square(move[:2])[0], parse_square(move[:2])[1]][1]]
    if len(move) > 4:
        priority += 1000
    return priority

def alphabeta(board, depth, alpha, beta, maximizing, side):
    if depth == 0:
        return evaluation_for_side(board, side)

    moves = generate_legal_moves(board, side)
    if not moves:
        if is_king_in_check(board, side):
            return -100000 + depth   # prefer slower mate
        else:
            return 0                  # stalemate

    moves.sort(key=lambda m: move_priority(board, m, side), reverse=True)

    if maximizing:
        max_eval = -10**9
        for m in moves:
            nb = apply_move(board, m, side)
            nxt_side = 'black' if side == 'white' else 'white'
            val = alphabeta(nb, depth-1, alpha, beta, False, nxt_side)
            max_eval = max(max_eval, val)
            alpha = max(alpha, val)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = 10**9
        for m in moves:
            nb = apply_move(board, m, side)
            nxt_side = 'black' if side == 'white' else 'white'
            val = alphabeta(nb, depth-1, alpha, beta, True, nxt_side)
            min_eval = min(min_eval, val)
            beta = min(beta, val)
            if beta <= alpha:
                break
        return min_eval

def best_move(board, depth, side):
    moves = generate_legal_moves(board, side)
    if not moves:
        return None
    moves.sort(key=lambda m: move_priority(board, m, side), reverse=True)

    best = None
    alpha = -10**9
    beta = 10**9
    for m in moves:
        nb = apply_move(board, m, side)
        nxt_side = 'black' if side == 'white' else 'white'
        val = alphabeta(nb, depth-1, alpha, beta, False, nxt_side)
        if val > alpha:
            alpha = val
            best = m
    return best

# ----------------------------------------------------------------------
# Main policy entry point
# ----------------------------------------------------------------------
def policy(pieces: dict[str, str], to_play: str) -> str:
    # Build board
    board = [[None for _ in range(8)] for __ in range(8)]
    for sq, pc in pieces.items():
        col = ord(sq[0]) - ord('a')
        row = int(sq[1]) - 1
        board[row][col] = pc

    side = 'white' if to_play == 'white' else 'black'
    side_letter = 'w' if side == 'white' else 'b'

    # Ensure at least one legal move exists
    legal = generate_legal_moves(board, side_letter)
    if not legal:
        # Should not happen in a real game, but return any empty string to avoid crash
        return ''

    # Iterative deepening
    start = time.time()
    best = legal[0]
    for depth in range(1, 4):
        if time.time() - start > 0.9:
            break
        candidate = best_move(board, depth, side_letter)
        if candidate is not None:
            best = candidate
    return best
