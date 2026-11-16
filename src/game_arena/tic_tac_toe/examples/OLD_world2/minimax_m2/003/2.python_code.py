
def policy(board: list[list[int]]) -> tuple[int, int]:
    moves = []
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                moves.append((i, j))
    
    def winner(b):
        for i in range(4):
            row = b[i]
            if row[0] != 0 and all(cell == row[0] for cell in row):
                return row[0]
        for j in range(4):
            col = [b[i][j] for i in range(4)]
            if col[0] != 0 and all(cell == col[0] for cell in col):
                return col[0]
        diag1 = [b[i][i] for i in range(4)]
        if diag1[0] != 0 and all(cell == diag1[0] for cell in diag1):
            return diag1[0]
        diag2 = [b[i][3-i] for i in range(4)]
        if diag2[0] != 0 and all(cell == diag2[0] for cell in diag2):
            return diag2[0]
        return 0
    
    def is_full(b):
        for i in range(4):
            for j in range(4):
                if b[i][j] == 0:
                    return False
        return True
    
    def heuristic(b):
        lines = []
        for i in range(4):
            lines.append([(i, j) for j in range(4)])
        for j in range(4):
            lines.append([(i, j) for i in range(4)])
        lines.append([(i, i) for i in range(4)])
        lines.append([(i, 3-i) for i in range(4)])
        score = 0
        for line in lines:
            ai_count = sum(1 for (i, j) in line if b[i][j] == 1)
            opp_count = sum(1 for (i, j) in line if b[i][j] == -1)
            if ai_count > 0 and opp_count == 0:
                score += ai_count ** 2
            elif opp_count > 0 and ai_count == 0:
                score -= opp_count ** 2
        return score
    
    def minimax(b, current_player, depth, max_depth, alpha, beta):
        win = winner(b)
        if win != 0:
            return 10 if win == 1 else -10
        if is_full(b):
            return 0
        if depth == max_depth:
            return heuristic(b)
        
        if current_player == 1:
            best = -10
            for i in range(4):
                for j in range(4):
                    if b[i][j] == 0:
                        b[i][j] = 1
                        score = minimax(b, -1, depth+1, max_depth, alpha, beta)
                        b[i][j] = 0
                        best = max(best, score)
                        alpha = max(alpha, score)
                        if beta <= alpha:
                            break
                if beta <= alpha:
                    break
            return best
        else:
            best = 10
            for i in range(4):
                for j in range(4):
                    if b[i][j] == 0:
                        b[i][j] = -1
                        score = minimax(b, 1, depth+1, max_depth, alpha, beta)
                        b[i][j] = 0
                        best = min(best, score)
                        beta = min(beta, score)
                        if beta <= alpha:
                            break
                if beta <= alpha:
                    break
            return best
    
    for i, j in moves:
        board[i][j] = 1
        if winner(board) == 1:
            board[i][j] = 0
            return (i, j)
        board[i][j] = 0
    
    best_move = None
    best_score = -10
    for i, j in moves:
        board[i][j] = 1
        score = minimax(board, -1, 1, 3, -10, 10)
        board[i][j] = 0
        if score > best_score:
            best_score = score
            best_move = (i, j)
    return best_move
