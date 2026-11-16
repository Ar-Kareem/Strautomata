
import time

# Constants for piece types
EMPTY = 0
WMAN = 1
WKING = 2
BMAN = 3
BKING = 4

# Precomputed valid diagonal steps [up-left, up-right, down-right, down-left]
STEP_DIRS = [7, 9, -7, -9]
VALID_STEPS = [[False]*4 for _ in range(64)]

for idx in range(64):
    r, c = divmod(idx, 8)
    # up-left
    if r+1 < 8 and c-1 >= 0:
        VALID_STEPS[idx][0] = True
    # up-right
    if r+1 < 8 and c+1 < 8:
        VALID_STEPS[idx][1] = True
    # down-right
    if r-1 >= 0 and c+1 < 8:
        VALID_STEPS[idx][2] = True
    # down-left
    if r-1 >= 0 and c-1 >= 0:
        VALID_STEPS[idx][3] = True

# Time control globals
START_TIME = 0.0
TIME_LIMIT = 1.0

class TimeoutError(Exception):
    pass

def check_time():
    if time.time() - START_TIME > TIME_LIMIT:
        raise TimeoutError

def opponent(color):
    return 'w' if color == 'b' else 'b'

def valid_step(idx, d):
    return VALID_STEPS[idx][d]

def can_capture(board, idx, d, color, captured):
    if not valid_step(idx, d):
        return False
    mid = idx + STEP_DIRS[d]
    if color == 'w':
        opp_pieces = (BMAN, BKING)
    else:
        opp_pieces = (WMAN, WKING)
    if board[mid] not in opp_pieces:
        return False
    if mid in captured:
        return False
    land = mid + STEP_DIRS[d]
    if not valid_step(mid, d):
        return False
    if board[land] != EMPTY:
        return False
    return True

def gen_captures(board, idx, color, captured, start_idx):
    """Generate all capture sequences from idx, yielding (start_idx, end_idx, frozenset(captured))."""
    piece = board[idx]
    if color == 'w':
        my_man = WMAN
    else:
        my_man = BMAN

    if piece == my_man:
        dirs = [0, 1] if color == 'w' else [2, 3]
    else:
        dirs = [0, 1, 2, 3]

    for d in dirs:
        if not can_capture(board, idx, d, color, captured):
            continue
        mid = idx + STEP_DIRS[d]
        land = mid + STEP_DIRS[d]

        captured_piece = board[mid]
        board[mid] = EMPTY
        board[idx] = EMPTY
        board[land] = piece
        new_captured = captured | {mid}
        r_land = land // 8
        stop = False
        if piece == my_man:
            if (color == 'w' and r_land == 7) or (color == 'b' and r_land == 0):
                stop = True

        has_further = False
        if not stop:
            for move in gen_captures(board, land, color, new_captured, start_idx):
                has_further = True
                yield move
        if not has_further:
            yield (start_idx, land, frozenset(new_captured))

        # revert
        board[mid] = captured_piece
        board[idx] = piece
        board[land] = EMPTY

def get_moves(board, color):
    """Return all legal moves for color. If captures exist, only those are returned."""
    if color == 'w':
        my_piece_types = (WMAN, WKING)
    else:
        my_piece_types = (BMAN, BKING)

    my_indices = [i for i in range(64) if board[i] in my_piece_types]

    all_captures = []
    for idx in my_indices:
        piece = board[idx]
        if piece in my_piece_types:
            captures = list(gen_captures(board, idx, color, set(), idx))
            all_captures.extend(captures)

    if all_captures:
        return all_captures

    # Normal moves
    normal_moves = []
    for idx in my_indices:
        piece = board[idx]
        if piece == (WMAN if color == 'w' else BMAN):
            dirs = [0, 1] if color == 'w' else [2, 3]
        else:
            dirs = [0, 1, 2, 3]
        for d in dirs:
            if not valid_step(idx, d):
                continue
            target = idx + STEP_DIRS[d]
            if board[target] == EMPTY:
                normal_moves.append((idx, target, frozenset()))
    return normal_moves

