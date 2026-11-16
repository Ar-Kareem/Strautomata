
from typing import List, Tuple, Optional

# Precompute all cells
CELLS = [(i, j, k) for i in range(3) for j in range(3) for k in range(3)]

def _generate_lines():
    lines = []

    # Axis-aligned lines
    for j in range(3):
        for k in range(3):
            lines.append([(i, j, k) for i in range(3)])  # vary i
    for i in range(3):
        for k in range(3):
            lines.append([(i, j, k) for j in range(3)])  # vary j
    for i in range(3):
        for j in range(3):
            lines.append([(i, j, k) for k in range(3)])  # vary k

    # Plane diagonals
    # i-j planes for each k
    for k in range(3):
        lines.append([(0, 0, k), (1, 1, k), (2, 2, k)])
        lines.append([(0, 2, k), (1, 1, k), (2, 0, k)])

    # i-k planes for each j
    for j in range(3):
        lines.append([(0, j, 0), (1, j, 1), (2, j, 2)])
        lines.append([(0, j, 2), (1, j, 1), (2, j, 0)])

    # j-k planes for each i
    for i in range(3):
        lines.append([(i, 0, 0), (i, 1, 1), (i, 2, 2)])
        lines.append([(i, 0, 2), (i, 1, 1), (i, 2, 0)])

    # Space diagonals
    lines.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
    lines.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
    lines.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
    lines.append([(0, 2, 2), (1, 1, 1), (2, 0, 0)])

    return lines

LINES = _generate_lines()

# For move ordering/evaluation: how many winning lines each cell belongs to
CELL_TO_LINES = {cell: [] for cell in CELLS}
for idx, line in enumerate(LINES):
    for cell in line:
        CELL_TO_LINES[cell].append(idx)

CELL_IMPORTANCE = {cell: len(CELL_TO_LINES[cell]) for cell in CELLS}

# Preferred static move order: center, corners, then others by line participation
def _cell_class(cell):
    c = sum(1 for x in cell if x == 1)
    # center has 3 ones
    if cell == (1, 1, 1):
        return 0
    # corners have coordinates all in {0,2}
    if all(x != 1 for x in cell):
        return 1
    # face centers have two 1s, edges have one 1; prioritize by line count anyway
    return 2

STATIC_ORDER = sorted(
    CELLS,
    key=lambda c: (_cell_class(c), -CELL_IMPORTANCE[c], c)
)

WIN_SCORE = 10**7
LINE_WEIGHTS = {0: 0, 1: 1, 2: 12, 3: 1000}

def _flatten(board: List[List[List[int]]]) -> List[int]:
    return [board[i][j][k] for i in range(3) for j in range(3) for k in range(3)]

def _idx(cell):
    i, j, k = cell
    return i * 9 + j * 3 + k

def _winner(flat: List[int]) -> int:
    for line in LINES:
        s = flat[_idx(line[0])] + flat[_idx(line[1])] + flat[_idx(line[2])]
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0

def _legal_moves(flat: List[int]):
    for cell in STATIC_ORDER:
        if flat[_idx(cell)] == 0:
            yield cell

def _immediate_winning_moves(flat: List[int], player: int):
    wins = []
    for cell in _legal_moves(flat):
        p = _idx(cell)
        flat[p] = player
        if _winner(flat) == player:
            wins.append(cell)
        flat[p] = 0
    return wins

def _evaluate(flat: List[int]) -> int:
    w = _winner(flat)
    if w == 1:
        return WIN_SCORE
    if w == -1:
        return -WIN_SCORE

    score = 0
    for line in LINES:
        vals = [flat[_idx(c)] for c in line]
        c1 = vals.count(1)
        c2 = vals.count(-1)
        if c1 and c2:
            continue
        if c1:
            score += LINE_WEIGHTS[c1]
        elif c2:
            score -= LINE_WEIGHTS[c2]

    # Small positional bonus
    for cell in CELLS:
        v = flat[_idx(cell)]
        if v != 0:
            score += v * CELL_IMPORTANCE[cell]

    return score

def _ordered_moves(flat: List[int], player: int):
    moves = [cell for cell in STATIC_ORDER if flat[_idx(cell)] == 0]

    scored = []
    for cell in moves:
        p = _idx(cell)

        # Immediate tactical priority
        flat[p] = player
        if _winner(flat) == player:
            flat[p] = 0
            scored.append((10**9, cell))
            continue
        flat[p] = 0

        flat[p] = -player
        opp_wins = _winner(flat) == -player
        flat[p] = 0

        tactical = 10**8 if opp_wins else 0

        # Heuristic one-ply score
        flat[p] = player
        h = _evaluate(flat)
        flat[p] = 0

        scored.append((tactical + h, cell))

    scored.sort(reverse=True)
    return [cell for _, cell in scored]

TT = {}

def _negamax(flat: List[int], player: int, alpha: int, beta: int) -> int:
    key = (tuple(flat), player)
    if key in TT:
        return TT[key]

    w = _winner(flat)
    if w != 0:
        val = WIN_SCORE if w == player else -WIN_SCORE
        TT[key] = val
        return val

    if all(v != 0 for v in flat):
        TT[key] = 0
        return 0

    # Tactical shortcuts
    my_wins = _immediate_winning_moves(flat, player)
    if my_wins:
        TT[key] = WIN_SCORE - 1
        return WIN_SCORE - 1

    opp_wins = _immediate_winning_moves(flat, -player)
    # If opponent has multiple immediate wins, likely losing unless we already had one
    if len(opp_wins) >= 2:
        TT[key] = -WIN_SCORE + 2
        return -WIN_SCORE + 2

    empties = sum(1 for v in flat if v == 0)
    if empties <= 8:
        # Near endgame: full search
        best = -10**9
        for cell in _ordered_moves(flat, player):
            p = _idx(cell)
            flat[p] = player
            val = -_negamax(flat, -player, -beta, -alpha)
            flat[p] = 0
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        TT[key] = best
        return best

    # Midgame/fullgame search still feasible with pruning
    best = -10**9
    for cell in _ordered_moves(flat, player):
        p = _idx(cell)
        flat[p] = player
        val = -_negamax(flat, -player, -beta, -alpha)
        flat[p] = 0
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    # Fallback heuristic if something odd happens
    if best == -10**9:
        best = _evaluate(flat) * player

    TT[key] = best
    return best

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    flat = _flatten(board)

    legal = [cell for cell in STATIC_ORDER if flat[_idx(cell)] == 0]
    if not legal:
        return (0, 0, 0)  # unreachable in legal play, but ensures return type

    # 1. Immediate win
    wins = _immediate_winning_moves(flat, 1)
    if wins:
        return wins[0]

    # 2. Block immediate opponent win
    opp_wins = _immediate_winning_moves(flat, -1)
    if opp_wins:
        # If several, choose one that also maximizes our position
        best_move = opp_wins[0]
        best_score = -10**18
        for cell in opp_wins:
            p = _idx(cell)
            flat[p] = 1
            score = _evaluate(flat)
            flat[p] = 0
            if score > best_score:
                best_score = score
                best_move = cell
        return best_move

    # 3. Search best move
    best_move = legal[0]
    best_val = -10**18

    alpha = -10**9
    beta = 10**9

    for cell in _ordered_moves(flat, 1):
        p = _idx(cell)
        flat[p] = 1
        val = -_negamax(flat, -1, -beta, -alpha)
        flat[p] = 0

        if val > best_val:
            best_val = val
            best_move = cell
        if val > alpha:
            alpha = val

    # 4. Safety: always return legal move
    if flat[_idx(best_move)] == 0:
        return best_move
    return legal[0]
