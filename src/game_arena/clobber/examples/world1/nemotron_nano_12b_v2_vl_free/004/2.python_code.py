
def policy(you, opponent):
    possible_moves = []

    # Collect all valid moves
    for r in range(5):
        for c in range(6):
            if you[r][c]:
                # Up
                if r > 0 and opponent[r-1][c]:
                    possible_moves.append((r, c, 'U', r-1, c))
                # Right
                if c + 1 < 6 and opponent[r][c+1]:
                    possible_moves.append((r, c, 'R'))
                # Down
                if r + 1 < 5 and opponent[r+1][c]:
                    possible_moves.append((r, c, 'D'))
                # Left
                if c - 1 >= 0 and opponent[r][c-1]:
                    possible_moves.append((r, c, 'L'))

    if not possible_moves:
        return None  # This case should not occur per problem constraints

    best_move = possible_moves[0]
    min_opponent_moves = float('inf')

    for move in possible_moves:
        start_r, start_c, dir, new_r, new_c = move

        # Simulate the move
        new_you = [row.copy() for row in you]
        new_opponent = [row.copy() for row in opponent]
        new_you[start_r][start_c] = 0
        new_you[new_r][new_c] = 1
        new_opponent[new_r][new_c] = 0

        # Count opponent's possible moves after this move
        count = 0
        for opp_r in range(5):
            for opp_c in range(6):
                if new_opponent[opp_r][opp_c]:
                    for dr, dc in [(-1, 0), (0, 1), (1, 0), (0, -1)]:
                        nr = opp_r + dr
                        nc_val = opp_c + dc
                        if 0 <= nr_opp < 5 and 0 <= nc_val < 6:
                            if new_you[nr_opp][nc_val] == 1:
                                count += 1
                                break  # Count one move per cell, not direction

        if count == 0:
            return f"{r},{c},{dir}"

        # Update best move if this reduces opponent's options
        if count < min_opponent_moves:
            min_opponent_moves = count
            best_move = move
        elif count == min_opponent_moves:
            # Tie-breaker: prefer earlier row-column tuples
            best_row, best_col = best_move[0], best_move[1]
            if (move[0], move[1]) < (best_row, best_col):
                best_move = move

    return f"{best_move[0]},{best_move[1]},{best_move[2]}"
