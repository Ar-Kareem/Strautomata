
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

    # 4 space diagonals
    lines.append([(d, d, d) for d in range(3)])
    lines.append([(d, d, 2 - d) for d in range(3)])
    lines.append([(d, 2 - d, d) for d in range(3)])
    lines.append([(d, 2 - d, 2 - d) for d in range(3)])

    # Remove any accidental duplicates while preserving order
    seen = set()
    uniq = []
    for line in lines:
        t = tuple(line)
        if t not in seen:
            seen.add(t)
            uniq.append(line)
    return uniq

LINES = _generate_lines()

# For each cell, store which winning lines pass through it.
CELL_TO_LINES = {(i, j, k): [] for i in range(3) for j in range(3) for k in range(3)}
for idx, line in enumerate(LINES):
    for cell in line:
        CELL_TO_LINES[cell].append(idx)

# Static positional weights based on line participation, with a tiny center bonus.
POSITION_WEIGHT = {}
for cell, line_ids in CELL_TO_LINES.items():
    POSITION_WEIGHT[cell] = len(line_ids)
POSITION_WEIGHT[(1, 1, 1)] += 3  # emphasize true center

def _empty_cells(board: Board):
    out = []
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    out.append((i, j, k))
    return out

def _find_immediate_win(board: Board, player: int):
    # Return a winning empty cell for player if it exists.
    for line in LINES:
        vals = [board[i][j][k] for (i, j, k) in line]
        if vals.count(player) == 2 and vals.count(0) == 1:
            idx = vals.index(0)
            return line[idx]
    return None

def _count_immediate_wins(board: Board, player: int):
    # Count distinct empty cells that are immediate winning moves for player.
    wins = set()
    for line in LINES:
        vals = [board[i][j][k] for (i, j, k) in line]
        if vals.count(player) == 2 and vals.count(0) == 1:
            wins.add(line[vals.index(0)])
    return len(wins)

def _would_allow_opponent_win(board: Board, move: Tuple[int, int, int]):
    i, j, k = move
    board[i][j][k] = 1
    opp_can_win = _find_immediate_win(board, -1) is not None
    board[i][j][k] = 0
    return opp_can_win

def _move_score(board: Board, move: Tuple[int, int, int]):
    i, j, k = move

    # Play move
    board[i][j][k] = 1

    # If this is winning, make it enormous.
    if _find_immediate_win(board, 1) is not None:
        # This means there may still be another immediate win next turn,
        # but actual immediate win is handled earlier; keep large score anyway.
        base = 100000
    else:
        base = 0

    # Count our next-turn winning threats after this move
    my_threats = _count_immediate_wins(board, 1)

    # Count opponent immediate winning threats after this move
    opp_threats = _count_immediate_wins(board, -1)

    # Line-based heuristic around this move
    line_value = 0
    for line_idx in CELL_TO_LINES[(i, j, k)]:
        line = LINES[line_idx]
        vals = [board[a][b][c] for (a, b, c) in line]
        my_count = vals.count(1)
        opp_count = vals.count(-1)
        empty_count = vals.count(0)
        if opp_count == 0:
            if my_count == 2 and empty_count == 1:
                line_value += 50
            elif my_count == 1 and empty_count == 2:
                line_value += 8
            elif my_count == 3:
                line_value += 200
        if my_count == 0:
            if opp_count == 2 and empty_count == 1:
                line_value += 30  # occupying a critical defensive line
            elif opp_count == 1 and empty_count == 2:
                line_value += 3

    pos = POSITION_WEIGHT[(i, j, k)]

    score = (
        base
        + 1000 * my_threats
        - 1200 * opp_threats
        + line_value
        + 5 * pos
    )

    # Undo move
    board[i][j][k] = 0
    return score

def policy(board: Board) -> Tuple[int, int, int]:
    legal = _empty_cells(board)
    if not legal:
        # Should not happen in normal play, but return a valid tuple.
        return (0, 0, 0)

    # 1. Immediate win
    win = _find_immediate_win(board, 1)
    if win is not None and board[win[0]][win[1]][win[2]] == 0:
        return win

    # 2. Immediate block
    block = _find_immediate_win(board, -1)
    if block is not None and board[block[0]][block[1]][block[2]] == 0:
        return block

    # 3. Score moves, preferring safe ones.
    best_move = None
    best_score = None

    safe_moves = []
    unsafe_moves = []
    for mv in legal:
        if _would_allow_opponent_win(board, mv):
            unsafe_moves.append(mv)
        else:
            safe_moves.append(mv)

    candidates = safe_moves if safe_moves else legal

    for mv in candidates:
        sc = _move_score(board, mv)

        # Deterministic tie-breakers:
        # higher positional weight, then lexicographically smallest
        tie = (POSITION_WEIGHT[mv], -mv[0], -mv[1], -mv[2])
        key = (sc, tie)

        if best_score is None or key > best_score:
            best_score = key
            best_move = mv

    if best_move is not None:
        return best_move

    # 4. Fallback: always return first legal move
    return legal[0]
