
import re

def policy(state: list[list[object]], role: str) -> str:
    # ---------- Helpers ----------
    def parse_cells(st):
        cells = set()
        for fact in st:
            if len(fact) >= 4 and fact[0] == "cell":
                _, col, row, color = fact[:4]
                cells.add((col, int(row), color))
        return cells

    cols = ["a", "b", "c", "d", "e", "f"]
    col_to_i = {c: i for i, c in enumerate(cols)}
    i_to_col = {i: c for c, i in col_to_i.items()}

    def in_bounds(ci, r):
        return 0 <= ci < 6 and 1 <= r <= 6

    # Standard knight deltas
    KN_DELTAS = [
        (1, 2), (2, 1), (2, -1), (1, -2),
        (-1, 2), (-2, 1), (-2, -1), (-1, -2)
    ]

    def goal_distance_for(color, row):
        # White must reach opposite side (top): row 6
        # Black must reach opposite side (bottom): row 1
        if color == "white":
            return 6 - row
        else:
            return row - 1

    def can_move_forward(color, r_from, r_to):
        # White at bottom moves "up" (increasing row), Black "down" (decreasing row)
        return (r_to > r_from) if color == "white" else (r_to < r_from)

    # ---------- Build board state ----------
    cells = parse_cells(state)
    my_color = role
    opp_color = "black" if role == "white" else "white"

    my_pieces = [(c, r) for (c, r, col) in cells if col == my_color]
    opp_pieces = {(c, r) for (c, r, col) in cells if col == opp_color}

    # If no pieces (shouldn't happen), return a syntactically valid fallback
    if not my_pieces:
        return "move(a,2,b,4)"

    legal_moves = []

    for (c_from, r_from) in my_pieces:
        ci_from = col_to_i[c_from]
        for dc, dr in KN_DELTAS:
            ci_to = ci_from + dc
            r_to = r_from + dr
            if not in_bounds(ci_to, r_to):
                continue
            if not can_move_forward(my_color, r_from, r_to):
                continue
            c_to = i_to_col[ci_to]

            # Can't land on own piece
            if (c_to, r_to) in {(c, r) for (c, r, col) in cells if col == my_color}:
                continue

            is_capture = (c_to, r_to) in opp_pieces
            legal_moves.append((c_from, r_from, c_to, r_to, is_capture))

    if not legal_moves:
        # No legal move found; return a fallback (should not be legal in real play, but avoid crash)
        return "move(a,2,b,4)"

    # ---------- One-ply safety check ----------
    # Determine if a destination square is attacked by opponent after the move.
    def squares_attacked_by(color):
        # Return set of squares (col,row) that 'color' could capture/occupy next,
        # using the same move rules and forward-only restriction.
        pieces = [(cc, rr) for (cc, rr, col) in cells if col == color]
        attacked = set()
        color_is_white = (color == "white")
        for (c_from, r_from) in pieces:
            ci_from = col_to_i[c_from]
            for dc, dr in KN_DELTAS:
                ci_to = ci_from + dc
                r_to = r_from + dr
                if not in_bounds(ci_to, r_to):
                    continue
                # forward constraint for attacker
                if color_is_white:
                    if r_to <= r_from:
                        continue
                else:
                    if r_to >= r_from:
                        continue
                c_to = i_to_col[ci_to]
                # In knights, "attack" depends only on being able to move there;
                # landing on own piece would be illegal, but for capture threat
                # we care about whether opponent can move onto our square.
                # That is allowed if our square is empty or occupied by opponent? Here it's our piece square,
                # so treat as empty for attack generation by checking not occupied by attacker.
                if (c_to, r_to) in {(c, r) for (c, r, col) in cells if col == color}:
                    continue
                attacked.add((c_to, r_to))
        return attacked

    # Precompute opponent attacked squares as baseline; we'll refine for captures by reasoning:
    # if we capture, opponent pieces set changes. We do a lightweight recompute for each candidate.
    opp_attacked_initial = squares_attacked_by(opp_color)

    def evaluate_move(move):
        c_from, r_from, c_to, r_to, is_capture = move

        # Priority 1: capture
        if is_capture:
            capture_value = 1000  # very high
        else:
            capture_value = 0

        # Priority 2: advancement
        my_dist = goal_distance_for(my_color, r_to)
        advance_value = -my_dist  # smaller dist => larger value

        # Priority 3: safety (avoid being capturable immediately)
        # Recompute attacked squares after move (simple and still cheap).
        # Build temporary piece sets
        new_my_pieces = [(c, r) for (c, r) in my_pieces if not (c == c_from and r == r_from)]
        new_my_pieces.append((c_to, r_to))

        new_opp_pieces = set(opp_pieces)
        if is_capture and (c_to, r_to) in new_opp_pieces:
            new_opp_pieces.remove((c_to, r_to))

        # Generate attacked squares by opponent using temp sets
        temp_cells = set()
        for (c, r) in new_my_pieces:
            temp_cells.add((c, r, my_color))
        for (c, r) in new_opp_pieces:
            temp_cells.add((c, r, opp_color))

        def temp_attacked_by(color, temp_cells):
            pieces = [(cc, rr) for (cc, rr, col) in temp_cells if col == color]
            attacked = set()
            color_is_white = (color == "white")
            own_squares = {(cc, rr) for (cc, rr, col) in temp_cells if col == color}
            for (c_from2, r_from2) in pieces:
                ci_from2 = col_to_i[c_from2]
                for dc, dr in KN_DELTAS:
                    ci_to2 = ci_from2 + dc
                    r_to2 = r_from2 + dr
                    if not in_bounds(ci_to2, r_to2):
                        continue
                    if color_is_white:
                        if r_to2 <= r_from2:
                            continue
                    else:
                        if r_to2 >= r_from2:
                            continue
                    c_to2 = i_to_col[ci_to2]
                    if (c_to2, r_to2) in own_squares:
                        continue
                    attacked.add((c_to2, r_to2))
            return attacked

        opp_attacked_after = temp_attacked_by(opp_color, temp_cells)
        threatened = (c_to, r_to) in opp_attacked_after

        safety_value = -500 if threatened else 0

        # Small preference to moves that also reduce opponent distance (pressure)
        opp_dist = goal_distance_for(opp_color, r_to)  # not exactly meaningful, but okay
        pressure_value = -0.1 * opp_dist

        return capture_value + advance_value + safety_value + pressure_value

    best = None
    best_score = None
    # Sort deterministically for stability
    for mv in sorted(legal_moves, key=lambda x: (x[0], x[1], x[2], x[3])):
        score = evaluate_move(mv)
        if best_score is None or score > best_score:
            best_score = score
            best = mv

    c_from, r_from, c_to, r_to, _ = best
    return f"move({c_from},{r_from},{c_to},{r_to})"
