
import numpy as np

def get_queen_moves(board, r, c):
    moves = []
    directions = [ (-1, 0), (1, 0), (0, -1), (0, 1),
                   (-1, -1), (-1, 1), (1, -1), (1, 1) ]
    for (dx, dy) in directions:
        i = 1
        while True:
            nr = r + dx * i
            nc = c + dy * i
            if not (0 <= nr < 6 and 0 <= nc < 6):
                break
            if board[nr][nc] != 0:
                break
            path_clear = True
            for s in range(1, i):
                pr = r + dx * s
                pc = c + dy * s
                if not (0 <= pr < 6 and 0 <= pc < 6) or board[pr][pc] != 0:
                    path_clear = False
                    break
            if valid and board[nr][nc] == 0:
                moves.append( (nr, nc) )
            else:
                break
            valid = True
            i += 1
    return moves

def policy(board):
    candidates = []
    for i in range(6):
        for j in range(6):
            if board[i][j] == 1:
                moves = get_queen_moves(board, i, j)
                for (nr, nc) in moves:
                    temp_board = np.copy(board)
                    temp_board[i][j] = 0
                    temp_board[nr][nc] = 1
                    arrow_moves = get_queen_moves(temp_board, nr, nc)
                    for ar_r, ar_c in arrow_moves:
                        candidates.append( (i, j, nr, nc, ar_r, ar_c) )
    if not candidates:
        return "0,0:0,0:3,3"
    best = None
    min_center = float('inf')
    center_x, center_y = 2.5, 2.5
    for candidate in candidates:
        ar_r, ar_c = candidate[4], candidate[5]
        current_dist = abs(ar_r - center_x) + abs(ar_c - center_y)
        if current_dist < min_center:
            min_center = current_dist
            best = candidate
    from_r, from_c, to_r, to_c, ar_r, ar_c = best
    return f"{from_r},{from_c}:{to_r},{to_c}:{ar_r},{ar_c}"
