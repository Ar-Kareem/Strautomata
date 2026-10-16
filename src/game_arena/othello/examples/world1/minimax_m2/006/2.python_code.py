
import numpy as np
import sys

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
DIRS = [(-1, -1), (-1, 0), (-1, 1),
        (0, -1),          (0, 1),
        (1, -1),  (1, 0), (1, 1)]

# Weight matrix – corners high, neighbours of corners negative, edges moderate
WEIGHTS = np.array([
    [ 100, -20,  10,   5,   5,  10, -20, 100],
    [ -20, -50,  -2,  -2,  -2,  -2, -50, -20],
    [  10,  -2,   1,   1,   1,   1,  -2,  10],
    [   5,  -2,   1,   0,   0,   1,  -2,   5],
    [   5,  -2,   1,   0,   0,   1,  -2,   5],
    [  10,  -2,   1,   1,   1,   1,  -2,  10],
    [ -20, -50,  -2,  -2,  -2,  -2, -50, -20],
    [ 100, -20,  10,   5,   5,  10, -20, 100],
], dtype=np.float64)

MAX_DEPTH = 4               # search depth (adjustable)
INF = 10 ** 9

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def can_flip(r: int, c: int, player: np.ndarray, opponent: np.ndarray) -> bool:
    """Return True if placing a disc at (r,c) would flip any opponent discs."""
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        has_opp = False
        while 0 <= nr < 8 and 0 <= nc < 8 and opponent[nr, nc] == 1:
            has_opp = True
            nr += dr
            nc += dc
        if has_opp and 0 <= nr < 8 and 0 <= nc < 8 and player[nr, nc] == 1:
            return True
    return False


def get_flips(r: int, c: int, player: np.ndarray, opponent: np.ndarray):
    """Return a list of opponent disc positions that would be flipped."""
    flips = []
    for dr, dc in DIRS:
        cur = []
        nr, nc = r + dr, c + dc
        while 0 <= nr < 8 and 0 <= nc < 8 and opponent[nr, nc] == 1:
            cur.append((nr, nc))
            nr += dr
            nc += dc
        if cur and 0 <= nr < 8 and 0 <= nc < 8 and player[nr, nc] == 1:
            flips.extend(cur)
    return flips


def legal_moves(player: np.ndarray, opponent: np.ndarray):
    """Return a list of (r,c) tuples of all legal moves for player."""
    empty = np.where((player == 0) & (opponent == 0))
    moves = []
    for r, c in zip(empty[0], empty[1]):
        if can_flip(r, c, player, opponent):
            moves.append((r, c))
    return moves


def apply_move(player: np.ndarray, opponent: np.ndarray, move):
    """Place a disc for player at move and flip opponent discs."""
    r, c = move
    flips = get_flips(r, c, player, opponent)
    new_player = player.copy()
    new_opponent = opponent.copy()
    new_player[r, c] = 1
    for fr, fc in flips:
        new_player[fr, fc] = 1
        new_opponent[fr, fc] = 0
    return new_player, new_opponent


def static_eval(player: np.ndarray, opponent: np.ndarray):
    """Weighted square evaluation from the perspective of the player to move."""
    # Basic weighted sum
    score = np.sum(WEIGHTS * player) - np.sum(WEIGHTS * opponent)

    # Optional corner bonus (corners are already heavily weighted,
    # but an explicit count can help in some positions)
    corners = [(0, 0), (0, 7), (7, 0), (7, 7)]
    player_corners = sum(player[r, c] for r, c in corners)
    opp_corners = sum(opponent[r, c] for r, c in corners)
    score += 10 * (player_corners - opp_corners)

    # Small mobility bonus (optional, can be disabled for speed)
    # player_moves = len(legal_moves(player, opponent))
    # opp_moves = len(legal_moves(opponent, player))
    # score += 0.5 * (player_moves - opp_moves)

    return score


# ----------------------------------------------------------------------
# Minimax with alpha‑beta pruning
# ----------------------------------------------------------------------
def minimax(player: np.ndarray, opponent: np.ndarray,
            depth: int, alpha: int, beta: int, maximizing: bool):
    """Return the minimax value for the given board."""
    if depth == 0:
        return static_eval(player, opponent)

    moves = legal_moves(player, opponent)

    # If no moves, pass the turn to the opponent
    if not moves:
        # If the opponent also has no moves, the game ends – evaluate current board
        return minimax(opponent, player, depth - 1, alpha, beta, not maximizing)

    # Move ordering – evaluate the board after each immediate move and sort
    move_evals = []
    for m in moves:
        np_player, np_opponent = apply_move(player, opponent, m)
        # static_eval is from the perspective of the player who just moved
        ev = static_eval(np_player, np_opponent)
        move_evals.append((ev, m))

    if maximizing:
        # sort descending
        move_evals.sort(key=lambda x: -x[0])
        value = -INF
        for _, m in move_evals:
            np_player, np_opponent = apply_move(player, opponent, m)
            child = minimax(np_player, np_opponent,
                            depth - 1, alpha, beta, False)
            if child > value:
                value = child
            if value > alpha:
                alpha = value
            if beta <= alpha:
                break
        return value
    else:
        # minimizing
        move_evals.sort(key=lambda x: x[0])
        value = INF
        for _, m in move_evals:
            np_player, np_opponent = apply_move(player, opponent, m)
            child = minimax(np_player, np_opponent,
                            depth - 1, alpha, beta, True)
            if child < value:
                value = child
            if value < beta:
                beta = value
            if beta <= alpha:
                break
        return value


def choose_move(you: np.ndarray, opponent: np.ndarray):
    """Return the best move (r,c) for the current player, or None if no move."""
    moves = legal_moves(you, opponent)
    if not moves:
        return None
    if len(moves) == 1:
        return moves[0]

    # Order moves using static evaluation for the initial player
    ordered = []
    for m in moves:
        np_you, np_opp = apply_move(you, opponent, m)
        ev = static_eval(np_you, np_opp)
        ordered.append((ev, m))
    ordered.sort(key=lambda x: -x[0])

    best_val = -INF
    best_move = None
    for _, m in ordered:
        np_you, np_opp = apply_move(you, opponent, m)
        val = minimax(np_you, np_opp, MAX_DEPTH - 1, -INF, INF, False)
        if val > best_val:
            best_val = val
            best_move = m
    return best_move


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """
    Return the next move for the Othello game.
    you, opponent : 8x8 numpy arrays (0/1)
    The function must return a move string like 'd3' or 'pass'.
    """
    move = choose_move(you, opponent)
    if move is None:
        return "pass"
    r, c = move
    # Convert to algebraic notation: column a..h, row 1..8
    return chr(ord('a') + c) + str(r + 1)
