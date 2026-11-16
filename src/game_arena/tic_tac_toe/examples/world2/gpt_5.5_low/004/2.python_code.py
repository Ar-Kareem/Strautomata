
import time
from typing import List, Tuple

N = 4

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

POSITION_WEIGHTS = [
    [3, 4, 4, 3],
    [4, 7, 7, 4],
    [4, 7, 7, 4],
    [3, 4, 4, 3],
]

WIN_SCORE = 1_000_000
TIME_LIMIT = 0.92


class TimeoutSearch(Exception):
    pass


def policy(board: List[List[int]]) -> Tuple[int, int]:
    start_time = time.time()

    try:
        legal = [(r, c) for r in range(N) for c in range(N) if board[r][c] == 0]
        if not legal:
            return (0, 0)

        if len(legal) == 16:
            return (1, 1)

        # Immediate winning move.
        move = find_immediate_move(board, 1)
        if move is not None:
            return move

        # Immediate block.
        move = find_immediate_move(board, -1)
        if move is not None:
            return move

        # Strong tactical preference: create or block many 3-in-a-row threats.
        tactical = best_tactical_move(board, legal)
        if tactical is not None:
            return tactical

        best_move = order_moves(board, legal, 1)[0]
        cache = {}

        empties = len(legal)

        if empties >= 13:
            max_depth = 5
        elif empties >= 10:
            max_depth = 7
        else:
            max_depth = empties

        for depth in range(1, max_depth + 1):
            if time.time() - start_time > TIME_LIMIT:
                break

            current_best = best_move
            current_score = -10**18
            alpha = -10**18
            beta = 10**18

            ordered = order_moves(board, legal, 1)

            for r, c in ordered:
                if time.time() - start_time > TIME_LIMIT:
                    raise TimeoutSearch()

                board[r][c] = 1
                score = alphabeta(board, depth - 1, alpha, beta, -1, start_time, cache)
                board[r][c] = 0

                if score > current_score:
                    current_score = score
                    current_best = (r, c)

                alpha = max(alpha, current_score)

            best_move = current_best

            if current_score >= WIN_SCORE // 2:
                break

        if is_legal(board, best_move):
            return best_move

    except Exception:
        pass

    # Absolute safety fallback.
    for r in range(N):
        for c in range(N):
            if board[r][c] == 0:
                return (r, c)

    return (0, 0)


def alphabeta(board, depth, alpha, beta, turn, start_time, cache):
    if time.time() - start_time > TIME_LIMIT:
        raise TimeoutSearch()

    winner = check_winner(board)
    if winner == 1:
        return WIN_SCORE + depth
    if winner == -1:
        return -WIN_SCORE - depth

    legal = [(r, c) for r in range(N) for c in range(N) if board[r][c] == 0]

    if not legal:
        return evaluate(board)

    if depth <= 0:
        return evaluate(board)

    key = (tuple(cell for row in board for cell in row), depth, turn)
    cached = cache.get(key)
    if cached is not None:
        return cached

    ordered = order_moves(board, legal, turn)

    if turn == 1:
        value = -10**18

        for r, c in ordered:
            board[r][c] = 1
            value = max(value, alphabeta(board, depth - 1, alpha, beta, -1, start_time, cache))
            board[r][c] = 0

            alpha = max(alpha, value)
            if alpha >= beta:
                break

    else:
        value = 10**18

        for r, c in ordered:
            board[r][c] = -1
            value = min(value, alphabeta(board, depth - 1, alpha, beta, 1, start_time, cache))
            board[r][c] = 0

            beta = min(beta, value)
            if alpha >= beta:
                break

    cache[key] = value
    return value


def check_winner(board):
    for line in LINES:
        s = 0
        for r, c in line:
            s += board[r][c]
        if s == 4:
            return 1
        if s == -4:
            return -1
    return 0


