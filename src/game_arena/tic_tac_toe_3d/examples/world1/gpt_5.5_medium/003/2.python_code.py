
from itertools import product
import time


# ---------- Precomputation ----------

def _idx(i, j, k):
    return i * 9 + j * 3 + k


def _coord(idx):
    return (idx // 9, (idx % 9) // 3, idx % 3)


def _make_lines():
    lines = set()

    directions = []
    for dx, dy, dz in product((-1, 0, 1), repeat=3):
        if dx == dy == dz == 0:
            continue
        directions.append((dx, dy, dz))

    for i, j, k in product(range(3), repeat=3):
        for dx, dy, dz in directions:
            cells = []
            ok = True
            for t in range(3):
                x = i + dx * t
                y = j + dy * t
                z = k + dz * t
                if not (0 <= x < 3 and 0 <= y < 3 and 0 <= z < 3):
                    ok = False
                    break
                cells.append(_idx(x, y, z))
            if ok:
                lines.add(tuple(sorted(cells)))

    lines = sorted(lines)
    cell_lines = [[] for _ in range(27)]
    for line in lines:
        for c in line:
            cell_lines[c].append(line)

    return lines, cell_lines


WIN_LINES, CELL_LINES = _make_lines()
CELL_WEIGHT = [len(CELL_LINES[i]) for i in range(27)]

INF = 1_000_000
BIG = 10_000_000

_DEADLINE = 0.0
_NODES = 0
_TT = {}


class _Timeout(Exception):
    pass


# ---------- Basic board helpers ----------

def _flatten(board):
    return [int(board[i][j][k]) for i in range(3) for j in range(3) for k in range(3)]


def _winner(flat):
    for a, b, c in WIN_LINES:
        s = flat[a] + flat[b] + flat[c]
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0


def _empty_cells(flat):
    return [i for i, v in enumerate(flat) if v == 0]


def _immediate_winning_cells(flat, player):
    """Cells where player can move and win immediately."""
    wins = set()
    target = 2 * player
    for line in WIN_LINES:
        a, b, c = line
        if flat[a] + flat[b] + flat[c] == target:
            if flat[a] == 0:
                wins.add(a)
            elif flat[b] == 0:
                wins.add(b)
            elif flat[c] == 0:
                wins.add(c)
    return wins


# ---------- Heuristic evaluation ----------

def _evaluate(flat):
    w = _winner(flat)
    if w == 1:
        return INF
    if w == -1:
        return -INF

    score = 0

    # Positional value: center and cells lying on many lines are strongest.
    for i, v in enumerate(flat):
        if v:
            score += v * CELL_WEIGHT[i] * 3

    # Line potential.
    for line in WIN_LINES:
        vals = [flat[x] for x in line]
        my = vals.count(1)
        opp = vals.count(-1)

        if my and opp:
            continue

        if my:
            if my == 1:
                score += 10
            elif my == 2:
                score += 260
        elif opp:
            if opp == 1:
                score -= 11
            elif opp == 2:
                score -= 320

    # Immediate threat and fork awareness.
    my_threats = len(_immediate_winning_cells(flat, 1))
    opp_threats = len(_immediate_winning_cells(flat, -1))

    score += my_threats * 550
    score -= opp_threats * 700

    if my_threats > 1:
        score += (my_threats - 1) * 1800
    if opp_threats > 1:
        score -= (opp_threats - 1) * 2400

    return score


def _move_score(flat, move, player):
    """Static move ordering score from current player's perspective."""
    score = CELL_WEIGHT[move] * 20

    # Prefer the exact center heavily when available.
    if move == 13:
        score += 500

    made_threats = 0

    for line in CELL_LINES[move]:
        own = 0
        opp = 0
        for c in line:
            if c == move:
                continue
            if flat[c] == player:
                own += 1
            elif flat[c] == -player:
                opp += 1

        if opp == 0:
            if own == 2:
                score += 100000      # immediate win
            elif own == 1:
                score += 1200
                made_threats += 1
            else:
                score += 40
        elif own == 0:
            if opp == 2:
                score += 95000       # immediate block
            elif opp == 1:
                score += 350

    if made_threats > 1:
        score += 3500 * (made_threats - 1)

    return score


def _ordered_moves(flat, player):
    moves = _empty_cells(flat)
    moves.sort(key=lambda m: _move_score(flat, m, player), reverse=True)
    return moves


# ---------- Alpha-beta search ----------

def _check_time():
    global _NODES
    _NODES += 1
    if (_NODES & 1023) == 0 and time.perf_counter() > _DEADLINE:
        raise _Timeout()


def _alphabeta(flat, depth, alpha, beta, player):
    _check_time()

    w = _winner(flat)
    if w == 1:
        return INF + depth
    if w == -1:
        return -INF - depth

    if not any(v == 0 for v in flat):
        return 0

    # Tactical quiescence: if the side to move can win immediately, it will.
    own_now = _immediate_winning_cells(flat, player)
    if own_now:
        return INF + depth if player == 1 else -INF - depth

    # If the opponent has multiple immediate wins, this side is lost.
    opp_now = _immediate_winning_cells(flat, -player)
    if len(opp_now) > 1:
        return -INF - depth if player == 1 else INF + depth

    # At horizon, if there is exactly one immediate threat, assume forced block
    # before evaluating. This reduces horizon blunders.
    if depth == 0:
        if len(opp_now) == 1:
            m = next(iter(opp_now))
            if flat[m] == 0:
                flat[m] = player
                try:
                    return _evaluate(flat)
                finally:
                    flat[m] = 0
        return _evaluate(flat)

    key = (tuple(flat), player, depth)
    entry = _TT.get(key)
    if entry is not None:
        val, flag = entry
        if flag == 0:
            return val
        if flag == 1:
            alpha = max(alpha, val)
        elif flag == -1:
            beta = min(beta, val)
        if alpha >= beta:
            return val

    alpha_orig = alpha
    beta_orig = beta

    # If there is one immediate opponent threat, the only sensible legal move is
    # to block it.
    if len(opp_now) == 1:
        moves = list(opp_now)
    else:
        moves = _ordered_moves(flat, player)

    if player == 1:
        value = -BIG
        for m in moves:
            if flat[m] != 0:
                continue
            flat[m] = player
            try:
                v = _alphabeta(flat, depth - 1, alpha, beta, -player)
            finally:
                flat[m] = 0

            if v > value:
                value = v
            if value > alpha:
                alpha = value
            if alpha >= beta:
                break
    else:
        value = BIG
        for m in moves:
            if flat[m] != 0:
                continue
            flat[m] = player
            try:
                v = _alphabeta(flat, depth - 1, alpha, beta, -player)
            finally:
                flat[m] = 0

            if v < value:
                value = v
            if value < beta:
                beta = value
            if alpha >= beta:
                break

    # Transposition-table flag.
    if value <= alpha_orig:
        flag = -1     # upper bound
    elif value >= beta_orig:
        flag = 1      # lower bound
    else:
        flag = 0      # exact

    _TT[key] = (value, flag)
    return value


# ---------- Required API ----------

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    global _DEADLINE, _NODES, _TT

    flat = _flatten(board)
    empties = _empty_cells(flat)

    # No legal move exists. This should not be requested by the game engine.
    if not empties:
        return (0, 0, 0)

    # 1. Win immediately if possible.
    my_wins = _immediate_winning_cells(flat, 1)
    if my_wins:
        return _coord(max(my_wins, key=lambda m: _move_score(flat, m, 1)))

    # 2. Block opponent's immediate win.
    opp_wins = _immediate_winning_cells(flat, -1)
    if opp_wins:
        return _coord(max(opp_wins, key=lambda m: _move_score(flat, m, 1)))

    # 3. Strong opening principle: take the center early.
    if flat[13] == 0 and len(empties) >= 25:
        return (1, 1, 1)

    # 4. Heuristic fallback before search, guaranteeing a legal move.
    root_moves = _ordered_moves(flat, 1)
    best_move = root_moves[0] if root_moves else empties[0]

    # Search budget kept below one second for safety.
    _DEADLINE = time.perf_counter() + 0.82
    _NODES = 0
    _TT = {}

    n = len(empties)
    if n <= 10:
        max_depth = n
    elif n <= 14:
        max_depth = 9
    elif n <= 18:
        max_depth = 7
    else:
        max_depth = 5

    try:
        for depth in range(1, max_depth + 1):
            depth_best = best_move
            depth_best_val = -BIG

            # Try previous best first.
            if best_move in root_moves:
                ordered = [best_move] + [m for m in root_moves if m != best_move]
            else:
                ordered = root_moves

            alpha = -BIG
            beta = BIG

            for m in ordered:
                if flat[m] != 0:
                    continue

                flat[m] = 1
                try:
                    val = _alphabeta(flat, depth - 1, alpha, beta, -1)
                finally:
                    flat[m] = 0

                if val > depth_best_val:
                    depth_best_val = val
                    depth_best = m

                if val > alpha:
                    alpha = val

            # Completed this depth, so accept its result.
            best_move = depth_best

            # If we found a forced win, no need to search further.
            if depth_best_val >= INF:
                break

            if time.perf_counter() > _DEADLINE:
                break

    except _Timeout:
        pass

    # Final legality check and fallback.
    if 0 <= best_move < 27 and flat[best_move] == 0:
        return _coord(best_move)

    for m in empties:
        if flat[m] == 0:
            return _coord(m)

    return (0, 0, 0)
