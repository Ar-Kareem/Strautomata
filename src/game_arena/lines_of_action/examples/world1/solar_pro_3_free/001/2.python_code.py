
def policy(board):
    """
    Return a legal move string for the current player (value 1) on an 8×8 Lines of Action board.
    Move format: "from_row,from_col:to_row,to_col"
    """
    PLAYER = 1
    OPPONENT = -1
    # All eight directions: (dr, dc)
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0),
                  (1, 1), (1, -1), (-1, 1), (-1, -1)]

    # Store candidate moves as (origin_r, origin_c, dest_r, dest_c, step_cnt, capture)
    candidates = []

    # Scan every cell to find pieces that belong to the current player
    for r in range(8):
        for c in range(8):
            if board[r][c] == PLAYER:
                for dr, dc in directions:
                    # 1️⃣ Count pieces in the line (excluding the starting cell)
                    cnt = 0
                    nr, nc = r + dr, c + dc
                    while 0 <= nr < 8 and 0 <= nc < 8:
                        if board[nr][nc] != 0:
                            cnt += 1
                        nr += dr
                        nc += dc

                    # Destination after moving exactly cnt squares
                    dest_r = r + dr * cnt
                    dest_c = c + dc * cnt
                    if not (0 <= dest_r < 8 and 0 <= dest_c < 8):
                        continue

                    # 2️⃣ Verify that no opponent piece blocks the way
                    blocked = False
                    for step in range(1, cnt):   # squares before the destination
                        nr = r + dr * step
                        nc = c + dc * step
                        if board[nr][nc] == OPPONENT:
                            blocked = True
                            break

                    if blocked:
                        continue

                    # 3️⃣ Capture check – opponent piece may only be at the destination
                    capture = board[dest_r][dest_c] == OPPONENT

                    candidates.append((r, c, dest_r, dest_c, cnt, capture))

    # If we found at least one legal move, choose the best according to the heuristic
    if candidates:
        # Prefer captures; if there are captures, pick the longest one
        capture_moves = [move for move in candidates if move[5]]
        if capture_moves:
            best = max(capture_moves, key=lambda m: m[4])  # longest capture
        else:
            # No capture, pick the longest non‑capture move
            best = max(candidates, key=lambda m: m[4])
        origin_r, origin_c, dest_r, dest_c, _, capture = best
        if capture:
            return f"{origin_r},{origin_c}:{dest_r},{dest_c}"
        else:
            return f"{origin_r},{origin_c}:{dest_r},{dest_c}"
    # In theory we should never reach here, but return a placeholder if board is strange
    # (This keeps the function from raising an exception while still abiding by the spec)
    # Scan again for any move – if none, return the first legal move we saw earlier.
    # As a safe fallback we simply use the first candidate even if it is empty.
    # This satisfies the “always return a legal move” requirement.
    # The arena should never give us an empty candidate list on a valid turn.
    # To avoid returning an empty string we raise an informative error (won't be seen by the arena).
    raise RuntimeError("No legal moves found – this should never happen on a valid board.")

# The function is ready to be imported and called as `policy(board)`.
