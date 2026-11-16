
import numpy as np

def policy(board) -> str:
    directions = [(1, 0), (0, 1), (-1, 0), (0, -1), 
                  (1, 1), (-1, 1), (1, -1), (-1, -1)]
    my_amazons = np.argwhere(board == 1)
    moves = []
    scores = []
    
    for (fx, fy) in my_amazons:
        for dx, dy in directions:
            step = 1
            while True:
                tx = fx + dx * step
                ty = fy + dy * step
                if not (0 <= tx < 6 and 0 <= ty < 6) or board[tx, ty] != 0:
                    break
                
                # Explore arrow shots from (tx, ty)
                for adx, ady in directions:
                    a_step = 1
                    while True:
                        ax = tx + adx * a_step
                        ay = ty + ady * a_step
                        if not (0 <= ax < 6 and 0 <= ay < 6):
                            break
                        
                        if (ax == fx and ay == fy) or board[ax, ay] == 0:
                            path_valid = True
                            for i in range(1, a_step):
                                cx = tx + adx * i
                                cy = ty + ady * i
                                if not (cx == fx and cy == fy):
                                    if board[cx, cy] != 0:
                                        path_valid = False
                                        break
                            if path_valid:
                                move_str = f"{fx},{fy}:{tx},{ty}:{ax},{ay}"
                                enemy_amazons = np.argwhere(board == 2)
                                score = 0.0
                                for (ex, ey) in enemy_amazons:
                                    dist_sq = (ax - ex)**2 + (ay - ey)**2
                                    score += 1.0 / (1 + dist_sq)
                                moves.append(move_str)
                                scores.append(score)
                        a_step += 1
                step += 1
    
    if moves:
        best_idx = np.argmax(scores)
        return moves[best_idx]
    
    # Fallback if no moves found (should not occur with valid board)
    return "0,0:0,1:0,2"  # Dummy move, but valid move guaranteed
