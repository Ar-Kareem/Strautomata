
from typing import List, Tuple

# Precompute all 49 winning lines in a 3x3x3 cube.
def _generate_lines():
    lines = []

    # Rows in each layer
    for i in range(3):
        for j in range(3):
            lines.append([(i, j, k) for k in range(3)])

    # Columns in each layer
    for i in range(3):
        for k in range(3):
            lines.append([(i, j, k) for j in range(3)])

    # Pillars through layers
    for j in range(3):
        for k in range(3):
            lines.append([(i, j, k) for i in range(3)])

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

    # 4 space diagonals
    lines.append([(d, d, d) for d in range(3)])
    lines.append([(d, d, 2 - d) for d in range(3)])
    lines.append([(d, 2 - d, d) for d in range(3)])
    lines.append([(d, 2 - d, 2 - d) for d in range(3)])

    return lines


_LINES = _generate_lines()

# For each cell, which lines contain it?
_CELL_TO_LINES = {}
for i in range(3):
    for j in range(3):
        for k in range(3):
            _CELL_TO_LINES[(i, j, k)] = []
for idx, line in enumerate(_LINES):
    for cell in line:
        _CELL_TO_LINES[cell].append(idx)


def _empty_cells(board):
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


def _line_values(board, line):
    return [board[i][j][k] for (i, j, k) in line]


def _winning_moves(board, player):
    wins = []
    for line in _LINES:
        vals = _line_values(board, line)
        if vals.count(player) == 2 and vals.count(0) == 1:
            empty_idx = vals.index(0)
            wins.append(line[empty_idx])
    # deduplicate while preserving order
    seen = set()
    out = []
    for m in wins:
        if m not in seen:
            seen.add(m)
            out.append(m)
    return out


def _count_immediate_wins_after_move(board, move, player):
    i, j, k = move
    board[i][j][k] = player
    count = len(_winning_moves(board, player))
    board[i][j][k] = 0
    return count


def _positional_score(cell):
    # Number of coordinates equal to center 1.
    # center (3) > face centers (2) > edges/corners etc by line participation.
    i, j, k = cell
    center_matches = (i == 1) + (j == 1) + (k == 1)

    # Primary preference by actual line participation
    participation = len(_CELL_TO_LINES[cell])

    # Small deterministic tie-break favoring center, then corners slightly
    is_center = 1 if cell == (1, 1, 1) else 0
    is_corner = 1 if (i in (0, 2) and j in (0, 2) and k in (0, 2)) else 0

    return participation * 100 + is_center * 10 + center_matches * 3 + is_corner


def _strategic_score(board, move):
    # Build a heuristic score for move quality.
    score = 0

    # Offensive potential and line control
    for line_idx in _CELL_TO_LINES[move]:
        line = _LINES[line_idx]
        vals = _line_values(board, line)
        my_count = vals.count(1)
        opp_count = vals.count(-1)
        empty_count = vals.count(0)

        if opp_count == 0:
            # Purely usable line for us
            if my_count == 2 and empty_count == 1:
                score += 10000
            elif my_count == 1 and empty_count == 2:
                score += 200
            elif my_count == 0 and empty_count == 3:
                score += 30

        if my_count == 0:
            # If line is open only for opponent, occupying this square disrupts it
            if opp_count == 2 and empty_count == 1:
                score += 9000
            elif opp_count == 1 and empty_count == 2:
                score += 120

        if my_count > 0 and opp_count > 0:
            # contested line has less value
            score += 1

    score += _positional_score(move)
    return score


def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    # Gather legal moves safely
    legal = _empty_cells(board)
    if not legal:
        # Should not happen in valid play, but return a valid tuple format.
        return (0, 0, 0)

    # 1. Immediate win
    my_wins = _winning_moves(board, 1)
    for move in my_wins:
        if move in legal:
            return move

    # 2. Immediate block
    opp_wins = _winning_moves(board, -1)
    if opp_wins:
        # If multiple blocks exist, choose the most strategic blocking move.
        best = None
        best_score = None
        for move in opp_wins:
            if move in legal:
                s = _strategic_score(board, move) + _positional_score(move)
                if best is None or s > best_score:
                    best = move
                    best_score = s
        if best is not None:
            return best

    # 3. Create fork: move that yields at least 2 immediate wins next turn
    best_fork = None
    best_fork_score = None
    for move in legal:
        wins_created = _count_immediate_wins_after_move(board, move, 1)
        if wins_created >= 2:
            s = wins_created * 100000 + _strategic_score(board, move)
            if best_fork is None or s > best_fork_score:
                best_fork = move
                best_fork_score = s
    if best_fork is not None:
        return best_fork

    # 4. Prevent opponent fork: choose move minimizing opponent's fork chances
    best = None
    best_tuple = None
    for move in legal:
        i, j, k = move
        board[i][j][k] = 1

        opp_best_fork_count = 0
        opp_immediate_wins = 0
        for omove in _empty_cells(board):
            c = _count_immediate_wins_after_move(board, omove, -1)
            if c >= 2:
                opp_best_fork_count += 1
            if c >= 1:
                opp_immediate_wins += 1

        board[i][j][k] = 0

        # Lexicographic objective:
        # fewer opponent forks, fewer opponent immediate threats, higher own strategic score
        tup = (-opp_best_fork_count, -opp_immediate_wins, _strategic_score(board, move), _positional_score(move))
        if best is None or tup > best_tuple:
            best = move
            best_tuple = tup

    if best is not None:
        return best

    # 5. Fallback: highest positional score legal move
    legal.sort(key=lambda m: (_positional_score(m), m[0], m[1], m[2]), reverse=True)
    return legal[0]
