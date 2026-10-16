
import random
from copy import deepcopy

# all winning lines on a 3x3 board
WIN_LINES = [
    [(0, 0), (0, 1), (0, 2)],
    [(1, 0), (1, 1), (1, 2)],
    [(2, 0), (2, 1), (2, 2)],
    [(0, 0), (1, 0), (2, 0)],
    [(0, 1), (1, 1), (2, 1)],
    [(0, 2), (1, 2), (2, 2)],
    [(0, 0), (1, 1), (2, 2)],
    [(0, 2), (1, 1), (2, 0)],
]

def check_win(board_marks, player):
    """board_marks is a set of (r,c) occupied by the player."""
    for line in WIN_LINES:
        if all(cell in board_marks for cell in line):
            return True
    return False

def _simulate_one(board, move, rng):
    """
    Simulate a random continuation after we attempt ``move``.
    Returns 1 if we eventually win, -1 if opponent wins, 0 for draw.
    """
    # Our confirmed marks
    my_marks = {(r, c) for r in range(3) for c in range(3) if board[r][c] == 1}
    # Cells we do not know anything about
    unknown = [(r, c) for r in range(3) for c in range(3) if board[r][c] == 0]

    # How many opponent marks are plausible?
    # In a normal alternating game the opponent has either the same
    # number of successful moves as we have, or one less if we started.
    my_cnt = len(my_marks)
    possible_opp_counts = [my_cnt, max(0, my_cnt - 1)]
    opp_cnt = rng.choice([c for c in possible_opp_counts if c <= len(unknown)])

    # Randomly pick opponent positions among the unknown cells
    opp_marks = set(rng.sample(unknown, opp_cnt))

    # Attempt our move
    r, c = move
    if (r, c) in opp_marks:
        # move fails – we gain nothing, turn passes to opponent
        succeeded = False
    else:
        succeeded = True
        my_marks.add((r, c))

    # Immediate win check after a successful placement
    if succeeded and check_win(my_marks, 1):
        return 1

    # Remaining empty cells after the attempt
    empty = [cell for cell in unknown if cell not in opp_marks and cell not in my_marks]

    # Next player: opponent if our move succeeded or not (in both cases turn passes)
    turn = 'opp'

    while empty:
        cell = rng.choice(empty)
        empty.remove(cell)
        if turn == 'opp':
            opp_marks.add(cell)
            if check_win(opp_marks, 2):
                return -1
            turn = 'me'
        else:
            my_marks.add(cell)
            if check_win(my_marks, 1):
                return 1
            turn = 'opp'

    # board full – draw
    return 0

def _estimate_move(board, move, simulations=300):
    """Estimate win probability for a given move using Monte‑Carlo."""
    rng = random.Random()
    win = 0
    for _ in range(simulations):
        result = _simulate_one(board, move, rng)
        if result == 1:
            win += 1
    return win / simulations

def policy(board):
    """
    Return the next move (row, col) for Phantom Tic‑Tac‑Toe.
    `board` is a 3×3 list of lists with 1 = our confirmed mark,
    0 = unknown (could be empty or opponent's).
    """
    # Collect all cells that are not already ours
    legal = [(r, c) for r in range(3) for c in range(3) if board[r][c] == 0]

    if not legal:
        # No move possible – fallback to centre (should never happen)
        return (1, 1)

    # ---- 1. Immediate winning move (if any) ----
    my_marks = {(r, c) for r in range(3) for c in range(3) if board[r][c] == 1}
    for r, c in legal:
        # Pretend we get this cell; does it complete a line?
        hypothetical = my_marks | {(r, c)}
        if check_win(hypothetical, 1):
            return (r, c)

    # ---- 2. Monte‑Carlo evaluation ----
    best_move = None
    best_score = -1.0

    # Number of simulations per candidate adapts to remaining time;
    # 300 is a safe default for the 1 s limit.
    sims_per_move = 300

    for move in legal:
        score = _estimate_move(board, move, simulations=sims_per_move)
        if score > best_score:
            best_score = score
            best_move = move

    # If for some reason Monte‑Carlo failed to pick (should not), pick centre or random.
    if best_move is None:
        best_move = (1, 1) if board[1][1] == 0 else legal[0]

    return best_move
