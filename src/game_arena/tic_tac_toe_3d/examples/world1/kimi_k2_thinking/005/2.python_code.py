
import time

# ----------------------------------------------------------------------
# 1.  Pre‑compute all winning lines and their bit‑masks
# ----------------------------------------------------------------------
def _generate_lines_and_masks():
    """Return (list of line triples, list of bit‑masks) for 3x3x3 tic‑tac‑toe."""
    lines, masks = [], []
    seen = set()
    for i0 in range(3):
        for j0 in range(3):
            for k0 in range(3):
                for di in (-1, 0, 1):
                    for dj in (-1, 0, 1):
                        for dk in (-1, 0, 1):
                            if di == dj == dk == 0:
                                continue
                            i1, j1, k1 = i0 + di, j0 + dj, k0 + dk
                            i2, j2, k2 = i0 + 2 * di, j0 + 2 * dj, k0 + 2 * dk
                            if 0 <= i1 < 3 and 0 <= j1 < 3 and 0 <= k1 < 3 \
                               and 0 <= i2 < 3 and 0 <= j2 < 3 and 0 <= k2 < 3:
                                idx0 = i0 * 9 + j0 * 3 + k0
                                idx1 = i1 * 9 + j1 * 3 + k1
                                idx2 = i2 * 9 + j2 * 3 + k2
                                key = tuple(sorted((idx0, idx1, idx2)))
                                if key not in seen:
                                    seen.add(key)
                                    lines.append((idx0, idx1, idx2))
                                    masks.append((1 << idx0) | (1 << idx1) | (1 << idx2))
    return lines, masks


_WIN_LINES, _LINE_MASKS = _generate_lines_and_masks()

# ----------------------------------------------------------------------
# 2.  Helper constants and conversions
# ----------------------------------------------------------------------
_WIN_SCORE = 1_000_000          # value of a certain win
_CENTER_IDX = 13                 # (1,1,1) in flat indexing
_CORNER_IDX = {0, 2, 6, 8, 18, 20, 24, 26}


def _flatten(board):
    """Convert 3‑D list into a flat tuple of 27 ints."""
    return tuple(board[i][j][k] for i in range(3) for j in range(3) for k in range(3))


def _idx_to_coord(idx):
    """Turn a flat index (0‑26) into a 3‑D coordinate tuple (i,j,k)."""
    i = idx // 9
    rem = idx % 9
    j = rem // 3
    k = rem % 3
    return (i, j, k)


def _bits_from_board(board):
    """Return two bit‑sets: bits occupied by player 1 and by player -1."""
    pl_bits, opp_bits = 0, 0
    for idx, v in enumerate(board):
        if v == 1:
            pl_bits |= 1 << idx
        elif v == -1:
            opp_bits |= 1 << idx
    return pl_bits, opp_bits


# ----------------------------------------------------------------------
# 3.  Core game‑logic functions (win detection, evaluation)
# ----------------------------------------------------------------------
def _is_win(board, player):
    """Return True if `player` (1 or -1) has a winning line."""
    bits = 0
    for idx, v in enumerate(board):
        if v == player:
            bits |= 1 << idx
    for m in _LINE_MASKS:
        if (bits & m) == m:
            return True
    return False


def _evaluate(board):
    """
    Heuristic evaluation of a board position from the point of view
    of player 1.  Higher values mean a better position for player 1.
    """
    pl_bits, opp_bits = _bits_from_board(board)
    total = 0
    for m in _LINE_MASKS:
        pc = (pl_bits & m).bit_count()
        oc = (opp_bits & m).bit_count()
        if pc == 3:
            total += _WIN_SCORE
        elif oc == 3:
            total -= _WIN_SCORE
        elif pc == 2 and oc == 0:
            total += 10
        elif oc == 2 and pc == 0:
            total -= 10
        elif pc == 1 and oc == 0:
            total += 1
        elif oc == 1 and pc == 0:
            total -= 1
    return total


def _empty_cells(board):
    """Return a list of flat indices that are still empty."""
    return [i for i, v in enumerate(board) if v == 0]


def _copy_board_move(board, idx, player):
    """Return a new board tuple with `player` placed at `idx`."""
    return board[:idx] + (player,) + board[idx + 1:]


# ----------------------------------------------------------------------
# 4.  Move ordering helper
# ----------------------------------------------------------------------
def _sort_moves(moves):
    """Return `moves` ordered: centre, corners, rest."""
    result = []
    if _CENTER_IDX in moves:
        result.append(_CENTER_IDX)
    for m in moves:
        if m in _CORNER_IDX and m != _CENTER_IDX:
            result.append(m)
    for m in moves:
        if m != _CENTER_IDX and m not in _CORNER_IDX:
            result.append(m)
    return result


# ----------------------------------------------------------------------
# 5.  Minimax with alpha‑beta pruning
# ----------------------------------------------------------------------
def _minimax(board, depth, maximizing, alpha, beta):
    """Standard alpha‑beta search."""
    if _is_win(board, 1):
        return _WIN_SCORE
    if _is_win(board, -1):
        return -_WIN_SCORE
    if depth == 0:
        return _evaluate(board)

    empty = _empty_cells(board)
    if not empty:
        return 0

    if maximizing:                     # player 1 to move
        best = -float('inf')
        for idx in _sort_moves(empty):
            nxt = _copy_board_move(board, idx, 1)
            val = _minimax(nxt, depth - 1, False, alpha, beta)
            best = max(best, val)
            alpha = max(alpha, val)
            if beta <= alpha:
                break
        return best
    else:                               # opponent (‑1) to move
        best = float('inf')
        for idx in _sort_moves(empty):
            nxt = _copy_board_move(board, idx, -1)
            val = _minimax(nxt, depth - 1, True, alpha, beta)
            best = min(best, val)
            beta = min(beta, val)
            if beta <= alpha:
                break
        return best


# ----------------------------------------------------------------------
# 6.  Search a given depth (returns best move and its value)
# ----------------------------------------------------------------------
def _search_best(board, depth):
    """Find the best move at a fixed depth."""
    empty = _empty_cells(board)
    best_val = -float('inf')
    best_move = None
    for idx in _sort_moves(empty):
        nxt = _copy_board_move(board, idx, 1)
        # if the move already wins, play it immediately
        if _is_win(nxt, 1):
            return idx, _WIN_SCORE
        # let the opponent answer
        if depth > 1:
            val = _minimax(nxt, depth - 1, False, -float('inf'), float('inf'))
        else:
            val = _evaluate(nxt)
        if val > best_val:
            best_val = val
            best_move = idx
    return best_move, best_val


# ----------------------------------------------------------------------
# 7.  Iterative deepening with a time limit
# ----------------------------------------------------------------------
def _iterative_deepening(board, time_limit=0.95):
    """Search deeper and deeper until time runs out."""
    start = time.time()
    best_move = None
    depth = 1
    while True:
        move, val = _search_best(board, depth)
        if val >= _WIN_SCORE // 2:          # a forced win – play it now
            return move
        if move is not None:
            best_move = move
        if time.time() - start > time_limit:
            break
        depth += 1
        # do not search deeper than the number of empty squares + 1
        if depth > len(_empty_cells(board)) + 2:
            break
    return best_move


# ----------------------------------------------------------------------
# 8.  Public API required by the arena
# ----------------------------------------------------------------------
def policy(board):
    """
    Return the next move as a tuple (i, j, k) for the given board.
    The board is a 3‑D list: board[i][j][k] ∈ {‑1, 0, 1}.
    """
    flat_board = _flatten(board)
    best_idx = _iterative_deepening(flat_board)
    return _idx_to_coord(best_idx)
