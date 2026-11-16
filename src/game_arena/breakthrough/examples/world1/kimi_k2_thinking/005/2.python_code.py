
import time

BOARD_SIZE = 8                     # 8×8 Breakthrough board

# ----------------------------------------------------------------------
#  Move generation
# ----------------------------------------------------------------------
def generate_moves(my_set, opp_set, color):
    """
    Return a list of legal moves for the player `color`.
    If a move reaches the opponent's home row it is returned as a single‑element list
    (instant win).
    Each move is ((from_row, from_col), (to_row, to_col)).
    """
    moves = []
    dr = -1 if color == 'b' else 1          # black moves down, white moves up
    home = 0 if color == 'b' else 7          # opponent's home row

    for r, c in my_set:
        nr = r + dr
        if not (0 <= nr < BOARD_SIZE):
            continue

        # ----- straight forward ------------------------------------------------
        if (nr, c) not in my_set and (nr, c) not in opp_set:
            if nr == home:                     # immediate win
                return [((r, c), (nr, c))]
            moves.append(((r, c), (nr, c)))

        # ----- diagonal left --------------------------------------------------
        nc = c - 1
        if 0 <= nc < BOARD_SIZE:
            if (nr, nc) in opp_set:            # capture
                if nr == home:
                    return [((r, c), (nr, nc))]
                moves.append(((r, c), (nr, nc)))
            elif (nr, nc) not in my_set:       # empty diagonal
                moves.append(((r, c), (nr, nc)))

        # ----- diagonal right -------------------------------------------------
        nc = c + 1
        if 0 <= nc < BOARD_SIZE:
            if (nr, nc) in opp_set:            # capture
                if nr == home:
                    return [((r, c), (nr, nc))]
                moves.append(((r, c), (nr, nc)))
            elif (nr, nc) not in my_set:       # empty diagonal
                moves.append(((r, c), (nr, nc)))

    return moves


# ----------------------------------------------------------------------
#  Apply a move (private helper)
# ----------------------------------------------------------------------
def apply_move(my_set, opp_set, move):
    """Return the two new sets after `move` is executed for the player."""
    fr, to = move
    new_my = set(my_set)
    new_opp = set(opp_set)

    # capture
    if to in new_opp:
        new_opp.remove(to)

    # move the piece
    new_my.remove(fr)
    new_my.add(to)

    return new_my, new_opp


# ----------------------------------------------------------------------
#  Evaluation helpers
# ----------------------------------------------------------------------
def sum_distance(pieces, color):
    """Sum of distances of `pieces` to the goal row for `color`."""
    if color == 'w':
        return sum(7 - r for r, _ in pieces)
    else:
        return sum(r for r, _ in pieces)


def evaluate(my_set, opp_set, color):
    """
    Score the position from the point of view of `color`.
    Large positive = winning.
    """
    # instant win for the player to move
    home = 0 if color == 'b' else 7
    if any(r == home for r, _ in my_set):
        return 1e6
    if len(opp_set) == 0:
        return 1e6

    # material advantage
    material = (len(my_set) - len(opp_set)) * 1000

    # advancement
    my_dist = sum_distance(my_set, color)
    opp_color = 'w' if color == 'b' else 'b'
    opp_dist = sum_distance(opp_set, opp_color)
    dist_score = (opp_dist - my_dist) * 10

    # central columns (3,4) give a tiny bonus
    central_my = sum(1 for _, c in my_set if c in (3, 4))
    central_opp = sum(1 for _, c in opp_set if c in (3, 4))
    central_score = (central_my - central_opp) * 5

    return material + dist_score + central_score


# ----------------------------------------------------------------------
#  Negamax α‑β search
# ----------------------------------------------------------------------
def negamax(my_set, opp_set, color, depth, alpha, beta,
            start_time, max_time):
    """Negamax with α‑β pruning – returns value for the player to move."""
    if time.time() - start_time > max_time:
        raise TimeoutError

    # win / lose immediately
    home = 0 if color == 'b' else 7
    if any(r == home for r, _ in my_set):
        return 1e6
    if len(opp_set) == 0:
        return 1e6

    if depth == 0:
        return evaluate(my_set, opp_set, color)

    moves = generate_moves(my_set, opp_set, color)
    if not moves:
        return -1e6                     # no legal move → lose

    # move ordering – captures first, forward second, diagonal last
    def move_key(m):
        fr, to = m
        if to in opp_set:
            return 1000
        if to[1] == fr[1]:
            return 100
        return 50

    moves = sorted(moves, key=move_key, reverse=True)

    best_val = -float('inf')
    opp_color = 'w' if color == 'b' else 'b'

    for mv in moves:
        new_my, new_opp = apply_move(my_set, opp_set, mv)
        child_val = -negamax(new_opp, new_my, opp_color,
                             depth - 1,
                             -beta, -alpha,
                             start_time, max_time)
        best_val = max(best_val, child_val)
        alpha = max(alpha, best_val)
        if alpha >= beta:
            break
    return best_val


# ----------------------------------------------------------------------
#  Iterative deepening driver
# ----------------------------------------------------------------------
def find_best_move(my_set, opp_set, color):
    """Return the best move for `color` using iterative deepening."""
    start = time.time()
    max_time = 0.9                     # stay safely under the 1 s limit

    # ------------------------------------------------ quick win detection
    home = 0 if color == 'b' else 7
    for r, c in my_set:
        nr = r + (-1 if color == 'b' else 1)
        if nr == home:
            # forward win
            if (nr, c) not in my_set and (nr, c) not in opp_set:
                return ((r, c), (nr, c))
            # diagonal capture win
            for nc in (c - 1, c + 1):
                if 0 <= nc < BOARD_SIZE and (nr, nc) in opp_set:
                    return ((r, c), (nr, nc))

    # ------------------------------------------------ normal search
    moves = generate_moves(my_set, opp_set, color)
    if not moves:                      # should never happen, but be safe
        return ((0, 0), (0, 0))
    if len(moves) == 1:
        return moves[0]

    # root move ordering (same heuristic as inside negamax)
    def move_key(m):
        fr, to = m
        if to in opp_set:
            return 1000
        if to[1] == fr[1]:
            return 100
        return 50

    moves = sorted(moves, key=move_key, reverse=True)

    best_move = None
    best_val = -float('inf')
    depth = 1

    try:
        while True:
            cur_best_move = None
            cur_best_val = -float('inf')
            alpha = -float('inf')
            beta = float('inf')

            for mv in moves:
                new_my, new_opp = apply_move(my_set, opp_set, mv)
                opp_color = 'w' if color == 'b' else 'b'
                val = -negamax(new_opp, new_my, opp_color,
                               depth - 1,
                               -beta, -alpha,
                               start, max_time)
                if val > cur_best_val:
                    cur_best_val = val
                    cur_best_move = mv
                alpha = max(alpha, val)
                if alpha >= beta:
                    break

            best_move = cur_best_move
            best_val = cur_best_val
            depth += 1
            if time.time() - start > max_time:
                break
    except TimeoutError:
        pass

    # final fallback – should never be needed
    if best_move is None:
        best_move = moves[0]
    return best_move


# ----------------------------------------------------------------------
#  Public API required by the arena
# ----------------------------------------------------------------------
def policy(me, opp, color):
    """
    me   – list of (row, col) of our pieces
    opp  – list of (row, col) of opponent pieces
    color – 'b' (black, moving down) or 'w' (white, moving up)
    returns ((from_row, from_col), (to_row, to_col))
    """
    my_set = set(me)
    opp_set = set(opp)
    move = find_best_move(my_set, opp_set, color)
    return move
