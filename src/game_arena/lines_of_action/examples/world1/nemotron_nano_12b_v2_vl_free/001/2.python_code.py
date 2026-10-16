
def policy(board) -> str:
    possible_moves = []

    for i in range(8):
        for j in range(8):
            if board[i][j] != 1:
                continue

            # Check row i (horizontal)
            row_cells = [(i, y) for y in range(8)]
            k_row = sum(board[x][y] != 0 for (x, y) in row_cells)
            if k_row > 0:
                # Move right
                new_j = j + k_row
                if 0 <= new_j < 8:
                    valid = True
                    for dy_step in range(1, k_row):
                        if board[i][j + dy_step] == -1:
                            valid = False
                            break
                    if valid and board[i][new_j] in (0, -1):
                        possible_moves.append(f"{i},{j}:{i},{new_j}")
                # Move left
                new_j = j - k_row
                if new_j >= 0:
                    valid = True
                    for dy_step in range(1, k_row):
                        if board[i][j - dy_step] == -1:
                            valid = False
                            break
                    if valid and board[i][new_j] in (0, -1):
                        possible_moves.append(f"{i},{j}:{i},{new_j}")

            # Check column j (vertical)
            col_cells = [(x, j) for x in range(8)]
            k_col = sum(board[x][y] != 0 for (x, y) in col_cells)
            if k_col > 0:
                # Move down
                new_i = i + k_col
                if 0 <= new_i < 8:
                    valid = True
                    for dx_step in range(1, k_col):
                        if board[i + dx_step][j] == -1:
                            valid = False
                            break
                    if valid and board[new_i][j] in (0, -1):
                        possible_moves.append(f"{i},{j}:{new_i},{j}")
                # Move up
                new_i = i - k_col
                if new_i >= 0:
                    valid = True
                    for dx_step in range(1, k_col):
                        if board[i - dx_step][j] == -1:
                            valid = False
                            break
                    if valid and board[new_i][j] in (0, -1):
                        possible_moves.append(f"{i},{j}:{new_i},{j}")

            # Check diagonal1 (i - j constant)
            diagonal1 = []
            x, y = i, j
            while x >= 0 and y >= 0:
                diagonal1.append((x, y))
                x -= 1
                y -= 1
            x, y = i + 1, j + 1
            while x < 8 and y < 8:
                diagonal1.append((x, y))
                x += 1
                y += 1
            k_diag1 = sum(board[x][y] != 0 for (x, y) in diagonal1)
            if k_diag1 > 0:
                # Direction (1,1)
                new_i = i + k_diag1
                new_j = j + k_diag1
                if 0 <= new_i < 8 and 0 <= new_j < 8:
                    valid = True
                    for t in range(1, k_diag1):
                        x_step = i + t
                        y_step = j + t
                        if not (0 <= x_step < 8 and 0 <= y_step < 8) or board[x_step][y_step] == -1:
                            valid = False
                            break
                    if valid and board[new_i][new_j] in (0, -1):
                        possible_moves.append(f"{i},{j}:{new_i},{new_j}")
                # Direction (-1,-1)
                new_i = i - k_diag1
                new_j = j - k_diag1
                if 0 <= new_i < 8 and 0 <= new_j < 8:
                    valid = True
                    for t in range(1, k_diag1):
                        x_step = i - t
                        y_step = j - t
                        if not (0 <= x_step < 8 and 0 <= y_step < 8) or board[x_step][y_step] == -1:
                            valid = False
                            break
                    if valid and board[new_i][new_j] in (0, -1):
                        possible_moves.append(f"{i},{j}:{new_i},{new_j}")

            # Check diagonal2 (i + j constant)
            diagonal2 = []
            x, y = i, j
            while x >= 0 and y < 8:
                diagonal2.append((x, y))
                x -= 1
                y += 1
            x, y = i + 1, j - 1
            while x < 8 and y >= 0:
                diagonal2.append((x, y))
                x += 1
                y -= 1
            k_diag2 = sum(board[x][y] != 0 for (x, y) in diagonal2)
            if k_diag2 > 0:
                # Direction (1, -1)
                new_i = i + k_diag2
                new_j = j - k_diag2
                if 0 <= new_i < 8 and 0 <= new_j < 8:
                    valid = True
                    for t in range(1, k_diag2):
                        x_step = i + t
                        y_step = j - t
                        if not (0 <= x_step < 8 and 0 <= y_step < 8) or board[x_step][y_step] == -1:
                            valid = False
                            break
                    if valid and board[new_i][new_j] in (0, -1):
                        possible_moves.append(f"{i},{j}:{new_i},{new_j}")
                # Direction (-1, 1)
                new_i = i - k_diag2
                new_j = j + k_diag2
                if 0 <= new_i < 8 and 0 <= new_j < 8:
                    valid = True
                    for t in range(1, k_diag2):
                        x_step = i - t
                        y_step = j + t
                        if not (0 <= x_step < 8 and 0 <= y_step < 8) or board[x_step][y_step] == -1:
                            valid = False
                            break
                    if valid and board[new_i][new_j] in (0, -1):
                        possible_moves.append(f"{i},{j}:{new_i},{new_j}")

    # Remove duplicate moves
    possible_moves = list(set(possible_moves))

    if not possible_moves:
        return ""

    # Evaluate and select the best move
    best_score = -float('inf')
    best_move = possible_moves[0]

    for move in possible_moves:
        from_str, to_str = move.split(':')
        from_i, from_j = map(int, from_str.split(','))
        to_i, to_j = map(int, to_str.split(','))

        score = 0
        if board[to_i][to_j] == -1:
            score += 100  # Prioritize captures

        # Proximity to center (3.5, 3.5)
        dist = (to_i - 3.5) ** 2 + (to_j - 3.5) ** 2
        score += 10 / (dist + 1e-5)

        # Prefer moves that start/end in the upper half (to climb faster)
        if from_i < 4:
            score += 5
        if to_i > 4:
            score += 5

        if (score > best_score) or (score == best_score and move < best_move):
            best_score = score
            best_move = move

    return best_move
