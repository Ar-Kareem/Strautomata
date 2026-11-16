
import time
from typing import List, Tuple, Optional, Dict

# Public API:
# def policy(board: list[list[list[int]]]) -> tuple[int, int, int]


# ---------------------------
# Precompute winning lines
# ---------------------------

def _generate_winning_lines_3x3x3():
    # Generate all unique length-3 lines in a 3x3x3 grid using direction vectors.
    dirs = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dx == dy == dz == 0:
                    continue
                # Keep each undirected direction once
                # Choose canonical: first nonzero component positive
                # (or lexicographically positive if earlier components zero)
                if dx != 0:
                    if dx < 0:
                        continue
                elif dy != 0:
                    if dy < 0:
                        continue
                else:
                    if dz < 0:
                        continue
                dirs.append((dx, dy, dz))

    lines = []
    seen = set()
    for dx, dy, dz in dirs:
        for x in range(3):
            for y in range(3):
                for z in range(3):
                    x2, y2, z2 = x + 2 * dx, y + 2 * dy, z + 2 * dz
                    if 0 <= x2 < 3 and 0 <= y2 < 3 and 0 <= z2 < 3:
                        coords = [(x + t * dx, y + t * dy, z + t * dz) for t in range(3)]
                        key = tuple(coords)
                        # Avoid duplicates (should be rare with canonical dirs, but keep robust)
                        if key not in seen:
                            seen.add(key)
                            lines.append(coords)
    return lines


WIN_LINES = _generate_winning_lines_3x3x3()  # should be 49 for 3x3x3

# Precompute cell positional weights (center > corners > edges)
POS_W = [[[0 for _ in range(3)] for _ in range(3)] for _ in range(3)]
for i in range(3):
    for j in range(3):
        for k in range(3):
            # Manhattan distance to center (1,1,1)
            d = abs(i - 1) + abs(j - 1) + abs(k - 1)
            if d == 0:
                POS_W[i][j][k] = 6   # center
            elif d == 1:
                POS_W[i][j][k] = 3   # face-centers
            elif d == 2:
                POS_W[i][j][k] = 2   # edge-centers
            else:
                POS_W[i][j][k] = 4   # corners (d==3), corners are strong in 3D


# Base-3 encoding helpers for transposition table
POW3 = [1]
for _ in range(27):
    POW3.append(POW3[-1] * 3)

def _encode_board(board: List[List[List[int]]]) -> int:
    # Map: 0->0, 1->1, -1->2 in base-3
    code = 0
    idx = 0
    for i in range(3):
        for j in range(3):
            for k in range(3):
                v = board[i][j][k]
                d = 0 if v == 0 else (1 if v == 1 else 2)
                code += d * POW3[idx]
                idx += 1
    return code


# ---------------------------
# Game logic
# ---------------------------

def _check_win(board: List[List[List[int]]], player: int) -> bool:
    for line in WIN_LINES:
        if all(board[i][j][k] == player for (i, j, k) in line):
            return True
    return False

def _empties(board: List[List[List[int]]]) -> List[Tuple[int, int, int]]:
    out = []
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    out.append((i, j, k))
    return out

def _heuristic(board: List[List[List[int]]]) -> int:
    # Evaluate from perspective of player 1 (us).
    # Open line scoring: weights grow sharply for 2-in-a-row.
    w = [0, 2, 30, 100000]  # 3 is terminal-like; real terminal handled separately
    score = 0

    # Line-based evaluation
    for line in WIN_LINES:
        c1 = 0
        c2 = 0
        for (i, j, k) in line:
            v = board[i][j][k]
            if v == 1:
                c1 += 1
            elif v == -1:
                c2 += 1
        if c1 and c2:
            continue  # blocked line
        if c1:
            score += w[c1]
        elif c2:
            score -= w[c2]

    # Positional tie-breaker
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 1:
                    score += POS_W[i][j][k]
                elif board[i][j][k] == -1:
                    score -= POS_W[i][j][k]

    return score


# ---------------------------
# Search (iterative deepening alpha-beta)
# ---------------------------

INF = 10**12

class _SearchTimeout(Exception):
    pass

