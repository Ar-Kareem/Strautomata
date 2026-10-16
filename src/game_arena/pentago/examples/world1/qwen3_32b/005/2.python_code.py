
def policy(you, opponent) -> str:
    def rotate_quadrant(board, quad, direction):
        start_row = (quad // 2) * 3
        start_col = (quad % 2) * 3
        original = [[board[start_row + i][start_col + j] for j in range(3)] for i in range(3)]
        if direction == 'R':
            for i in range(3):
                for j in range(3):
                    board[start_row + i][start_col + j] = original[2 - j][i]
        elif direction == 'L':
            for i in range(3):
                for j in range(3):
                    board[start_row + i][start_col + j] = original[j][2 - i]

    def check_win(board):
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for r in range(6):
            for c in range(6):
                for dr, dc in directions:
                    count = 1
                    nr, nc = r + dr, c + dc
                    while 0 <= nr < 6 and 0 <= nc < 6 and board[nr][nc] == 1:
                        count += 1
                        nr += dr
                        nc += dc
                    nr, nc = r - dr, c - dc
                    while 0 <= nr < 6 and 0 <= nc < 6 and board[nr][nc] == 1:
                        count += 1
                        nr -= dr
                        nc -= dc
                    if count >= 5:
                        return True
        return False

    def simulate_move(you_board, opponent_board, r, c, quad, direction):
        new_you = [row[:] for row in you_board]
        new_opp = [row[:] for row in opponent_board]
        new_you[r][c] = 1
        rotate_quadrant(new_you, quad, direction)
        rotate_quadrant(new_opp, quad, direction)
        return new_you, new_opp

    def max_consecutive(board):
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        max_len = 0
        for r in range(6):
            for c in range(6):
                for dr, dc in directions:
                    current_len = 1
                    nr, nc = r + dr, c + dc
                    while 0 <= nr < 6 and 0 <= nc < 6 and board[nr][nc] == 1:
                        current_len += 1
                        nr += dr
                        nc += dc
                    nr, nc = r - dr, c - dc
                    while 0 <= nr < 6 and 0 <= nc < 6 and board[nr][nc] == 1:
                        current_len += 1
                        nr -= dr
                        nc -= dc
                    if current_len > max_len:
                        max_len = current_len
        return max_len

    def opponent_can_win_after_move(new_you, new_opp):
        for r in range(6):
            for c in range(6):
                if new_you[r][c] == 0 and new_opp[r][c] == 0:
                    for quad in range(4):
                        for direction in ['L', 'R']:
                            temp_you = [row[:] for row in new_you]
                            temp_opp = [row[:] for row in new_opp]
                            temp_opp[r][c] = 1
                            rotate_quadrant(temp_you, quad, direction)
                            rotate_quadrant(temp_opp, quad, direction)
                            if check_win(temp_opp):
                                return True
        return False

    legal_moves = []
    for r in range(6):
        for c in range(6):
            if you[r][c] == 0 and opponent[r][c] == 0:
                for quad in range(4):
                    for direction in ['L', 'R']:
                        legal_moves.append((r, c, quad, direction))

    for move in legal_moves:
        r, c, quad, direction = move
        new_you, new_opp = simulate_move(you, opponent, r, c, quad, direction)
        if check_win(new_you):
            return f"{r+1},{c+1},{quad},{direction}"

    safe_moves = []
    for move in legal_moves:
        r, c, quad, direction = move
        new_you, new_opp = simulate_move(you, opponent, r, c, quad, direction)
        if not opponent_can_win_after_move(new_you, new_opp):
            score = max_consecutive(new_you)
            safe_moves.append((move, score))

    if safe_moves:
        safe_moves.sort(key=lambda x: x[1], reverse=True)
        best_move = safe_moves[0][0]
        r, c, quad, direction = best_move
        return f"{r+1},{c+1},{quad},{direction}"
    else:
        best_score = -1
        best_move = legal_moves[0]
        for move in legal_moves:
            r, c, quad, direction = move
            new_you, _ = simulate_move(you, opponent, r, c, quad, direction)
            score = max_consecutive(new_you)
            if score > best_score:
                best_score = score
                best_move = move
        r, c, quad, direction = best_move
        return f"{r+1},{c+1},{quad},{direction}"
