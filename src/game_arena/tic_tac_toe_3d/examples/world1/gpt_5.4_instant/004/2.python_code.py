
from typing import List, Tuple

# Precompute all 49 winning lines in 3x3x3 tic tac toe.
def _generate_lines():
    lines = []

    # Axis-aligned lines
    for j in range(3):
        for k in range(3):
            lines.append([(i, j, k) for i in range(3)])  # along i
    for i in range(3):
        for k in range(3):
            lines.append([(i, j, k) for j in range(3)])  # along j
    for i in range(3):
        for j in range(3):
            lines.append([(i, j, k) for k in range(3)])  # along k

    # Diagonals in planes with fixed i
    for i in range(3):
        lines.append([(i, d, d) for d in range(3)])
        lines.append([(i, d, 2 - d) for d in range(3)])

    # Diagonals in planes with fixed j
    for j in range(3):
        lines.append([(d, j, d) for d in range(3)])
        lines.append([(d, j, 2 - d) for d in range(3)])

    # Diagonals in planes with fixed k
    for k in range(3):
        lines.append([(d, d, k) for d in range(3)])
        lines.append([(d, 2 - d, k) for d in range(3)])

    # Space diagonals
    lines.append([(d, d, d) for d in range(3)])
    lines.append([(d, d, 2 - d) for d in range(3)])
    lines.append([(d, 2 - d, d) for d in range(3)])
    lines.append([(d, 2 - d, 2 - d) for d in range(3)])

    return lines


LINES = _generate_lines()

# For each cell, which lines contain it?
CELL_TO_LINES = {(i, j, k): [] for i in range(3) for j in range(3) for k in range(3)}
for idx, line in enumerate(LINES):
    for cell in line:
        CELL_TO_LINES[cell].append(idx)

# Positional weight = number of winning lines through the cell.
POSITION_WEIGHT = {cell: len(CELL_TO_LINES[cell]) for cell in CELL_TO_LINES}


def _legal_moves(board):
    moves = []
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    moves.append((i, j, k))
    return moves


def _find_immediate_wins(board, player):
    wins = []
    for line in LINES:
        vals = [board[i][j][k] for (i, j, k) in line]
        if vals.count(player) == 2 and vals.count(0) == 1:
            empty_idx = vals.index(0)
            wins.append(line[empty_idx])
    # deduplicate while preserving order
    seen = set()
    out = []
    for mv in wins:
        if mv not in seen:
            seen.add(mv)
            out.append(mv)
    return out


def _count_immediate_wins_after_move(board, move, player):
    i, j, k = move
    board[i][j][k] = player
    cnt = len(_find_immediate_wins(board, player))
    board[i][j][k] = 0
    return cnt


def _move_score(board, move):
    i, j, k = move

    # Play move temporarily
    board[i][j][k] = 1

    # If already winning, make it maximal
    if _is_win(board, 1):
        board[i][j][k] = 0
        return 10**9

    my_threats = len(_find_immediate_wins(board, 1))
    opp_threats_after = len(_find_immediate_wins(board, -1))

    # Evaluate line structure around the move
    line_value = 0
    for line_idx in CELL_TO_LINES[(i, j, k)]:
        line = LINES[line_idx]
        vals = [board[a][b][c] for (a, b, c) in line]
        my_count = vals.count(1)
        opp_count = vals.count(-1)
        empty_count = vals.count(0)

        if opp_count == 0:
            if my_count == 2 and empty_count == 1:
                line_value += 500
            elif my_count == 1 and empty_count == 2:
                line_value += 40
            elif my_count == 3:
                line_value += 100000
        if my_count == 0:
            if opp_count == 2 and empty_count == 1:
                line_value += 80
            elif opp_count == 1 and empty_count == 2:
                line_value += 5

    board[i][j][k] = 0

    # Also evaluate opponent fork potential if we do not occupy this square.
    opp_forks_blocked = _count_immediate_wins_after_move(board, move, -1)

    score = 0
    score += 20000 * my_threats
    score -= 12000 * opp_threats_after
    score += 3000 * opp_forks_blocked
    score += 100 * POSITION_WEIGHT[(i, j, k)]
    score += line_value

    # Deterministic tiny tie-breaker favoring lexicographically smaller cells
    score -= (i * 9 + j * 3 + k) * 0.001
    return score


def _is_win(board, player):
    for line in LINES:
        if all(board[i][j][k] == player for (i, j, k) in line):
            return True
    return False


def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    legal = _legal_moves(board)
    if not legal:
        return (0, 0, 0)  # should not happen in valid game states

    # 1. Immediate win
    my_wins = _find_immediate_wins(board, 1)
    for mv in my_wins:
        if board[mv[0]][mv[1]][mv[2]] == 0:
            return mv

    # 2. Immediate block
    opp_wins = _find_immediate_wins(board, -1)
    for mv in opp_wins:
        if board[mv[0]][mv[1]][mv[2]] == 0:
            return mv

    # 3. Choose best heuristic move
    best_move = legal[0]
    best_score = None
    for mv in legal:
        sc = _move_score(board, mv)
        if best_score is None or sc > best_score:
            best_score = sc
            best_move = mv

    # 4. Guaranteed legal fallback
    if board[best_move[0]][best_move[1]][best_move[2]] == 0:
        return best_move

    for mv in legal:
        if board[mv[0]][mv[1]][mv[2]] == 0:
            return mv

    return (0, 0, 0)
