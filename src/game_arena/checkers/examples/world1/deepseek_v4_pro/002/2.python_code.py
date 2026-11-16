
import time

# ----------------------------------------------------------------------
# Tables for positional evaluation (only dark squares have non-zero)
# ----------------------------------------------------------------------
WHITE_MAN_TABLE = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 5, 0, 5, 0, 5, 0, 5],
    [0, 0,10, 0,10, 0,10, 0],
    [0,15, 0,15, 0,15, 0,15],
    [0, 0,20, 0,25, 0,20, 0],
    [0,25, 0,30, 0,30, 0,25],
    [0, 0,35, 0,40, 0,35, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
]

BLACK_MAN_TABLE = WHITE_MAN_TABLE[::-1]

KING_TABLE = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0,30, 0,35, 0,35, 0,30],
    [0, 0,35, 0,40, 0,35, 0],
    [0,35, 0,40, 0,40, 0,35],
    [0, 0,45, 0,50, 0,45, 0],
    [0,35, 0,40, 0,40, 0,35],
    [0, 0,35, 0,40, 0,35, 0],
    [0,30, 0,35, 0,35, 0,30],
]

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def build_board(my_men, my_kings, opp_men, opp_kings, our_color):
    """Convert piece lists into an 8x8 board.
       Our pieces: 1=man, 2=king; Opponent pieces: -1=man, -2=king."""
    board = [[0] * 8 for _ in range(8)]
    for r, c in my_men:
        board[r][c] = 1
    for r, c in my_kings:
        board[r][c] = 2
    for r, c in opp_men:
        board[r][c] = -1
    for r, c in opp_kings:
        board[r][c] = -2
    return board


def piece_color(piece, our_color):
    """Return the color of a piece given its integer representation and our color."""
    if piece > 0:
        return our_color
    return 'b' if our_color == 'w' else 'w'


def forward(color):
    """Return the row-step for a man of the given color."""
    return 1 if color == 'w' else -1


def get_pieces(board, color_to_move, our_color):
    """Return list of (r, c, piece) for the player color_to_move."""
    targets = (1, 2) if color_to_move == our_color else (-1, -2)
    pieces = []
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if p in targets:
                pieces.append((r, c, p))
    return pieces


def apply_move(board, move, color_to_move, our_color):
    """Apply a single step move (regular or capture). Returns (new_board, next_color)."""
    (fr, fc), (tr, tc) = move
    new_board = [row[:] for row in board]
    piece = new_board[fr][fc]
    new_board[fr][fc] = 0
    new_board[tr][tc] = piece

    is_capture = abs(fr - tr) == 2
    if is_capture:
        cr = (fr + tr) // 2
        cc = (fc + tc) // 2
        new_board[cr][cc] = 0

    p_color = piece_color(piece, our_color)

    # Promotion
    if abs(piece) == 1:
        if (p_color == 'w' and tr == 7) or (p_color == 'b' and tr == 0):
            new_board[tr][tc] = 2 if piece > 0 else -2
            # promotion ends the turn
            return new_board, ('b' if color_to_move == 'w' else 'w')

    if is_capture:
        # Check if the moved piece can capture again
        piece_type = new_board[tr][tc]
        p_color = piece_color(piece_type, our_color)
        fwd = forward(p_color)
        dirs = [(fwd, -1), (fwd, 1)] if abs(piece_type) == 1 \
               else [(1, -1), (1, 1), (-1, -1), (-1, 1)]
        can_capture = False
        for dr, dc in dirs:
            nr, nc = tr + dr, tc + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                if new_board[nr][nc] != 0 and (new_board[nr][nc] > 0) != (piece_type > 0):
                    jr, jc = tr + 2*dr, tc + 2*dc
                    if 0 <= jr < 8 and 0 <= jc < 8 and new_board[jr][jc] == 0:
                        can_capture = True
                        break
        if can_capture:
            return new_board, color_to_move
        else:
            return new_board, ('b' if color_to_move == 'w' else 'w')
    else:
        return new_board, ('b' if color_to_move == 'w' else 'w')


def generate_legal_moves(board, color_to_move, our_color):
    """Generate all legal moves (captures are mandatory if present).
       Returns list of (move, next_board, next_color)."""
    captures = []
    regular = []
    pieces = get_pieces(board, color_to_move, our_color)

    for r, c, piece in pieces:
        p_color = piece_color(piece, our_color)
        fwd = forward(p_color)
        dirs = [(fwd, -1), (fwd, 1)] if abs(piece) == 1 \
               else [(1, -1), (1, 1), (-1, -1), (-1, 1)]

        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                if board[nr][nc] == 0:
                    regular.append(((r, c), (nr, nc)))
                elif (board[nr][nc] > 0) != (piece > 0):  # opponent piece
                    jr, jc = r + 2*dr, c + 2*dc
                    if 0 <= jr < 8 and 0 <= jc < 8 and board[jr][jc] == 0:
                        captures.append(((r, c), (jr, jc)))

    source = captures if captures else regular
    moves = []
    for mv in source:
        nb, nc = apply_move(board, mv, color_to_move, our_color)
        moves.append((mv, nb, nc))
    return moves


