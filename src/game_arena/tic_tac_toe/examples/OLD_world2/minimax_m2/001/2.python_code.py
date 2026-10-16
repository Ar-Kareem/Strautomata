
def policy(board: list[list[int]]) -> tuple[int, int]:
    if len(board) != 4 or any(len(row) != 4 for row in board):
        raise ValueError("Board must be 4x4")
    
    centers = {(1,1), (1,2), (2,1), (2,2)}
    corners = {(0,0), (0,3), (3,0), (3,3)}
    
    def check_win(board, player):
        for i in range(4):
            for j in range(4):
                if board[i][j] == player:
                    if j + 3 < 4:
                        if all(board[i][j + k] == player for k in range(4)):
                            return True
                    if i + 3 < 4:
                        if all(board[i + k][j] == player for k in range(4)):
                            return True
                    if i + 3 < 4 and j + 3 < 4:
                        if all(board[i + k][j + k] == player for k in range(4)):
                            return True
                    if i + 3 < 4 and j - 3 >= 0:
                        if all(board[i + k][j - k] == player for k in range(4)):
                            return True
        return False
    
    def break_tie(candidates):
        def get_priority(cell):
            if cell in centers:
                return 0
            elif cell in corners:
                return 1
            else:
                return 2
        candidates.sort(key=lambda x: (get_priority(x), x[0], x[1]))
        return candidates[0]
    
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                board[i][j] = 1
                if check_win(board, 1):
                    board[i][j] = 0
                    return (i, j)
                board[i][j] = 0
                
    block_candidates = []
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                board[i][j] = -1
                if check_win(board, -1):
                    block_candidates.append((i, j))
                board[i][j] = 0
                
    if block_candidates:
        return break_tie(block_candidates)
    
    total_score = {}
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                score = 0
                row_our = 0
                row_opp = 0
                for k in range(4):
                    if board[i][k] == 1:
                        row_our += 1
                    elif board[i][k] == -1:
                        row_opp += 1
                if row_opp == 0:
                    score += row_our
                
                col_our = 0
                col_opp = 0
                for k in range(4):
                    if board[k][j] == 1:
                        col_our += 1
                    elif board[k][j] == -1:
                        col_opp += 1
                if col_opp == 0:
                    score += col_our
                
                if i == j:
                    diag_our = 0
                    diag_opp = 0
                    for k in range(4):
                        if board[k][k] == 1:
                            diag_our += 1
                        elif board[k][k] == -1:
                            diag_opp += 1
                    if diag_opp == 0:
                        score += diag_our
                
                if i + j == 3:
                    anti_our = 0
                    anti_opp = 0
                    for k in range(4):
                        if board[k][3 - k] == 1:
                            anti_our += 1
                        elif board[k][3 - k] == -1:
                            anti_opp += 1
                    if anti_opp == 0:
                        score += anti_our
                
                total_score[(i, j)] = score
    
    if not total_score:
        return (0, 0)
        
    max_score = max(total_score.values())
    candidates = [(i, j) for (i, j), score in total_score.items() if score == max_score]
    return break_tie(candidates)
