
# 3x3x3 Tic Tac Toe policy
# Player: 1
# Opponent: -1

from functools import lru_cache
import time

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

    # Face diagonals: fixed i
    for i in range(N):
        lines.append(tuple((i, t, t) for t in range(N)))
        lines.append(tuple((i, t, N - 1 - t) for t in range(N)))

    # Face diagonals: fixed j
    for j in range(N):
        lines.append(tuple((t, j, t) for t in range(N)))
        lines.append(tuple((t, j, N - 1 - t) for t in range(N)))

    # Face diagonals: fixed k
    for k in range(N):
        lines.append(tuple((t, t, k) for t in range(N)))
        lines.append(tuple((t, N - 1 - t, k) for t in range(N)))

    # Space diagonals
    lines.append(tuple((t, t, t) for t in range(N)))
    lines.append(tuple((t, t, N - 1 - t) for t in range(N)))
    lines.append(tuple((t, N - 1 - t, t) for t in range(N)))
    lines.append(tuple((t, N - 1 - t, N - 1 - t) for t in range(N)))

    return tuple(lines)


LINES = _generate_lines()

CELL_LINE_COUNT = {}
for i in range(N):
    for j in range(N):
        for k in range(N):
            CELL_LINE_COUNT[(i, j, k)] = 0

for line in LINES:
    for cell in line:
        CELL_LINE_COUNT[cell] += 1

CENTER = (1, 1, 1)


def _flatten(board):
    return tuple(board[i][j][k] for i in range(N) for j in range(N) for k in range(N))


def _idx(cell):
    i, j, k = cell
    return i * 9 + j * 3 + k


def _cell(index):
    return (index // 9, (index % 9) // 3, index % 3)


LINES_IDX = tuple(tuple(_idx(c) for c in line) for line in LINES)


def _winner(flat):
    for line in LINES_IDX:
        s = flat[line[0]] + flat[line[1]] + flat[line[2]]
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0


def _legal_moves(flat):
    return [i for i, v in enumerate(flat) if v == 0]


def _move_order(flat, moves, player):
    scored = []
    for m in moves:
        c = _cell(m)
        score = CELL_LINE_COUNT[c] * 10

        # Prefer center, then corners/strategic cells
        if c == CENTER:
            score += 100

        # Tactical ordering: completing or blocking lines
        for line in LINES_IDX:
            if m not in line:
                continue
            vals = [flat[x] for x in line]
            own = vals.count(player)
            opp = vals.count(-player)
            empty = vals.count(0)
            if empty == 1:
                if own == 2:
                    score += 10000
                if opp == 2:
                    score += 8000
            elif empty == 2:
                if own == 1:
                    score += 120
                if opp == 1:
                    score += 80

        scored.append((score, m))

    scored.sort(reverse=True)
    return [m for _, m in scored]


def _immediate_move(flat, player):
    """Return a winning move for player if one exists."""
    for line in LINES_IDX:
        vals = [flat[x] for x in line]
        if vals.count(player) == 2 and vals.count(0) == 1:
            return line[vals.index(0)]
    return None


def _evaluate(flat):
    w = _winner(flat)
    if w == 1:
        return 1_000_000
    if w == -1:
        return -1_000_000

    score = 0
    my_threats = 0
    opp_threats = 0

    for line in LINES_IDX:
        vals = [flat[x] for x in line]
        my = vals.count(1)
        opp = vals.count(-1)
        emp = vals.count(0)

        if opp == 0:
            if my == 1:
                score += 12
            elif my == 2:
                score += 260
                my_threats += 1
            elif my == 0:
                score += 1

        if my == 0:
            if opp == 1:
                score -= 14
            elif opp == 2:
                score -= 320
                opp_threats += 1
            elif opp == 0:
                score -= 1

    # Fork potential matters greatly in 3D tic tac toe.
    if my_threats >= 2:
        score += 700 * my_threats
    if opp_threats >= 2:
        score -= 850 * opp_threats

    # Positional value
    for idx, v in enumerate(flat):
        if v:
            c = _cell(idx)
            positional = CELL_LINE_COUNT[c] * 8
            if c == CENTER:
                positional += 60
            score += positional if v == 1 else -positional

    return score


def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    try:
        flat = _flatten(board)
        legal = _legal_moves(flat)

        if not legal:
            return (0, 0, 0)

        # 1. Take immediate win.
        m = _immediate_move(flat, 1)
        if m is not None and flat[m] == 0:
            return _cell(m)

        # 2. Block immediate opponent win.
        m = _immediate_move(flat, -1)
        if m is not None and flat[m] == 0:
            return _cell(m)

        empties = len(legal)

        # Strong opening preference.
        if empties == 27:
            return CENTER
        if flat[_idx(CENTER)] == 0 and empties >= 24:
            return CENTER

        # Adaptive depth for speed.
        if empties <= 10:
            depth = empties
        elif empties <= 14:
            depth = 7
        elif empties <= 18:
            depth = 5
        else:
            depth = 4

        start_time = time.time()
        time_limit = 0.92
        trans = {}

        def alphabeta(pos, d, alpha, beta, player):
            # Time safety. Return static evaluation if near limit.
            if time.time() - start_time > time_limit:
                return _evaluate(pos)

            key = (pos, d, player)
            if key in trans:
                return trans[key]

            w = _winner(pos)
            if w == 1:
                return 1_000_000 + d
            if w == -1:
                return -1_000_000 - d

            moves = _legal_moves(pos)
            if d == 0 or not moves:
                return _evaluate(pos)

            # Tactical shortcuts inside search.
            win_move = _immediate_move(pos, player)
            if win_move is not None:
                val = (900_000 + d) if player == 1 else (-900_000 - d)
                trans[key] = val
                return val

            moves = _move_order(pos, moves, player)

            if player == 1:
                value = -10**9
                for mv in moves:
                    new_pos = list(pos)
                    new_pos[mv] = 1
                    new_pos = tuple(new_pos)
                    value = max(value, alphabeta(new_pos, d - 1, alpha, beta, -1))
                    alpha = max(alpha, value)
                    if alpha >= beta:
                        break
            else:
                value = 10**9
                for mv in moves:
                    new_pos = list(pos)
                    new_pos[mv] = -1
                    new_pos = tuple(new_pos)
                    value = min(value, alphabeta(new_pos, d - 1, alpha, beta, 1))
                    beta = min(beta, value)
                    if alpha >= beta:
                        break

            trans[key] = value
            return value

        best_move = None
        best_score = -10**9

        ordered = _move_order(flat, legal, 1)

        for mv in ordered:
            if time.time() - start_time > time_limit:
                break

            new_flat = list(flat)
            new_flat[mv] = 1
            new_flat = tuple(new_flat)

            score = alphabeta(new_flat, depth - 1, -10**9, 10**9, -1)

            # Small tie-breaker for positional strength.
            score += CELL_LINE_COUNT[_cell(mv)]

            if _cell(mv) == CENTER:
                score += 3

            if score > best_score:
                best_score = score
                best_move = mv

        if best_move is not None and flat[best_move] == 0:
            return _cell(best_move)

        # Guaranteed legal fallback.
        legal = _legal_moves(flat)
        legal.sort(key=lambda x: CELL_LINE_COUNT[_cell(x)], reverse=True)
        return _cell(legal[0])

    except Exception:
        # Absolute safety fallback: scan for any empty cell.
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    if board[i][j][k] == 0:
                        return (i, j, k)

        return (0, 0, 0)
