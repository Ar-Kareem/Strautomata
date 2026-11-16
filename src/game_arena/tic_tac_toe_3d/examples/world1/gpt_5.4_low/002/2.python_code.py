
from functools import lru_cache

# 3x3x3 Tic Tac Toe policy
# board[i][j][k] in {0, 1, -1}
# returns (i, j, k)

# ---------- Precompute board geometry ----------

def _idx(i, j, k):
    return i * 9 + j * 3 + k

def _coord(idx):
    return (idx // 9, (idx % 9) // 3, idx % 3)

def _generate_lines():
    lines = []

    # Axis-aligned lines
    for j in range(3):
        for k in range(3):
            lines.append(tuple(_idx(i, j, k) for i in range(3)))  # along i
    for i in range(3):
        for k in range(3):
            lines.append(tuple(_idx(i, j, k) for j in range(3)))  # along j
    for i in range(3):
        for j in range(3):
            lines.append(tuple(_idx(i, j, k) for k in range(3)))  # along k

    # Diagonals in planes with i fixed
    for i in range(3):
        lines.append(tuple(_idx(i, d, d) for d in range(3)))
        lines.append(tuple(_idx(i, d, 2 - d) for d in range(3)))

    # Diagonals in planes with j fixed
    for j in range(3):
        lines.append(tuple(_idx(d, j, d) for d in range(3)))
        lines.append(tuple(_idx(d, j, 2 - d) for d in range(3)))

    # Diagonals in planes with k fixed
    for k in range(3):
        lines.append(tuple(_idx(d, d, k) for d in range(3)))
        lines.append(tuple(_idx(d, 2 - d, k) for d in range(3)))

    # Space diagonals
    lines.append(tuple(_idx(d, d, d) for d in range(3)))
    lines.append(tuple(_idx(d, d, 2 - d) for d in range(3)))
    lines.append(tuple(_idx(d, 2 - d, d) for d in range(3)))
    lines.append(tuple(_idx(d, 2 - d, 2 - d) for d in range(3)))

    return lines

LINES = _generate_lines()
CELL_LINES = [[] for _ in range(27)]
for li, line in enumerate(LINES):
    for c in line:
        CELL_LINES[c].append(li)

CENTER = _idx(1, 1, 1)
CORNERS = {
    _idx(i, j, k)
    for i in (0, 2) for j in (0, 2) for k in (0, 2)
}
FACE_CENTERS = {
    _idx(1, 1, 0), _idx(1, 1, 2),
    _idx(1, 0, 1), _idx(1, 2, 1),
    _idx(0, 1, 1), _idx(2, 1, 1),
}

WIN_SCORE = 10**7
LINE_WEIGHTS = [0, 2, 20, 5000]  # 0/1/2/3 marks in open line


# ---------- Utility functions ----------

def _flatten(board):
    return tuple(board[i][j][k] for i in range(3) for j in range(3) for k in range(3))

def _legal_moves(flat):
    return [i for i, v in enumerate(flat) if v == 0]

def _winner(flat):
    for a, b, c in LINES:
        s = flat[a] + flat[b] + flat[c]
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0

def _make_move(flat, idx, player):
    lst = list(flat)
    lst[idx] = player
    return tuple(lst)

def _immediate_wins(flat, player):
    wins = []
    for idx in _legal_moves(flat):
        for li in CELL_LINES[idx]:
            a, b, c = LINES[li]
            s = flat[a] + flat[b] + flat[c]
            if s == 2 * player:
                wins.append(idx)
                break
    return wins

def _fork_moves(flat, player):
    moves = []
    for idx in _legal_moves(flat):
        threats = 0
        for li in CELL_LINES[idx]:
            line = LINES[li]
            vals = [flat[p] for p in line]
            if -player in vals:
                continue
            # before move: line has exactly one player's mark and two empties, one of them is idx
            if sum(vals) == player and vals.count(0) == 2:
                threats += 1
        if threats >= 2:
            moves.append(idx)
    return moves

def _positional_bonus(idx):
    if idx == CENTER:
        return 30
    if idx in CORNERS:
        return 12
    if idx in FACE_CENTERS:
        return 8
    return 4


# ---------- Evaluation ----------

def _heuristic_abs(flat):
    # Positive means good for player 1, negative good for player -1
    score = 0

    # Line-based evaluation
    for a, b, c in LINES:
        vals = (flat[a], flat[b], flat[c])
        if 1 in vals and -1 in vals:
            continue
        cnt1 = vals.count(1)
        cntm1 = vals.count(-1)
        if cntm1 == 0:
            score += LINE_WEIGHTS[cnt1]
        elif cnt1 == 0:
            score -= LINE_WEIGHTS[cntm1]

    # Positional bonuses
    if flat[CENTER] == 1:
        score += 18
    elif flat[CENTER] == -1:
        score -= 18

    for idx in CORNERS:
        if flat[idx] == 1:
            score += 4
        elif flat[idx] == -1:
            score -= 4

    return score

def _heuristic(flat, player):
    return player * _heuristic_abs(flat)


# ---------- Move ordering ----------

def _move_order_score(flat, idx, player):
    score = _positional_bonus(idx)

    # Prefer moves participating in many open lines and strong continuations
    for li in CELL_LINES[idx]:
        a, b, c = LINES[li]
        vals = [flat[a], flat[b], flat[c]]
        if -player not in vals:
            cnt = vals.count(player)
            score += (1, 6, 100)[cnt] if cnt < 3 else 0
        if player not in vals:
            cnto = vals.count(-player)
            score += (0, 3, 30)[cnto] if cnto < 3 else 0

    return score


# ---------- Search ----------

TT = {}

def _negamax(flat, player, depth, alpha, beta):
    key = (flat, player, depth)
    if key in TT:
        return TT[key]

    w = _winner(flat)
    if w != 0:
        val = (WIN_SCORE + depth) if w == player else -(WIN_SCORE + depth)
        TT[key] = val
        return val

    moves = _legal_moves(flat)
    if not moves:
        TT[key] = 0
        return 0

    if depth == 0:
        val = _heuristic(flat, player)
        TT[key] = val
        return val

    # Tactical shortcut inside search
    wins = _immediate_wins(flat, player)
    if wins:
        val = WIN_SCORE + depth - 1
        TT[key] = val
        return val

    ordered = sorted(moves, key=lambda m: _move_order_score(flat, m, player), reverse=True)

    best = -10**18
    for mv in ordered:
        child = _make_move(flat, mv, player)
        val = -_negamax(child, -player, depth - 1, -beta, -alpha)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    TT[key] = best
    return best


# ---------- Main policy ----------

def policy(board):
    flat = _flatten(board)
    legal = _legal_moves(flat)

    # Guaranteed legal fallback
    if not legal:
        return (0, 0, 0)
    fallback = _coord(legal[0])

    # If board is empty, take center
    if len(legal) == 27 and flat[CENTER] == 0:
        return (1, 1, 1)

    # 1. Immediate win
    my_wins = _immediate_wins(flat, 1)
    if my_wins:
        return _coord(sorted(my_wins, key=lambda m: _move_order_score(flat, m, 1), reverse=True)[0])

    # 2. Immediate block
    opp_wins = _immediate_wins(flat, -1)
    if opp_wins:
        # If multiple threats, choose move that blocks the most and is strongest positionally
        opp_set = set(opp_wins)
        candidates = []
        for mv in legal:
            blocks = 1 if mv in opp_set else 0
            if blocks:
                candidates.append((blocks, _move_order_score(flat, mv, 1), mv))
        if candidates:
            candidates.sort(reverse=True)
            return _coord(candidates[0][2])
        # If somehow no direct blocking cell recognized, still return fallback legal
        return fallback

    # 3. Create fork
    my_forks = _fork_moves(flat, 1)
    if my_forks:
        best = max(my_forks, key=lambda m: _move_order_score(flat, m, 1))
        return _coord(best)

    # 4. Block opponent fork
    opp_forks = _fork_moves(flat, -1)
    if opp_forks:
        # Prefer taking the fork square itself if available; otherwise choose a forcing move by search
        best = max(opp_forks, key=lambda m: _move_order_score(flat, m, 1))
        return _coord(best)

    # 5. Search
    empties = len(legal)
    if empties >= 20:
        depth = 2
    elif empties >= 14:
        depth = 3
    elif empties >= 10:
        depth = 4
    elif empties >= 7:
        depth = 5
    else:
        depth = empties  # solve exactly in very late game

    ordered = sorted(legal, key=lambda m: _move_order_score(flat, m, 1), reverse=True)

    best_move = ordered[0]
    best_val = -10**18
    alpha = -10**18
    beta = 10**18

    for mv in ordered:
        child = _make_move(flat, mv, 1)
        val = -_negamax(child, -1, depth - 1, -beta, -alpha)
        if val > best_val:
            best_val = val
            best_move = mv
        if val > alpha:
            alpha = val

    # Final legality guard
    i, j, k = _coord(best_move)
    if 0 <= i < 3 and 0 <= j < 3 and 0 <= k < 3 and board[i][j][k] == 0:
        return (i, j, k)
    return fallback
