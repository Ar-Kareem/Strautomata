
import time

class SearchTimeout(Exception):
    pass

# Direction vectors
WHITE_MAN_DIRS = [(1, -1), (1, 1)]
BLACK_MAN_DIRS = [(-1, -1), (-1, 1)]
KING_DIRS = [(1, -1), (1, 1), (-1, -1), (-1, 1)]

# Positional tables (row 0 to 7, col 0 to 7)
WHITE_MAN_PST = [
    [0, 20,  0, 20,  0, 20,  0, 20],  # row 0: back rank defense
    [5,  0,  5,  0,  5,  0,  5,  0],  # row 1
    [0,  8,  0, 12,  0, 12,  0,  8],  # row 2
    [10, 0, 16,  0, 16,  0, 10,  0],  # row 3: center control
    [0, 18,  0, 22,  0, 22,  0, 18],  # row 4
    [25, 0, 30,  0, 30,  0, 25,  0],  # row 5
    [0, 40,  0, 45,  0, 45,  0, 40],  # row 6: close to crown
    [0,  0,  0,  0,  0,  0,  0,  0],  # row 7: crowned
]

BLACK_MAN_PST = [
    [0,  0,  0,  0,  0,  0,  0,  0],  # row 0: crowned
    [40, 0, 45,  0, 45,  0, 40,  0],  # row 1: close to crown
    [0, 25,  0, 30,  0, 30,  0, 25],  # row 2
    [18, 0, 22,  0, 22,  0, 18,  0],  # row 3
    [0, 10,  0, 16,  0, 16,  0, 10],  # row 4: center control
    [8,  0, 12,  0, 12,  0,  8,  0],  # row 5
    [0,  5,  0,  5,  0,  5,  0,  5],  # row 6
    [20, 0, 20,  0, 20,  0, 20,  0],  # row 7: back rank defense
]

KING_PST = [
    [0,  2,  0,  2,  0,  2,  0,  2],
    [2,  0,  8,  0,  8,  0,  2,  0],
    [0,  8,  0, 16,  0, 16,  0,  8],
    [2,  0, 16,  0, 20,  0, 16,  0],
    [0, 16,  0, 20,  0, 16,  0,  2],
    [8,  0, 16,  0, 16,  0,  8,  0],
    [0,  2,  0,  8,  0,  8,  0,  2],
    [2,  0,  2,  0,  2,  0,  2,  0],
]

def get_captures(board, player, specific_sq=None):
    """Generate all capture moves for `player` (+1 for White, -1 for Black)."""
    captures = []
    squares = [specific_sq] if specific_sq is not None else [
        (r, c) for r in range(8) for c in range(8)
        if (board[r * 8 + c] > 0 if player == 1 else board[r * 8 + c] < 0)
    ]

    for r, c in squares:
        val = board[r * 8 + c]
        if val == 0:
            continue
        if abs(val) == 1:
            dirs = WHITE_MAN_DIRS if val == 1 else BLACK_MAN_DIRS
        else:
            dirs = KING_DIRS

        for dr, dc in dirs:
            mr, mc = r + dr, c + dc
            er, ec = r + 2 * dr, c + 2 * dc
            if 0 <= er < 8 and 0 <= ec < 8:
                mid_val = board[mr * 8 + mc]
                end_val = board[er * 8 + ec]
                if end_val == 0:
                    if (player == 1 and mid_val < 0) or (player == -1 and mid_val > 0):
                        captures.append(((r, c), (er, ec)))
    return captures

def get_quiet_moves(board, player):
    """Generate all non-capture moves for `player`."""
    moves = []
    for r in range(8):
        for c in range(8):
            val = board[r * 8 + c]
            if (player == 1 and val <= 0) or (player == -1 and val >= 0):
                continue
            if abs(val) == 1:
                dirs = WHITE_MAN_DIRS if val == 1 else BLACK_MAN_DIRS
            else:
                dirs = KING_DIRS

            for dr, dc in dirs:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8 and board[nr * 8 + nc] == 0:
                    moves.append(((r, c), (nr, nc)))
    return moves

