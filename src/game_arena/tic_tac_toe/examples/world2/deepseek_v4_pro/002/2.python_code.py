
import time
import math

# Custom exception for timeouts
class TimeoutException(Exception):
    pass

# Win masks for 4x4 tic-tac-toe (10 lines)
WIN_MASKS = [
    0x000F, 0x00F0, 0x0F00, 0xF000,  # rows
    0x1111, 0x2222, 0x4444, 0x8888,  # columns
    0x8421, 0x1248                   # diagonals
]

# Heuristic weights: value of having 1, 2, or 3 pieces in a line
WEIGHTS = [0, 1, 10, 100]

def evaluate(my_pieces, opp_pieces):
    """Heuristic evaluation from the perspective of the player owning my_pieces."""
    score = 0
    for mask in WIN_MASKS:
        my_count = (my_pieces & mask).bit_count()
        opp_count = (opp_pieces & mask).bit_count()
        if my_count > 0 and opp_count > 0:
            continue  # line is dead
        elif my_count > 0:
            score += WEIGHTS[my_count]
        elif opp_count > 0:
            score -= WEIGHTS[opp_count]
    return score

def is_win(pieces):
    """Check whether the given bitboard contains a winning line."""
    for mask in WIN_MASKS:
        if (pieces & mask) == mask:
            return True
    return False

def get_legal_moves(my_pieces, opp_pieces):
    """Return a list of empty cell indices (0-15)."""
    empty = ~(my_pieces | opp_pieces) & 0xFFFF
    moves = []
    while empty:
        move = (empty & -empty).bit_length() - 1
        moves.append(move)
        empty &= empty - 1
    return moves

# Transposition table: key -> (flag, value, depth)
# flag: 0=exact, 1=lowerbound, -1=upperbound
TT = {}

def negamax(my_pieces, opp_pieces, depth, alpha, beta):
    """
    Negamax search with alpha-beta pruning.
    my_pieces: bitboard of the player to move.
    opp_pieces: bitboard of the opponent.
    Returns the evaluation from the perspective of the player to move.
    """
    # Check transposition table
    key = (my_pieces, opp_pieces)
    if key in TT:
        flag, tt_value, tt_depth = TT[key]
        if tt_depth >= depth:
            if flag == 0:
                return tt_value
            elif flag == 1:
                alpha = max(alpha, tt_value)
            elif flag == -1:
                beta = min(beta, tt_value)
            if alpha >= beta:
                return tt_value

    # If opponent already won on their last move, this is a loss for us
    if is_win(opp_pieces):
        return -10000 - depth

    if depth == 0:
        return evaluate(my_pieces, opp_pieces)

    # Draw if board full and no winner
    if (my_pieces | opp_pieces) == 0xFFFF:
        return 0

    moves = get_legal_moves(my_pieces, opp_pieces)
    if not moves:
        return 0

    # Move ordering: evaluate immediate wins and heuristic scores
    move_scores = []
    for move in moves:
        new_my = my_pieces | (1 << move)
        if is_win(new_my):
            score = 100000  # always try winning moves first
        else:
            score = evaluate(new_my, opp_pieces)
        move_scores.append((score, move))
    move_scores.sort(reverse=True, key=lambda x: x[0])
    ordered_moves = [m for _, m in move_scores]

    best_value = -math.inf
    flag = -1
    for move in ordered_moves:
        new_my = my_pieces | (1 << move)
        if is_win(new_my):
            value = 10000 + depth
        else:
            value = -negamax(opp_pieces, new_my, depth - 1, -beta, -alpha)
        if value > best_value:
            best_value = value
            flag = 0
        alpha = max(alpha, value)
        if alpha >= beta:
            flag = 1
            break

    TT[key] = (flag, best_value, depth)
    return best_value


def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Given a 4x4 board, return the best move as (row, col).
    Board: 1 = our move, -1 = opponent, 0 = empty.
    """
    # Convert board to bitboards
    my_pieces = 0
    opp_pieces = 0
    for r in range(4):
        for c in range(4):
            idx = r * 4 + c
            if board[r][c] == 1:
                my_pieces |= (1 << idx)
            elif board[r][c] == -1:
                opp_pieces |= (1 << idx)

    start_time = time.time()
    TIME_LIMIT = 0.95

    legal = get_legal_moves(my_pieces, opp_pieces)
    # If only one move, return immediately
    if len(legal) == 1:
        move = legal[0]
        return (move // 4, move % 4)

    # Clear transposition table for the new search
    global TT
    TT.clear()

    best_move = legal[0]
    depth = 1

    try:
        while True:
            if time.time() - start_time > TIME_LIMIT:
                break

            # Order root moves
            move_scores = []
            for move in legal:
                new_my = my_pieces | (1 << move)
                if is_win(new_my):
                    score = 100000
                else:
                    score = evaluate(new_my, opp_pieces)
                move_scores.append((score, move))
            move_scores.sort(reverse=True, key=lambda x: x[0])
            ordered_legal = [m for _, m in move_scores]

            best_value = -math.inf
            current_best = ordered_legal[0]
            alpha = -math.inf
            beta = math.inf

            for move in ordered_legal:
                if time.time() - start_time > TIME_LIMIT:
                    raise TimeoutException()

                new_my = my_pieces | (1 << move)
                if is_win(new_my):
                    value = 10000 + depth
                else:
                    value = -negamax(opp_pieces, new_my, depth - 1, -beta, -alpha)

                if value > best_value:
                    best_value = value
                    current_best = move
                alpha = max(alpha, value)

            best_move = current_best
            depth += 1

            # If a forced win is found, no need to search deeper
            if best_value >= 10000:
                break

    except (TimeoutException, RecursionError):
        pass

    return (best_move // 4, best_move % 4)
