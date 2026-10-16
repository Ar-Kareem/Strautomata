
import time

def policy(you, opponent):
    if hasattr(you, 'tolist'):
        you = you.tolist()
    if hasattr(opponent, 'tolist'):
        opponent = opponent.tolist()
    
    my = [list(row) for row in you]
    opp = [list(row) for row in opponent]
    
    ROWS, COLS = 5, 6
    DELTA = {'U': (-1, 0), 'D': (1, 0), 'L': (0, -1), 'R': (0, 1)}
    DIRS = ['U', 'D', 'L', 'R']
    
    start_time = time.time()
    TIME_LIMIT = 0.9
    WIN_SCORE = 100000
    
    def get_legal_moves(mine, theirs):
        moves = []
        for r in range(ROWS):
            for c in range(COLS):
                if mine[r][c]:
                    for d in DIRS:
                        dr, dc = DELTA[d]
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < ROWS and 0 <= nc < COLS and theirs[nr][nc]:
                            moves.append((r, c, d))
        return moves
    
    def apply_move(mine, theirs, r, c, d):
        dr, dc = DELTA[d]
        nr, nc = r + dr, c + dc
        new_mine = [row[:] for row in mine]
        new_theirs = [row[:] for row in theirs]
        new_mine[r][c] = 0
        new_mine[nr][nc] = 1
        new_theirs[nr][nc] = 0
        return new_mine, new_theirs
    
    def negamax(mine, theirs, depth, alpha, beta):
        if time.time() - start_time > TIME_LIMIT:
            return 0, True
        
        moves = get_legal_moves(mine, theirs)
        if not moves:
            return -WIN_SCORE, False
        
        if depth == 0:
            opp_moves = len(get_legal_moves(theirs, mine))
            return len(moves) - opp_moves, False
        
        best = -WIN_SCORE - 1
        for r, c, d in moves:
            new_mine, new_theirs = apply_move(mine, theirs, r, c, d)
            score, timeout = negamax(new_theirs, new_mine, depth - 1, -beta, -alpha)
            score = -score
            
            if timeout:
                return 0, True
            
            if score > best:
                best = score
            if score > alpha:
                alpha = score
            if alpha >= beta:
                break
        
        return best, False
    
    all_moves = get_legal_moves(my, opp)
    
    if not all_moves:
        return "0,0,U"
    
    if len(all_moves) == 1:
        r, c, d = all_moves[0]
        return f"{r},{c},{d}"
    
    best_move = all_moves[0]
    
    for depth in range(1, 100):
        if time.time() - start_time > TIME_LIMIT * 0.3:
            break
        
        current_best = best_move
        current_best_score = float('-inf')
        
        ordered_moves = [best_move] + [m for m in all_moves if m != best_move]
        alpha = float('-inf')
        completed = True
        
        for r, c, d in ordered_moves:
            if time.time() - start_time > TIME_LIMIT * 0.8:
                completed = False
                break
            
            new_mine, new_theirs = apply_move(my, opp, r, c, d)
            score, timeout = negamax(new_theirs, new_mine, depth - 1, float('-inf'), -alpha)
            score = -score
            
            if timeout:
                completed = False
                break
            
            if score > current_best_score:
                current_best_score = score
                current_best = (r, c, d)
            if score > alpha:
                alpha = score
            if score >= WIN_SCORE:
                break
        
        if completed:
            best_move = current_best
            if current_best_score >= WIN_SCORE:
                break
    
    return f"{best_move[0]},{best_move[1]},{best_move[2]}"
