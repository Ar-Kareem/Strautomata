
def policy(board: list[list[int]]) -> tuple[int, int]:
    b = [row[:] for row in board]

    def check_winner(bd):
        lines = []
        for i in range(3):
            lines.append(bd[i])
            lines.append([bd[0][i], bd[1][i], bd[2][i]])
        lines.append([bd[0][0], bd[1][1], bd[2][2]])
        lines.append([bd[0][2], bd[1][1], bd[2][0]])
        for ln in lines:
            if ln[0] != 0 and ln[0] == ln[1] == ln[2]:
                return ln[0]
        return 0

    def is_full(bd):
        return all(bd[i][j] != 0 for i in range(3) for j in range(3))

    def minimax(bd, player, alpha, beta):
        w = check_winner(bd)
        if w != 0:
            return w * 10, None
        if is_full(bd):
            return 0, None
        best_move = None
        if player == 1:
            best = -100
            for i in range(3):
                for j in range(3):
                    if bd[i][j] == 0:
                        bd[i][j] = 1
                        score, _ = minimax(bd, -1, alpha, beta)
                        bd[i][j] = 0
                        # Prefer faster wins / slower losses
                        if score > 0:
                            score -= 1
                        elif score < 0:
                            score += 1
                        if score > best:
                            best = score
                            best_move = (i, j)
                        alpha = max(alpha, best)
                        if beta <= alpha:
                            return best, best_move
            return best, best_move
        else:
            best = 100
            for i in range(3):
                for j in range(3):
                    if bd[i][j] == 0:
                        bd[i][j] = -1
                        score, _ = minimax(bd, 1, alpha, beta)
                        bd[i][j] = 0
                        if score > 0:
                            score -= 1
                        elif score < 0:
                            score += 1
                        if score < best:
                            best = score
                            best_move = (i, j)
                        beta = min(beta, best)
                        if beta <= alpha:
                            return best, best_move
            return best, best_move

    # Count moves to know if first move
    my_count = sum(1 for i in range(3) for j in range(3) if b[i][j] == 1)
    opp_count = sum(1 for i in range(3) for j in range(3) if b[i][j] == -1)

    # First move: take center for speed
    if my_count == 0 and opp_count == 0:
        return (1, 1)
    if my_count == 0 and opp_count == 1:
        if b[1][1] == 0:
            return (1, 1)
        else:
            return (0, 0)

    _, move = minimax(b, 1, -100, 100)
    if move is None:
        for i in range(3):
            for j in range(3):
                if b[i][j] == 0:
                    return (i, j)
    return move
