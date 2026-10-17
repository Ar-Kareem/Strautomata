
import numpy as np
import time

# -------------------------------------------------------------------------
#  Directions used for movement and for the 8‑neighbour connectivity check
DIRS = [(-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)]

# -------------------------------------------------------------------------
#  Helpers for line‑of‑action move generation
def line_counts(board):
    """
    Returns:
        row_counts    – number of pieces in each row (both players)
        col_counts    – number of pieces in each column
        diag1_counts  – number of pieces on each NW‑SE diagonal (r‑c constant)
        diag2_counts  – number of pieces on each NE‑SW diagonal (r+c constant)
    """
    # rows / columns
    row_counts = np.sum(np.abs(board), axis=1)          # shape (8,)
    col_counts = np.sum(np.abs(board), axis=0)          # shape (8,)

    # diagonals
    diag1_counts = np.zeros(15, dtype=int)              # index = (r‑c) + 7
    diag2_counts = np.zeros(15, dtype=int)              # index = (r+c)

    for r in range(8):
        for c in range(8):
            if board[r, c] != 0:
                diff = r - c
                diag1_counts[diff + 7] += 1
                s = r + c
                diag2_counts[s] += 1

    return row_counts, col_counts, diag1_counts, diag2_counts


def generate_moves(board, player):
    """
    Return a list of legal moves for *player* (1 or -1).
    Each move is ((from_r, from_c), (to_r, to_c)).
    """
    moves = []
    row_c, col_c, d1_c, d2_c = line_counts(board)

    for r in range(8):
        for c in range(8):
            if board[r, c] != player:
                continue
            for dr, dc in DIRS:
                # distance that must be travelled in this direction
                if dr == 0 and dc != 0:                     # horizontal
                    L = row_c[r]
                elif dc == 0 and dr != 0:                   # vertical
                    L = col_c[c]
                elif dr == dc:                              # NE‑SW diagonal
                    diff = r - c
                    L = d1_c[diff + 7]
                else:                                       # NW‑SE diagonal
                    s = r + c
                    L = d2_c[s]

                if L == 0:          # should never happen (piece itself counts)
                    continue

                tr = r + dr * L
                tc = c + dc * L
                if not (0 <= tr < 8 and 0 <= tc < 8):
                    continue
                if board[tr, tc] == player:                # cannot land on own piece
                    continue

                # path must not contain an opponent piece
                blocked = False
                for step in range(1, L):
                    sr = r + dr * step
                    sc = c + dc * step
                    if board[sr, sc] == -player:
                        blocked = True
                        break
                if blocked:
                    continue

                moves.append(((r, c), (tr, tc)))
    return moves


def apply_move(board, move, player):
    """Return a new board where *move* has been played by *player*."""
    (r, c), (tr, tc) = move
    nb = board.copy()
    nb[r, c] = 0                # source becomes empty
    nb[tr, tc] = player         # destination gets the piece (capture is automatic)
    return nb


# -------------------------------------------------------------------------
#  Evaluation
def count_groups(board, player):
    """Number of connected components of *player* (8‑neighbour connectivity)."""
    visited = np.zeros((8, 8), dtype=bool)
    groups = 0
    for r in range(8):
        for c in range(8):
            if board[r, c] == player and not visited[r, c]:
                groups += 1
                stack = [(r, c)]
                visited[r, c] = True
                while stack:
                    cr, cc = stack.pop()
                    for dr, dc in DIRS:
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < 8 and 0 <= nc < 8 and not visited[nr, nc] and board[nr, nc] == player:
                            visited[nr, nc] = True
                            stack.append((nr, nc))
    return groups


def evaluate(board, player):
    """
    Heuristic value of *board* from the point of view of *player*.
    Larger is better for *player*.
    """
    my_groups = count_groups(board, player)
    if my_groups == 1:                 # player already connected → win
        return 1e6

    opp_groups = count_groups(board, -player)
    if opp_groups == 1:                 # opponent already connected → lose
        return -1e6

    my_pieces = np.sum(board == player)
    opp_pieces = np.sum(board == -player)

    # material is less important than connectivity, therefore a smaller weight
    score = (opp_groups - my_groups) * 100 + (my_pieces - opp_pieces) * 10
    return score


# -------------------------------------------------------------------------
#  Negamax search with α‑β
def negamax(board, player, depth, alpha, beta, start_time, time_limit):
    """Return the negamax value of *board*, respecting the clock."""
    if time.time() - start_time > time_limit:
        return 0                     # time‑out → neutral value, search will be cut

    if depth == 0:
        return evaluate(board, player)

    moves = generate_moves(board, player)
    if not moves:                    # no legal move (should not happen)
        return -1e6

    # simple move ordering – try promising moves first
    scored = []
    for mv in moves:
        nb = apply_move(board, mv, player)
        scored.append((evaluate(nb, player), mv))
    scored.sort(key=lambda x: x[0], reverse=True)

    best = -np.inf
    for _, mv in scored:
        if time.time() - start_time > time_limit:
            break
        nb = apply_move(board, mv, player)
        val = -negamax(nb, -player, depth - 1, -beta, -alpha, start_time, time_limit)
        if val >= beta:
            return beta
        if val > best:
            best = val
        if val > alpha:
            alpha = val
    return best


def find_best_move(board, player, depth, start_time, time_limit):
    """
    Search *board* for the best move for *player* with given depth.
    Returns (move, value) or (None, -∞) if the search is aborted.
    """
    moves = generate_moves(board, player)
    if not moves:
        return None, -np.inf

    # quick move ordering
    scored = []
    for mv in moves:
        nb = apply_move(board, mv, player)
        scored.append((evaluate(nb, player), mv))
    scored.sort(key=lambda x: x[0], reverse=True)

    best_move = None
    best_val = -np.inf
    for _, mv in scored:
        if time.time() - start_time > time_limit:
            break
        nb = apply_move(board, mv, player)
        val = -negamax(nb, -player, depth - 1, -np.inf, np.inf, start_time, time_limit)
        if val > best_val:
            best_val = val
            best_move = mv
    return best_move, best_val


# -------------------------------------------------------------------------
def policy(board):
    """
    Entry point for the tournament – receives an 8×8 list of lists
    (0 = empty, 1 = our piece, -1 = opponent) and returns a move string
    "from_row,from_col:to_row,to_col".
    """
    player = 1                                 # we are always the player "1"
    board_np = np.array(board, dtype=int)      # work with a numpy array
    start = time.time()
    max_time = 0.9   # leave a safety margin

    # fallback – any legal move (the first one)
    all_moves = generate_moves(board_np, player)
    if not all_moves:
        # Should never happen, but the rules require a legal move.
        return "0,0:0,0"
    best_move = all_moves[0]

    # iterative deepening (depth 1..4)
    for depth in range(1, 5):
        if time.time() - start > max_time:
            break
        move, _ = find_best_move(board_np, player, depth, start, max_time)
        if move is not None:
            best_move = move

    (fr, fc), (tr, tc) = best_move
    return f"{fr},{fc}:{tr},{tc}"
