
# 3x3x3 Tic Tac Toe policy
# Board values: 1 = us, -1 = opponent, 0 = empty

from functools import lru_cache

N = 3

def _generate_lines():
    lines = []

    # Axis-aligned lines
    for j in range(N):
        for k in range(N):
            lines.append(tuple((i, j, k) for i in range(N)))
    for i in range(N):
        for k in range(N):
            lines.append(tuple((i, j, k) for j in range(N)))
    for i in range(N):
        for j in range(N):
            lines.append(tuple((i, j, k) for k in range(N)))

    # Diagonals in planes i = const
    for i in range(N):
        lines.append(tuple((i, t, t) for t in range(N)))
        lines.append(tuple((i, t, N - 1 - t) for t in range(N)))

    # Diagonals in planes j = const
    for j in range(N):
        lines.append(tuple((t, j, t) for t in range(N)))
        lines.append(tuple((t, j, N - 1 - t) for t in range(N)))

    # Diagonals in planes k = const
    for k in range(N):
        lines.append(tuple((t, t, k) for t in range(N)))
        lines.append(tuple((t, N - 1 - t, k) for t in range(N)))

    # Space diagonals
    lines.append(tuple((t, t, t) for t in range(N)))
    lines.append(tuple((t, t, N - 1 - t) for t in range(N)))
    lines.append(tuple((t, N - 1 - t, t) for t in range(N)))
    lines.append(tuple((N - 1 - t, t, t) for t in range(N)))

    # Remove accidental duplicates, preserving order
    seen = set()
    unique = []
    for line in lines:
        key = tuple(sorted(line))
        if key not in seen:
            seen.add(key)
            unique.append(line)
    return unique

LINES = _generate_lines()

CELL_LINES = {}
for cell in ((i, j, k) for i in range(N) for j in range(N) for k in range(N)):
    CELL_LINES[cell] = [line for line in LINES if cell in line]

# Static preference: center, then corners, then high line-incidence cells.
def _static_cell_value(cell):
    i, j, k = cell
    dist_center = abs(i - 1) + abs(j - 1) + abs(k - 1)
    corner_bonus = 1 if i in (0, 2) and j in (0, 2) and k in (0, 2) else 0
    return 10 * len(CELL_LINES[cell]) + 8 * (3 - dist_center) + 12 * corner_bonus

STATIC_VALUE = {
    (i, j, k): _static_cell_value((i, j, k))
    for i in range(N) for j in range(N) for k in range(N)
}

PREFERRED_CELLS = sorted(STATIC_VALUE, key=lambda c: STATIC_VALUE[c], reverse=True)


def _empties(board):
    return [(i, j, k)
            for i in range(N) for j in range(N) for k in range(N)
            if board[i][j][k] == 0]


def _line_counts(board, line):
    s = 0
    empty = []
    for i, j, k in line:
        v = board[i][j][k]
        s += v
        if v == 0:
            empty.append((i, j, k))
    return s, empty


def _find_immediate(board, player):
    # Return winning/blocking cell for player if player has 2 in a line and one empty.
    target = 2 * player
    best = None
    best_val = -10**9
    for line in LINES:
        s, empty = _line_counts(board, line)
        if s == target and len(empty) == 1:
            cell = empty[0]
            val = STATIC_VALUE[cell]
            if val > best_val:
                best_val = val
                best = cell
    return best


def _count_immediate_wins_after_move(board, move, player):
    i, j, k = move
    if board[i][j][k] != 0:
        return -999
    board[i][j][k] = player
    count = 0
    for line in CELL_LINES[move]:
        s, empty = _line_counts(board, line)
        if s == 2 * player and len(empty) == 1:
            count += 1
    board[i][j][k] = 0
    return count


def _opponent_can_win_next(board):
    return _find_immediate(board, -1) is not None


