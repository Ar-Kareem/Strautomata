
import time
from functools import lru_cache
from itertools import product


def _idx(i: int, j: int, k: int) -> int:
    return i * 9 + j * 3 + k


def _coord(x: int) -> tuple[int, int, int]:
    return (x // 9, (x % 9) // 3, x % 3)


def _build_lines() -> tuple[tuple[int, int, int], ...]:
    def inside(x: int, y: int, z: int) -> bool:
        return 0 <= x < 3 and 0 <= y < 3 and 0 <= z < 3

    lines = []
    seen = set()

    for dx, dy, dz in product((-1, 0, 1), repeat=3):
        if dx == dy == dz == 0:
            continue
        first_nonzero = dx if dx != 0 else (dy if dy != 0 else dz)
        if first_nonzero <= 0:
            continue

        for x, y, z in product(range(3), repeat=3):
            x2, y2, z2 = x + 2 * dx, y + 2 * dy, z + 2 * dz
            if not inside(x2, y2, z2):
                continue
            if inside(x - dx, y - dy, z - dz):
                continue

            line = (_idx(x, y, z), _idx(x + dx, y + dy, z + dz), _idx(x2, y2, z2))
            if line not in seen:
                seen.add(line)
                lines.append(line)

    return tuple(lines)


LINES = _build_lines()
assert len(LINES) == 49

CELL_TO_PAIRS = [[] for _ in range(27)]
for a, b, c in LINES:
    CELL_TO_PAIRS[a].append((b, c))
    CELL_TO_PAIRS[b].append((a, c))
    CELL_TO_PAIRS[c].append((a, b))

CELL_WEIGHTS = tuple(len(v) for v in CELL_TO_PAIRS)
CENTER = _idx(1, 1, 1)
CORNERS = tuple(_idx(i, j, k) for i in (0, 2) for j in (0, 2) for k in (0, 2))

INF = 10**18
WIN = 10**9
LINE_VALUE = (0, 4, 40, 0)

TT = {}
DEADLINE = 0.0


def _flatten(board: list[list[list[int]]]) -> tuple[int, ...]:
    return tuple(board[i][j][k] for i in range(3) for j in range(3) for k in range(3))


def _make_move(state: tuple[int, ...], move: int, player: int) -> tuple[int, ...]:
    return state[:move] + (player,) + state[move + 1:]


@lru_cache(maxsize=100000)
def _winner(state: tuple[int, ...]) -> int:
    for a, b, c in LINES:
        s = state[a] + state[b] + state[c]
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0


@lru_cache(maxsize=100000)
def _immediate_wins(state: tuple[int, ...], player: int) -> tuple[int, ...]:
    target = 2 * player
    seen = set()
    wins = []
    for a, b, c in LINES:
        if state[a] + state[b] + state[c] != target:
            continue
        if state[a] == 0:
            if a not in seen:
                seen.add(a)
                wins.append(a)
        elif state[b] == 0:
            if b not in seen:
                seen.add(b)
                wins.append(b)
        elif state[c] == 0:
            if c not in seen:
                seen.add(c)
                wins.append(c)
    return tuple(wins)


def _move_order_score(state: tuple[int, ...], move: int, player: int) -> int:
    score = 6 * CELL_WEIGHTS[move]

    for x, y in CELL_TO_PAIRS[move]:
        vx, vy = state[x], state[y]

        if vx == -player or vy == -player:
            # Blocking / interfering with opponent lines
            if vx != player and vy != player:
                opp = (vx == -player) + (vy == -player)
                if opp == 2:
                    score += 5000
                elif opp == 1:
                    score += 30
        else:
            # Extending our own uncontested lines
            own = (vx == player) + (vy == player)
            if own == 2:
                score += 10000
            elif own == 1:
                score += 60
            else:
                score += 8

    return score


def _ordered_moves(state: tuple[int, ...], player: int) -> list[int]:
    wins = _immediate_wins(state, player)
    if wins:
        return sorted(wins, key=lambda m: (CELL_WEIGHTS[m], m), reverse=True)

    opp_wins = _immediate_wins(state, -player)
    if opp_wins:
        cells = list(opp_wins)
    else:
        cells = [i for i, v in enumerate(state) if v == 0]

    scored = [(_move_order_score(state, m, player), CELL_WEIGHTS[m], m) for m in cells]
    scored.sort(reverse=True)
    return [m for _, _, m in scored]


@lru_cache(maxsize=100000)
def _heuristic(state: tuple[int, ...]) -> int:
    score = 0

    for a, b, c in LINES:
        va, vb, vc = state[a], state[b], state[c]

        if va != -1 and vb != -1 and vc != -1:
            cnt = (va == 1) + (vb == 1) + (vc == 1)
            if cnt:
                score += LINE_VALUE[cnt]

        if va != 1 and vb != 1 and vc != 1:
            cnt = (va == -1) + (vb == -1) + (vc == -1)
            if cnt:
                score -= LINE_VALUE[cnt]

    score += 90 * len(_immediate_wins(state, 1))
    score -= 100 * len(_immediate_wins(state, -1))

    pos = 0
    for i, v in enumerate(state):
        if v:
            pos += v * CELL_WEIGHTS[i]
    score += 2 * pos

    return score


def _alphabeta(state: tuple[int, ...], player: int, depth: int, alpha: int, beta: int) -> int:
    global TT, DEADLINE

    if time.perf_counter() >= DEADLINE:
        raise TimeoutError

    key = (state, player, depth)
    cached = TT.get(key)
    if cached is not None:
        return cached

    empties = state.count(0)
    ply = 27 - empties

    w = _winner(state)
    if w == 1:
        val = WIN - ply
        TT[key] = val
        return val
    if w == -1:
        val = -WIN + ply
        TT[key] = val
        return val
    if empties == 0:
        TT[key] = 0
        return 0

    if _immediate_wins(state, player):
        val = (WIN - ply) if player == 1 else (-WIN + ply)
        TT[key] = val
        return val

    if depth == 0:
        val = _heuristic(state)
        TT[key] = val
        return val

    moves = _ordered_moves(state, player)
    cutoff = False

    if player == 1:
        value = -INF
        for move in moves:
            child = _make_move(state, move, 1)
            child_val = _alphabeta(child, -1, depth - 1, alpha, beta)
            if child_val > value:
                value = child_val
            if value > alpha:
                alpha = value
            if alpha >= beta:
                cutoff = True
                break
    else:
        value = INF
        for move in moves:
            child = _make_move(state, move, -1)
            child_val = _alphabeta(child, 1, depth - 1, alpha, beta)
            if child_val < value:
                value = child_val
            if value < beta:
                beta = value
            if alpha >= beta:
                cutoff = True
                break

    if not cutoff:
        TT[key] = value
    return value


def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    global TT, DEADLINE

    state = _flatten(board)
    legal = [i for i, v in enumerate(state) if v == 0]

    if not legal:
        return (0, 0, 0)

    # If somehow called on a terminal board, still return a legal move.
    if _winner(state) != 0:
        return _coord(legal[0])

    TT = {}

    # Tactical musts first.
    wins = _immediate_wins(state, 1)
    if wins:
        best = max(wins, key=lambda m: (_move_order_score(state, m, 1), CELL_WEIGHTS[m], m))
        return _coord(best)

    opp_wins = _immediate_wins(state, -1)
    if opp_wins:
        best = max(opp_wins, key=lambda m: (_move_order_score(state, m, 1), CELL_WEIGHTS[m], m))
        return _coord(best)

    total_moves = 27 - len(legal)

    # Opening preferences.
    if total_moves <= 2 and state[CENTER] == 0:
        return _coord(CENTER)

    if total_moves == 1 and state[CENTER] == -1:
        for c in CORNERS:
            if state[c] == 0:
                return _coord(c)

    root_moves = _ordered_moves(state, 1)
    best_move = root_moves[0]

    DEADLINE = time.perf_counter() + 0.92
    empties = len(legal)

    if empties > 20:
        max_depth = 3
    elif empties > 13:
        max_depth = 4
    elif empties > 8:
        max_depth = 5
    else:
        max_depth = empties

    for depth in range(1, max_depth + 1):
        try:
            alpha = -INF
            local_best = best_move
            local_best_score = -INF
            scored = []

            for move in root_moves:
                if time.perf_counter() >= DEADLINE:
                    raise TimeoutError

                child = _make_move(state, move, 1)
                score = _alphabeta(child, -1, depth - 1, alpha, INF)
                scored.append((score, move))

                if (
                    score > local_best_score
                    or (
                        score == local_best_score
                        and _move_order_score(state, move, 1) > _move_order_score(state, local_best, 1)
                    )
                ):
                    local_best_score = score
                    local_best = move

                if local_best_score > alpha:
                    alpha = local_best_score

            scored.sort(
                key=lambda sm: (
                    sm[0],
                    _move_order_score(state, sm[1], 1),
                    CELL_WEIGHTS[sm[1]],
                    sm[1],
                ),
                reverse=True,
            )
            root_moves = [m for _, m in scored]
            best_move = local_best

            if abs(local_best_score) >= WIN - 1000:
                break

        except TimeoutError:
            break

    return _coord(best_move)
