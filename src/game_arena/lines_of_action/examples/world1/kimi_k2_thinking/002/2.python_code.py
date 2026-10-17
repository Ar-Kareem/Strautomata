
import numpy as np

def policy(board):
    """
    Return a legal Lines‑of‑Action move for the current player (1).
    The board is an 8×8 list of lists, 0 = empty, 1 = player, -1 = opponent.
    """
    board_arr = np.array(board, dtype=int)
    player = 1
    try:
        move = get_best_move(board_arr, player)
    except Exception:
        # safety fallback – should never happen
        moves = generate_moves(board_arr, player)
        move = moves[0] if moves else (0, 0, 0, 0)
    return f"{move[0]},{move[1]}:{move[2]},{move[3]}"

def get_best_move(board, player):
    """Alpha‑beta depth‑2 search – returns the best move tuple (r0,c0,r1,c1)."""
    _, move = minimax(board, player, depth=2, maximizing=True,
                      alpha=-np.inf, beta=np.inf)
    if move is None:
        moves = generate_moves(board, player)
        move = moves[0] if moves else (0, 0, 0, 0)
    return move

def minimax(board, player, depth, maximizing, alpha, beta):
    """Standard alpha‑beta recursion."""
    if depth == 0:
        return evaluate(board, player), None

    opp = -player
    if maximizing:
        best_score = -np.inf
        best_move = None
        moves = generate_moves(board, player)
        # try captures first – simple move ordering
        moves_sorted = sorted(moves,
                              key=lambda m: board[m[2], m[3]] == -player,
                              reverse=True)
        for mv in moves_sorted:
            nb = apply_move(board, mv, player)
            # instant win?
            if count_components(nb, player) == 1:
                return 1e6, mv
            score, _ = minimax(nb, opp, depth - 1, False, alpha, beta)
            if score > best_score:
                best_score = score
                best_move = mv
            alpha = max(alpha, best_score)
            if beta <= alpha:
                break
        return best_score, best_move
    else:
        best_score = np.inf
        best_move = None
        moves = generate_moves(board, opp)
        moves_sorted = sorted(moves,
                              key=lambda m: board[m[2], m[3]] == player,
                              reverse=True)
        for mv in moves_sorted:
            nb = apply_move(board, mv, opp)
            if count_components(nb, opp) == 1:
                return -1e6, None
            score, _ = minimax(nb, player, depth - 1, True, alpha, beta)
            if score < best_score:
                best_score = score
                best_move = mv
            beta = min(beta, best_score)
            if beta <= alpha:
                break
        return best_score, best_move

def generate_moves(board, player):
    """All legal moves for `player` on the given board."""
    moves = []

    # line counts for the whole board
    row_counts = [np.count_nonzero(board[r, :]) for r in range(8)]
    col_counts = [np.count_nonzero(board[:, c]) for c in range(8)]

    diag_main = {}   # key = r‑c
    diag_anti = {}   # key = r+c
    for r in range(8):
        for c in range(8):
            if board[r, c] != 0:
                d = r - c
                diag_main[d] = diag_main.get(d, 0) + 1
                s = r + c
                diag_anti[s] = diag_anti.get(s, 0) + 1

    for r in range(8):
        for c in range(8):
            if board[r, c] != player:
                continue
            # 8 directions (dx,dy)
            for dx, dy in [(-1, 0), (1, 0),
                           (0, -1), (0, 1),
                           (-1, -1), (1, 1),
                           (-1, 1), (1, -1)]:
                # distance to travel = number of pieces in the chosen line
                if dx == 0:                     # horizontal
                    dist = row_counts[r]
                elif dy == 0:                   # vertical
                    dist = col_counts[c]
                elif dx == dy:                  # main diagonal
                    d = r - c
                    dist = diag_main.get(d, 0)
                else:                           # anti diagonal
                    s = r + c
                    dist = diag_anti.get(s, 0)

                if dist == 0:
                    continue

                nr = r + dx * dist
                nc = c + dy * dist
                if not (0 <= nr < 8 and 0 <= nc < 8):
                    continue

                # cannot jump over opponent pieces
                blocked = False
                for step in range(1, dist):
                    sr = r + dx * step
                    sc = c + dy * step
                    if board[sr, sc] == -player:
                        blocked = True
                        break
                if blocked:
                    continue

                # cannot land on a friendly piece
                if board[nr, nc] == player:
                    continue

                moves.append((r, c, nr, nc))
    return moves

def apply_move(board, move, player):
    """Return a new board after performing `move`."""
    r0, c0, r1, c1 = move
    nb = board.copy()
    nb[r1, c1] = player
    nb[r0, c0] = 0
    return nb

def count_components(board, player):
    """Number of 8‑connected groups of `player`'s pieces."""
    visited = np.zeros((8, 8), dtype=bool)
    count = 0
    for r in range(8):
        for c in range(8):
            if board[r, c] == player and not visited[r, c]:
                count += 1
                stack = [(r, c)]
                visited[r, c] = True
                while stack:
                    cr, cc = stack.pop()
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = cr + dr, cc + dc
                            if 0 <= nr < 8 and 0 <= nc < 8 \
                                    and board[nr, nc] == player \
                                    and not visited[nr, nc]:
                                visited[nr, nc] = True
                                stack.append((nr, nc))
    return count

def evaluate(board, player):
    """Static evaluation: higher is better for `player`."""
    opp = -player
    own_c = count_components(board, player)
    opp_c = count_components(board, opp)

    if own_c == 1:
        return 1e6                 # already won
    if opp_c == 1:
        return -1e6                # opponent already won

    own_p = np.sum(board == player)
    opp_p = np.sum(board == opp)

    # favour fewer own components, more opponent components, and material advantage
    return (opp_c - own_c) * 100 + (own_p - opp_p)
