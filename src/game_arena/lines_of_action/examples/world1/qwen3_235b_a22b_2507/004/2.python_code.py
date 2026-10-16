
def policy(board) -> str:
    import numpy as np

    # Directions: 8 possible movement directions (dy, dx)
    directions = [(-1,-1), (-1,0), (-1,1),
                  (0,-1),           (0,1),
                  (1,-1),  (1,0),   (1,1)]

    def in_bounds(r, c):
        return 0 <= r < 8 and 0 <= c < 8

    def count_pieces_along_direction(brd, r, c, dr, dc):
        count = 0
        cr, cc = r, c
        while in_bounds(cr, cc):
            if brd[cr][cc] != 0:
                count += 1
            cr += dr
            cc += dc
        return count

    def trace_path(brd, r, c, dr, dc, steps):
        # Returns the final (r, c) and whether path is blocked (by enemy piece mid-move)
        for i in range(1, steps + 1):
            nr, nc = r + dr * i, c + dc * i
            if not in_bounds(nr, nc):
                return None, False
            if i < steps and brd[nr][nc] == -1:  # Can jump over own, not opponent
                return None, False
        final_r, final_c = r + dr * steps, c + dc * steps
        if not in_bounds(final_r, final_c):
            return None, False
        return (final_r, final_c), True

    def get_legal_moves(brd):
        moves = []
        for r in range(8):
            for c in range(8):
                if brd[r][c] != 1:
                    continue
                for dr, dc in directions:
                    if dr == 0 and dc == 0:
                        continue
                    steps = count_pieces_along_direction(brd, r, c, dr, dc)
                    if steps == 0:
                        continue
                    # Try to move in this direction
                    final_pos, is_valid = trace_path(brd, r, c, dr, dc, steps)
                    if not is_valid or final_pos is None:
                        continue
                    fr, fc = final_pos
                    if brd[fr][fc] == 1:
                        continue  # Can't land on own piece
                    moves.append((r, c, fr, fc))
        return moves

    def count_groups(brd):
        visited = np.zeros((8,8), dtype=bool)
        groups = 0
        for i in range(8):
            for j in range(8):
                if brd[i][j] == 1 and not visited[i][j]:
                    groups += 1
                    # BFS to mark connected group
                    stack = [(i, j)]
                    visited[i][j] = True
                    while stack:
                        r, c = stack.pop()
                        for dr, dc in directions:
                            nr, nc = r + dr, c + dc
                            if in_bounds(nr, nc) and brd[nr][nc] == 1 and not visited[nr][nc]:
                                visited[nr][nc] = True
                                stack.append((nr, nc))
        return groups

    def evaluate_move(board, from_r, from_c, to_r, to_c):
        # Simulate move
        brd = [row[:] for row in board]
        brd[from_r][from_c] = 0
        was_capture = brd[to_r][to_c] == -1
        brd[to_r][to_c] = 1

        # Count groups
        new_groups = count_groups(brd)
        current_groups = count_groups(board)

        score = 0
        # Reward group reduction (more connecting)
        score += (current_groups - new_groups) * 100

        # Reward capturing (but not too much)
        if was_capture:
            score += 10

        # Encourage centrality of new position
        dist_from_center = abs(to_r - 3.5) + abs(to_c - 3.5)
        score -= dist_from_center * 0.5  # Prefer center

        # Avoid stranding the piece
        neighbors = 0
        for dr, dc in directions:
            nr, nc = to_r + dr, to_c + dc
            if in_bounds(nr, nc) and brd[nr][nc] == 1:
                neighbors += 1
        if neighbors == 0:
            score -= 50

        return score

    # Main logic
    legal_moves = get_legal_moves(board)
    if not legal_moves:
        # Fallback: must have at least one piece? if not, game over, but return dummy
        # In practice, if no legal moves, current player loses, but we must return something
        for r in range(8):
            for c in range(8):
                if board[r][c] == 1:
                    return f"{r},{c}:{r},{c}"

    # Score all moves
    scored_moves = []
    for move in legal_moves:
        score = evaluate_move(board, *move)
        scored_moves.append((score, move))

    # Sort by score descending
    scored_moves.sort(key=lambda x: x[0], reverse=True)
    best_move = scored_moves[0][1]

    return f"{best_move[0]},{best_move[1]}:{best_move[2]},{best_move[3]}"
