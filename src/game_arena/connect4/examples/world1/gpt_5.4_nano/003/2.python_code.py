
import math
import random
from functools import lru_cache

ROWS = 6
COLS = 7
CONNECT_N = 4

# Precompute all line segments (for evaluation)
LINES = []
# Horizontal
for r in range(ROWS):
    for c in range(COLS - CONNECT_N + 1):
        LINES.append([(r, c+i) for i in range(CONNECT_N)])
# Vertical
for c in range(COLS):
    for r in range(ROWS - CONNECT_N + 1):
        LINES.append([(r+i, c) for i in range(CONNECT_N)])
# Diagonal down-right
for r in range(ROWS - CONNECT_N + 1):
    for c in range(COLS - CONNECT_N + 1):
        LINES.append([(r+i, c+i) for i in range(CONNECT_N)])
# Diagonal up-right
for r in range(CONNECT_N - 1, ROWS):
    for c in range(COLS - CONNECT_N + 1):
        LINES.append([(r-i, c+i) for i in range(CONNECT_N)])


def legal_moves(board):
    return [c for c in range(COLS) if board[0][c] == 0]


def next_row(board, col):
    for r in range(ROWS-1, -1, -1):
        if board[r][col] == 0:
            return r
    return None


def apply_move(board, col, player):
    r = next_row(board, col)
    if r is None:
        return None
    newb = [row[:] for row in board]
    newb[r][col] = player
    return newb


def is_win(board, player):
    # Check all lines
    for line in LINES:
        if all(board[r][c] == player for r, c in line):
            return True
    return False


def board_key(board):
    # Small board; string key is fine
    return tuple(tuple(row) for row in board)


def evaluate_board(board, me):
    """
    Heuristic: score based on all 4-length segments.
    me is either 1 or -1 (current player perspective).
    Opponent is -me.
    """
    opp = -me
    score = 0

    # Center preference
    center_col = COLS // 2
    center_weight = 6
    center_count = sum(1 for r in range(ROWS) if board[r][center_col] == me)
    score += center_weight * center_count
    center_count_opp = sum(1 for r in range(ROWS) if board[r][center_col] == opp)
    score -= center_weight * center_count_opp

    # Segment scoring
    # For each segment of length 4:
    # - If segment contains only my discs and empties: reward based on #my
    # - If segment contains only opp discs and empties: penalize based on #opp
    # - If mixed: ignore (neutral)
    weights = {0: 0, 1: 1, 2: 8, 3: 60, 4: 10_000}
    for line in LINES:
        vals = [board[r][c] for r, c in line]
        if opp not in vals:
            cnt_me = vals.count(me)
            score += weights[cnt_me]
        elif me not in vals:
            cnt_opp = vals.count(opp)
            score -= weights[cnt_opp] * 1.05  # slight extra penalty vs opponent
        # else mixed: no direct contribution

    # Additional subtlety: prefer moves that create "immediate next threats"
    # (e.g., segments where we have 3 and one empty and opponent doesn't block).
    # This is already captured by weights[3], but we can add small bias for empties.
    # We'll add a tiny term for potential "open threes".
    def open_three(player):
        total = 0
        for line in LINES:
            vals = [board[r][c] for r, c in line]
            if opp in vals:
                continue
            cnt_p = vals.count(player)
            cnt_0 = vals.count(0)
            if cnt_p == 3 and cnt_0 == 1:
                # ensure empty is actually playable soon? approximate by counting empties lower bias
                # We'll just count.
                total += 1
        return total

    open3_me = open_three(me)
    open3_opp = open_three(opp)
    score += 25 * open3_me
    score -= 25 * open3_opp

    return score


def order_moves(board, moves, me):
    """
    Move ordering for alpha-beta: center first and also consider immediate tactical gain.
    """
    # Prefer columns closer to center
    center = COLS // 2
    scored = []
    for c in moves:
        # quick tactic: winning move
        nb = apply_move(board, c, me)
        if nb is None:
            continue
        if is_win(nb, me):
            return [c]  # highest priority
        # block win (opponent win next)
        # if we don't block, opponent could win immediately
        # (approx by checking if opponent has a winning move after we play)
        opp = -me
        opp_moves = legal_moves(nb)
        blocks = 0
        for oc in opp_moves:
            nb2 = apply_move(nb, oc, opp)
            if nb2 is not None and is_win(nb2, opp):
                blocks = 1
                break
        # evaluate for ordering
        base = -abs(c - center)
        # small add for heuristic value
        sc = base * 2 + (50 if blocks else 0) + evaluate_board(nb, me) * 0.001
        scored.append((sc, c))
    scored.sort(reverse=True)
    return [c for _, c in scored]


