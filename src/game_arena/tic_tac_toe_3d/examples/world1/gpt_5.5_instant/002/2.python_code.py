
# 3x3x3 Tic Tac Toe policy
# Player:  1 (us)
# Opponent: -1

from functools import lru_cache
import math

N = 3
CELLS = [(i, j, k) for i in range(N) for j in range(N) for k in range(N)]
IDX = {c: n for n, c in enumerate(CELLS)}

def _generate_lines():
    """Generate all length-3 straight winning lines in 3x3x3."""
    dirs = []
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            for dk in (-1, 0, 1):
                if (di, dj, dk) == (0, 0, 0):
                    continue
                # keep one representative of each undirected direction
                if (di, dj, dk) > (0, 0, 0):
                    dirs.append((di, dj, dk))

    lines = set()
    for i, j, k in CELLS:
        for di, dj, dk in dirs:
            cells = []
            ok = True
            for t in range(3):
                x, y, z = i + di * t, j + dj * t, k + dk * t
                if not (0 <= x < 3 and 0 <= y < 3 and 0 <= z < 3):
                    ok = False
                    break
                cells.append((x, y, z))
            if ok:
                lines.add(tuple(sorted(IDX[c] for c in cells)))
    return sorted(lines)

LINES = _generate_lines()

CELL_LINES = [[] for _ in range(27)]
for li, line in enumerate(LINES):
    for idx in line:
        CELL_LINES[idx].append(li)

CENTER = IDX[(1, 1, 1)]

# Static positional preference: center, corners, line participation, then edges/faces.
STATIC_SCORE = [0] * 27
for idx, (i, j, k) in enumerate(CELLS):
    score = 10 * len(CELL_LINES[idx])
    if idx == CENTER:
        score += 80
    coords = (i, j, k)
    extremes = sum(1 for x in coords if x in (0, 2))
    if extremes == 3:
        score += 35     # corners
    elif extremes == 2:
        score += 18
    elif extremes == 1:
        score += 8
    STATIC_SCORE[idx] = score

ORDER = sorted(range(27), key=lambda x: STATIC_SCORE[x], reverse=True)

def _flat(board):
    return tuple(board[i][j][k] for i in range(3) for j in range(3) for k in range(3))

def _winner_from_flat(b):
    for line in LINES:
        s = b[line[0]] + b[line[1]] + b[line[2]]
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0

def _winning_moves(b, player):
    moves = []
    target = 2 * player
    for line in LINES:
        vals = b[line[0]], b[line[1]], b[line[2]]
        if vals[0] + vals[1] + vals[2] == target:
            for idx in line:
                if b[idx] == 0:
                    moves.append(idx)
                    break
    return moves

def _creates_forks(b, idx, player):
    """Number of immediate winning threats after playing idx."""
    bb = list(b)
    bb[idx] = player
    return len(set(_winning_moves(tuple(bb), player)))

def _heuristic(b):
    """Positive is good for us."""
    winner = _winner_from_flat(b)
    if winner:
        return winner * 1000000

    score = 0

    # Positional material
    for idx, v in enumerate(b):
        if v == 1:
            score += STATIC_SCORE[idx]
        elif v == -1:
            score -= STATIC_SCORE[idx]

    # Line potential
    line_score = {
        0: 0,
        1: 25,
        2: 420,
        3: 1000000,
    }
    for line in LINES:
        vals = [b[x] for x in line]
        us = vals.count(1)
        them = vals.count(-1)
        if us and them:
            continue
        if us:
            score += line_score[us]
        elif them:
            score -= int(line_score[them] * 1.08)

    # Fork pressure
    our_forks = 0
    opp_forks = 0
    for idx, v in enumerate(b):
        if v == 0:
            f1 = _creates_forks(b, idx, 1)
            f2 = _creates_forks(b, idx, -1)
            if f1 >= 2:
                our_forks += f1
            if f2 >= 2:
                opp_forks += f2
    score += 260 * our_forks
    score -= 300 * opp_forks

    return score

