
def policy(board):
    import copy

    def get_legal_moves(board):
        moves = []
        for r in range(8):
            for c in range(8):
                if board[r][c] == 1:
                    # Check row moves
                    k_row = sum(1 for cell in board[r] if cell != 0)
                    # East
                    new_c = c + k_row
                    if 0 <= new_c < 8:
                        valid = True
                        for step in range(1, k_row):
                            if c + step >= 8 or board[r][c + step] == -1:
                                valid = False
                                break
                        if valid:
                            moves.append((r, c, r, new_c))
                    # West
                    new_c = c - k_row
                    if 0 <= new_c < 8:
                        valid = True
                        for step in range(1, k_row):
                            if c - step < 0 or board[r][c - step] == -1:
                                valid = False
                                break
                        if valid:
                            moves.append((r, c, r, new_c))
                    
                    # Check column moves
                    k_col = sum(1 for i in range(8) if board[i][c] != 0)
                    # South
                    new_r = r + k_col
                    if 0 <= new_r < 8:
                        valid = True
                        for step in range(1, k_col):
                            if r + step >= 8 or board[r + step][c] == -1:
                                valid = False
                                break
                        if valid:
                            moves.append((r, c, new_r, c))
                    # North
                    new_r = r - k_col
                    if 0 <= new_r < 8:
                        valid = True
                        for step in range(1, k_col):
                            if r - step < 0 or board[r - step][c] == -1:
                                valid = False
                                break
                        if valid:
                            moves.append((r, c, new_r, c))
                    
                    # Check diagonal (r - c)
                    k_diag = sum(1 for i in range(8) for j in range(8) if i - j == r - c and board[i][j] != 0)
                    # Northeast
                    new_r = r + k_diag
                    new_c = c + k_diag
                    if 0 <= new_r < 8 and 0 <= new_c < 8:
                        valid = True
                        for step in range(1, k_diag):
                            nr, nc = r + step, c + step
                            if nr >= 8 or nc >= 8 or board[nr][nc] == -1:
                                valid = False
                                break
                        if valid:
                            moves.append((r, c, new_r, new_c))
                    # Southwest
                    new_r = r - k_diag
                    new_c = c - k_diag
                    if 0 <= new_r < 8 and 0 <= new_c < 8:
                        valid = True
                        for step in range(1, k_diag):
                            nr, nc = r - step, c - step
                            if nr < 0 or nc < 0 or board[nr][nc] == -1:
                                valid = False
                                break
                        if valid:
                            moves.append((r, c, new_r, new_c))
                    
                    # Check anti-diagonal (r + c)
                    k_antidiag = sum(1 for i in range(8) for j in range(8) if i + j == r + c and board[i][j] != 0)
                    # Northwest
                    new_r = r - k_antidiag
                    new_c = c + k_antidiag
                    if 0 <= new_r < 8 and 0 <= new_c < 8:
                        valid = True
                        for step in range(1, k_antidiag):
                            nr, nc = r - step, c + step
                            if nr < 0 or nc >= 8 or board[nr][nc] == -1:
                                valid = False
                                break
                        if valid:
                            moves.append((r, c, new_r, new_c))
                    # Southeast
                    new_r = r + k_antidiag
                    new_c = c - k_antidiag
                    if 0 <= new_r < 8 and 0 <= new_c < 8:
                        valid = True
                        for step in range(1, k_antidiag):
                            nr, nc = r + step, c - step
                            if nr >= 8 or nc < 0 or board[nr][nc] == -1:
                                valid = False
                                break
                        if valid:
                            moves.append((r, c, new_r, new_c))
        return [f"{fr},{fc}:{tr},{tc}" for fr, fc, tr, tc in moves]

    def evaluate(new_board):
        my_pieces = [(r, c) for r in range(8) for c in range(8) if new_board[r][c] == 1]
        if not my_pieces:
            return -float('inf')
        
        # Chebyshev distance sum
        sum_dist = 0
        for i in range(len(my_pieces)):
            for j in range(i + 1, len(my_pieces)):
                r1, c1 = my_pieces[i]
                r2, c2 = my_pieces[j]
                sum_dist += max(abs(r1 - r2), abs(c1 - c2))
        
        # Connected components via BFS
        visited = set()
        components = 0
        for piece in my_pieces:
            if piece not in visited:
                components += 1
                queue = [piece]
                visited.add(piece)
                while queue:
                    r, c = queue.pop(0)
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = r + dr, c + dc
                            if (nr, nc) in visited or not (0 <= nr < 8 and 0 <= nc < 8):
                                continue
                            if new_board[nr][nc] == 1:
                                visited.add((nr, nc))
                                queue.append((nr, nc))
        
        enemy_count = sum(row.count(-1) for row in new_board)
        return -components * 100 - sum_dist - enemy_count * 10

    legal_moves = get_legal_moves(board)
    if not legal_moves:
        return "0,0:0,0"
    
    best_score = -float('inf')
    best_move = legal_moves[0]
    
    for move in legal_moves:
        fr, fc = map(int, move.split(':')[0].split(','))
        tr, tc = map(int, move.split(':')[1].split(','))
        new_board = [list(row) for row in board]
        new_board[fr][fc] = 0
        new_board[tr][tc] = 1
        current_score = evaluate(new_board)
        if current_score > best_score:
            best_score = current_score
            best_move = move
    
    return best_move