def apply_move(board, move, color):
    """Return a new board after applying the move."""
    start, end, captured = move
    new_board = board[:]
    piece = new_board[start]
    new_board[start] = EMPTY
    new_board[end] = piece
    for cap in captured:
        new_board[cap] = EMPTY
    # Promotion
    if color == 'w':
        if piece == WMAN and end // 8 == 7:
            new_board[end] = WKING
    else:
        if piece == BMN and end // 8 == 0:
            new_board[end] = BKING
    return new_board

def evaluate(board, color):
    """Material + positional evaluation from the perspective of color."""
    score = 0
    for idx, piece in enumerate(board):
        if piece == EMPTY:
            continue
        r, c = divmod(idx, 8)
        center = 4 - abs(c - 3)  # 0..4, center bonus
        if piece == WMAN:
            val = 100 + r * 5 + center
            if color == 'w':
                score += val
            else:
                score -= val
        elif piece == WKING:
            val = 200 + r * 2 + center * 2
            if color == 'w':
                score += val
            else:
                score -= val
        elif piece == BMN:
            val = 100 + (7 - r) * 5 + center
            if color == 'b':
                score += val
            else:
                score -= val
        elif piece == BKING:
            val = 200 + (7 - r) * 2 + center * 2
            if color == 'b':
                score += val
            else:
                score -= val
    return score

def negamax(board, depth, color, alpha, beta):
    """Alpha-beta negamax search."""
    check_time()
    if depth == 0:
        return evaluate(board, color)
    moves = get_moves(board, color)
    if not moves:
        return -1000000
    for move in moves:
        new_board = apply_move(board, move, color)
        score = -negamax(new_board, depth - 1, opponent(color), -beta, -alpha)
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break
    return alpha

def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    global START_TIME, TIME_LIMIT
    START_TIME = time.time()
    TIME_LIMIT = 0.95

    # Initialize board
    board = [EMPTY] * 64
    if color == 'w':
        my_man_piece, my_king_piece = WMAN, WKING
        opp_man_piece, opp_king_piece = BMN, BKING
    else:
        my_man_piece, my_king_piece = BMN, BKING
        opp_man_piece, opp_king_piece = WMAN, WKING

    for r, c in my_men:
        board[r * 8 + c] = my_man_piece
    for r, c in my_kings:
        board[r * 8 + c] = my_king_piece
    for r, c in opp_men:
        board[r * 8 + c] = opp_man_piece
    for r, c in opp_kings:
        board[r * 8 + c] = opp_king_piece

    legal_moves = get_moves(board, color)
    if not legal_moves:
        # Should not happen if game is ongoing; return a dummy move
        return ((0, 0), (1, 1))

    # Initial move ordering: captures first, then promotions, then advancing non-captures
    def move_key(m):
        start, end, caps = m
        has_cap = 1 if caps else 0
        piece = board[start]
        r_end = end // 8
        promotes = 0
        if piece == my_man_piece:
            if (color == 'w' and r_end == 7) or (color == 'b' and r_end == 0):
                promotes = 1
        adv = 0
        if piece == my_man_piece and not promotes:
            r_start = start // 8
            if color == 'w':
                adv = r_end - r_start
            else:
                adv = r_start - r_end
        return (-has_cap, -promotes, -adv)

    legal_moves.sort(key=move_key)

    best_move = legal_moves[0]
    depth = 1
    max_depth = 20

    try:
        while depth <= max_depth:
            if time.time() - START_TIME > 0.85:
                break
            current_best = None
            alpha = -float('inf')
            beta = float('inf')
            move_scores = []
            for move in legal_moves:
                if time.time() - START_TIME > 0.9:
                    break
                new_board = apply_move(board, move, color)
                score = -negamax(new_board, depth - 1, opponent(color), -beta, -alpha)
                move_scores.append((score, move))
                if score > alpha:
                    alpha = score
                    current_best = move
            # Sort moves by score for next depth
            move_scores.sort(key=lambda x: x[0], reverse=True)
            legal_moves = [m for _, m in move_scores]
            best_move = legal_moves[0]
            depth += 1
    except TimeoutError:
        pass

    start_idx, end_idx, _ = best_move
    return ((start_idx // 8, start_idx % 8), (end_idx // 8, end_idx % 8))
