
import numpy as np
import time

# ----------------------------------------------------------------------
# 1. Constants and pre‑computed tables
# ----------------------------------------------------------------------
# Weight of each square (high positive = good, negative = dangerous)
WEIGHTS = np.array([
    [100, -10,  10,   5,   5,  10, -10, 100],
    [-10, -20,  -5,  -2,  -2,  -5, -20, -10],
    [ 10,  -5,   5,   1,   1,   5,  -5,  10],
    [  5,  -2,   1,   0,   0,   1,  -2,   5],
    [  5,  -2,   1,   0,   0,   1,  -2,   5],
    [ 10,  -5,   5,   1,   1,   5,  -5,  10],
    [-10, -20,  -5,  -2,  -2,  -5, -20, -10],
    [100, -10,  10,   5,   5,  10, -10, 100],
], dtype=int)

# Eight possible directions on the board
DIRS = [(-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)]

# Infinity for α‑β (any value larger than any realistic evaluation)
INF = 10 ** 9

# ----------------------------------------------------------------------
# 2. Public API – the only function that must be present
# ----------------------------------------------------------------------
def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """
    Return a legal Othello move for the player `you`.
    If no move exists return "pass".
    """
    # Build a board where 1 = player to move, -1 = opponent, 0 = empty
    board = you.astype(int) - opponent.astype(int)

    # Quick check – do we have any legal move?
    moves = legal_moves(board)
    if not moves:
        return "pass"

    # Iterative deepening with a soft time limit (≈0.9 s)
    start = time.perf_counter()
    best_move = None
    for depth in range(1, 30):                # depth will be increased until time runs out
        move, _ = negamax_root(board, depth)
        if move is not None:
            best_move = move
        if time.perf_counter() - start > 0.9:
            break

    # Fallback – if the search did not finish even a depth‑1 search,
    # return the first move we already generated.
    return best_move if best_move is not None else moves[0]

# ----------------------------------------------------------------------
# 3. Search core – negamax with α‑β pruning
# ----------------------------------------------------------------------
def negamax_root(board: np.ndarray, depth: int):
    """
    Find the best move for the player to move (board perspective) at a
    fixed depth.  Returns (move, score).
    """
    moves = legal_moves(board)
    # Order moves by static square value – helps α‑β cut‑offs
    moves.sort(key=lambda m: WEIGHTS[move_to_coord(m)], reverse=True)

    best_score = -INF
    best_move = None
    alpha, beta = -INF, INF

    for move in moves:
        new_board = make_move(board, move)
        score = -negamax(-new_board, depth - 1, -beta, -alpha)
        if score > best_score:
            best_score = score
            best_move = move
            alpha = max(alpha, score)
            if alpha >= beta:
                break
    return best_move, best_score

def negamax(board: np.ndarray, depth: int, alpha: int, beta: int) -> int:
    """
    Pure negamax evaluation from the viewpoint of the player to move.
    """
    if depth == 0:
        return evaluate(board)

    moves = legal_moves(board)
    if not moves:                                   # player cannot move
        opp_moves = legal_moves(-board)
        if not opp_moves:                           # both sides stuck → terminal
            return final_eval(board)
        # pass the turn to the opponent without consuming a ply
        return -negamax(-board, depth, -beta, -alpha)

    best = -INF
    for move in moves:
        new_board = make_move(board, move)
        score = -negamax(-new_board, depth - 1, -beta, -alpha)
        best = max(best, score)
        alpha = max(alpha, best)
        if alpha >= beta:
            break
    return best

def final_eval(board: np.ndarray) -> int:
    """Game‑over evaluation – large win/loss depending on disc difference."""
    diff = np.sum(board)                 # player discs – opponent discs
    if diff > 0:
        return 10000 + diff
    if diff < 0:
        return -10000 + diff
    return 0

def evaluate(board: np.ndarray) -> int:
    """
    Static evaluation from the player‑to‑move perspective.
    Uses a weighted board, a tiny mobility term and a frontier term.
    """
    # Weighted squares
    score = np.sum(board * WEIGHTS)

    # Mobility difference (how many more moves can we make than the opponent)
    player_mob = len(legal_moves(board))
    opp_mob = len(legal_moves(-board))
    score += (player_mob - opp_mob) * 5

    # Frontier difference (empty squares touching our discs vs opponent's)
    player_front = frontier_count(board)
    opp_front = frontier_count(-board)
    score -= (player_front - opp_front) * 5          # fewer frontier discs are better

    return score

def frontier_count(board: np.ndarray) -> int:
    """Number of empty squares that are adjacent to a player's disc."""
    empty = np.argwhere(board == 0)
    count = 0
    for r, c in empty:
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8 and board[nr, nc] == 1:
                count += 1
                break
    return count

# ----------------------------------------------------------------------
# 4. Move generation and board manipulation
# ----------------------------------------------------------------------
def legal_moves(board: np.ndarray):
    """All legal moves (algebraic notation) for the player to move."""
    empties = np.argwhere(board == 0)
    moves = []
    for r, c in empties:
        if is_legal_move(board, r, c):
            moves.append(coord_to_move(r, c))
    # Order by static value – helps the search
    moves.sort(key=lambda m: WEIGHTS[move_to_coord(m)], reverse=True)
    return moves

def is_legal_move(board: np.ndarray, r: int, c: int) -> bool:
    """True if placing a disc at (r,c) would flip at least one opponent disc."""
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        # need an opponent disc as the first neighbour
        if not (0 <= nr < 8 and 0 <= nc < 8) or board[nr, nc] != -1:
            continue
        # continue in the same direction looking for a player disc
        kr, kc = nr + dr, nc + dc
        while 0 <= kr < 8 and 0 <= kc < 8:
            val = board[kr, kc]
            if val == 1:                     # player disc at the far end → legal
                return True
            if val == -1:                     # another opponent disc, keep scanning
                kr += dr
                kc += dc
                continue
            break                              # empty cell – line doesn't close
    return False

def make_move(board: np.ndarray, move: str):
    """Return the board *after* the move is played (still from the mover's view)."""
    r, c = move_to_coord(move)
    new_board = board.copy()
    new_board[r, c] = 1                         # place the new disc

    for dr, dc in DIRS:
        to_flip = []
        nr, nc = r + dr, c + dc
        # collect a continuous line of opponent discs
        while 0 <= nr < 8 and 0 <= nc < 8 and new_board[nr, nc] == -1:
            to_flip.append((nr, nc))
            nr += dr
            nc += dc
        # if the line ends with a player disc, flip the whole line
        if 0 <= nr < 8 and 0 <= nc < 8 and new_board[nr, nc] == 1:
            for fr, fc in to_flip:
                new_board[fr, fc] = 1
        # otherwise the direction does not produce flips
    return new_board

def coord_to_move(r: int, c: int) -> str:
    """Zero‑based coordinates → algebraic notation (a1…h8)."""
    file_char = chr(ord('a') + c)
    rank = r + 1
    return f"{file_char}{rank}"

def move_to_coord(move: str):
    """Algebraic notation → zero‑based coordinates."""
    file_char = move[0]
    rank_char = move[1]
    c = ord(file_char) - ord('a')
    r = int(rank_char) - 1
    return r, c
