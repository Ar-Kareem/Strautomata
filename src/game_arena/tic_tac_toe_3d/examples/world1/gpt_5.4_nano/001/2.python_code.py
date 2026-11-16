
import random
from functools import lru_cache

# Precompute all winning lines in a 3x3x3 cube.
# Each line is a list of (i,j,k) coordinates of length 3.
WIN_LINES = []

# Helper to add a line from 3 points
def _add_line(p1, p2, p3):
    WIN_LINES.append((p1, p2, p3))

# All lines with constant two coords (axes)
for i in range(3):
    for j in range(3):
        _add_line((i, j, 0), (i, j, 1), (i, j, 2))  # varying k
for i in range(3):
    for k in range(3):
        _add_line((i, 0, k), (i, 1, k), (i, 2, k))  # varying j
for j in range(3):
    for k in range(3):
        _add_line((0, j, k), (1, j, k), (2, j, k))  # varying i

# Diagonals in each plane (3 planes for each fixed coord)
# Planes i=const: vary (j,k)
for i in range(3):
    _add_line((i, 0, 0), (i, 1, 1), (i, 2, 2))
    _add_line((i, 0, 2), (i, 1, 1), (i, 2, 0))
# Planes j=const: vary (i,k)
for j in range(3):
    _add_line((0, j, 0), (1, j, 1), (2, j, 2))
    _add_line((0, j, 2), (1, j, 1), (2, j, 0))
# Planes k=const: vary (i,j)
for k in range(3):
    _add_line((0, 0, k), (1, 1, k), (2, 2, k))
    _add_line((0, 2, k), (1, 1, k), (2, 0, k))

# Space diagonals (4)
_add_line((0, 0, 0), (1, 1, 1), (2, 2, 2))
_add_line((0, 0, 2), (1, 1, 1), (2, 2, 0))
_add_line((0, 2, 0), (1, 1, 1), (2, 0, 2))
_add_line((0, 2, 2), (1, 1, 1), (2, 0, 0))

# For speed: map each cell to lines that include it.
CELL_TO_LINES = {(i, j, k): [] for i in range(3) for j in range(3) for k in range(3)}
for line in WIN_LINES:
    for cell in line:
        CELL_TO_LINES[cell].append(line)


def _get_cell(board, i, j, k):
    return board[i][j][k]


def _set_move(board, i, j, k, player):
    board[i][j][k] = player


def _winner_and_lines(board):
    """Return winner: 1 or -1 if someone has a 3-in-a-row, else 0."""
    for a, b, c in WIN_LINES:
        va = _get_cell(board, *a)
        vb = _get_cell(board, *b)
        vc = _get_cell(board, *c)
        if va != 0 and va == vb and vb == vc:
            return va
    return 0


def _available_moves(board):
    moves = []
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    moves.append((i, j, k))
    return moves


def _immediate_win_move(board, player):
    """If player can win in one move, return such move else None."""
    for (i, j, k) in _available_moves(board):
        board[i][j][k] = player
        w = _winner_and_lines(board)
        board[i][j][k] = 0
        if w == player:
            return (i, j, k)
    return None


def _line_score_for_player(line, player):
    """Heuristic score for a line for player given current board content."""
    opp = -player
    vals = []
    for (i, j, k) in line:
        vals.append((i, j, k))
    # Count player/opponent/empty on the line by reading board values later.
    return vals


def _heuristic_move(board, move, player):
    """
    Strong-ish heuristic: compute line potential after placing 'player' at move.
    Higher score is better.
    """
    # Place mentally by evaluating lines that include move.
    opp = -player
    i, j, k = move
    score = 0

    # Positional prior: center is good, corners slightly better than edges.
    # In 3D, "center" is (1,1,1). Corners are 8 cells with sum of coords in {0,6}.
    if (i, j, k) == (1, 1, 1):
        score += 6
    s = i + j + k
    if (s == 0) or (s == 6):
        score += 3
    # Edges (two coords are 0/2 and one is 1) are moderate.
    # Count how many coordinates are middle.
    mid_count = (i == 1) + (j == 1) + (k == 1)
    if mid_count == 2:
        score += 1

    # Line-based threat evaluation
    for line in CELL_TO_LINES[(i, j, k)]:
        counts = {player: 0, opp: 0, 0: 0}
        empties = 0
        for (x, y, z) in line:
            v = board[x][y][z]
            if (x, y, z) == (i, j, k):
                v = player
            counts[v] = counts.get(v, 0) + 1
            if v == 0:
                empties += 1

        # If line is already blocked by opponent, no potential.
        if counts[opp] > 0:
            # But prefer blocking: if opponent has 2 and empty here, reward.
            if counts[player] == 0 and counts[opp] == 2 and empties == 1:
                score += 50
            continue

        # Otherwise, opponent not present => we can build.
        if counts[player] == 2 and empties == 1:
            score += 100  # immediate threat (would be winning next)
        elif counts[player] == 1 and empties == 2:
            score += 10
        elif counts[player] == 0 and empties == 3:
            score += 0
        else:
            # counts[player]==3 would be a win, but immediate_win already handled.
            score += 0

    # Additionally, try to reduce opponent's best threats by considering opponent lines.
    # This is a small look-ahead: if opponent could win next turn, block them.
    # Already handled immediate block; this catches "fork-like" setups.
    # We evaluate opponent potential after our move.
    # (Lightweight: check each opponent winning-threat opportunity.)
    # Temporarily apply move
    board[i][j][k] = player
    opp_threats = 0
    for opp_move in _available_moves(board):
        board[opp_move[0]][opp_move[1]][opp_move[2]] = opp
        if _winner_and_lines(board) == opp:
            opp_threats += 1
        board[opp_move[0]][opp_move[1]][opp_move[2]] = 0
    board[i][j][k] = 0
    score -= 25 * opp_threats

    return score


def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    Decide next move for 3x3x3 Tic Tac Toe.

    board[i][j][k] in {0,1,-1}. We are player 1.
    """
    player = 1
    opponent = -1

    # Defensive copy reference is fine since we mutate temporarily and revert.
    moves = _available_moves(board)
    # If board is full, shouldn't happen; return something legal if so.
    if not moves:
        return (0, 0, 0)

    # 1) Win immediately if possible.
    win_move = _immediate_win_move(board, player)
    if win_move is not None:
        return win_move

    # 2) Block opponent immediate win.
    block_move = _immediate_win_move(board, opponent)
    if block_move is not None:
        return block_move

    # 3) Heuristic scoring among remaining moves.
    # Add small randomness to avoid deterministic ties.
    best = None
    best_score = -10**18
    # Prefer center early when empty-ish.
    empty_count = len(moves)
    center = (1, 1, 1)
    if empty_count == 27 and board[1][1][1] == 0:
        return center

    # Score all candidates
    for m in moves:
        sc = _heuristic_move(board, m, player)
        # slight preference for moves with maximum line participation among empty lines
        # (acts as a tie-breaker)
        if best is None or sc > best_score:
            best_score = sc
            best = m
        elif sc == best_score:
            if random.random() < 0.5:
                best = m

    return best
