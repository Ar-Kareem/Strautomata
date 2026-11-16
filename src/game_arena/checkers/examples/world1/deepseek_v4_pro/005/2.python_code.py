
import time

# Constants for board representation
BLACK_MAN = 1
BLACK_KING = 2
WHITE_MAN = -1
WHITE_KING = -2

# Global deadline for iterative deepening timeout
deadline = 0


class TimeoutError(Exception):
    """Raised when the search exceeds the time limit."""
    pass


def opponent(color):
    """Return the opponent's color."""
    return 'w' if color == 'b' else 'b'


def find_captures(board, r, c, color, forward, king_row, is_king):
    """
    Depth-first search for all capture sequences starting from (r, c).
    Returns a list of tuples: (to_row, to_col, list_of_captured_squares).
    """
    moves = []

    def dfs(brd, cr, cc, piece, is_king, captured):
        jumps = []
        directions = [forward]
        if is_king:
            directions = [forward, -forward]

        for dr in directions:
            for dc in (-1, 1):
                nr = cr + dr
                nc = cc + dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    opp_piece = brd[nr][nc]
                    if (color == 'b' and opp_piece < 0) or (color == 'w' and opp_piece > 0):
                        br = nr + dr
                        bc = nc + dc
                        if 0 <= br < 8 and 0 <= bc < 8 and brd[br][bc] == 0:
                            jumps.append((br, bc, nr, nc))

        if not jumps:
            if captured:
                moves.append((cr, cc, captured))
            return

        for br, bc, cr_jump, cc_jump in jumps:
            new_brd = [row[:] for row in brd]
            new_brd[cr_jump][cc_jump] = 0
            piece_val = piece
            new_captured = captured + [(cr_jump, cc_jump)]

            # Promotion during a multi-jump ends the turn
            if (color == 'b' and piece_val == BLACK_MAN and br == 0) or \
               (color == 'w' and piece_val == WHITE_MAN and br == 7):
                new_brd[cr][cc] = 0
                new_brd[br][bc] = BLACK_KING if color == 'b' else WHITE_KING
                moves.append((br, bc, new_captured))
            else:
                new_brd[cr][cc] = 0
                new_brd[br][bc] = piece_val
                dfs(new_brd, br, bc, piece_val, piece_val in (BLACK_KING, WHITE_KING), new_captured)

    dfs(board, r, c, board[r][c], is_king, [])
    return moves


def get_all_moves(board, color):
    """
    Return all legal moves for the given color.
    Each move is a tuple: ((from_row, from_col), (to_row, to_col), [captured_squares]).
    If any captures are possible, only captures are returned.
    """
    if color == 'b':
        forward = -1
        king_row = 0
    else:
        forward = 1
        king_row = 7

    pieces = []
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if (color == 'b' and piece > 0) or (color == 'w' and piece < 0):
                pieces.append((r, c))

    captures = []
    simples = []

    for r, c in pieces:
        piece = board[r][c]
        is_king = piece in (BLACK_KING, WHITE_KING)
        cap_moves = find_captures(board, r, c, color, forward, king_row, is_king)
        for tr, tc, captured in cap_moves:
            captures.append(((r, c), (tr, tc), captured))

    if captures:
        return captures

    # No captures available – generate simple moves
    for r, c in pieces:
        piece = board[r][c]
        is_king = piece in (BLACK_KING, WHITE_KING)
        directions = [forward]
        if is_king:
            directions = [forward, -forward]
        for dr in directions:
            for dc in (-1, 1):
                nr, nc = r + dr, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8 and board[nr][nc] == 0:
                    simples.append(((r, c), (nr, nc), []))

    return simples


def apply_move(board, move_info):
    """Return a new board after applying the given move."""
    (fr, fc), (tr, tc), captured = move_info
    new_brd = [row[:] for row in board]
    piece = new_brd[fr][fc]
    new_brd[fr][fc] = 0
    for cap_r, cap_c in captured:
        new_brd[cap_r][cap_c] = 0

    if piece == BLACK_MAN and tr == 0:
        piece = BLACK_KING
    elif piece == WHITE_MAN and tr == 7:
        piece = WHITE_KING

    new_brd[tr][tc] = piece
    return new_brd


