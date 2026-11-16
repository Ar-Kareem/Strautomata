
import numpy as np
import time

def policy(you: list[int], opponent: list[int]) -> str:
    you = np.array(you)
    opponent = np.array(opponent)
    
    DIRS = {'U': (-1, 0), 'D': (1, 0), 'L': (0, -1), 'R': (0, 1)}
    ROWS, COLS = 5, 6
    start_time = time.time()
    TIME_LIMIT = 0.9
    
    def get_moves(my_pieces, opp_pieces):
        moves = []
        for r in range(ROWS):
            for c in range(COLS):
                if my_pieces[r, c] == 1:
                    for d, (dr, dc) in DIRS.items():
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < ROWS and 0 <= nc < COLS and opp_pieces[nr, nc] == 1:
                            moves.append((r, c, d, nr, nc))
        return moves
    
    def make_move(my_pieces, opp_pieces, move):
        r, c, d, nr, nc = move
        new_my = my_pieces.copy()
        new_opp = opp_pieces.copy()
        new_my[r, c] = 0
        new_my[nr, nc] = 1
        new_opp[nr, nc] = 0
        return new_my, new_opp
    
    def evaluate(my_pieces, opp_pieces):
        my_moves = len(get_moves(my_pieces, opp_pieces))
        opp_moves = len(get_moves(opp_pieces, my_pieces))
        
        my_count = np.sum(my_pieces)
        opp_count = np.sum(opp_pieces)
        
        # Mobility is most important
        mobility_score = (my_moves - opp_moves) * 10
        
        # Piece advantage matters less
        piece_score = (my_count - opp_count) * 2
        
        return mobility_score + piece_score
    
    def minimax(my_pieces, opp_pieces, depth, alpha, beta, maximizing):
        if time.time() - start_time > TIME_LIMIT:
            return evaluate(my_pieces, opp_pieces), None
        
        moves = get_moves(my_pieces, opp_pieces) if maximizing else get_moves(opp_pieces, my_pieces)
        
        if not moves:
            return (-10000 if maximizing else 10000), None
        
        if depth == 0:
            return evaluate(my_pieces, opp_pieces), None
        
        best_move = None
        if maximizing:
            max_eval = float('-inf')
            for move in moves:
                new_my, new_opp = make_move(my_pieces, opp_pieces, move)
                eval_score, _ = minimax(new_my, new_opp, depth - 1, alpha, beta, False)
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for move in moves:
                new_opp, new_my = make_move(opp_pieces, my_pieces, move)
                eval_score, _ = minimax(new_my, new_opp, depth - 1, alpha, beta, True)
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval, best_move
    
    legal_moves = get_moves(you, opponent)
    
    if not legal_moves:
        # Shouldn't happen but return something
        return "0,0,U"
    
    if len(legal_moves) == 1:
        m = legal_moves[0]
        return f"{m[0]},{m[1]},{m[2]}"
    
    best_move = legal_moves[0]
    
    for depth in range(1, 20):
        if time.time() - start_time > TIME_LIMIT:
            break
        _, move = minimax(you, opponent, depth, float('-inf'), float('inf'), True)
        if move is not None:
            best_move = move
    
    return f"{best_move[0]},{best_move[1]},{best_move[2]}"
