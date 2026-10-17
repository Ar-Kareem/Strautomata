
import time
import math

# All 10 winning lines as flat indices (0-15)
LINES = [
    [0, 1, 2, 3],      # row 0
    [4, 5, 6, 7],      # row 1
    [8, 9, 10, 11],    # row 2
    [12, 13, 14, 15],  # row 3
    [0, 4, 8, 12],     # col 0
    [1, 5, 9, 13],     # col 1
    [2, 6, 10, 14],    # col 2
    [3, 7, 11, 15],    # col 3
    [0, 5, 10, 15],    # main diagonal
    [3, 6, 9, 12]      # anti-diagonal
]

# Static evaluation weights
WEIGHTS = {1: 1, 2: 10, 3: 100, 4: 10000}

# Board zones for basic move ordering
CENTER = {5, 6, 9, 10}
CORNERS = {0, 3, 12, 15}
EDGES = {1, 2, 4, 7, 8, 11, 13, 14}


class TimeoutError(Exception):
    """Raised when the time limit is exceeded."""
    pass


def check_winner(cells):
    """Return 1 if '1' wins, -1 if '-1' wins, else 0."""
    for line in LINES:
        vals = [cells[i] for i in line]
        if all(v == 1 for v in vals):
            return 1
        if all(v == -1 for v in vals):
            return -1
    return 0


def evaluate(cells):
    """Heuristic evaluation of the board from X's perspective."""
    score = 0
    for line in LINES:
        vals = [cells[i] for i in line]
        # Line is dead if both players occupy it
        if 1 in vals and -1 in vals:
            continue
        count_1 = vals.count(1)
        count_m1 = vals.count(-1)
        if count_1 > 0:
            score += WEIGHTS[count_1]
        elif count_m1 > 0:
            score -= WEIGHTS[count_m1]
    return score


def minimax(cells, depth, alpha, beta, maximizing, start_time):
    """Alpha-beta minimax with time checks and limited depth."""
    # Time enforcement
    if time.time() - start_time > 0.95:
        raise TimeoutError()

    winner = check_winner(cells)
    if winner == 1:
        return 10000 + depth  # earlier win is better
    if winner == -1:
        return -10000 - depth
    if depth == 0:
        return evaluate(cells)

    empty = [i for i in range(16) if cells[i] == 0]
    if not empty:
        return 0  # draw

    if maximizing:
        # Move ordering: immediate wins, then center, corners, edges
        def key(m):
            new = list(cells)
            new[m] = 1
            if check_winner(tuple(new)) == 1:
                return -1
            if m in CENTER: return 0
            if m in CORNERS: return 1
            return 2
        ordered = sorted(empty, key=key)
        max_eval = -math.inf
        for move in ordered:
            new = list(cells)
            new[move] = 1
            val = minimax(tuple(new), depth - 1, alpha, beta, False, start_time)
            max_eval = max(max_eval, val)
            alpha = max(alpha, val)
            if beta <= alpha:
                break
        return max_eval
    else:
        # Move ordering: immediate opponent wins, then center, corners, edges
        def key(m):
            new = list(cells)
            new[m] = -1
            if check_winner(tuple(new)) == -1:
                return -1
            if m in CENTER: return 0
            if m in CORNERS: return 1
            return 2
        ordered = sorted(empty, key=key)
        min_eval = math.inf
        for move in ordered:
            new = list(cells)
            new[move] = -1
            val = minimax(tuple(new), depth - 1, alpha, beta, True, start_time)
            min_eval = min(min_eval, val)
            beta = min(beta, val)
            if beta <= alpha:
                break
        return min_eval


def policy(board: list[list[int]]) -> tuple[int, int]:
    """Main policy: receives 4x4 board, returns (row, col)."""
    # Flatten the board into a 16-element tuple
    cells = tuple(board[i][j] for i in range(4) for j in range(4))

    empty = [i for i in range(16) if cells[i] == 0]
    if len(empty) == 1:
        # Only one move left – play it instantly
        return (empty[0] // 4, empty[0] % 4)

    start_time = time.time()

    # Immediate winning move
    for move in empty:
        new = list(cells)
        new[move] = 1
        if check_winner(tuple(new)) == 1:
            return (move // 4, move % 4)

    # Opponent's immediate winning move must be blocked
    for move in empty:
        new = list(cells)
        new[move] = -1
        if check_winner(tuple(new)) == -1:
            return (move // 4, move % 4)

    # Basic static ordering for the root (center > corners > edges)
    def move_key(m):
        if m in CENTER: return 0
        if m in CORNERS: return 1
        return 2
    ordered_moves = sorted(empty, key=move_key)

    best_move = ordered_moves[0]
    depth = 1
    max_depth = len(empty)

    while depth <= max_depth:
        current_best_move = best_move
        current_best_score = -math.inf
        alpha = -math.inf
        beta = math.inf
        try:
            for move in ordered_moves:
                new = list(cells)
                new[move] = 1
                score = minimax(tuple(new), depth - 1, alpha, beta, False, start_time)
                if score > current_best_score:
                    current_best_score = score
                    current_best_move = move
                alpha = max(alpha, score)
        except TimeoutError:
            # Keep the move from the last fully completed depth
            break

        # Update best move only if we finished the iteration
        best_move = current_best_move

        # If we found a forced win, no need to search deeper
        if current_best_score >= 10000:
            break
        # If we are running out of time, stop deepening
        if time.time() - start_time > 0.8:
            break
        depth += 1

    return (best_move // 4, best_move % 4)
