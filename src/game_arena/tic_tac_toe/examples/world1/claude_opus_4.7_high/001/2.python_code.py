
def policy(board):
    b = [row[:] for row in board]

    def winner(b):
        lines = []
        for i in range(3):
            lines.append(b[i])
            lines.append([b[0][i], b[1][i], b[2][i]])
        lines.append([b[0][0], b[1][1], b[2][2]])
        lines.append([b[0][2], b[1][1], b[2][0]])
        for ln in lines:
            if ln[0] != 0 and ln[0] == ln[1] == ln[2]:
                return ln[0]
        return 0

    def is_full(b):
        return all(b[i][j] != 0 for i in range(3) for j in range(3))

    def minimax(b, player):
        w = winner(b)
        if w != 0:
            return (w * 10, None)  # player-independent: 1 wins => +10
        if is_full(b):
            return (0, None)
        best_move = None
        if player == 1:
            best = -999
            for i in range(3):
                for j in range(3):
                    if b[i][j] == 0:
                        b[i][j] = 1
                        v, _ = minimax(b, -1)
                        b[i][j] = 0
                        # prefer faster wins / slower losses
                        v_adj = v - 1 if v > 0 else (v + 1 if v < 0 else 0)
                        if v_adj > best:
                            best = v_adj
                            best_move = (i, j)
            return (best, best_move)
        else:
            best = 999
            for i in range(3):
                for j in range(3):
                    if b[i][j] == 0:
                        b[i][j] = -1
                        v, _ = minimax(b, 1)
                        b[i][j] = 0
                        v_adj = v - 1 if v > 0 else (v + 1 if v < 0 else 0)
                        if v_adj < best:
                            best = v_adj
                            best_move = (i, j)
            return (best, best_move)

    _, move = minimax(b, 1)
    if move is None:
        for i in range(3):
            for j in range(3):
                if b[i][j] == 0:
                    return (i, j)
    return move
