
import time
from functools import lru_cache

# ---------- Precomputed geometry ----------

CELLS = [(i, j, k) for i in range(3) for j in range(3) for k in range(3)]

# All 13 unique directions in a 3x3x3 cube
DIRS = []
for di in (-1, 0, 1):
    for dj in (-1, 0, 1):
        for dk in (-1, 0, 1):
            if di == dj == dk == 0:
                continue
            d = (di, dj, dk)
            # Keep only one orientation of each line
            for x in d:
                if x != 0:
                    if x > 0:
                        DIRS.append(d)
                    break

LINES = []
for i, j, k in CELLS:
    for di, dj, dk in DIRS:
        line = []
        ok = True
        for t in range(3):
            x, y, z = i + di * t, j + dj * t, k + dk * t
            if not (0 <= x < 3 and 0 <= y < 3 and 0 <= z < 3):
                ok = False
                break
            line.append((x, y, z))
        if not ok:
            continue

        # Ensure this is the first cell of the line
        pi, pj, pk = i - di, j - dj, k - dk
        if 0 <= pi < 3 and 0 <= pj < 3 and 0 <= pk < 3:
            continue

        LINES.append(tuple(line))

# Remove possible duplicates defensively
_seen = set()
_unique = []
for line in LINES:
    key = tuple(sorted(line))
    if key not in _seen:
        _seen.add(key)
        _unique.append(line)
LINES = _unique

CELL_LINE_COUNT = {c: 0 for c in CELLS}
for line in LINES:
    for c in line:
        CELL_LINE_COUNT[c] += 1

# Prefer cells involved in many winning lines.
POSITION_SCORE = {
    c: CELL_LINE_COUNT[c] for c in CELLS
}


# ---------- Helpers ----------

def _flatten(board):
    return tuple(board[i][j][k] for i in range(3) for j in range(3) for k in range(3))


def _get(flat, cell):
    i, j, k = cell
    return flat[i * 9 + j * 3 + k]


def _set(flat, cell, value):
    i, j, k = cell
    idx = i * 9 + j * 3 + k
    lst = list(flat)
    lst[idx] = value
    return tuple(lst)


def _legal_moves(flat):
    return [c for c in CELLS if _get(flat, c) == 0]


def _winner(flat):
    for line in LINES:
        s = _get(flat, line[0]) + _get(flat, line[1]) + _get(flat, line[2])
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0


def _winning_moves(flat, player):
    moves = []
    for c in CELLS:
        if _get(flat, c) != 0:
            continue
        nf = _set(flat, c, player)
        if _winner(nf) == player:
            moves.append(c)
    return moves


def _heuristic(flat):
    """
    Positive is good for us, negative is good for opponent.
    """
    win = _winner(flat)
    if win == 1:
        return 1_000_000
    if win == -1:
        return -1_000_000

    score = 0

    # Line potential.
    # Two-in-a-row with one empty is extremely important.
    for line in LINES:
        vals = [_get(flat, c) for c in line]
        ours = vals.count(1)
        opps = vals.count(-1)

        if ours and opps:
            continue

        if ours:
            if ours == 1:
                score += 8
            elif ours == 2:
                score += 260
        elif opps:
            if opps == 1:
                score -= 9
            elif opps == 2:
                score -= 310

    # Positional value.
    for c in CELLS:
        v = _get(flat, c)
        if v == 1:
            score += 3 * POSITION_SCORE[c]
        elif v == -1:
            score -= 3 * POSITION_SCORE[c]

    # Fork pressure: count open two-threats.
    our_twos = 0
    opp_twos = 0
    for line in LINES:
        vals = [_get(flat, c) for c in line]
        if vals.count(1) == 2 and vals.count(0) == 1:
            our_twos += 1
        if vals.count(-1) == 2 and vals.count(0) == 1:
            opp_twos += 1

    if our_twos >= 2:
        score += 350 * our_twos
    if opp_twos >= 2:
        score -= 420 * opp_twos

    return score


