
import numpy as np

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    directions = [(-1, -1), (-1, 0), (-1, 1),
                  (0, -1),          (0, 1),
                  (1, -1), (1, 0), (1, 1)]
    
    weights = np.array([
        [20, -3, 11, 6, 6, 11, -3, 20],
        [-3, -7, -4, 1, 1, -4, -7, -3],
        [11, -4, 2, 2, 2, 2, -4, 11],
        [6, 1, 2, 0, 0, 2, 1, 6],
        [6, 1, 2, 0, 0, 2, 1, 6],
        [11, -4, 2, 2, 2, 2, -4, 11],
        [-3, -7, -4, 1, 1, -4, -7, -3],
        [20, -3, 11, 6, 6, 11, -3, 20]
    ])
    
    legal_moves = []
    for r in range(8):
        for c in range(8):
            if you[r][c] == 0 and opponent[r][c] == 0:
                is_legal = False
                for dx, dy in directions:
                    x, y = r + dx, c + dy
                    current_flips = []
                    while 0 <= x < 8 and 0 <= y < 8:
                        if opponent[x][y] == 1:
                            current_flips.append((x, y))
                            x += dx
                            y += dy
                        elif you[x][y] == 1:
                            if len(current_flips) > 0:
                                is_legal = True
                            break
                        else:
                            break
                    if is_legal:
                        break
                if is_legal:
                    legal_moves.append((r, c))
    
    if not legal_moves:
        return "pass"
    
    best_score = -float('inf')
    best_moves = []
    for r, c in legal_moves:
        new_you = np.copy(you)
        new_opponent = np.copy(opponent)
        new_you[r][c] = 1
        
        flips = []
        for dx, dy in directions:
            x, y = r + dx, c + dy
            current_flips = []
            while 0 <= x < 8 and 0 <= y < 8:
                if new_opponent[x][y] == 1:
                    current_flips.append((x, y))
                    x += dx
                    y += dy
                elif new_you[x][y] == 1:
                    if len(current_flips) > 0:
                        flips.extend(current_flips)
                    break
                else:
                    break
        
        for fx, fy in flips:
            new_opponent[fx][fy] = 0
            new_you[fx][fy] = 1
        
        score = 0
        for i in range(8):
            for j in range(8):
                if new_you[i][j] == 1:
                    score += weights[i][j]
                if new_opponent[i][j] == 1:
                    score -= weights[i][j]
        
        if score > best_score:
            best_score = score
            best_moves = [(r, c)]
        elif score == best_score:
            best_moves.append((r, c))
    
    def prefer_corners(move):
        r, c = move
        if (r, c) in [(0,0), (0,7), (7,0), (7,7)]:
            return 0
        elif r == 0 or r == 7 or c == 0 or c == 7:
            return 1
        else:
            return 2
    
    best_moves.sort(key=prefer_corners)
    r, c = best_moves[0]
    column_letters = 'abcdefgh'
    return column_letters[c] + str(r + 1)
