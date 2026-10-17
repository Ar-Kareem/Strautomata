
import numpy as np

def policy(you, opponent):
    legal_moves = []
    directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    
    for r in range(8):
        for c in range(8):
            if you[r, c] != 0 or opponent[r, c] != 0:
                continue  # Skip occupied cells
            
            total_flips = 0
            valid_move = False
            
            for dx, dy in directions:
                x, y = r + dx, c + dy
                dir_flips = 0
                found_player = False
                
                while 0 <= x < 8 and 0 <= y < 8:
                    if you[x, y] == 1:
                        found_player = True
                        break
                    elif opponent[x, y] == 1:
                        dir_flips += 1
                    else:
                        break  # Empty cell blocks the line
                    x += dx
                    y += dy
                
                if found_player and dir_flips > 0:
                    total_flips += dir_flips
                    valid_move = True
            
            if valid_move:
                legal_moves.append((r, c, total_flips))
    
    if not legal_moves:
        return "pass"
    
    def cell_rank(r, c):
        if (r == 0 or r == 7) and (c == 0 or c == 7):
            return 0  # Corners
        elif r == 0 or r == 7 or c == 0 or c == 7:
            return 1  # Edge cells
        else:
            return 2  # Inner cells
    
    legal_moves.sort(key=lambda x: (cell_rank(x[0], x[1]), -x[2]))
    
    best_move = legal_moves[0]
    c, r = best_move[1], best_move[0]
    return f"{chr(ord('a') + c)}{8 - r}"
