
from typing import List, Tuple

# 3x3x3 Tic Tac Toe policy
# 0 = empty, 1 = us, -1 = opponent

# ---------- Precomputation ----------

def _idx(i: int, j: int, k: int) -> int:
    return i * 9 + j * 3 + k

IDX_TO_COORD = [(i, j, k) for i in range(3) for j in range(3) for k in range(3)]

def _generate_lines():
    lines = []

    # Axis-aligned lines
    for i in range(3):
        for j in range(3):
            lines.append([_idx(i, j, k) for k in range(3)])  # vary k
    for i in range(3):
        for k in range(3):
            lines.append([_idx(i, j, k) for j in range(3)])  # vary j
    for j in range(3):
        for k in range(3):
            lines.append([_idx(i, j, k) for i in range(3)])  # vary i

    # Plane diagonals
    # fixed i, diagonal in (j,k)
    for i in range(3):
        lines.append([_idx(i, 0, 0), _idx(i, 1, 1), _idx(i, 2, 2)])
        lines.append([_idx(i, 0, 2), _idx(i, 1, 1), _idx(i, 2, 0)])

    # fixed j, diagonal in (i,k)
    for j in range(3):
        lines.append([_idx(0, j, 0), _idx(1, j, 1), _idx(2, j, 2)])
        lines.append([_idx(0, j, 2), _idx(1, j, 1), _idx(2, j, 0)])

    # fixed k, diagonal in (i,j)
    for k in range(3):
        lines.append([_idx(0, 0, k), _idx(1, 1, k), _idx(2, 2, k)])
        lines.append([_idx(0, 2, k), _idx(1, 1, k), _idx(2, 0, k)])

    # Space diagonals
    lines.append([_idx(0, 0, 0), _idx(1, 1, 1), _idx(2, 2, 2)])
    lines.append([_idx(0, 0, 2), _idx(1, 1, 1), _idx(2, 2, 0)])
    lines.append([_idx(0, 2, 0), _idx(1, 1, 1), _idx(2, 0, 2)])
    lines.append([_idx(0, 2, 2), _idx(1, 1, 1), _idx(2, 0, 0)])

    return lines

LINES = _generate_lines()

CELL_TO_LINES = [[] for _ in range(27)]
for li, line in enumerate(LINES):
    for c in line:
        CELL_TO_LINES[c].append(li)

# Positional value: number of winning lines through the cell
POS_WEIGHT = [len(CELL_TO_LINES[c]) for c in range(27)]

INF = 10**9

# Heuristic weights for open lines
SELF_LINE_SCORE = [0, 2, 18, 100000]
OPP_LINE_SCORE  = [0, 3, 24, 100000]

# ---------- Helpers ----------

def _flatten(board: List[List[List[int]]]) -> List[int]:
    flat = [0] * 27
    t = 0
    for i in range(3):
        for j in range(3):
            for k in range(3):
                flat[t] = board[i][j][k]
                t += 1
    return flat

def _legal_moves(flat: List[int]) -> List[int]:
    return [i for i, v in enumerate(flat) if v == 0]

def _winner(flat: List[int]) -> int:
    for a, b, c in LINES:
        s = flat[a] + flat[b] + flat[c]
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0

def _is_winning_move(flat: List[int], move: int, player: int) -> bool:
    for li in CELL_TO_LINES[move]:
        line = LINES[li]
        total = 0
        ok = True
        for c in line:
            v = player if c == move else flat[c]
            if v != player:
                ok = False
                break
            total += v
        if ok and total == 3 * player:
            return True
    return False

def _immediate_wins(flat: List[int], player: int) -> List[int]:
    wins = []
    for m in _legal_moves(flat):
        if _is_winning_move(flat, m, player):
            wins.append(m)
    return wins

def _fork_count_after_move(flat: List[int], move: int, player: int) -> int:
    flat[move] = player
    cnt = 0
    for m in _legal_moves(flat):
        if _is_winning_move(flat, m, player):
            cnt += 1
    flat[move] = 0
    return cnt

def _evaluate(flat: List[int]) -> int:
    w = _winner(flat)
    if w == 1:
        return 500000
    if w == -1:
        return -500000

    score = 0

    # Positional score
    for c, v in enumerate(flat):
        if v == 1:
            score += POS_WEIGHT[c] * 3
        elif v == -1:
            score -= POS_WEIGHT[c] * 3

    # Line score
    for a, b, c in LINES:
        vals = (flat[a], flat[b], flat[c])
        p1 = vals.count(1)
        p2 = vals.count(-1)
        if p1 and p2:
            continue
        if p1:
            score += SELF_LINE_SCORE[p1]
        elif p2:
            score -= OPP_LINE_SCORE[p2]

    return score

