
from functools import lru_cache
from math import inf

N = 4

# Positional preference: center squares are slightly better.
POS_WEIGHTS = (
    (3, 4, 4, 3),
    (4, 5, 5, 4),
    (4, 5, 5, 4),
    (3, 4, 4, 3),
)

LINES = []

# Rows
for r in range(N):
    LINES.append(tuple((r, c) for c in range(N)))
# Cols
for c in range(N):
    LINES.append(tuple((r, c) for r in range(N)))
# Diagonals
LINES.append(tuple((i, i) for i in range(N)))
LINES.append(tuple((i, N - 1 - i) for i in range(N)))


def _flatten(board):
    return tuple(cell for row in board for cell in row)


def _legal_moves(board):
    moves = []
    for r in range(N):
        for c in range(N):
            if board[r][c] == 0:
                moves.append((r, c))
    return moves


def _winner(board):
    for line in LINES:
        s = sum(board[r][c] for r, c in line)
        if s == N:
            return 1
        if s == -N:
            return -1
    return 0


def _is_full(board):
    for r in range(N):
        for c in range(N):
            if board[r][c] == 0:
                return False
    return True


def _immediate_win(board, player):
    for r in range(N):
        for c in range(N):
            if board[r][c] == 0:
                board[r][c] = player
                if _winner(board) == player:
                    board[r][c] = 0
                    return (r, c)
                board[r][c] = 0
    return None


def _count_immediate_wins(board, player):
    count = 0
    for r in range(N):
        for c in range(N):
            if board[r][c] == 0:
                board[r][c] = player
                if _winner(board) == player:
                    count += 1
                board[r][c] = 0
    return count


def _evaluate(board):
    w = _winner(board)
    if w == 1:
        return 100000
    if w == -1:
        return -100000

    score = 0

    # Positional value
    for r in range(N):
        for c in range(N):
            if board[r][c] == 1:
                score += POS_WEIGHTS[r][c]
            elif board[r][c] == -1:
                score -= POS_WEIGHTS[r][c]

    # Line-based value
    for line in LINES:
        vals = [board[r][c] for r, c in line]
        my_count = vals.count(1)
        opp_count = vals.count(-1)
        empty = vals.count(0)

        if my_count > 0 and opp_count > 0:
            continue  # blocked line

        if opp_count == 0:
            if my_count == 3 and empty == 1:
                score += 500
            elif my_count == 2 and empty == 2:
                score += 60
            elif my_count == 1 and empty == 3:
                score += 10
        elif my_count == 0:
            if opp_count == 3 and empty == 1:
                score -= 550
            elif opp_count == 2 and empty == 2:
                score -= 70
            elif opp_count == 1 and empty == 3:
                score -= 10

    # Threats: immediate wins next turn
    my_threats = _count_immediate_wins(board, 1)
    opp_threats = _count_immediate_wins(board, -1)
    score += my_threats * 800
    score -= opp_threats * 900

    return score


def _ordered_moves(board):
    moves = _legal_moves(board)

    def move_key(move):
        r, c = move
        return POS_WEIGHTS[r][c]

    moves.sort(key=move_key, reverse=True)
    return moves


_CACHE = {}


def _board_to_key(board, player, depth):
    return (_flatten(board), player, depth)


def _minimax(board, depth, alpha, beta, player):
    w = _winner(board)
    if w == 1:
        return 100000 + depth
    if w == -1:
        return -100000 - depth
    if depth == 0 or _is_full(board):
        return _evaluate(board)

    key = _board_to_key(board, player, depth)
    if key in _CACHE:
        return _CACHE[key]

    moves = _ordered_moves(board)

    if player == 1:
        best = -inf
        for r, c in moves:
            board[r][c] = 1
            val = _minimax(board, depth - 1, alpha, beta, -1)
            board[r][c] = 0
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
    else:
        best = inf
        for r, c in moves:
            board[r][c] = -1
            val = _minimax(board, depth - 1, alpha, beta, 1)
            board[r][c] = 0
            if val < best:
                best = val
            if best < beta:
                beta = best
            if alpha >= beta:
                break

    _CACHE[key] = best
    return best


def policy(board: list[list[int]]) -> tuple[int, int]:
    moves = _legal_moves(board)
    if not moves:
        return (0, 0)  # Should not happen in valid play, but always return a tuple.

    # 1. Immediate win
    win_move = _immediate_win(board, 1)
    if win_move is not None:
        return win_move

    # 2. Immediate block
    block_move = _immediate_win(board, -1)
    if block_move is not None:
        return block_move

    empties = len(moves)

    # Deeper late-game search, shallower early-game.
    if empties >= 12:
        depth = 4
    elif empties >= 8:
        depth = 5
    elif empties >= 5:
        depth = 7
    else:
        depth = 10

    best_move = None
    best_val = -inf

    ordered = _ordered_moves(board)

    for r, c in ordered:
        board[r][c] = 1

        # If this move creates multiple threats, strongly prefer it.
        if _winner(board) == 1:
            board[r][c] = 0
            return (r, c)

        val = _minimax(board, depth - 1, -inf, inf, -1)
        board[r][c] = 0

        # Small tie-break for positional quality
        val += POS_WEIGHTS[r][c] * 0.01

        if val > best_val or best_move is None:
            best_val = val
            best_move = (r, c)

    if best_move is not None and board[best_move[0]][best_move[1]] == 0:
        return best_move

    # Guaranteed legal fallback
    for r in range(N):
        for c in range(N):
            if board[r][c] == 0:
                return (r, c)

    return (0, 0)
