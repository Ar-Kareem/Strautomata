
import time
import math
from functools import lru_cache

# Pentago policy: always return a legal move string.
# Board cells: 0 empty, 1 us, 2 opponent internally.

DIRS = ("L", "R")
QUADS = (0, 1, 2, 3)
TIME_LIMIT = 0.92

# Precompute all 5-cell winning windows in a 6x6 board.
WIN_LINES = []
for r in range(6):
    for c in range(2):
        WIN_LINES.append(tuple((r, c + k) for k in range(5)))
for c in range(6):
    for r in range(2):
        WIN_LINES.append(tuple((r + k, c) for k in range(5)))
for r in range(2):
    for c in range(2):
        WIN_LINES.append(tuple((r + k, c + k) for k in range(5)))
for r in range(2):
    for c in range(4, 6):
        WIN_LINES.append(tuple((r + k, c - k) for k in range(5)))

# Quadrant coordinates.
QORIGIN = {
    0: (0, 0),
    1: (0, 3),
    2: (3, 0),
    3: (3, 3),
}

# Preference for placements: center-ish positions usually matter more.
POS_WEIGHT = [
    [2, 3, 3, 3, 3, 2],
    [3, 5, 5, 5, 5, 3],
    [3, 5, 6, 6, 5, 3],
    [3, 5, 6, 6, 5, 3],
    [3, 5, 5, 5, 5, 3],
    [2, 3, 3, 3, 3, 2],
]


class Timeout(Exception):
    pass


def _tuple_board(you, opponent):
    b = []
    for r in range(6):
        row = []
        for c in range(6):
            if int(you[r][c]):
                row.append(1)
            elif int(opponent[r][c]):
                row.append(2)
            else:
                row.append(0)
        b.append(tuple(row))
    return tuple(b)


def _set_cell(board, r, c, v):
    rows = [list(x) for x in board]
    rows[r][c] = v
    return tuple(tuple(x) for x in rows)


def _rotate(board, q, d):
    sr, sc = QORIGIN[q]
    rows = [list(x) for x in board]
    sub = [[board[sr + i][sc + j] for j in range(3)] for i in range(3)]

    if d == "R":
        rot = [[sub[2 - j][i] for j in range(3)] for i in range(3)]
    else:
        rot = [[sub[j][2 - i] for j in range(3)] for i in range(3)]

    for i in range(3):
        for j in range(3):
            rows[sr + i][sc + j] = rot[i][j]
    return tuple(tuple(x) for x in rows)


def _apply(board, move, player):
    r, c, q, d = move
    b = _set_cell(board, r, c, player)
    return _rotate(b, q, d)


def _has_win(board, player):
    for line in WIN_LINES:
        ok = True
        for r, c in line:
            if board[r][c] != player:
                ok = False
                break
        if ok:
            return True
    return False


def _full(board):
    for r in range(6):
        for c in range(6):
            if board[r][c] == 0:
                return False
    return True


def _terminal_score(board, root_player):
    p = root_player
    o = 3 - p
    pw = _has_win(board, p)
    ow = _has_win(board, o)
    if pw and ow:
        return 0
    if pw:
        return 1000000
    if ow:
        return -1000000
    if _full(board):
        return 0
    return None


def _line_score(mine, theirs, empties):
    if mine and theirs:
        return 0
    if mine == 5:
        return 100000
    if theirs == 5:
        return -100000
    if mine == 4 and empties == 1:
        return 6500
    if theirs == 4 and empties == 1:
        return -7600
    if mine == 3 and empties == 2:
        return 620
    if theirs == 3 and empties == 2:
        return -720
    if mine == 2 and empties == 3:
        return 75
    if theirs == 2 and empties == 3:
        return -85
    if mine == 1 and empties == 4:
        return 8
    if theirs == 1 and empties == 4:
        return -8
    return 0


def _evaluate(board, player):
    opp = 3 - player
    score = 0

    # Window potential.
    for line in WIN_LINES:
        mine = theirs = empty = 0
        for r, c in line:
            v = board[r][c]
            if v == player:
                mine += 1
            elif v == opp:
                theirs += 1
            else:
                empty += 1
        score += _line_score(mine, theirs, empty)

    # Positional weight.
    for r in range(6):
        for c in range(6):
            if board[r][c] == player:
                score += POS_WEIGHT[r][c]
            elif board[r][c] == opp:
                score -= POS_WEIGHT[r][c]

    return score


def _legal_moves(board):
    moves = []
    empties = []
    for r in range(6):
        for c in range(6):
            if board[r][c] == 0:
                empties.append((r, c))

    # Sort placements by positional value to improve alpha-beta move ordering.
    empties.sort(key=lambda rc: POS_WEIGHT[rc[0]][rc[1]], reverse=True)

    for r, c in empties:
        for q in QUADS:
            for d in DIRS:
                moves.append((r, c, q, d))
    return moves


