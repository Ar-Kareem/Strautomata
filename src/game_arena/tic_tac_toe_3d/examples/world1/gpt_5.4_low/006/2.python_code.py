
from __future__ import annotations

from functools import lru_cache
from typing import List, Tuple

# ----------------------------
# Precompute all winning lines
# ----------------------------

def _generate_lines():
    lines_set = set()
    directions = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dx == dy == dz == 0:
                    continue
                # canonical direction: first nonzero component must be positive
                if dx != 0:
                    if dx > 0:
                        directions.append((dx, dy, dz))
                elif dy != 0:
                    if dy > 0:
                        directions.append((dx, dy, dz))
                else:
                    if dz > 0:
                        directions.append((dx, dy, dz))

    for x in range(3):
        for y in range(3):
            for z in range(3):
                for dx, dy, dz in directions:
                    x2, y2, z2 = x + 2 * dx, y + 2 * dy, z + 2 * dz
                    if 0 <= x2 < 3 and 0 <= y2 < 3 and 0 <= z2 < 3:
                        line = ((x, y, z), (x + dx, y + dy, z + dz), (x2, y2, z2))
                        lines_set.add(tuple(sorted(line)))
    lines = [list(line) for line in sorted(lines_set)]
    return lines

LINES = _generate_lines()  # 49 lines

CELL_TO_LINES = {(i, j, k): [] for i in range(3) for j in range(3) for k in range(3)}
for idx, line in enumerate(LINES):
    for cell in line:
        CELL_TO_LINES[cell].append(idx)

CELL_WEIGHTS = {}
for cell, line_ids in CELL_TO_LINES.items():
    # Number of winning lines passing through the cell is a good positional weight
    CELL_WEIGHTS[cell] = len(line_ids)

# --------------
# Board helpers
# --------------

def _flatten(board: List[List[List[int]]]) -> Tuple[int, ...]:
    return tuple(board[i][j][k] for i in range(3) for j in range(3) for k in range(3))

