
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
            return w * 10, None
        mv = moves(b)
        if not mv:
            return 0, None
        best_move = mv[0]
        if player == 1:
            best = -100
            for (r, c) in mv:
                b[r][c] = 1
                score, _ = minimax(b, -1, alpha, beta)
                b[r][c] = 0
                # prefer faster wins / slower losses
                score -= (1 if score > 0 else -1 if score < 0 else 0)
                if score > best:
                    best = score
                    best_move = (r, c)
                alpha = max(alpha, best)
                if beta <= alpha:
                    break
            return best, best_move
        else:
            best = 100
            for (r, c) in mv:
                b[r][c] = -1
                score, _ = minimax(b, 1, alpha, beta)
                b[r][c] = 0
                score -= (1 if score > 0 else -1 if score < 0 else 0)
                if score < best:
                    best = score
                    best_move = (r, c)
                beta = min(beta, best)
                if beta <= alpha:
                    break
            return best, best_move
    
    _, move = minimax(b, 1, -1000, 1000)
    if move is None:
        for r in range(3):
            for c in range(3):
                if b[r][c] == 0:
                    return (r, c)
    return move
