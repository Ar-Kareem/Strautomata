
"""
3x3x3 3D Tic Tac Toe policy.

API:
    def policy(board: list[list[list[int]]]) -> tuple[int, int, int]

Board encoding:
    0 empty, 1 us, -1 opponent.

Approach:
    - Precompute all 49 winning lines.
    - Immediate win > immediate block.
    - Iterative deepening minimax with alpha-beta and transposition table.
    - Heuristic evaluation based on open lines and cell connectivity.
"""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import List, Tuple, Dict, Optional


# -------------------- Precomputation: lines, helpers --------------------

def _idx(i: int, j: int, k: int) -> int:
    return i * 9 + j * 3 + k


def _coord(index: int) -> Tuple[int, int, int]:
    i = index // 9
    r = index % 9
    j = r // 3
    k = r % 3
    return i, j, k


def _generate_lines() -> List[Tuple[int, int, int]]:
    lines: List[Tuple[int, int, int]] = []

    # Axis-aligned lines
    for j in range(3):
        for k in range(3):
            lines.append((_idx(0, j, k), _idx(1, j, k), _idx(2, j, k)))  # x
    for i in range(3):
        for k in range(3):
            lines.append((_idx(i, 0, k), _idx(i, 1, k), _idx(i, 2, k)))  # y
    for i in range(3):
        for j in range(3):
            lines.append((_idx(i, j, 0), _idx(i, j, 1), _idx(i, j, 2)))  # z

    # Plane diagonals: x fixed (i), diagonals in (j,k)
    for i in range(3):
        lines.append((_idx(i, 0, 0), _idx(i, 1, 1), _idx(i, 2, 2)))
        lines.append((_idx(i, 0, 2), _idx(i, 1, 1), _idx(i, 2, 0)))

    # Plane diagonals: y fixed (j), diagonals in (i,k)
    for j in range(3):
        lines.append((_idx(0, j, 0), _idx(1, j, 1), _idx(2, j, 2)))
        lines.append((_idx(0, j, 2), _idx(1, j, 1), _idx(2, j, 0)))

    # Plane diagonals: z fixed (k), diagonals in (i,j)
    for k in range(3):
        lines.append((_idx(0, 0, k), _idx(1, 1, k), _idx(2, 2, k)))
        lines.append((_idx(0, 2, k), _idx(1, 1, k), _idx(2, 0, k)))

    # Space diagonals (4)
    lines.append((_idx(0, 0, 0), _idx(1, 1, 1), _idx(2, 2, 2)))
    lines.append((_idx(0, 0, 2), _idx(1, 1, 1), _idx(2, 2, 0)))
    lines.append((_idx(0, 2, 0), _idx(1, 1, 1), _idx(2, 0, 2)))
    lines.append((_idx(0, 2, 2), _idx(1, 1, 1), _idx(2, 0, 0)))

    # Sanity: should be 49
    # assert len(lines) == 49
    return lines


LINES: List[Tuple[int, int, int]] = _generate_lines()

# For each cell, which lines contain it?
CELL_LINES: List[List[Tuple[int, int, int]]] = [[] for _ in range(27)]
for line in LINES:
    for c in line:
        CELL_LINES[c].append(line)

# Cell connectivity weight: number of winning lines passing through cell.
CELL_CONNECTIVITY: List[int] = [len(CELL_LINES[i]) for i in range(27)]

# Preferred move ordering by connectivity then center-ish bias
CENTER_IDX = _idx(1, 1, 1)


# -------------------- Core evaluation / tactics --------------------

WIN_SCORE = 100000
# Heuristic weights
TWO_IN_ROW_US = 220
TWO_IN_ROW_OPP = 260  # slightly larger: prioritize blocking
ONE_IN_ROW = 4
CONNECTIVITY_BONUS = 2  # multiplied by CELL_CONNECTIVITY


def _check_winner(cells: List[int]) -> int:
    """Return 1 if us win, -1 if opponent win, 0 otherwise."""
    for a, b, c in LINES:
        s = cells[a] + cells[b] + cells[c]
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0


