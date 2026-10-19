
import time
from typing import List, Tuple

# Policy function required by the arena
def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Choose a move for 4x4 Tic-Tac-Toe.
    board: 4x4 list of lists with 0 (empty), 1 (us), -1 (opponent)
    returns: (row, col)
    """
    SIZE = 4
    # Precompute all winning lines (length 4)
    LINES = []
    # rows
    for r in range(SIZE):
        LINES.append([(r, c) for c in range(SIZE)])
    # cols
    for c in range(SIZE):
        LINES.append([(r, c) for r in range(SIZE)])
    # main diag
    LINES.append([(i, i) for i in range(SIZE)])
    # anti diag
    LINES.append([(i, SIZE - 1 - i) for i in range(SIZE)])

    INF = 10**9

    # Helpers
    def check_winner(bd: List[List[int]]) -> int:
        # return 1 if we win, -1 if opponent wins, 0 otherwise
        for line in LINES:
            s = sum(bd[r][c] for (r, c) in line)
            if s == SIZE:
                return 1
            if s == -SIZE:
                return -1
        return 0

    def is_full(bd: List[List[int]]) -> bool:
        for r in range(SIZE):
            for c in range(SIZE):
                if bd[r][c] == 0:
                    return False
        return True

    def heuristic(bd: List[List[int]]) -> int:
        # Positive is good for us, negative good for opponent.
        w = check_winner(bd)
        if w != 0:
            return INF if w == 1 else -INF
        score = 0
        for line in LINES:
            cnt1 = 0
            cntm1 = 0
            for (r, c) in line:
                if bd[r][c] == 1:
                    cnt1 += 1
                elif bd[r][c] == -1:
                    cntm1 += 1
            if cnt1 > 0 and cntm1 > 0:
                continue
            if cnt1 > 0:
                # exponential weight for progress
                score += 10 ** cnt1
            elif cntm1 > 0:
                score -= 10 ** cntm1
        return score

    # Collect empty cells
    empties = [(r, c) for r in range(SIZE) for c in range(SIZE) if board[r][c] == 0]

    # Immediate win
    for (r, c) in empties:
        board[r][c] = 1
        if check_winner(board) == 1:
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0
    # Immediate block
    for (r, c) in empties:
        board[r][c] = -1
        if check_winner(board) == -1:
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0

    # If no empties, just return a dummy (shouldn't happen normally)
    if not empties:
        return (0, 0)

    # Set search depth depending on empties (deeper near endgame)
    remaining = len(empties)
    if remaining <= 4:
        max_depth = remaining  # full search
    elif remaining <= 8:
        max_depth = 6
    else:
        max_depth = 4

    # Time limit safety
    t_start = time.time()
    TIME_LIMIT = 0.9  # seconds

    # Transposition table: map from tuple(board) to (depth, value)
    tt = {}

    def board_key(bd: List[List[int]]) -> Tuple[int, ...]:
        return tuple(v for row in bd for v in row)

    def negamax(depth: int, alpha: int, beta: int, turn: int) -> int:
        # turn: 1 if AI to move, -1 if opponent to move
        # Returns evaluation from AI perspective (higher is better for AI)
        # Time check
        if time.time() - t_start > TIME_LIMIT:
            # return heuristic early if out of time
            return heuristic(board)

        key = (board_key(board), depth, turn)
        if key in tt:
            return tt[key]

        w = check_winner(board)
        if w != 0:
            val = INF if w == 1 else -INF
            tt[key] = val
            return val
        if is_full(board) or depth == 0:
            val = heuristic(board)
            tt[key] = val
            return val

        best = -INF
        # Generate moves and order them by static eval after move (descending)
        moves = []
        for (r, c) in [(r, c) for r in range(SIZE) for c in range(SIZE) if board[r][c] == 0]:
            board[r][c] = turn
            val = heuristic(board)
            moves.append(((r, c), val))
            board[r][c] = 0
        # sort by heuristic descending (prefer promising moves)
        moves.sort(key=lambda x: x[1], reverse=True)

        for (r, c), _ in moves:
            board[r][c] = turn
            val = -negamax(depth - 1, -beta, -alpha, -turn)
            board[r][c] = 0
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break

        # If no legal moves (should be handled above), return heuristic
        if best == -INF:
            best = heuristic(board)

        tt[key] = best
        return best

    # Root search to pick the best move
    best_move = None
    best_val = -INF
    alpha = -INF
    beta = INF

    # Root move ordering: same idea as in negamax
    root_moves = []
    for (r, c) in empties:
        board[r][c] = 1
        val = heuristic(board)
        root_moves.append(((r, c), val))
        board[r][c] = 0
    root_moves.sort(key=lambda x: x[1], reverse=True)

    for (r, c), _ in root_moves:
        if time.time() - t_start > TIME_LIMIT:
            break
        board[r][c] = 1
        val = -negamax(max_depth - 1, -beta, -alpha, -1)
        board[r][c] = 0
        if val > best_val:
            best_val = val
            best_move = (r, c)
        if best_val > alpha:
            alpha = best_val

    # If no best_move selected due to timeout, fall back to heuristic pick
    if best_move is None:
        # pick the empty move with maximum immediate heuristic
        best_move = max(empties, key=lambda pos: heuristic_with_move(board, pos))

    return best_move

# Helper used in fallback (placed after function to keep policy signature clean)
def heuristic_with_move(board: List[List[int]], move: Tuple[int, int]) -> int:
    r, c = move
    board[r][c] = 1
    # Simple local heuristic: count lines improved
    SIZE = 4
    lines = []
    for rr in range(SIZE):
        lines.append([(rr, cc) for cc in range(SIZE)])
    for cc in range(SIZE):
        lines.append([(rr, cc) for rr in range(SIZE)])
    lines.append([(i, i) for i in range(SIZE)])
    lines.append([(i, SIZE - 1 - i) for i in range(SIZE)])
    score = 0
    for line in lines:
        cnt1 = 0
        cntm1 = 0
        for (rr, cc) in line:
            if board[rr][cc] == 1:
                cnt1 += 1
            elif board[rr][cc] == -1:
                cntm1 += 1
        if cnt1 > 0 and cntm1 > 0:
            continue
        if cnt1 > 0:
            score += 10 ** cnt1
        elif cntm1 > 0:
            score -= 10 ** cntm1
    board[r][c] = 0
    return score
