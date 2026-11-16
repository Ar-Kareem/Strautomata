
import time

# 4x4 Tic Tac Toe: win by getting 4 in a row.

LINES = [
    # Rows
    ((0, 0), (0, 1), (0, 2), (0, 3)),
    ((1, 0), (1, 1), (1, 2), (1, 3)),
    ((2, 0), (2, 1), (2, 2), (2, 3)),
    ((3, 0), (3, 1), (3, 2), (3, 3)),
    # Cols
    ((0, 0), (1, 0), (2, 0), (3, 0)),
    ((0, 1), (1, 1), (2, 1), (3, 1)),
    ((0, 2), (1, 2), (2, 2), (3, 2)),
    ((0, 3), (1, 3), (2, 3), (3, 3)),
    # Diagonals
    ((0, 0), (1, 1), (2, 2), (3, 3)),
    ((0, 3), (1, 2), (2, 1), (3, 0)),
]

CELL_LINES = {(r, c): [] for r in range(4) for c in range(4)}
for idx, line in enumerate(LINES):
    for cell in line:
        CELL_LINES[cell].append(idx)

POS_WEIGHTS = [
    [3, 4, 4, 3],
    [4, 6, 6, 4],
    [4, 6, 6, 4],
    [3, 4, 4, 3],
]

INF = 10**18
WIN_SCORE = 10**9

DEADLINE = 0.0
NODE_COUNT = 0


def legal_moves(board):
    moves = []
    for r in range(4):
        row = board[r]
        for c in range(4):
            if row[c] == 0:
                moves.append((r, c))
    return moves


def move_wins(board, r, c, player):
    """Assumes board[r][c] == player."""
    for line_idx in CELL_LINES[(r, c)]:
        line = LINES[line_idx]
        ok = True
        for a, b in line:
            if board[a][b] != player:
                ok = False
                break
        if ok:
            return True
    return False


def immediate_wins(board, player, moves=None):
    if moves is None:
        moves = legal_moves(board)
    wins = []
    for r, c in moves:
        board[r][c] = player
        if move_wins(board, r, c, player):
            wins.append((r, c))
        board[r][c] = 0
    return wins


def evaluate(board):
    """
    Static evaluation from our perspective:
    positive is good for player 1, negative is good for player -1.
    """
    score = 0

    # Positional value
    for r in range(4):
        for c in range(4):
            v = board[r][c]
            if v != 0:
                score += v * POS_WEIGHTS[r][c]

    # Open-line value
    # Strongly reward 3-in-a-row with one empty, since it is an immediate threat.
    for line in LINES:
        cnt1 = 0
        cntm1 = 0
        for r, c in line:
            v = board[r][c]
            if v == 1:
                cnt1 += 1
            elif v == -1:
                cntm1 += 1

        if cnt1 and cntm1:
            continue

        if cnt1:
            if cnt1 == 1:
                score += 4
            elif cnt1 == 2:
                score += 24
            elif cnt1 == 3:
                score += 350
        elif cntm1:
            if cntm1 == 1:
                score -= 4
            elif cntm1 == 2:
                score -= 26
            elif cntm1 == 3:
                score -= 380

    return score


def move_priority(board, r, c, player, pv_move=None):
    """
    Higher means better for the side to move.
    Used only for move ordering.
    """
    score = POS_WEIGHTS[r][c] * 10

    if pv_move == (r, c):
        score += 2_000_000

    # Analyze the lines that pass through this cell.
    for line_idx in CELL_LINES[(r, c)]:
        own = 0
        opp = 0
        for a, b in LINES[line_idx]:
            v = board[a][b]
            if v == player:
                own += 1
            elif v == -player:
                opp += 1

        # If the line is open for us, building it is good.
        if opp == 0:
            if own == 0:
                score += 6
            elif own == 1:
                score += 25
            elif own == 2:
                score += 120
            elif own == 3:
                score += 2500

        # If the line is open for the opponent, blocking it is also good.
        if own == 0:
            if opp == 1:
                score += 20
            elif opp == 2:
                score += 90
            elif opp == 3:
                score += 3000

    # Immediate wins first.
    board[r][c] = player
    if move_wins(board, r, c, player):
        score += 50_000_000
    board[r][c] = 0

    return score