def _evaluate(cells: List[int]) -> int:
    """
    Static evaluation from our perspective.
    Positive is good for us (1), negative is good for opponent (-1).
    """
    w = _check_winner(cells)
    if w == 1:
        return WIN_SCORE
    if w == -1:
        return -WIN_SCORE

    score = 0

    # Line-based evaluation: open lines and threats
    for a, b, c in LINES:
        line = (cells[a], cells[b], cells[c])
        cnt_us = (line[0] == 1) + (line[1] == 1) + (line[2] == 1)
        cnt_opp = (line[0] == -1) + (line[1] == -1) + (line[2] == -1)
        if cnt_us and cnt_opp:
            continue  # blocked line

        if cnt_us == 2 and cnt_opp == 0:
            score += TWO_IN_ROW_US
        elif cnt_opp == 2 and cnt_us == 0:
            score -= TWO_IN_ROW_OPP
        elif cnt_us == 1 and cnt_opp == 0:
            score += ONE_IN_ROW
        elif cnt_opp == 1 and cnt_us == 0:
            score -= ONE_IN_ROW

    # Positional: favor high-connectivity empty control (already placed pieces matter too)
    # This is mild to avoid overriding tactics.
    for idx in range(27):
        v = cells[idx]
        if v == 1:
            score += CONNECTIVITY_BONUS * CELL_CONNECTIVITY[idx]
        elif v == -1:
            score -= CONNECTIVITY_BONUS * CELL_CONNECTIVITY[idx]

    # Tiny extra preference for owning center (it has max connectivity anyway)
    if cells[CENTER_IDX] == 1:
        score += 3
    elif cells[CENTER_IDX] == -1:
        score -= 3

    return score


def _winning_moves(cells: List[int], player: int) -> List[int]:
    """Return list of empty indices that win immediately for 'player'."""
    wins: List[int] = []
    for m in range(27):
        if cells[m] != 0:
            continue
        # Check only lines containing this cell
        for a, b, c in CELL_LINES[m]:
            s = cells[a] + cells[b] + cells[c]
            # If we place at m, sum increases by player
            if s + player == 3 * player:
                wins.append(m)
                break
    return wins


def _forced_blocks(cells: List[int], player: int) -> List[int]:
    """
    Return list of empty indices that block opponent's immediate win.
    If non-empty, the current player must play one of these (unless they can win immediately).
    """
    opp = -player
    blocks: List[int] = []
    for m in range(27):
        if cells[m] != 0:
            continue
        for a, b, c in CELL_LINES[m]:
            s = cells[a] + cells[b] + cells[c]
            # If opponent would place at m and win:
            if s + opp == 3 * opp:
                blocks.append(m)
                break
    return blocks


def _order_moves(cells: List[int], moves: List[int], player: int) -> List[int]:
    """
    Strong move ordering:
      - higher connectivity first
      - slight preference for center
    """
    def key(m: int) -> Tuple[int, int]:
        # primary: connectivity, secondary: center proximity (exact center best)
        center_bonus = 3 if m == CENTER_IDX else 0
        return (CELL_CONNECTIVITY[m] * 10 + center_bonus, 0)

    return sorted(moves, key=key, reverse=True)


# -------------------- Search (iterative deepening alpha-beta) --------------------

@dataclass
class TTEntry:
    depth: int
    score: int
    best_move: Optional[int]


class _Timeout(Exception):
    pass


