
# 3x3x3 Tic Tac Toe policy
# Returns a legal move tuple (i, j, k) for player 1.

from __future__ import annotations

import time
from typing import List, Tuple, Set, Dict

N = 3
WIN_SCORE = 1_000_000
INF = 10_000_000

# ---------------------------------------------------------------------
# Precompute all 3-cell winning lines in a 3x3x3 cube.
# There are 49 such lines.
# ---------------------------------------------------------------------

def _idx(i: int, j: int, k: int) -> int:
    return i * 9 + j * 3 + k

def _coord(idx: int) -> Tuple[int, int, int]:
    return idx // 9, (idx % 9) // 3, idx % 3

def _inside(i: int, j: int, k: int) -> bool:
    return 0 <= i < 3 and 0 <= j < 3 and 0 <= k < 3

def _generate_lines() -> List[Tuple[int, int, int]]:
    dirs = []
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            for dk in (-1, 0, 1):
                if di == dj == dk == 0:
                    continue
                # Keep only one direction from each +/- pair.
                if (di, dj, dk) < (0, 0, 0):
                    continue
                dirs.append((di, dj, dk))

    lines = []
    seen = set()

    for di, dj, dk in dirs:
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    pi, pj, pk = i - di, j - dj, k - dk
                    if _inside(pi, pj, pk):
                        continue

                    cells = []
                    ok = True
                    for t in range(3):
                        ni, nj, nk = i + t * di, j + t * dj, k + t * dk
                        if not _inside(ni, nj, nk):
                            ok = False
                            break
                        cells.append(_idx(ni, nj, nk))

                    if ok:
                        key = tuple(sorted(cells))
                        if key not in seen:
                            seen.add(key)
                            lines.append(tuple(cells))

    return lines

LINES = _generate_lines()

CELL_LINES: List[List[Tuple[int, int, int]]] = [[] for _ in range(27)]
for line in LINES:
    for c in line:
        CELL_LINES[c].append(line)

# Number of winning lines through each cell: center is strongest.
CELL_WEIGHT = [len(CELL_LINES[c]) for c in range(27)]

# A small transposition table retained across calls.
_TT: Dict[Tuple[Tuple[int, ...], int, int], int] = {}


# ---------------------------------------------------------------------
# Basic board helpers
# ---------------------------------------------------------------------

def _flatten(board: List[List[List[int]]]) -> Tuple[int, ...]:
    vals = []
    for i in range(3):
        for j in range(3):
            for k in range(3):
                v = board[i][j][k]
                vals.append(1 if v == 1 else (-1 if v == -1 else 0))
    return tuple(vals)

def _legal_moves(state: Tuple[int, ...]) -> List[int]:
    return [i for i, v in enumerate(state) if v == 0]

def _place(state: Tuple[int, ...], move: int, side: int) -> Tuple[int, ...]:
    return state[:move] + (side,) + state[move + 1:]

def _has_win(state: Tuple[int, ...], side: int) -> bool:
    for a, b, c in LINES:
        if state[a] == side and state[b] == side and state[c] == side:
            return True
    return False

def _is_win_after_move(state: Tuple[int, ...], move: int, side: int) -> bool:
    for a, b, c in CELL_LINES[move]:
        s = state[a] + state[b] + state[c] + side
        # Since state[move] is currently 0 and side is added once,
        # a completed side line has sum 3*side.
        if s == 3 * side:
            return True
    return False

def _threat_cells(state: Tuple[int, ...], side: int) -> Set[int]:
    """Cells where side could win immediately."""
    threats: Set[int] = set()
    target = 2 * side
    for line in LINES:
        vals = (state[line[0]], state[line[1]], state[line[2]])
        if vals[0] + vals[1] + vals[2] == target:
            for c in line:
                if state[c] == 0:
                    threats.add(c)
                    break
    return threats


# ---------------------------------------------------------------------
# Evaluation and move ordering
# ---------------------------------------------------------------------

def _evaluate(state: Tuple[int, ...], side: int) -> int:
    """Heuristic value from the perspective of side-to-move."""
    if _has_win(state, side):
        return WIN_SCORE
    if _has_win(state, -side):
        return -WIN_SCORE

    score = 0

    # Positional value: cells involved in more lines are more valuable.
    for c, v in enumerate(state):
        if v == side:
            score += CELL_WEIGHT[c] * 5
        elif v == -side:
            score -= CELL_WEIGHT[c] * 6

    # Line potential.
    for a, b, c in LINES:
        vals = (state[a], state[b], state[c])
        mine = vals.count(side)
        opp = vals.count(-side)

        if mine and opp:
            continue

        if opp == 0:
            if mine == 1:
                score += 12
            elif mine == 2:
                score += 260
        elif mine == 0:
            if opp == 1:
                score -= 14
            elif opp == 2:
                score -= 320

    # Distinct immediate threats matter greatly; two threats are usually decisive.
    my_threats = len(_threat_cells(state, side))
    opp_threats = len(_threat_cells(state, -side))
    score += 170 * my_threats * my_threats
    score -= 230 * opp_threats * opp_threats

    return score

