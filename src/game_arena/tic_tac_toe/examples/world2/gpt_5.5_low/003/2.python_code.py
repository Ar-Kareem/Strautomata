
import time
from math import inf

# All possible 4-in-a-row winning lines on a 4x4 board:
# 4 rows, 4 columns, 2 diagonals.
LINES = (
    ((0, 0), (0, 1), (0, 2), (0, 3)),
    ((1, 0), (1, 1), (1, 2), (1, 3)),
    ((2, 0), (2, 1), (2, 2), (2, 3)),
    ((3, 0), (3, 1), (3, 2), (3, 3)),

    ((0, 0), (1, 0), (2, 0), (3, 0)),
    ((0, 1), (1, 1), (2, 1), (3, 1)),
    ((0, 2), (1, 2), (2, 2), (3, 2)),
    ((0, 3), (1, 3), (2, 3), (3, 3)),

    ((0, 0), (1, 1), (2, 2), (3, 3)),
    ((0, 3), (1, 2), (2, 1), (3, 0)),
)

# Preferred static move order.
# Centers are strongest, then corners, then edges.
PREFERRED_MOVES = (
    (1, 1), (1, 2), (2, 1), (2, 2),
    (0, 0), (0, 3), (3, 0), (3, 3),
    (0, 1), (0, 2), (1, 0), (2, 0),
    (1, 3), (2, 3), (3, 1), (3, 2),
)

WIN_SCORE = 1_000_000
TIME_LIMIT = 0.90


