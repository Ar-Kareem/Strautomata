
import numpy as np

def policy(you, opponent) -> str:
    me = np.array(you, dtype=np.int8)
    opp = np.array(opponent, dtype=np.int8)
    
    QUAD_POS = [(0, 0), (0, 3), (3, 0), (3, 3)]
    
    def rotate_quad(board, q, d):
        r, c = QUAD_POS[q]
        sub = board[r:r+3, c:c+3].copy()
        rotated = np.rot90(sub, 1 if d == 'L' else -1)
        result = board.copy()
        result[r:r+3, c:c+3] = rotated
        return result
    
    def do_move(my_b, opp_b, row, col, q, d):
        new_me = my_b.copy()
        new_me[row, col] = 1
        return rotate_quad(new_me, q, d), rotate_quad(opp_b, q, d)
    
    LINES = []
    for r in range(6):
        for c in range(2):
            LINES.append(tuple((r, c+i) for i in range(5)))
    for r in range(2):
        for c in range(6):
            LINES.append(tuple((r+i, c) for i in range(5)))
    for r in range(2):
        for c in range(2):
            LINES.append(tuple((r+i, c+i) for i in range(5)))
    for r in range(2):
        for c in range(4, 6):
            LINES.append(tuple((r+i, c-i) for i in range(5)))
    
    def check_win(board):
        for line in LINES:
            if all(board[p] for p in line):
                return True
        return False
    
    def get_empty(my_b, opp_b):
        return [(r, c) for r in range(6) for c in range(6) 
                if my_b[r, c] == 0 and opp_b[r, c] == 0]
    
    def evaluate(my_b, opp_b):
        score = 0
        my_fours = 0
        for line in LINES:
            mc = sum(my_b[p] for p in line)
            oc = sum(opp_b[p] for p in line)
            if mc and oc:
                continue
            if mc == 4:
                score += 10000
                my_fours += 1
            elif mc == 3:
                score += 500
            elif mc == 2:
                score += 50
            elif mc == 1:
                score += 5
            if oc == 4:
                score -= 8000
            elif oc == 3:
                score -= 400
            elif oc == 2:
                score -= 40
        if my_fours >= 2:
            score += 100000
        return score
    
    def opp_can_win(opp_b, my_b):
        for r, c in get_empty(opp_b, my_b):
            for q in range(4):
                for d in ['L', 'R']:
                    no, nm = do_move(opp_b, my_b, r, c, q, d)
                    if check_win(no) and not check_win(nm):
                        return True
        return False
    
    cells = get_empty(me, opp)
    best = (cells[0][0], cells[0][1], 0, 'L')
    best_val = float('-inf')
    
    moves = []
    for r, c in cells:
        for q in range(4):
            for d in ['L', 'R']:
                nm, no = do_move(me, opp, r, c, q, d)
                iwin = check_win(nm)
                owin = check_win(no)
                if iwin and not owin:
                    return f"{r+1},{c+1},{q},{d}"
                if owin:
                    val = 0 if iwin else -1000000
                    needs_check = False
                else:
                    val = evaluate(nm, no)
                    needs_check = True
                moves.append((r, c, q, d, val, nm, no, needs_check))
    
    moves.sort(key=lambda x: -x[4])
    
    checked = 0
    for r, c, q, d, val, nm, no, needs_check in moves:
        if not needs_check or val >= 100000:
            adj = val
        elif checked < 40:
            checked += 1
            adj = -500000 if opp_can_win(no, nm) else val
        else:
            adj = val
        if adj > best_val:
            best_val = adj
            best = (r, c, q, d)
    
    return f"{best[0]+1},{best[1]+1},{best[2]},{best[3]}"