def minimax(board, depth, alpha, beta, me):
    """
    Alpha-beta minimax for current player 'me' to move.
    Board contains 1, -1, 0 with respect to absolute players; me is current player's value.
    """
    moves = legal_moves(board)
    if not moves:
        return 0, None

    # Terminal checks
    if is_win(board, me):
        return 1_000_000, None
    if is_win(board, -me):
        return -1_000_000, None
    if depth == 0:
        return evaluate_board(board, me), None

    best_move = None
    ordered = order_moves(board, moves, me)

    # Make sure we also consider immediate win/block at deeper nodes (still handled by ordering + eval)
    for c in ordered:
        nb = apply_move(board, c, me)
        if nb is None:
            continue
        # Next player
        val, _ = minimax(nb, depth - 1, alpha, beta, -me)
        val = -val  # because perspective flips

        if val > alpha:
            alpha = val
            best_move = c
        if alpha >= beta:
            break

    return alpha, best_move


def policy(board: list[list[int]]) -> int:
    """
    Return a legal column index (0-6) for the current player.
    """
    # Determine which value represents "our discs" in this board.
    # By problem statement, we are always the current player when called,
    # but encoding uses 1 for "your disc (current player)" and -1 for opponent.
    me = 1

    moves = legal_moves(board)
    if not moves:
        # Shouldn't happen; but return something legal if possible
        return 0

    # 1) Immediate win
    for c in moves:
        nb = apply_move(board, c, me)
        if nb is not None and is_win(nb, me):
            return c

    # 2) Immediate block opponent win
    opp = -me
    for c in moves:
        # If we play c, does opponent have a winning response? If yes, c is a block candidate.
        nb = apply_move(board, c, me)
        if nb is None:
            continue
        opp_can_win = False
        for oc in legal_moves(nb):
            nb2 = apply_move(nb, oc, opp)
            if nb2 is not None and is_win(nb2, opp):
                opp_can_win = True
                break
        if not opp_can_win:
            # But we should specifically block if opponent wins next.
            # Better: find any move that prevents all immediate opponent wins.
            # We'll use this as a blocking criterion.
            return c

    # If above didn't return, we did not find a "safe" move by that logic.
    # We can instead do an explicit best block: if opponent can win in one,
    # choose a move that blocks at least one winning line.
    # Check opponent immediate win columns on current board:
    opp_win_cols = []
    for oc in legal_moves(board):
        nb2 = apply_move(board, oc, opp)
        if nb2 is not None and is_win(nb2, opp):
            opp_win_cols.append(oc)

    if opp_win_cols:
        # Try to find a move that blocks the most critical opponent winning placements.
        # Since moves drop discs, exact blocking requires simulation.
        best_block = None
        best_block_score = -math.inf
        for c in moves:
            nb = apply_move(board, c, me)
            if nb is None:
                continue
            # how many of opp_win_cols are still available as immediate wins?
            remaining_wins = 0
            for oc in legal_moves(nb):
                nb2 = apply_move(nb, oc, opp)
                if nb2 is not None and is_win(nb2, opp):
                    remaining_wins += 1
            # Lower remaining_wins is better; break ties by evaluation.
            sc = -1000 * remaining_wins + evaluate_board(nb, me) * 0.01
            if sc > best_block_score:
                best_block_score = sc
                best_block = c
        if best_block is not None:
            return best_block

    # 3) Depth-limited minimax with alpha-beta
    # Choose depth based on game phase: more empties -> deeper possible, else shallower.
    empties = sum(1 for r in range(ROWS) for c in range(COLS) if board[r][c] == 0)
    if empties > 28:
        depth = 5
    elif empties > 18:
        depth = 6  # still usually fine for 7x6 with ordering
    else:
        depth = 5

    # Add slight randomness to break symmetry among equally good moves
    # while keeping determinism mostly.
    # We'll also cache via local memoization keyed by board and depth.
    @lru_cache(maxsize=50_000)
    def mm_cached(bkey, depth_left, alpha, beta, turn):
        # alpha and beta are not suitable for caching with those exact values,
        # so avoid caching alpha/beta; implement non-cached minimax below instead.
        # This placeholder won't be used; kept to avoid accidental complexity.
        return 0, None

    # Run minimax without caching alpha/beta (fast enough with ordering and depth limits)
    _, best = minimax(board, depth, -math.inf, math.inf, me)
    if best in moves:
        return best

    # 4) Fallback: choose best heuristic move
    best_move = moves[0]
    best_val = -math.inf
    ordered = order_moves(board, moves, me)
    for c in ordered:
        nb = apply_move(board, c, me)
        if nb is None:
            continue
        v = evaluate_board(nb, me)
        # small tiebreaker favor closer to center
        v += 0.001 * (-abs(c - (COLS // 2)))
        if v > best_val:
            best_val = v
            best_move = c
    return best_move
