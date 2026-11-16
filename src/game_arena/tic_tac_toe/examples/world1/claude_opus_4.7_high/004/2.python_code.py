
def policy(board):
    b = [row[:] for row in board]
    
    def check(b):
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
        w = check(b)
        if w != 0:
            return w * player * 10, None  # relative to player
        m = moves(b)
        if not m:
            return 0, None
        best_score = -999
        best_move = m[0]
        for (r, c) in m:
            b[r][c] = player
            score, _ = minimax(b, -player, -beta, -alpha)
            score = -score
            b[r][c] = 0
            # prefer quicker wins / slower losses
            if score > 0:
                score -= 1
            elif score < 0:
                score += 1
            if score > best_score:
                best_score = score
                best_move = (r, c)
            if best_score > alpha:
                alpha = best_score
            if alpha >= beta:
                break
        return best_score, best_move
    
    # count moves to ensure it's our turn; just play
    _, move = minimax(b, 1, -999, 999)
    if move is None or b[move[0]][move[1]] != 0:
        for r in range(3):
            for c in range(3):
                if b[r][c] == 0:
                    return (r, c)
    return move