def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Return the next move for player 1 on a 4x4 Tic Tac Toe board.

    board values:
        0  = empty
        1  = us
        -1 = opponent
    """
    start_time = time.perf_counter()
    deadline = start_time + TIME_LIMIT

    try:
        legal = [(r, c) for r in range(4) for c in range(4) if board[r][c] == 0]
        if not legal:
            # Should never happen in a valid call, but return a valid-shaped move.
            return (0, 0)

        # Safe fallback: best static legal move.
        fallback = _first_preferred_legal(board)

        # 1. Take immediate win.
        move = _find_winning_move(board, 1)
        if move is not None:
            return move

        # 2. Block opponent immediate win.
        move = _find_winning_move(board, -1)
        if move is not None:
            return move

        # 3. If board is empty or nearly empty, take a strong central move quickly.
        if len(legal) >= 15:
            return fallback

        best_move = fallback
        cache = {}

        empties = len(legal)

        # Iterative deepening. We keep the best fully completed depth result.
        for depth in range(1, empties + 1):
            if time.perf_counter() > deadline:
                break

            result = _search_root(board, depth, deadline, cache)
            if result is None:
                break

            score, move = result
            if move is not None:
                best_move = move

            # If we found a forced win, no need to search deeper.
            if score >= WIN_SCORE // 2:
                break

        if board[best_move[0]][best_move[1]] == 0:
            return best_move

        return _first_legal(board)

    except Exception:
        # Absolute safety against disqualification.
        return _first_legal(board)


def _first_legal(board):
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                return (r, c)
    return (0, 0)


def _first_preferred_legal(board):
    for r, c in PREFERRED_MOVES:
        if board[r][c] == 0:
            return (r, c)
    return _first_legal(board)


def _winner(board):
    for line in LINES:
        s = 0
        for r, c in line:
            s += board[r][c]
        if s == 4:
            return 1
        if s == -4:
            return -1
    return 0


def _find_winning_move(board, player):
    for r, c in _ordered_moves(board, player):
        board[r][c] = player
        won = _winner(board) == player
        board[r][c] = 0
        if won:
            return (r, c)
    return None


def _search_root(board, depth, deadline, cache):
    alpha = -inf
    beta = inf
    best_score = -inf
    best_move = None

    moves = _ordered_moves(board, 1)

    for r, c in moves:
        if time.perf_counter() > deadline:
            return None

        board[r][c] = 1
        score = _minimax(board, depth - 1, -1, alpha, beta, deadline, cache)
        board[r][c] = 0

        if score is None:
            return None

        if score > best_score:
            best_score = score
            best_move = (r, c)

        alpha = max(alpha, best_score)

    return best_score, best_move


def _minimax(board, depth, player, alpha, beta, deadline, cache):
    if time.perf_counter() > deadline:
        return None

    w = _winner(board)
    if w == 1:
        return WIN_SCORE + depth
    if w == -1:
        return -WIN_SCORE - depth

    legal_count = 0
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                legal_count += 1

    if legal_count == 0:
        return 0

    if depth <= 0:
        return _evaluate(board)

    key = (_board_key(board), player, depth)
    if key in cache:
        return cache[key]

    moves = _ordered_moves(board, player)

    if player == 1:
        value = -inf
        for r, c in moves:
            board[r][c] = 1
            score = _minimax(board, depth - 1, -1, alpha, beta, deadline, cache)
            board[r][c] = 0

            if score is None:
                return None

            if score > value:
                value = score

            alpha = max(alpha, value)
            if alpha >= beta:
                break

    else:
        value = inf
        for r, c in moves:
            board[r][c] = -1
            score = _minimax(board, depth - 1, 1, alpha, beta, deadline, cache)
            board[r][c] = 0

            if score is None:
                return None

            if score < value:
                value = score

            beta = min(beta, value)
            if alpha >= beta:
                break

    cache[key] = value
    return value


def _board_key(board):
    return tuple(
        board[0] + board[1] + board[2] + board[3]
    )


def _ordered_moves(board, player):
    moves = []
    opponent = -player

    for r, c in PREFERRED_MOVES:
        if board[r][c] != 0:
            continue

        priority = 0

        # Prefer immediate wins very highly.
        board[r][c] = player
        if _winner(board) == player:
            priority += 100000
        board[r][c] = 0

        # Prefer blocking opponent wins.
        board[r][c] = opponent
        if _winner(board) == opponent:
            priority += 90000
        board[r][c] = 0

        # Prefer moves participating in promising lines.
        priority += _move_potential(board, r, c, player)

        # Static positional preference.
        if (r, c) in ((1, 1), (1, 2), (2, 1), (2, 2)):
            priority += 50
        elif (r, c) in ((0, 0), (0, 3), (3, 0), (3, 3)):
            priority += 25
        else:
            priority += 10

        moves.append((priority, r, c))

    moves.sort(reverse=True)
    return [(r, c) for _, r, c in moves]


def _move_potential(board, r, c, player):
    score = 0
    opponent = -player

    for line in LINES:
        if (r, c) not in line:
            continue

        own = 0
        opp = 0

        for rr, cc in line:
            v = board[rr][cc]
            if v == player:
                own += 1
            elif v == opponent:
                opp += 1

        if opp == 0:
            score += (own + 1) ** 3
        if own == 0:
            score += (opp + 1) ** 3

    return score


def _evaluate(board):
    """
    Positive is good for us, negative is good for opponent.
    """
    score = 0

    # Line weights.
    # 3 in an open line is extremely important on a 4x4 board.
    weights = [0, 3, 25, 1200, WIN_SCORE]

    for line in LINES:
        own = 0
        opp = 0

        for r, c in line:
            v = board[r][c]
            if v == 1:
                own += 1
            elif v == -1:
                opp += 1

        if own and opp:
            continue

        if own:
            score += weights[own]
        elif opp:
            # Slightly overweight opponent threats to encourage safe play.
            score -= int(weights[opp] * 1.15)

    # Small positional bonus.
    for r, c in ((1, 1), (1, 2), (2, 1), (2, 2)):
        if board[r][c] == 1:
            score += 8
        elif board[r][c] == -1:
            score -= 8

    for r, c in ((0, 0), (0, 3), (3, 0), (3, 3)):
        if board[r][c] == 1:
            score += 4
        elif board[r][c] == -1:
            score -= 4

    return score