def _quick_move_score(flat: List[int], move: int, player: int) -> int:
    # Fast ordering heuristic
    score = POS_WEIGHT[move] * 10

    for li in CELL_TO_LINES[move]:
        line = LINES[li]
        mine = 0
        opp = 0
        for c in line:
            v = player if c == move else flat[c]
            if v == player:
                mine += 1
            elif v == -player:
                opp += 1
        if mine and opp:
            continue
        if opp == 0:
            score += (0, 4, 20, 0)[mine]
        elif mine == 0:
            score += (0, 5, 24, 0)[opp]

    # Tactical bonuses
    if _is_winning_move(flat, move, player):
        score += 1000000

    # Prefer creating forks
    forks = _fork_count_after_move(flat, move, player)
    score += forks * 500

    # Prefer moves that do not allow easy counterplay
    flat[move] = player
    opp_wins = len(_immediate_wins(flat, -player))
    flat[move] = 0
    score -= opp_wins * 800

    return score

def _ordered_moves(flat: List[int], player: int, max_moves: int = None) -> List[int]:
    moves = _legal_moves(flat)
    moves.sort(key=lambda m: _quick_move_score(flat, m, player), reverse=True)
    if max_moves is not None and len(moves) > max_moves:
        moves = moves[:max_moves]
    return moves

def _negamax(flat: List[int], player: int, depth: int, alpha: int, beta: int, max_branch: int) -> int:
    w = _winner(flat)
    if w != 0:
        return w * 500000 * player

    empties = flat.count(0)
    if empties == 0:
        return 0
    if depth == 0:
        return _evaluate(flat) * player

    # Tactical shortcut: if current player has an immediate win, it dominates.
    wins = _immediate_wins(flat, player)
    if wins:
        return 450000

    moves = _ordered_moves(flat, player, max_branch)

    best = -INF
    for m in moves:
        flat[m] = player
        val = -_negamax(flat, -player, depth - 1, -beta, -alpha, max_branch)
        flat[m] = 0

        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    return best

# ---------- Main policy ----------

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    flat = _flatten(board)
    legal = _legal_moves(flat)

    # Absolute safety: always return a legal move
    if not legal:
        return (0, 0, 0)

    # 1) Immediate win
    for m in legal:
        if _is_winning_move(flat, m, 1):
            return IDX_TO_COORD[m]

    # 2) Analyze opponent immediate wins now
    opp_now_wins = _immediate_wins(flat, -1)

    # 3) Build candidate list with tactical filtering
    candidates = []
    for m in legal:
        flat[m] = 1
        opp_reply_wins = _immediate_wins(flat, -1)
        my_future_wins = _immediate_wins(flat, 1)
        flat[m] = 0

        candidates.append((
            m,
            len(opp_reply_wins),     # fewer is better
            len(my_future_wins),     # more is better
            _quick_move_score(flat, m, 1)
        ))

    # Prefer moves that eliminate opponent immediate wins if possible
    if opp_now_wins:
        min_opp = min(x[1] for x in candidates)
        reduced = [x for x in candidates if x[1] == min_opp]
    else:
        min_opp = min(x[1] for x in candidates)
        safe = [x for x in candidates if x[1] == 0]
        reduced = safe if safe else [x for x in candidates if x[1] == min_opp]

    # Strong ordering
    reduced.sort(key=lambda x: (x[1], -x[2], -x[3]))
    root_moves = [x[0] for x in reduced]

    # Dynamic search settings
    empties = len(legal)
    if empties >= 20:
        depth = 2
        max_branch = 8
    elif empties >= 14:
        depth = 3
        max_branch = 8
    elif empties >= 9:
        depth = 3
        max_branch = 10
    elif empties >= 6:
        depth = 4
        max_branch = 12
    else:
        depth = 6
        max_branch = 27

    # Search only best few root candidates unless the board is sparse late-game
    root_limit = 10 if empties >= 10 else len(root_moves)
    root_moves = root_moves[:root_limit] if root_moves else legal

    best_move = root_moves[0]
    best_val = -INF

    alpha = -INF
    beta = INF

    for m in root_moves:
        flat[m] = 1

        # If move creates immediate multiple threats and avoids opponent win, that's excellent
        my_wins_next = len(_immediate_wins(flat, 1))
        opp_wins_next = len(_immediate_wins(flat, -1))

        if my_wins_next > 0 and opp_wins_next == 0:
            tactical_bonus = 20000 + my_wins_next * 2000
        else:
            tactical_bonus = -opp_wins_next * 3000 + my_wins_next * 1000

        val = -_negamax(flat, -1, depth - 1, -beta, -alpha, max_branch) + tactical_bonus
        flat[m] = 0

        if val > best_val:
            best_val = val
            best_move = m
        if val > alpha:
            alpha = val

    # Final legality check
    if flat[best_move] != 0:
        for m in legal:
            if flat[m] == 0:
                best_move = m
                break

    return IDX_TO_COORD[best_move]
