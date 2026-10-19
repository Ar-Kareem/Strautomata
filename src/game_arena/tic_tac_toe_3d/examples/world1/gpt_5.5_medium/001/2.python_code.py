
import time
from typing import List, Tuple, Set

# ---------- Precomputed geometry for 3x3x3 Tic Tac Toe ----------

def _idx(i: int, j: int, k: int) -> int:
    return i * 9 + j * 3 + k


def _coord(index: int) -> Tuple[int, int, int]:
    return index // 9, (index % 9) // 3, index % 3


def _make_lines():
    lines = set()

    directions = []
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            for dk in (-1, 0, 1):
                if di == 0 and dj == 0 and dk == 0:
                    continue
                directions.append((di, dj, dk))

    for i in range(3):
        for j in range(3):
            for k in range(3):
                for di, dj, dk in directions:
                    cells = []
                    ok = True
                    for t in range(3):
                        ni, nj, nk = i + di * t, j + dj * t, k + dk * t
                        if not (0 <= ni < 3 and 0 <= nj < 3 and 0 <= nk < 3):
                            ok = False
                            break
                        cells.append(_idx(ni, nj, nk))
                    if ok:
                        lines.add(tuple(sorted(cells)))

    return sorted(lines)


_LINES = _make_lines()

_CELL_LINES = [[] for _ in range(27)]
for line in _LINES:
    for c in line:
        _CELL_LINES[c].append(line)

# Positional value: cells that belong to many winning lines are stronger.
_CELL_WEIGHT = [len(_CELL_LINES[i]) for i in range(27)]

_CENTER = _idx(1, 1, 1)
_CORNERS = {
    _idx(i, j, k)
    for i in (0, 2)
    for j in (0, 2)
    for k in (0, 2)
}

WIN_SCORE = 1_000_000
INF = 10_000_000


# ---------- Tactical helpers ----------

def _flatten(board: List[List[List[int]]]) -> List[int]:
    return [board[i][j][k] for i in range(3) for j in range(3) for k in range(3)]


def _winning_moves(b: List[int], player: int) -> Set[int]:
    moves = set()
    for a, c, d in _LINES:
        vals = (b[a], b[c], b[d])
        if vals.count(player) == 2 and vals.count(0) == 1:
            if b[a] == 0:
                moves.add(a)
            elif b[c] == 0:
                moves.add(c)
            else:
                moves.add(d)
    return moves


def _is_win_at(b: List[int], index: int, player: int) -> bool:
    if index < 0:
        return False
    for line in _CELL_LINES[index]:
        a, c, d = line
        if b[a] == player and b[c] == player and b[d] == player:
            return True
    return False


def _evaluate(b: List[int]) -> int:
    score = 0

    # Positional score.
    for i, v in enumerate(b):
        if v == 1:
            score += _CELL_WEIGHT[i] * 8
        elif v == -1:
            score -= _CELL_WEIGHT[i] * 8

    # Line potential score.
    for a, c, d in _LINES:
        x, y, z = b[a], b[c], b[d]
        ours = (1 if x == 1 else 0) + (1 if y == 1 else 0) + (1 if z == 1 else 0)
        opps = (1 if x == -1 else 0) + (1 if y == -1 else 0) + (1 if z == -1 else 0)

        if ours and opps:
            continue

        if ours == 3:
            return WIN_SCORE
        if opps == 3:
            return -WIN_SCORE

        if ours == 2:
            score += 850
        elif ours == 1:
            score += 35

        if opps == 2:
            score -= 950
        elif opps == 1:
            score -= 35

    # Threat and fork score.
    our_wins = _winning_moves(b, 1)
    opp_wins = _winning_moves(b, -1)

    score += len(our_wins) * 2200
    score -= len(opp_wins) * 2500

    if len(our_wins) >= 2:
        score += 5000 + 1500 * len(our_wins)
    if len(opp_wins) >= 2:
        score -= 6000 + 1800 * len(opp_wins)

    return score