def _order_moves(board: List[List[List[int]]], moves: List[Tuple[int, int, int]]) -> List[Tuple[int, int, int]]:
    # Strong move ordering:
    # 1) immediate wins
    # 2) immediate blocks
    # 3) otherwise by (positional + quick heuristic delta) descending
    win_moves = []
    block_moves = []
    scored = []

    for (i, j, k) in moves:
        # Try as us
        board[i][j][k] = 1
        if _check_win(board, 1):
            board[i][j][k] = 0
            win_moves.append((i, j, k))
            continue
        board[i][j][k] = 0

        # Try as opponent (block)
        board[i][j][k] = -1
        if _check_win(board, -1):
            board[i][j][k] = 0
            block_moves.append((i, j, k))
            continue
        board[i][j][k] = 0

        # Score move quickly
        base = POS_W[i][j][k]
        # Small local line potential estimate:
        # count how many lines through this cell are still open for us and for opponent
        pot = 0
        for line in WIN_LINES:
            if (i, j, k) not in line:
                continue
            c1 = c2 = 0
            for (a, b, c) in line:
                v = board[a][b][c]
                if v == 1:
                    c1 += 1
                elif v == -1:
                    c2 += 1
            if c2 == 0:
                pot += (1 + 4 * c1)
            if c1 == 0:
                pot += (1 + 2 * c2)
        scored.append((base + pot, (i, j, k)))

    if win_moves:
        return win_moves
    if block_moves:
        # Still consider multiple blocks if exist
        return block_moves

    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in scored]

def _minimax(
    board: List[List[List[int]]],
    depth: int,
    alpha: int,
    beta: int,
    to_move: int,
    end_time: float,
    tt: Dict[Tuple[int, int, int], int],
) -> int:
    if time.perf_counter() >= end_time:
        raise _SearchTimeout()

    # Terminal checks
    if _check_win(board, 1):
        return 10**9 + depth  # prefer faster wins
    if _check_win(board, -1):
        return -10**9 - depth  # prefer slower losses

    moves = _empties(board)
    if not moves:
        return 0  # draw

    if depth == 0:
        return _heuristic(board)

    key = (_encode_board(board), to_move, depth)
    if key in tt:
        return tt[key]

    # Move ordering
    moves = _order_moves(board, moves)

    if to_move == 1:
        best = -INF
        for (i, j, k) in moves:
            board[i][j][k] = 1
            val = _minimax(board, depth - 1, alpha, beta, -1, end_time, tt)
            board[i][j][k] = 0
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
    else:
        best = INF
        for (i, j, k) in moves:
            board[i][j][k] = -1
            val = _minimax(board, depth - 1, alpha, beta, 1, end_time, tt)
            board[i][j][k] = 0
            if val < best:
                best = val
            if best < beta:
                beta = best
            if alpha >= beta:
                break

    tt[key] = best
    return best


def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    # Safety: ensure we always return a legal move.
    moves = _empties(board)
    if not moves:
        return (0, 0, 0)

    # Immediate win
    for (i, j, k) in moves:
        board[i][j][k] = 1
        if _check_win(board, 1):
            board[i][j][k] = 0
            return (i, j, k)
        board[i][j][k] = 0

    # Immediate block
    for (i, j, k) in moves:
        board[i][j][k] = -1
        if _check_win(board, -1):
            board[i][j][k] = 0
            return (i, j, k)
        board[i][j][k] = 0

    # Strong opening preference: center if available
    if board[1][1][1] == 0:
        return (1, 1, 1)

    # Iterative deepening minimax with alpha-beta and TT
    # Depth cap chosen for time; will stop early on timeout.
    start = time.perf_counter()
    end_time = start + 0.95  # keep margin within 1s

    tt: Dict[Tuple[int, int, int], int] = {}

    # Order root moves
    root_moves = _order_moves(board, moves)

    best_move = root_moves[0]
    best_val = -INF

    # Depth schedule: deeper as board empties shrink
    empties_n = len(moves)
    max_depth = 4
    if empties_n <= 18:
        max_depth = 5
    if empties_n <= 14:
        max_depth = 6
    if empties_n <= 10:
        max_depth = 7

    for depth in range(1, max_depth + 1):
        if time.perf_counter() >= end_time:
            break
        cur_best_move = best_move
        cur_best_val = -INF
        alpha = -INF
        beta = INF

        try:
            for (i, j, k) in root_moves:
                if time.perf_counter() >= end_time:
                    raise _SearchTimeout()

                board[i][j][k] = 1
                val = _minimax(board, depth - 1, alpha, beta, -1, end_time, tt)
                board[i][j][k] = 0

                if val > cur_best_val:
                    cur_best_val = val
                    cur_best_move = (i, j, k)
                if val > alpha:
                    alpha = val

            # If we completed this depth, accept it
            best_move = cur_best_move
            best_val = cur_best_val

            # Reorder root moves by last iteration results (principal variation first)
            # Simple reorder: move best to front.
            if best_move in root_moves:
                root_moves.remove(best_move)
                root_moves.insert(0, best_move)

        except _SearchTimeout:
            break

    # Final legality check
    i, j, k = best_move
    if 0 <= i < 3 and 0 <= j < 3 and 0 <= k < 3 and board[i][j][k] == 0:
        return best_move

    # Fallback: first empty
    return moves[0]
