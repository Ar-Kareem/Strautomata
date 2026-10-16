
from typing import List, Tuple

# Precompute all 49 winning lines in a 3x3x3 cube.
LINES = []

# Axis-aligned lines
for j in range(3):
    for k in range(3):
        LINES.append([(i, j, k) for i in range(3)])  # along i
for i in range(3):
    for k in range(3):
        LINES.append([(i, j, k) for j in range(3)])  # along j
for i in range(3):
    for j in range(3):
        LINES.append([(i, j, k) for k in range(3)])  # along k

# Plane diagonals
# i-j planes for each k
for k in range(3):
    LINES.append([(0, 0, k), (1, 1, k), (2, 2, k)])
    LINES.append([(0, 2, k), (1, 1, k), (2, 0, k)])
# i-k planes for each j
for j in range(3):
    LINES.append([(0, j, 0), (1, j, 1), (2, j, 2)])
    LINES.append([(0, j, 2), (1, j, 1), (2, j, 0)])
# j-k planes for each i
for i in range(3):
    LINES.append([(i, 0, 0), (i, 1, 1), (i, 2, 2)])
    LINES.append([(i, 0, 2), (i, 1, 1), (i, 2, 0)])

# Space diagonals
LINES.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
LINES.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
LINES.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
LINES.append([(0, 2, 2), (1, 1, 1), (2, 0, 0)])

# For each cell, which lines contain it
CELL_TO_LINES = {(i, j, k): [] for i in range(3) for j in range(3) for k in range(3)}
for idx, line in enumerate(LINES):
    for cell in line:
        CELL_TO_LINES[cell].append(idx)

CENTER = (1, 1, 1)
FACE_CENTERS = {
    (1, 1, 0), (1, 1, 2),
    (1, 0, 1), (1, 2, 1),
    (0, 1, 1), (2, 1, 1),
}
CORNERS = {
    (0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),
    (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2),
}

def get_empty_cells(board):
    cells = []
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    cells.append((i, j, k))
    return cells

def line_values(board, line):
    return [board[i][j][k] for (i, j, k) in line]

def immediate_win_moves(board, player):
    wins = []
    for line in LINES:
        vals = line_values(board, line)
        if vals.count(player) == 2 and vals.count(0) == 1:
            idx = vals.index(0)
            wins.append(line[idx])
    # Deduplicate while preserving deterministic order
    seen = set()
    out = []
    for mv in wins:
        if mv not in seen:
            seen.add(mv)
            out.append(mv)
    return out

def count_immediate_wins_after_move(board, move, player):
    i, j, k = move
    board[i][j][k] = player
    count = 0
    seen = set()
    for line_idx in CELL_TO_LINES[move]:
        line = LINES[line_idx]
        vals = line_values(board, line)
        if vals.count(player) == 2 and vals.count(0) == 1:
            idx = vals.index(0)
            target = line[idx]
            if target not in seen:
                seen.add(target)
                count += 1
    board[i][j][k] = 0
    return count

def move_creates_immediate_win(board, move, player):
    i, j, k = move
    board[i][j][k] = player
    found = False
    for line_idx in CELL_TO_LINES[move]:
        line = LINES[line_idx]
        vals = line_values(board, line)
        if vals.count(player) == 3:
            found = True
            break
    board[i][j][k] = 0
    return found

def heuristic_score(board, move):
    i, j, k = move
    score = 0.0

    # Positional preference
    if move == CENTER:
        score += 7.0
    elif move in FACE_CENTERS:
        score += 4.0
    elif move in CORNERS:
        score += 3.5
    else:
        score += 2.5

    # Number of lines through cell
    score += 0.6 * len(CELL_TO_LINES[move])

    # Offensive line potential and defensive denial
    for line_idx in CELL_TO_LINES[move]:
        line = LINES[line_idx]
        vals = line_values(board, line)
        my_count = vals.count(1)
        opp_count = vals.count(-1)
        empty_count = vals.count(0)

        # Before move, if line is open for us
        if opp_count == 0:
            if my_count == 1:
                score += 2.0
            elif my_count == 0:
                score += 0.8

        # If opponent is building in this line, occupying here is useful
        if my_count == 0:
            if opp_count == 1:
                score += 1.2
            elif opp_count == 2 and empty_count == 1:
                score += 10.0

    # Evaluate after making move
    board[i][j][k] = 1
    future_wins = 0
    strong_lines = 0
    weak_blocks_given = 0
    for line_idx in CELL_TO_LINES[move]:
        line = LINES[line_idx]
        vals = line_values(board, line)
        my_count = vals.count(1)
        opp_count = vals.count(-1)
        if my_count == 2 and opp_count == 0:
            future_wins += 1
        if my_count == 1 and opp_count == 0:
            strong_lines += 1
        if my_count == 0 and opp_count == 2:
            weak_blocks_given += 1
    # Opponent immediate wins after our move
    opp_immediate = len(immediate_win_moves(board, -1))
    board[i][j][k] = 0

    score += 6.0 * future_wins
    score += 1.0 * strong_lines
    score -= 8.0 * opp_immediate
    score -= 0.5 * weak_blocks_given

    return score

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    empties = get_empty_cells(board)
    if not empties:
        return (0, 0, 0)  # Should not happen in a valid game, but returns a tuple.

    # 1. Immediate winning move
    my_wins = immediate_win_moves(board, 1)
    if my_wins:
        return sorted(my_wins)[0]

    # 2. Block opponent immediate win
    opp_wins = immediate_win_moves(board, -1)
    if opp_wins:
        # If multiple blocks exist, prefer one that also helps us most
        best = None
        best_score = None
        for mv in opp_wins:
            if board[mv[0]][mv[1]][mv[2]] != 0:
                continue
            sc = heuristic_score(board, mv)
            if best is None or sc > best_score or (sc == best_score and mv < best):
                best = mv
                best_score = sc
        if best is not None:
            return best

    # 3. Create fork: move that gives at least two distinct immediate winning threats next turn
    fork_moves = []
    for mv in empties:
        threats = count_immediate_wins_after_move(board, mv, 1)
        if threats >= 2:
            fork_moves.append((threats, mv))
    if fork_moves:
        fork_moves.sort(key=lambda x: (-x[0], x[1]))
        return fork_moves[0][1]

    # 4. Block opponent fork if possible
    opp_forks = []
    for mv in empties:
        threats = count_immediate_wins_after_move(board, mv, -1)
        if threats >= 2:
            opp_forks.append((threats, mv))
    if opp_forks:
        # Prefer moves that occupy one of opponent fork cells; otherwise choose move
        # that creates our own threat / best heuristic.
        fork_cells = {mv for _, mv in opp_forks}
        candidates = [mv for mv in empties if mv in fork_cells]
        if not candidates:
            candidates = empties
        best = None
        best_score = None
        for mv in candidates:
            sc = heuristic_score(board, mv)
            # Bonus for directly occupying opponent fork square
            if mv in fork_cells:
                sc += 5.0
            if best is None or sc > best_score or (sc == best_score and mv < best):
                best = mv
                best_score = sc
        if best is not None:
            return best

    # 5. Prefer center
    if board[1][1][1] == 0:
        return (1, 1, 1)

    # 6. Best heuristic move
    best = None
    best_score = None
    for mv in empties:
        sc = heuristic_score(board, mv)
        if best is None or sc > best_score or (sc == best_score and mv < best):
            best = mv
            best_score = sc

    if best is not None and board[best[0]][best[1]][best[2]] == 0:
        return best

    # 7. Guaranteed legal fallback
    return sorted(empties)[0]
