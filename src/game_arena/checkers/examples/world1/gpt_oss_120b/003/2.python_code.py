
import itertools

def policy(my_men, my_kings, opp_men, opp_kings, color):
    """
    Return a legal move ((from_row, from_col), (to_row, to_col)) for the player to move.
    Captures are mandatory. The move selection follows a simple heuristic described above.
    """
    # ----- Helpers -------------------------------------------------
    def on_board(r, c):
        return 0 <= r < 8 and 0 <= c < 8

    def is_dark(r, c):
        return (r + c) % 2 == 1

    # Build a quick lookup for occupied squares
    occupied = {}
    for sq in my_men:
        occupied[sq] = 'my_man'
    for sq in my_kings:
        occupied[sq] = 'my_king'
    for sq in opp_men:
        occupied[sq] = 'opp_man'
    for sq in opp_kings:
        occupied[sq] = 'opp_king'

    # Direction vectors
    # (dr, dc) for simple moves
    if color == 'b':        # black moves downwards → lower row numbers
        man_dirs = [(-1, -1), (-1, 1)]
        promotion_row = 0
    else:                  # white moves upwards → higher row numbers
        man_dirs = [(1, -1), (1, 1)]
        promotion_row = 7

    king_dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)]

    # ----- Capture generation ---------------------------------------
    def generate_captures(piece_pos, is_king):
        captures = []
        r, c = piece_pos
        dirs = king_dirs if is_king else man_dirs
        for dr, dc in dirs:
            mid_r, mid_c = r + dr, c + dc          # square of the opponent piece
            to_r, to_c = r + 2*dr, c + 2*dc        # landing square
            if not (on_board(mid_r, mid_c) and on_board(to_r, to_c)):
                continue
            if not is_dark(to_r, to_c):
                continue
            if (mid_r, mid_c) not in occupied:
                continue
            if occupied[(mid_r, mid_c)] not in ('opp_man', 'opp_king'):
                continue
            if (to_r, to_c) in occupied:
                continue
            captures.append(((r, c), (to_r, to_c), occupied[(mid_r, mid_c)]))
        return captures

    # ----- Simple move generation ------------------------------------
    def generate_simple_moves(piece_pos, is_king):
        moves = []
        r, c = piece_pos
        dirs = king_dirs if is_king else man_dirs
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if not (on_board(nr, nc) and is_dark(nr, nc)):
                continue
            if (nr, nc) in occupied:
                continue
            moves.append(((r, c), (nr, nc)))
        return moves

    # ----- Collect all possible captures -----------------------------
    all_captures = []
    for p in my_men:
        all_captures.extend(generate_captures(p, is_king=False))
    for p in my_kings:
        all_captures.extend(generate_captures(p, is_king=True))

    if all_captures:
        # Prefer captures that take a king, then closest to promotion
        def capture_score(cap):
            (_, _), (_, _), victim = cap
            score = 0
            if victim == 'opp_king':
                score -= 1000            # big bonus
            # advance towards promotion
            (fr, _), (tr, _) = cap[0], cap[1]
            if color == 'b':
                score -= tr               # lower row is better
            else:
                score += tr               # higher row is better
            return score

        best_cap = min(all_captures, key=capture_score)
        return (best_cap[0], best_cap[1])

    # ----- No capture: choose an advancing simple move ---------------
    all_moves = []
    for p in my_men:
        all_moves.extend(generate_simple_moves(p, is_king=False))
    for p in my_kings:
        all_moves.extend(generate_simple_moves(p, is_king=True))

    if not all_moves:
        # No legal move (should not happen in a normal game); return a dummy stay‑move
        if my_men:
            return (my_men[0], my_men[0])
        elif my_kings:
            return (my_kings[0], my_kings[0])
        else:
            raise RuntimeError("No pieces to move")

    # Heuristic for simple moves
    def move_score(mv):
        (fr, fc), (tr, tc) = mv
        # distance to promotion for men
        if (fr, fc) in my_men:
            if color == 'b':
                return tr            # lower is better
            else:
                return -tr           # higher is better (negative to make smaller better)
        # for kings: centre distance (prefer centre)
        centre = 3.5
        return (abs(tr - centre) + abs(tc - centre))

    best_move = min(all_moves, key=move_score)
    return best_move