def _move_order_key(board, move, player):
    r, c, q, d = move
    nb = _apply(board, move, player)
    if _has_win(nb, player):
        return 10**9
    opp = 3 - player
    if _has_win(nb, opp):
        return -10**8
    # Quick local heuristic.
    return _evaluate(nb, player) + POS_WEIGHT[r][c] * 5


def _opponent_has_immediate_win(board, opponent_player):
    for m in _legal_moves(board):
        nb = _apply(board, m, opponent_player)
        ow = _has_win(nb, opponent_player)
        mw = _has_win(nb, 3 - opponent_player)
        if ow and not mw:
            return True
    return False


def policy(you, opponent) -> str:
    start = time.time()

    try:
        board = _tuple_board(you, opponent)

        legal = _legal_moves(board)
        if not legal:
            return "1,1,0,L"

        # Deterministic emergency fallback.
        fallback = legal[0]
        fallback_s = f"{fallback[0]+1},{fallback[1]+1},{fallback[2]},{fallback[3]}"

        # 1. Immediate win.
        best_draw_win = None
        for m in legal:
            nb = _apply(board, m, 1)
            yw = _has_win(nb, 1)
            ow = _has_win(nb, 2)
            if yw and not ow:
                return f"{m[0]+1},{m[1]+1},{m[2]},{m[3]}"
            if yw and ow and best_draw_win is None:
                best_draw_win = m

        # 2. Prefer moves that do not allow opponent immediate win.
        safe_moves = []
        for m in sorted(legal, key=lambda x: _move_order_key(board, x, 1), reverse=True):
            if time.time() - start > TIME_LIMIT * 0.35:
                break
            nb = _apply(board, m, 1)
            term = _terminal_score(nb, 1)
            if term == 0 and _has_win(nb, 1) and _has_win(nb, 2):
                safe_moves.append(m)
                continue
            if not _opponent_has_immediate_win(nb, 2):
                safe_moves.append(m)

        search_moves = safe_moves if safe_moves else legal
        if best_draw_win is not None and not safe_moves:
            return f"{best_draw_win[0]+1},{best_draw_win[1]+1},{best_draw_win[2]},{best_draw_win[3]}"

        search_moves = sorted(search_moves, key=lambda x: _move_order_key(board, x, 1), reverse=True)

        # Limit root branching slightly for speed, but keep enough tactical variety.
        empties_count = sum(1 for r in range(6) for c in range(6) if board[r][c] == 0)
        if empties_count > 24:
            root_limit = 36
            depth = 2
        elif empties_count > 14:
            root_limit = 64
            depth = 2
        else:
            root_limit = 96
            depth = 3

        candidates = search_moves[:min(root_limit, len(search_moves))]
        best_move = candidates[0]
        best_score = -10**18

        cache = {}

        def negamax(b, depth_left, player, alpha, beta):
            if time.time() - start > TIME_LIMIT:
                raise Timeout()

            # Evaluate terminal from root perspective, then convert to side-to-move perspective.
            t = _terminal_score(b, 1)
            if t is not None:
                return t if player == 1 else -t
            if depth_left == 0:
                val = _evaluate(b, 1)
                return val if player == 1 else -val

            key = (b, depth_left, player)
            if key in cache:
                return cache[key]

            moves = _legal_moves(b)
            moves.sort(key=lambda x: _move_order_key(b, x, player), reverse=True)
            if depth_left >= 2:
                moves = moves[:48]
            else:
                moves = moves[:72]

            best = -10**18
            opp = 3 - player
            for mv in moves:
                nb = _apply(b, mv, player)
                val = -negamax(nb, depth_left - 1, opp, -beta, -alpha)
                if val > best:
                    best = val
                if val > alpha:
                    alpha = val
                if alpha >= beta:
                    break
            cache[key] = best
            return best

        # Iterative deepening: depth 2 then maybe depth 3/4 if late game and time permits.
        depths = [1, depth]
        if empties_count <= 10:
            depths.append(4)

        for dpth in depths:
            if time.time() - start > TIME_LIMIT:
                break
            current_best_move = best_move
            current_best_score = -10**18
            for m in candidates:
                if time.time() - start > TIME_LIMIT:
                    raise Timeout()
                nb = _apply(board, m, 1)
                val = -negamax(nb, dpth - 1, 2, -10**18, 10**18)

                # Small tie-breaker for good placement.
                val += POS_WEIGHT[m[0]][m[1]]
                if val > current_best_score:
                    current_best_score = val
                    current_best_move = m

            best_move = current_best_move
            best_score = current_best_score

            # If a forced-looking win is found, stop.
            if best_score > 500000:
                break

        return f"{best_move[0]+1},{best_move[1]+1},{best_move[2]},{best_move[3]}"

    except Exception:
        # Absolute safety fallback: scan inputs directly and return first legal placement.
        try:
            for r in range(6):
                for c in range(6):
                    if int(you[r][c]) == 0 and int(opponent[r][c]) == 0:
                        return f"{r+1},{c+1},0,L"
        except Exception:
            pass
        return "1,1,0,L"
