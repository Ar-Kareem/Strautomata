
import time
from itertools import product

# ---------- Precomputation ----------

def _idx(i, j, k):
    return i * 9 + j * 3 + k

def _coord(idx):
    return (idx // 9, (idx // 3) % 3, idx % 3)

# Generate the 13 unique line directions.
_DIRS = []
for dx, dy, dz in product((-1, 0, 1), repeat=3):
    if dx == dy == dz == 0:
        continue
    # Keep only one orientation of each direction.
    for v in (dx, dy, dz):
        if v != 0:
            if v > 0:
                _DIRS.append((dx, dy, dz))
            break

# Generate all 49 winning lines.
_LINES = []
for dx, dy, dz in _DIRS:
    for i, j, k in product(range(3), repeat=3):
        i2, j2, k2 = i + 2 * dx, j + 2 * dy, k + 2 * dz
        if 0 <= i2 < 3 and 0 <= j2 < 3 and 0 <= k2 < 3:
            _LINES.append((
                _idx(i, j, k),
                _idx(i + dx, j + dy, k + dz),
                _idx(i2, j2, k2),
            ))

_CELL_LINES = [[] for _ in range(27)]
for line in _LINES:
    for c in line:
        _CELL_LINES[c].append(line)

# Positional strength: number of winning lines through each cell.
_CELL_WEIGHT = [len(_CELL_LINES[c]) for c in range(27)]

_INF = 10 ** 9
_WIN_SCORE = 1000000


class _Timeout(Exception):
    pass


# ---------- Basic board utilities ----------

def _flatten(board):
    return [board[i][j][k] for i in range(3) for j in range(3) for k in range(3)]

def _empties(flat):
    return [i for i, v in enumerate(flat) if v == 0]

def _has_win(flat, player):
    for a, b, c in _LINES:
        if flat[a] == player and flat[b] == player and flat[c] == player:
            return True
    return False

def _winning_moves(flat, player):
    """Cells where player can immediately complete a line."""
    result = set()
    for line in _LINES:
        vals = [flat[x] for x in line]
        if vals.count(player) == 2 and vals.count(0) == 1:
            result.add(line[vals.index(0)])
    return result

def _first_legal(flat):
    for i, v in enumerate(flat):
        if v == 0:
            return i
    return 0


# ---------- Tactical helpers ----------

def _score_move_for_player(flat, move, player):
    """
    Static move score from the point of view of 'player'.
    Used for ordering and tie-breaking.
    """
    opp = -player
    score = _CELL_WEIGHT[move] * 8

    for line in _CELL_LINES[move]:
        own = 0
        enemy = 0
        for c in line:
            if flat[c] == player:
                own += 1
            elif flat[c] == opp:
                enemy += 1

        # Offensive value.
        if enemy == 0:
            if own == 0:
                score += 3
            elif own == 1:
                score += 35
            elif own == 2:
                score += 2000

        # Defensive value: occupying this cell blocks enemy potential.
        if own == 0:
            if enemy == 1:
                score += 18
            elif enemy == 2:
                score += 1800

    # Tiny deterministic tie-breaker toward geometrically central cells.
    i, j, k = _coord(move)
    score -= abs(i - 1) + abs(j - 1) + abs(k - 1)
    return score

def _creates_fork(flat, move, player):
    flat[move] = player
    try:
        return len(_winning_moves(flat, player)) >= 2
    finally:
        flat[move] = 0

def _fork_moves(flat, player):
    res = []
    for m in _empties(flat):
        if _creates_fork(flat, m, player):
            res.append(m)
    return res

def _best_static_move(flat, moves, player=1):
    return max(moves, key=lambda m: _score_move_for_player(flat, m, player))


# ---------- Evaluation and search ----------

def _evaluate(flat):
    if _has_win(flat, 1):
        return _WIN_SCORE
    if _has_win(flat, -1):
        return -_WIN_SCORE

    score = 0

    # Positional material.
    for i, v in enumerate(flat):
        if v == 1:
            score += _CELL_WEIGHT[i] * 5
        elif v == -1:
            score -= _CELL_WEIGHT[i] * 6

    # Line-based heuristic.
    for a, b, c in _LINES:
        vals = (flat[a], flat[b], flat[c])
        mine = vals.count(1)
        opp = vals.count(-1)

        if mine and opp:
            continue

        if mine:
            if mine == 1:
                score += 8
            elif mine == 2:
                score += 120
            elif mine == 3:
                score += _WIN_SCORE
        elif opp:
            if opp == 1:
                score -= 10
            elif opp == 2:
                score -= 150
            elif opp == 3:
                score -= _WIN_SCORE

    return score

def _ordered_moves(flat, player):
    moves = _empties(flat)
    if not moves:
        return []

    own_wins = _winning_moves(flat, player)
    opp_wins = _winning_moves(flat, -player)

    def key(m):
        s = _score_move_for_player(flat, m, player)
        if m in own_wins:
            s += 100000
        if m in opp_wins:
            s += 90000
        return s

    moves.sort(key=key, reverse=True)
    return moves

def _alphabeta(flat, depth, alpha, beta, player, deadline, cache, nodes):
    nodes[0] += 1
    if (nodes[0] & 1023) == 0 and time.perf_counter() > deadline:
        raise _Timeout()

    if _has_win(flat, 1):
        return _WIN_SCORE + depth
    if _has_win(flat, -1):
        return -_WIN_SCORE - depth

    moves = _empties(flat)
    if depth == 0 or not moves:
        return _evaluate(flat)

    key = (tuple(flat), depth, player)
    cached = cache.get(key)
    if cached is not None:
        return cached

    if player == 1:
        value = -_INF
        for m in _ordered_moves(flat, player):
            flat[m] = player
            try:
                child = _alphabeta(flat, depth - 1, alpha, beta, -player, deadline, cache, nodes)
            finally:
                flat[m] = 0

            if child > value:
                value = child
            if value > alpha:
                alpha = value
            if alpha >= beta:
                return value

        cache[key] = value
        return value

    else:
        value = _INF
        for m in _ordered_moves(flat, player):
            flat[m] = player
            try:
                child = _alphabeta(flat, depth - 1, alpha, beta, -player, deadline, cache, nodes)
            finally:
                flat[m] = 0

            if child < value:
                value = child
            if value < beta:
                beta = value
            if alpha >= beta:
                return value

        cache[key] = value
        return value

def _search_best_move(flat, deadline):
    moves = _ordered_moves(flat, 1)
    if not moves:
        return _first_legal(flat)

    best_completed = moves[0]
    cache = {}
    nodes = [0]

    empty_count = len(_empties(flat))

    if empty_count <= 8:
        max_depth = empty_count
    elif empty_count <= 12:
        max_depth = 8
    elif empty_count <= 17:
        max_depth = 6
    else:
        max_depth = 5

    root_order = moves[:]

    for depth in range(1, max_depth + 1):
        if time.perf_counter() > deadline:
            break

        try:
            best_this_depth = root_order[0]
            best_value = -_INF
            alpha = -_INF
            beta = _INF

            for m in root_order:
                if time.perf_counter() > deadline:
                    raise _Timeout()

                flat[m] = 1
                try:
                    value = _alphabeta(flat, depth - 1, alpha, beta, -1, deadline, cache, nodes)
                finally:
                    flat[m] = 0

                if value > best_value:
                    best_value = value
                    best_this_depth = m

                if value > alpha:
                    alpha = value

            best_completed = best_this_depth

            # Try the current best first in the next iteration.
            root_order = [best_completed] + [m for m in _ordered_moves(flat, 1) if m != best_completed]

        except _Timeout:
            break

    return best_completed


# ---------- Required API ----------

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    Return a legal move as (i, j, k).
    1 is this policy's mark, -1 is the opponent's mark.
    """
    try:
        flat = _flatten(board)
        legal = _empties(flat)

        if not legal:
            return (0, 0, 0)

        # Opening preference: the center is the strongest cell in 3D Tic Tac Toe.
        if len(legal) == 27:
            return (1, 1, 1)

        # 1. Win immediately if possible.
        wins = _winning_moves(flat, 1)
        if wins:
            return _coord(_best_static_move(flat, list(wins), 1))

        # 2. Block opponent's immediate win.
        opp_wins = _winning_moves(flat, -1)
        if opp_wins:
            return _coord(_best_static_move(flat, list(opp_wins), 1))

        # 3. Create a fork if possible.
        my_forks = _fork_moves(flat, 1)
        if my_forks:
            return _coord(_best_static_move(flat, my_forks, 1))

        # 4. Prevent opponent forks when possible.
        opp_forks = _fork_moves(flat, -1)
        if opp_forks:
            safe_moves = []
            for m in legal:
                flat[m] = 1
                try:
                    if not _fork_moves(flat, -1):
                        safe_moves.append(m)
                finally:
                    flat[m] = 0

            if safe_moves:
                return _coord(_best_static_move(flat, safe_moves, 1))

            # If no move prevents all forks, occupy the most dangerous fork square.
            return _coord(_best_static_move(flat, opp_forks, 1))

        # 5. Time-limited alpha-beta search.
        deadline = time.perf_counter() + 0.80
        move = _search_best_move(flat, deadline)

        if flat[move] == 0:
            return _coord(move)

        # Absolute safety fallback.
        return _coord(_first_legal(flat))

    except Exception:
        # Never fail to return a legal-looking move if the arena supplies a normal board.
        try:
            flat = _flatten(board)
            return _coord(_first_legal(flat))
        except Exception:
            return (0, 0, 0)
