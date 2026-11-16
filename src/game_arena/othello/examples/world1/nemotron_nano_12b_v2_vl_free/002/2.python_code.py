
import numpy as np

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    legal_moves = []
    directions = [(-1, -1), (-1, 0), (-1, 1),
                  (0, -1),           (0, 1),
                  (1, -1),  (1, 0),  (1, 1)]
    
    for row in range(8):
        for col in range(8):
            if you[row, col] != 0 or opponent[row, col] != 0:
                continue
            valid_move = False
            for dr, dc in directions:
                pr, pc = row + dr, col + dc
                if pr < 0 or pr >= 8 or pc < 0 or pc >= 8:
                    continue
                if opponent[pr, pc] != 1:
                    continue
                
                path = []
                temp_r, temp_c = pr, pc
                while 0 <= temp_r < 8 and 0 <= temp_c < 8 and opponent[temp_r, temp_c] == 1:
                    path.append((temp_r, temp_c))
                    temp_r += dr
                    temp_c += dc
                
                if 0 <= pr < 8 and 0 <= pc < 8 and you[pr, pc] == 1 and path:
                    valid_move = True
                    break
            if valid_move:
                legal_moves.append((row, col))
    
    if not legal_moves:
        return "pass"
    
    weight = np.array([
        [  10,  -3,  -3,   2,   2,  -3,  -3,  10],
        [  -3,  -6,  -3,  -1,  -1,  -3,  -6,  -3],
        [  -3,  -3,  -1,   0,   0,  -3,  -3,  -3],
        [   2,  -1,   0,   0,   0,  -1,   2,  -1],
        [   2,  -1,   0,   0,   0,  -1,   2,  -1],
        [  -3,  -3,  -1,  -1,  -1,  -3,  -6,  -3],
        [  -3,  -6,  -3,  -1,  -1,  -3,  -6,  -3],
        [  10,  -3,  -3,   2,   2,  -3,  -3,  10]
    ])
    
    best_move = None
    best_eval = -np.inf
    
    for r, c in legal_moves:
        new_you = np.copy(you)
        new_opponent = np.copy(opponent)
        new_you[r, c] = 1
        new_opponent[r, c] = 0
        
        for dr, dc in directions:
            pr, pc = r + dr, c + dc
            if not (0 <= pr < 8 and 0 <= pc < 8):
                continue
            if opponent[pr, pc] != 1:
                continue
            
            branch = []
            current_r, current_c = pr, pc
            while 0 <= current_r < 8 and 0 <= current_c < 8 and opponent[current_r, current_c] == 1:
                branch.append((current_r, current_c))
                current_r += dr
                current_c += dc
            
            if 0 <= current_r < 8 and 0 <= current_c < 8 and you[current_r, current_c] == 1:
                for x, y in branch:
                    new_you[x, y] = 1
                    new_opponent[x, y] = 0
        
        evaluation = np.sum((new_you - new_opponent) * weight)
        if evaluation > best_eval:
            best_eval = evaluation
            best_move = (r, c)
    
    col_char = chr(97 + best_move[1])
    row_num = best_move[0] + 1
    return f"{col_char}{row_num}"
