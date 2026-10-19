
from functools import lru_cache
import time
import math

N = 4

# All winning / tactical lines: 4 rows, 4 cols, 2 diagonals.
LINES = []
for r in range(N):
    LINES.append(tuple((r, c) for c in range(N)))
for c in range(N):
    LINES.append(tuple((r, c) for r in range(N)))
LINES.append(tuple((i, i) for i in range(N)))
LINES.append(tuple((i, N - 1 - i) for i in range(N)))

# Extra pattern features: all 2x2 squares, useful for building forks/control.
SQUARES = []
for r in range(N - 1):
    for c in range(N - 1):
        SQUARES.append(((r, c), (r + 1, c), (r, c + 1), (r + 1, c + 1)))

# Prefer central influence first.
POSITION_WEIGHT = (
    (3, 4, 4, 3),
    (4, 7, 7, 4),
    (4, 7, 7, 4),
    (3, 4, 4, 3),
)

PREFERRED_MOVES = (
    (1, 1), (1, 2), (2, 1), (2, 2),
    (0, 0), (0, 3), (3, 0), (3, 3),
    (0, 1), (0, 2), (1, 0), (1, 3),
    (2, 0), (2, 3), (3, 1), (3, 2)
)


def _flatten(board):
    return tuple(board[r][c] for r in range(N) for c in range(N))


def _idx(r, c):
    return r * N + c


LINE_IDXS = [tuple(_idx(r, c) for r, c in line) for line in LINES]
SQUARE_IDXS = [tuple(_idx(r, c) for r, c in sq) for sq in SQUARES]


def _winner(state):
    for line in LINE_IDXS:
        s = state[line[0]] + state[line[1]] + state[line[2]] + state[line[3]]
        if s == 4:
            return 1
        if s == -4:
            return -1
    return 0


def _legal_moves_state(state):
    return [i for i, v in enumerate(state) if v == 0]


def _terminal_score(state, ply_from_root):
    w = _winner(state)
    if w == 1:
        return 1000000 - ply_from_root
    if w == -1:
        return -1000000 + ply_from_root
    if all(v != 0 for v in state):
        return 0
    return None


def _evaluate(state):
    # Static evaluation from our perspective.
    score = 0

    # Positional control.
    for i, v in enumerate(state):
        if v:
            r, c = divmod(i, N)
            score += v * POSITION_WEIGHT[r][c] * 4

    # Line potential. Opponent threats are weighted slightly more to ensure blocks.
    for line in LINE_IDXS:
        vals = [state[i] for i in line]
        own = vals.count(1)
        opp = vals.count(-1)
        empty = vals.count(0)

        if own and opp:
            continue

        if own:
            if own == 3 and empty == 1:
                score += 9000
            elif own == 2 and empty == 2:
                score += 750
            elif own == 1 and empty == 3:
                score += 70
        elif opp:
            if opp == 3 and empty == 1:
                score -= 11000
            elif opp == 2 and empty == 2:
                score -= 900
            elif opp == 1 and empty == 3:
                score -= 80
        else:
            score += 5

    # 2x2 local control / fork potential.
    for sq in SQUARE_IDXS:
        vals = [state[i] for i in sq]
        own = vals.count(1)
        opp = vals.count(-1)
        if own and opp:
            continue
        if own:
            score += (own * own) * 45
        elif opp:
            score -= (opp * opp) * 50

    # Count immediate winning threats for each side; double threats are huge.
    own_threats = 0
    opp_threats = 0
    for line in LINE_IDXS:
        s = sum(state[i] for i in line)
        zeros = sum(1 for i in line if state[i] == 0)
        if zeros == 1:
            if s == 3:
                own_threats += 1
            elif s == -3:
                opp_threats += 1
    if own_threats >= 2:
        score += 50000
    elif own_threats == 1:
        score += 6000
    if opp_threats >= 2:
        score -= 65000
    elif opp_threats == 1:
        score -= 8000

    return score


def _apply(state, move, player):
    lst = list(state)
    lst[move] = player
    return tuple(lst)