def ordered_moves(board, player, pv_move=None):
    scored = []
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                scored.append((move_priority(board, r, c, player, pv_move), (r, c)))
    scored.sort(reverse=True)
    return [m for _, m in scored]


def check_timeout():
    global NODE_COUNT, DEADLINE
    NODE_COUNT += 1
    if (NODE_COUNT & 255) == 0 and time.perf_counter() >= DEADLINE:
        raise TimeoutError


def search(board, depth, alpha, beta, maximizing, empties, last_move, last_player):
    """
    Alpha-beta minimax from the fixed perspective of player 1.
    last_move / last_player let us detect terminal states cheaply.
    """
    check_timeout()

    if last_move is not None:
        lr, lc = last_move
        if move_wins(board, lr, lc, last_player):
            if last_player == 1:
                return WIN_SCORE + depth
            return -WIN_SCORE - depth

    if empties == 0:
        return 0

    if depth == 0:
        return evaluate(board)

    player = 1 if maximizing else -1
    moves = ordered_moves(board, player)

    if maximizing:
        value = -INF
        for r, c in moves:
            board[r][c] = 1
            child = search(board, depth - 1, alpha, beta, False, empties - 1, (r, c), 1)
            board[r][c] = 0

            if child > value:
                value = child
            if value > alpha:
                alpha = value
            if alpha >= beta:
                break
        return value

    value = INF
    for r, c in moves:
        board[r][c] = -1
        child = search(board, depth - 1, alpha, beta, True, empties - 1, (r, c), -1)
        board[r][c] = 0

        if child < value:
            value = child
        if value < beta:
            beta = value
        if alpha >= beta:
            break
    return value


def search_root(board, depth, empties, pv_move):
    moves = ordered_moves(board, 1, pv_move)
    best_move = moves[0]
    best_value = -INF
    alpha = -INF
    beta = INF

    for r, c in moves:
        board[r][c] = 1
        if move_wins(board, r, c, 1):
            value = WIN_SCORE + depth
        else:
            value = search(board, depth - 1, alpha, beta, False, empties - 1, (r, c), 1)
        board[r][c] = 0

        if value > best_value:
            best_value = value
            best_move = (r, c)

        if value > alpha:
            alpha = value

    return best_value, best_move


def policy(board):
    moves = legal_moves(board)
    if not moves:
        # Should not happen in a normal game, but keep API total.
        return (0, 0)

    # Simple opening preference on an empty board.
    if len(moves) == 16 and board[1][1] == 0:
        return (1, 1)

    # Fast fallback: always legal.
    fallback = max(moves, key=lambda m: move_priority(board, m[0], m[1], 1))

    # Tactical layer 1: win immediately if possible.
    my_wins = immediate_wins(board, 1, moves)
    if my_wins:
        return max(my_wins, key=lambda m: POS_WEIGHTS[m[0]][m[1]])

    # Tactical layer 2: if opponent has exactly one immediate win, block it.
    opp_wins = immediate_wins(board, -1, moves)
    if len(opp_wins) == 1:
        return opp_wins[0]

    empties = len(moves)

    # Adaptive depth cap.
    if empties > 12:
        max_depth = 5
    elif empties > 9:
        max_depth = 6
    elif empties > 7:
        max_depth = 8
    else:
        max_depth = empties

    global DEADLINE, NODE_COUNT
    DEADLINE = time.perf_counter() + 0.95

    best_move = fallback
    pv_move = None

    for depth in range(1, max_depth + 1):
        try:
            NODE_COUNT = 0
            _, candidate = search_root(board, depth, empties, pv_move)
            best_move = candidate
            pv_move = candidate
        except TimeoutError:
            break

    # Final legality guard.
    r, c = best_move
    if 0 <= r < 4 and 0 <= c < 4 and board[r][c] == 0:
        return best_move

    # If anything went wrong, still return a legal move.
    return fallback