def _move_order(b: List[int], player: int) -> List[int]:
    empties = [i for i, v in enumerate(b) if v == 0]

    my_wins = _winning_moves(b, player)
    blocks = _winning_moves(b, -player)

    scored = []
    for m in empties:
        s = 0

        if m in my_wins:
            s += 1_000_000
        if m in blocks:
            s += 700_000

        s += _CELL_WEIGHT[m] * 100

        if m == _CENTER:
            s += 450
        if m in _CORNERS:
            s += 220

        b[m] = player
        next_my_wins = len(_winning_moves(b, player))
        next_opp_wins = len(_winning_moves(b, -player))
        b[m] = 0

        s += next_my_wins * 3500
        if next_my_wins >= 2:
            s += 7000

        # Avoid moves that allow many immediate opponent replies.
        s -= next_opp_wins * 1200

        scored.append((s, m))

    scored.sort(reverse=True)
    return [m for _, m in scored]


def _fallback_move(b: List[int]) -> int:
    empties = [i for i, v in enumerate(b) if v == 0]
    if not empties:
        return 0

    # Win immediately.
    wins = _winning_moves(b, 1)
    if wins:
        return max(wins, key=lambda m: (_CELL_WEIGHT[m], m == _CENTER, m in _CORNERS))

    # Block immediately.
    opp_wins = _winning_moves(b, -1)
    if opp_wins:
        return max(opp_wins, key=lambda m: (_CELL_WEIGHT[m], m == _CENTER, m in _CORNERS))

    # Opening / positional priority.
    if b[_CENTER] == 0:
        return _CENTER

    # Otherwise choose best ordered move.
    ordered = _move_order(b, 1)
    return ordered[0] if ordered else empties[0]


# ---------- Required API ----------

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    b = _flatten(board)
    empties = [i for i, v in enumerate(b) if v == 0]

    # No legal move exists on a full board; this should not normally be called.
    if not empties:
        return (0, 0, 0)

    # Very strong and fast opening rule.
    if len(empties) == 27:
        return (1, 1, 1)

    fallback = _fallback_move(b)

    # If there is a forced immediate tactic, take it without spending time.
    immediate_wins = _winning_moves(b, 1)
    if immediate_wins:
        return _coord(_fallback_move(b))

    immediate_blocks = _winning_moves(b, -1)
    if immediate_blocks:
        return _coord(_fallback_move(b))

    deadline = time.perf_counter() + 0.86
    nodes = 0

    class SearchTimeout(Exception):
        pass

    def check_time():
        if time.perf_counter() > deadline:
            raise SearchTimeout()

    def alphabeta(depth: int, alpha: int, beta: int, turn: int, last_move: int) -> int:
        nonlocal nodes
        nodes += 1
        if nodes & 2047 == 0:
            check_time()

        prev = -turn
        if last_move >= 0 and _is_win_at(b, last_move, prev):
            if prev == 1:
                return WIN_SCORE + depth
            else:
                return -WIN_SCORE - depth

        if depth == 0:
            return _evaluate(b)

        if not any(v == 0 for v in b):
            return 0

        moves = _move_order(b, turn)

        if turn == 1:
            value = -INF
            for m in moves:
                b[m] = 1
                val = alphabeta(depth - 1, alpha, beta, -1, m)
                b[m] = 0

                if val > value:
                    value = val
                if value > alpha:
                    alpha = value
                if alpha >= beta:
                    break
            return value

        else:
            value = INF
            for m in moves:
                b[m] = -1
                val = alphabeta(depth - 1, alpha, beta, 1, m)
                b[m] = 0

                if val < value:
                    value = val
                if value < beta:
                    beta = value
                if alpha >= beta:
                    break
            return value

    def search_root(depth: int) -> Tuple[int, int]:
        check_time()

        moves = _move_order(b, 1)
        best_move = moves[0]
        best_value = -INF
        alpha = -INF
        beta = INF

        for m in moves:
            check_time()

            b[m] = 1
            val = alphabeta(depth - 1, alpha, beta, -1, m)
            b[m] = 0

            if val > best_value:
                best_value = val
                best_move = m

            if best_value > alpha:
                alpha = best_value

        return best_value, best_move

    best = fallback

    # Iterative deepening. The time guard keeps this under the limit.
    depth = 1
    max_depth = len(empties)

    try:
        while depth <= max_depth:
            val, move = search_root(depth)
            if b[move] == 0:
                best = move

            # If a forced win is visible, no need to search more.
            if val >= WIN_SCORE // 2:
                break

            depth += 1

    except SearchTimeout:
        pass
    except Exception:
        # Safety: never fail to return a legal move.
        best = fallback

    if best not in empties or b[best] != 0:
        best = _fallback_move(b)

    return _coord(best)