def find_immediate_move(board, side):
    for r in range(N):
        for c in range(N):
            if board[r][c] == 0:
                board[r][c] = side
                if check_winner(board) == side:
                    board[r][c] = 0
                    return (r, c)
                board[r][c] = 0
    return None


def best_tactical_move(board, legal):
    best = None
    best_score = 0

    for r, c in legal:
        board[r][c] = 1
        my_threats = count_open_threes(board, 1)
        my_twos = count_open_twos(board, 1)
        board[r][c] = 0

        board[r][c] = -1
        opp_threats_after = count_open_threes(board, -1)
        board[r][c] = 0

        score = my_threats * 100 + my_twos * 10 - opp_threats_after * 80 + POSITION_WEIGHTS[r][c]

        if score > best_score:
            best_score = score
            best = (r, c)

    if best_score >= 100:
        return best

    return None


def count_open_threes(board, side):
    count = 0
    for line in LINES:
        own = 0
        empty = 0
        blocked = False

        for r, c in line:
            v = board[r][c]
            if v == side:
                own += 1
            elif v == 0:
                empty += 1
            else:
                blocked = True
                break

        if not blocked and own == 3 and empty == 1:
            count += 1

    return count


def count_open_twos(board, side):
    count = 0
    for line in LINES:
        own = 0
        empty = 0
        blocked = False

        for r, c in line:
            v = board[r][c]
            if v == side:
                own += 1
            elif v == 0:
                empty += 1
            else:
                blocked = True
                break

        if not blocked and own == 2 and empty == 2:
            count += 1

    return count


def evaluate(board):
    winner = check_winner(board)
    if winner == 1:
        return WIN_SCORE
    if winner == -1:
        return -WIN_SCORE

    score = 0

    for line in LINES:
        own = 0
        opp = 0
        empty = 0

        for r, c in line:
            v = board[r][c]
            if v == 1:
                own += 1
            elif v == -1:
                opp += 1
            else:
                empty += 1

        if own and opp:
            continue

        if own:
            if own == 1:
                score += 6
            elif own == 2:
                score += 45
            elif own == 3:
                score += 700
            elif own == 4:
                score += WIN_SCORE
        elif opp:
            if opp == 1:
                score -= 7
            elif opp == 2:
                score -= 55
            elif opp == 3:
                score -= 900
            elif opp == 4:
                score -= WIN_SCORE
        else:
            score += 1

    for r in range(N):
        for c in range(N):
            if board[r][c] == 1:
                score += POSITION_WEIGHTS[r][c]
            elif board[r][c] == -1:
                score -= POSITION_WEIGHTS[r][c]

    score += 120 * count_open_threes(board, 1)
    score -= 150 * count_open_threes(board, -1)
    score += 20 * count_open_twos(board, 1)
    score -= 25 * count_open_twos(board, -1)

    return score


def order_moves(board, legal, turn):
    scored = []

    for r, c in legal:
        score = POSITION_WEIGHTS[r][c]

        board[r][c] = turn

        if check_winner(board) == turn:
            score += 100000

        if turn == 1:
            score += 120 * count_open_threes(board, 1)
            score += 20 * count_open_twos(board, 1)
            score -= 80 * count_open_threes(board, -1)
        else:
            score += 120 * count_open_threes(board, -1)
            score += 20 * count_open_twos(board, -1)
            score -= 80 * count_open_threes(board, 1)

        board[r][c] = 0

        # Prefer moves that also block opponent wins/threats.
        board[r][c] = -turn
        if check_winner(board) == -turn:
            score += 90000
        board[r][c] = 0

        scored.append((score, r, c))

    reverse = True
    scored.sort(reverse=reverse)

    return [(r, c) for _, r, c in scored]


def is_legal(board, move):
    if not isinstance(move, tuple) or len(move) != 2:
        return False

    r, c = move

    return (
        isinstance(r, int)
        and isinstance(c, int)
        and 0 <= r < N
        and 0 <= c < N
        and board[r][c] == 0
    )
