
def policy(board):
    b = [row[:] for row in board]
    
    def winner(b):
        lines = []
        for i in range(3):
            lines.append(b[i])
            lines.append([b[0][i], b[1][i], b[2][i]])
        lines.append([b[0][0], b[1][1], b[2][2]])
        lines.append([b[0][2], b[1][1], b[2][0]])
        for line in lines:
            if line[0] != 0 and line[0] == line[1] == line[2]:
                return line[0]
        return 0
    
    def moves(b):
        return [(r, c) for r in range(3) for c in range(3) if b[r][c] == 0]
    
    def minimax(b, player, alpha, beta):
        w = winner(b)
        if w != 0:
            return w, None
        avail = moves(b)
        if not avail:
            return 0, None
        
        best_move = avail[0]
        if player == 1:
            best = -2
            for m in avail:
                b[m[0]][m[1]] = 1
                val, _ = minimax(b, -1, alpha, beta)
                b[m[0]][m[1]] = 0
                if val > best:
                    best = val
                    best_move = m
                alpha = max(alpha, best)
                if alpha >= beta:
                    break
            return best, best_move
        else:
            best = 2
            for m in avail:
                b[m[0]][m[1]] = -1
                val, _ = minimax(b, 1, alpha, beta)
                b[m[0]][m[1]] = 0
                if val < best:
                    best = val
                    best_move = m
                beta = min(beta, best)
                if alpha >= beta:
                    break
            return best, best_move
    
    _, move = minimax(b, 1, -2, 2)
    if move is None:
        avail = moves(b)
        return avail[0] if avail else (0, 0)
    return move
