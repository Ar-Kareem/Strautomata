
def policy(board):
    moves = []
    directions = [
        (0, 1),   # East
        (0, -1),  # West
        (1, 0),   # South
        (-1, 0),  # North
        (1, 1),   # Southeast
        (-1, -1), # Northwest
        (-1, 1),  # Northeast
        (1, -1),  # Southwest
    ]

    for r in range(8):
        for c in range(8):
            if board[r][c] != 1:
                continue

            for dr, dc in directions:
                # Determine line type and count of pieces in the line
                if dr == 0:
                    line_type = 'row'
                    line_pieces = [board[r][j] for j in range(8) if j != c]
                    N = sum(1 for cell in line_pieces if cell != 0)
                elif dc == 0:
                    line_type = 'col'
                    line_pieces = [board[i][c] for i in range(8) if i != r]
                    N = sum(1 for cell in line_pieces if cell != 0)
                elif dr == dc:
                    line_type = 'main'
                    k = r - c
                    line_pieces = []
                    for i in range(8):
                        j = i - k
                        if 0 <= j < 8:
                            line_pieces.append(board[i][j])
                    N = sum(1 for cell in line_pieces if cell != 0)
                elif dr == -dc:
                    line_type = 'anti'
                    k = r + c
                    line_pieces = []
                    for i in range(8):
                        j = k - i
                        if 0 <= j < 8:
                            line_pieces.append(board[i][j])
                    N = sum(1 for cell in line_pieces if cell != 0)
                else:
                    continue  # Not a valid direction for line movement

                if N == 0:
                    continue

                # Calculate new position
                new_r = r + dr * N
                new_c = c + dc * N

                if not (0 <= new_r < 8 and 0 <= new_c < 8):
                    continue

                # Check path validity
                valid = True
                for step in range(1, N + 1):
                    path_r = r + dr * step
                    path_c = c + dc * step
                    if path_r < 0 or path_r >= 8 or path_c < 0 or path_c >= 8:
                        valid = False
                        break
                    if board[path_r][path_c] == -1:
                        valid = False
                        break

                if not valid:
                    continue

                # Check destination cell
                if board[new_r][new_c] in (0, -1):
                    valid = True
                else:
                    valid = False

                if valid:
                    # Empirical evaluation to prioritize captures and central positions
                    score = 0
                    if board[new_r][new_c] == -1:
                        score += 100  # High priority for captures
                    # Proximity to center
                    score -= (4.5 - new_r) ** 2 + (4.5 - new_c) ** 2  # Higher is better (closer to center)
                    moves.append((score, r, c, new_r, new_c))

    if not moves:
        # Emergency fallback (should not happen in a valid game state)
        for r in range(8):
            for c in range(8):
                if board[r][c] == 1:
                    return "0,0:0,0"  # Default move to prevent failure, adjust as needed

    # Select the best move based on evaluation score
    moves.sort(reverse=True, key=lambda x: x[0])
    best_move = moves[0]
    return f"{best_move[1]},{best_move[2]}:{best_move[3]},{best_move[4]}"
