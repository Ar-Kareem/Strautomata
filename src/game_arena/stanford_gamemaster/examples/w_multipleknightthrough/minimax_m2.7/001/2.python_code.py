
import random

def policy(state, role):
    # ------------------------------------------------------------------
    # Helper mappings
    # ------------------------------------------------------------------
    board_to_idx = {'a': 0, 'b': 1, 'c': 2}
    idx_to_board = {0: 'a', 1: 'b', 2: 'c'}
    col_to_idx   = {'a': 0, 'b': 1, 'c': 2, 'd': 3}
    idx_to_col   = {0: 'a', 1: 'b', 2: 'c', 3: 'd'}

    # ------------------------------------------------------------------
    # Parse the board – build a dictionary of occupied squares
    # ------------------------------------------------------------------
    occupancy = {}
    for fact in state:
        if fact[0] == 'cell':
            board = fact[1]
            col   = fact[2]
            row   = int(fact[3])
            color = fact[4]
            occupancy[(board, col, row)] = color

    # ------------------------------------------------------------------
    # Determine forward direction and winning target
    # ------------------------------------------------------------------
    forward_sign = 1 if role == 'white' else -1
    target_board = 'b'
    target_row   = 8 if role == 'white' else 1

    # ------------------------------------------------------------------
    # Generate all legal moves
    # ------------------------------------------------------------------
    moves = []
    for (board, col, row), color in occupancy.items():
        if color != role:
            continue

        board_idx = board_to_idx[board]
        col_idx   = col_to_idx[col]
        row_val   = row

        # Row step can be 1 or 2, forward direction only
        for row_step in (1, 2):
            delta_row = forward_sign * row_step
            new_row = row_val + delta_row
            if not (1 <= new_row <= 8):
                continue

            # Board step can be -2 .. +2 (including staying on same board)
            for board_delta in range(-2, 3):
                new_board_idx = board_idx + board_delta
                if new_board_idx < 0 or new_board_idx > 2:
                    continue

                # The knight‑like constraint: |Δrow| + |Δboard| must be 2 or 3
                if (abs(delta_row) + abs(board_delta)) not in (2, 3):
                    continue

                # Column does not change (Δcol = 0)
                new_col_idx = col_idx

                target_board_str = idx_to_board[new_board_idx]
                target_col_str   = idx_to_col[new_col_idx]

                # Cannot land on a square occupied by our own piece
                if occupancy.get((target_board_str, target_col_str, new_row)) == role:
                    continue

                moves.append((board, col, row_val,
                              target_board_str, target_col_str, new_row))

    # Remove possible duplicates (different generation paths can give same move)
    seen = set()
    unique_moves = []
    for m in moves:
        if m not in seen:
            seen.add(m)
            unique_moves.append(m)

    # If no legal move (should not happen), return a dummy legal move
    if not unique_moves:
        return "move(a,a,1,b,3)"   # arbitrary fallback

    # ------------------------------------------------------------------
    # Check for immediate winning moves
    # ------------------------------------------------------------------
    winning = [m for m in unique_moves
               if m[3] == target_board and m[5] == target_row]
    if winning:
        chosen = random.choice(winning)
        return f"move({chosen[0]},{chosen[1]},{chosen[2]},{chosen[3]},{chosen[4]},{chosen[5]})"

    # ------------------------------------------------------------------
    # Heuristic scoring: prefer higher row progress and proximity to board b
    # ------------------------------------------------------------------
    def score_move(m):
        _, _, _, nb, _, nr = m
        board_idx = board_to_idx[nb]
        board_dist = abs(board_idx - 1)          # distance to board 'b' (index 1)
        if role == 'white':
            row_score = nr * 100                  # higher row is better
        else:
            row_score = (9 - nr) * 100             # lower row is better for black
        board_score = (2 - board_dist) * 10        # board b is best (distance 0)
        return row_score + board_score

    best_score = -1
    best_moves = []
    for m in unique_moves:
        s = score_move(m)
        if s > best_score:
            best_score = s
            best_moves = [m]
        elif s == best_score:
            best_moves.append(m)

    chosen = random.choice(best_moves)
    return f"move({chosen[0]},{chosen[1]},{chosen[2]},{chosen[3]},{chosen[4]},{chosen[5]})"