def _find_immediate_win(state, player):
    for m in _legal_moves_state(state):
        ns = _apply(state, m, player)
        if _winner(ns) == player:
            return m
    return None


def _move_order(state, moves, player):
    ordered = []
    for m in moves:
        ns = _apply(state, m, player)

        # Winning moves first, blocking and threats next.
        win = 1 if _winner(ns) == player else 0

        r, c = divmod(m, N)
        score = POSITION_WEIGHT[r][c] * 10 + (20 if (r, c) in PREFERRED_MOVES[:4] else 0)

        # Prefer moves contributing to open lines.
        for line in LINE_IDXS:
            if m in line:
                vals = [state[i] for i in line]
                own = vals.count(player)
                opp = vals.count(-player)
                if opp == 0:
                    score += 30 * own + 5
                if own == 0:
                    score += 20 * opp  # may block

        # Does this create immediate threats?
        threats = 0
        for line in LINE_IDXS:
            vals = [ns[i] for i in line]
            if vals.count(player) == 3 and vals.count(0) == 1:
                threats += 1
        score += threats * 500

        ordered.append((win, score, m))

    ordered.sort(reverse=True)
    return [m for _, __, m in ordered]


def policy(board: list[list[int]]) -> tuple[int, int]:
    start = time.time()
    limit = 0.92

    state = _flatten(board)
    legal = _legal_moves_state(state)

    # Absolute legal fallback.
    if not legal:
        return (0, 0)

    # If board encoding ever differs, still choose first actually empty from input.
    fallback = legal[0]
    for pr, pc in PREFERRED_MOVES:
        k = _idx(pr, pc)
        if k in legal:
            fallback = k
            break

    # First move: take a center.
    if len(legal) == 16:
        return (1, 1)

    # Immediate win.
    m = _find_immediate_win(state, 1)
    if m is not None:
        return divmod(m, N)

    # Immediate block.
    m = _find_immediate_win(state, -1)
    if m is not None:
        return divmod(m, N)

    # Depth choice: full search near the end, shallower early.
    empties = len(legal)
    if empties <= 8:
        max_depth = empties
    elif empties <= 11:
        max_depth = 8
    else:
        max_depth = 6

    cache = {}

    def negamax(st, depth, alpha, beta, player, ply):
        # Return score from our perspective, not side-to-move perspective.
        term = _terminal_score(st, ply)
        if term is not None:
            return term

        if depth == 0 or time.time() - start > limit:
            return _evaluate(st)

        key = (st, depth, player)
        if key in cache:
            return cache[key]

        moves = _legal_moves_state(st)
        moves = _move_order(st, moves, player)

        if player == 1:
            best = -math.inf
            for mv in moves:
                val = negamax(_apply(st, mv, 1), depth - 1, alpha, beta, -1, ply + 1)
                if val > best:
                    best = val
                alpha = max(alpha, best)
                if alpha >= beta:
                    break
        else:
            best = math.inf
            for mv in moves:
                val = negamax(_apply(st, mv, -1), depth - 1, alpha, beta, 1, ply + 1)
                if val < best:
                    best = val
                beta = min(beta, best)
                if alpha >= beta:
                    break

        cache[key] = best
        return best

    best_move = fallback
    best_score = -math.inf

    # Iterative deepening for robustness under time limit.
    ordered_root = _move_order(state, legal, 1)
    for depth in range(1, max_depth + 1):
        if time.time() - start > limit:
            break

        current_best = best_move
        current_score = -math.inf
        alpha = -math.inf
        beta = math.inf

        for mv in ordered_root:
            if time.time() - start > limit:
                break
            ns = _apply(state, mv, 1)
            val = negamax(ns, depth - 1, alpha, beta, -1, 1)
            if val > current_score:
                current_score = val
                current_best = mv
            alpha = max(alpha, current_score)

        if time.time() - start <= limit:
            best_move = current_best
            best_score = current_score

        # If a forced win is found, no need to continue.
        if best_score > 900000:
            break

    # Final safety: ensure returned move is legal.
    if best_move not in legal:
        best_move = fallback

    return divmod(best_move, N)
