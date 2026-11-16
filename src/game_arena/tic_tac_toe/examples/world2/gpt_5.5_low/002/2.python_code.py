
import time

BOARD_SIZE = 4
EMPTY = 0
ME = 1
OPP = -1

# All winning lines for standard 4x4 Tic Tac Toe: 4 rows, 4 cols, 2 diagonals.
LINES = [
    [(0, 0), (0, 1), (0, 2), (0, 3)],
    [(1, 0), (1, 1), (1, 2), (1, 3)],
    [(2, 0), (2, 1), (2, 2), (2, 3)],
    [(3, 0), (3, 1), (3, 2), (3, 3)],

    [(0, 0), (1, 0), (2, 0), (3, 0)],
    [(0, 1), (1, 1), (2, 1), (3, 1)],
    [(0, 2), (1, 2), (2, 2), (3, 2)],
    [(0, 3), (1, 3), (2, 3), (3, 3)],

    [(0, 0), (1, 1), (2, 2), (3, 3)],
    [(0, 3), (1, 2), (2, 1), (3, 0)],
]

# Slight preference for central-ish squares.
POSITION_VALUE = [
    [3, 4, 4, 3],
    [4, 6, 6, 4],
    [4, 6, 6, 4],
    [3, 4, 4, 3],
]

WIN_SCORE = 1_000_000
TIME_LIMIT = 0.85


class Timeout(Exception):
    pass


def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Return a legal move for a 4x4 Tic Tac Toe board.
    0 = empty, 1 = us, -1 = opponent.
    """

    start_time = time.perf_counter()
    deadline = start_time + TIME_LIMIT

    empties = [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) if board[r][c] == EMPTY]

    # Absolute safety fallback.
    if not empties:
        return (0, 0)

    fallback = ordered_moves(board, ME)[0] if empties else empties[0]

    # 1. Immediate win.
    for r, c in empties:
        board[r][c] = ME
        if winner(board) == ME:
            board[r][c] = EMPTY
            return (r, c)
        board[r][c] = EMPTY

    # 2. Immediate block.
    for r, c in empties:
        board[r][c] = OPP
        if winner(board) == OPP:
            board[r][c] = EMPTY
            return (r, c)
        board[r][c] = EMPTY

    transposition = {}

    def check_time():
        if time.perf_counter() >= deadline:
            raise Timeout()

    def board_key():
        return tuple(tuple(row) for row in board)

    def evaluate(side: int) -> int:
        """
        Static evaluation from the perspective of 'side'.
        Positive is good for 'side'.
        """
        w = winner(board)
        if w == side:
            return WIN_SCORE
        if w == -side:
            return -WIN_SCORE

        score = 0

        # Line-based evaluation.
        # Open lines with 1,2,3 marks become increasingly valuable.
        weights = [0, 2, 20, 250, WIN_SCORE]

        for line in LINES:
            side_count = 0
            opp_count = 0
            for r, c in line:
                if board[r][c] == side:
                    side_count += 1
                elif board[r][c] == -side:
                    opp_count += 1

            if side_count and opp_count:
                continue
            if side_count:
                score += weights[side_count]
            elif opp_count:
                score -= weights[opp_count]

        # Positional bonus.
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board[r][c] == side:
                    score += POSITION_VALUE[r][c]
                elif board[r][c] == -side:
                    score -= POSITION_VALUE[r][c]

        return score

    def negamax(depth: int, alpha: int, beta: int, side: int) -> int:
        check_time()

        w = winner(board)
        if w == side:
            return WIN_SCORE + depth
        if w == -side:
            return -WIN_SCORE - depth

        moves = ordered_moves(board, side)
        if not moves:
            return 0

        if depth <= 0:
            return evaluate(side)

        key = (board_key(), depth, side)
        if key in transposition:
            return transposition[key]

        best = -10**18

        for r, c in moves:
            board[r][c] = side
            val = -negamax(depth - 1, -beta, -alpha, -side)
            board[r][c] = EMPTY

            if val > best:
                best = val
            if val > alpha:
                alpha = val
            if alpha >= beta:
                break

        transposition[key] = best
        return best

    best_move = fallback
    max_depth = len(empties)

    # Iterative deepening: always keep the best fully completed depth.
    try:
        for depth in range(1, max_depth + 1):
            check_time()

            current_best = best_move
            current_score = -10**18
            alpha = -10**18
            beta = 10**18

            for r, c in ordered_moves(board, ME):
                check_time()

                board[r][c] = ME
                score = -negamax(depth - 1, -beta, -alpha, OPP)
                board[r][c] = EMPTY

                if score > current_score:
                    current_score = score
                    current_best = (r, c)

                if score > alpha:
                    alpha = score

            best_move = current_best

            # If we found a forced win, no need to search deeper.
            if current_score >= WIN_SCORE:
                break

    except Timeout:
        pass

    # Final legality check.
    r, c = best_move
    if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == EMPTY:
        return best_move

    # Emergency legal fallback.
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == EMPTY:
                return (r, c)

    return (0, 0)


def winner(board: list[list[int]]) -> int:
    """
    Return 1 if player 1 has won, -1 if player -1 has won, otherwise 0.
    """
    for line in LINES:
        total = 0
        for r, c in line:
            total += board[r][c]
        if total == 4:
            return 1
        if total == -4:
            return -1
    return 0


def ordered_moves(board: list[list[int]], side: int) -> list[tuple[int, int]]:
    """
    Produce tactically ordered legal moves.
    Winning moves first, then blocks, then high-potential/central moves.
    """
    moves = []

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != EMPTY:
                continue

            score = POSITION_VALUE[r][c]

            # Prefer moves that immediately win.
            board[r][c] = side
            if winner(board) == side:
                score += 100_000
            board[r][c] = EMPTY

            # Prefer moves that block opponent's immediate win.
            board[r][c] = -side
            if winner(board) == -side:
                score += 90_000
            board[r][c] = EMPTY

            # Add local line potential.
            for line in LINES:
                if (r, c) not in line:
                    continue

                own = 0
                opp = 0
                empty = 0

                for rr, cc in line:
                    val = board[rr][cc]
                    if val == side:
                        own += 1
                    elif val == -side:
                        opp += 1
                    else:
                        empty += 1

                if opp == 0:
                    score += [0, 5, 30, 300, 0][own]
                if own == 0:
                    score += [0, 4, 25, 250, 0][opp]

            moves.append((score, r, c))

    moves.sort(reverse=True)
    return [(r, c) for _, r, c in moves]
