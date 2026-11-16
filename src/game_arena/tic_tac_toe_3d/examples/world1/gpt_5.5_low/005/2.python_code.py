
# 3x3x3 Tic Tac Toe policy

from math import inf

N = 3

# Generate all 49 winning lines in a 3x3x3 cube.
LINES = []
DIRS = []

for dx in (-1, 0, 1):
    for dy in (-1, 0, 1):
        for dz in (-1, 0, 1):
            if dx == dy == dz == 0:
                continue
            # Keep only one orientation of each direction.
            if (dx, dy, dz) > (0, 0, 0):
                DIRS.append((dx, dy, dz))

for i in range(N):
    for j in range(N):
        for k in range(N):
            for dx, dy, dz in DIRS:
                pi, pj, pk = i - dx, j - dy, k - dz
                # Start only at the first valid cell of the line.
                if 0 <= pi < N and 0 <= pj < N and 0 <= pk < N:
                    continue

                line = []
                x, y, z = i, j, k
                while 0 <= x < N and 0 <= y < N and 0 <= z < N:
                    line.append((x, y, z))
                    x += dx
                    y += dy
                    z += dz

                if len(line) == 3:
                    LINES.append(tuple(line))

# Positional weight: number of winning lines through each cell.
POS_WEIGHT = [[[0 for _ in range(N)] for _ in range(N)] for _ in range(N)]
for line in LINES:
    for i, j, k in line:
        POS_WEIGHT[i][j][k] += 1


def _empty_cells(board):
    return [
        (i, j, k)
        for i in range(N)
        for j in range(N)
        for k in range(N)
        if board[i][j][k] == 0
    ]


def _winner(board):
    for line in LINES:
        s = 0
        for i, j, k in line:
            s += board[i][j][k]
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0


def _winning_move(board, player):
    """Return a move that completes a line for player, or None."""
    target = 2 * player
    for line in LINES:
        s = 0
        empty = None
        for i, j, k in line:
            v = board[i][j][k]
            s += v
            if v == 0:
                empty = (i, j, k)
        if s == target and empty is not None:
            return empty
    return None


def _evaluate(board):
    """Static evaluation from our perspective: positive is good for player 1."""
    win = _winner(board)
    if win == 1:
        return 1_000_000
    if win == -1:
        return -1_000_000

    score = 0

    # Line pattern values.
    # Open two-in-a-row is very important in 3x3x3.
    for line in LINES:
        mine = 0
        opp = 0
        empty = 0

        for i, j, k in line:
            v = board[i][j][k]
            if v == 1:
                mine += 1
            elif v == -1:
                opp += 1
            else:
                empty += 1

        if mine and opp:
            continue

        if mine:
            if mine == 1:
                score += 8
            elif mine == 2:
                score += 250
        elif opp:
            if opp == 1:
                score -= 9
            elif opp == 2:
                score -= 300

    # Positional value.
    for i in range(N):
        for j in range(N):
            for k in range(N):
                v = board[i][j][k]
                if v == 1:
                    score += POS_WEIGHT[i][j][k] * 3
                elif v == -1:
                    score -= POS_WEIGHT[i][j][k] * 3

    return score


def _move_score(board, move, player):
    """Heuristic used only for move ordering."""
    i, j, k = move
    score = POS_WEIGHT[i][j][k] * 10

    board[i][j][k] = player

    # Prefer immediate wins and strong threats.
    if _winner(board) == player:
        score += 100_000

    own_twos = 0
    opp_twos_blocked = 0

    for line in LINES:
        if move not in line:
            continue

        s = 0
        empties = 0
        for a, b, c in line:
            v = board[a][b][c]
            s += v
            if v == 0:
                empties += 1

        if s == 2 * player and empties == 1:
            own_twos += 1
        if s == -player and empties == 1:
            opp_twos_blocked += 1

    score += own_twos * 500
    score += opp_twos_blocked * 120

    board[i][j][k] = 0
    return score


def _ordered_moves(board, player, limit=None):
    moves = _empty_cells(board)
    moves.sort(key=lambda m: _move_score(board, m, player), reverse=True)
    if limit is not None and len(moves) > limit:
        return moves[:limit]
    return moves


def _alphabeta(board, depth, alpha, beta, player):
    win = _winner(board)
    if win == 1:
        return 1_000_000 + depth
    if win == -1:
        return -1_000_000 - depth

    empties = _empty_cells(board)
    if depth == 0 or not empties:
        return _evaluate(board)

    # Tactical shortcut.
    wm = _winning_move(board, player)
    if wm is not None:
        return (1_000_000 + depth) if player == 1 else (-1_000_000 - depth)

    if player == 1:
        value = -inf

        # Broader search near the end, narrower early.
        limit = None
        if len(empties) > 16:
            limit = 10
        elif len(empties) > 11:
            limit = 14

        for move in _ordered_moves(board, player, limit):
            i, j, k = move
            board[i][j][k] = player
            value = max(value, _alphabeta(board, depth - 1, alpha, beta, -player))
            board[i][j][k] = 0

            alpha = max(alpha, value)
            if alpha >= beta:
                break

        return value

    else:
        value = inf

        limit = None
        if len(empties) > 16:
            limit = 10
        elif len(empties) > 11:
            limit = 14

        for move in _ordered_moves(board, player, limit):
            i, j, k = move
            board[i][j][k] = player
            value = min(value, _alphabeta(board, depth - 1, alpha, beta, -player))
            board[i][j][k] = 0

            beta = min(beta, value)
            if alpha >= beta:
                break

        return value


def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    empties = _empty_cells(board)

    # If somehow called on a full board, return a valid-shaped fallback.
    # Normal game engines should not request a move in this state.
    if not empties:
        return (0, 0, 0)

    # 1. Win immediately if possible.
    move = _winning_move(board, 1)
    if move is not None and board[move[0]][move[1]][move[2]] == 0:
        return move

    # 2. Block opponent's immediate win.
    move = _winning_move(board, -1)
    if move is not None and board[move[0]][move[1]][move[2]] == 0:
        return move

    # 3. Prefer center on the opening if available.
    if len(empties) >= 25 and board[1][1][1] == 0:
        return (1, 1, 1)

    # 4. Search.
    n_empty = len(empties)

    if n_empty <= 9:
        depth = n_empty
    elif n_empty <= 13:
        depth = 6
    elif n_empty <= 18:
        depth = 5
    else:
        depth = 4

    best_move = None
    best_value = -inf

    # Root move ordering.
    root_limit = None
    if n_empty > 20:
        root_limit = 14
    elif n_empty > 15:
        root_limit = 18

    for move in _ordered_moves(board, 1, root_limit):
        i, j, k = move
        if board[i][j][k] != 0:
            continue

        board[i][j][k] = 1
        value = _alphabeta(board, depth - 1, -inf, inf, -1)
        board[i][j][k] = 0

        if value > best_value:
            best_value = value
            best_move = move

    # 5. Guaranteed legal fallback.
    if best_move is not None and board[best_move[0]][best_move[1]][best_move[2]] == 0:
        return best_move

    # Choose highest positional value empty cell as final fallback.
    empties.sort(key=lambda m: POS_WEIGHT[m[0]][m[1]][m[2]], reverse=True)
    return empties[0]