def evaluate(board, our_color):
    """Static evaluation from our perspective (positive is good)."""
    score = 0
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece == 0:
                continue
            if piece > 0:
                if piece == 1:
                    val = 100
                    if our_color == 'w':
                        val += WHITE_MAN_TABLE[r][c]
                    else:
                        val += BLACK_MAN_TABLE[r][c]
                else:
                    val = 200 + KING_TABLE[r][c]
                score += val
            else:
                if piece == -1:
                    val = 100
                    if our_color == 'w':
                        val += BLACK_MAN_TABLE[r][c]
                    else:
                        val += WHITE_MAN_TABLE[r][c]
                    score -= val
                else:
                    val = 200 + KING_TABLE[r][c]
                    score -= val
    return score


def order_moves(moves, our_color, maximizing):
    """Order moves by static evaluation to improve alpha-beta pruning."""
    scored = []
    for mv, nb, nc in moves:
        s = evaluate(nb, our_color)
        scored.append((s, mv, nb, nc))
    scored.sort(key=lambda x: x[0], reverse=maximizing)
    return [(mv, nb, nc) for _, mv, nb, nc in scored]


class Timeout(Exception):
    pass


def minimax(state, depth, alpha, beta, color_to_move, our_color, start_time, time_limit):
    """Minimax with alpha-beta pruning. Raises Timeout if out of time."""
    if time.time() - start_time > time_limit:
        raise Timeout()

    if depth == 0:
        return evaluate(state, our_color)

    moves = generate_legal_moves(state, color_to_move, our_color)
    if not moves:
        return -99999 if color_to_move == our_color else 99999

    ordered = order_moves(moves, our_color, color_to_move == our_color)

    if color_to_move == our_color:
        best_val = -float('inf')
        for _, next_state, next_color in ordered:
            val = minimax(next_state, depth - 1, alpha, beta,
                          next_color, our_color, start_time, time_limit)
            if val > best_val:
                best_val = val
            alpha = max(alpha, val)
            if alpha >= beta:
                break
        return best_val
    else:
        best_val = float('inf')
        for _, next_state, next_color in ordered:
            val = minimax(next_state, depth - 1, alpha, beta,
                          next_color, our_color, start_time, time_limit)
            if val < best_val:
                best_val = val
            beta = min(beta, val)
            if alpha >= beta:
                break
        return best_val


def find_best_move(board, depth, our_color, start_time, time_limit):
    """Root call to minimax. Returns (best_move, value)."""
    moves = generate_legal_moves(board, our_color, our_color)
    if not moves:
        return None, -99999

    ordered = order_moves(moves, our_color, True)
    best_move = ordered[0][0]
    best_val = -float('inf')
    alpha = -float('inf')
    beta = float('inf')

    for _, next_state, next_color in ordered:
        val = minimax(next_state, depth - 1, alpha, beta,
                      next_color, our_color, start_time, time_limit)
        if val > best_val:
            best_val = val
            best_move = _[1]  # move from the tuple we unwrapped
        # Actually we need the move from the ordered list. Let's rewrite the loop cleanly.
    
    # --- Cleaner version of the loop above ---
    best_move = ordered[0][0]
    best_val = -float('inf')
    alpha = -float('inf')
    beta = float('inf')
    for move, next_state, next_color in ordered:
        val = minimax(next_state, depth - 1, alpha, beta,
                      next_color, our_color, start_time, time_limit)
        if val > best_val:
            best_val = val
            best_move = move
        alpha = max(alpha, val)
        if alpha >= beta:
            break
    return best_move, best_val


# ----------------------------------------------------------------------
# Main policy function required by the arena
# ----------------------------------------------------------------------
def policy(my_men, my_kings, opp_men, opp_kings, color):
    """Return the best legal move as ((from_row, from_col), (to_row, to_col))."""
    start_time = time.time()
    time_limit = 0.9
    board = build_board(my_men, my_kings, opp_men, opp_kings, color)

    best_move = None
    depth = 1
    while True:
        if time.time() - start_time > time_limit * 0.8:
            break
        try:
            move, val = find_best_move(board, depth, color, start_time, time_limit)
            if move is not None:
                best_move = move
        except Timeout:
            break
        depth += 1
        if depth > 20:
            break

    if best_move is None:
        # Fallback: return the first legal move
        moves = generate_legal_moves(board, color, color)
        if moves:
            best_move = moves[0][0]
        else:
            # Should never happen, but return a safe dummy
            return ((0, 0), (0, 0))

    return best_move