def _ordered_moves(state: Tuple[int, ...], side: int) -> List[int]:
    moves = _legal_moves(state)
    opp_threats = _threat_cells(state, -side)

    scored = []
    for m in moves:
        s = CELL_WEIGHT[m] * 20

        if _is_win_after_move(state, m, side):
            s += 1_000_000

        if m in opp_threats:
            s += 80_000

        ns = _place(state, m, side)
        my_t = len(_threat_cells(ns, side))
        opp_t = len(_threat_cells(ns, -side))

        s += my_t * 1200
        s -= opp_t * 1600

        # Local line promise around the candidate move.
        for line in CELL_LINES[m]:
            mine = 0
            opp = 0
            for c in line:
                v = ns[c]
                if v == side:
                    mine += 1
                elif v == -side:
                    opp += 1

            if opp == 0:
                if mine == 1:
                    s += 20
                elif mine == 2:
                    s += 600
            elif mine == 0:
                if opp == 1:
                    s -= 20
                elif opp == 2:
                    s -= 700

        scored.append((s, m))

    scored.sort(reverse=True)
    return [m for _, m in scored]


# ---------------------------------------------------------------------
# Alpha-beta negamax search with a time guard
# ---------------------------------------------------------------------

def _search_best_move(
    state: Tuple[int, ...],
    max_depth: int,
    deadline: float,
) -> int | None:
    nodes = 0

    def negamax(
        st: Tuple[int, ...],
        side: int,
        depth: int,
        alpha: int,
        beta: int,
    ) -> int:
        nonlocal nodes
        nodes += 1

        if (nodes & 255) == 0 and time.perf_counter() > deadline:
            raise TimeoutError

        # In a normal game, if there is already a win, it was made by the
        # previous player.
        if _has_win(st, -side):
            return -WIN_SCORE - depth
        if _has_win(st, side):
            return WIN_SCORE + depth

        moves = _legal_moves(st)
        if not moves:
            return 0

        if depth <= 0:
            return _evaluate(st, side)

        key = (st, side, depth)
        if key in _TT:
            return _TT[key]

        best = -INF
        complete = True

        for m in _ordered_moves(st, side):
            if _is_win_after_move(st, m, side):
                val = WIN_SCORE + depth
            else:
                ns = _place(st, m, side)
                val = -negamax(ns, -side, depth - 1, -beta, -alpha)

            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                complete = False
                break

        if complete:
            if len(_TT) > 200_000:
                _TT.clear()
            _TT[key] = best

        return best

    best_move = None
    best_score = -INF

    for m in _ordered_moves(state, 1):
        if time.perf_counter() > deadline:
            raise TimeoutError

        if _is_win_after_move(state, m, 1):
            score = WIN_SCORE + max_depth
        else:
            ns = _place(state, m, 1)
            score = -negamax(ns, -1, max_depth - 1, -INF, INF)

        if score > best_score:
            best_score = score
            best_move = m

    return best_move


# ---------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    Return a legal empty cell as (i, j, k).
    Player 1 is this policy, player -1 is the opponent.
    """
    try:
        state = _flatten(board)
    except Exception:
        # Extremely defensive fallback for malformed input.
        return (0, 0, 0)

    legal = _legal_moves(state)
    if not legal:
        return (0, 0, 0)

    # Failsafe default: best static legal cell.
    fallback = max(legal, key=lambda m: CELL_WEIGHT[m])

    # 1. Win immediately if possible.
    winning = [m for m in legal if _is_win_after_move(state, m, 1)]
    if winning:
        return _coord(max(winning, key=lambda m: CELL_WEIGHT[m]))

    # 2. If opponent has exactly one immediate winning cell, block it.
    opp_wins = _threat_cells(state, -1)
    if len(opp_wins) == 1:
        m = next(iter(opp_wins))
        if state[m] == 0:
            return _coord(m)

    # 3. Opening preferences.
    occupied = 27 - len(legal)
    center = _idx(1, 1, 1)

    if occupied == 0:
        return (1, 1, 1)

    if occupied == 1:
        if state[center] == 0:
            return (1, 1, 1)
        # If opponent took center, choose a corner.
        corners = [
            _idx(i, j, k)
            for i in (0, 2)
            for j in (0, 2)
            for k in (0, 2)
            if state[_idx(i, j, k)] == 0
        ]
        if corners:
            return _coord(corners[0])

    # 4. If there is no immediate danger, create a fork if possible.
    # A move producing two distinct immediate winning cells is usually a forced win.
    if not opp_wins:
        fork_moves = []
        for m in legal:
            ns = _place(state, m, 1)
            if len(_threat_cells(ns, 1)) >= 2:
                fork_moves.append(m)
        if fork_moves:
            return _coord(max(fork_moves, key=lambda m: CELL_WEIGHT[m]))

    # 5. Otherwise use iterative deepening alpha-beta search.
    empties = len(legal)
    if empties <= 8:
        max_depth = empties
    elif empties <= 12:
        max_depth = 9
    elif empties <= 16:
        max_depth = 7
    elif empties <= 22:
        max_depth = 6
    else:
        max_depth = 5

    deadline = time.perf_counter() + 0.85
    best = fallback

    try:
        for depth in range(1, max_depth + 1):
            if time.perf_counter() > deadline:
                break
            candidate = _search_best_move(state, depth, deadline)
            if candidate is not None and state[candidate] == 0:
                best = candidate
    except TimeoutError:
        pass
    except Exception:
        best = fallback

    # Final legality guard.
    if best not in legal:
        best = fallback
    if state[best] != 0:
        for m in legal:
            if state[m] == 0:
                best = m
                break

    return _coord(best)
