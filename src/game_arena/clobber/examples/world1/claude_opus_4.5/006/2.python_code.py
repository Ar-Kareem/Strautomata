
import numpy as np

def policy(you: list[int], opponent: list[int]) -> str:
    you = np.array(you)
    opponent = np.array(opponent)
    
    DIRS = {'U': (-1, 0), 'D': (1, 0), 'L': (0, -1), 'R': (0, 1)}
    ROWS, COLS = 5, 6
    
    def get_moves(my_board, opp_board):
        moves = []
        for r in range(ROWS):
            for c in range(COLS):
                if my_board[r, c] == 1:
                    for d, (dr, dc) in DIRS.items():
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < ROWS and 0 <= nc < COLS and opp_board[nr, nc] == 1:
                            moves.append((r, c, d, nr, nc))
        return moves
    
    def apply_move(my_board, opp_board, move):
        r, c, d, nr, nc = move
        new_my = my_board.copy()
        new_opp = opp_board.copy()
        new_my[r, c] = 0
        new_my[nr, nc] = 1
        new_opp[nr, nc] = 0
        return new_my, new_opp
    
    def evaluate(my_board, opp_board):
        my_moves = len(get_moves(my_board, opp_board))
        opp_moves = len(get_moves(opp_board, my_board))
        
        if my_moves == 0:
            return -10000
        if opp_moves == 0:
            return 10000
        
        # Mobility is key
        score = (my_moves - opp_moves) * 10
        
        # Count active pieces (pieces that can potentially capture)
        my_active = 0
        opp_active = 0
        for r in range(ROWS):
            for c in range(COLS):
                if my_board[r, c]:
                    for dr, dc in DIRS.values():
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < ROWS and 0 <= nc < COLS and opp_board[nr, nc]:
                            my_active += 1
                            break
                if opp_board[r, c]:
                    for dr, dc in DIRS.values():
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < ROWS and 0 <= nc < COLS and my_board[nr, nc]:
                            opp_active += 1
                            break
        
        score += (my_active - opp_active) * 2
        return score
    
    def minimax(my_board, opp_board, depth, alpha, beta, maximizing):
        moves = get_moves(my_board, opp_board) if maximizing else get_moves(opp_board, my_board)
        
        if not moves:
            return -10000 if maximizing else 10000
        
        if depth == 0:
            return evaluate(my_board, opp_board)
        
        if maximizing:
            max_eval = -float('inf')
            for move in moves:
                new_my, new_opp = apply_move(my_board, opp_board, move)
                eval_score = minimax(new_my, new_opp, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in moves:
                new_opp, new_my = apply_move(opp_board, my_board, move)
                eval_score = minimax(new_my, new_opp, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    moves = get_moves(you, opponent)
    
    if not moves:
        # Should not happen if called correctly, but safety fallback
        return "0,0,U"
    
    if len(moves) == 1:
        m = moves[0]
        return f"{m[0]},{m[1]},{m[2]}"
    
    best_move = moves[0]
    best_score = -float('inf')
    
    # Adaptive depth based on number of moves
    depth = 4 if len(moves) < 15 else 3
    
    for move in moves:
        new_my, new_opp = apply_move(you, opponent, move)
        score = minimax(new_my, new_opp, depth, -float('inf'), float('inf'), False)
        if score > best_score:
            best_score = score
            best_move = move
    
    return f"{best_move[0]},{best_move[1]},{best_move[2]}"