def get_legal_moves(board, player, continuation_sq=None):
    """Captures are mandatory in checkers."""
    captures = get_captures(board, player, continuation_sq)
    if captures or continuation_sq is not None:
        return captures
    return get_quiet_moves(board, player)

def make_move(board, move):
    """Applies a move and returns state needed for undo."""
    (r1, c1), (r2, c2) = move
    piece = board[r1 * 8 + c1]
    board[r1 * 8 + c1] = 0

    is_capture = abs(r2 - r1) == 2
    captured_piece = 0
    cap_r, cap_c = -1, -1
    if is_capture:
        cap_r, cap_c = (r1 + r2) // 2, (c1 + c2) // 2
        captured_piece = board[cap_r * 8 + cap_c]
        board[cap_r * 8 + cap_c] = 0

    promoted = False
    if piece == 1 and r2 == 7:
        board[r2 * 8 + c2] = 2
        promoted = True
    elif piece == -1 and r2 == 0:
        board[r2 * 8 + c2] = -2
        promoted = True
    else:
        board[r2 * 8 + c2] = piece

    return piece, captured_piece, cap_r, cap_c, promoted

def unmake_move(board, move, undo_info):
    (r1, c1), (r2, c2) = move
    piece, captured_piece, cap_r, cap_c, _ = undo_info
    board[r1 * 8 + c1] = piece
    board[r2 * 8 + c2] = 0
    if captured_piece != 0:
        board[cap_r * 8 + cap_c] = captured_piece

def evaluate(board):
    """Static evaluation from White's perspective."""
    w_mat, b_mat = 0, 0
    w_pos, b_pos = 0, 0
    w_kings, b_kings = [], []
    w_men_count, b_men_count = 0, 0

    for r in range(8):
        for c in range(8):
            val = board[r * 8 + c]
            if val == 0:
                continue
            if val == 1:
                w_mat += 100
                w_pos += WHITE_MAN_PST[r][c]
                w_men_count += 1
            elif val == 2:
                w_mat += 180
                w_pos += KING_PST[r][c]
                w_kings.append((r, c))
            elif val == -1:
                b_mat += 100
                b_pos += BLACK_MAN_PST[r][c]
                b_men_count += 1
            elif val == -2:
                b_mat += 180
                b_pos += KING_PST[r][c]
                b_kings.append((r, c))

    score = (w_mat + w_pos) - (b_mat + b_pos)

    # Endgame king centralization: drive lonely kings toward opponent
    total_w = w_men_count + len(w_kings)
    total_b = b_men_count + len(b_kings)
    if total_w > total_b and total_b <= 2 and w_kings:
        # Chase black pieces
        dist_sum = 0
        opp_coords = [(r, c) for r in range(8) for c in range(8) if board[r * 8 + c] < 0]
        if opp_coords:
            for kr, kc in w_kings:
                dist_sum += min(abs(kr - opr) + abs(kc - opc) for opr, opc in opp_coords)
            score -= dist_sum * 4
    elif total_b > total_w and total_w <= 2 and b_kings:
        dist_sum = 0
        opp_coords = [(r, c) for r in range(8) for c in range(8) if board[r * 8 + c] > 0]
        if opp_coords:
            for kr, kc in b_kings:
                dist_sum += min(abs(kr - opr) + abs(kc - opc) for opr, opc in opp_coords)
            score += dist_sum * 4

    return score