def _score_move(board, move):
    i, j, k = move
    board[i][j][k] = 1

    score = STATIC_VALUE[move]

    # Reward our open lines and threats; penalize opponent open lines.
    for line in LINES:
        us = opp = empty = 0
        for a, b, c in line:
            v = board[a][b][c]
            if v == 1:
                us += 1
            elif v == -1:
                opp += 1
            else:
                empty += 1

        if opp == 0:
            if us == 1:
                score += 4
            elif us == 2:
                score += 80
            elif us == 3:
                score += 100000
        if us == 0:
            if opp == 1:
                score -= 3
            elif opp == 2:
                score -= 90
            elif opp == 3:
                score -= 100000

    # Prefer creating multiple immediate threats.
    my_threats = 0
    opp_threats = 0
    for line in LINES:
        s, empty = _line_counts(board, line)
        if s == 2 and len(empty) == 1:
            my_threats += 1
        elif s == -2 and len(empty) == 1:
            opp_threats += 1
    score += 350 * my_threats
    score -= 420 * opp_threats

    # Avoid moves allowing an immediate opponent win unless unavoidable.
    if _opponent_can_win_next(board):
        score -= 10000

    board[i][j][k] = 0
    return score


def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    legal = _empties(board)
    if not legal:
        # Should not happen in normal play; still return in-bounds tuple.
        return (0, 0, 0)

    # 1. Win immediately.
    win = _find_immediate(board, 1)
    if win is not None and board[win[0]][win[1]][win[2]] == 0:
        return win

    # 2. Block opponent's immediate win.
    block = _find_immediate(board, -1)
    if block is not None and board[block[0]][block[1]][block[2]] == 0:
        return block

    # 3. Create a fork: multiple winning threats next turn.
    best_fork = None
    best_fork_count = 1
    best_fork_score = -10**9
    for m in legal:
        cnt = _count_immediate_wins_after_move(board, m, 1)
        if cnt > best_fork_count:
            sc = _score_move(board, m)
            best_fork = m
            best_fork_count = cnt
            best_fork_score = sc
        elif cnt == best_fork_count and cnt > 1:
            sc = _score_move(board, m)
            if sc > best_fork_score:
                best_fork = m
                best_fork_score = sc
    if best_fork is not None:
        return best_fork

    # 4. Block opponent forks when possible.
    opp_fork_moves = []
    for m in legal:
        cnt = _count_immediate_wins_after_move(board, m, -1)
        if cnt > 1:
            opp_fork_moves.append(m)

    if opp_fork_moves:
        # If there is one critical fork square, occupy it.
        if len(opp_fork_moves) == 1:
            m = opp_fork_moves[0]
            if board[m[0]][m[1]][m[2]] == 0:
                return m

        # Otherwise choose a move that minimizes opponent fork opportunities.
        best = None
        best_key = None
        for m in legal:
            board[m[0]][m[1]][m[2]] = 1
            remaining_opp_forks = 0
            for om in _empties(board):
                if _count_immediate_wins_after_move(board, om, -1) > 1:
                    remaining_opp_forks += 1
            board[m[0]][m[1]][m[2]] = 0

            key = (-remaining_opp_forks, _score_move(board, m), STATIC_VALUE[m])
            if best is None or key > best_key:
                best = m
                best_key = key
        if best is not None:
            return best

    # 5. Early-game strong placement.
    if board[1][1][1] == 0:
        return (1, 1, 1)

    # If opponent took center and a corner is free, corners are strong in 3D.
    for c in PREFERRED_CELLS:
        if board[c[0]][c[1]][c[2]] == 0 and c[0] in (0, 2) and c[1] in (0, 2) and c[2] in (0, 2):
            # Prefer a corner only if it does not allow immediate tactics.
            return c

    # 6. General heuristic selection.
    best = None
    best_score = -10**18
    for m in legal:
        sc = _score_move(board, m)
        if sc > best_score:
            best_score = sc
            best = m

    if best is not None and board[best[0]][best[1]][best[2]] == 0:
        return best

    # 7. Absolute safety fallback.
    for m in PREFERRED_CELLS:
        if board[m[0]][m[1]][m[2]] == 0:
            return m

    return legal[0]
