
import numpy as np

# ---------------------------------------------------------------------
#  Directions and helper lookups
# ---------------------------------------------------------------------
DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1),
              (0, -1),           (0, 1),
              (1, -1),  (1, 0),  (1, 1)]

DIR_TO_COUNT_TYPE = {
    (-1, 0): 'col',   (1, 0): 'col',
    (0, -1): 'row',   (0, 1): 'row',
    (-1, -1): 'diag1', (1, 1): 'diag1',
    (-1, 1): 'diag2',  (1, -1): 'diag2'
}

# ---------------------------------------------------------------------
#  Connectivity and win detection
# ---------------------------------------------------------------------
def _components(board, player):
    """Return (num_components, size_of_largest_component) for player."""
    visited = np.zeros((8, 8), dtype=bool)
    max_size = 0
    num_comp = 0
    for r in range(8):
        for c in range(8):
            if board[r, c] == player and not visited[r, c]:
                num_comp += 1
                size = 0
                stack = [(r, c)]
                visited[r, c] = True
                while stack:
                    cr, cc = stack.pop()
                    size += 1
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = cr + dr, cc + dc
                            if 0 <= nr < 8 and 0 <= nc < 8 and not visited[nr, nc] and board[nr, nc] == player:
                                visited[nr, nc] = True
                                stack.append((nr, nc))
                if size > max_size:
                    max_size = size
    return num_comp, max_size

def _is_win(board, player):
    """Return True if all of player's pieces form one connected group."""
    comp, _ = _components(board, player)
    return comp == 1 and np.any(board == player)

# ---------------------------------------------------------------------
#  Evaluation (from player 1's perspective)
# ---------------------------------------------------------------------
def _evaluate(board):
    """Static evaluation of the board for player 1."""
    our = np.sum(board == 1)
    opp = np.sum(board == -1)

    if our == 0:
        return -1_000_000
    if opp == 0:
        return 1_000_000

    if _is_win(board, 1):
        return 1_000_000
    if _is_win(board, -1):
        return -1_000_000

    # Piece material
    score = (our - opp) * 1000

    # Connectivity
    our_comp, our_big = _components(board, 1)
    opp_comp, opp_big = _components(board, -1)

    # Fewer groups / larger biggest group is better for us
    score += (our_big - opp_big) * 50
    score += (opp_comp - our_comp) * 30

    # Center control (central 2x2)
    centre = board[3:5, 3:5]
    score += (np.sum(centre == 1) - np.sum(centre == -1)) * 20

    return score

# ---------------------------------------------------------------------
#  Move generation
# ---------------------------------------------------------------------
def _legal_moves(board, player):
    """Return list of legal move strings for player."""
    moves = []

    # Line counts
    row_cnt = np.sum(np.abs(board) > 0, axis=1)
    col_cnt = np.sum(np.abs(board) > 0, axis=0)

    diag1_cnt = {}
    diag2_cnt = {}
    for r in range(8):
        for c in range(8):
            if board[r, c] != 0:
                diff = r - c
                s = r + c
                diag1_cnt[diff] = diag1_cnt.get(diff, 0) + 1
                diag2_cnt[s] = diag2_cnt.get(s, 0) + 1

    ours = np.argwhere(board == player)
    for r, c in ours:
        for dr, dc in DIRECTIONS:
            cnt_type = DIR_TO_COUNT_TYPE[(dr, dc)]
            if cnt_type == 'row':
                dist = row_cnt[r]
            elif cnt_type == 'col':
                dist = col_cnt[c]
            elif cnt_type == 'diag1':
                dist = diag1_cnt.get(r - c, 0)
            else:  # diag2
                dist = diag2_cnt.get(r + c, 0)

            if dist == 0:
                continue

            tr = r + dr * dist
            tc = c + dc * dist
            if not (0 <= tr < 8 and 0 <= tc < 8):
                continue
            if board[tr, tc] == player:
                continue  # cannot land on own piece

            # Check path for enemy pieces
            illegal = False
            for step in range(1, dist):
                rr = r + dr * step
                cc = c + dc * step
                if board[rr, cc] == -player:
                    illegal = True
                    break
            if not illegal:
                moves.append(f"{r},{c}:{tr},{tc}")

    return moves

# ---------------------------------------------------------------------
#  Apply a move
# ---------------------------------------------------------------------
def _apply(board, move, player):
    """Return a new board after 'player' plays 'move'."""
    fr, fc, tr, tc = map(int, move.replace(':', ',').split(','))
    b2 = board.copy()
    b2[tr, tc] = b2[fr, fc]
    b2[fr, fc] = 0
    return b2

# ---------------------------------------------------------------------
#  Minimax with alpha‑beta
# ---------------------------------------------------------------------
def _minimax(board, depth, alpha, beta, maximizing):
    """Return (value, best_move) for the current node."""
    if depth == 0:
        return _evaluate(board), None

    player = 1 if maximizing else -1
    moves = _legal_moves(board, player)
    if not moves:
        return _evaluate(board), None

    best_move = None
    if maximizing:
        max_val = -np.inf
        for m in moves:
            child = _apply(board, m, player)
            val, _ = _minimax(child, depth - 1, alpha, beta, False)
            if val > max_val:
                max_val = val
                best_move = m
            alpha = max(alpha, val)
            if beta <= alpha:
                break
        return max_val, best_move
    else:
        min_val = np.inf
        for m in moves:
            child = _apply(board, m, player)
            val, _ = _minimax(child, depth - 1, alpha, beta, True)
            if val < min_val:
                min_val = val
                best_move = m
            beta = min(beta, val)
            if beta <= alpha:
                break
        return min_val, best_move

# ---------------------------------------------------------------------
#  Public API
# ---------------------------------------------------------------------
def policy(board):
    """
    Return a legal move for player 1 on the given 8×8 board.
    The move is chosen by a depth‑2 minimax search with alpha‑beta pruning.
    """
    # Ensure we work with a NumPy array
    b = np.array(board, dtype=int)

    # Look for an immediate winning move
    my_moves = _legal_moves(b, 1)
    for m in my_moves:
        if _is_win(_apply(b, m, 1), 1):
            return m

    # Otherwise search two plies deep
    _, move = _minimax(b, depth=2, alpha=-np.inf, beta=np.inf, maximizing=True)

    # Fallback (should never happen)
    if move is None:
        return my_moves[0] if my_moves else "0,0:0,0"
    return move
