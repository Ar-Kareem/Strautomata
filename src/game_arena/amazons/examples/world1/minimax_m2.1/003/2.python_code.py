
import numpy as np

DIRECTIONS = [(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (-1,1), (1,-1), (1,1)]

def arrow_shot_counts(board, r, c, new_r, new_c):
    count = 0
    for dr, dc in DIRECTIONS:
        step = 1
        while True:
            ar = new_r + step * dr
            ac = new_c + step * dc
            if ar < 0 or ar >= 6 or ac < 0 or ac >= 6:
                break
            if ar == r and ac == c:
                count += 1
            elif board[ar][ac] == 0:
                count += 1
            else:
                break
            step += 1
    return count

def count_opponent_moves(board):
    total = 0
    for i in range(6):
        for j in range(6):
            if board[i][j] == 2:
                for dr, dc in DIRECTIONS:
                    step = 1
                    while True:
                        nr = i + step * dr
                        nc = j + step * dc
                        if nr < 0 or nr >= 6 or nc < 0 or nc >= 6:
                            break
                        if board[nr][nc] != 0:
                            break
                        arrow_count = arrow_shot_counts(board, i, j, nr, nc)
                        total += arrow_count
                        step += 1
    return total

def policy(board):
    our_amazons = []
    for i in range(6):
        for j in range(6):
            if board[i][j] == 1:
                our_amazons.append((i, j))
    
    moves = []
    
    for r, c in our_amazons:
        for dr, dc in DIRECTIONS:
            step = 1
            while True:
                nr = r + step * dr
                nc = c + step * dc
                if nr < 0 or nr >= 6 or nc < 0 or nc >= 6:
                    break
                if board[nr][nc] != 0:
                    break
                board_after = board.copy()
                board_after[r][c] = 0
                board_after[nr][nc] = 1
                for dr2, dc2 in DIRECTIONS:
                    step2 = 1
                    while True:
                        ar = nr + step2 * dr2
                        ac = nc + step2 * dc2
                        if ar < 0 or ar >= 6 or ac < 0 or ac >= 6:
                            break
                        if board_after[ar][ac] != 0:
                            break
                        board_after_arrow = board_after.copy()
                        board_after_arrow[ar][ac] = -1
                        opp_mobility = count_opponent_moves(board_after_arrow)
                        moves.append((r, c, nr, nc, ar, ac, opp_mobility))
                        step2 += 1
                step += 1
                
    if not moves:
        return ""
    best_move = min(moves, key=lambda x: x[6])
    r, c, nr, nc, ar, ac, _ = best_move
    return f"{r},{c}:{nr},{nc}:{ar},{ac}"
