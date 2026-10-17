
from typing import List, Tuple

Board = List[List[List[int]]]

# Precompute all 49 winning lines in 3x3x3 tic tac toe.
def _generate_lines():
    lines = []

    # Straight lines along each axis
    for j in range(3):
        for k in range(3):
            lines.append([(i, j, k) for i in range(3)])  # vary i
    for i in range(3):
        for k in range(3):
            lines.append([(i, j, k) for j in range(3)])  # vary j
    for i in range(3):
        for j in range(3):
            lines.append([(i, j, k) for k in range(3)])  # vary k

    # Diagonals in planes
    # i-j planes for each k
    for k in range(3):
        lines.append([(d, d, k) for d in range(3)])
        lines.append([(d, 2 - d, k) for d in range(3)])

    # i-k planes for each j
    for j in range(3):
        lines.append([(d, j, d) for d in range(3)])
        lines.append([(d, j, 2 - d) for d in range(3)])

    # j-k planes for each i
    for i in range(3):
        lines.append([(i, d, d) for d in range(3)])
        lines.append([(i, d, 2 - d) for d in range(3)])

    # Space diagonals
    lines.append([(d, d, d) for d in range(3)])
    lines.append([(d, d, 2 - d) for d in range(3)])
    lines.append([(d, 2 - d, d) for d in range(3)])
    lines.append([(d, 2 - d, 2 - d) for d in range(3)])

    return lines

LINES = _generate_lines()

# Map each cell to the lines containing it.
CELL_TO_LINES = {}
for i in range(3):
    for j in range(3):
        for k in range(3):
            CELL_TO_LINES[(i, j, k)] = []
for idx, line in enumerate(LINES):
    for cell in line:
        CELL_TO_LINES[cell].append(idx)

# Static positional weights:
# center > corners > face centers > edge centers
POSITION_WEIGHT = {}
for i in range(3):
    for j in range(3):
        for k in range(3):
            c = sum(x == 1 for x in (i, j, k))
            # Number of coordinates equal to center 1
            if c == 3:
                w = 12  # center
            elif c == 2:
                w = 6   # face centers
            elif c == 1:
                w = 7   # corners
            else:
                w = 4   # edge-like outer centers
            POSITION_WEIGHT[(i, j, k)] = w

def _empty_cells(board: Board):
    cells = []
    for i in range(3):
        for j in range(3):
            for k in range(3):
                try:
                    if board[i][j][k] == 0:
                        cells.append((i, j, k))
                except Exception:
                    pass
    return cells

def _line_values(board: Board, line):
    vals = [board[i][j][k] for (i, j, k) in line]
    my_count = vals.count(1)
    opp_count = vals.count(-1)
    empty_count = vals.count(0)
    return my_count, opp_count, empty_count, vals

def _winning_moves(board: Board, player: int):
    wins = []
    target_other = -player
    for line in LINES:
        vals = [board[i][j][k] for (i, j, k) in line]
        if vals.count(player) == 2 and vals.count(0) == 1 and vals.count(target_other) == 0:
            idx = vals.index(0)
            wins.append(line[idx])
    # Deduplicate while preserving order
    seen = set()
    out = []
    for mv in wins:
        if mv not in seen:
            seen.add(mv)
            out.append(mv)
    return out

def _count_immediate_wins_after_move(board: Board, move, player: int):
    i, j, k = move
    board[i][j][k] = player
    wins = len(_winning_moves(board, player))
    board[i][j][k] = 0
    return wins

def _opponent_immediate_wins_after_my_move(board: Board, move):
    i, j, k = move
    board[i][j][k] = 1
    wins = len(_winning_moves(board, -1))
    board[i][j][k] = 0
    return wins

def _heuristic(board: Board, move):
    i, j, k = move

    # If illegal, terrible score.
    if not (0 <= i < 3 and 0 <= j < 3 and 0 <= k < 3):
        return -10**18
    if board[i][j][k] != 0:
        return -10**18

    score = POSITION_WEIGHT[move]

    # Simulate move
    board[i][j][k] = 1

    # Immediate tactical value
    my_wins = _winning_moves(board, 1)
    opp_wins = _winning_moves(board, -1)

    # Strongly reward creating multiple threats; strongly penalize allowing them.
    score += 200 * len(my_wins)
    score -= 260 * len(opp_wins)

    # Evaluate lines through this cell and globally
    for line_idx in CELL_TO_LINES[move]:
        line = LINES[line_idx]
        myc, oppc, empc, _ = _line_values(board, line)
        if oppc == 0:
            if myc == 3:
                score += 10000
            elif myc == 2 and empc == 1:
                score += 120
            elif myc == 1 and empc == 2:
                score += 18
        if myc == 0:
            if oppc == 2 and empc == 1:
                score += 90  # if our move blocked such a line, this line now won't qualify, but keeping some local defense value
            elif oppc == 1 and empc == 2:
                score -= 10

    # Global line evaluation
    for line in LINES:
        myc, oppc, empc, _ = _line_values(board, line)
        if oppc == 0:
            if myc == 2 and empc == 1:
                score += 25
            elif myc == 1 and empc == 2:
                score += 4
        elif myc == 0:
            if oppc == 2 and empc == 1:
                score -= 35
            elif oppc == 1 and empc == 2:
                score -= 3

    board[i][j][k] = 0
    return score

def policy(board: Board) -> Tuple[int, int, int]:
    # Gather legal moves safely
    legal = _empty_cells(board)

    # Absolute fallback: always return a legal tuple if possible
    if not legal:
        return (0, 0, 0)

    # 1. Immediate win
    my_wins = _winning_moves(board, 1)
    for mv in my_wins:
        if mv in legal:
            return mv

    # 2. Immediate block
    opp_wins = _winning_moves(board, -1)
    if opp_wins:
        # If several threats exist, choose a block that also scores best / blocks most.
        best_mv = None
        best_key = None
        opp_set = set(opp_wins)
        for mv in legal:
            blocks = 1 if mv in opp_set else 0

            # Simulate and see how many opponent immediate wins remain
            i, j, k = mv
            board[i][j][k] = 1
            rem_opp = len(_winning_moves(board, -1))
            my_next = len(_winning_moves(board, 1))
            board[i][j][k] = 0

            key = (blocks, -rem_opp, my_next, _heuristic(board, mv))
            if best_key is None or key > best_key:
                best_key = key
                best_mv = mv
        if best_mv is not None:
            return best_mv

    # 3. Heuristic search over legal moves
    best_move = None
    best_score = None
    for mv in legal:
        score = _heuristic(board, mv)
        # Small deterministic tie-breakers:
        # prefer center-like lexicographically stable ordering through tuple compare
        tie = (-abs(mv[0] - 1) - abs(mv[1] - 1) - abs(mv[2] - 1), -mv[0], -mv[1], -mv[2])
        key = (score, tie)
        if best_score is None or key > best_score:
            best_score = key
            best_move = mv

    if best_move is not None and best_move in legal:
        return best_move

    # Final legal fallback
    return legal[0]