def _legal_moves_from_flat(flat: Tuple[int, ...]):
    for idx, v in enumerate(flat):
        if v == 0:
            yield (idx // 9, (idx % 9) // 3, idx % 3)

def _set_cell(flat: Tuple[int, ...], move: Tuple[int, int, int], player: int) -> Tuple[int, ...]:
    idx = move[0] * 9 + move[1] * 3 + move[2]
    lst = list(flat)
    lst[idx] = player
    return tuple(lst)

def _cell_value(flat: Tuple[int, ...], cell: Tuple[int, int, int]) -> int:
    return flat[cell[0] * 9 + cell[1] * 3 + cell[2]]

@lru_cache(maxsize=None)
def _winner(flat: Tuple[int, ...]) -> int:
    for line in LINES:
        s = 0
        for c in line:
            s += _cell_value(flat, c)
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0

def _count_empty(flat: Tuple[int, ...]) -> int:
    return flat.count(0)

def _legal_moves_list(flat: Tuple[int, ...]):
    return list(_legal_moves_from_flat(flat))

# -------------------
# Tactical primitives
# -------------------

def _winning_moves(flat: Tuple[int, ...], player: int):
    wins = []
    for mv in _legal_moves_from_flat(flat):
        new_flat = _set_cell(flat, mv, player)
        if _winner(new_flat) == player:
            wins.append(mv)
    return wins

def _fork_moves(flat: Tuple[int, ...], player: int):
    forks = []
    for mv in _legal_moves_from_flat(flat):
        new_flat = _set_cell(flat, mv, player)
        wins = _winning_moves(new_flat, player)
        if len(wins) >= 2:
            forks.append(mv)
    return forks

# -----------------
# Heuristic scoring
# -----------------

@lru_cache(maxsize=None)
def _evaluate(flat: Tuple[int, ...]) -> int:
    w = _winner(flat)
    if w == 1:
        return 1_000_000
    if w == -1:
        return -1_000_000

    score = 0

    # Line-based evaluation
    # Reward uncontested lines for us; penalize uncontested lines for opponent.
    for line in LINES:
        vals = [_cell_value(flat, c) for c in line]
        c1 = vals.count(1)
        c2 = vals.count(-1)
        c0 = vals.count(0)

        if c1 and c2:
            continue

        if c1 == 2 and c0 == 1:
            score += 120
        elif c1 == 1 and c0 == 2:
            score += 12
        elif c1 == 3:
            score += 10_000

        if c2 == 2 and c0 == 1:
            score -= 150
        elif c2 == 1 and c0 == 2:
            score -= 14
        elif c2 == 3:
            score -= 10_000

    # Positional weight: cells participating in many lines are stronger.
    for i in range(3):
        for j in range(3):
            for k in range(3):
                v = flat[i * 9 + j * 3 + k]
                if v != 0:
                    score += v * CELL_WEIGHTS[(i, j, k)] * 3

    return score

def _move_order_score(flat: Tuple[int, ...], mv: Tuple[int, int, int], player: int) -> int:
    # Fast move ordering for alpha-beta
    base = CELL_WEIGHTS[mv] * 10
    new_flat = _set_cell(flat, mv, player)
    w = _winner(new_flat)
    if w == player:
        return 1_000_000
    # Prefer creating threats / blocking key cells
    val = _evaluate(new_flat)
    return base + (val if player == 1 else -val)

# --------------------
# Alpha-beta minimax
# --------------------

def _search_depth(empty_count: int) -> int:
    if empty_count >= 22:
        return 2
    if empty_count >= 16:
        return 3
    if empty_count >= 10:
        return 4
    if empty_count >= 7:
        return 5
    return 8  # near endgame

@lru_cache(maxsize=None)
def _minimax(flat: Tuple[int, ...], player: int, depth: int, alpha: int, beta: int) -> int:
    w = _winner(flat)
    if w == 1:
        return 1_000_000 + depth
    if w == -1:
        return -1_000_000 - depth

    legal = _legal_moves_list(flat)
    if not legal:
        return 0
    if depth == 0:
        return _evaluate(flat)

    ordered = sorted(legal, key=lambda mv: _move_order_score(flat, mv, player), reverse=True)

    if player == 1:
        best = -10**18
        for mv in ordered:
            nxt = _set_cell(flat, mv, 1)
            val = _minimax(nxt, -1, depth - 1, alpha, beta)
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        return best
    else:
        best = 10**18
        for mv in ordered:
            nxt = _set_cell(flat, mv, -1)
            val = _minimax(nxt, 1, depth - 1, alpha, beta)
            if val < best:
                best = val
            if best < beta:
                beta = best
            if alpha >= beta:
                break
        return best

# -------------
# Main policy
# -------------

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    flat = _flatten(board)
    legal = _legal_moves_list(flat)

    # Guaranteed legal fallback
    if not legal:
        return (0, 0, 0)
    fallback = legal[0]

    # 1) Immediate win
    my_wins = _winning_moves(flat, 1)
    if my_wins:
        return max(my_wins, key=lambda mv: CELL_WEIGHTS[mv])

    # 2) Immediate block
    opp_wins = _winning_moves(flat, -1)
    if opp_wins:
        # If multiple, any blocking move among them is good; choose strongest square.
        blocking = [mv for mv in opp_wins if mv in legal]
        if blocking:
            return max(blocking, key=lambda mv: CELL_WEIGHTS[mv])

    # 3) Create fork
    my_forks = _fork_moves(flat, 1)
    if my_forks:
        return max(my_forks, key=lambda mv: CELL_WEIGHTS[mv])

    # 4) Block opponent fork
    opp_forks = _fork_moves(flat, -1)
    if len(opp_forks) == 1:
        return opp_forks[0]
    elif len(opp_forks) > 1:
        # Choose a move that minimizes opponent fork opportunities after our play.
        best_mv = fallback
        best_key = None
        for mv in legal:
            nxt = _set_cell(flat, mv, 1)
            remaining_opp_forks = len(_fork_moves(nxt, -1))
            # Prefer also moves with strong heuristic value
            key = (remaining_opp_forks, -_evaluate(nxt), -CELL_WEIGHTS[mv])
            if best_key is None or key < best_key:
                best_key = key
                best_mv = mv
        return best_mv

    # 5) Search
    depth = _search_depth(_count_empty(flat))
    ordered = sorted(legal, key=lambda mv: _move_order_score(flat, mv, 1), reverse=True)

    best_score = -10**18
    best_move = fallback
    alpha = -10**18
    beta = 10**18

    for mv in ordered:
        nxt = _set_cell(flat, mv, 1)
        score = _minimax(nxt, -1, depth - 1, alpha, beta)
        if score > best_score:
            best_score = score
            best_move = mv
        if score > alpha:
            alpha = score

    # Final legality check
    if _cell_value(flat, best_move) == 0:
        return best_move
    return fallback