@lru_cache(maxsize=200000)
def _negamax(b, player, depth, alpha, beta):
    """
    Returns value from current player's perspective.
    b is tuple length 27. player is 1 or -1.
    """
    w = _winner_from_flat(b)
    if w != 0:
        # If winner is current player, good; otherwise bad.
        return 1000000 if w == player else -1000000

    empties = [idx for idx in ORDER if b[idx] == 0]
    if not empties:
        return 0
    if depth <= 0:
        return _heuristic(b) * player

    # Tactical: if current player can win immediately, do it.
    wins = _winning_moves(b, player)
    if wins:
        return 999000 + depth

    # Move ordering: wins, blocks, forks, static preference.
    opp_wins = set(_winning_moves(b, -player))

    def move_key(idx):
        bb = list(b)
        bb[idx] = player
        own_forks = len(set(_winning_moves(tuple(bb), player)))
        block_bonus = 10000 if idx in opp_wins else 0
        return block_bonus + 600 * own_forks + STATIC_SCORE[idx]

    moves = sorted(empties, key=move_key, reverse=True)

    best = -10**9
    for idx in moves:
        bb = list(b)
        bb[idx] = player
        nb = tuple(bb)
        val = -_negamax(nb, -player, depth - 1, -beta, -alpha)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best

def _choose_by_score(b, candidates, player=1):
    best_idx = candidates[0]
    best_val = -10**18
    empties = sum(1 for x in b if x == 0)

    # Search depth chosen for speed. Late game can search deeper.
    if empties >= 20:
        depth = 3
    elif empties >= 13:
        depth = 4
    elif empties >= 8:
        depth = 5
    else:
        depth = 8

    for idx in candidates:
        bb = list(b)
        bb[idx] = player
        nb = tuple(bb)

        if _winner_from_flat(nb) == player:
            val = 10**9
        else:
            val = -_negamax(nb, -player, depth - 1, -10**9, 10**9)

        # Small deterministic tie-breaker for strong squares.
        val += STATIC_SCORE[idx] * 0.001

        if val > best_val:
            best_val = val
            best_idx = idx

    return best_idx

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    b = _flat(board)
    empties = [idx for idx in ORDER if b[idx] == 0]

    # Absolute safety fallback.
    if not empties:
        return (0, 0, 0)

    # First move: center is strongest in 3D tic-tac-toe.
    if len(empties) == 27:
        return (1, 1, 1)

    # If center is free, take it early.
    if b[CENTER] == 0 and len(empties) >= 24:
        return (1, 1, 1)

    # 1. Immediate win.
    wins = _winning_moves(b, 1)
    if wins:
        idx = max(wins, key=lambda x: STATIC_SCORE[x])
        return CELLS[idx]

    # 2. Immediate block.
    blocks = _winning_moves(b, -1)
    if blocks:
        # If multiple blocks, choose the one that also maximizes our prospects.
        idx = _choose_by_score(b, list(set(blocks)), 1)
        return CELLS[idx]

    # 3. Create a fork if possible, especially one with multiple threats.
    fork_moves = []
    for idx in empties:
        f = _creates_forks(b, idx, 1)
        if f >= 2:
            fork_moves.append((f, idx))
    if fork_moves:
        maxf = max(f for f, _ in fork_moves)
        candidates = [idx for f, idx in fork_moves if f == maxf]
        idx = _choose_by_score(b, candidates, 1)
        return CELLS[idx]

    # 4. Prevent opponent forks when urgent.
    opp_fork_moves = []
    for idx in empties:
        f = _creates_forks(b, idx, -1)
        if f >= 2:
            opp_fork_moves.append((f, idx))
    if opp_fork_moves:
        maxf = max(f for f, _ in opp_fork_moves)
        candidates = [idx for f, idx in opp_fork_moves if f == maxf]
        # Sometimes making our own strong move is better; search among all good candidates.
        candidate_set = set(candidates)
        candidate_set.update(empties[:8])
        idx = _choose_by_score(b, list(candidate_set), 1)
        return CELLS[idx]

    # 5. Search among ordered promising moves, not necessarily all early-game moves.
    if len(empties) > 18:
        candidates = empties[:14]
    else:
        candidates = empties

    idx = _choose_by_score(b, candidates, 1)

    # Final legal fallback in case of any unexpected issue.
    if b[idx] != 0:
        idx = empties[0]
    return CELLS[idx]
