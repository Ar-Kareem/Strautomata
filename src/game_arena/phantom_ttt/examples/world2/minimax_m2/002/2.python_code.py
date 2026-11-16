
def policy(board: list[list[int]]) -> tuple[int, int]:
    win_lines = [
        [(0,0), (0,1), (0,2)],
        [(1,0), (1,1), (1,2)],
        [(2,0), (2,1), (2,2)],
        [(0,0), (1,0), (2,0)],
        [(0,1), (1,1), (2,1)],
        [(0,2), (1,2), (2,2)],
        [(0,0), (1,1), (2,2)],
        [(0,2), (1,1), (2,0)]
    ]
    
    L_map = {
        (1,1): 4,
        (0,0): 3, (0,2): 3, (2,0): 3, (2,2): 3,
        (0,1): 2, (1,0): 2, (1,2): 2, (2,1): 2
    }
    
    winning_moves = []
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                count_1s = 0
                for line in win_lines:
                    if (i, j) in line:
                        for (x, y) in line:
                            if (x, y) != (i, j) and board[x][y] == 1:
                                count_1s += 1
                if count_1s == 2:
                    winning_moves.append((i, j))
    
    if winning_moves:
        best_move = winning_moves[0]
        max_L = 0
        for move in winning_moves:
            L = L_map.get(move, 0)
            if L > max_L:
                max_L = L
                best_move = move
        return best_move
    
    best_score = -1
    best_move = (0, 0)
    best_L = 0
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                W = 0
                for line in win_lines:
                    if (i, j) in line:
                        count_1s = 0
                        for (x, y) in line:
                            if (x, y) != (i, j) and board[x][y] == 1:
                                count_1s += 1
                        if count_1s == 1:
                            W += 1
                L = L_map.get((i, j), 0)
                score = W * 10 + L
                if score > best_score:
                    best_score = score
                    best_move = (i, j)
                    best_L = L
                elif score == best_score and L > best_L:
                    best_move = (i, j)
                    best_L = L
    return best_move
