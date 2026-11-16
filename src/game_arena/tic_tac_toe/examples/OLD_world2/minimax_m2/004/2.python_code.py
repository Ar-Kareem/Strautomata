
def policy(board):
    lines = [
        [(i, j) for j in range(4)] for i in range(4)
    ] + [
        [(i, j) for i in range(4)] for j in range(4)
    ] + [
        [(i, i) for i in range(4)],
        [(i, 3-i) for i in range(4)]
    ]
    
    empty_cells = []
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                empty_cells.append((i, j))
                
    if not empty_cells:
        return (0, 0)
        
    def check_win(player):
        for line in lines:
            count = 0
            for (i, j) in line:
                if board[i][j] == player:
                    count += 1
            if count == 4:
                return True
        return False
        
    for (i, j) in empty_cells:
        board[i][j] = 1
        if check_win(1):
            board[i][j] = 0
            return (i, j)
        board[i][j] = 0
        
    for (i, j) in empty_cells:
        board[i][j] = -1
        if check_win(-1):
            board[i][j] = 0
            return (i, j)
        board[i][j] = 0
        
    def evaluate():
        score = 0
        for line in lines:
            count_1 = 0
            count_minus1 = 0
            for (i, j) in line:
                if board[i][j] == 1:
                    count_1 += 1
                elif board[i][j] == -1:
                    count_minus1 += 1
            score += count_1 * 10
            score -= count_minus1 * 10
        return score
        
    best_move = None
    best_score = -10**9
    
    for (i, j) in empty_cells:
        board[i][j] = 1
        new_empty = []
        for x in range(4):
            for y in range(4):
                if board[x][y] == 0:
                    new_empty.append((x, y))
        min_score = 10**9
        
        for (k, l) in new_empty:
            board[k][l] = -1
            if check_win(-1):
                score = -1000
            else:
                score = evaluate()
            board[k][l] = 0
            if score < min_score:
                min_score = score
        board[i][j] = 0
        if min_score > best_score:
            best_score = min_score
            best_move = (i, j)
            
    return best_move
