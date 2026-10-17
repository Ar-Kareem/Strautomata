
def policy(board):
    def generate_all_legal_moves(board):
        directions = [(0,1),(0,-1),(1,0),(-1,0),(1,1),(-1,-1),(1,-1),(-1,1)]
        moves = []

        def get_diagonal_1(r, c):
            diag = []
            cr, cc = r, c
            while cr > 0 and cc > 0:
                cr -= 1
                cc -= 1
            while cr <= 7 and cc <= 7:
                diag.append((cr, cc))
                cr += 1
                cc += 1
            return diag

        def get_diagonal_2(r, c):
            diag = []
            cr, cc = r, c
            while cr > 0 and cc < 7:
                cr -= 1
                cc += 1
            while cr <= 7 and cc >= 0:
                diag.append((cr, cc))
                cr += 1
                cc -= 1
            return diag

        for r in range(8):
            for c in range(8):
                if board[r][c] != 1:
                    continue
                for dr, dc in directions:
                    if dr == 0:  # Horizontal
                        line = [(r, col) for col in range(8)]
                        line_count = sum(1 for _, col in line if board[r][col] != 0)
                    elif dc == 0:  # Vertical
                        line = [(row, c) for row in range(8)]
                        line_count = sum(1 for row, _ in line if board[row][c] != 0)
                    elif dr == dc:  # Diagonal 1
                        line = get_diagonal_1(r, c)
                        line_count = sum(1 for rec_r, rec_c in line if board[rec_r][rec_c] != 0)
                    else:  # Diagonal 2
                        line = get_diagonal_2(r, c)
                        line_count = sum(1 for rec_r, rec_c in line if board[rec_r][rec_c] != 0)
                    k = line_count
                    tr = r + dr * k
                    tc = c + dc * k
                    if not (0 <= tr < 8 and 0 <= tc < 8):
                        continue
                    path_clear = True
                    for i in range(1, k):
                        nr = r + dr * i
                        nc = c + dc * i
                        if not (0 <= nr < 8 and 0 <= nc < 8):
                            path_clear = False
                            break
                        if board[nr][nc] == -1:
                            path_clear = False
                            break
                    if not path_clear:
                        continue
                    if board[tr][tc] == 1:
                        continue
                    moves.append((r, c, tr, tc))
        return moves

    def count_components(board, player):
        visited = [[False]*8 for _ in range(8)]
        components = 0
        for r in range(8):
            for c in range(8):
                if board[r][c] == player and not visited[r][c]:
                    components += 1
                    queue = [(r, c)]
                    visited[r][c] = True
                    while queue:
                        cr, cc = queue.pop(0)
                        for dr in (-1, 0, 1):
                            for dc in (-1, 0, 1):
                                if dr == 0 and dc == 0:
                                    continue
                                nr, nc = cr + dr, cc + dc
                                if 0 <= nr < 8 and 0 <= nc < 8:
                                    if not visited[nr][nc] and board[nr][nc] == player:
                                        visited[nr][nc] = True
                                        queue.append((nr, nc))
        return components

    def select_best_move(board, legal_moves):
        captures = []
        non_captures = []
        for r, c, tr, tc in legal_moves:
            if board[tr][tc] == -1:
                captures.append((r, c, tr, tc))
            else:
                non_captures.append((r, c, tr, tc))
        if captures:
            evals = []
            for r, c, tr, tc in captures:
                new_board = [row[:] for row in board]
                new_board[r][c] = 0
                new_board[tr][tc] = 1
                player_comp = count_components(new_board, 1)
                opponent_comp = count_components(new_board, -1)
                evals.append((player_comp - opponent_comp, r, c, tr, tc))
            evals.sort()
            _, best_r, best_c, best_tr, best_tc = evals[0]
            return f"{best_r},{best_c}:{best_tr},{best_tc}"
        else:
            evals = []
            for r, c, tr, tc in non_captures:
                new_board = [row[:] for row in board]
                new_board[r][c] = 0
                new_board[tr][tc] = 1
                player_comp = count_components(new_board, 1)
                opponent_comp = count_components(new_board, -1)
                evals.append((player_comp - opponent_comp, r, c, tr, tc))
            evals.sort()
            _, best_r, best_c, best_tr, best_tc = evals[0]
            return f"{best_r},{best_c}:{best_tr},{best_tc}"

    legal_moves = generate_all_legal_moves(board)
    return select_best_move(board, legal_moves)