def _ordered_moves(flat, player):
    moves = _legal_moves(flat)

    def move_score(c):
        nf = _set(flat, c, player)

        # Winning move first.
        if _winner(nf) == player:
            return 1_000_000

        # Blocking opponent immediate win.
        block = 0
        for line in LINES:
            if c not in line:
                continue
            vals = [_get(flat, x) for x in line]
            if vals.count(-player) == 2 and vals.count(0) == 1:
                block += 50_000

        # General positional and heuristic impact.
        base = POSITION_SCORE[c] * 20
        if c == (1, 1, 1):
            base += 200

        if player == 1:
            h = _heuristic(nf)
        else:
            h = -_heuristic(nf)

        return block + base + h

    return sorted(moves, key=move_score, reverse=True)


# ---------- Main policy ----------

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    start = time.time()
    time_limit = 0.88

    flat = _flatten(board)
    legal = _legal_moves(flat)

    # Absolute safety: if somehow no legal moves, return a valid tuple.
    # In normal play this should never happen.
    if not legal:
        return (0, 0, 0)

    # If center is open early, it is usually strongest.
    if len(legal) == 27:
        return (1, 1, 1)

    # 1. Take immediate win.
    wins = _winning_moves(flat, 1)
    if wins:
        return max(wins, key=lambda c: POSITION_SCORE[c])

    # 2. Block immediate opponent win.
    blocks = _winning_moves(flat, -1)
    if blocks:
        return max(blocks, key=lambda c: POSITION_SCORE[c])

    empties = len(legal)

    # Adaptive depth.
    if empties <= 8:
        max_depth = empties
    elif empties <= 12:
        max_depth = 7
    elif empties <= 17:
        max_depth = 5
    else:
        max_depth = 4

    cache = {}

    class Timeout(Exception):
        pass

    def minimax(f, player, depth, alpha, beta):
        if time.time() - start > time_limit:
            raise Timeout()

        key = (f, player, depth, alpha, beta)
        # Alpha and beta in key reduce hits, so use a smaller key.
        key = (f, player, depth)
        if key in cache:
            return cache[key]

        w = _winner(f)
        if w == 1:
            return 1_000_000 + depth
        if w == -1:
            return -1_000_000 - depth

        moves = _legal_moves(f)
        if depth == 0 or not moves:
            val = _heuristic(f)
            cache[key] = val
            return val

        ordered = _ordered_moves(f, player)

        if player == 1:
            best = -10_000_000
            for m in ordered:
                nf = _set(f, m, 1)
                val = minimax(nf, -1, depth - 1, alpha, beta)
                if val > best:
                    best = val
                alpha = max(alpha, best)
                if beta <= alpha:
                    break
        else:
            best = 10_000_000
            for m in ordered:
                nf = _set(f, m, -1)
                val = minimax(nf, 1, depth - 1, alpha, beta)
                if val < best:
                    best = val
                beta = min(beta, best)
                if beta <= alpha:
                    break

        cache[key] = best
        return best

    # Initial fallback: best heuristic move.
    ordered_root = _ordered_moves(flat, 1)
    best_move = ordered_root[0]
    best_score = -10_000_000

    # Iterative deepening improves anytime behavior.
    try:
        for depth in range(1, max_depth + 1):
            local_best = best_move
            local_score = -10_000_000

            for m in ordered_root:
                if time.time() - start > time_limit:
                    raise Timeout()

                nf = _set(flat, m, 1)

                # Avoid moves that allow an immediate opponent win unless forced.
                opp_reply_wins = _winning_moves(nf, -1)
                penalty = 0
                if opp_reply_wins:
                    penalty = 80_000 * len(opp_reply_wins)

                val = minimax(nf, -1, depth - 1, -10_000_000, 10_000_000) - penalty

                if val > local_score:
                    local_score = val
                    local_best = m

            best_move = local_best
            best_score = local_score

    except Timeout:
        pass

    # Final legality guard.
    if best_move in legal:
        return best_move

    # Guaranteed legal fallback.
    return legal[0]
