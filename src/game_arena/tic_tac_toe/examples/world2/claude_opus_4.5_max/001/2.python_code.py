
def policy(board: list[list[int]]) -> tuple[int, int]:
    
    def get_empty(b):
        return [(i, j) for i in range(4) for j in range(4) if b[i][j] == 0]
    
    def check_winner(b):
        for i in range(4):
            if b[i][0] and b[i][0] == b[i][1] == b[i][2] == b[i][3]:
                return b[i][0]
            if b[0][i] and b[0][i] == b[1][i] == b[2][i] == b[3][i]:
                return b[0][i]
        if b[0][0] and b[0][0] == b[1][1] == b[2][2] == b[3][3]:
            return b[0][0]
        if b[0][3] and b[0][3] == b[1][2] == b[2][1] == b[3][0]:
            return b[0][3]
        return 0
    
    def evaluate(b):
        score = 0
        weights = [0, 1, 10, 100, 1000]
        lines = []
        for i in range(4):
            lines.append([b[i][j] for j in range(4)])
            lines.append([b[j][i] for j in range(4)])
        lines.append([b[i][i] for i in range(4)])
        lines.append([b[i][3-i] for i in range(4)])
        for line in lines:
            me = line.count(1)
            opp = line.count(-1)
            if opp == 0:
                score += weights[me]
            if me == 0:
                score -= weights[opp]
        return score
    
    def minimax(b, depth, maximizing, alpha, beta):
        winner = check_winner(b)
        if winner == 1:
            return 10000 + depth
        if winner == -1:
            return -10000 - depth
        empty = get_empty(b)
        if not empty or depth == 0:
            return evaluate(b)
        if maximizing:
            value = float('-inf')
            for r, c in empty:
                b[r][c] = 1
                value = max(value, minimax(b, depth - 1, False, alpha, beta))
                b[r][c] = 0
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value
        else:
            value = float('inf')
            for r, c in empty:
                b[r][c] = -1
                value = min(value, minimax(b, depth - 1, True, alpha, beta))
                b[r][c] = 0
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return value
    
    empty = get_empty(board)
    if not empty:
        return (0, 0)
    
    if len(empty) == 16:
        return (1, 1)
    
    for r, c in empty:
        board[r][c] = 1
        if check_winner(board) == 1:
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0
    
    for r, c in empty:
        board[r][c] = -1
        if check_winner(board) == -1:
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0
    
    n = len(empty)
    if n <= 6:
        depth = 12
    elif n <= 8:
        depth = 10
    elif n <= 10:
        depth = 8
    elif n <= 12:
        depth = 6
    else:
        depth = 5
    
    best_move = empty[0]
    best_score = float('-inf')
    alpha = float('-inf')
    
    for r, c in empty:
        board[r][c] = 1
        score = minimax(board, depth, False, alpha, float('inf'))
        board[r][c] = 0
        if score > best_score:
            best_score = score
            best_move = (r, c)
        alpha = max(alpha, score)
    
    return best_move