def evaluate(board, color):
    """
    Static evaluation from the perspective of `color`.
    Positive values indicate an advantage for `color`.
    """
    score = 0
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece == 0:
                continue
            if piece == BLACK_MAN:
                val = 100 + (7 - r) * 5
            elif piece == BLACK_KING:
                val = 130
            elif piece == WHITE_MAN:
                val = 100 + r * 5
            elif piece == WHITE_KING:
                val = 130
            else:
                continue

            if color == 'b':
                if piece > 0:
                    score += val
                else:
                    score -= val
            else:  # color == 'w'
                if piece < 0:
                    score += val
                else:
                    score -= val
    return score


def order_moves(moves, board, color):
    """
    Sort moves in-place to improve alpha-beta pruning.
    Prioritises captures (especially of kings) and promotions.
    """
    def priority(move):
        (fr, fc), (tr, tc), captured = move
        piece = board[fr][fc]
        score = 0
        if captured:
            score += 1000
            for cap_r, cap_c in captured:
                cap_piece = board[cap_r][cap_c]
                if cap_piece in (BLACK_KING, WHITE_KING):
                    score += 200
            if (color == 'b' and piece == BLACK_MAN and tr == 0) or \
               (color == 'w' and piece == WHITE_MAN and tr == 7):
                score += 300
        else:
            if (color == 'b' and piece == BLACK_MAN and tr == 0) or \
               (color == 'w' and piece == WHITE_MAN and tr == 7):
                score += 500
            if color == 'b':
                score += (7 - tr)
            else:
                score += tr
        return -score  # higher priority first

    moves.sort(key=priority)


def negamax(board, color, depth, alpha, beta):
    """Recursive negamax search with alpha-beta pruning."""
    global deadline
    if time.time() > deadline:
        raise TimeoutError()

    moves = get_all_moves(board, color)
    if depth == 0 or not moves:
        return evaluate(board, color), None

    order_moves(moves, board, color)

    value = -float('inf')
    best_move = None
    for move in moves:
        new_board = apply_move(board, move)
        val, _ = negamax(new_board, opponent(color), depth - 1, -beta, -alpha)
        val = -val
        if val > value:
            value = val
            best_move = move
        alpha = max(alpha, value)
        if alpha >= beta:
            break
    return value, best_move


def root_alpha_beta(board, color, depth):
    """Root of the search. Handles move ordering and time checks."""
    global deadline
    moves = get_all_moves(board, color)
    if not moves:
        return None

    order_moves(moves, board, color)

    alpha = -float('inf')
    beta = float('inf')
    value = -float('inf')
    best_move = None

    for move in moves:
        if time.time() > deadline:
            raise TimeoutError()
        new_board = apply_move(board, move)
        val, _ = negamax(new_board, opponent(color), depth - 1, -beta, -alpha)
        val = -val
        if val > value:
            value = val
            best_move = move
        alpha = max(alpha, value)
        if alpha >= beta:
            break
    return best_move


def policy(my_men, my_kings, opp_men, opp_kings, color):
    """
    Compute the best move using iterative deepening alpha-beta search.
    Returns a tuple ((from_row, from_col), (to_row, to_col)).
    """
    # Build internal board representation
    board = [[0] * 8 for _ in range(8)]
    if color == 'b':
        for r, c in my_men:
            board[r][c] = BLACK_MAN
        for r, c in my_kings:
            board[r][c] = BLACK_KING
        for r, c in opp_men:
            board[r][c] = WHITE_MAN
        for r, c in opp_kings:
            board[r][c] = WHITE_KING
    else:
        for r, c in my_men:
            board[r][c] = WHITE_MAN
        for r, c in my_kings:
            board[r][c] = WHITE_KING
        for r, c in opp_men:
            board[r][c] = BLACK_MAN
        for r, c in opp_kings:
            board[r][c] = BLACK_KING

    global deadline
    deadline = time.time() + 0.9

    best_move = None
    depth = 1
    try:
        while True:
            move = root_alpha_beta(board, color, depth)
            if move is not None:
                best_move = move
            depth += 1
    except TimeoutError:
        pass

    if best_move is None:
        moves = get_all_moves(board, color)
        if moves:
            best_move = (moves[0][0], moves[0][1])
        else:
            # Should never happen if there is a legal move
            best_move = ((0, 0), (0, 0))

    return best_move
