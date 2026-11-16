
import numpy as np

# ----------------------------------------------------------------------
# Othello policy implementation
# ----------------------------------------------------------------------
DIRS = [(-1, -1), (-1, 0), (-1, 1),
        (0, -1),          (0, 1),
        (1, -1),  (1, 0), (1, 1)]

# classic positional weights (corners, edges, X‑squares, etc.)
WEIGHTS = np.array([
    [100, -20, 10, 5, 5, 10, -20, 100],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [10, -2, -1, -1, -1, -1, -2, 10],
    [5, -2, -1, -1, -1, -1, -2, 5],
    [5, -2, -1, -1, -1, -1, -2, 5],
    [10, -2, -1, -1, -1, -1, -2, 10],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [100, -20, 10, 5, 5, 10, -20, 100]
])

def legal_moves(you: np.ndarray, opp: np.ndarray):
    """Return a list of (r, c) tuples for all legal moves of `you`."""
    empties = np.where((you == 0) & (opp == 0))
    moves = []
    for r, c in zip(*empties):
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            seen_opponent = False
            while 0 <= nr < 8 and 0 <= nc < 8:
                if opp[nr, nc]:
                    seen_opponent = True
                elif you[nr, nc]:
                    if seen_opponent:
                        moves.append((r, c))
                    break
                else:
                    break
                nr += dr
                nc += dc
            if (r, c) in moves:
                break
    return moves

def apply_move(you: np.ndarray, opp: np.ndarray, move):
    """Place a disc for `you` at `move` and flip captured opponent discs."""
    r, c = move
    new_you = you.copy()
    new_opp = opp.copy()
    new_you[r, c] = 1

    for dr, dc in DIRS:
        flips = []
        nr, nc = r + dr, c + dc
        while 0 <= nr < 8 and 0 <= nc < 8:
            if opp[nr, nc]:
                flips.append((nr, nc))
            elif you[nr, nc]:
                for fr, fc in flips:
                    new_you[fr, fc] = 1
                    new_opp[fr, fc] = 0
                break
            else:
                break
            nr += dr
            nc += dc
    return new_you, new_opp

def evaluate(you: np.ndarray, opp: np.ndarray):
    """Static board evaluation from the point of view of `you`."""
    disc_diff = np.sum(you) - np.sum(opp)
    positional = np.sum(WEIGHTS * (you - opp))
    mob = len(legal_moves(you, opp)) - len(legal_moves(opp, you))
    # weighting factors (tuned empirically)
    return 10 * disc_diff + positional + 5 * mob

def negamax(you: np.ndarray, opp: np.ndarray, depth: int,
            alpha: float, beta: float) -> float:
    """
    Negamax search with alpha‑beta pruning.
    Returns the best score for the player to move (`you`).
    """
    moves = legal_moves(you, opp)

    # terminal / leaf node
    if depth == 0 or not moves:
        # if both players have no moves the game is over
        if not moves and not legal_moves(opp, you):
            return evaluate(you, opp)
        # pass turn
        if not moves:
            return -negamax(opp, you, depth - 1, -beta, -alpha)

    best = -float('inf')
    for mv in moves:
        n_you, n_opp = apply_move(you, opp, mv)
        # after the move the opponent becomes the "you" for the next call
        score = -negamax(n_opp, n_you, depth - 1, -beta, -alpha)
        if score > best:
            best = score
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best

def move_to_str(move):
    """Convert (r,c) board coordinate to algebraic notation."""
    r, c = move
    return chr(ord('a') + c) + str(r + 1)

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """
    Return the chosen move in algebraic notation or "pass".
    """
    moves = legal_moves(you, opponent)

    if not moves:
        return "pass"

    best_score = -float('inf')
    best_move = moves[0]

    # depth 4 works well within the time limit; can be lowered if needed
    SEARCH_DEPTH = 4

    for mv in moves:
        new_you, new_opp = apply_move(you, opponent, mv)
        score = -negamax(new_opp, new_you, SEARCH_DEPTH - 1,
                         -float('inf'), float('inf'))
        if score > best_score:
            best_score = score
            best_move = mv

    return move_to_str(best_move)
