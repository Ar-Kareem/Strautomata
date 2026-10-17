
from time import time

# All winning lines in 4x4 tic-tac-toe: 4 rows, 4 cols, 2 diagonals
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

# Positional preference. The four central squares are strongest.
POS_WEIGHTS = (
    (3, 4, 4, 3),
    (4, 7, 7, 4),
    (4, 7, 7, 4),
    (3, 4, 4, 3),
)

WIN_SCORE = 1_000_000


def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Return the next move for player 1 on a 4x4 tic-tac-toe board.
    The returned move is always a legal empty square.
    """

    # Copy board to avoid mutating caller state unexpectedly.
    b = [row[:] for row in board]

    empties = [(r, c) for r in range(4) for c in range(4) if b[r][c] == 0]
    if not empties:
        # Should not happen in a valid call, but keep API safe.
        return (0, 0)

    # 1. Immediate win.
    move = _find_immediate_win(b, 1)
    if move is not None:
        return move

    # 2. Immediate block.
    move = _find_immediate_win(b, -1)
    if move is not None:
        return move

    # 3. Strong deterministic opening preference.
    if len(empties) >= 14:
        for m in ((1, 1), (1, 2), (2, 1), (2, 2), (0, 0), (0, 3), (3, 0), (3, 3)):
            if b[m[0]][m[1]] == 0:
                return m

    # 4. Iterative-deepening alpha-beta minimax.
    deadline = time() + 0.90

    # Choose a reasonable maximum depth based on game stage.
    n = len(empties)
    if n <= 9:
        max_depth = n       # usually solve the endgame exactly
    elif n <= 11:
        max_depth = 8
    elif n <= 13:
        max_depth = 6
    else:
        max_depth = 5

    ordered = _ordered_moves(b, empties, 1)
    best_move = ordered[0]
    best_score = -10**18

    # Transposition table reused across depths.
    table = {}

    for depth in range(1, max_depth + 1):
        if time() > deadline:
            break

        current_best = best_move
        current_score = -10**18
        alpha = -10**18
        beta = 10**18

        for r, c in ordered:
            if time() > deadline:
                break

            b[r][c] = 1
            score = _minimax(b, depth - 1, -1, alpha, beta, deadline, table)
            b[r][c] = 0

            if score > current_score:
                current_score = score
                current_best = (r, c)

            alpha = max(alpha, current_score)

        if time() <= deadline:
            best_move = current_best
            best_score = current_score

            # If a forced win is found, no need to search further.
            if best_score > WIN_SCORE // 2:
                break

    # Final legality guard.
    if b[best_move[0]][best_move[1]] == 0:
        return best_move

    # Absolute fallback.
    return empties[0]


def _find_immediate_win(b, player):
    for r in range(4):
        for c in range(4):
            if b[r][c] == 0:
                b[r][c] = player
                if _winner(b) == player:
                    b[r][c] = 0
                    return (r, c)
                b[r][c] = 0
    return None


def _winner(b):
    for line in LINES:
        s = 0
        for r, c in line:
            s += b[r][c]
        if s == 4:
            return 1
        if s == -4:
            return -1
    return 0


def _board_key(b, side, depth):
    return (
        tuple(
            b[0] + b[1] + b[2] + b[3]
        ),
        side,
        depth,
    )


def _minimax(b, depth, side, alpha, beta, deadline, table):
    """
    side == 1  -> maximizing player
    side == -1 -> minimizing opponent
    Scores are always from player 1's perspective.
    """

    w = _winner(b)
    if w == 1:
        return WIN_SCORE + depth
    if w == -1:
        return -WIN_SCORE - depth

    empties = [(r, c) for r in range(4) for c in range(4) if b[r][c] == 0]

    if not empties:
        return 0

    if depth <= 0 or time() > deadline:
        return _evaluate(b)

    key = _board_key(b, side, depth)
    if key in table:
        return table[key]

    moves = _ordered_moves(b, empties, side)

    if side == 1:
        value = -10**18

        for r, c in moves:
            b[r][c] = 1
            value = max(value, _minimax(b, depth - 1, -1, alpha, beta, deadline, table))
            b[r][c] = 0

            alpha = max(alpha, value)
            if alpha >= beta:
                break

        table[key] = value
        return value

    else:
        value = 10**18

        for r, c in moves:
            b[r][c] = -1
            value = min(value, _minimax(b, depth - 1, 1, alpha, beta, deadline, table))
            b[r][c] = 0

            beta = min(beta, value)
            if alpha >= beta:
                break

        table[key] = value
        return value


def _ordered_moves(b, empties, side):
    scored = []

    for r, c in empties:
        score = POS_WEIGHTS[r][c]

        # Prefer moves that create immediate tactical pressure.
        b[r][c] = side

        for line in LINES:
            if (r, c) in line:
                own = 0
                opp = 0
                for rr, cc in line:
                    if b[rr][cc] == side:
                        own += 1
                    elif b[rr][cc] == -side:
                        opp += 1

                if opp == 0:
                    if own == 3:
                        score += 80
                    elif own == 2:
                        score += 12
                if own == 0:
                    if opp == 3:
                        score += 70
                    elif opp == 2:
                        score += 10

        b[r][c] = 0
        scored.append((score, r, c))

    scored.sort(reverse=True)
    return [(r, c) for _, r, c in scored]


def _evaluate(b):
    """
    Static evaluation from player 1's perspective.
    Positive is good for us, negative is good for opponent.
    """

    total = 0

    # Positional score.
    for r in range(4):
        for c in range(4):
            if b[r][c] == 1:
                total += POS_WEIGHTS[r][c]
            elif b[r][c] == -1:
                total -= POS_WEIGHTS[r][c]

    # Line potential score.
    # Open lines with more stones are exponentially more valuable.
    my_weights = (0, 2, 18, 220, WIN_SCORE)
    opp_weights = (0, 3, 24, 260, WIN_SCORE)

    for line in LINES:
        mine = 0
        opp = 0

        for r, c in line:
            if b[r][c] == 1:
                mine += 1
            elif b[r][c] == -1:
                opp += 1

        if mine and opp:
            continue

        if opp == 0:
            total += my_weights[mine]
        elif mine == 0:
            total -= opp_weights[opp]

    # Fork-like bonus: count open three-threats.
    my_threes = 0
    opp_threes = 0

    for line in LINES:
        mine = 0
        opp = 0
        empty = 0

        for r, c in line:
            if b[r][c] == 1:
                mine += 1
            elif b[r][c] == -1:
                opp += 1
            else:
                empty += 1

        if mine == 3 and empty == 1:
            my_threes += 1
        if opp == 3 and empty == 1:
            opp_threes += 1

    if my_threes >= 2:
        total += 500
    if opp_threes >= 2:
        total -= 650

    return total
