
import numpy as np

def policy(you, opponent) -> str:
    lines = []
    directions = [(0,1), (1,0), (1,1), (1,-1)]
    for r in range(6):
        for c in range(6):
            for dr, dc in directions:
                if 0 <= r + 4*dr < 6 and 0 <= c + 4*dc < 6:
                    line = [(r + i*dr, c + i*dc) for i in range(5)]
                    if line not in lines:
                        lines.append(line)
    
    you_arr = np.array(you)
    opp_arr = np.array(opponent)
    empty = np.where((you_arr == 0) & (opp_arr == 0))
    empty_positions = list(zip(empty[0], empty[1]))
    
    best_score = -float('inf')
    best_move = None
    
    for r, c in empty_positions:
        new_you = you_arr.copy()
        new_opp = opp_arr.copy()
        new_you[r, c] = 1
        
        for quad in range(4):
            for dir in ['L', 'R']:
                tmp_you = new_you.copy()
                tmp_opp = new_opp.copy()
                
                if quad == 0:
                    q_rows = slice(0,3)
                    q_cols = slice(0,3)
                elif quad == 1:
                    q_rows = slice(0,3)
                    q_cols = slice(3,6)
                elif quad == 2:
                    q_rows = slice(3,6)
                    q_cols = slice(0,3)
                else:
                    q_rows = slice(3,6)
                    q_cols = slice(3,6)
                
                k = 1 if dir == 'L' else -1
                tmp_you[q_rows, q_cols] = np.rot90(tmp_you[q_rows, q_cols], k=k)
                tmp_opp[q_rows, q_cols] = np.rot90(tmp_opp[q_rows, q_cols], k=k)
                
                you_win = any(all(tmp_you[r][c] for (r, c) in line) for line in lines)
                if you_win:
                    return f"{r+1},{c+1},{quad},{dir}"
                
                opp_win = any(all(tmp_opp[r][c] for (r, c) in line) for line in lines)
                if opp_win:
                    score = -float('inf')
                else:
                    score = evaluate(tmp_you, tmp_opp, lines)
                
                if score > best_score:
                    best_score = score
                    best_move = f"{r+1},{c+1},{quad},{dir}"
    
    return best_move

def evaluate(you, opponent, lines):
    my_score = 0
    opp_score = 0
    for line in lines:
        my_count = sum(you[r][c] for (r, c) in line)
        opp_count = sum(opponent[r][c] for (r, c) in line)
        empty_count = 5 - my_count - opp_count
        
        if opp_count == 0 and my_count > 0:
            my_score += (my_count ** 3) * empty_count
        elif my_count == 0 and opp_count > 0:
            opp_score += (opp_count ** 3) * empty_count
    
    return my_score - opp_score
