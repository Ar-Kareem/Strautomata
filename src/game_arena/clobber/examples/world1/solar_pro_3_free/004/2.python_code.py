
def policy(you: list[list[int]], opponent: list[list[int]]) -> str:
    """
    Choose a legal capture move for a 5×6 Clobber board.
    Returns a string 'row,col,dir' where dir ∈ {'U','R','D','L'}.
    """
    # Directions: up, right, down, left
    dirs = [(-1, 0, 'U'), (1, 0, 'D'), (0, -1, 'L'), (0, 1, 'R')]
    moves = []  # list of (score, row, col, dest_row, dest_col, dir)

    for row in range(5):
        for col in range(6):
            if you[row][col] != 1:
                continue
            # Examine all orthogonal directions for a capture
            for dr, dc, d in dirs:
                dest_row, dest_col = row + dr, col + dc
                if not (0 <= dest_row < 5 and 0 <= dest_col < 6):
                    continue
                if opponent[dest_row][dest_col] != 1:
                    continue

                # ----- start piece's friendly adjacency (excluding the capture square) -----
                start_friendly = 0
                for ddr, ddc, ddir in dirs:
                    nr, nc = row + ddr, col + ddc
                    if nr == dest_row and nc == dest_col:
                        continue  # ignore the capture direction
                    if 0 <= nr < 5 and 0 <= nc < 6 and you[nr][nc] == 1:
                        start_friendly += 1

                # ----- destination piece's friendly adjacency after the move -----
                dest_friendly = 0
                for ddr, ddc, ddir in dirs:
                    nr, nc = dest_row + ddr, dest_col + ddc
                    if nr == row and nc == col:   # exclude the former start square (it will be empty)
                        continue
                    if 0 <= nr < 5 and 0 <= nc < 6 and you[nr][nc] == 1:
                        dest_friendly += 1

                # ----- opponent piece's adjacency at the destination (excluding the start square) -----
                opp_adj = 0
                for ddr, ddc, ddir in dirs:
                    nr, nc = dest_row + ddr, dest_col + ddc
                    if nr == row and nc == col:
                        continue
                    if 0 <= nr < 5 and 0 <= nc < 6 and opponent[nr][nc] == 1:
                        opp_adj += 1

                # ----- Penalties / bonuses -----
                isolated_pen = -10 if dest_friendly == 0 else -5 if dest_friendly == 1 else 0
                border_bonus = 1 if dest_row == 0 or dest_row == 4 or dest_col == 0 or dest_col == 5 else 0
                score = (
                    dest_friendly
                    + opp_adj
                    + border_bonus
                    - start_friendly
                    + isolated_pen
                )
                moves.append((score, row, col, dest_row, dest_col, d))

    if not moves:
        # No legal move – according to the arena this should not happen.
        raise ValueError("No legal moves found")

    # Choose the highest‑scoring move, breaking ties lexicographically
    best = max(moves, key=lambda x: (x[0], x[1], x[2], x[3], x[4]))
    return f"{best[1]},{best[3]},{best[4]}"