def order_moves(board, moves):
    """Sort moves: captures first, king captures high priority, promotions."""
    def move_priority(m):
        (r1, c1), (r2, c2) = m
        score = 0
        is_capture = abs(r2 - r1) == 2
        if is_capture:
            mid = board[((r1 + r2) // 2) * 8 + ((c1 + c2) // 2)]
            score += 1000 + abs(mid) * 100
        piece = board[r1 * 8 + c1]
        if (piece == 1 and r2 == 7) or (piece == -1 and r2 == 0):
            score += 500
        return score
    return sorted(moves, key=move_priority, reverse=True)

class Engine:
    def __init__(self, start_time, time_limit=0.80):
        self.start_time = start_time
        self.time_limit = time_limit
        self.node_count = 0

    def check_time(self):
        self.node_count += 1
        if (self.node_count & 255) == 0:
            if time.time() - self.start_time > self.time_limit:
                raise SearchTimeout()

    def search(self, board, player, depth, alpha, beta, continuation_sq=None):
        self.check_time()

        moves = get_legal_moves(board, player, continuation_sq)
        if not moves:
            # If player has no moves during turn, they lose
            if continuation_sq is not None:
                # Finished multi-jump, pass turn to opponent
                return -self.search(board, -player, depth, -beta, -alpha, None)
            return -20000 + (10 - depth)

        if depth <= 0 and continuation_sq is None:
            # Stand-pat quiescent evaluation
            base_eval = evaluate(board) * player
            return base_eval

        ordered = order_moves(board, moves)
        best_val = -30000

        for move in ordered:
            undo = make_move(board, move)
            _, captured, _, _, promoted = undo
            (r1, c1), (r2, c2) = move

            # Continuation jump logic
            next_cont = None
            if captured != 0 and not promoted:
                if get_captures(board, player, (r2, c2)):
                    next_cont = (r2, c2)

            if next_cont is not None:
                val = self.search(board, player, depth, alpha, beta, next_cont)
            else:
                val = -self.search(board, -player, depth - 1, -beta, -alpha, None)

            unmake_move(board, move, undo)

            if val > best_val:
                best_val = val
            alpha = max(alpha, best_val)
            if alpha >= beta:
                break

        return best_val

def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    start_time = time.time()
    player = 1 if color == 'w' else -1

    board = [0] * 64
    for r, c in my_men:
        board[r * 8 + c] = 1 if player == 1 else -1
    for r, c in my_kings:
        board[r * 8 + c] = 2 if player == 1 else -2
    for r, c in opp_men:
        board[r * 8 + c] = -1 if player == 1 else 1
    for r, c in opp_kings:
        board[r * 8 + c] = -2 if player == 1 else 2

    legal_moves = get_legal_moves(board, player)
    if not legal_moves:
        return ((0, 0), (0, 0))
    if len(legal_moves) == 1:
        m = legal_moves[0]
        return ((int(m[0][0]), int(m[0][1])), (int(m[1][0]), int(m[1][1])))

    ordered_moves = order_moves(board, legal_moves)
    best_move = ordered_moves[0]
    engine = Engine(start_time, time_limit=0.80)

    # Iterative deepening
    for depth in range(1, 32):
        current_best = None
        current_best_val = -30000
        alpha = -30000
        beta = 30000
        try:
            for move in ordered_moves:
                undo = make_move(board, move)
                _, captured, _, _, promoted = undo
                (r1, c1), (r2, c2) = move

                next_cont = None
                if captured != 0 and not promoted:
                    if get_captures(board, player, (r2, c2)):
                        next_cont = (r2, c2)

                if next_cont is not None:
                    val = engine.search(board, player, depth, alpha, beta, next_cont)
                else:
                    val = -engine.search(board, -player, depth - 1, -beta, -alpha, None)

                unmake_move(board, move, undo)

                if val > current_best_val:
                    current_best_val = val
                    current_best = move
                alpha = max(alpha, current_best_val)

            if current_best is not None:
                best_move = current_best
                # Move best move to the front for subsequent iterations
                ordered_moves.remove(best_move)
                ordered_moves.insert(0, best_move)

        except SearchTimeout:
            break

    return ((int(best_move[0][0]), int(best_move[0][1])), (int(best_move[1][0]), int(best_move[1][1])))
