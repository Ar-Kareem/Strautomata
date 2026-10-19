
def policy(board):
    lines = []
    for i in range(4):
        lines.append([(i, j) for j in range(4)])
    for j in range(4):
        lines.append([(i, j) for i in range(4)])
    lines.append([(i, i) for i in range(4)])
    lines.append([(i, 3 - i) for i in range(4)])
    
    for line in lines:
        ones = 0
        empty_cell = None
        for (i, j) in line:
            if board[i][j] == 1:
                ones += 1
            elif board[i][j] == 0:
                empty_cell = (i, j)
        if ones == 3 and empty_cell is not None:
            return empty_cell
    
    for line in lines:
        opps = 0
        empty_cell = None
        for (i, j) in line:
            if board[i][j] == -1:
                opps += 1
            elif board[i][j] == 0:
                empty_cell = (i, j)
        if opps == 3 and empty_cell is not None:
            return empty_cell
    
    empty_cells = [(i, j) for i in range(4) for j in range(4) if board[i][j] == 0]
    moves_scores = []
    for (i, j) in empty_cells:
        score = 0
        for line in lines:
            if (i, j) not in line:
                continue
            count_ours = 0
            count_opp = 0
            for (x, y) in line:
                if (x, y) == (i, j):
                    continue
                if board[x][y] == 1:
                    count_ours += 1
                elif board[x][y] == -1:
                    count_opp += 1
            if count_opp >= 2:
                score += 100
            if count_ours >= 2:
                score += 20
            if count_ours == 1:
                score += 5
            if count_opp == 1:
                score += 3
            if count_ours == 0 and count_opp == 0:
                score += 1
        if (i, j) in [(1, 1), (1, 2), (2, 1), (2, 2)]:
            score += 10
        elif (i, j) in [(0, 0), (0, 3), (3, 0), (3, 3)]:
            score += 5
        moves_scores.append((score, (i, j)))
    
    moves_scores.sort(key=lambda x: x[0], reverse=True)
    return moves_scores[0][1]