def _alphabeta(
    cells: List[int],
    depth: int,
    alpha: int,
    beta: int,
    player: int,
    ply: int,
    tt: Dict[Tuple[Tuple[int, ...], int], TTEntry],
    t0: float,
    time_limit: float,
) -> Tuple[int, Optional[int]]:
    if time.perf_counter() - t0 > time_limit:
        raise _Timeout

    key = (tuple(cells), player)
    ent = tt.get(key)
    if ent is not None and ent.depth >= depth:
        return ent.score, ent.best_move

    winner = _check_winner(cells)
    if winner != 0:
        # Prefer faster wins and slower losses
        if winner == 1:
            return (WIN_SCORE - ply), None
        else:
            return (-WIN_SCORE + ply), None

    # Draw / no moves
    empties = [i for i in range(27) if cells[i] == 0]
    if not empties:
        return 0, None

    if depth == 0:
        return _evaluate(cells), None

    # Tactical reduction: if player has immediate win, only consider those.
    win_moves = _winning_moves(cells, player)
    if win_moves:
        # Any of these wins; pick best (doesn't matter much but keep deterministic)
        win_moves = _order_moves(cells, win_moves, player)
        m = win_moves[0]
        cells[m] = player
        score, _ = _alphabeta(cells, depth - 1, alpha, beta, -player, ply + 1, tt, t0, time_limit)
        cells[m] = 0
        # Store exact
        tt[key] = TTEntry(depth=depth, score=score, best_move=m)
        return score, m

    # If must block opponent win, restrict to block moves
    block_moves = _forced_blocks(cells, player)
    if block_moves:
        moves = _order_moves(cells, block_moves, player)
    else:
        moves = _order_moves(cells, empties, player)

    best_move: Optional[int] = None

    if player == 1:
        value = -10**9
        for m in moves:
            cells[m] = 1
            sc, _ = _alphabeta(cells, depth - 1, alpha, beta, -1, ply + 1, tt, t0, time_limit)
            cells[m] = 0
            if sc > value:
                value = sc
                best_move = m
            alpha = max(alpha, value)
            if alpha >= beta:
                break
    else:
        value = 10**9
        for m in moves:
            cells[m] = -1
            sc, _ = _alphabeta(cells, depth - 1, alpha, beta, 1, ply + 1, tt, t0, time_limit)
            cells[m] = 0
            if sc < value:
                value = sc
                best_move = m
            beta = min(beta, value)
            if alpha >= beta:
                break

    tt[key] = TTEntry(depth=depth, score=value, best_move=best_move)
    return value, best_move


# -------------------- Public API --------------------

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Flatten board to 1D
    cells = [0] * 27
    for i in range(3):
        for j in range(3):
            for k in range(3):
                cells[_idx(i, j, k)] = int(board[i][j][k])

    empties = [i for i in range(27) if cells[i] == 0]
    if not empties:
        return (0, 0, 0)  # Should not happen in normal play

    # 1) Immediate win
    win_now = _winning_moves(cells, 1)
    if win_now:
        m = _order_moves(cells, win_now, 1)[0]
        return _coord(m)

    # 2) Immediate block
    blocks = _forced_blocks(cells, 1)
    if blocks:
        m = _order_moves(cells, blocks, 1)[0]
        return _coord(m)

    # 3) Iterative deepening alpha-beta
    t0 = time.perf_counter()
    time_limit = 0.92  # seconds; keep margin
    tt: Dict[Tuple[Tuple[int, ...], int], TTEntry] = {}

    # Default fallback: best connectivity move
    ordered = _order_moves(cells, empties, 1)
    best_move = ordered[0]
    best_score = -10**9

    # Depth schedule: increase while time allows
    max_depth = min(empties.__len__(), 10)  # practical cap
    for depth in range(1, max_depth + 1):
        try:
            score, move = _alphabeta(
                cells=cells,
                depth=depth,
                alpha=-10**9,
                beta=10**9,
                player=1,
                ply=0,
                tt=tt,
                t0=t0,
                time_limit=time_limit,
            )
            if move is not None:
                best_move = move
                best_score = score
            # Early exit if clearly winning
            if best_score >= WIN_SCORE - 5:
                break
        except _Timeout:
            break

    # Safety: ensure legal
    if cells[best_move] != 0:
        for m in empties:
            if cells[m] == 0:
                best_move = m
                break

    return _coord(best_move)
